from pel.peltool.pel_values import creatorIDs
import os
import json

componentIDs = {}
basePath = '/usr/share/phosphor-logging/pels/'
basePathPresent = os.path.exists(basePath)
overallCheckCompIDFilePath, importSuccess = True, True
checkCompIDFilePath = [overallCheckCompIDFilePath, importSuccess, basePathPresent]

def getCompIDFilePath(creatorID: str) -> str:
    """
    Returns the file path to look up the component ID in.
    The pel_registry module isn't available on the BMC,
    so just look in /usr/share/... if that module isn't present.
    """
    file = basePath
    if checkCompIDFilePath[1]:
        try:
            import pel_registry
            file = pel_registry.get_comp_id_file_path(creatorID)
            return file
        except ModuleNotFoundError:
            checkCompIDFilePath[1] = False
            checkCompIDFilePath[0] = checkCompIDFilePath[2]
    if checkCompIDFilePath[2]:
        # Use the BMC path
        name = creatorID + '_component_ids.json'
        file = os.path.join(basePath, name)
    return file


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
    if creatorID not in componentIDs:
        if checkCompIDFilePath[0]:
            compIDFile = getCompIDFilePath(creatorID)
            if os.path.exists(compIDFile):
                with open(compIDFile, 'r') as file:
                    componentIDs[creatorID] = json.load(file)

    compIDStr = '{:04X}'.format(componentID).upper()
    if creatorID in componentIDs and compIDStr in componentIDs[creatorID]:
        return componentIDs[creatorID][compIDStr]

    return "{:04X}".format(componentID)
