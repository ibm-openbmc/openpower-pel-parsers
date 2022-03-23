from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import actionFlagsValues, subsystemValues, \
    severityValues, eventTypeValues, eventScopeValues, transmissionStates
from pel.peltool.comp_id import getDisplayCompID


class UserHeader:
    """
    This represents the Private Header section in a PEL.  It is required,
    and it is always the second section.

    The Section base class handles the section header structure that every
    PEL section has at offset zero.

    The fields in this class directly correspond to the order and sizes of
    the fields in the section.
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
        self.eventSubsystem = 0
        self.eventScope = 0
        self.eventSeverity = 0
        self.eventType = 0
        self.reserved4Byte1 = 0
        self.problemDomain = 0
        self.problemVector = 0
        self.actionFlags = 0
        self.states = 0

    def toJSON(self) -> OrderedDict:
        self.eventSubsystem = self.stream.get_int(1)
        self.eventScope = self.stream.get_int(1)
        self.eventSeverity = self.stream.get_int(1)
        self.eventType = self.stream.get_int(1)
        self.reserved4Byte1 = self.stream.get_int(4)
        self.problemDomain = self.stream.get_int(1)
        self.problemVector = self.stream.get_int(1)
        self.actionFlags = self.stream.get_int(2)
        self.states = self.stream.get_int(4)

        list = []
        for key in actionFlagsValues:
            if key & self.actionFlags:
                list.append(actionFlagsValues[key])

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Log Committed by"] = getDisplayCompID(
            self.componentID, self.creatorID)
        out["Subsystem"] = subsystemValues.get(self.eventSubsystem, 'Invalid')
        out["Event Scope"] = eventScopeValues.get(self.eventScope, 'Invalid')
        out["Event Severity"] = severityValues.get(self.eventSeverity, 'Invalid')
        out["Event Type"] = eventTypeValues.get(self.eventType, 'Invalid')
        out["Action Flags"] = list
        out["Host Transmission"] = transmissionStates.get(
            self.states & 0xff, 'Unknown')
        out["HMC Transmission"] = transmissionStates.get(
            (self.states & 0x0000FF00) >> 8, 'Unknown')

        return out
