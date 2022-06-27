import os
import unittest

from udparsers.m2c00.utils import get_header_file_path


class TestUtils(unittest.TestCase):

    def test_get_header_file_path(self):
        path = get_header_file_path()
        self.assertTrue(os.path.exists(path))
        self.assertEqual(os.path.basename(path), 'mex_pte.h')
