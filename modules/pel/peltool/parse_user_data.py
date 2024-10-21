from pel.peltool.pel_values import creatorIDs
from pel.peltool.config import Config
from pel.hexdump import hexdump
from enum import Enum, unique
import json
import importlib

userDataParsers = {}

@unique
class UserDataFormat(Enum):
    json = 0x1
    cbor = 0x2
    text = 0x3
    custom = 0x4


def get_value(data: memoryview, start: int, end: int) -> int:
    return int.from_bytes(data[start: start + end], byteorder="big")


class ParseUserData:
    """
    The toJSON() function handles parsing the data from either UserData or
    ExtUserData sections.
    """

    def __init__(self, creatorID: str, compID: int, subType: int, version: int,
                 data: bytes):
        self.creatorID = creatorID
        self.compID = compID
        self.subType = subType
        self.version = version
        self.data = data

    def parse(self, config: Config) -> str:
        if self.creatorID in creatorIDs and creatorIDs[self.creatorID] == "BMC" \
                and self.compID == 0x2000:
            value = self.getBuiltinFormatJSON()
        else:
            if config.allow_plugins:
                value = self.parseCustom()
            else:
                d = dict()
                if self.data:
                    mv = memoryview(self.data)
                    d["Data"] = hexdump(mv)
                return json.dumps(d)

        # Catch if value is None, otherwise python crashes
        if value == None:
            d = dict()
            # in case we have problems, try to make every attempt to get some data points out
            d["Error"] = ("Parser returned a value of None for creatorID={} compID={} subType={} version={}"
                     .format(self.creatorID, "0x%04X" % self.compID, self.subType, self.version))
            if self.data:
                mv = memoryview(self.data)
                d["Data"] = hexdump(mv)
            return json.dumps(d)
        # Normal processing below
        return value

    def parseCustom(self) -> str:
        name = (self.creatorID.lower() + "%04X" % self.compID).lower()
        userDataParserMod = "udparsers." + name + "." + name
        try:
            if userDataParserMod in userDataParsers:
                cls = userDataParsers[userDataParserMod]
            else:
                cls = importlib.import_module(userDataParserMod)
                userDataParsers[userDataParserMod] = cls
            if self.data:
                mv = memoryview(self.data)
                if cls is None:
                    # The module, which was previously checked, is not found.
                    return json.dumps(hexdump(mv))
                else:
                    return cls.parseUDToJson(self.subType, self.version, mv)
        except ImportError:
            userDataParsers[userDataParserMod] = None
            # No print for informational purposes, this is encountered often, e.g. PHYP
            if self.data:
                mv = memoryview(self.data)
                return json.dumps(hexdump(mv))
        except Exception as e:
            d = dict()
            # in case we do NOT have data, dump the Error at a minimum
            d["Error"] = ("Failed parsing user data for creator={} compID={} subType={} version={} Exception={}"
                              .format(self.creatorID, "0x%04X" % self.compID, "0x%X" % self.subType, self.version, e))
            if self.data:
                mv = memoryview(self.data)
                d["Data"] = hexdump(mv)
            return json.dumps(d)
        # We should have returned above, but in case we did NOT
        return json.dumps("")


    def getBuiltinFormatJSON(self) -> str:
        if self.subType == UserDataFormat.json.value:
            string = bytes.decode(self.data).strip().rstrip('\x00')
            return string
        elif self.subType == UserDataFormat.cbor.value:
            # TODO, support CBOR (binary JSON)
            # pad = get_value(self.stream.data, self.dataLength - 4, 4)
            # if self.dataLength > pad + 4:
            #     self.dataLength = self.dataLength - pad - 4
            # out.update(json.loads(bytes.decode(
            #     self.stream.get_mem(self.dataLength)).strip()))

            mv = memoryview(self.data)
            return json.dumps(hexdump(mv))

        elif self.subType == UserDataFormat.text.value:
            lines = []
            line = ''
            for ch in bytes.decode(self.data).strip().rstrip('\x00'):
                if ch != '\n':
                    if ord(ch) < ord(' ') or ord(ch) > ord('~'):
                        ch = '.'
                    line += ch
                else:
                    lines.append(line)
                    line = ''

            if line != '':
                lines.append(line)

            return json.dumps(lines)
        else:
            mv = memoryview(self.data)
            return json.dumps(hexdump(mv))
