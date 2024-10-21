from pel.datastream import DataStream
from collections import OrderedDict
from enum import Enum, unique
from pel.peltool.pel_types import SRCType
from pel.peltool.registry import Registry
from pel.peltool.pel_values import failingComponentType, \
    calloutPriorityValues
from pel.peltool.comp_id import getDisplayCompID
from pel.peltool.config import Config
import json
import sys
import importlib

registry = Registry()
calloutParsers = {}
srcParsers = {}

@unique
class HeaderFlags(Enum):
    additionalSections = 0x01
    powerFaultEvent = 0x02
    hypDumpInit = 0x04
    postOPPanel = 0x08
    i5OSServiceEventBit = 0x10
    virtualProgressSRC = 0x80


@unique
class ErrorStatusFlags(Enum):
    terminateFwErr = 0x20000000
    deconfigured = 0x02000000
    guarded = 0x01000000


@unique
class Flags(Enum):
    pnSupplied = 0x08
    ccinSupplied = 0x04
    maintProcSupplied = 0x02
    snSupplied = 0x01


def get_value(data: memoryview, start: int, end: int) -> int:
    return int.from_bytes(data[start: start + end], byteorder="big")


class FRUIdentity:
    def __init__(self, stream: DataStream):
        self.type = stream.get_int(2)
        self.size = stream.get_int(1)
        self.flags = stream.get_int(1)
        self.pnOrProcedureID = ""
        self.ccin = ""
        self.sn = ""
        self.flattenedSize = 4

        if self.flags & Flags.pnSupplied.value or self.flags & Flags.maintProcSupplied.value:
            self.pnOrProcedureID = bytes.decode(
                stream.get_mem(8)).strip("\u0000")
            self.flattenedSize += 8

        if self.flags & Flags.ccinSupplied.value:
            self.ccin = bytes.decode(stream.get_mem(4)).strip("\u0000")
            self.flattenedSize += 4

        if self.flags & Flags.snSupplied.value:
            self.sn = bytes.decode(stream.get_mem(12)).strip("\u0000")
            self.flattenedSize += 12


class PCEIdentity:
    def __init__(self, stream: DataStream):
        self.type = stream.get_int(2)
        self.flattenedSize = stream.get_int(1)
        self.flags = stream.get_int(1)
        self.machineType = bytes.decode(stream.get_mem(8)).strip("\u0000")
        self.serialNumber = bytes.decode(
            stream.get_mem(12)).strip("\u0000")
        if self.flattenedSize < (4 + 8 + 12):
            print("PCE identity structure size field too small")
            return
        self.pceNameSize = self.flattenedSize - (4 + 8 + 12)
        self.pceName = bytes.decode(
            stream.get_mem(self.pceNameSize)).strip("\u0000")


class MRUCallout:
    def __init__(self, priority: int, id: int) -> None:
        self.priority = priority
        self.id = id


class MRU:
    def __init__(self, stream: DataStream):
        self.type = stream.get_int(2)
        self.flattenedSize = stream.get_int(1)
        self.flags = stream.get_int(1)
        self.reserved4B = stream.get_int(4)
        self.mrus = []
        for _ in range(self.flags & 0xf):
            mru = MRUCallout(stream.get_int(4), stream.get_int(4))
            self.mrus.append(mru)


class Callout:
    def __init__(self, stream: DataStream):
        self.size = stream.get_int(1)
        self.flags = stream.get_int(1)
        self.priority = stream.get_int(1)
        self.locationCode = ""
        self.locationCodeSize = stream.get_int(1)
        if self.locationCodeSize > 0:
            self.locationCode = bytes.decode(
                stream.get_mem(self.locationCodeSize)).strip("\u0000")
        self.fruIdentity = None
        self.pceIdentity = None
        self.mru = None

        currentSize = 4 + self.locationCodeSize
        while self.size > currentSize:
            type = get_value(stream.data, stream.index, 2)
            if type == 0x4944:
                self.fruIdentity = FRUIdentity(stream)
            elif type == 0x5045:
                self.pceIdentity = PCEIdentity(stream)
            elif type == 0x4D52:
                self.mru = MRU(stream)
            else:
                break

    def flattenedSize(self):
        size = 4 + self.locationCodeSize
        size += self.fruIdentity.flattenedSize if self.fruIdentity else 0
        size += self.pceIdentity.flattenedSize if self.pceIdentity else 0
        size += self.mru.flattenedSize if self.mru else 0
        return size


