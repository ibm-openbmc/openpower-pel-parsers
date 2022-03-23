from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import *
from pel.hexdump import hexdump
from enum import Enum, unique
import json


@unique
class UserDataFormat(Enum):
    json = 0x1
    cbor = 0x2
    text = 0x3
    custom = 0x4


def get_value(data: memoryview, start: int, end: int) -> int:
    return int.from_bytes(data[start: start + end], byteorder="big")


class UserData:
    """
    This represents the User Data section in a PEL.  It is free form data
    that the creator knows the contents of.  The component ID, version,
    and sub-type fields in the section header are used to identify the
    format.

    The Section base class handles the section header structure that every
    PEL section has at offset zero.
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
        self.dataLength = sectionLen - 8
        self.data = self.stream.get_mem(self.dataLength)

    def parse(self) -> str:
        import importlib
        name = (self.creatorID.lower() + "%04X" % self.componentID).lower()
        try:
            cls = importlib.import_module("udparsers." + name + "." + name)
            mv = memoryview(self.data)
            return cls.parseUDToJson(self.subType, self.versionID, mv)
        except:
            mv = memoryview(self.data)
            return json.dumps(hexdump(mv))

    def getBuiltinFormatJSON(self) -> str:
        if self.subType == UserDataFormat.json.value:
            string = bytes.decode(self.data).strip().rstrip('\x00')
            return string
        elif self.subType == UserDataFormat.cbor.value:
            # TODO, support CBOR
            # pad = get_value(self.stream.data, self.dataLength - 4, 4)
            # if self.dataLength > pad + 4:
            #     self.dataLength = self.dataLength - pad - 4
            # out.update(json.loads(bytes.decode(
            #     self.stream.get_mem(self.dataLength)).strip())).

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

            return json.dumps(lines)

    def toJSON(self) -> str:

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = "0x{:02X}".format(self.componentID)

        if creatorIDs[self.creatorID] == "BMC" and self.componentID == 0x2000:
            value = self.getBuiltinFormatJSON()
        else:
            value = self.parse()

        j = json.loads(value)
        if not isinstance(j, dict):
            out['Data'] = j
        else:
            out.update(j)

        return out
