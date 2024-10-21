from pel.peltool.pel_values import creatorIDs
import os
import json
import sys

componentIDs = {}

pelConfigRootPath = "/usr/share/phosphor-logging/pels"
attemptedToParseCompIDs = False

def getAllCreatorsCompIDs():
    global attemptedToParseCompIDs
    if attemptedToParseCompIDs:
        return

    attemptedToParseCompIDs = True
    componentsConfigPath = ""
    if os.path.exists(pelConfigRootPath): # BMC env
        componentsConfigPath = pelConfigRootPath
    else: # Non-BMC env
        try:
            import pel_registry
            componentsConfigPath = os.path.dirname(pel_registry.__file__)
        except ModuleNotFoundError:
            print("Failed to find PEL creators components config file", file=sys.stderr)
            return

    componentIDFileSuffix = "_component_ids.json"
    for file in os.listdir(componentsConfigPath):
        if componentIDFileSuffix not in file:
            continue
        with open(os.path.join(componentsConfigPath, file), 'r') as fileFd:
            creatorID = file[0:file.find(componentIDFileSuffix)]
            componentIDs[creatorID] = json.load(fileFd)

def getDisplayCompID(componentID: int, creatorID: str) -> str:
    """
    Converts a component ID to a name if possible for display.
    Otherwise it returns the comp id like "0xFFFF"
    """

    # PHYP's IDs are ASCII
    if creatorID in creatorIDs and creatorIDs[creatorID] == "PHYP":
        first = (componentID >> 8) & 0xFF
        second = componentID & 0xFF
        if first != 0 and second != 0:
            return chr(first) + chr(second)

        return "{:04X}".format(componentID)

    # try the comp IDs file named after the creator ID
    if not componentIDs:
        getAllCreatorsCompIDs()

    compIDStr = '{:04X}'.format(componentID)
    if creatorID in componentIDs and compIDStr.upper() in componentIDs[creatorID]:
        return componentIDs[creatorID][compIDStr]

    return compIDStr
