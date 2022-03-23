from pel.datastream import DataStream
from pel.hexdump import hexdump
from collections import OrderedDict
import json


class Default:
    """
    This represents a section in a PEL that isn't handled by another class.
    The toJSON function will just hexdump the contents.
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int):
        self.stream = stream
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.subType = subType
        self.componentID = componentID
        self.dataLength = sectionLen - 8
        self.data = self.stream.get_mem(self.dataLength)

    def toJSON(self) -> OrderedDict:

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = "0x{:02X}".format(self.componentID)

        mv = memoryview(self.data)
        out['Data'] = hexdump(mv)

        return out
