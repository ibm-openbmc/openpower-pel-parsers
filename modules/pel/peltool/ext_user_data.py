from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.parse_user_data import ParseUserData
from pel.peltool.comp_id import getDisplayCompID
from pel.peltool.config import Config
from pel.hexdump import hexdump
import json


class ExtUserData:
    """
    This represents the Extended User Data section in a PEL.  It is free form
    data that the creator knows the contents of.  The component ID, version, and
    sub-type fields in the section header are used to identify the format.

    This section is used for one subsystem to add FFDC data to a PEL created
    by another subsystem.  It is basically the same as a UserData section,
    except it has the creator ID of the section creator stored in the section.
    """

    def __init__(self, stream: DataStream, sectionID: int, sectionLen: int,
                 versionID: int, subType: int, componentID: int):
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.subType = subType
        self.componentID = componentID
        dataLength = sectionLen - 4 - 8
        self.creatorID = chr(stream.get_int(1))
        self.reserved1B = stream.get_int(1)
        self.reserved2B = stream.get_int(2)
        self.data = stream.get_mem(dataLength)

    def toJSON(self, config: Config) -> OrderedDict:
        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Created by"] = getDisplayCompID(self.componentID, self.creatorID)

        parser = ParseUserData(self.creatorID, self.componentID, self.subType,
                               self.versionID, self.data)

        value = parser.parse(config)

        try:
            j = json.loads(value)
        except json.decoder.JSONDecodeError:
            # This should have been valid JSON but if it isn't
            # then hexdump it.
            mv = memoryview(value.encode('utf-8'))
            j = json.loads(json.dumps(hexdump(mv)))

        if not isinstance(j, dict):
            out['Data'] = j
        else:
            out.update(j)

        return out
