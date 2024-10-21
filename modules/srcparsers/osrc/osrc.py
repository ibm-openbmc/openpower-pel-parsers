import importlib
import json

osrcParsers = {}

def parseSRCToJson(refcode: str,
                   word2: str, word3: str, word4: str, word5: str,
                   word6: str, word7: str, word8: str, word9: str) -> str:
    """
    SRC parser for BMC generated PELs.

    This returns a string containing formatted JSON data. The data is simply
    appended to the end of the "Primary SRC" section of the PEL and will not
    impact any other fields in that section.

    IMPORTANT:
    This function is simply a wrapper for component SRC parsers. To define a
    parser for a component, create an SRC parser module with a path in the
    following format:

        srcparsers/<subsystem><component>/<subsystem><component>.py

    Where the <subsystem> is 'o' for the BMC and <component> is the four
    character component ID in the format `xx00`, where `xx` is the component ID
    in lower case (example: e500). Then add this same function definition to
    the new module.
    """

    # Need to search for the SRC parser modules for this component. The
    # component ID can be pulled from the third byte of the reference code.
    subsystem = 'o'
    component = subsystem + refcode[4:6].lower() + '00'
    module_name = '.'.join(['srcparsers', component, component])

    # There is a special case, like a hostboot TI, where the BMC will create
    # a PEL with a hostboot SRC.  When that happens, route it through the
    # hostboot SRC parser instead.
    if refcode[:2] == 'BC':
        name = 'bsrc'
        module_name = '.'.join(['srcparsers', name, name])

    try:
        if module_name in osrcParsers:
            module = osrcParsers[module_name]
        else:
            # Grab the module if it exist. If not, it will throw an exception.
            module = importlib.import_module(module_name)
            osrcParsers[module_name] = module
    except ModuleNotFoundError:
        osrcParsers[module_name] = None
        # The module does not exist. No need to parse the SRC. Using
        # 'json.dumps()' here so that it returns the JSON 'null' value.
        out = json.dumps(None)

    else:
        if module is None:
            # The module, which was previously checked, is not found.
            out = json.dumps(None)
        else:
            # The module was found. Call the component parser in that module.
            out = module.parseSRCToJson(refcode,
                                        word2, word3, word4, word5,
                                        word6, word7, word8, word9)

    return out