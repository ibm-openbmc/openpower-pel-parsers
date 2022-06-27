"""
This module contains functions to parse and format history log data.
"""

import re
from collections import namedtuple

from pel.datastream import DataStream
from pel.hexdump import hexdump
from udparsers.m2c00.utils import get_header_file_path


# This namedtuple represents a field in the history log
HistoryLogField = namedtuple('HistoryLogField', ('name', 'size'))


def get_hlog_fields(header_file_path: str = None) -> list:
    """
    Returns the list of fields in the history log.

    Parses a C++ header file to obtain the field definitions.

    If the header file path is not specified, it will be found in the
    standard location.
    """

    # Find header file path if not specified
    if not header_file_path:
        header_file_path = get_header_file_path()

    # Compile regular expressions for parsing C++ header file
    start_re = re.compile(r'\s*struct\s+mex_hlog_field\s+'
                           'mex_hlog_fields.*\=\s*\{?\s*')
    field_re = re.compile(r'\s*\{\s*([12])\s*\,\s*"([^"]+)"\s*\}\s*\,?\s*')
    end_re = re.compile(r'\s*\}\s*;\s*')

    # Build list of fields by parsing C++ header file
    fields = []
    in_data_structure = False
    with open(header_file_path) as file:
        for line in file:
            if start_re.fullmatch(line):
                in_data_structure = True
            elif end_re.fullmatch(line):
                in_data_structure = False
            elif in_data_structure:
                match = field_re.fullmatch(line)
                if match:
                    properties = match.groups()
                    if len(properties) == 2:
                        size = int(properties[0])
                        name = properties[1]
                        field = HistoryLogField(name, size)
                        fields.append(field)
    return fields


def parse_hlog_data(data: memoryview,
                    header_file_path: str = None) -> list:
    """
    Parses binary history log data and returns formatted output.

    Parses a C++ header file to obtain the history log field
    definitions.

    If the header file path is not specified, it will be found in the
    standard location.
    """

    # Add hex dump of all history log data to output
    lines = ['Hex Dump:']
    lines.append('')
    lines.extend(hexdump(data))
    lines.append('')

    # Get history log fields from C++ header file
    fields = get_hlog_fields(header_file_path)

    # Loop over fields.  Add field name/value to output if value is != 0.
    lines.append('Non-Zero Field Values:')
    lines.append('')
    stream = DataStream(data, byte_order='big', is_signed=False)
    for field in fields:
        if not stream.check_range(field.size):
            break
        value = stream.get_int(field.size)
        if value != 0:
            lines.append(f'{field.name}: 0x{value:0{field.size * 2}X}')

    return lines
