import os
import tempfile
import unittest

from io_drawer.trace import (TraceString, TraceStringFile, TraceBufferHeader,
                             TraceEntry, TraceBuffer, _format_trace_entry,
                             parse_trace_data)
from pel.datastream import DataStream


class TestTraceBase(unittest.TestCase):
    """
    Base class for unit tests for the trace module.

    Contains shared setUp/tearDown code and utility methods.
    """

    def setUp(self):
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()
        self.string_file_path = tmp_file.name

    def tearDown(self):
        os.remove(self.string_file_path)

    def _assertEntry(self, entry: TraceEntry, tbh: int, tbl: int, length: int,
                     tag: int, hash_value: int, line: int, data: memoryview):
        self.assertEqual(entry.tbh, tbh)
        self.assertEqual(entry.tbl, tbl)
        self.assertEqual(entry.length, length)
        self.assertEqual(entry.tag, tag)
        self.assertEqual(entry.hash_value, hash_value)
        self.assertEqual(entry.line, line)
        self.assertEqual(entry.data, data)

    def _assertHeader(self, header: TraceBufferHeader, ver: int, hdr_len: int,
                      time_flg: int, endian_flg: int, comp: str, size: int,
                      times_wrap: int, next_free: int):
        self.assertEqual(header.ver, ver)
        self.assertEqual(header.hdr_len, hdr_len)
        self.assertEqual(header.time_flg, time_flg)
        self.assertEqual(header.endian_flg, endian_flg)
        self.assertEqual(header.comp, comp)
        self.assertEqual(header.size, size)
        self.assertEqual(header.times_wrap, times_wrap)
        self.assertEqual(header.next_free, next_free)

    def _assertTraceString(self, trace_string: TraceString, hash_value: int,
                           message_format: str, location: str):
        self.assertEqual(trace_string.hash_value, hash_value)
        self.assertEqual(trace_string.message_format, message_format)
        self.assertEqual(trace_string.location, location)

    def _create_string_file(self, lines: list,
                            add_newlines: bool = True):
        with open(self.string_file_path, 'w') as file:
            for line in lines:
                file.write(line)
                if add_newlines:
                    file.write('\n')


