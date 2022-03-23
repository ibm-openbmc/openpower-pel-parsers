class DataStream:
    """
    A simple object to manage extracting data from a memoryview. Will perform
    range checks to ensure data can be extracted and will automatically
    increment the current index with data is extracted.

    Special note on extracting integers: To ensure the data in the memoryview
    is extracted in the proper format, users can specify the byte order ('big'
    or 'little') and if the data is signed (True or False). This can be done in
    the constructor or the `get_int` function. If specified, the latter takes
    precedence over the former.
    """

    def __init__(self, data: memoryview, byte_order: str = None,
                 is_signed: bool = None):
        self.data = data
        self.size = len(data)
        self.index = 0
        self.byte_order = byte_order
        self.is_signed = is_signed

    def check_range(self, num_bytes: int) -> bool:
        """
        Returns True if the given number of bytes can be extracted from the
        data. False otherwise.
        """
        assert 0 < num_bytes, "must provide a positive, non-zero integer"
        return True if self.index + num_bytes <= self.size else False

    def inc_index(self, num_bytes: int) -> None:
        """
        Simply increments the current index. Useful when skipping over
        unused/reserved fields in the data stream.
        """
        assert self.check_range(num_bytes), "range check failure"
        self.index += num_bytes

    def get_mem(self, num_bytes: int) -> memoryview:
        """
        Returns a memoryview for the given number of bytes and increments the
        current index.
        """
        assert self.check_range(num_bytes), "range check failure"
        o_mv = self.data[self.index: self.index + num_bytes]
        self.inc_index(num_bytes)
        return o_mv

    def get_int(self, num_bytes: int, byte_order: str = None,
                is_signed: bool = None) -> int:
        """
        Returns an integer for the given number of bytes and increments the
        current index.
        """

        # If not specified, use the objects definition of byte_order and
        # is_signed from the constructor.
        if None == byte_order:
            byte_order = self.byte_order

        if None == is_signed:
            is_signed = self.is_signed

        # Ensure byte_order and is_signed have been specified somewhere.
        assert None != byte_order, "byte_order not defined"
        assert None != is_signed,  "is_signed not defined"

        return int.from_bytes(self.get_mem(num_bytes),
                              byteorder=byte_order, signed=is_signed)
