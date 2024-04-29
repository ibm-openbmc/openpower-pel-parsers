#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import json
import argparse
from pel.datastream import DataStream
from collections import OrderedDict
from pel.peltool.private_header import PrivateHeader
from pel.peltool.user_header import UserHeader
from pel.peltool.src import SRC
from pel.peltool.pel_types import SectionID
from pel.peltool.extend_user_header import ExtendedUserHeader
from pel.peltool.failing_mtms import FailingMTMS
from pel.peltool.user_data import UserData
from pel.peltool.ext_user_data import ExtUserData
from pel.peltool.default import Default
from pel.peltool.imp_partition import ImpactedPartition
from pel.peltool.pel_values import sectionNames, severityValues
from pel.peltool.config import Config


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
        print("Failed to parse Private Header, section ID = %x" % (sectionID))
        return False, None

    ph = PrivateHeader(stream, sectionID, sectionLen,
                       versionID, subType, componentID)
    out[getSectionName(sectionID)] = ph.toJSON()
    return True, ph


def generateUH(stream: DataStream, creatorID: str, out: OrderedDict) -> (bool, UserHeader):
    sectionID, sectionLen, versionID, subType, componentID = parseHeader(
        stream)
    if sectionID != SectionID.userHeader.value:
        print("Failed to parse User Header, section ID = %d" % (sectionID))
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

    if config.serviceable_only and not uh.isServiceable():
        return "", ""

    if config.non_serviceable_only and uh.isServiceable():
        return "", ""
    
    if config.critSysTerm and uh.eventSeverity != int(config.critSysTerm):
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
            print(f"No PEL parsed for {file}: {e}")


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
    eid = ph.pLID
    ret, uh = generateUH(stream, ph.creatorID, out)
    if ret is False:
        return "", ""
    if not uh.isServiceable():
        return "", ""
    if config.critSysTerm and uh.eventSeverity != int(config.critSysTerm):
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
                return eid, summary
        except Exception as e:
            print(f"Exception: No PEL parsed for {file}: {e}")
    return "", ""

def listOption(path: str, config: Config, extension: str, rev: bool =False):
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
    final_summary = {}
    for file in file_list:
        eid, summary = extractAndSummarizePEL(os.path.join(root, file), config)
        if eid :
            final_summary[eid] = summary
    print(prettyPrint(json.dumps(final_summary, indent=4) , desiredSpace = 29))


def main():
    inBMC=False
    BMCPELsPath="/var/lib/phosphor-logging/extensions/pels/logs/"
    if os.path.isdir(BMCPELsPath):
        inBMC=True
    critSysTermSeverity = "81"
    parser = argparse.ArgumentParser(description="PELTools")

    parser.add_argument('-f', '--file', dest='file',
                        help='input pel file to parse')
    parser.add_argument('-s', '--serviceable',
                        help='Only parse serviceable (not info/recovered) PELs',
                        action='store_true')
    parser.add_argument('-n', '--non-serviceable',
                        help='Only parse non-serviceable (info/recovered) PELs',
                        action='store_true')
    parser.add_argument('-p', '--no-plugins', dest='skip_plugins',
                        action='store_true', help='Skip loading plugins')
    parser.add_argument('-d', '--directory', dest='directory',
                        help='Process all files in a directory and save as <filename>.json.'
                        ' Use -o to specify output directory')
    parser.add_argument('-o', '--output-dir', dest='output_dir',
                        help='Directory to write output files when processing a directory')
    parser.add_argument('-e', '--extension', dest='extension',
                        help='Used with -d, only look for files with this extension (e.g. ".pel")')
    parser.add_argument('-x', '--delete', dest='delete', action='store_true',
                        help='Delete original file after parsing')
    parser.add_argument('-t', '--termination', nargs='?', const=critSysTermSeverity,
                        default=None, help='List only critical system terminating PELs')
    if inBMC:
        parser.add_argument('-l', '--list',
                            help='List PELs',
                            action='store_true')
    else:
        parser.add_argument('-l', '--list',
                            help='List PELs',
                            dest='list')
    args = parser.parse_args()

    config = Config()

    if args.skip_plugins:
        config.allow_plugins = False

    if args.serviceable:
        config.serviceable_only = True

    if args.non_serviceable:
        config.non_serviceable_only = True

    if args.termination:
        if int(args.termination) not in severityValues:
            print(json.dumps(severityValues, indent=4))
            sys.exit(f"{args.termination} is not a valid severity value, choose from above")
        config.critSysTerm = args.termination

    if args.directory:
        if not os.path.isdir(args.directory):
            sys.exit(f"{args.directory} is not a valid directory")

        output_dir = args.directory
        if args.output_dir:
            if not os.path.isdir(args.output_dir):
                sys.exit(f"Output directory {args.output_dir} doesn't exist")

            output_dir = args.output_dir

        for root, _, files in os.walk(args.directory):
            for file in files:
                if args.extension and args.extension != os.path.splitext(file)[1]:
                    continue

                parseAndWriteOutput(os.path.join(
                    root, file), output_dir, config,
                    args.delete)

            # Only process top level directory
            break

        sys.exit(0)

    if args.list:
        if inBMC:
            listOption(BMCPELsPath, config, args.extension)
        else:
            if not os.path.isdir(args.list):
                sys.exit(f"{args.list} is not a valid directory")
            listOption(args.list, config, args.extension)
        sys.exit(0)

    with open(args.file, 'rb') as fd:
        data = fd.read()
        stream = DataStream(data, byte_order='big', is_signed=False)

        _, json_string = parsePEL(stream, config, True)
        print(json_string)

        if args.delete:
            os.remove(args.file)


if __name__ == '__main__':
    main()
