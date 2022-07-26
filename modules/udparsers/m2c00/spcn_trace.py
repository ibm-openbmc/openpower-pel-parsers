#!/usr/bin/env python3

"""
This module contains functions to parse and format SPCN Trace data produced by
IO drawers.

The SPCN Trace data can be obtained in the following ways:
    * Using the web interface to the BMC and predecessors of the BMC.
    * Collecting a Resource Dump.  The SPCN Trace data must be extracted from
      the dump using a separate Resource Dump tool.

The SPCN Trace is a hex dump of memory containing the following:
    * ILOG/PTE data
    * Zero or more trace buffers

This module can also be run standalone as a script.
"""

import argparse
import sys

import pel.hexdump as hexdump
from udparsers.m2c00.ilog import parse_ilog_data
from udparsers.m2c00.trace import parse_trace_data


# Byte values expected at the start of a trace buffer header
TRACE_BUFFER_HEADER_START = (b'\x02'        # ver field
                             b'\x20'        # hdr_len field
                             b'\x01'        # time_flg field
                             b'\x42')       # endian_flg field ('B')


# Valid values for the 'comp' field in a trace buffer header.  This field
# contains the buffer name.
TRACE_BUFFER_NAMES = ['IICS', 'IICM', 'POWR', 'FANS', 'INFO', 'ERRL']


# Possible hex dump line formats for the SPCN Trace data
HEX_DUMP_LINE_FORMATS = [
    # Format for BMC systems
    'AAAA:  DDDDDDDD DDDDDDDD DDDDDDDD DDDDDDDD  <CCCCCCCCCCCCCCCC>',

    # Format for pre-BMC systems
    'DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD CCCCCCCCCCCCCCCC'
]


# Divider line between SPCN Trace sections in formatted output
DIVIDER_LINE = \
    '-------------------------------------------------------------------------'


def _format_ilog_data(data: memoryview, lines: list, header_file: str = None):
    """
    Parses and formats ILOG/PTE data.

    Stores the output lines in the specified list parameter.

    Parses the specified C++ header file to obtain the PTE table.

    If the header file is not specified, it will be found in the standard
    location.
    """

    lines.append('ILOG')
    lines.append('')
    lines.extend(parse_ilog_data(data, header_file))
    lines.append('')
    lines.append(DIVIDER_LINE)
    lines.append('')


def _format_trace_data(data: memoryview, lines: list, string_file: str = None):
    """
    Parses and formats trace data.

    Stores the output lines in the specified list parameter.

    Parses the specified trace string file to obtain the trace strings.

    If the string file is not specified, it will be found in the standard
    location.
    """

    lines.append('Trace')
    lines.append('')
    lines.extend(parse_trace_data(data, string_file))
    lines.append('')
    lines.append(DIVIDER_LINE)
    lines.append('')


def parse_spcn_trace_data(data: memoryview, header_file: str = None,
                          string_file: str = None) -> list:
    """
    Parses and formats SPCN Trace data.

    Returns the resulting output lines.

    Parses the specified C++ header file to obtain the PTE table.  Parses the
    specified trace string file to obtain the trace strings.

    If the header file or string file is not specified, they will be found in
    the standard location.
    """

    lines = []

    # Verify we have at least one byte of data
    if not data:
        return lines

    # Get the bytes referenced by the memoryview so we can use find()
    data_bytes = data.tobytes()

    # The SPCN Trace contains ILOG data followed by zero or more trace buffers.
    # We don't know the size of the ILOG data, so we first search for trace
    # buffers.  The trace buffer header starts with 4 known byte values
    # followed by the buffer name.  Search for that byte pattern.
    buffer_offsets = []
    for buffer_name in TRACE_BUFFER_NAMES:
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


def parse_spcn_trace_file(spcn_trace_file: str = None, header_file: str = None,
                          string_file: str = None) -> list:
    """
    Parses and formats SPCN Trace data in the specified file.

    Returns the resulting output lines.

    Parses the specified C++ header file to obtain the PTE table.  Parses the
    specified trace string file to obtain the trace strings.

    If the header file or string file is not specified, they will be found in
    the standard location.
    """

    # Parse the SPCN Trace file as a hex dump to obtain the data bytes
    with open(spcn_trace_file) as file:
        lines = file.readlines()
    data = bytearray()
    for line_format in HEX_DUMP_LINE_FORMATS:
        data = hexdump.parse(lines, line_format)
        if data:
            break

    # Parse/format the SPCN Trace data bytes
    lines = []
    if data:
        data = memoryview(data)
        lines = parse_spcn_trace_data(data, header_file, string_file)

    return lines


def main():
    """
    Parses the command line parameters and then parses/formats SPCN Trace data.

    Writes the resulting lines to the standard output stream.
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SPCN Trace parser/formatter.')
    parser.add_argument('spcn_trace_file',
                        help='File containing SPCN Trace hexdump')
    parser.add_argument('-d', '--header-file',
                        help='Generated header file containing the PTE table')
    parser.add_argument('-s', '--string-file',
                        help='File containing the trace strings')
    args = parser.parse_args()
    spcn_trace_file = args.spcn_trace_file
    header_file = args.header_file
    string_file = args.string_file

    rc = 0
    try:
        lines = parse_spcn_trace_file(spcn_trace_file, header_file, string_file)
        for line in lines:
            print(line)
    except Exception as e:
        print(f'Error: {str(e)}', file=sys.stderr)
        rc = 1

    sys.exit(rc)


if __name__ == '__main__':
    main()
