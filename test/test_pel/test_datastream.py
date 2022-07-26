import unittest

from pel.datastream import DataStream


class TestDataStream(unittest.TestCase):

    def setUp(self):
        self.data = memoryview(bytes.fromhex('f0f1f2f3f4f5f6f7'))

    def test_endian(self):
        s = DataStream(self.data, byte_order='little', is_signed=False)

        # little endian
        self.assertEqual(0xf3f2f1f0, s.get_int(4))

        # big endian
        self.assertEqual(0xf4f5f6f7, s.get_int(4, byte_order='big'))

        # check end of range
        self.assertFalse(s.check_range(1))

    def test_signed(self):
        s = DataStream(self.data, byte_order='big', is_signed=False)

        # unsigned
        self.assertEqual(0xf0f1f2f3, s.get_int(4))

        # signed
        self.assertEqual(-185207049, s.get_int(4, is_signed=True))

        # attempt to access out of bounds
        with self.assertRaises(AssertionError):
            s.get_mem(1)
