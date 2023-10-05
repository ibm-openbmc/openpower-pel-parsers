"""
This module contains data types related to I/O drawer types.
"""

import os


class DrawerType:
    """
    Represents an I/O drawer type.
    """

    def __init__(self, name: str, header_file_name: str, string_file_name: str,
                 user_data_version: int):
        """
        Constructor.
        """

        self.name = name
        self.header_file_name = header_file_name
        self.string_file_name = string_file_name
        self.user_data_version = user_data_version

    def get_header_file_path(self) -> str:
        """
        Returns the path to the C++ header file that contains ilog and history
        log definitions.
        """

        return os.path.join(os.path.dirname(__file__), self.header_file_name)

    def get_trace_string_file_path(self) -> str:
        """
        Returns the path to the file that contains the trace strings.
        """

        return os.path.join(os.path.dirname(__file__), self.string_file_name)


"""
Supported I/O drawer types.
"""
MEX_DRAWER_TYPE = DrawerType('mex', 'mex_pte.h', 'mexStringFile', 1)
NIMITZ_DRAWER_TYPE = DrawerType('nimitz', 'nimitz_pte.h', 'nimitzStringFile', 2)
DRAWER_TYPES = [ MEX_DRAWER_TYPE, NIMITZ_DRAWER_TYPE ]
