"""
This module parses and formats trace data.
"""

import re

from pel.datastream import DataStream
from pel.hexdump import hexdump
from udparsers.m2c00.utils import format_timestamp, get_trace_string_file_path


class TraceString:
    """
    Represents one trace string from the trace string file.
    """

    def __init__(self, hash_value: int, message_format: str, location: str):
        """
        Constructor.
        """

        self.hash_value = hash_value
        self.message_format = message_format
        self.location = location

    def get_message(self, args: tuple) -> str:
        """
        Returns a formatted message using the specified argument values.
        """

        try:
            message = self.message_format % args
        except Exception:
            message = self.message_format
        return message

    def is_match(self, hash_value: int) -> bool:
        """
        Returns whether this trace string has the specified hash value.

        Returns True only if the hash values exactly match.
        """

        return self.hash_value == hash_value

    def is_partial_match(self, hash_value: int) -> bool:
        """
        Returns whether this trace string partially matches the specified hash
        value.

        A partial match can occur when the trace entry is from a older or newer
        build than the one that created the trace string file.  In that case,
        the source file line number containing the trace may have changed.
        """

        # Currently the source file line number is multipled by 100000 to form
        # part of the hash value.  Check if the lower order digits in the hash
        # match; those digits are not based on the line number.
        return ((self.hash_value != hash_value) and
                ((self.hash_value % 100000) == (hash_value % 100000)))


class TraceStringFile:
    """
    Represents the trace string file that is generated when building the IO
    drawer firmware.
    """

    # Regular expression for one valid line from the string file.
    #
    # The line contains one trace string.
    #
    # Example:
    #   92602121||I> ADT7470: trace_level = %u||adt7470_fan_ctl.cpp(926)
    LINE_RE = re.compile(r'\s*([0-9]+)\s*\|\|(.*)\|\|(.*)\n?')

    def __init__(self, string_file_path: str = None):
        """
        Constructor.

        Parses the specified trace string file to obtain the trace strings.

        If the string file path is not specified, it will be found in the
        standard location.
        """

        self.string_file_path = string_file_path
        self.trace_strings = []

        # Find string file path if not specified
        if not self.string_file_path:
            self.string_file_path = get_trace_string_file_path()

        # Parse string file to obtain trace strings
        with open(self.string_file_path) as file:
            for line in file:
                match = self.LINE_RE.fullmatch(line)
                if match:
                    self._add_trace_string(match.groups())

    def get_trace_string(self, hash_value: int) -> TraceString:
        """
        Returns the trace string that matches the specified hash value.

        Returns None if no matching trace string is found.
        """

        # Loop through all trace strings looking for an exact match.  Also save
        # any partial matches.  If no exact match is found, return the last
        # partial match found (if any).
        partial_match = None
        for trace_string in self.trace_strings:
            if trace_string.is_match(hash_value):
                return trace_string
            elif trace_string.is_partial_match(hash_value):
                partial_match = trace_string
        return partial_match

    def _add_trace_string(self, fields: tuple):
        """
        Creates a trace string based on the specified fields from the string
        file.
        """

        # Verify we have the right number of fields
        if len(fields) != 3:
            return

        # Obtain trace string properties from the string values in fields tuple
        hash_value = int(fields[0].strip())
        message_format = fields[1].strip()
        location = fields[2].strip()

        # Create trace string and add to list of trace strings
        trace_string = TraceString(hash_value, message_format, location)
        self.trace_strings.append(trace_string)


class TraceBufferHeader:
    """
    Represents the header structure at the beginning of a binary trace buffer.
    """

    # Size in bytes of the header
    SIZE = 32

    def __init__(self):
        """
        Constructor.
        """

        self.ver = None         # version of this struct
        self.hdr_len = None     # size of this struct in bytes
        self.time_flg = None    # meaning of timestamp entry field
        self.endian_flg = None  # flag for big ('B') or little ('L') endian
        self.comp = None        # the buffer name as specified in init call
        self.size = None        # size of buffer, including this struct
        self.times_wrap = None  # how often the buffer wrapped
        self.next_free = None   # offset of the byte behind the latest entry

    def read(self, stream: DataStream) -> bool:
        """
        Reads the header contents from the specified big-endian data stream.

        Returns True if the header was successfully read.
        """

        if not stream.check_range(self.SIZE):
            return False

        # Read header field values from stream
        self.ver = stream.get_int(1)
        self.hdr_len = stream.get_int(1)
        self.time_flg = stream.get_int(1)
        self.endian_flg = stream.get_int(1)
        self.comp = stream.get_mem(12)
        stream.inc_index(4)         # Ignore 4 byte reserved field
        self.size = stream.get_int(4)
        self.times_wrap = stream.get_int(4)
        self.next_free = stream.get_int(4)

        # Convert 'comp' field to a string
        self.comp = str(self.comp, encoding='ascii', errors='ignore')
        self.comp = self.comp.rstrip('\0').rstrip(' ')

        return True


