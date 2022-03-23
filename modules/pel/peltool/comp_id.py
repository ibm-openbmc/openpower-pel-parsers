from pel.peltool.pel_values import creatorIDs
import os
import json

componentIDs = {}


def getCompIDFilePath(creatorID: str) -> str:
    """
    Returns the file path to look up the component ID in.
    The pel_registry module isn't available on the BMC,
    so just look in /usr/share/... if that module isn't present.
    """
    try:
        import pel_registry
        file = pel_registry.get_comp_id_file_path(creatorID)
    except ModuleNotFoundError:
        # Use the BMC path
        basePath = '/usr/share/phosphor-logging/pels/'
        name = creatorID + '_component_ids.json'
        file = os.path.join(os.path.join(basePath, name))

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
        compIDFile = getCompIDFilePath(creatorID)
        if os.path.exists(compIDFile):
            with open(compIDFile, 'r') as file:
                componentIDs[creatorID] = json.load(file)

    compIDStr = '{:04X}'.format(componentID).upper()
    if creatorID in componentIDs and compIDStr in componentIDs[creatorID]:
        return componentIDs[creatorID][compIDStr]

    return "{:04X}".format(componentID)
