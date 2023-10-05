import os
import unittest

from io_drawer.drawer_type import (DrawerType, MEX_DRAWER_TYPE, 
                                   NIMITZ_DRAWER_TYPE, DRAWER_TYPES)


class TestDrawerType(unittest.TestCase):
    """
    Unit tests for the DrawerType class.
    """

    def test__init__(self):
        drawer_type = DrawerType('foo', 'foo.h', 'fooSF', 5)
        self.assertEqual(drawer_type.name, 'foo')
        self.assertEqual(drawer_type.header_file_name, 'foo.h')
        self.assertEqual(drawer_type.string_file_name, 'fooSF')
        self.assertEqual(drawer_type.user_data_version, 5)

    def test_get_header_file_path(self):
        path = MEX_DRAWER_TYPE.get_header_file_path()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(os.path.basename(path), 'mex_pte.h')

        path = NIMITZ_DRAWER_TYPE.get_header_file_path()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(os.path.basename(path), 'nimitz_pte.h')

    def test_get_trace_string_file_path(self):
        path = MEX_DRAWER_TYPE.get_trace_string_file_path()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(os.path.basename(path), 'mexStringFile')

        path = NIMITZ_DRAWER_TYPE.get_trace_string_file_path()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(os.path.basename(path), 'nimitzStringFile')

    def test_constants(self):
        self.assertEqual(MEX_DRAWER_TYPE.name, 'mex')
        self.assertEqual(MEX_DRAWER_TYPE.header_file_name, 'mex_pte.h')
        self.assertEqual(MEX_DRAWER_TYPE.string_file_name, 'mexStringFile')
        self.assertEqual(MEX_DRAWER_TYPE.user_data_version, 1)

        self.assertEqual(NIMITZ_DRAWER_TYPE.name, 'nimitz')
        self.assertEqual(NIMITZ_DRAWER_TYPE.header_file_name, 'nimitz_pte.h')
        self.assertEqual(NIMITZ_DRAWER_TYPE.string_file_name, 'nimitzStringFile')
        self.assertEqual(NIMITZ_DRAWER_TYPE.user_data_version, 2)

        self.assertEqual(len(DRAWER_TYPES), 2)
        self.assertEqual(DRAWER_TYPES[0].name, 'mex')
        self.assertEqual(DRAWER_TYPES[1].name, 'nimitz')