class TestTraceString(TestTraceBase):
    """
    Unit tests for the TraceString class.
    """

    def test__init__(self):
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%X: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self._assertTraceString(trace_string, 32403714,
                                'E> ADT7470: Dev 0x%X: Failure count = %d',
                                'adt7470_fan_ctl.cpp(324)')

    def test_get_message(self):
        # No parameters
        trace_string = TraceString(33902203,
                                   'I> BMP180: Calibration data',
                                   'bmp180_sensor.cpp(339)')
        args = ()
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'I> BMP180: Calibration data')

        # One parameter and use of %u
        trace_string = TraceString(92902023,
                                   'I> ADT7470: fail_count = %u',
                                   'adt7470_fan_ctl.cpp(929)')
        args = (18,)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'I> ADT7470: fail_count = 18')

        # Two parameters and use of %x and %d
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        args = (0xD3, 5)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'E> ADT7470: Dev 0xd3: Failure count = 5')

        # Three parameters and use of %c, %02X, and %02u
        trace_string = TraceString(45603949,
                                   'Dev %c: Read 0x%02X from tach %02u',
                                   'adt7470_fan_ctl.cpp(456)')
        args = (ord('C'), 0xb, 3)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'Dev C: Read 0x0B from tach 03')

        # Five parameters and use of %04X, %08X, %.2X, %.4X, %.8X
        trace_string = TraceString(276406914,
                                   'Data: 0x%04X %08X 0x%.2X %.4X 0x%.8X',
                                   'cmds_util.cpp(2764)')
        args = (0x2b, 0x1beef, 0xd, 0xc0ffe, 0xc03df)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'Data: 0x002B 0001BEEF 0x0D C0FFE 0x000C03DF')

        # Too few parameters for message format string
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        args = (0xD3)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'E> ADT7470: Dev 0x%x: Failure count = %d')

        # Too many parameters for message format string
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        args = (0xD3, 3, 5)
        message = trace_string.get_message(args)
        self.assertEqual(message,
                         'E> ADT7470: Dev 0x%x: Failure count = %d')

    def test_is_match(self):
        # Test where hash values match
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self.assertTrue(trace_string.is_match(32403714))

        # Test where hash values don't match
        trace_string = TraceString(32403714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self.assertFalse(trace_string.is_match(32403715))

    def test_is_partial_match(self):
        # Test where True
        # Note: 32423714 % 100000 = 23714
        trace_string = TraceString(32423714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self.assertTrue(trace_string.is_partial_match(171823714))

        # Test where False: hash values are exact match
        trace_string = TraceString(32423714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self.assertFalse(trace_string.is_partial_match(32423714))

        # Test where False: hash values are not a partial match
        # Note: 32423714 % 100000 = 23714
        trace_string = TraceString(32423714,
                                   'E> ADT7470: Dev 0x%x: Failure count = %d',
                                   'adt7470_fan_ctl.cpp(324)')
        self.assertFalse(trace_string.is_partial_match(32423715))


class TestTraceStringFile(TestTraceBase):
    """
    Unit tests for the TraceStringFile class.
    """

    def test__init__(self):
		# Test with real string file generated during firmware build
        file = TraceStringFile()
        self.assertTrue(os.path.exists(file.string_file_path))
        self.assertEqual(os.path.basename(file.string_file_path),
                         'mexStringFile')
        self.assertTrue(len(file.trace_strings) > 650)

        # Test with dummy string file: Standard format
        self._create_string_file([
            '#FSP_TRACE_v2|||Thu Sep 24 12:55:43 2020|||BUILD:Release',
            '103402736||I> FANS_MGR: mps_fan_spd_tbl = %u||fans_mgr.cpp(1034)',
            '48602109||I> BMP180: Sensor 0x%X: UP = %d||bmp180_sensor.cpp(486)'
        ])
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(file.string_file_path, self.string_file_path)
        self.assertEqual(len(file.trace_strings), 2)
        self._assertTraceString(file.trace_strings[0], 103402736,
                                'I> FANS_MGR: mps_fan_spd_tbl = %u',
                                'fans_mgr.cpp(1034)')
        self._assertTraceString(file.trace_strings[1], 48602109,
                                'I> BMP180: Sensor 0x%X: UP = %d',
                                'bmp180_sensor.cpp(486)')

        # Test with dummy string file: Extra white space: Last line has no
        # newline
        self._create_string_file([
            '  103402736  || I> FANS_MGR: mps_fan_spd_tbl = %u  || fans_mgr.cpp(1034)  \n',
            '  48602109  || I> BMP180: Sensor 0x%X: UP = %d  || bmp180_sensor.cpp(486)  '
        ], add_newlines=False)
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(file.string_file_path, self.string_file_path)
        self.assertEqual(len(file.trace_strings), 2)
        self._assertTraceString(file.trace_strings[0], 103402736,
                                'I> FANS_MGR: mps_fan_spd_tbl = %u',
                                'fans_mgr.cpp(1034)')
        self._assertTraceString(file.trace_strings[1], 48602109,
                                'I> BMP180: Sensor 0x%X: UP = %d',
                                'bmp180_sensor.cpp(486)')

        # Test with dummy string file: Invalid lines
        self._create_string_file([
            '#FSP_TRACE_v2|||Thu Sep 24 12:55:43 2020|||BUILD:Release',
            '103402736||I> FANS_MGR: mps_fan_spd_tbl = %u||fans_mgr.cpp(1034)',
            '# VPD-related trace strings:',
            '#100803149||VINI size %d too large on io bay %d||fpga.cpp(1008)',
            'abc||def',
            '  ',
            '48602109||I> BMP180: Sensor 0x%X: UP = %d||bmp180_sensor.cpp(486)'
            '',
        ])
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(file.string_file_path, self.string_file_path)
        self.assertEqual(len(file.trace_strings), 2)
        self._assertTraceString(file.trace_strings[0], 103402736,
                                'I> FANS_MGR: mps_fan_spd_tbl = %u',
                                'fans_mgr.cpp(1034)')
        self._assertTraceString(file.trace_strings[1], 48602109,
                                'I> BMP180: Sensor 0x%X: UP = %d',
                                'bmp180_sensor.cpp(486)')

        # Test where string file does not exist
        with self.assertRaises(Exception):
            file = TraceStringFile('/does_not_exist/dne/mexStringFile')

    def test_get_trace_string(self):
        # Create dummy string file and load it
        self._create_string_file([
            '103402736||I> FANS_MGR: mps_fan_spd_tbl = %u||fans_mgr.cpp(1034)',
            '48602109||I> BMP180: Sensor 0x%X: UP = %d||bmp180_sensor.cpp(486)'
        ])
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(len(file.trace_strings), 2)

        # Test where matching trace string is found: Exact match
        self.assertIsNotNone(file.get_trace_string(48602109))

        # Test where matching trace string is found: Partial match
        self.assertIsNotNone(file.get_trace_string(97802736))

        # Test where matching trace string is not found
        self.assertIsNone(file.get_trace_string(103402746))

    def test__add_trace_string(self):
        # Create empty string file and load it
        self._create_string_file([''])
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(len(file.trace_strings), 0)

        # Add entry where fields don't have extra white space
        file._add_trace_string(('103402736',
                                'I> FANS_MGR: mps_fan_spd_tbl = %u',
                                'fans_mgr.cpp(1034)'))
        self.assertEqual(len(file.trace_strings), 1)
        self._assertTraceString(file.trace_strings[0], 103402736,
                                'I> FANS_MGR: mps_fan_spd_tbl = %u',
                                'fans_mgr.cpp(1034)')

        # Add entry where fields have extra white space
        file._add_trace_string(('  48602109  ',
                                '  I> BMP180: Sensor 0x%X: UP = %d  ',
                                '  bmp180_sensor.cpp(486)  '))
        self.assertEqual(len(file.trace_strings), 2)
        self._assertTraceString(file.trace_strings[1], 48602109,
                                'I> BMP180: Sensor 0x%X: UP = %d',
                                'bmp180_sensor.cpp(486)')

        # Specify invalid number of fields (2).  Should return without adding a
        # new trace string.
        file._add_trace_string(('103402736',
                                'I> FANS_MGR: mps_fan_spd_tbl = %u'))
        self.assertEqual(len(file.trace_strings), 2)


class TestTraceBufferHeader(TestTraceBase):
    """
    Unit tests for the TraceBufferHeader class.
    """

    def test__init__(self):
        header = TraceBufferHeader()
        self._assertHeader(header,
                           None, None, None, None, None, None, None, None)

    def test_read(self):
        # Test where works: Verify strips blanks/nulls from component name
        data = memoryview(b'\x01'               # ver
                          b'\x20'               # hdr_len
                          b'\x01'               # time_flg
                          b'\x42'               # endian_flg 'B'
                          b'\x46\x41\x4e\x53'   # comp
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   # rsvd
                          b'\x00\x00\x00\x64'   # size
                          b'\x00\x00\x00\xFE'   # times_wrap
                          b'\x00\x00\x00\x32')  # next_free
        stream = DataStream(data, byte_order='big', is_signed=False)
        header = TraceBufferHeader()
        self.assertTrue(header.read(stream))
        self._assertHeader(header,
                           0x01, 0x20, 0x01, 0x42, 'FANS', 0x64, 0xFE, 0x32)

        # Test where fails: Not enough bytes
        data = memoryview(b'\x01'               # ver
                          b'\x20'               # hdr_len
                          b'\x01'               # time_flg
                          b'\x42'               # endian_flg 'B'
                          b'\x46\x41\x4e\x53'   # comp
                          b'\x20\x20\x20\x20'   #
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   # rsvd
                          b'\x00\x00\x00\x64'   # size
                          b'\x00\x00\x00\xFE'   # times_wrap
                          b'\x00\x00\x32')      # next_free (1 byte short)
        stream = DataStream(data, byte_order='big', is_signed=False)
        header = TraceBufferHeader()
        self.assertFalse(header.read(stream))

class TestTraceEntry(TestTraceBase):
    """
    Unit tests for the TraceEntry class.
    """

    def test__init__(self):
        entry = TraceEntry()
        self._assertEntry(entry, None, None, None, None, None, None, None)

    def test_get_args(self):
        # Binary trace entry: Verify returns 0 arguments
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDBIN
        entry.data = memoryview(b'\x01\x02\x03\x04'
                                b'\xde\xad\xbe\xef'
                                b'\xba\xdc\x0f\xfe')
        self.assertEqual(entry.get_args(), ())

        # Non-binary trace entry: 0 arguments: No data
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = None
        self.assertEqual(entry.get_args(), ())

        # Non-binary trace entry: 0 arguments: Zero length data
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = memoryview(b'')
        self.assertEqual(entry.get_args(), ())

        # Non-binary trace entry: 0 arguments: Less than 4 bytes of data
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = memoryview(b'\x01\x02\x03')
        self.assertEqual(entry.get_args(), ())

        # Non-binary trace entry: 1 argument
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = memoryview(b'\x01\x02\x03\x04')
        self.assertEqual(entry.get_args(), (0x01020304,))

        # Non-binary trace entry: 3 arguments: Extra data bytes at end
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = memoryview(b'\x01\x02\x03\x04'
                                b'\xde\xad\xbe\xef'
                                b'\xba\xdc\x0f\xfe'
                                b'\xff\xee\xdd')
        self.assertEqual(entry.get_args(),
                         (0x01020304, 0xDEADBEEF, 0xBADC0FFE))

        # Non-binary trace entry: 5 arguments: Extra data bytes at end
        entry = TraceEntry()
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        entry.data = memoryview(b'\x01\x02\x03\x04'
                                b'\xde\xad\xbe\xef'
                                b'\xba\xdc\x0f\xfe'
                                b'\x03\x76\x34\x00'
                                b'\xEF\xFE\x69\x36'
                                b'\xDA\xEF\x45\x38')
        self.assertEqual(entry.get_args(),
                         (0x01020304, 0xDEADBEEF, 0xBADC0FFE,
                          0x03763400, 0xEFFE6936))

    def test_is_binary_trace(self):
        entry = TraceEntry()

        # Test where True
        entry.tag = TraceEntry.TYPE_FIELDBIN
        self.assertTrue(entry.is_binary_trace())

        # Test where False
        entry.tag = TraceEntry.TYPE_FIELDTRACE
        self.assertFalse(entry.is_binary_trace())

    def test_read(self):
        # Test where works: No entry data
        data = memoryview(b'\x8A\xDF'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x00'           # length (0)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\x53'   # hash_value
                          b'\x00\x00\x00\xFE'   # line
                          b'\x00\x00\x00\x14')  # entry_size (20)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        self._assertEntry(entry, 0x8ADF, 0x0123, 0x0000, 0x4654, 0x46414E53,
                          0x000000FE,
                          memoryview(b''))

        # Test where works: Has entry data: Data is 4-byte aligned
        data = memoryview(b'\x8A\xDF'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x10'           # length (16)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE\xEF'   #
                          b'\xBA\xDC\x0F\xFE'   #
                          b'\x04\x03\x02\x01'   #
                          b'\x00\x00\x00\x24')  # entry_size (36)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        self._assertEntry(entry, 0x8ADF, 0x0123, 0x0010, 0x4654, 0x46414EFF,
                          0x00000232,
                          memoryview(b'\x01\x02\x03\x04'
                                     b'\xDE\xAD\xBE\xEF'
                                     b'\xBA\xDC\x0F\xFE'
                                     b'\x04\x03\x02\x01'))

        # Test where works: Has entry data: Data is not 4-byte aligned
        data = memoryview(b'\x8A\xAB'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x07'           # length (7)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               # padding for 4-byte alignment
                          b'\x00\x00\x00\x1C')  # entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        self._assertEntry(entry, 0x8AAB, 0x0123, 0x0007, 0x4644, 0x46414EFF,
                          0x00000232,
                          memoryview(b'\x01\x02\x03\x04'
                                     b'\xDE\xAD\xBE'))

        # Test where fails: Not enough bytes for fixed fields
        data = memoryview(b'\x8A\xDF'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x00'           # length (0)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\x53'   # hash_value
                          b'\x00\x00\xFE')      # line (1 byte short)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))

        # Test where fails: Entry data length is invalid
        data = memoryview(b'\x8A\xDF'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x04\x01'           # length (1025 - max is 1024)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\x00\x00\x00\x18')  # entry_size (24)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))

        # Test where fails: No entry data bytes
        data = memoryview(b'\x8A\xDF'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x01'           # length (1)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\x53'   # hash_value
                          b'\x00\x00\x00\xFE')  # line
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))

        # Test where fails: No alignment padding bytes
        data = memoryview(b'\x8A\xAB'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x07'           # length (7)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE')      #
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))

        # Test where fails: No entry size at end
        data = memoryview(b'\x8A\xAB'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x07'           # length (7)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE'       #
                          b'\x00')              # padding for 4-byte alignment
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))

        # Test where fails: Entry size at end is invalid
        data = memoryview(b'\x8A\xAB'           # tbh
                          b'\x01\x23'           # tbl
                          b'\x00\x07'           # length (7)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   # hash_value
                          b'\x00\x00\x02\x32'   # line
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               # padding for 4-byte alignment
                          b'\x00\x00\x00\x1B')  # entry_size (27; should be 28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertFalse(entry.read(stream))


