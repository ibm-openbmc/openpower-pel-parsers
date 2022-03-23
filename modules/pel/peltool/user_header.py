from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.pel_values import *


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
                 versionID: int, subType: int, componentID: int):
        self.stream = stream
        self.sectionID = sectionID
        self.sectionLen = sectionLen
        self.versionID = versionID
        self.subType = subType
        self.componentID = componentID
        self.eventSubsystem = 0
        self.eventScope = 0
        self.eventSeverity = 0
        self.eventType = 0
        self.reserved4Byte1 = 0
        self.problemDomain = 0
        self.problemVector = 0
        self.actionFlags = 0
        self.states = 0

    def toJSON(self) -> str:
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
                list.append(actionFlagsValues[key][1])

        out = OrderedDict()
        out["Section Version"] = self.versionID
        out["Sub-section type"] = self.subType
        out["Log Committed by"] = "0x{:02X}".format(self.componentID)
        out["Subsystem"] = subsystemValues[self.eventSubsystem][1]
        out["Event Scope"] = eventScopeValues[self.eventScope][1]
        out["Event Severity"] = severityValues[self.eventSeverity][1]
        out["Event Type"] = eventTypeValues[self.eventType][1]
        out["Action Flags"] = list
        out["Host Transmission"] = transmissionStates[self.states & 0xff]
        out["HMC Transmission"] = transmissionStates[(
            self.states & 0x0000FF00) >> 8]

        return out