class SRC:
    """
    SRC stands for System Reference Code.

    This class represents the SRC sections in the PEL, of which there are 2:
    primary SRC and secondary SRC.  These are the same structurally, the
    difference is that the primary SRC must be the 3rd section in the PEL if
    present and there is only one of them, and the secondary SRC sections are
    optional and there can be more than one (by definition, for there to be a
    secondary SRC, a primary SRC must also exist).

    This section consists of:
    - An 8B header (Has the version, flags, hexdata word count, and size fields)
    - 8 4B words of hex data
    - An ASCII character string
    - An optional subsection for Callouts
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int, creatorID: str):
        self.stream = stream
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.subType = subType
        self.componentID = componentID
        self.creatorID = creatorID
        self.version = 0
        self.flags = 0
        self.reserved1B = 0
        self.wordCount = 0
        self.reserved2B = 0
        self.size = 0
        self.hexData = []
        self.srcType = 0
        self.asciiString = ""

    def buildMessage(self, details: dict) -> str:
        if 'Message' not in details:
            return ''

        message = details['Message']
        if 'MessageArgSources' in details:
            hexword_args = []

            # Strip off the word number from SRCWordN and subtract 2 to get
            # the hexData word to use
            for arg in details['MessageArgSources']:
                hexword_args.append(hex(self.hexData[int(arg[-1]) - 2]))

            # message may have %1, etc. replace with {} and then fill
            # those in with the hexData words
            import re
            message = re.sub(r'%[1-9]', "{}", message)
            message = message.format(*hexword_args)

        return message

    def buildHexwordDescs(self, details: dict) -> OrderedDict:
        descriptions = OrderedDict()
        if 'Words6To9' not in details or not details['Words6To9']:
            return

        for num, word_contents in details['Words6To9'].items():
            # Nobody wants to see these if no description
            if 'Description' not in word_contents:
                continue

            index = int(num) - 2
            descriptions[word_contents['AdditionalDataPropSource']] = \
                [self.hexData[index], word_contents['Description']]

        return descriptions

    def getErrorDetails(self, out: OrderedDict, code: str, srcType: str):
        code = "0x" + code
        details = registry.getErrorMessage(code, srcType)

        od = OrderedDict()
        od["Message"] = self.buildMessage(details)
        if od["Message"]:
            descs = self.buildHexwordDescs(details)
            if descs:
                od.update(descs)

            out["Error Details"] = od

    def getProcedureDesc(self, procName: str, out: OrderedDict):
        """
        Look up the procedure description from a
        calloutparsers.Xcallouts.Xcallouts module if it's there.
        (X = creator ID in lower case)
        """
        try:
            name = self.creatorID.lower() + "callouts"
            calloutParserMod = "calloutparsers." + name + "." + name
            if calloutParserMod in calloutParsers:
                cls = calloutParsers[calloutParserMod]
                if cls is None:
                    # The module, which was previously checked, is not found.
                    return
            else:
                cls = importlib.import_module(calloutParserMod)
                calloutParsers[calloutParserMod] = cls

            desc = cls.getMaintProcDesc(procName)
            if desc:
                out["Description"] = json.loads(desc)
        except:
            calloutParsers[calloutParserMod] = None
            pass

    def getCallouts(self, out: OrderedDict, config: Config):
        od = OrderedDict()
        _ = self.stream.get_int(1)  # subsectionID
        _ = self.stream.get_int(1)  # subsectionFlags
        subsectionWordLength = self.stream.get_int(2)
        currentLength = 4
        callouts = []
        while subsectionWordLength * 4 > currentLength:
            callout = Callout(self.stream)
            callouts.append(callout)
            currentLength += callout.flattenedSize()
        od["Callout Count"] = len(callouts)
        calloutJsons = []
        for callout in callouts:
            json = OrderedDict()
            if callout.fruIdentity:
                json["FRU Type"] = \
                    failingComponentType.get(callout.fruIdentity.flags & 0xf0,
                                             'Invalid')
                json["Priority"] = calloutPriorityValues.get(
                    callout.priority, 'Invalid')
                if len(callout.locationCode) > 0:
                    json["Location Code"] = callout.locationCode
                if callout.fruIdentity.flags & Flags.pnSupplied.value:
                    json["Part Number"] = callout.fruIdentity.pnOrProcedureID
                if callout.fruIdentity.flags & Flags.maintProcSupplied.value:
                    json["Procedure"] = callout.fruIdentity.pnOrProcedureID
                    if config.allow_plugins:
                        self.getProcedureDesc(json["Procedure"], json)
                if callout.fruIdentity.flags & Flags.ccinSupplied.value:
                    json["CCIN"] = callout.fruIdentity.ccin
                if callout.fruIdentity.flags & Flags.snSupplied.value:
                    json["Serial Number"] = callout.fruIdentity.sn

            if callout.pceIdentity:
                if len(callout.pceIdentity.machineType) > 0:
                    json["PCE MTMS"] = callout.pceIdentity.machineType + \
                        "_" + callout.pceIdentity.serialNumber
                if len(callout.pceIdentity.pceName):
                    json["PCE Name"] = callout.pceIdentity.pceName

            if callout.mru:
                mru = OrderedDict()
                mruId = ""
                for mru in callout.mru.mrus:
                    mruId += "%08X" % mru.id + ","
                json["MRU Id"] = mruId[:-1]

            calloutJsons.append(json)
        od["Callouts"] = calloutJsons
        out["Callout Section"] = od

    def parse(self, hexwords: list) -> str:
        if len(hexwords) < 8:
            print("The length of the hexwords < 8, exit")
            exit(1)

        name = self.creatorID.lower() + "src"
        srcParserMod = "srcparsers." + name + "." + name
        try:
            if srcParserMod in srcParsers:
                cls = srcParsers[srcParserMod]
                if cls is None:
                    # The module, which was previously checked, is not found.
                    return ""
            else:
                cls = importlib.import_module(srcParserMod)
                srcParsers[srcParserMod] = cls
        except:
            srcParsers[srcParserMod] = None
            return ""

        try:
            return cls.parseSRCToJson(self.asciiString, hexwords[0], hexwords[1], hexwords[2],
                                      hexwords[3], hexwords[4], hexwords[5], hexwords[6], hexwords[7])
        except Exception as e:
            print('Error getting SRC details for {}: {}'.format(
                self.asciiString.rstrip(), str(e)), file=sys.stderr)
            return ''

    def toJSON(self, config: Config) -> OrderedDict:
        self.version = "0x" + self.stream.get_mem(1).hex()
        self.flags = self.stream.get_int(1)
        self.reserved1B = self.stream.get_int(1)
        self.wordCount = self.stream.get_int(1)
        self.reserved2B = self.stream.get_int(2)
        self.size = self.stream.get_int(2)
        for i in range(8):
            self.hexData.append(self.stream.get_int(4))
        self.asciiString = bytes.decode(self.stream.get_mem(32))
        self.srcType = self.asciiString[0:2]

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = getDisplayCompID(self.componentID, self.creatorID)
        out["SRC Version"] = self.version
        out["SRC Format"] = "0x{:02X}".format(self.hexData[0] & 0xFF)
        out["Virtual Progress SRC"] = "True" if self.flags & HeaderFlags.virtualProgressSRC.value else "False"
        out["I5/OS Service Event Bit"] = "True" if self.flags & HeaderFlags.i5OSServiceEventBit.value else "False"
        out["Hypervisor Dump Initiated"] = "True" if self.flags & HeaderFlags.hypDumpInit.value else "False"

        is_bmc_src = self.srcType == SRCType.bmcError.value or self.srcType == SRCType.powerError.value
        is_hostboot_src = self.srcType == SRCType.hostbootError.value

        if is_bmc_src:
            out["Backplane CCIN"] = str("%04X" % (self.hexData[1] >> 16))
            out["Terminate FW Error"] = "True" if self.hexData[3] & ErrorStatusFlags.terminateFwErr.value else "False"
        if is_bmc_src or is_hostboot_src:
            out["Deconfigured"] = "True" if self.hexData[3] & ErrorStatusFlags.deconfigured.value else "False"
            out["Guarded"] = "True" if self.hexData[3] & ErrorStatusFlags.guarded.value else "False"
            self.getErrorDetails(
                out, self.asciiString[4:8], self.asciiString[0:2])

        out["Valid Word Count"] = "0x" + "%02X" % self.wordCount
        out["Reference Code"] = self.asciiString.strip()

        hexwords = []
        for i in range(2, self.wordCount + 1):
            num = i
            if num >= 2 and num <= 9:
                num -= 2
            tmpWord = "%08X" % self.hexData[num]
            out["Hex Word " + str(i)] = tmpWord
            hexwords.append(tmpWord)

        # add zeroes to get 8 hexwords for parse()
        while len(hexwords) < 8:
            hexwords.append('00000000')

        if self.flags & HeaderFlags.additionalSections.value:
            self.getCallouts(out, config)

        if config.allow_plugins:
            value = self.parse(hexwords)
            if value != '' and value != 'null':
                out["SRC Details"] = json.loads(value)

        return out
