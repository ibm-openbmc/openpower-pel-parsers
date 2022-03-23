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
from pel.peltool.registry import Registry
from pel.peltool.extend_user_header import ExtendedUserHeader
from pel.peltool.failing_mtms import FailingMTMS
from pel.peltool.user_data import UserData
from pel.peltool.ext_user_data import ExtUserData
import pel_registry


class Static:
    count = 0

    def __init__(self) -> None:
        pass


def parserHeader(stream: DataStream):
    sectionID = stream.get_int(2)
    sectionLen = stream.get_int(2)
    versionID = stream.get_int(1)
    subType = stream.get_int(1)
    componentID = stream.get_int(2)
    # componentID = "0x{:02X}".format(stream.get_int(2))
    return sectionID, sectionLen, versionID, subType, componentID


def generatePH(stream: DataStream, out: OrderedDict) -> (bool, PrivateHeader):
    sectionID, sectionLen, versionID, subType, componentID = parserHeader(
        stream)
    if sectionID != SectionID.privateHeader.value:
        print("Failed to parser Private Header, section ID = %x" % (sectionID))
        return False, None

    ph = PrivateHeader(stream, sectionID, sectionLen,
                       versionID, subType, componentID)
    out["Private Header"] = ph.toJSON()
    return True, ph


def generateUH(stream: DataStream, out: OrderedDict) -> (bool, UserHeader):
    sectionID, sectionLen, versionID, subType, componentID = parserHeader(
        stream)
    if sectionID != SectionID.userHeader.value:
        print("Failed to parser User Header, section ID = %d" % (sectionID))
        return False, None

    uh = UserHeader(stream, sectionID, sectionLen,
                    versionID, subType, componentID)
    out["User Header"] = uh.toJSON()
    return True, uh


def generateSRC(registry: Registry, stream: DataStream, out: OrderedDict,
                sectionID: int, sectionLen: int, versionID: int, subType: int,
                componentID: int, creatorID: str) -> (bool, SRC):
    src = SRC(registry, stream, sectionID, sectionLen,
              versionID, subType, componentID, creatorID)
    out["Primary SRC"] = src.toJSON()
    return True, src


def generateEH(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int) -> (bool, ExtendedUserHeader):
    eh = ExtendedUserHeader(stream, sectionID, sectionLen,
                            versionID, subType, componentID)
    out["Extended User Header"] = eh.toJSON()
    return True, eh


def generateMT(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int) -> (bool, FailingMTMS):
    mt = FailingMTMS(stream, sectionID, sectionLen,
                     versionID, subType, componentID)
    out["Failing MTMS"] = mt.toJSON()
    return True, mt


def generateED(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int) -> (bool, ExtUserData):
    ed = ExtUserData(stream, sectionID, sectionLen,
                     versionID, subType, componentID)
    out["Extended User Data"] = ed.toJSON()
    return True, ed


def generateUD(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str) -> (bool, UserData):
    ud = UserData(stream, sectionID, sectionLen, versionID,
                  subType, componentID, creatorID)

    out["User Data " + str(Static.count)] = ud.toJSON()
    Static.count += 1
    return True, ud


def sectionFun(stream: DataStream, out: OrderedDict, sectionID: int,
               sectionLen: int, versionID: int, subType: int,
               componentID: int, creatorID: str):
    registry = Registry(pel_registry.get_path())
    if sectionID == SectionID.primarySRC.value or sectionID == SectionID.secondarySRC.value:
        generateSRC(registry, stream, out, sectionID, sectionLen,
                    versionID, subType, componentID, creatorID)
    elif sectionID == SectionID.extendedUserHeader.value:
        generateEH(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID)
    elif sectionID == SectionID.failingMTMS.value:
        generateMT(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID)
    elif sectionID == SectionID.extUserData.value:
        generateED(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID)
    elif sectionID == SectionID.userData.value:
        generateUD(stream, out, sectionID, sectionLen,
                   versionID, subType, componentID, creatorID)


def main():
    parser = argparse.ArgumentParser(description="OpenPOWER PELTools")

    parser.add_argument('-f', '--file', dest='file',
                        help='input pel file to parse')
    args = parser.parse_args()

    with open(os.path.join(script_dir, args.file), 'rb') as fd:
        data = fd.read()
        stream = DataStream(data, byte_order='big', is_signed=False)
        out = OrderedDict()
        ret, ph = generatePH(stream, out)
        if ret == False:
            return

        ret, uh = generateUH(stream, out)
        if ret == False:
            return

        for i in range(2, ph.sectionCount):
            sectionID, sectionLen, versionID, subType, componentID = parserHeader(
                stream)
            sectionFun(stream, out, sectionID, sectionLen,
                       versionID, subType, componentID, ph.creatorID)

        print(json.dumps(out, indent=4))


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))
    main()
