from pel.datastream import DataStream
from pel.peltool.comp_id import getDisplayCompID
from collections import OrderedDict


class FailingMTMS:
    """
    This represents the Failing Enclosure MTMS section in a PEL.
    It is a required section.  In the BMC case, the enclosure is
    the system enclosure.
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int, creatorID: str):
        self.stream = stream
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.reserved0 = 0
        self.reserved1 = 0
        self.subType = subType
        self.componentID = componentID
        self.creatorID = creatorID
        self.machineType = ""
        self.serialNumber = ""

    def toJSON(self) -> OrderedDict:
        self.machineType = bytes.decode(self.stream.get_mem(8))
        self.serialNumber = bytes.decode(self.stream.get_mem(12))

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = getDisplayCompID(self.componentID, self.creatorID)
        out["Machine Type Model"] = self.machineType.strip("\u0000")
        out["Serial Number"] = self.serialNumber.strip("\u0000")

        return out
