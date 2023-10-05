"""
This module parses and formats ilog/PTE data.
"""

import re

from io_drawer.utils import format_timestamp
from pel.datastream import DataStream


# Size in bytes of an ilog entry 
ILOG_ENTRY_SIZE = 8

# Mask to check if PTE is an error
ERROR_MASK = 0xF0000000

# Value after mask that indicates PTE is an error
ERROR_VALUE = 0xE0000000

# Mask to check if PTE has reported error flag on
REPORTED_MASK = 0x00040000

# Value after mask that indicates PTE has reported error flag on
REPORTED_VALUE = 0x00040000


# The following regular expressions describe lines from the C++ header file.
# The header file defines a table of PTE entries.

# Regex for line that starts the table.  Opening brace could be on this line or
# the next one.
#
# Example:
#   static struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = 
TBL_START_RE = re.compile(r'(\s*static\s+)?\s*struct\s+pte_entry_struct\s+'
                           'static_pte_entry_table.*\=\s*\{?\s*')

# Regex for line that defines one table entry.  The message format field is a
# string surrounded by double quotes, but it can also contain escaped double
# quotes.  The params field is an array of integers; a list of zero or more
# comma-delimited numbers surrounded by braces.
#
# Examples:
#   { "01040000", "Power on complete", {}, "states.cpp", 601 },
#   { "100100**", "PS%d - Faults Cleared", {4}, "mps.cpp", 759 },
#   { "0200****", "This PEROM level = %c%c", {3, 4}, "states.cpp", 254 },
#   { "E2082690", "P1 IO Bay VRM in \"N-Mode\"", {}, "vrm_monitor.cpp", 145 },
TBL_ENTRY_RE = re.compile(r'\s*\{\s*"([^"]+)"\s*\,\s*"((?:[^"]|\\")*)"\s*'
                           '\,\s*\{([^}]*)\}\s*\,\s*"([^"]*)"\s*\,\s*'
                           '([0-9]+)\s*\}\s*\,\s*')

# Regex for line that ends the table.  It is an empty table entry.  In Python
# '.*' does not by default match newline, so the regex ends with '\s*'.
#
# Example:
#   { ""        , "The End" }
TBL_END_RE = re.compile(r'\s*\{\s*""\s*\,\s*"The End".*\s*')


class PTETableEntry:
    """
    Represents one entry in the PTE table from the C++ header file.
    """

    def __init__(self, pte_pattern: str, message_format: str, params: tuple,
                 file: str, line: int):
        """
        Constructor.
        """

        self.pte_pattern = pte_pattern
        self.message_format = message_format
        self.params = params
        self.file = file
        self.line = line

        # Discard any parameters outside the valid range 1-4.  The parameters
        # are 1-based byte numbers within a PTE that provide the values to use
        # in the message format string.  A PTE is 4 bytes long.
        self.params = tuple(p for p in self.params if (p >= 1) and (p <= 4))

        # Compile regular expression corresponding to pte_pattern.  pte_pattern
        # is not in regular expression format.  It contains '*' characters to
        # match any one character.  Convert '*' to '.'.
        re_pattern = self.pte_pattern.replace('*', '.')
        self.pte_re = re.compile(re_pattern, re.IGNORECASE)

    def get_message(self, pte: int) -> str:
        """
        Returns a formatted message for the specified PTE.

        The PTE should be a 4 byte, unsigned integer value.

        If the message contains parameters, this method obtains the parameter
        values from the PTE bytes.
        """

        # Build list of 4 bytes in the PTE
        pte_bytes = list((pte & 0xFFFFFFFF).to_bytes(4, 'big'))

        # Get parameter values from PTE bytes.  Note that parameter numbers are
        # 1-based, so we need to subtract 1 for byte indices.
        param_values = tuple(pte_bytes[p - 1] for p in self.params)

        # Format the message using the parameter values (if any)
        try:
            message = self.message_format % param_values
        except Exception:
            message = self.message_format

        # Add suffix to message if PTE indicates it is a reported error
        if self._is_reported_error_pte(pte):
            message += ' - PEL entry created'

        return message
    
    def matches(self, pte: int) -> bool:
        """
        Returns whether the specified PTE matches this table entry.
        """

        # Check for an exact match
        if self._is_exact_match(pte):
            return True

        # Check if the PTE is an error that has been reported.  If so, remove
        # the reported flag and check again for a match.
        if self._is_reported_error_pte(pte):
            pte &= ~REPORTED_MASK
            if self._is_exact_match(pte):
                return True

        return False

    def _is_exact_match(self, pte: int) -> bool:
        """
        Returns whether the specified PTE matches the regular expression for
        this table entry.
        """

        hex_string = f'{pte:08X}'
        match = self.pte_re.fullmatch(hex_string)
        return match is not None

    def _is_reported_error_pte(self, pte: int) -> bool:
        """
        Returns whether the specified PTE is a reported error.
        """

        return (((pte & ERROR_MASK) == ERROR_VALUE) and
                ((pte & REPORTED_MASK) == REPORTED_VALUE))


