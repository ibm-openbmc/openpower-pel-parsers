#!/usr/bin/env python3

"""
This module contains functions to parse and format IO drawer dumps.

An IO drawer dump can be obtained in the following ways:
    * Using the web interface to the BMC and predecessors of the BMC.
    * Collecting a Resource Dump.  The IO drawer dump is contained inside the
      Resource Dump and must be extracted using a separate tool.

The IO drawer dump is a hex dump of memory containing the following:
    * ILOG/PTE data
    * Zero or more trace buffers

This module can also be run standalone as a script.
"""

import argparse
import sys

from io_drawer.drawer_type import DrawerType, DRAWER_TYPES
from io_drawer.ilog import parse_ilog_data
from io_drawer.trace import parse_trace_data, TraceBufferHeader
import pel.hexdump as hexdump


# Byte values expected at the start of a trace buffer header
TRACE_BUFFER_HEADER_START = (b'\x02'        # ver field
                             b'\x20'        # hdr_len field
                             b'\x01'        # time_flg field
                             b'\x42')       # endian_flg field ('B')


# Possible hex dump line formats for the IO drawer dump
HEX_DUMP_LINE_FORMATS = [
    # Format for BMC systems
    'AAAA:  DDDDDDDD DDDDDDDD DDDDDDDD DDDDDDDD  <CCCCCCCCCCCCCCCC>',

    # Format for pre-BMC systems
    'DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD CCCCCCCCCCCCCCCC'
]


# Divider line between IO drawer dump sections in the formatted output
DIVIDER_LINE = \
    '-------------------------------------------------------------------------'


def _get_drawer_type_names() -> list:
    """
    Returns a list of valid drawer type names.
    """

    return [drawer_type.name for drawer_type in DRAWER_TYPES]


def _get_drawer_type(name: str) -> DrawerType:
    """
    Returns the drawer type with the specified name.

    Returns None if no matching drawer type is found.
    """

    for drawer_type in DRAWER_TYPES:
        if drawer_type.name == name:
            return drawer_type

    return None


def _format_ilog_data(data: memoryview, lines: list, header_file: str):
    """
    Parses and formats ILOG/PTE data.

    Stores the output lines in the specified list parameter.

    Parses the specified C++ header file to obtain the PTE table.
    """

    lines.append('ILOG')
    lines.append('')
    lines.extend(parse_ilog_data(data, header_file))
    lines.append('')
    lines.append(DIVIDER_LINE)
    lines.append('')


def _format_trace_data(data: memoryview, lines: list, string_file: str):
    """
    Parses and formats trace data.

    Stores the output lines in the specified list parameter.

    Parses the specified trace string file to obtain the trace strings.
    """

    lines.append('Trace')
    lines.append('')
    lines.extend(parse_trace_data(data, string_file))
    lines.append('')
    lines.append(DIVIDER_LINE)
    lines.append('')


def parse_dump_data(data: memoryview, header_file: str,
                    string_file: str) -> list:
    """
    Parses and formats IO drawer dump data.

    Returns the resulting output lines.

    Parses the specified C++ header file to obtain the PTE table.  Parses the
    specified trace string file to obtain the trace strings.
    """

    lines = []

    # Verify we have at least one byte of data
    if not data:
        return lines

    # Get the bytes referenced by the memoryview so we can use find()
    data_bytes = data.tobytes()

    # The IO drawer dump contains ILOG data followed by zero or more trace
    # buffers.  We don't know the size of the ILOG data, so we first search for
    # trace buffers.  The trace buffer header starts with 4 known byte values
    # followed by the buffer name.  Search for that byte pattern.
    buffer_offsets = []
    for buffer_name in TraceBufferHeader.BUFFER_NAMES:
        start_bytes = TRACE_BUFFER_HEADER_START + buffer_name.encode()
        offset = data_bytes.find(start_bytes)
        if offset != -1:
            buffer_offsets.append(offset)

    # Format the ILOG data.  It is located before the first trace buffer.
    buffer_offsets = sorted(buffer_offsets)
    begin = 0
    if buffer_offsets:
        end = buffer_offsets[0]
    else:
        end = len(data) 
    ilog_data = data[begin:end]
    _format_ilog_data(ilog_data, lines, header_file)

    # Format the trace buffers.  Each buffer ends where next one begins.
    for (i, buffer_offset) in enumerate(buffer_offsets):
        begin = buffer_offset
        if (i + 1) < len(buffer_offsets):
            end = buffer_offsets[i + 1]
        else:
            end = len(data)
        trace_data = data[begin:end]
        _format_trace_data(trace_data, lines, string_file)

    return lines


def parse_dump_file(dump_file: str, header_file: str, string_file: str) -> list:
    """
    Parses and formats IO drawer dump data in the specified file.

    Returns the resulting output lines.

    Parses the specified C++ header file to obtain the PTE table.  Parses the
    specified trace string file to obtain the trace strings.
    """

    # Parse the IO drawer dump file as a hex dump to obtain the data bytes
    with open(dump_file) as file:
        lines = file.readlines()
    data = bytearray()
    for line_format in HEX_DUMP_LINE_FORMATS:
        data = hexdump.parse(lines, line_format)
        if data:
            break

    # Parse/format the IO drawer dump data bytes
    lines = []
    if data:
        data = memoryview(data)
        lines = parse_dump_data(data, header_file, string_file)

    return lines


def parse_args() -> tuple:
    """
    Parses the command line arguments.

    Returns a tuple containing the dump file, header file, and string file.
    """

    parser = argparse.ArgumentParser(description='IO drawer dump parser/formatter.')
    parser.add_argument('dump_file',
                        help='IO drawer dump file')
    parser.add_argument('-t', '--drawer-type', required=True,
                        dest='drawer_type_name',
                        choices=_get_drawer_type_names(),
                        help='Drawer type that produced the dump')
    parser.add_argument('-d', '--header-file',
                        help='Generated header file containing the PTE table')
    parser.add_argument('-s', '--string-file',
                        help='File containing the trace strings')
    args = parser.parse_args()
    dump_file = args.dump_file
    drawer_type_name = args.drawer_type_name
    header_file = args.header_file
    string_file = args.string_file

    drawer_type = _get_drawer_type(drawer_type_name)
    if not drawer_type:
        parser.error(f'Invalid drawer type specified: {drawer_type_name}')

    if not header_file:
        header_file = drawer_type.get_header_file_path()

    if not string_file:
        string_file = drawer_type.get_trace_string_file_path()

    return (dump_file, header_file, string_file)


def main():
    """
    Parses the command line parameters and then parses/formats the IO drawer
    dump data.

    Writes the resulting lines to the standard output stream.
    """

    # Parse command line arguments
    (dump_file, header_file, string_file) = parse_args()

    rc = 0
    try:
        lines = parse_dump_file(dump_file, header_file, string_file)
        for line in lines:
            print(line)
    except Exception as e:
        print(f'Error: {str(e)}', file=sys.stderr)
        rc = 1

    sys.exit(rc)


if __name__ == '__main__':
    main()
