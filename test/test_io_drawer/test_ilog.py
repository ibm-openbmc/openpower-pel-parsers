import os
import re
import tempfile
import unittest

from io_drawer.ilog import PTETableEntry, PTETable, parse_ilog_data


class TestILogBase(unittest.TestCase):
    """
    Base class for unit tests for the ilog module.

    Contains shared setUp/tearDown code and utility methods.
    """

    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()
        self.header_file_path = tmp_file.name

    def tearDown(self):
        os.remove(self.header_file_path)

    def _assertEntry(self, entry: PTETableEntry, pte_pattern: str,
                     message_format: str, params: tuple, file: str, line: int,
                     re_pattern: str):
        self.assertEqual(entry.pte_pattern, pte_pattern)
        self.assertEqual(entry.message_format, message_format)
        self.assertEqual(entry.params, params)
        self.assertEqual(entry.file, file)
        self.assertEqual(entry.line, line)
        self.assertEqual(entry.pte_re.pattern, re_pattern)
        self.assertTrue((entry.pte_re.flags & re.IGNORECASE) != 0)

    def _create_header_file(self, lines: list):
        with open(self.header_file_path, 'w') as file:
            for line in lines:
                file.write(line)
                file.write('\n')


class TestPTETableEntry(TestILogBase):
    """
    Unit tests for the PTETableEntry class.
    """

    def test__init__(self):
        # No wildcard in PTE pattern, no parameters
        entry = PTETableEntry('15A00000',
                              'Bad non-volatile storage count offset',
                              (), 'nvs.cpp', 1001)
        self._assertEntry(entry, '15A00000',
                          'Bad non-volatile storage count offset',
                          (), 'nvs.cpp', 1001, '15A00000')

        # One wildcard in PTE pattern, one parameter
        entry = PTETableEntry('010000**',
                              'Begin power on, node type = 0x%02X',
                              (4,), 'states.cpp', 485)
        self._assertEntry(entry, '010000**',
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')

        # Two wildcards in PTE pattern, two parameters
        entry = PTETableEntry('0210****',
                              'Code level date stamp:  month %x, day %x',
                              (3, 4), 'elog.cpp', 863)
        self._assertEntry(entry, '0210****',
                          'Code level date stamp:  month %x, day %x',
                          (3, 4), 'elog.cpp', 863, '0210....')

        # One invalid parameter: < 1: Verify removed
        entry = PTETableEntry('0210****',
                              'Code level date stamp:  month %x, day %x',
                              (0, 4), 'elog.cpp', 863)
        self.assertEqual(entry.params, (4,))

        # One invalid parameter: > 4: Verify removed
        entry = PTETableEntry('0210****',
                              'Code level date stamp:  month %x, day %x',
                              (1, 5), 'elog.cpp', 863)
        self.assertEqual(entry.params, (1,))

        # All parameters invalid: Verify all removed
        entry = PTETableEntry('0210****',
                              'Code level date stamp:  month %x, day %x',
                              (-1, 99), 'elog.cpp', 863)
        self.assertEqual(entry.params, ())

    def test_get_message(self):
        # No parameters
        entry = PTETableEntry('01430000',
                              'New IO bay detected on power on.',
                              (), 'states.cpp', 380)
        msg = entry.get_message(0x01430000)
        self.assertEqual(msg, 'New IO bay detected on power on.')

        # One parameter and use of %d
        entry = PTETableEntry('0143**00',
                              'New IO bay %d detected on power on.',
                              (3,), 'states.cpp', 445)
        msg = entry.get_message(0x01430100)
        self.assertEqual(msg, 'New IO bay 1 detected on power on.')

        # Two parameters and use of %c
        entry = PTETableEntry('0200****',
                              'This PEROM level = %c%c',
                              (3, 4), 'states.cpp', 254)
        msg = entry.get_message(0x02004445)
        self.assertEqual(msg, 'This PEROM level = DE')

        # Two parameters in descending order and use of %X
        entry = PTETableEntry('0200****',
                              'This PEROM level = 0x%02X%02X',
                              (4, 3), 'states.cpp', 254)
        msg = entry.get_message(0x0200DEAD)
        self.assertEqual(msg, 'This PEROM level = 0xADDE')

        # Too few parameters for message format string
        entry = PTETableEntry('0200****',
                              'This PEROM level = 0x%02X%02X',
                              (4,), 'states.cpp', 254)
        msg = entry.get_message(0x0200DEAD)
        self.assertEqual(msg, 'This PEROM level = 0x%02X%02X')

        # Too many parameters for message format string
        entry = PTETableEntry('0143**00',
                              'New IO bay %d detected on power on.',
                              (3, 4), 'states.cpp', 445)
        msg = entry.get_message(0x01430100)
        self.assertEqual(msg, 'New IO bay %d detected on power on.')

        # Not a reported error: No suffix added
        entry = PTETableEntry('15A40000',
                              'Bad non-volatile storage count offset',
                              (), 'nvs.cpp', 1001)
        msg = entry.get_message(0x15A40000)
        self.assertEqual(msg, 'Bad non-volatile storage count offset')

        # Reported error: Adds suffix for PEL entry creation
        entry = PTETableEntry('E3087704',
                              'Fan Missing - System Fan 1',
                              (), 'sys_fan.cpp', 191)
        msg = entry.get_message(0xE30C7704)
        self.assertEqual(msg, 'Fan Missing - System Fan 1 - PEL entry created')

    def test_matches(self):
        # Exact match
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry.matches(0xE3087704))

        # Matches after removing reported error flag
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry.matches(0xE30C7704))

        # Doesn't match
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertFalse(entry.matches(0xE3087705))

    def test__is_exact_match(self):
        # Matches: No wildcard in PTE pattern
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry._is_exact_match(0xE3087704))

        # Matches: One wildcard in PTE pattern
        entry = PTETableEntry('E30877**', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry._is_exact_match(0xE30877AE))

        # Matches: Two wildcards in PTE pattern
        entry = PTETableEntry('E308****', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry._is_exact_match(0xE30823AE))

        # Doesn't match: No wildcard in PTE pattern
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertFalse(entry._is_exact_match(0xE3087705))

        # Doesn't match: One wildcard in PTE pattern
        entry = PTETableEntry('E30877**', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertFalse(entry._is_exact_match(0xE40877AE))

        # Doesn't match: Two wildcards in PTE pattern
        entry = PTETableEntry('E308****', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertFalse(entry._is_exact_match(0xE30A23AE))

    def test__is_reported_error_pte(self):
        # Not a reported error: First PTE byte is not 0xE*
        entry = PTETableEntry('15A40000', 'Bad NVS', (), 'nvs.cpp', 1001)
        self.assertFalse(entry._is_reported_error_pte(0x15A40000))

        # Not a reported error: Second PTE byte doesn't have reported flag 0x04
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertFalse(entry._is_reported_error_pte(0xE3087704))

        # Reported error
        entry = PTETableEntry('E3087704', 'Fan Missing', (), 'sys_fan.cpp', 191)
        self.assertTrue(entry._is_reported_error_pte(0xE30C7704))


class TestPTETable(TestILogBase):
    """
    Unit tests for the PTETable class.
    """

    def test__init__(self):
		# Test with real header file generated during firmware build
        table = PTETable()
        self.assertTrue(os.path.exists(table.header_file_path))
        self.assertEqual(os.path.basename(table.header_file_path), 'mex_pte.h')
        self.assertTrue(len(table.entries) > 600)

        # Test with dummy header file: Standard C++ format
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "010000**", "Begin power on, node type = 0x%02X", {4}, "states.cpp", 485 },',
            '  { "01040000", "Power on complete", {}, "states2.cpp", 601 },',
            '  { ""        , "The End" }',
            '};'
        ])
        table = PTETable(self.header_file_path)
        self.assertEqual(table.header_file_path, self.header_file_path)
        self.assertEqual(len(table.entries), 2)
        self._assertEntry(table.entries[0], '010000**', 
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')
        self._assertEntry(table.entries[1], '01040000', 
                          'Power on complete',
                          (), 'states2.cpp', 601, '01040000')

        # Test where header file does not exist
        with self.assertRaises(Exception):
            table = PTETable('/does_not_exist/dne/mex_pte.h')

    def test_get_entry(self):
        # Create dummy header file and load into PTE table
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { "01040000", "Power on complete", {}, "states2.cpp", 601 },',
            '  { ""        , "The End" }',
            '};'
        ])
        table = PTETable(self.header_file_path)

        # Test where matching entry is found: No wildcards in PTE pattern
        self.assertIsNotNone(table.get_entry(0x01040000))

        # Test where matching entry is found: Wildcards in PTE pattern
        self.assertIsNotNone(table.get_entry(0x0101BEEF))

        # Test where matching entry is not found
        self.assertIsNone(table.get_entry(0x0102BEEF))

    def test__add_entry(self):
        # Create empty header file and empty PTE table
        self._create_header_file([''])
        table = PTETable(self.header_file_path)
        self.assertEqual(len(table.entries), 0)

        # Add entry with no PTE wildcards and 0 parameters
        table._add_entry(('01040000', 'Power on complete',
                          '', 'states.cpp', '601'))
        self.assertEqual(len(table.entries), 1)
        self._assertEntry(table.entries[0], '01040000', 
                          'Power on complete',
                          (), 'states.cpp', 601, '01040000')

        # Add entry with PTE wildcards, 1 parameter, and trailing whitespace in
        # message format field
        table._add_entry(('100100**', 'PS%d - Faults Cleared    ',
                          ' 4 ', 'mps.cpp', '759'))
        self.assertEqual(len(table.entries), 2)
        self._assertEntry(table.entries[1], '100100**', 
                          'PS%d - Faults Cleared',
                          (4,), 'mps.cpp', 759, '100100..')

        # Add entry with PTE wildcards and 2 parameters
        table._add_entry(('2065****', 'IO Bay %d type = %d',
                          ' 3 , 4 ', 'vpd_col.cpp', '2635'))
        self.assertEqual(len(table.entries), 3)
        self._assertEntry(table.entries[2], '2065****', 
                          'IO Bay %d type = %d',
                          (3, 4), 'vpd_col.cpp', 2635, '2065....')

        # Add entry with escaped double quotes
        table._add_entry(('E2082690', r'P1 IO Bay VRM in \"N-Mode\" ',
                          '', 'vrm_monitor.cpp', '145'))
        self.assertEqual(len(table.entries), 4)
        self._assertEntry(table.entries[3], 'E2082690', 
                          'P1 IO Bay VRM in "N-Mode"',
                          (), 'vrm_monitor.cpp', 145, 'E2082690')

        # Specify invalid number of fields (4).  Should return without adding a
        # new entry.
        table._add_entry(('15D10000', 'POP non-volatile storage update',
                          '', 'nvs.cpp'))
        self.assertEqual(len(table.entries), 4)

    def test__parse_header_file(self):
		# Test with real header file generated during firmware build
        table = PTETable()
        table.entries = []
        table._parse_header_file()
        self.assertTrue(len(table.entries) > 600)

        # Test with dummy header file: Standard C++ format
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "010000**", "Begin power on, node type = 0x%02X", {4}, "states.cpp", 485 },',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { "01040000", "Power on complete", {}, "states2.cpp", 601 },',
            '  // The following must be the last entry',
            '  { ""        , "The End" }',
            '};'
        ])
        table.header_file_path = self.header_file_path
        table.entries = []
        table._parse_header_file()
        self.assertEqual(len(table.entries), 3)
        self._assertEntry(table.entries[0], '010000**', 
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')
        self._assertEntry(table.entries[1], '0101****', 
                          'Fan presence 0x%02X, flash = %c',
                          (4, 3), 'fan.cpp', 530, '0101....')
        self._assertEntry(table.entries[2], '01040000', 
                          'Power on complete',
                          (), 'states2.cpp', 601, '01040000')

        # Test with dummy header file: Extra white space
        self._create_header_file([
            ' struct  pte_entry_struct  static_pte_entry_table [ PTE_TABLE_SIZE ] =   ',
            ' { ',
            '  {  "010000**" , "Begin power on, node type = 0x%02X  " , { 4 } , "states.cpp" , 485 } , ',
            '  {  "0101****" , "Fan presence 0x%02X, flash = %c  " , { 4 , 3 } , "fan.cpp" , 530 } , ',
            '  {  "01040000" , "  Power on complete  " , {  } , "states2.cpp" , 601 } , ',
            '  {  ""        ,  "The End"  }  ',
            '  }  ;'
        ])
        table.entries = []
        table._parse_header_file()
        self.assertEqual(len(table.entries), 3)
        self._assertEntry(table.entries[0], '010000**', 
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')
        self._assertEntry(table.entries[1], '0101****', 
                          'Fan presence 0x%02X, flash = %c',
                          (4, 3), 'fan.cpp', 530, '0101....')
        self._assertEntry(table.entries[2], '01040000', 
                          'Power on complete',
                          (), 'states2.cpp', 601, '01040000')

        # Test with dummy header file: Minimal white space
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[]={',
            '{"010000**","Begin power on, node type = 0x%02X",{4},"states.cpp",485},',
            '{"0101****","Fan presence 0x%02X, flash = %c",{4,3},"fan.cpp",530},',
            '{"01040000","Power on complete",{},"states2.cpp",601},',
            '{"","The End"}',
            '};'
        ])
        table.entries = []
        table._parse_header_file()
        self.assertEqual(len(table.entries), 3)
        self._assertEntry(table.entries[0], '010000**', 
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')
        self._assertEntry(table.entries[1], '0101****', 
                          'Fan presence 0x%02X, flash = %c',
                          (4, 3), 'fan.cpp', 530, '0101....')
        self._assertEntry(table.entries[2], '01040000', 
                          'Power on complete',
                          (), 'states2.cpp', 601, '01040000')

        # Test with dummy header file: Invalid lines and escaped double quotes
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '  ',
            '{',
            '  // State PTEs',
            '  { "010000**", "Begin power on, node type = 0x%02X", {4}, "states.cpp", 485 },',
            '  ',
            '  // { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
           r'  { "E2082690", "P1 IO Bay VRM in \"N-Mode\" ", {}, "vrm_monitor.cpp", 145 },',
            '  { "01040000", "Power on complete", {}, "states2.cpp", 601 },',
            '  // The following must be the last entry',
            '  ',
            '  { ""        , "The End" }',
            '  ',
            '};'
        ])
        table.entries = []
        table._parse_header_file()
        self.assertEqual(len(table.entries), 3)
        self._assertEntry(table.entries[0], '010000**', 
                          'Begin power on, node type = 0x%02X',
                          (4,), 'states.cpp', 485, '010000..')
        self._assertEntry(table.entries[1], 'E2082690', 
                          'P1 IO Bay VRM in "N-Mode"',
                          (), 'vrm_monitor.cpp', 145, 'E2082690')
        self._assertEntry(table.entries[2], '01040000', 
                          'Power on complete',
                          (), 'states2.cpp', 601, '01040000')

        # Test where header file does not exist
        table.header_file_path = '/does_not_exist/dne/mex_pte.h'
        with self.assertRaises(Exception):
            table._parse_header_file()