class PTETable:
    """
    Represents the PTE table defined in the C++ header file.
    """

    def __init__(self, header_file_path: str):
        """
        Constructor.

        Parses the specified C++ header file to obtain the PTE table.
        """

        self.header_file_path = header_file_path
        self.entries = []

        # Parse header file to get PTE table
        self._parse_header_file()

    def get_entry(self, pte: int) -> PTETableEntry:
        """
        Returns the table entry that matches the specified PTE.

        Returns None if no matching entry is found.
        """

        for entry in self.entries:
            if entry.matches(pte):
                return entry
        return None

    def _add_entry(self, fields: tuple):
        """
        Creates a table entry based on the specified fields from the C++ header
        file.
        """

        # Verify we have the right number of fields
        if len(fields) != 5:
            return

        # Obtain entry properties from the string values in the fields tuple.
        # Example:
        #   ('0200****', 'PEROM level = %c%c  ', '3, 4', 'states.cpp', '254')
        pte_pattern = fields[0]
        message_format = fields[1]
        params_str = fields[2]
        file = fields[3]
        line = int(fields[4])

        # Remove leading/trailing blanks from message format string and replace
        # escaped double quotes with plain double quotes
        message_format = message_format.strip().replace(r'\"', '"')

        # Convert string with list of parameters into tuple of numbers.
        # Example: '3, 4' -> (3, 4)
        params = tuple(int(p) for p in params_str if p.isdecimal())

        # Create entry and add to list of entries
        entry = PTETableEntry(pte_pattern, message_format, params, file, line)
        self.entries.append(entry)

    def _parse_header_file(self):
        """
        Parses the C++ header file to get the PTE table.
        """

        in_table = False
        with open(self.header_file_path) as file:
            for line in file:
                if TBL_START_RE.fullmatch(line):
                    in_table = True
                elif TBL_END_RE.fullmatch(line):
                    in_table = False
                elif in_table:
                    match = TBL_ENTRY_RE.fullmatch(line)
                    if match:
                        self._add_entry(match.groups())


def parse_ilog_data(data: memoryview, header_file_path: str) -> list:
    """
    Parses binary ilog/PTE data and returns formatted output.

    Parses the specified C++ header file to obtain the PTE table.
    """

    # Get PTE Table from C++ header file
    table = PTETable(header_file_path)

    # Add ilog table header to output lines
    lines = []
    lines.append('hh:mm:ss seq  pppppppp description')
    lines.append('-------- ---- -------- ------------------------------------')

    # Loop over the data bytes
    stream = DataStream(data, byte_order='big', is_signed=False)
    while stream.check_range(ILOG_ENTRY_SIZE):
        # Parse ilog entry fields
        timestamp = stream.get_int(2)
        seq_num = stream.get_int(2)
        pte = stream.get_int(4)

        # Ignore invalid ilog entries
        if (timestamp == 0) and (seq_num == 0) and (pte == 0x00000000):
            continue

        # Format timestamp value
        timestamp_str = format_timestamp(timestamp)

        # Get entry from table that matches PTE.  Then get message from entry.
        message = 'Undefined'
        entry = table.get_entry(pte)
        if entry is not None:
            message = entry.get_message(pte)

        # Add output line for ilog entry
        lines.append(f'{timestamp_str} {seq_num:04X} {pte:08X} {message}')

    return lines
