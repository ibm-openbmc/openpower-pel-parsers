#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import json
import argparse
import syslog
from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.private_header import PrivateHeader
from pel.peltool.user_header import UserHeader
from pel.peltool.src import SRC
from pel.peltool.pel_types import SectionID, SeverityValues
from pel.peltool.extend_user_header import ExtendedUserHeader
from pel.peltool.failing_mtms import FailingMTMS
from pel.peltool.user_data import UserData
from pel.peltool.ext_user_data import ExtUserData
from pel.peltool.default import Default
from pel.peltool.imp_partition import ImpactedPartition
from pel.peltool.pel_values import sectionNames, severityGroupValues
from pel.peltool.config import Config
from pel.hexdump import hexdump


def getSectionName(sectionID: int) -> str:
    id = chr((sectionID >> 8) & 0xFF) + chr(sectionID & 0xFF)
    return sectionNames.get(id, 'Unknown')


def parseHeader(stream: DataStream):
    sectionID = stream.get_int(2)
    sectionLen = stream.get_int(2)
    versionID = stream.get_int(1)
    subType = stream.get_int(1)
    componentID = stream.get_int(2)
    return sectionID, sectionLen, versionID, subType, componentID


def generatePH(stream: DataStream, out: OrderedDict) -> (bool, PrivateHeader):
    sectionID, sectionLen, versionID, subType, componentID = parseHeader(
        stream)
    if sectionID != SectionID.privateHeader.value:
        print("Failed to parse Private Header, section ID = %x" % (sectionID), file=sys.stderr)
        return False, None

    ph = PrivateHeader(stream, sectionID, sectionLen,
                       versionID, subType, componentID)
    out[getSectionName(sectionID)] = ph.toJSON()
    return True, ph


