#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
from pel.peltool.pel_values import sectionNames


def getSectionName(sectionID: int) -> str:
    id = chr((sectionID >> 8) & 0xFF) + chr(sectionID & 0xFF)
    return sectionNames.get(id, 'Unknown')


def parserHeader(stream: DataStream):
    sectionID = stream.get_int(2)
    sectionLen = stream.get_int(2)
    versionID = stream.get_int(1)
    subType = stream.get_int(1)
    componentID = stream.get_int(2)
    return sectionID, sectionLen, versionID, subType, componentID


def generatePH(stream: DataStream, out: OrderedDict) -> (bool, PrivateHeader):
    sectionID, sectionLen, versionID, subType, componentID = parserHeader(
        stream)
    if sectionID != SectionID.privateHeader.value:
        print("Failed to parser Private Header, section ID = %x" % (sectionID))
        return False, None

    ph = PrivateHeader(stream, sectionID, sectionLen,
                       versionID, subType, componentID)
    out[getSectionName(sectionID)] = ph.toJSON()
    return True, ph


def generateUH(stream: DataStream, creatorID: str, out: OrderedDict) -> (bool, UserHeader):
    sectionID, sectionLen, versionID, subType, componentID = parserHeader(
        stream)
    if sectionID != SectionID.userHeader.value:
        print("Failed to parser User Header, section ID = %d" % (sectionID))
        return False, None

    uh = UserHeader(stream, sectionID, sectionLen,
                    versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = uh.toJSON()
    return True, uh


def generateSRC(stream: DataStream, out: OrderedDict,
                sectionID: int, sectionLen: int, versionID: int, subType: int,
                componentID: int, creatorID: str) -> (bool, SRC):
    src = SRC(stream, sectionID, sectionLen,
              versionID, subType, componentID, creatorID)
    out[getSectionName(sectionID)] = src.toJSON()
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
               componentID: int) -> (bool, ExtUserData):
    ed = ExtUserData(stream, sectionID, sectionLen,
                     versionID, subType, componentID)
    out[getSectionName(sectionID)] = ed.toJSON()
    return True, ed


def generateUD(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str) -> (bool, UserData):
    ud = UserData(stream, sectionID, sectionLen, versionID,
                  subType, componentID, creatorID)

    out[getSectionName(sectionID)] = ud.toJSON()
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
               componentID: int, creatorID: str):
    if sectionID == SectionID.primarySRC.value or \
            sectionID == SectionID.secondarySRC.value:
        generateSRC(stream, out, sectionID, sectionLen,
                    versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.extendedUserHeader.value:
        generateEH(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.failingMTMS.value:
        generateMT(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.extUserData.value:
        generateED(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID)
    elif sectionID == SectionID.userData.value:
        generateUD(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)
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


def main():
    parser = argparse.ArgumentParser(description="PELTools")

    parser.add_argument('-f', '--file', dest='file',
                        help='input pel file to parse')
    args = parser.parse_args()

    with open(args.file, 'rb') as fd:
        data = fd.read()
        stream = DataStream(data, byte_order='big', is_signed=False)
        out = OrderedDict()
        ret, ph = generatePH(stream, out)
        if ret == False:
            return

        ret, _ = generateUH(stream, ph.creatorID, out)
        if ret == False:
            return

        section_jsons = []
        for _ in range(2, ph.sectionCount):
            sectionID, sectionLen, versionID, subType, componentID = parserHeader(
                stream)
            section_json = {}
            sectionFun(stream, section_json, sectionID, sectionLen,
                       versionID, subType, componentID, ph.creatorID)
            section_jsons.append(section_json)

        buildOutput(section_jsons, out)

        print(json.dumps(out, indent=4))


if __name__ == '__main__':
    main()
