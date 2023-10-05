"""
This module contains functions to parse and format history log data.
"""

import re
from collections import namedtuple

from pel.datastream import DataStream
from pel.hexdump import hexdump


# This namedtuple represents a field in the history log
HistoryLogField = namedtuple('HistoryLogField', ('name', 'size'))


# The following regular expressions describe lines from the C++ header file.
# The header file defines an array of history log field structs.

# Regex for line that starts the array.  Opening brace could be on this line or
# the next one.
#
# Example:
#   static struct mex_hlog_field mex_hlog_fields[MEX_HLOG_FIELD_COUNT] =
HLOG_START_RE = re.compile(r'(\s*static\s+)?\s*struct\s+mex_hlog_field\s+'
                            'mex_hlog_fields.*\=\s*\{?\s*')

# Regex for line that defines one field struct in the array.  Trailing comma is
# optional on the last array element.
#
# Example:
#   { 1, "hl_net_block_crc_failures" }, 
HLOG_FIELD_RE = re.compile(r'\s*\{\s*([12])\s*\,\s*"([^"]+)"\s*\}\s*\,?\s*')

# Regex for line that ends the array.
#
# Example:
#   };
HLOG_END_RE = re.compile(r'\s*\}\s*;\s*')


def get_hlog_fields(header_file_path: str) -> list:
    """
    Returns the list of fields in the history log.

    Parses the C++ header file to obtain the field definitions.
    """

    # Build list of fields by parsing C++ header file
    fields = []
    in_data_structure = False
    with open(header_file_path) as file:
        for line in file:
            if HLOG_START_RE.fullmatch(line):
                in_data_structure = True
            elif HLOG_END_RE.fullmatch(line):
                in_data_structure = False
            elif in_data_structure:
                match = HLOG_FIELD_RE.fullmatch(line)
                if match:
                    properties = match.groups()
                    if len(properties) == 2:
                        size = int(properties[0])
                        name = properties[1]
                        field = HistoryLogField(name, size)
                        fields.append(field)
    return fields


def parse_hlog_data(data: memoryview, header_file_path: str) -> list:
    """
    Parses binary history log data and returns formatted output.

    Parses the C++ header file to obtain the history log field definitions.
    """

    # Add hex dump of all history log data to output
    lines = ['Hex Dump']
    lines.append('--------')
    lines.extend(hexdump(data))
    lines.append('')

    # Get history log fields from C++ header file
    fields = get_hlog_fields(header_file_path)

    # Loop over fields.  Add field name/value to output if value is != 0.
    lines.append('Non-Zero Field Values')
    lines.append('---------------------')
    stream = DataStream(data, byte_order='big', is_signed=False)
    for field in fields:
        if not stream.check_range(field.size):
            break
        value = stream.get_int(field.size)
        if value != 0:
            lines.append(f'{field.name}: 0x{value:0{field.size * 2}X}')

    return lines
