import os
import tempfile
import unittest

from udparsers.m2c00.hlog import get_hlog_fields, parse_hlog_data


class TestHLog(unittest.TestCase):

    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()
        self.header_file_path = tmp_file.name

    def tearDown(self):
        os.remove(self.header_file_path)

    def _create_header_file(self, lines: list):
        with open(self.header_file_path, 'w') as file:
            for line in lines:
                file.write(line)
                file.write('\n')

    def test_get_hlog_fields(self):

		# Test with real header file generated during firmware build
        fields = get_hlog_fields()
        self.assertTrue(len(fields) > 37)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[19].name, 'hl_pel_entries_created')
        self.assertEqual(fields[19].size, 2)
        self.assertEqual(fields[37].name, 'hl_ss_sets')
        self.assertEqual(fields[37].size, 1)

        # Test with dummy header file: standard C++ format
        self._create_header_file([
            'struct mex_hlog_field mex_hlog_fields[MEX_HLOG_FIELD_COUNT] =',
            '{',
            '  { 1, "hl_isolated_standby" },',
            '  { 2, "hl_power_ups" }',
            '};'
        ])
        fields = get_hlog_fields(self.header_file_path)
        self.assertTrue(len(fields) == 2)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[1].name, 'hl_power_ups')
        self.assertEqual(fields[1].size, 2)

        # Test with dummy header file: Extra white space
        self._create_header_file([
            '  ',
            ' struct   mex_hlog_field   mex_hlog_fields [ MEX_HLOG_FIELD_COUNT ]  = ',
            '  ',
            '  { ',
            '  { 1 , "hl_isolated_standby" }  , ',
            '  ',
            '  { 2 , "hl_power_ups" }  ',
            '  ',
            '  } ;  '
        ])
        fields = get_hlog_fields(self.header_file_path)
        self.assertTrue(len(fields) == 2)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[1].name, 'hl_power_ups')
        self.assertEqual(fields[1].size, 2)

        # Test with dummy header file: Minimal white space
        self._create_header_file([
            'struct mex_hlog_field mex_hlog_fields[]={',
            '{1,"hl_isolated_standby"},',
            '{2,"hl_power_ups"},',
            '};'
        ])
        fields = get_hlog_fields(self.header_file_path)
        self.assertTrue(len(fields) == 2)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[1].name, 'hl_power_ups')
        self.assertEqual(fields[1].size, 2)

        # Test with dummy header file: Invalid field sizes
        self._create_header_file([
            'struct mex_hlog_field mex_hlog_fields[MEX_HLOG_FIELD_COUNT] =',
            '{',
            '  { 1, "hl_isolated_standby" },',
            '  { 0, "hl_net_block_crc_failures" },',
            '  { 2, "hl_power_ups" }',
            '  { 3, "hl_left_iobay_removes" }',
            '};'
        ])
        fields = get_hlog_fields(self.header_file_path)
        self.assertTrue(len(fields) == 2)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[1].name, 'hl_power_ups')
        self.assertEqual(fields[1].size, 2)

        # Test with dummy header file: Invalid lines
        self._create_header_file([
            'foo bar {',
            '};',
            'struct mex_hlog_field mex_hlog_fields[MEX_HLOG_FIELD_COUNT] =',
            '{',
            '  { 1, "hl_isolated_standby" },',
            '    1, "hl_net_block_crc_failures"',
            '  { 2, "hl_power_ups" }',
            '  { "hl_left_iobay_removes" }',
            '};',
            'baz'
        ])
        fields = get_hlog_fields(self.header_file_path)
        self.assertTrue(len(fields) == 2)
        self.assertEqual(fields[0].name, 'hl_isolated_standby')
        self.assertEqual(fields[0].size, 1)
        self.assertEqual(fields[1].name, 'hl_power_ups')
        self.assertEqual(fields[1].size, 2)

        # Test where header file does not exist
        with self.assertRaises(Exception):
            fields = get_hlog_fields('/does_not_exist/dne/mex_pte.h')

    def test_parse_hlog_data(self):

		# Test with real header file generated during firmware build
        data = memoryview(b'\x23'     # hl_isolated_standby
                          b'\x01'     # hl_net_block_crc_failures
                          b'\x12\x46' # hl_power_ups
                          b'\x07'     # hl_left_iobay_removes
                          b'\xA1'     # hl_right_iobay_removes
                          b'\x13'     # hl_nmi_calls
                          b'\xFF'     # hl_fpga_init_retries
                          b'\x2f'     # hl_unused_ints_calls
                          b'\x00'     # hl_software_trap_calls
                          b'\x02'     # hl_fpga_alert_retries
                          b'\xAB'     # hl_previous_level
                          b'\x16'     # hl_code_updates
                          b'\x21'     # hl_crc_table_corrupt
                          b'\xEF'     # hl_ac_loss
                          b'\x20'     # hl_unavailable_pel_entry
                          b'\x21'     # hl_incorrect_pel_state
                          b'\x03'     # hl_invalid_pel_state
                          b'\x00'     # hl_src_mismatch
                          b'\x00'     # hl_pel_entry_overwrite
                          b'\x16\xF7' # hl_pel_entries_created
                          b'\x88'     # hl_led_sets
                          b'\x09'     # hl_sys_fan_removes
                          b'\x20\x03' # hl_sys_fan_events
                          b'\x02\x30' # hl_mps_fan_events
                          b'\x0B'     # hl_fan_ctl_events
                          b'\x11'     # hl_sensor_events
                          b'\x00'     # hl_service_mode
                          b'\x03'     # hl_1F02_info_logs
                          b'\x98\x76' # hl_i2c_bus1_events
                          b'\x56\x89' # hl_i2c_bus2_events
                          b'\x10\x10' # hl_i2c_bus3_events
                          b'\x01\x01' # hl_i2c_bus4_events
                          b'\x01'     # hl_i2c_bus1_recovered
                          b'\x02'     # hl_i2c_bus2_recovered
                          b'\x00'     # hl_i2c_bus3_recovered
                          b'\x04'     # hl_i2c_bus4_recovered
                          b'\x00'     # hl_hswp_ctl_events
                          b'\xF0')    # hl_ss_sets
        lines = parse_hlog_data(data)
        expected_lines = [
            'Hex Dump:',
            '',
            '00000000:  23011246 07A113FF 2F0002AB 1621EF20  |#..F..../....!. |',
            '00000010:  21030000 16F78809 20030230 0B110003  |!....... ..0....|',
            '00000020:  98765689 10100101 01020004 00F0      |.vV...........  |',
            '',
            'Non-Zero Field Values:',
            '',
            'hl_isolated_standby: 0x23',
            'hl_net_block_crc_failures: 0x01',
            'hl_power_ups: 0x1246',
            'hl_left_iobay_removes: 0x07',
            'hl_right_iobay_removes: 0xA1',
            'hl_nmi_calls: 0x13',
            'hl_fpga_init_retries: 0xFF',
            'hl_unused_ints_calls: 0x2F',
            'hl_fpga_alert_retries: 0x02',
            'hl_previous_level: 0xAB',
            'hl_code_updates: 0x16',
            'hl_crc_table_corrupt: 0x21',
            'hl_ac_loss: 0xEF',
            'hl_unavailable_pel_entry: 0x20',
            'hl_incorrect_pel_state: 0x21',
            'hl_invalid_pel_state: 0x03',
            'hl_pel_entries_created: 0x16F7',
            'hl_led_sets: 0x88',
            'hl_sys_fan_removes: 0x09',
            'hl_sys_fan_events: 0x2003',
            'hl_mps_fan_events: 0x0230',
            'hl_fan_ctl_events: 0x0B',
            'hl_sensor_events: 0x11',
            'hl_1F02_info_logs: 0x03',
            'hl_i2c_bus1_events: 0x9876',
            'hl_i2c_bus2_events: 0x5689',
            'hl_i2c_bus3_events: 0x1010',
            'hl_i2c_bus4_events: 0x0101',
            'hl_i2c_bus1_recovered: 0x01',
            'hl_i2c_bus2_recovered: 0x02',
            'hl_i2c_bus4_recovered: 0x04',
            'hl_ss_sets: 0xF0',
        ]
        self.assertEqual(lines, expected_lines)

        # The remaining tests use a dummy header file
        self._create_header_file([
            'struct mex_hlog_field mex_hlog_fields[MEX_HLOG_FIELD_COUNT] =',
            '{',
            '  { 1, "hl_isolated_standby" },',
            '  { 2, "hl_power_ups" }',
            '};'
        ])

        # Data buffer has correct number of bytes
        data = memoryview(b'\x01\xDE\xAD')
        lines = parse_hlog_data(data, self.header_file_path)
        expected_lines = [
            'Hex Dump:',
            '',
            '00000000:  01DEAD                               |...             |',
            '',
            'Non-Zero Field Values:',
            '',
            'hl_isolated_standby: 0x01',
            'hl_power_ups: 0xDEAD',
        ]
        self.assertEqual(lines, expected_lines)

        # Data buffer has too few bytes
        data = memoryview(b'\x01\xDE')
        lines = parse_hlog_data(data, self.header_file_path)
        expected_lines = [
            'Hex Dump:',
            '',
            '00000000:  01DE                                 |..              |',
            '',
            'Non-Zero Field Values:',
            '',
            'hl_isolated_standby: 0x01',
        ]
        self.assertEqual(lines, expected_lines)

        # Data buffer has too many bytes
        data = memoryview(b'\x01\xDE\xAD\xBE')
        lines = parse_hlog_data(data, self.header_file_path)
        expected_lines = [
            'Hex Dump:',
            '',
            '00000000:  01DEADBE                             |....            |',
            '',
            'Non-Zero Field Values:',
            '',
            'hl_isolated_standby: 0x01',
            'hl_power_ups: 0xDEAD',
        ]
        self.assertEqual(lines, expected_lines)

        # Verify fields with value of 0 are not formatted
        data = memoryview(b'\x00\xDE\xAD')
        lines = parse_hlog_data(data, self.header_file_path)
        expected_lines = [
            'Hex Dump:',
            '',
            '00000000:  00DEAD                               |...             |',
            '',
            'Non-Zero Field Values:',
            '',
            'hl_power_ups: 0xDEAD',
        ]
        self.assertEqual(lines, expected_lines)
