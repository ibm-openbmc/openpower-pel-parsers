from pel.datastream import DataStream
from collections import OrderedDict
import json
from pel.peltool.parse_user_data import ParseUserData
from pel.peltool.comp_id import getDisplayCompID


class UserData:
    """
    This represents the User Data section in a PEL.  It is free form data
    that the creator knows the contents of.  The component ID, version,
    and sub-type fields in the section header are used to identify the
    format.
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

    def toJSON(self) -> OrderedDict:

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = getDisplayCompID(self.componentID, self.creatorID)

        parser = ParseUserData(self.creatorID, self.componentID, self.subType,
                               self.versionID, self.data)

        value = parser.parse()

        j = json.loads(value)
        if not isinstance(j, dict):
            out['Data'] = j
        else:
            out.update(j)

        return out
