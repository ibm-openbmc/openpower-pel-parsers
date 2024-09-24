from pel.peltool.pel_types import TransmissionState

"""
Creator IDs
"""
creatorIDs = {"B": "Hostboot", "C": "HMC", "H": "PHYP", "K": "Sapphire",
              "L": "Partition FW", "M": "I/O Drawer", "O": "BMC",
              "P": "PowerNV", "S": "SLIC",  "T": "OCC"}

"""
Section Names
"""
sectionNames = {
    "PH": "Private Header",
    "UH": "User Header",
    "PS": "Primary SRC",
    "SS": "Secondary SRC",
    "EH": "Extended User Header",
    "MT": "Failing MTMS",
    "DH": "Dump Location",
    "SW": "Firmware Error",
    "LP": "Impacted Partition",
    "LR": "Logical Resource",
    "HM": "HMC ID",
    "EP": "EPOW",
    "IE": "IO Event",
    "MI": "MFG Info",
    "CH": "Call Home",
    "UD": "User Data",
    "EI": "Env Info",
    "ED": "Extended User Data"}

"""
The possible values for the subsystem field  in the User Header.
"""
subsystemValues = {
    0x10: "Processor",
    0x11: "Processor FRU",
    0x12: "Processor Chip Cache",
    0x13: "Processor Unit (CPU)",
    0x14: "Processor Bus Controller",

    0x20: "Memory ",
    0x21: "Memory Controller",
    0x22: "Memory Bus Interface",
    0x23: "Memory DIMM",
    0x24: "Memory Card/FRU",
    0x25: "External Cache",

    0x30: "I/O",
    0x31: "I/O Hub",
    0x32: "I/O Bridge",
    0x33: "I/O bus interface",
    0x34: "I/O Processor",
    0x35: "SMA Hub",
    0x38: "PCI Bridge Chip",

    0x40: "I/O Adapter",
    0x41: "I/O Adapter Communication",
    0x46: "I/O Device",
    0x47: "I/O Device Disk",
    0x4C: "I/O External Peripheral",
    0x4D: "I/O External Peripheral Local Work Station",
    0x4E: "I/O Storage Mezza Expansion",

    0x50: "CEC Hardware",
    0x51: "CEC Hardware - Service Processor A",
    0x52: "CEC Hardware - Service Processor B",
    0x53: "CEC Hardware - Node Controller",
    0x55: "CEC Hardware - VPD Interface",
    0x56: "CEC Hardware - I2C Devices",
    0x57: "CEC Hardware - CEC Chip Interface",
    0x58: "CEC Hardware - Clock",
    0x59: "CEC Hardware - Operator Panel",
    0x5A: "CEC Hardware - Time-Of-Day Hardware",
    0x5B: "CEC Hardware - Memory Device",
    0x5C: "CEC Hardware - Hypervisor<->Service Processor Interface",
    0x5D: "CEC Hardware - Service Network",
    0x5E: "CEC Hardware - Hostboot-Service Processor Interface",

    0x60: "Power/Cooling",
    0x61: "Power Supply",
    0x62: "Power Control Hardware",
    0x63: "Fan (AMD)",
    0x64: "Digital Power Supply",

    0x70: "Miscellaneous",
    0x71: "HMC & Hardware",
    0x72: "Test Tool",
    0x73: "Removable Media",
    0x74: "Multiple Subsystems",
    0x75: "Not Applicable",
    0x76: "Miscellaneous",

    0x7A: "Hypervisor lost communication with service processor",
    0x7B: "Service processor lost communication with Hypervisor",
    0x7C: "Service processor lost communication with HMC",
    0x7D: "HMC lost communication with logical partition",
    0x7E: "HMC lost communication with BPA",
    0x7F: "HMC lost communication with another HMC",

    0x80: "Platform Firmware",
    0x81: "Service Processor Firmware",
    0x82: "System Hypervisor Firmware",
    0x83: "Partition Firmware",
    0x84: "SLIC Firmware",
    0x85: "System Power Control Network Firmware",
    0x86: "Bulk Power Firmware Side A",
    0x87: "HMC Code",
    0x88: "Bulk Power Firmware Side B",
    0x89: "Virtual Service Processor Firmware",
    0x8A: "HostBoot",
    0x8B: "OCC",
    0x8D: "BMC Firmware",

    0x90: "Software",
    0x91: "Operating System software",
    0x92: "XPF software",
    0x93: "Application software",

    0xA0: "External Environment",
    0xA1: "Input Power Source (ac)",
    0xA2: "Room Ambient Temperature",
    0xA3: "User Error",
    0xA4: "Corrosion"}


