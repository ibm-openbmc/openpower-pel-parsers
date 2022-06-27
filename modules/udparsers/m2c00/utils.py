"""
This module contains shared utility functions.
"""

import os


def get_header_file_path():
    """
    Returns the path to the C++ header file that contains ilog and
    history log definitions.
    """
    return os.path.join(os.path.dirname(__file__), 'mex_pte.h')
