import json

procedures = {
    "BMC0001": [
        "A problem has been detected in the eBMC firmware."
    ],

    "BMC0002": [
        "Save any dump data, and then contact your next level ",
        "of support for assistance."
    ],

    "BMC0003": [
        "A problem was detected in the firmware of the ",
        "system processor module."
    ],

    "BMC0004": [
        "The system detected an error with the firmware of ",
        "a peripheral interface bus."
    ],

    "BMC0005": [
        "A load fault is occurring on a power supply in the system unit."
    ],

    "BMC0006": [
        "A system uncorrectable error has occurred."
    ],

    "BMC0007": [
        "A system data mismatch has been detected."
    ],

    "BMC0008": [
        "Failed parts present in the system. Service needed"
    ],
    "BMC0009": [
        "CEC node does not have input power."
    ],

    "BMC000A": [
        "A BMC failover was blocked."
    ],

    "BMC000B": [
        "BMC redundancy cannot be enabled."
    ],

    "BMC000C": [
        "The BMC must be passive due to an error."
    ]
}


def getMaintProcDesc(procedure: str) -> str:
    if procedure in procedures:
        return json.dumps(procedures[procedure])
    return ''
