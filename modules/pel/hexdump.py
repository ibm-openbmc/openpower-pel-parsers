import math


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

        raw = ''
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
        raw = raw.ljust(char_per_line)
        text = text.ljust(bytes_per_line)

        # Append a new line in the output
        dump.append(("%08X:  %s  |%s|") % (i, raw, text))

    return dump
