from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import creatorIDs


def getTimestamp(stream: DataStream) -> str:
    year = stream.get_mem(2).hex()
    month = stream.get_mem(1).hex()
    day = stream.get_mem(1).hex()
    hour = stream.get_mem(1).hex()
    min = stream.get_mem(1).hex()
    sec = stream.get_mem(1).hex()
    hundredths = stream.get_mem(1).hex()
    #  "03/08/2022 18:40:27"
    createTime = month + "/" + day + "/" + year + " " + hour + ":" + min + ":" + sec
    return createTime


class PrivateHeader:
    """
    This represents the Private Header section in a PEL.  It is required,
    and it is always the first section.

    The Section base class handles the section header structure that every
    PEL section has at offset zero.

    The fields in this class directly correspond to the order and sizes of
    the fields in the section.
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int):
        self.stream = stream
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.reserved0 = 0
        self.reserved1 = 0
        self.subType = subType
        self.componentID = componentID
        self.sectionCount = 0
        self.creatorID = ""
        self.obmcLogID = 0
        self.creatorVersion = 0
        self.pLID = ""
        self.lEID = ""
        self.createTime = ""
        self.committeTime = ""

    def toJSON(self) -> str:
        self.createTime = getTimestamp(self.stream)
        self.committeTime = getTimestamp(self.stream)
        self.creatorID = bytes.decode(self.stream.get_mem(1))
        self.reserved0 = self.stream.get_int(1)
        self.reserved1 = self.stream.get_int(1)
        self.sectionCount = self.stream.get_int(1)
        self.obmcLogID = self.stream.get_int(4)
        self.creatorVersion = "0x{:02X}".format(self.stream.get_int(8))
        self.pLID = "0x{:02X}".format(self.stream.get_int(4))
        self.lEID = "0x{:02X}".format(self.stream.get_int(4))

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = "0x{:02X}".format(self.componentID)
        out["Created at"] = self.createTime
        out["Committed at"] = self.committeTime
        out["Creator Subsystem"] = creatorIDs[self.creatorID]
        out["CSSVER"] = self.creatorVersion
        out["Platform Log Id"] = self.pLID
        out["Entry Id"] = self.lEID
        out["BMC Event Log Id"] = str(self.obmcLogID)

        return out