def generateUH(stream: DataStream, creatorID: str, out: OrderedDict) -> (bool, UserHeader):
    sectionID, sectionLen, versionID, subType, componentID = parseHeader(
        stream)
    if sectionID != SectionID.userHeader.value:
        print("Failed to parse User Header, section ID = %d" % (sectionID), file=sys.stderr)
        return False, None

    uh = UserHeader(stream, sectionID, sectionLen,
                    versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = uh.toJSON()
    return True, uh


def generateSRC(stream: DataStream, out: OrderedDict,
                sectionID: int, sectionLen: int, versionID: int, subType: int,
                componentID: int, creatorID: str, config: Config) -> (bool, SRC):
    src = SRC(stream, sectionID, sectionLen,
              versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = src.toJSON(config)
    return True, src


def generateEH(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str) -> (bool, ExtendedUserHeader):
    eh = ExtendedUserHeader(stream, sectionID, sectionLen,
                            versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = eh.toJSON()
    return True, eh


def generateMT(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str) -> (bool, FailingMTMS):
    mt = FailingMTMS(stream, sectionID, sectionLen,
                     versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = mt.toJSON()
    return True, mt


def generateED(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, config: Config) -> (bool, ExtUserData):
    ed = ExtUserData(stream, sectionID, sectionLen,
                     versionID, subType, componentID)
    out[getSectionName(sectionID)] = ed.toJSON(config)
    return True, ed


def generateUD(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str,
               config: Config) -> (bool, UserData):
    ud = UserData(stream, sectionID, sectionLen, versionID,
                  subType, componentID, creatorID)

    out[getSectionName(sectionID)] = ud.toJSON(config)
    return True, ud


def generateIP(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str) -> (bool, ExtUserData):
    ip = ImpactedPartition(stream, sectionID, sectionLen,
                           versionID, subType, componentID,
                           creatorID)
    out[getSectionName(sectionID)] = ip.toJSON()
    return True, ip


def generateDefault(stream: DataStream, out: OrderedDict, sectionID: int,
                    sectionLen: int, versionID: int, subType: int,
                    componentID: int) -> (bool, ExtUserData):
    ed = Default(stream, sectionID, sectionLen,
                 versionID, subType, componentID)
    out[getSectionName(sectionID)] = ed.toJSON()
    return True, ed


def sectionFun(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str, config: Config):
    if sectionID == SectionID.primarySRC.value or \
            sectionID == SectionID.secondarySRC.value:
        generateSRC(stream, out, sectionID, sectionLen,
                    versionID, subType, componentID, creatorID, config)
    elif sectionID == SectionID.extendedUserHeader.value:
        generateEH(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.failingMTMS.value:
        generateMT(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.extUserData.value:
        generateED(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, config)
    elif sectionID == SectionID.userData.value:
        generateUD(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID, config)
    elif sectionID == SectionID.impactedPart.value:
        generateIP(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
    else:
        generateDefault(stream, out, sectionID, sectionLen,
                        versionID, subType, componentID)


def buildOutput(sections: list, out: OrderedDict):
    counts = {}

    # Find the section names that appear more than once.
    # counts[section name] = [# occurrences, counter]
    for section_num in range(len(sections)):
        name = list(sections[section_num].keys())[0]
        if name not in counts:
            counts[name] = [1, 0]
        else:
            counts[name] = [counts[name][0]+1, 0]

    # For sections that appear more than once, add a
    # ' <count>' to the name, eg 'User Data 1'.
    for section_num in range(len(sections)):
        name = list(sections[section_num].keys())[0]

        if counts[name][0] == 1:
            out[name] = sections[section_num][name]
        else:
            modifier = counts[name][1]
            out[name + ' ' + str(modifier)] = sections[section_num][name]
            counts[name][1] = modifier + 1


def prettyPrint(Mdata: str, desiredSpace: int = 34) -> str:
    # After index of these 2 characters ":  need to add desired space.
    CHARACTER_SPACE = 2
    lines = Mdata.split("\n")
    for i in range(len(lines)):
        line = lines[i]
        if "\":" in line and "{" not in line:
            ind = line.index("\":")
            spaces = (desiredSpace - ind) * " "    # Calculating spaces needed to add to get the desired spacing.
            ind += CHARACTER_SPACE
            lines[i] = line[:ind] + spaces + line[ind:]
    """
    Part of input
        "Section Version": 1,
        "Sub-section type": 0,
    Part of output
        "Section Version":           1,
        "Sub-section type":          0,
    """
    return '\n'.join(lines)


def considerPELIfSeverityMatches(uh: UserHeader, config: Config) -> bool:
    """
    Determine if a PEL should be considered based on its event severity.
    Returns: True if the PEL severity matches with the given severity list,
             False otherwise.
    """
    for sev in config.severities:
        if hex(uh.eventSeverity).startswith(hex(sev)):
            return True
    return False

def considerPEL(uh: UserHeader, config: Config) -> bool:
    """
    Evaluates whether a PEL meets criteria based on given option(s).
    Returns True if the PEL should be considered, False otherwise.
    """

    if config.every_pel:
        return True

    if config.critSysTerm and uh.eventSeverity == SeverityValues.critSysTermSeverity.value:
        return True

    if config.serviceable and uh.isServiceable():
        if config.only and config.severities and not considerPELIfSeverityMatches(uh, config):
            """
            Only consider matched serviceable severities PELs;
            disregard the rest.
            """
            return False
        return True

    if config.non_serviceable and not uh.isServiceable():
        if config.only and config.severities and not considerPELIfSeverityMatches(uh, config):
            """
            Only consider matched non-serviceable severities PELs;
            disregard the rest.
            """
            return False
        return True

    if config.hidden and uh.isHidden():
        if config.only and config.severities and not considerPELIfSeverityMatches(uh, config):
            """
            Only consider matched hidden severities PELs;
            disregard the rest.
            """
            return False
        return True
    
    if config.severities and considerPELIfSeverityMatches(uh, config):
        if config.only and (config.serviceable or
                            config.non_serviceable or
                            config.hidden):
            """
            Only consider matched severities PELs if no serviceable,
            non-serviceable, or hidden PELs are expected.
            """
            return False
        return True

    """
    Having verified each criteria options individually, reaching this point
    indicates that the PEL does not satisfy the criteria for any
    selected option.
    Therefore, check if the "--only" option is used to determine
    whether include serviceable PELs as the default case (i.e
    hidden and non-serviceable PELs should not be included)

    If "Yes", the serviceable PEL cannot be included.
    If "No", the serviceable PEL can be included.
    """
    if config.only or uh.isHidden() or not uh.isServiceable():
        # Ignore hidden/non-serviceable PELs check for the
        # --plid and --src option and --id and --bmc-id
        if config.plid or config.src or config.bmcID or config.pelID:
            return True
        return False

    return True

def parsePEL(stream: DataStream, config: Config, exit_on_error: bool):
    out = OrderedDict()

    ret, ph = generatePH(stream, out)
    if ret is False:
        if exit_on_error:
            sys.exit(1)
        else:
            return "", ""

    eid = ph.lEID
    if eid[0:2] == "0x" :
        eid = eid[2:]

    ret, uh = generateUH(stream, ph.creatorID, out)
    if ret is False:
        if exit_on_error:
            sys.exit(1)
        else:
            return "", ""

    if not considerPEL(uh, config):
        return "", ""

    section_jsons = []
    for _ in range(2, ph.sectionCount):
        sectionID, sectionLen, versionID, subType, componentID = parseHeader(
            stream)
        section_json = OrderedDict()
        sectionFun(stream, section_json, sectionID, sectionLen,
                   versionID, subType, componentID, ph.creatorID, config)
        section_jsons.append(section_json)

    buildOutput(section_jsons, out)

    return eid, prettyPrint(json.dumps(out, indent=4))


def parseAndWriteOutput(file: str, output_dir: str, config: Config,
                        delete_after_parsing: bool) -> None:

    with open(file, 'rb') as fd:
        data = fd.read()
        stream = DataStream(data, byte_order='big', is_signed=False)

        try:
            eid, json_string = parsePEL(stream, config, False)

            if len(json_string) != 0:
                output_file = os.path.join(
                    output_dir, os.path.basename(file) + '.' + eid + '.json')

                with open(output_file, "w") as output:
                    output.writelines(json_string)

                    if delete_after_parsing:
                        os.remove(file)
            else:
                print(f"No PEL parsed for {file}")
        except Exception as e:
            print(f"No PEL parsed for {file}: {e}", file=sys.stderr)


def deleteAllPELs(path: str) -> None:
    """
    Delete all files in given path
    Returns: None
    """
    syslog.syslog(syslog.LOG_INFO, 'peltool deleting all event logs')
    root = ""
    for root, _, files in os.walk(path):
        for file in files:
            if not os.path.isfile(os.path.join(root, file)):
                continue
            os.remove(os.path.join(root, file))
        # Only process top level directory
        break


def processId(pid: str) -> str:
    """
    Processes a string by converting it to uppercase and removing the "0X" prefix if present.
    Returns: str: Processed ID string.
    """
    # For Entry ID and Platform Log ID the default length is 8.
    DEFAULT_ID_LENGTH = 8
    pid = pid.upper()
    if pid.startswith("0X"):
        pid = pid[2:]
    if len(pid) != DEFAULT_ID_LENGTH:
        sys.exit("Invalid length of ID is provided!")
    return pid 

def deletePELFromPELId(path: str, pelID: str) -> None:
    """
    Search the PEL id in the given path and delete it.
    Returns: None
    """
    pelID = processId(pelID)
    foundID = False
    root = ""
    for root, _, files in os.walk(path):
        for file in files:
            if pelID not in file:
                continue
            os.remove(os.path.join(root, file))
            foundID = True
            break
        # Only process top level directory
        break
    if not foundID:
        print("PEL not found")


def parseAndPrintPELFile(file_path: str, config: Config, exit_on_error: bool) -> None:
    """
    Parses a PEL file and prints the JSON string representation.
    Returns: None
    """
    try:
        with open(file_path, 'rb') as fd:
            data = fd.read()
            stream = DataStream(data, byte_order='big', is_signed=False)
            _, json_string = parsePEL(stream, config, exit_on_error)
            if json_string:
                if not config.hex:
                    print(json_string)        
                else:
                    printPELInHexFormat(data)
    except Exception as e:
        print(f"Exception: No PEL parsed for {file_path}: {e}", file=sys.stderr)


def parsePelFromID(path: str, config: Config) -> None:
    """
    Search the PEL id in the given path and prints the details.
    Returns: None
    """
    pelID = processId(config.pelID)
    foundID = False
    root = ""
    for root, _, files in os.walk(path):
        for file in files:
            if pelID not in file:
                continue
            parseAndPrintPELFile(os.path.join(root, file), config, False)
            foundID = True
            break
        # Only process top level directory
        break
    if not foundID:
        print("PEL not found")


def parsePelFromBmcID(path: str, config: Config) -> None:
    """
    Search the PEL with given BMC Event ID in the given path and prints the details.
    Returns: None
    """
    foundID = False
    root = ""
    for root, _, files in os.walk(path):
        for file in files:
            try:
                with open(os.path.join(root, file), 'rb') as fd:
                    data = fd.read()
                    stream = DataStream(data, byte_order='big', is_signed=False)
                    out = OrderedDict()
                    _, ph = generatePH(stream, out)
                    if str(ph.obmcLogID) == config.bmcID:
                        stream = DataStream(data, byte_order='big', is_signed=False)
                        _, json_string = parsePEL(stream, config, False)
                        if json_string:
                            if not config.hex:
                                print(json_string)
                            else:
                                printPELInHexFormat(data)
                        foundID = True
                        break
            except Exception as e:
                print(f"Exception: Could not read PEL file {file}: {e}", file=sys.stderr)
        # Only process top level directory
        break
    if not foundID:
        print("PEL not found")


def parsePelFromPLID(path: str, config: Config):
    """
    Parse and display PELs matching with the input PLID from the specified directory.
    Returns: None
    Prints a JSON-formatted string containing valid PELs in the specified directory.
    """
    plid = processId(config.plid)
    root, file_list = getFileList(path, config.extension, config.rev)
    final_summary = {}
    for file in file_list:
        with open(os.path.join(root, file), 'rb') as fd:
            data = fd.read()
            stream = DataStream(data, byte_order='big', is_signed=False)
            try:
                eid, summary = parsePELSummary(stream, config)
                if eid :
                    if plid in summary['PLID']:
                        if config.hex:
                            printPELInHexFormat(data)
                        else:
                            final_summary[eid] = summary
            except Exception as e:
                print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)
    if not config.hex:
        print(prettyPrint(json.dumps(final_summary, indent=4) , desiredSpace = 29))


def parsePelFromSRCID(path: str, config: Config):
    """
    Parse and display PELs matching with the input SRC ID from the specified directory.
    Returns: None
    Prints a JSON-formatted string containing valid PELs in the specified directory.
    """
    if config.src:
        if len(config.src) > 32:
            sys.exit('Invalid SRC length is provided!')

    if config.srcExcludeFile:
        with open(config.srcExcludeFile, 'r') as fd:
            src_exclude_file_data = fd.read()

    root, file_list = getFileList(path, config.extension, config.rev)
    final_summary = {}
    for file in file_list:
        with open(os.path.join(root, file), 'rb') as fd:
            data = fd.read()
            stream = DataStream(data, byte_order='big', is_signed=False)
            try:
                eid, summary = parsePELSummary(stream, config)
                if eid :
                    if config.src and config.src in summary['SRC']:
                        if config.hex:
                            printPELInHexFormat(data)
                        else:
                            final_summary[eid] = summary
                    if (config.srcExcludeFile):
                        if summary['SRC'] not in src_exclude_file_data:
                            if config.hex:
                                printPELInHexFormat(data)
                            else:
                                final_summary[eid] = summary

            except Exception as e:
                print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)
    if not config.hex:
        print(prettyPrint(json.dumps(final_summary, indent=4) , desiredSpace = 29))


def parsePELSummary(stream: DataStream, config: Config):
    """
    Parses and summarizes data from a PEL stream.
    Returns: Event ID (eid) and summary of PEL data.
            If no PEL is parsed or an error occurs, empty strings are returned.
    """
    out = OrderedDict()
    ret, ph = generatePH(stream, out)
    if ret is False:
        return "", ""
    eid = ph.lEID
    ret, uh = generateUH(stream, ph.creatorID, out)
    if ret is False:
        return "", ""
    if not considerPEL(uh, config):
        return "", ""

    summary = OrderedDict()
    for _ in range(2, ph.sectionCount):
        sectionID, sectionLen, versionID, subType, componentID = parseHeader(stream)
        section_json = OrderedDict()
        sectionFun(stream, section_json, sectionID, sectionLen,
                   versionID, subType, componentID, ph.creatorID, config)
        if sectionID == SectionID.primarySRC.value:
            summary["SRC"] = section_json["Primary SRC"]["Reference Code"]
            if "Error Details" in section_json["Primary SRC"] :
                summary["Message"] = section_json["Primary SRC"]["Error Details"]["Message"]
            break
    summary["PLID"] = ph.pLID
    summary["CreatorID"] = out["Private Header"]["Creator Subsystem"]
    summary["Subsystem"] = out["User Header"]["Subsystem"]
    summary["Commit Time"] = ph.commitTime
    summary["Sev"] = out["User Header"]["Event Severity"]
    summary["CompID"] = out["Private Header"]["Created by"]
    return eid, summary

def extractAndSummarizePEL(file: str, config: Config):
    """
    Extracts and summarizes data from a PEL file.
    Returns: Event ID (eid) and summary extracted from the PEL.
            If no PEL is parsed, empty strings are returned.
    """
    with open(file, 'rb') as fd:
        data = fd.read()
        stream = DataStream(data, byte_order='big', is_signed=False)
        try:
            eid, summary = parsePELSummary(stream, config)
            if eid :
                if config.hex:
                    printPELInHexFormat(data)
                else:
                    return eid, summary
        except Exception as e:
            print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)
    return "", ""


def getFileList(path: str, extension: str, rev: bool = False):
    """
    Reads the passed folder path and creates a list of file names in the top level
    Returns: list of file name
    """
    file_list = []
    root = ""
    for root, _, files in os.walk(path):
        for file in files:
            if extension and extension != os.path.splitext(file)[1]:
                continue
            file_list.append(file)  ## create list of file names
        # Only process top level directory
        break
    file_list.sort(reverse=rev)
    return root, file_list

def listOption(path: str, config: Config):
    root, file_list = getFileList(path, config.extension, config.rev)
    final_summary = {}
    for file in file_list:
        eid, summary = extractAndSummarizePEL(os.path.join(root, file), config)
        if eid :
            final_summary[eid] = summary
    if not config.hex:
        print(prettyPrint(json.dumps(final_summary, indent=4) , desiredSpace = 29))

def extractAllPELsData(path: str, config: Config):
    """
    Extracts and display serviceable PELs data from files in the specified directory.
    Returns: None.
    Prints a JSON-formatted string containing PEL data from all valid files.
    """
    root, file_list = getFileList(path, config.extension, config.rev)
    if not config.hex:
        print("[")
    firstPELPrinted = False
    for file in file_list:
        with open(os.path.join(root, file), 'rb') as fd:
            data = fd.read()
            try:
                stream = DataStream(data, byte_order='big', is_signed=False)
                _, json_string = parsePEL(stream, config, False)
                if json_string:
                    if not config.hex:
                        if firstPELPrinted:
                            print(",")
                        print(json_string, end = "")
                        firstPELPrinted = True
                    else:
                        printPELInHexFormat(data)
            except Exception as e:
                print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)
    if not config.hex:
        if firstPELPrinted:
            print()
        print("]")


def printPELInHexFormat(data: memoryview) -> None:
    """
    Read single PEL file data and display in hexdecimal format.
    Returns: None
    Prints PEL data in the hexdecimal format.
    """
    try:
        mv = memoryview(data)
        hexdata = hexdump(mv)
        # Add line seperator for PELs in hexadecimal format.
        print("-------------- PEL Begin  ----------------")
        for line in hexdata:
            print(line)
        print("-------------- PEL End    ----------------")
    except Exception as e:
        print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)


def printPELCount(path: str, config: Config):
    """
    Reads and display serviceable PEL count from the specified directory.
    Returns: None
    Prints a JSON-formatted string containing count of valid PELs in specified directory.
    """
    count = 0
    root, file_list = getFileList(path, config.extension)
    for file in file_list:
        with open(os.path.join(root, file), 'rb') as fd:
            data = fd.read()
            stream = DataStream(data, byte_order='big', is_signed=False)
            try:
                out = OrderedDict()
                ret, ph = generatePH(stream, out)
                if not ret:
                    continue
                ret, uh = generateUH(stream, ph.creatorID, out)
                if not ret:
                    continue
                if not considerPEL(uh, config):
                    continue
                count+= 1
            except Exception as e:
                print(f"Exception: No PEL parsed for {file}: {e}", file=sys.stderr)
    print("{\n    \"Number of PELs found\": "+str(count)+"\n}")


class CustomFormatter(argparse.RawDescriptionHelpFormatter):
    """
    This class is to enhance the formatting of argparse help messages 
    for arguments that have choices and allow multiple values.
    """
    def _format_action(self, action):
        # Override the default formatting for choices when nargs='+' is used
        if action.choices and action.nargs == '+':
            metavar = self._get_default_metavar_for_optional(action)
            # Construct option string with metavar
            option = f'{action.option_strings[0]} {metavar}, {action.option_strings[1]} {metavar}'
            help_text = self._expand_help(action)
            # Format choices into a more readable list
            choices_str = ', '.join(action.choices)
            # Return formatted string for the action
            return f"  {option}\n\t\t\t{help_text}\n\t\t\tChoose from: {{{choices_str}}}." + \
                   f"\n\t\t\tCan choose multiple values.\n"
        return super()._format_action(action)


def main():
    PELsPath = "/var/lib/phosphor-logging/extensions/pels/logs/"
    PELsArchivePath = "/var/lib/phosphor-logging/extensions/pels/logs/archive"
    inBMC = os.path.isdir(PELsPath)

    peltool_cmd = os.path.basename(sys.argv[0])
    if not inBMC:
        peltool_cmd = peltool_cmd + " -p <pel_dir>"
    example_text = '''Examples:
        -------------------------

        List servicable PELs: {0} -l
        List informational PELs along with serviceable PELs: {0} -l -S Informational
        List every PEL irrespective of its type: {0} -l -E
        List only hidden PELs: {0} -l -H -O
        List only unrecoverable PELs: {0} -l -O -S Unrecoverable
        Count only hidden PELs: {0} -n -H -O
        Count only predictive PELs: {0} -n -O -S Predictive
        Display servicable PELs data: {0} -a
        Display recovered PELs along with serviceable PELs data: {0} -a -S Recovered
        Display only hidden PELs data: {0} -a -H -O
        Display only critical PELs data: {0} -a -O -S Critical
        '''.format(peltool_cmd)

    parser = argparse.ArgumentParser(formatter_class=CustomFormatter,
                                     description="PELTools", epilog=example_text)
    if not inBMC:
        parser.add_argument('-p', '--path', dest='path',
                            metavar='</path/to/pel/files/>',
                            help='Specify the path to parse PELs')
    else:
        parser.add_argument('-A', '--archive', action='store_true',
                            help='Fetch PEL(s) details from the archived path')

    parser.add_argument('-P', '--skip-parser-plugins', dest='skip_plugins',
                        action='store_true', help='Skip loading PEL parser plugins')

    parser.add_argument('-f', '--file', dest='file',
                        metavar='</path/to/pel/file>',
                        help='Input PEL file to extract PEL data')

    parser.add_argument('-l', '--list', action='store_true',
                        help='List PELs')
    parser.add_argument('-a', '--all-pels', dest='all', action='store_true',
                        help='Display all PELs data')
    parser.add_argument('-n', '--show-pel-count', dest='show_pel_count',
                        action='store_true', help='Show number of PELs')
    parser.add_argument('-d', '--delete', dest='IDToDelete',
                        metavar='<EID>', help='Delete a PEL based on its EID') 
    parser.add_argument('-D', '--delete-all', dest='deleteAll', action='store_true',
                        help='Delete all PELs')
    parser.add_argument('-i', '--id', dest='pelID', metavar='<EID>',
                        help='Display a PEL data based on its EID')
    parser.add_argument('--bmc-id', dest='bmcID',
                        metavar='<BMC_Event_Log_Id>',
                        help='Display a PEL data based on its BMC Event Log ID')
    parser.add_argument('--plid', dest='plID', metavar='<Platform_Log_Id>',
                        help='Display PELs summary based on its Platform Log ID')
    parser.add_argument('--src', dest='src', metavar='<System_Refrence_Code>',
                        help='Display PELs summary based on its System Reference Code')
    parser.add_argument('--src-exclude', dest='src_exclude_file',
                        metavar='<SRC_Exclude_file>', help='Display PELs summary excluding SRCs from the file')
    parser.add_argument('-x', '--hex', action='store_true',
                        help='Display PEL(s) in hexdump instead of JSON')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='Reverse order of output')
    parser.add_argument('-e', '--extension', dest='extension', metavar='<.extension>',
                        help='Search only for files with the specified extension (e.g., ".pel", ".txt")')

    # Exclusive peltool options
    pelExclusive = parser.add_argument_group('Exclusive options to get PELs',
                                             'Use below options along with -l/--list, '
                                             '-a/--all, -n/--show-pel-count options. '
                                             'Check example usage')
    pelExclusive.add_argument('-E', '--every-pel', action='store_true',
                              help='Operate on every single PEL')
    pelExclusive.add_argument('-s', '--serviceable', action='store_true',
                              help='Get Serviceable PELs')
    pelExclusive.add_argument('-N', '--non-serviceable', action='store_true',
                              help='Get Non-Serviceable PELs')
    pelExclusive.add_argument('-H', '--hidden', action='store_true',
                              help='Get hidden PELs')
    pelExclusive.add_argument('-t', '--termination', dest='critSysTerm', action='store_true',
                              help='Get critical system terminating PELs')
    pelExclusive.add_argument('-S', '--severities', nargs='+',
                              choices=list(severityGroupValues.keys()),
                              help=f'Filter by severity value')
    pelExclusive.add_argument('-O', '--only', action='store_true',
                              help='Include only PELs that match the selected options')
   
    # JSON specific options
    jsonPELsData = parser.add_argument_group('PEL data in JSON format',
                                             'Use to get and store PEL data in '
                                             'a JSON file/directory')
    jsonPELsData.add_argument('-j', '--json', action='store_true',
                              help='Process all files in a given input path or default PELs path '
                              'and save as <filename>.json. Use -o to specify output directory')
    jsonPELsData.add_argument('-o', '--output-dir', dest='output_dir',
                              metavar='</path/to/put/processed/pel/json/files>',
                              help='Stores the processed PEL JSON files in the specified output directory')
    jsonPELsData.add_argument('-c', '--clean', dest='clean', action='store_true',
                              help='Delete the original file after parsing')

    args = parser.parse_args()

    config = Config()

    if args.skip_plugins:
        config.allow_plugins = False

    if args.serviceable:
        config.serviceable = True

    if args.non_serviceable:
        config.non_serviceable = True

    if args.critSysTerm:
        config.critSysTerm = True

    if args.hidden:
        config.hidden = True

    if args.only:
        config.only = True

    if args.every_pel:
        config.every_pel = True

    if args.severities:
        config.severities.extend(severityGroupValues[sev] for sev in args.severities)

    if args.hex:
        config.hex = True

    if args.reverse:
        config.rev = True

    if args.extension:
        config.extension = args.extension

    if args.file:
        config.every_pel = True
        parseAndPrintPELFile(args.file, config, True)
        if args.clean:
            os.remove(args.file)
        sys.exit(0)

    if not inBMC:
        if not args.path:
            sys.exit("Outside the BMC environment, please provide the path to the PELs using the -p option.")
        if not os.path.isdir(args.path):
            sys.exit(f"{args.path} is not a valid directory")
        PELsPath = args.path
    else:
        # peltool -A/--archive is specific to BMC only.
        if args.archive:
            PELsPath = PELsArchivePath

    if args.json:
        output_dir = PELsPath
        if args.output_dir:
            if not os.path.isdir(args.output_dir):
                sys.exit(f"Output directory {args.output_dir} doesn't exist")
            output_dir = args.output_dir

        for root, _, files in os.walk(PELsPath):
            for file in files:
                if config.extension and config.extension != os.path.splitext(file)[1]:
                    continue
                parseAndWriteOutput(os.path.join(
                    root, file), output_dir, config,
                    args.clean)
            # Only process top level directory
            break
        sys.exit(0)

    if args.pelID:
        config.pelID = args.pelID
        parsePelFromID(PELsPath, config)
        sys.exit(0)
    
    if args.bmcID:
        config.bmcID = args.bmcID
        parsePelFromBmcID(PELsPath, config)
        sys.exit(0)

    if args.plID:
        config.plid = args.plID
        parsePelFromPLID(PELsPath, config)
        sys.exit(0)

    if args.src:
        config.src = args.src
        parsePelFromSRCID(PELsPath, config)
        sys.exit(0)

    if args.src_exclude_file:
        config.srcExcludeFile = args.src_exclude_file
        if not os.path.isfile(config.srcExcludeFile):
            sys.exit(f"Input {config.srcExcludeFile} file doesn't exist!")
        parsePelFromSRCID(PELsPath, config)
        sys.exit(0)

    if args.list:
        listOption(PELsPath, config)
        sys.exit(0)
    
    if args.show_pel_count:
        printPELCount(PELsPath, config)
        sys.exit(0)

    if args.all:
        extractAllPELsData(PELsPath, config)
        sys.exit(0)

    if args.IDToDelete:
        deletePELFromPELId(PELsPath, args.IDToDelete)
        sys.exit(0)

    if args.deleteAll:
        deleteAllPELs(PELsPath)
        sys.exit(0)


if __name__ == '__main__':
    main()
