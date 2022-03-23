from pel.datastream import DataStream
from pel.peltool.comp_id import getDisplayCompID
from collections import OrderedDict


class ImpactedPartition:
    """
    This represents the Impacted Partition section in a PEL.
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
        self.primaryPartID = 0
        self.lpNameLength = 0
        self.targetLPcount = 0
        self.logicalPartLogID = 0
        self.lpName = ""
        self.targetLPs = []

    def toJSON(self) -> OrderedDict:
        self.primaryPartID = self.stream.get_int(2)
        self.lpNameLength = self.stream.get_int(1)
        self.targetLPcount = self.stream.get_int(1)
        self.logicalPartLogID = self.stream.get_int(4)

        if self.lpNameLength:
            self.lpName = bytes.decode(
                self.stream.get_mem(self.lpNameLength)).rstrip('\x00')

        if self.targetLPcount:
            for _ in range(self.targetLPcount):
                self.targetLPs.append(self.stream.get_int(2))

        # PEL sections are 4 byte aligned, so may need
        # to advance the stream past the padding to get ready
        # for next section.
        if self.targetLPcount % 2:
            _ = self.stream.get_int(2)

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = getDisplayCompID(self.componentID, self.creatorID)

        out["Primary Partition ID"] = "0x{:04X}".format(self.primaryPartID)
        out["Length of LP Name"] = "0x{:02X}".format(self.lpNameLength)
        out["Target LP Count"] = "0x{:02X}".format(self.targetLPcount)
        out["Logical Partition Log ID"] = "0x{:08X}".format(
            self.logicalPartLogID)
        out["Primary Partition Name"] = self.lpName

        for i in range(self.targetLPcount):
            out["Target LP"] = "0x{:04X}".format(self.targetLPs[i])

        return out
