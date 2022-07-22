import unittest

from udparsers.m2c00.m2c00 import (_parse_hlog, _parse_ilog, _parse_trace,
                                   _parse_unsupported, parseUDToJson)


class TestM2C00(unittest.TestCase):

    def test__parse_hlog(self):
        version = 1
        key = 'History Log'

        # Test where there is no user data
        data = memoryview(b'')
        output = _parse_hlog(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key], [])

        # Test where there is user data
        data = memoryview(b'\x00\xDE\xAD')
        output = _parse_hlog(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key][0], 'Hex Dump')


    def test__parse_ilog(self):
        version = 1
        key = 'ILOG'

        # Test where there is no user data
        data = memoryview(b'')
        output = _parse_ilog(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key], [])

        # Test where there is user data
        data = memoryview(b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE')  #   pte
        output = _parse_ilog(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key][0], 'hh:mm:ss seq  pppppppp description')


    def test__parse_trace(self):
        version = 1
        key = 'Trace'

        # Test where there is no user data
        data = memoryview(b'')
        output = _parse_trace(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key], [])

        # Test where there is user data
        data = memoryview(                      # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x49\x49\x43\x53'   #   comp (IICS)
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x20'   #   size (32)
                          b'\x00\x00\x00\x00'   #   times_wrap
                          b'\x00\x00\x00\x20')  #   next_free
        output = _parse_trace(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key][0], 'Component: IICS')


    def test__parse_unsupported(self):
        version = 1
        key = 'Data'

        # Test where there is no user data
        data = memoryview(b'')
        output = _parse_unsupported(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key], [])

        # Test where there is user data
        data = memoryview(b'\xde\xad\xbe\xef')
        output = _parse_unsupported(version, data)
        self.assertEqual(len(output), 1)
        self.assertTrue(key in output)
        self.assertEqual(output[key][0],
                         '00000000:  DEADBEEF                             |....            |')


    def test_parseUDToJson(self):
        version = 1

        # Test where sub-section type is history log data
        data = memoryview(b'\x00\xDE\xAD')
        sub_type = 72
        output = parseUDToJson(sub_type, version, data)
        self.assertTrue(output.startswith('{"History Log":'))

        # Test where sub-section type is ilog/PTE data
        data = memoryview(b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE')  #   pte
        sub_type = 73
        output = parseUDToJson(sub_type, version, data)
        self.assertTrue(output.startswith('{"ILOG":'))

        # Test where sub-section type is trace data
        data = memoryview(                      # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x49\x49\x43\x53'   #   comp (IICS)
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x20'   #   size (32)
                          b'\x00\x00\x00\x00'   #   times_wrap
                          b'\x00\x00\x00\x20')  #   next_free
        sub_type = 84
        output = parseUDToJson(sub_type, version, data)
        self.assertTrue(output.startswith('{"Trace":'))

        # Test where sub-section type is unsupported
        data = memoryview(b'\xde\xad\xbe\xef')
        sub_type = 85
        output = parseUDToJson(sub_type, version, data)
        self.assertTrue(output.startswith('{"Data":'))