class TraceEntry:
    """
    Represents one trace entry within a binary trace buffer.
    """

    # Size in bytes of the fixed fields in a trace entry
    FIXED_SIZE = 16

    # Maximum size of the entry data
    MAX_DATA_LEN = 1024

    # Entry type; stored in the tag field
    TYPE_FIELDTRACE = 0x4654
    TYPE_FIELDBIN = 0x4644

    # Maximum number of arguments found within the entry data
    MAX_ARGS = 5

    def __init__(self):
        """
        Constructor.
        """

        self.tbh = None          # timestamp upper part (timestamp)
        self.tbl = None          # timestamp lower part (sequence number)
        self.length = None       # size of trace entry data
        self.tag = None          # type of entry
        self.hash_value = None   # a value for the (format) string
        self.line = None         # source file line number of trace call
        self.data = None         # trace entry data (variable size)

    def get_args(self) -> tuple:
        """
        Returns the arguments found within the entry data.

        These arguments are used to format the trace string.  They provide the
        values for formatting specifiers like %d.

        Binary trace entries do not have arguments.
        """

        args = []
        if (not self.is_binary_trace()) and (self.data is not None):
            stream = DataStream(self.data, byte_order='big', is_signed=False)
            for i in range(self.MAX_ARGS):
                if stream.check_range(4):
                    args.append(stream.get_int(4))
                else:
                    break
        return tuple(args)

    def is_binary_trace(self) -> bool:
        """
        Returns whether this is a binary trace entry.

        Binary entries do not have arguments used by the trace string.  The
        entry data can be any size and format.  It is displayed as a sequence
        of hexadecimal values when the trace entry is formatted.
        """

        return self.tag == TraceEntry.TYPE_FIELDBIN

    def read(self, stream: DataStream) -> bool:
        """
        Reads the entry contents from the specified big-endian data stream.

        Returns True if the entry was successfully read.
        """

        if not stream.check_range(self.FIXED_SIZE):
            return False

        # Save starting stream index so we can determine entry size
        start_index = stream.index

        # Read the fixed size fields
        self.tbh = stream.get_int(2)
        self.tbl = stream.get_int(2)
        self.length = stream.get_int(2)
        self.tag = stream.get_int(2)
        self.hash_value = stream.get_int(4)
        self.line = stream.get_int(4)

        # Verify data length field is valid
        if self.length > self.MAX_DATA_LEN:
            return False

        # Read entry data, if any
        if self.length == 0:
            self.data = memoryview(b'')
        else:
            # Verify stream has enough remaining bytes
            if not stream.check_range(self.length):
                return False

            # Read entry data
            self.data = stream.get_mem(self.length)

            # Entry data is aligned on 4 byte boundary.  Skip any pad bytes.
            if (self.length % 4) != 0:
                pad_size = 4 - (self.length % 4)
                if not stream.check_range(pad_size):
                    return False
                stream.inc_index(pad_size)

        # Read and verify 4 byte field at end containing the total entry size.
        # The entry size includes the size of this field.
        if not stream.check_range(4):
            return False
        entry_size = stream.get_int(4)
        if entry_size != (stream.index - start_index):
            return False

        return True


class TraceBuffer:
    """
    This class represents a binary trace buffer.

    The buffer contains a header followed by zero or more trace entries.
    """

    def __init__(self):
        """
        Constructor.
        """

        self.header = None
        self.entries = []

    def read(self, stream: DataStream) -> bool:
        """
        Reads the buffer contents from the specified big-endian data stream.

        Returns True if the buffer was successfully read.
        """

        # Read trace buffer header
        self.header = TraceBufferHeader()
        if not self.header.read(stream):
            return False

        # Read trace entries
        while stream.index < self.header.size:
            entry = TraceEntry()
            if not entry.read(stream):
                break
            self.entries.append(entry)

        return True


def _format_trace_entry(entry: TraceEntry, string_file: TraceStringFile,
                        lines: list):
    """
    Formats the specified trace entry.

    Writes output lines to the specified list.
    """

    # Get relevant fields from trace entry
    timestamp = format_timestamp(entry.tbh)
    seq = entry.tbl
    line = entry.line
    hash_value = entry.hash_value

    # Find trace string (if any) that matches the trace entry hash value
    trace_string = string_file.get_trace_string(hash_value)
    if trace_string is not None:
        args = entry.get_args()
        message = trace_string.get_message(args)
        is_partial_match = trace_string.is_partial_match(hash_value)
    else:
        message = f'No trace string found with hash value {hash_value}'
        is_partial_match = False

    # Add output line for trace entry
    lines.append(f'{timestamp} {seq:04X} {line:5d} {message}')

    # If trace string is partial match, add output line with string location
    indent = '                    '
    if is_partial_match:
        lines.append(f'{indent}Warning: Partial match with trace string '
                     f'from {trace_string.location}')

    # Add output lines with hex dump of entry data if needed
    if entry.is_binary_trace() or (trace_string is None) or is_partial_match:
        if entry.data is not None:
            for dump_line in hexdump(entry.data):
                lines.append(f'{indent}{dump_line}')


def parse_trace_data(data: memoryview,
                     string_file_path: str = None) -> list:
    """
    Parses binary trace data and returns formatted output.

    Parses the specified trace string file to obtain the trace strings.

    If the string file path is not specified, it will be found in the
    standard location.
    """

    # Parse trace string file
    string_file = TraceStringFile(string_file_path)

    # Parse trace buffer
    lines = []
    stream = DataStream(data, byte_order='big', is_signed=False)
    buffer = TraceBuffer()
    if buffer.read(stream):
        # Format trace buffer header
        lines.append(f'Component: {buffer.header.comp}')
        lines.append(f'Version: {buffer.header.ver}')
        lines.append(f'Size: {buffer.header.size}')
        lines.append(f'Times Wrapped: {buffer.header.times_wrap}')
        lines.append('')

        # Format trace entries
        lines.append('HH:MM:SS Seq  Line  Entry Data')
        lines.append('-------- ---- ----- ----------')
        for entry in buffer.entries:
            _format_trace_entry(entry, string_file, lines)
    else:
        lines.append('Unable to parse trace data.')
        lines.extend(hexdump(data))

    return lines
