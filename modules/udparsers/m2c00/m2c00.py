"""
User data parser for error logs from an I/O drawer.
"""

from collections import OrderedDict
import json

from io_drawer.hlog import parse_hlog_data
from io_drawer.ilog import parse_ilog_data
from io_drawer.trace import parse_trace_data
from pel.hexdump import hexdump


# Supported sub-section types
SUB_TYPE_HLOG = 72
SUB_TYPE_ILOG = 73
SUB_TYPE_TRACE = 84


def _parse_hlog(version: int, data: memoryview) -> dict:
    """
    Parses history log data.

    Returns a dictionary containing the parser output.
    """

    lines = []
    if data:
        lines = parse_hlog_data(data)
    return {'History Log': lines}


def _parse_ilog(version: int, data: memoryview) -> dict:
    """
    Parses ilog (PTE) data.

    Returns a dictionary containing the parser output.
    """

    lines = []
    if data:
        lines = parse_ilog_data(data)
    return {'ILOG': lines}


def _parse_trace(version: int, data: memoryview) -> dict:
    """
    Parses trace data.

    Returns a dictionary containing the parser output.
    """

    lines = []
    if data:
        lines = parse_trace_data(data)
    return {'Trace': lines}


def _parse_unsupported(version: int, data: memoryview) -> dict:
    """
    Parses user data with an unsupported sub-section type.

    Returns a dictionary containing the parser output.
    """

    lines = []
    if data:
        lines = hexdump(data)
    return {'Data': lines}


def parseUDToJson(sub_type: int, version: int, data: memoryview) -> str:
    """
    Required function provided by all user data parsers.

    Parses and formats the data based on the sub-section type.

    Returns the output as a string in JSON format.
    """

    # Get parser function for the specified sub-section type
    parsers = {
        SUB_TYPE_HLOG: _parse_hlog,
        SUB_TYPE_ILOG: _parse_ilog,
        SUB_TYPE_TRACE: _parse_trace
    }
    parser = parsers.get(sub_type, _parse_unsupported)

    # Call parser function to format the data
    output = OrderedDict()
    try:
        output = parser(version, data)
    except Exception as e:
        output['Error'] = f'Unable to format data: {str(e)}'
        output['Data'] = hexdump(data)

    # Return formatted output as a JSON string
    return json.dumps(output)