class TestILog(TestILogBase):
    """
    Unit tests for functions in the ilog module.
    """

    def test_parse_ilog_data(self):
		# Test with real header file generated during firmware build
        data = memoryview(                      # ILOG entry 1
                          b'\x8A\xDF'           #   timestamp
                          b'\x0F\x19'           #   seq_num
                          b'\x01\x00\x00\xDE'   #   pte (010000**)
                                                # ILOG entry 2
                          b'\x8D\x47'           #   timestamp
                          b'\x10\x24'           #   seq_num
                          b'\x01\x04\x00\x00')  #   pte (01040000)
        lines = parse_ilog_data(data)
        expected_lines = [
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            ' 9:52:31 0F19 010000DE Begin power on, node type = 0xDE',
            '10:02:47 1024 01040000 Power on complete',
        ]
        self.assertEqual(lines, expected_lines)

        # Test with dummy header file.  Verify ignores ILOG entry with all
        # fields set to 0.  Test where PTE is undefined (not found in table).
        # Test where the last ILOG entry is truncated.
        self._create_header_file([
            'struct pte_entry_struct static_pte_entry_table[PTE_TABLE_SIZE] = ',
            '{',
            '  { "010000**", "Begin power on, node type = 0x%02X", {4}, "states.cpp", 485 },',
            '  { "0101****", "Fan presence 0x%02X, flash = %c", {4, 3}, "fan.cpp", 530 },',
            '  { "01040000", "Power on complete", {}, "states2.cpp", 601 },',
            '  { ""        , "The End" }',
            '};'
        ])
        data = memoryview(                      # ILOG entry 1 - all zeros
                          b'\x00\x00'           #   timestamp
                          b'\x00\x00'           #   seq_num
                          b'\x00\x00\x00\x00'   #   pte
                                                # ILOG entry 2
                          b'\x8D\x47'           #   timestamp
                          b'\xDE\xAD'           #   seq_num
                          b'\x01\x00\x00\x03'   #   pte (010000**)
                                                # ILOG entry 3 - undefined PTE
                          b'\x8D\xD4'           #   timestamp
                          b'\xDF\x98'           #   seq_num
                          b'\x01\x02\x00\x03'   #   pte
                                                # ILOG entry 4
                          b'\x8D\xE3'           #   timestamp
                          b'\xDF\xA0'           #   seq_num
                          b'\x01\x01\x44\xEF'   #   pte (0101****)
                                                # ILOG entry 5
                          b'\x8D\xF1'           #   timestamp
                          b'\xDF\xA7'           #   seq_num
                          b'\x01\x04\x00\x00'   #   pte (01040000)
                                                # ILOG entry 6 - truncated
                          b'\x8D\xF9'           #   timestamp
                          b'\xDF\xAC'           #   seq_num
                          b'\x01\x02\x00')      #   pte
        lines = parse_ilog_data(data, self.header_file_path)
        expected_lines = [
            'hh:mm:ss seq  pppppppp description',
            '-------- ---- -------- ------------------------------------',
            '10:02:47 DEAD 01000003 Begin power on, node type = 0x03',
            '10:05:08 DF98 01020003 Undefined',
            '10:05:23 DFA0 010144EF Fan presence 0xEF, flash = D',
            '10:05:37 DFA7 01040000 Power on complete',
        ]
        self.assertEqual(lines, expected_lines)
