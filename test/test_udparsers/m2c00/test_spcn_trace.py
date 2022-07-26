import os
import tempfile
import unittest

from udparsers.m2c00.spcn_trace import (_format_ilog_data, _format_trace_data,
                                        parse_spcn_trace_data,
                                        parse_spcn_trace_file)


class TestSPCNTrace(unittest.TestCase):

    def setUp(self):
        self.header_file_path = self._create_temp_file()
        self.spcn_trace_file_path = self._create_temp_file()
        self.string_file_path = self._create_temp_file()

    def tearDown(self):
        os.remove(self.header_file_path)
        os.remove(self.spcn_trace_file_path)
        os.remove(self.string_file_path)

    def _create_header_file(self, lines: list):
        self._write_file(self.header_file_path, lines)

    def _create_spcn_trace_file(self, lines: list):
        self._write_file(self.spcn_trace_file_path, lines)

    def _create_string_file(self, lines: list):
        self._write_file(self.string_file_path, lines)

    def _create_temp_file(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()
        return tmp_file.name

    def _write_file(self, path: str, lines: list):
        with open(path, 'w') as file:
            for line in lines:
                file.write(line)
                file.write('\n')

    def test__format_ilog_data(self):
		# Test with real header file generated during firmware build
        data = memoryview(                      # ILOG entry 1
                          b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE'   #   pte (010000**)
                                                # ILOG entry 2
                          b'\x8D\x47'           #   timestamp
                          b'\x10\x24'           #   seq_num
                          b'\x01\x04\x00\x00')  #   pte (01040000)
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            ' 9:52:31 0F19 010000DE Begin power on, node type = 0xDE',
            '10:02:47 1024 01040000 Power on complete',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = []
        _format_ilog_data(data, lines)
        self.assertEqual(lines, expected_lines)

        # Test with dummy header file
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { ""        , "The End" }',
            '};'
        ])
        data = memoryview(b'\x8D\xE3'           # timestamp
                          b'\xDF\xA0'           # seq_num
                          b'\x01\x01\x44\xEF')  # pte (0101****)
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            '10:05:23 DFA0 010144EF Fan presence 0xEF, flash = D',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = []
        _format_ilog_data(data, lines, self.header_file_path)
        self.assertEqual(lines, expected_lines)

    def test__format_trace_data(self):
		# Test with real string file generated during firmware build
        data = memoryview(                      # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x3C'   #   size (32 + 28 = 60)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00\x3D'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh (9:51:39)
                          b'\x01\x23'           #   tbl
                          b'\x00\x07'           #   length (7)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\xFF\xFF\xFF\xFF'   #   hash_value (4294967295)
                          b'\x00\x00\x02\x32'   #   line (562)
                          b'\x01\x02\x03\x04'   #   data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               #   padding for 4-byte alignment
                          b'\x00\x00\x00\x1C')  #   entry_size (28)
        expected_lines = [
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:51:39 0123   562 No trace string found with hash value 4294967295',
            '                    00000000:  01020304 DEADBE                      |.......         |',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = []
        _format_trace_data(data, lines)
        self.assertEqual(lines, expected_lines)

        # Test with dummy string file
        self._create_string_file([
            '32413714||E> Dev 0x%x: Fail count = %d||adt7470_fan_ctl.cpp(324)',
        ])
        data = memoryview(                      # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x3C'   #   size (32 + 28 = 60)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00\x54'   #   next_free
                                                # entry 1
                          b'\x8A\xDF'           #   tbh (9:52:31)
                          b'\x01\x86'           #   tbl
                          b'\x00\x08'           #   length (8)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x01\xEE\x98\x12'   #   hash_value (32413714)
                          b'\x00\x00\x01\x44'   #   line (324)
                          b'\x00\x00\xFA\x04'   #   data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C')  #   entry_size (28)
        expected_lines = [
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:52:31 0186   324 E> Dev 0xfa04: Fail count = 48879',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = []
        _format_trace_data(data, lines, self.string_file_path)
        self.assertEqual(lines, expected_lines)

    def test_parse_spcn_trace_data(self):
        # Test where there is no data
        data = memoryview(b'')
        expected_lines = []
        lines = parse_spcn_trace_data(data)
        self.assertEqual(lines, expected_lines)

        # Test where there is only ILOG data.
		# Use real header file and string file generated during firmware build.
        data = memoryview(                      # ILOG entry 1
                          b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE')  #   pte (010000**)
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            ' 9:52:31 0F19 010000DE Begin power on, node type = 0xDE',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = parse_spcn_trace_data(data)
        self.assertEqual(lines, expected_lines)

        # Test where there is ILOG data and one trace buffer.
		# Use real header file and string file generated during firmware build.
        data = memoryview(                      # ILOG entry 1
                          b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE'   #   pte (010000**)
                                                # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x3C'   #   size (32 + 28 = 60)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00\x3D'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh (9:51:39)
                          b'\x01\x23'           #   tbl
                          b'\x00\x07'           #   length (7)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\xFF\xFF\xFF\xFF'   #   hash_value (4294967295)
                          b'\x00\x00\x02\x32'   #   line (562)
                          b'\x01\x02\x03\x04'   #   data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               #   padding for 4-byte alignment
                          b'\x00\x00\x00\x1C')  #   entry_size (28)
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            ' 9:52:31 0F19 010000DE Begin power on, node type = 0xDE',
            '',
            '-------------------------------------------------------------------------',
            '',
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:51:39 0123   562 No trace string found with hash value 4294967295',
            '                    00000000:  01020304 DEADBE                      |.......         |',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = parse_spcn_trace_data(data)
        self.assertEqual(lines, expected_lines)

        # Test where there is ILOG data and multiple trace buffers
        # Use dummy header file and string file.
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { ""        , "The End" }',
            '};'
        ])
        self._create_string_file([
            '276406914||Cmd Data: 0x%08X||cmds_util.cpp(2764)',
            '32413714||E> Dev 0x%x: Fail count = %d||adt7470_fan_ctl.cpp(324)'
        ])
        data = memoryview(                      # ILOG entry 1
                          b'\x8D\xE3'           #   timestamp
                          b'\xDF\xA0'           #   seq_num
                          b'\x01\x01\x44\xEF'   #   pte (0101****)
                                                # buffer header 1 (FANS)
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x3C'   #   size (32 + 28 = 60)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00\x3D'   #   next_free
                                                # entry 1
                          b'\x8A\xDF'           #   tbh (9:52:31)
                          b'\x01\x86'           #   tbl
                          b'\x00\x08'           #   length (8)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x01\xEE\x98\x12'   #   hash_value (32413714)
                          b'\x00\x00\x01\x44'   #   line (324)
                          b'\x00\x00\xFA\x04'   #   data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C'   #   entry_size (28)
                                                # buffer header 2 (POWR)
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x50\x4f\x57\x52'   #   comp (POWR)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x38'   #   size (32 + 24 = 56)
                          b'\x00\x00\x00\x02'   #   times_wrap (2)
                          b'\x00\x00\x00\x38'   #   next_free
                                                # entry 1
                          b'\x8A\xE1'           #   tbh (9:52:33)
                          b'\x01\x87'           #   tbl
                          b'\x00\x04'           #   length (4)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x10\x79\xA2\x82'   #   hash_value (276406914)
                          b'\x00\x00\x0A\xCC'   #   line (2764)
                          b'\xBA\xDC\x0F\xFE'   #   data
                          b'\x00\x00\x00\x18')  #   entry_size (24)
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            '10:05:23 DFA0 010144EF Fan presence 0xEF, flash = D',
            '',
            '-------------------------------------------------------------------------',
            '',
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:52:31 0186   324 E> Dev 0xfa04: Fail count = 48879',
            '',
            '-------------------------------------------------------------------------',
            '',
            'Trace',
            '',
            'Component: POWR',
            'Version: 2',
            'Size: 56',
            'Times Wrapped: 2',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:52:33 0187  2764 Cmd Data: 0xBADC0FFE',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = parse_spcn_trace_data(data, self.header_file_path,
                                      self.string_file_path)
        self.assertEqual(lines, expected_lines)

    def test_parse_spcn_trace_file(self):
        # Test where works.  Use real header file and string file generated
        # during firmware build.  Hexdump in format used by BMC web interface.
        self._create_spcn_trace_file([
            '0000:  8ADF0F19 010000DE 02200142 46414e53  <......... .BFANS>',
            '0010:  20202020 00000000 00000000 0000003C  <    ...........<>',
            '0020:  000000FE 0000003D 8AAB0123 00074644  <.......=...#..FD>',
            '0030:  FFFFFFFF 00000232 01020304 DEADBE00  <.......2........>',
            '0040:  0000001C                             <....            >'
        ])
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            ' 9:52:31 0F19 010000DE Begin power on, node type = 0xDE',
            '',
            '-------------------------------------------------------------------------',
            '',
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:51:39 0123   562 No trace string found with hash value 4294967295',
            '                    00000000:  01020304 DEADBE                      |.......         |',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = parse_spcn_trace_file(self.spcn_trace_file_path)
        self.assertEqual(lines, expected_lines)

        # Test where works.  Use dummy header file and string file.  Hexdump is
        # in format used by pre-BMC web interface.
        self._create_spcn_trace_file([
            '8D E3 DF A0 01 01 44 EF 02 20 01 42 46 41 4E 53 ......D.. .BFANS',
            '20 20 20 20 00 00 00 00 00 00 00 00 00 00 00 3C     ...........<',
            '00 00 00 FE 00 00 00 3D 8A DF 01 86 00 08 46 54 .......=......FT',
            '01 EE 98 12 00 00 01 44 00 00 FA 04 00 00 BE EF .......D........',
            '00 00 00 1C                                     ....            '
        ])
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { ""        , "The End" }',
            '};'
        ])
        self._create_string_file([
            '32413714||E> Dev 0x%x: Fail count = %d||adt7470_fan_ctl.cpp(324)'
        ])
        expected_lines = [
            'ILOG',
            '',
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            '10:05:23 DFA0 010144EF Fan presence 0xEF, flash = D',
            '',
            '-------------------------------------------------------------------------',
            '',
            'Trace',
            '',
            'Component: FANS',
            'Version: 2',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:52:31 0186   324 E> Dev 0xfa04: Fail count = 48879',
            '',
            '-------------------------------------------------------------------------',
            ''
        ]
        lines = parse_spcn_trace_file(self.spcn_trace_file_path,
                                      self.header_file_path,
                                      self.string_file_path)
        self.assertEqual(lines, expected_lines)

        # Test where fails.  No data is found in SPCN Trace file.
        self._create_spcn_trace_file([])
        lines = parse_spcn_trace_file(self.spcn_trace_file_path)
        self.assertEqual(lines, [])

        # Test where fails.  SPCN Trace file has unexpected hex dump line
        # format.
        self._create_spcn_trace_file([
            '00000000:  DEADBEEF BADC0FFE 42414443 30464645  |........BADC0FFE|'
        ])
        lines = parse_spcn_trace_file(self.spcn_trace_file_path)
        self.assertEqual(lines, [])

        # Test where fails.  SPCN Trace file does not exist.
        with self.assertRaises(Exception):
            lines = parse_spcn_trace_file('/does_not_exist/dne/spcn_trace')
