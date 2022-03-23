from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import creatorIDs
from pel.hexdump import hexdump
from enum import Enum, unique
import json
import sys


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

    def __init__(self, creatorID: str, compID: str, subType: int, version: int,
                 data: bytes):
        self.creatorID = creatorID
        self.compID = compID
        self.subType = subType
        self.version = version
        self.data = data

    def parse(self) -> str:
        if self.creatorID in creatorIDs and creatorIDs[self.creatorID] == "BMC" \
                and self.compID == 0x2000:
            value = self.getBuiltinFormatJSON()
        else:
            value = self.parseCustom()

        return value

    def parseCustom(self) -> str:
        import importlib
        name = (self.creatorID.lower() + "%04X" % self.compID).lower()
        try:
            cls = importlib.import_module("udparsers." + name + "." + name)
            mv = memoryview(self.data)
            return cls.parseUDToJson(self.subType, self.version, mv)
        except ImportError:
            mv = memoryview(self.data)
            return json.dumps(hexdump(mv))
        except Exception as e:
            print('Failed parsing user data for creator {} compID {} '
                  'subType {} version {}: {}'.format(
                      self.creatorID, "0x%04X" % self.compID,
                      "0x%X" % self.subType, self.version, str(e)), file=sys.stderr)
            mv = memoryview(self.data)
            return json.dumps(hexdump(mv))

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