"""
The possible values for the Event Scope field in the User Header.
"""
eventScopeValues = {
    0x01: "Single Partition",
    0x02: "Multiple Partitions",
    0x03: "Entire Platform",
    0x04: "Multiple Platforms"}


"""
The possible values for the Event Type field in the User Header.
"""
eventTypeValues = {
    0x00: "Not Applicable",
    0x01: "Miscellaneous, Informational Only",
    0x02: "Tracing Event",
    0x08: "Dump Notification",
    0x30: "Customer environmental problem back to normal"}


"""
The possible values for the severity field in the User Header.
"""
severityValues = {
    0x00: "Informational Event",

    0x10: "Recovered Error",
    0x20: "Predictive Error",
    0x21: "Predictive Error, Degraded Performance",
    0x22: "Predictive Error, Correctable",
    0x23: "Predictive Error, Correctable, Degraded",
    0x24: "Predictive Error, Redundancy Lost",

    0x40: "Unrecoverable Error",
    0x41: "Unrecoverable Error, Degraded Performance",
    0x44: "Unrecoverable Error, Loss of Redundancy",
    0x45: "Unrecoverable, Loss of Redundancy + Performance",
    0x48: "Unrecoverable Error, Loss of Function",

    0x50: "Critical Error, Scope of Failure unknown",
    0x51: "Critical Error, System Termination",
    0x52: "Critical Error, System Failure likely or imminent",
    0x53: "Critical Error, Partition(s) Termination",
    0x54: "Critical Error, Partition(s) Failure likely or imminent",

    0x60: "Error detected during diagnostic test",
    0x61: "Diagostic error, resource w/incorrect results",

    0x71: "Symptom Recovered",
    0x72: "Symptom Predictive",
    0x74: "Symptom Unrecoverable",
    0x75: "Symptom Critical",
    0x76: "Symptom Diag Err"}


"""
The possible severity groups with there distinct starting hex digit. 
"""
severityGroupValues = {
    'Informational': 0, 
    'Recovered':     1, 
    'Predictive':    2, 
    'Unrecoverable': 4, 
    'Critical':      5, 
    'Diagnostic':    6, 
    'Symptom':       7}


"""
The possible values for the Action Flags field in the User Header.
"""
actionFlagsValues = {
    0x8000: "Service Action Required",
    0x4000: "Event not customer viewable",
    0x2000: "Report Externally",
    0x1000: "Do Not Report To Hypervisor",
    0x0800: "HMC Call Home",
    0x0400: "Isolation Incomplete, further analysis required",
    0x0100: "Service Processor Call Home Required",
    0x0020: "Heartbeat Call Home Event"}

"""
Map for transmission states
"""
transmissionStates = {
    TransmissionState.newPEL.value: "Not Sent",
    TransmissionState.badPEL.value: "Rejected",
    TransmissionState.sent.value: "Sent",
    TransmissionState.acked.value: "Acked"}

"""
Map for Callout Failing Component Types
"""
failingComponentType = {
    0x10: "Normal Hardware FRU",
    0x20: "Code FRU",
    0x30: "Configuration error, configuration procedure required",
    0x40: "Maintenance Procedure Required",
    0x90: "External FRU",
    0xA0: "External Code FRU",
    0xB0: "Tool FRU",
    0xC0: "Symbolic FRU",
    0xE0: "Symbolic FRU with trusted location code"}

"""
The possible values for the Callout Priority field in the SRC.
"""
calloutPriorityValues = {
    0x48: "Mandatory, replace all with this type as a unit",
    0x4D: "Medium Priority",
    0x41: "Medium Priority A, replace these as a group",
    0x42: "Medium Priority B, replace these as a group",
    0x43: "Medium Priority C, replace these as a group",
    0x4C: "Lowest priority replacement"}
