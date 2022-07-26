import unittest

from pel.hexdump import hexdump, parse


class TestHexDump(unittest.TestCase):

    def test_hexdump(self):
        # Test with default parameter values: One full data line
        data = memoryview(b'\xde\xad\xbe\xef'
                          b'\xba\xdc\x0f\xfe'
                          b'\x42\x41\x44\x43'
                          b'\x30\x46\x46\x45')
        lines = hexdump(data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
            '00000000:  DEADBEEF BADC0FFE 42414443 30464645  |........BADC0FFE|')

        # Test where bytes_per_line and bytes_per_chunk specified
        data = memoryview(b'\xde\xad\xbe\xef'
                          b'\xba\xdc\x0f\xfe'
                          b'\x42\x41\x44\x43'
                          b'\x30\x46\x46\x45')
        lines = hexdump(data, bytes_per_line=8, bytes_per_chunk=2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '00000000:  DEAD BEEF BADC 0FFE  |........|')
        self.assertEqual(lines[1], '00000008:  4241 4443 3046 4645  |BADC0FFE|')

        # Test with less than one full line of data
        data = memoryview(b'\xde\xad\xbe\xef'
                          b'\xba\xdc\x0f\xfe'
                          b'\x42\x41')
        lines = hexdump(data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0],
            '00000000:  DEADBEEF BADC0FFE 4241               |........BA      |')

        # Test with one full and one partial line of data
        data = memoryview(b'\xde\xad\xbe\xef'
                          b'\xba\xdc\x0f\xfe'
                          b'\x42')
        lines = hexdump(data, bytes_per_line=8, bytes_per_chunk=2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], '00000000:  DEAD BEEF BADC 0FFE  |........|')
        self.assertEqual(lines[1], '00000008:  42                   |B       |')

        # Test where no data bytes specified
        data = memoryview(b'')
        lines = hexdump(data)
        self.assertEqual(len(lines), 0)

        # Test where bytes_per_line is invalid
        data = memoryview(b'\xde\xad\xbe\xef')
        with self.assertRaises(Exception):
            lines = hexdump(data, bytes_per_line=257, bytes_per_chunk=2)

        # Test where bytes_per_chunk is invalid
        data = memoryview(b'\xde\xad\xbe\xef')
        with self.assertRaises(Exception):
            lines = hexdump(data, bytes_per_line=8, bytes_per_chunk=257)

    def test_parse(self):
        # Test with default line format: Less than one full line of data
        lines = [
            '00000000:  DEADBEEF BADC0FFE 4241               |........BA      |'
        ]
        expected_data = memoryview(b'\xde\xad\xbe\xef'
                                   b'\xba\xdc\x0f\xfe'
                                   b'\x42\x41')
        data = parse(lines)
        self.assertEqual(data, expected_data)

        # Test with default line format: One full data line
        lines = [
            '00000000:  DEADBEEF BADC0FFE 42414443 30464645  |........BADC0FFE|'
        ]
        expected_data = memoryview(b'\xde\xad\xbe\xef'
                                   b'\xba\xdc\x0f\xfe'
                                   b'\x42\x41\x44\x43'
                                   b'\x30\x46\x46\x45')
        data = parse(lines)
        self.assertEqual(data, expected_data)

        # Test with default line format: One full and one partial line
        lines = [
            '00000000:  01200142 46414E53 20202020 A9876543  |. .BFANS    ..eC|',
            '00000010:  00010203 FF000074 DD                 |.......t.       |'
        ]
        expected_data = memoryview(b'\x01\x20\x01\x42'
                                   b'\x46\x41\x4e\x53'
                                   b'\x20\x20\x20\x20'
                                   b'\xA9\x87\x65\x43'
                                   b'\x00\x01\x02\x03'
                                   b'\xFF\x00\x00\x74'
                                   b'\xDD')
        data = parse(lines)
        self.assertEqual(data, expected_data)

        # Test with custom line format: No address, one byte chunks, no ASCII
        # delimeters
        line_format = \
            'DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD DD CCCCCCCCCCCCCCCC'
        lines = [
            '01 20 01 42 46 41 4E 53 20 20 20 20 A9 87 65 43 . .BFANS    ..eC',
            '00 01 02 03 FF 00 00 74 DD                      .......t.       '
        ]
        expected_data = memoryview(b'\x01\x20\x01\x42'
                                   b'\x46\x41\x4e\x53'
                                   b'\x20\x20\x20\x20'
                                   b'\xA9\x87\x65\x43'
                                   b'\x00\x01\x02\x03'
                                   b'\xFF\x00\x00\x74'
                                   b'\xDD')
        data = parse(lines, line_format)
        self.assertEqual(data, expected_data)

        # Test with custom line format: 4 byte address, different ASCII
        # delimeters
        line_format = \
            'AAAA:  DDDDDDDD DDDDDDDD DDDDDDDD DDDDDDDD  <CCCCCCCCCCCCCCCC>'
        lines = [
            '0000:  01200142 46414E53 20202020 A9876543  <. .BFANS    ..eC>',
            '0010:  00010203 FF000074 DD                 <.......t.       >'
        ]
        expected_data = memoryview(b'\x01\x20\x01\x42'
                                   b'\x46\x41\x4e\x53'
                                   b'\x20\x20\x20\x20'
                                   b'\xA9\x87\x65\x43'
                                   b'\x00\x01\x02\x03'
                                   b'\xFF\x00\x00\x74'
                                   b'\xDD')
        data = parse(lines, line_format)
        self.assertEqual(data, expected_data)

        # Test with custom line format: Different address delimeter, different
        # chunk size, different line size, no ASCII, newlines
        line_format = '[AAAA] DDDD DDDD DDDD DDDD'
        lines = [
            '[0000] 0120 0142 4641 4E53\n',
            '[0008] 2020 2020 A987 6543\n',
            '[0010] 0001 0203 FF00 0074\n',
            '[0018] DD\n'
        ]
        expected_data = memoryview(b'\x01\x20\x01\x42'
                                   b'\x46\x41\x4e\x53'
                                   b'\x20\x20\x20\x20'
                                   b'\xA9\x87\x65\x43'
                                   b'\x00\x01\x02\x03'
                                   b'\xFF\x00\x00\x74'
                                   b'\xDD')
        data = parse(lines, line_format)
        self.assertEqual(data, expected_data)

        # Test where some lines are invalid
        line_format = '[AAAA] DDDD DDDD DDDD DDDD'
        lines = [
            '# Hex dump from address 0x0000',
            '[0000] 0120 0142 4641 4E53\n',
            '[0008] 2020 2020 A987 6543\n',
            '[] ..',
            '[0010] 0001 0203 FF00 0074\n',
            '[0018] AX\n',
            '[0018] DD\n',
            'End of data'
        ]
        expected_data = memoryview(b'\x01\x20\x01\x42'
                                   b'\x46\x41\x4e\x53'
                                   b'\x20\x20\x20\x20'
                                   b'\xA9\x87\x65\x43'
                                   b'\x00\x01\x02\x03'
                                   b'\xFF\x00\x00\x74'
                                   b'\xDD')
        data = parse(lines, line_format)
        self.assertEqual(data, expected_data)

        # Test where lines array is empty
        line_format = '[AAAA] DDDD DDDD DDDD DDDD'
        lines = []
        expected_data = memoryview(b'')
        data = parse(lines, line_format)
        self.assertEqual(data, expected_data)
