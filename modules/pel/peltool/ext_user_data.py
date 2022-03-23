from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import *
import json


class ExtUserData:
    """
    This represents the Extended User Header section in a PEL.
    It is a required section. It contains code versions, an MTMS
    subsection, and a string called a symptom ID.

    The Section base class handles the section header structure that every
    PEL section has at offset zero.
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int):
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.subType = subType
        self.componentID = componentID
        dataLength = sectionLen - 4 - 8
        self.creatorID = stream.get_int(1)
        self.reserved1B = stream.get_int(1)
        self.reserved2B = stream.get_int(2)
        self.data = bytes.decode(stream.get_mem(dataLength)).strip()

    def toJSON(self) -> str:
        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = "0x{:02X}".format(self.componentID)
        out.update(json.loads(self.data))

        return out
