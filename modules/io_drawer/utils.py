"""
This module contains shared utility functions.
"""


def format_timestamp(timestamp: int) -> str:
    """
    Converts the specified two-byte, unsigned integer timestamp to a
    string.

    Returns the formatted string.  Uses the format HH:MM:SS.

    Note: the timestamp is NOT correlated to real world time.  It is a simple
    second counter that rolls over at 0xFFFF.
    """

    # Verify timestamp is valid
    if (timestamp < 0) or (timestamp >= 0xFFFF):
        return '--------'

    hh = timestamp // 3600
    mm = (timestamp - (hh*3600)) // 60
    ss = timestamp - (hh*3600) - (mm*60)
    return f'{hh:2d}:{mm:02d}:{ss:02d}'
