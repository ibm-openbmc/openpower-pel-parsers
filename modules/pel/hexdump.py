import math
import re

def hexdump(data: memoryview,
            bytes_per_line: int = 16,
            bytes_per_chunk: int = 4) -> list:
    """
    Returns a list of strings. Each entry will be one line of the hex dump from
    the given data.
    """

    # Allowing the flexibility for whatever size dump is needed, but still
    # placing reasonable limits.
    assert 1 <= bytes_per_line <= 256, "bytes_per_line must be within 1-256"
    assert 1 <= bytes_per_chunk <= 256, "bytes_per_chunk must be within 1-256"

    dump = []

    num_chunks = math.ceil(bytes_per_line / bytes_per_chunk)

    # Two char per byte plus the spaces in between each chunk.
    char_per_line = bytes_per_line * 2 + num_chunks - 1

    # Iterate one line at a time
    for i in range(0, len(data), bytes_per_line):

        raw  = ''
        text = ''

        # Iterate the data for this line.
        for j, b in enumerate(data[i:i+bytes_per_line]):

            # Add spaces in between each chunk.
            if 0 != j and 0 == j % bytes_per_chunk:
                raw += ' '

            # Convert to hex string.
            raw += ("%02X") % (b)

            # Convert to character.
            text += chr(b) if 0x20 <= b < 0x7f else '.'

        # Left justify to pad spaces on the right.
        raw  = raw.ljust(char_per_line)
        text = text.ljust(bytes_per_line)

        # Append a new line in the output
        dump.append(("%08X:  %s  |%s|") % (i, raw, text))

    return dump


# Default hex dump line format:
#     * 4 byte addresses
#     * 16 bytes per line
#     * 4 bytes per chunk
#     * ASCII representation of bytes surrounded by '|' characters
DEFAULT_LINE_FORMAT = \
    'AAAAAAAA:  DDDDDDDD DDDDDDDD DDDDDDDD DDDDDDDD  |CCCCCCCCCCCCCCCC|'


def parse(lines: list,
          line_format: str = DEFAULT_LINE_FORMAT) -> bytearray:
    """
    Parses a hex dump.

    Returns a bytearray of all the data bytes in the hex dump.

    The lines parameter is a list of strings containing the hex dump.

    The line_format parameter is a template that describes how to parse the hex
    dump lines.  The line_format string can contain the following characters:
        * 'A' represents one hex digit of the data address
        * 'D' represents one hex digit of the data
        * 'C' represents one character of the ASCII representation
        * All other characters (e.g. '|') are literal and must exist in line

    The data address and ASCII representation portions of the line format are
    optional.  This allows for parsing hex dumps that do not contain that
    information.

    The final line of the hex dump may contain less than the expected number of
    data bytes.  This occurs when the total data size is not a multiple of
    'bytes per line'.

    Ignores lines that do not match the specified line format.
    """

    hex_digit = re.compile('^[0-9a-fA-F]$')
    data = bytearray()
    for line in lines:
        line = line.rstrip('\n')
        prev_byte_is_high_nibble = False
        # Note: sometimes last line of hexdump is shorter than line format
        if len(line) <= len(line_format):
            for i in range(len(line)):
                if (line_format[i] == 'A'):
                    if not hex_digit.match(line[i]):
                        break
                elif (line_format[i] == 'D'):
                    if not hex_digit.match(line[i]):
                        break
                    if prev_byte_is_high_nibble:
                        byte_val = bytes.fromhex(line[(i-1):(i+1)])
                        data.extend(byte_val)
                        prev_byte_is_high_nibble = False
                    else:
                        prev_byte_is_high_nibble = True
                elif (line_format[i] == 'C'):
                    continue
                elif (line_format[i] != line[i]):
                    break
    return data