class TestTraceBuffer(TestTraceBase):
    """
    Unit tests for the TraceBuffer class.
    """

    def test__init__(self):
        buffer = TraceBuffer()
        self.assertIsNone(buffer.header)
        self.assertEqual(len(buffer.entries), 0)

    def test_read(self):
        # Test where works: Header and 0 entries
        data = memoryview(                      # buffer header
                          b'\x02'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x49\x49\x43\x53'   #   comp
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x20'   #   size (32)
                          b'\x00\x00\x00\x00'   #   times_wrap
                          b'\x00\x00\x00\x20')  #   next_free
        stream = DataStream(data, byte_order='big', is_signed=False)
        buffer = TraceBuffer()
        self.assertTrue(buffer.read(stream))
        self._assertHeader(buffer.header,
                           0x02, 0x20, 0x01, 0x42, 'IICS', 0x20, 0x00, 0x20)
        self.assertEqual(len(buffer.entries), 0)

        # Test where works: Header and 1 entry
        data = memoryview(                      # buffer header
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x3C'   #   size (32 + 28 = 60)
                          b'\x00\x00\x00\xFE'   #   times_wrap
                          b'\x00\x00\x00\x3D'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh
                          b'\x01\x23'           #   tbl
                          b'\x00\x07'           #   length (7)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   #   hash_value
                          b'\x00\x00\x02\x32'   #   line
                          b'\x01\x02\x03\x04'   #   data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               #   padding for 4-byte alignment
                          b'\x00\x00\x00\x1C')  #   entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        buffer = TraceBuffer()
        self.assertTrue(buffer.read(stream))
        self._assertHeader(buffer.header,
                           0x01, 0x20, 0x01, 0x42, 'FANS', 0x3C, 0xFE, 0x3D)
        self.assertEqual(len(buffer.entries), 1)
        self._assertEntry(buffer.entries[0], 0x8AAB, 0x0123, 0x0007, 0x4644,
                          0x46414EFF, 0x00000232,
                          memoryview(b'\x01\x02\x03\x04'
                                     b'\xDE\xAD\xBE'))

        # Test where works: Header and 2 entries
        data = memoryview(                      # buffer header
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x50'   #   size (32 + 28 + 20 = 80)
                          b'\x00\x00\x00\xFE'   #   times_wrap
                          b'\x00\x00\x00\x50'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh
                          b'\x01\x23'           #   tbl
                          b'\x00\x07'           #   length (7)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   #   hash_value
                          b'\x00\x00\x02\x32'   #   line
                          b'\x01\x02\x03\x04'   #   data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               #   padding for 4-byte alignment
                          b'\x00\x00\x00\x1C'   #   entry_size (28)
                                                # entry 2
                          b'\x8A\xDF'           #   tbh
                          b'\x01\x24'           #   tbl
                          b'\x00\x00'           #   length (0)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\x53'   #   hash_value
                          b'\x00\x00\x00\xFE'   #   line
                          b'\x00\x00\x00\x14')  #   entry_size (20)
        stream = DataStream(data, byte_order='big', is_signed=False)
        buffer = TraceBuffer()
        self.assertTrue(buffer.read(stream))
        self._assertHeader(buffer.header,
                           0x01, 0x20, 0x01, 0x42, 'FANS', 0x50, 0xFE, 0x50)
        self.assertEqual(len(buffer.entries), 2)
        self._assertEntry(buffer.entries[0], 0x8AAB, 0x0123, 0x0007, 0x4644,
                          0x46414EFF, 0x00000232,
                          memoryview(b'\x01\x02\x03\x04'
                                     b'\xDE\xAD\xBE'))
        self._assertEntry(buffer.entries[1], 0x8ADF, 0x0124, 0x0000, 0x4654,
                          0x46414E53, 0x000000FE,
                          memoryview(b''))

        # Test where works: Header and 2 entries + partial 3rd entry
        data = memoryview(                      # buffer header
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x74'   #   size (32+28+20+36=116)
                          b'\x00\x00\x00\xFE'   #   times_wrap
                          b'\x00\x00\x00\x74'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh
                          b'\x01\x23'           #   tbl
                          b'\x00\x07'           #   length (7)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\x46\x41\x4e\xFF'   #   hash_value
                          b'\x00\x00\x02\x32'   #   line
                          b'\x01\x02\x03\x04'   #   data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               #   padding for 4-byte alignment
                          b'\x00\x00\x00\x1C'   #   entry_size (28)
                                                # entry 2
                          b'\x8A\xDF'           #   tbh
                          b'\x01\x24'           #   tbl
                          b'\x00\x00'           #   length (0)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e\x53'   #   hash_value
                          b'\x00\x00\x00\xFE'   #   line
                          b'\x00\x00\x00\x14'   #   entry_size (20)
                                                # entry 3 (missing 25 bytes)
                          b'\x9A\xDF'           #   tbh
                          b'\x01\x25'           #   tbl
                          b'\x00\x10'           #   length (16)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x46\x41\x4e')      #   hash_value (missing 1 byte)
        stream = DataStream(data, byte_order='big', is_signed=False)
        buffer = TraceBuffer()
        self.assertTrue(buffer.read(stream))
        self._assertHeader(buffer.header,
                           0x01, 0x20, 0x01, 0x42, 'FANS', 0x74, 0xFE, 0x74)
        self.assertEqual(len(buffer.entries), 2)
        self._assertEntry(buffer.entries[0], 0x8AAB, 0x0123, 0x0007, 0x4644,
                          0x46414EFF, 0x00000232,
                          memoryview(b'\x01\x02\x03\x04'
                                     b'\xDE\xAD\xBE'))
        self._assertEntry(buffer.entries[1], 0x8ADF, 0x0124, 0x0000, 0x4654,
                          0x46414E53, 0x000000FE,
                          memoryview(b''))

        # Test where fails: Unable to read header
        data = memoryview(                      # buffer header (truncated)
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x74'   #   size (32+28+20+36=116)
                          b'\x00\x00\x00\xFE'   #   times_wrap
                          b'\x00\x00\x00')      #   next_free (missing 1 byte)
        stream = DataStream(data, byte_order='big', is_signed=False)
        buffer = TraceBuffer()
        self.assertFalse(buffer.read(stream))


class TestTrace(TestTraceBase):
    """
    Unit tests for functions in the trace module.
    """

    def test__format_trace_entry(self):
        # Create dummy string file and load it
        self._create_string_file([
            '32413714||E> Dev 0x%x: Fail count = %d||adt7470_fan_ctl.cpp(324)',
            '33902203||I> BMP180: Calibration data||bmp180_sensor.cpp(339)'
        ])
        file = TraceStringFile(self.string_file_path)
        self.assertEqual(len(file.trace_strings), 2)

        # Test where trace string is found: Exact match
        data = memoryview(b'\x8A\xDF'           # tbh (9:52:31)
                          b'\x00\x86'           # tbl
                          b'\x00\x08'           # length (8)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x01\xEE\x98\x12'   # hash_value (32413714)
                          b'\x00\x00\x01\x44'   # line (324)
                          b'\x00\x00\xFA\x04'   # data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C')  # entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        lines = []
        _format_trace_entry(entry, file, lines)
        expected_lines = [
            ' 9:52:31 0086   324 E> Dev 0xfa04: Fail count = 48879'
        ]
        self.assertEqual(lines, expected_lines)

        # Test where trace string is found: Partial match
        data = memoryview(b'\x8A\xE1'           # tbh (9:52:33)
                          b'\x01\x32'           # tbl
                          b'\x00\x08'           # length (8)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x01\xF1\xA5\x52'   # hash_value (32613714)
                          b'\x00\x00\x01\x46'   # line (326)
                          b'\x00\x00\xFA\x04'   # data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C')  # entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        lines = []
        _format_trace_entry(entry, file, lines)
        expected_lines = [
            ' 9:52:33 0132   326 E> Dev 0xfa04: Fail count = 48879',
            '                    Warning: Partial match with trace string from adt7470_fan_ctl.cpp(324)',
            '                    00000000:  0000FA04 0000BEEF                    |........        |'
        ]
        self.assertEqual(lines, expected_lines)

        # Test where trace string is not found
        data = memoryview(b'\x8A\xE1'           # tbh (9:52:33)
                          b'\x01\x32'           # tbl
                          b'\x00\x08'           # length (8)
                          b'\x46\x54'           # tag (TYPE_FIELDTRACE)
                          b'\x01\xF1\xA5\x53'   # hash_value (32613715)
                          b'\x00\x00\x01\x46'   # line (326)
                          b'\x00\x00\xFA\x04'   # data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C')  # entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        lines = []
        _format_trace_entry(entry, file, lines)
        expected_lines = [
            ' 9:52:33 0132   326 No trace string found with hash value 32613715',
            '                    00000000:  0000FA04 0000BEEF                    |........        |'
        ]
        self.assertEqual(lines, expected_lines)

        # Test where trace entry is binary with entry data as hexdump
        data = memoryview(b'\x8A\xAB'           # tbh (9:51:39)
                          b'\x01\x23'           # tbl
                          b'\x00\x07'           # length (7)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x02\x05\x4E\x7B'   # hash_value (33902203)
                          b'\x00\x00\x01\x53'   # line (339)
                          b'\x01\x02\x03\x04'   # data
                          b'\xDE\xAD\xBE'       #
                          b'\x00'               # padding for 4-byte alignment
                          b'\x00\x00\x00\x1C')  # entry_size (28)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        lines = []
        _format_trace_entry(entry, file, lines)
        expected_lines = [
            ' 9:51:39 0123   339 I> BMP180: Calibration data',
            '                    00000000:  01020304 DEADBE                      |.......         |'
        ]
        self.assertEqual(lines, expected_lines)

        # Test where entry data cannot be output as hexdump: No data available
        data = memoryview(b'\x8A\xAB'           # tbh (9:51:39)
                          b'\x01\x23'           # tbl
                          b'\x00\x00'           # length (0)
                          b'\x46\x44'           # tag (TYPE_FIELDBIN)
                          b'\x02\x05\x4E\x7B'   # hash_value (33902203)
                          b'\x00\x00\x01\x53'   # line (339)
                          b'\x00\x00\x00\x14')  # entry_size (20)
        stream = DataStream(data, byte_order='big', is_signed=False)
        entry = TraceEntry()
        self.assertTrue(entry.read(stream))
        lines = []
        _format_trace_entry(entry, file, lines)
        expected_lines = [
            ' 9:51:39 0123   339 I> BMP180: Calibration data'
        ]
        self.assertEqual(lines, expected_lines)

    def test_parse_trace_data(self):
		# Test with real string file generated during firmware build
        data = memoryview(                      # buffer header
                          b'\x01'               #   ver
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
        lines = parse_trace_data(data)
        expected_lines = [
            'Component: FANS',
            'Version: 1',
            'Size: 60',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:51:39 0123   562 No trace string found with hash value 4294967295',
            '                    00000000:  01020304 DEADBE                      |.......         |'
        ]
        self.assertEqual(lines, expected_lines)

        # Create dummy string file
        self._create_string_file([
            '32413714||E> Dev 0x%x: Fail count = %d||adt7470_fan_ctl.cpp(324)',
            '33902203||I> BMP180: Calibration data||bmp180_sensor.cpp(339)'
        ])

        # Test with dummy string file: Parsing works
        data = memoryview(                      # buffer header
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x54'   #   size (32 + 24 + 28 = 84)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00\x54'   #   next_free
                                                # entry 1
                          b'\x8A\xAB'           #   tbh (9:51:39)
                          b'\x01\x23'           #   tbl
                          b'\x00\x04'           #   length (4)
                          b'\x46\x44'           #   tag (TYPE_FIELDBIN)
                          b'\x02\x05\x4e\x7b'   #   hash_value (33902203)
                          b'\x00\x00\x01\x53'   #   line (339)
                          b'\xDE\xAD\xBE\xEF'   #   data
                          b'\x00\x00\x00\x18'   #   entry_size (24)
                                                # entry 2
                          b'\x8A\xDF'           #   tbh (9:52:31)
                          b'\x01\x86'           #   tbl
                          b'\x00\x08'           #   length (8)
                          b'\x46\x54'           #   tag (TYPE_FIELDTRACE)
                          b'\x01\xEE\x98\x12'   #   hash_value (32413714)
                          b'\x00\x00\x01\x44'   #   line (324)
                          b'\x00\x00\xFA\x04'   #   data
                          b'\x00\x00\xBE\xEF'   #
                          b'\x00\x00\x00\x1C')  #   entry_size (28)
        lines = parse_trace_data(data, self.string_file_path)
        expected_lines = [
            'Component: FANS',
            'Version: 1',
            'Size: 84',
            'Times Wrapped: 254',
            '',
            'HH:MM:SS Seq  Line  Entry Data',
            '-------- ---- ----- ----------',
            ' 9:51:39 0123   339 I> BMP180: Calibration data',
            '                    00000000:  DEADBEEF                             |....            |',
            ' 9:52:31 0186   324 E> Dev 0xfa04: Fail count = 48879'
        ]
        self.assertEqual(lines, expected_lines)

        # Test with dummy string file: Parsing fails
        data = memoryview(                      # buffer header (truncated)
                          b'\x01'               #   ver
                          b'\x20'               #   hdr_len (32)
                          b'\x01'               #   time_flg
                          b'\x42'               #   endian_flg
                          b'\x46\x41\x4e\x53'   #   comp (FANS)
                          b'\x20\x20\x20\x20'   #
                          b'\x00\x00\x00\x00'   #
                          b'\x00\x00\x00\x00'   #   rsvd
                          b'\x00\x00\x00\x74'   #   size (32+28+20+36=116)
                          b'\x00\x00\x00\xFE'   #   times_wrap (254)
                          b'\x00\x00\x00')      #   next_free (missing 1 byte)
        lines = parse_trace_data(data, self.string_file_path)
        expected_lines = [
            'Unable to parse trace data.',
            '00000000:  01200142 46414E53 20202020 00000000  |. .BFANS    ....|',
            '00000010:  00000000 00000074 000000FE 000000    |.......t....... |'
        ]
        self.assertEqual(lines, expected_lines)
