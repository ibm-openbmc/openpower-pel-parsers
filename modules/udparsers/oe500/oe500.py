import json
from collections import OrderedDict

from pel.hexdump import hexdump
from pel.datastream import DataStream
from pel.hwdiags.parserdata import ParserData


def _parse_signature_list(version: int, data: memoryview) -> str:
    """
    Parser for the signature list.
    """

    stream = DataStream(data, byte_order='big', is_signed=False)
    parser = ParserData()
    out    = OrderedDict()

    # The first 4 bytes contains the number of signatures in this data.
    sig_count = stream.get_int(4)

    # Iterate each signature.
    out["Signature List"] = []
    for i in range(0, sig_count):
        # Extact the three words of the signature.
        a = stream.get_mem(4).hex()
        b = stream.get_mem(4).hex()
        c = stream.get_mem(4).hex()

        # Get the signature data.
        out["Signature List"].append(parser.get_signature(a, b, c))

    # Convert to JSON format and dump to a string.
    return json.dumps(out)


def _parse_register_dump(version: int, data: memoryview) -> str:
    """
    Parser for the register dump.
    """

    stream = DataStream(data, byte_order='big', is_signed=False)
    parser = ParserData()
    out    = OrderedDict()

    # The register dump will just be a list of strings where each line is either
    # a chip description or the register data associated with the chip.
    dump = []

    reg_name_len   = 25
    data_chunk_len = 4
    chip_desc_len  = 31 + reg_name_len + data_chunk_len

    # The first 4 bytes contains the number of chips containing data.
    chip_count = stream.get_int(4)

    for c in range(0, chip_count):
        # Each chip will have the following information:
        #   4 byte chip model/EC
        #   2 byte chip position
        #   1 byte node position
        #   4 byte number of registers
        model_ec = stream.get_mem(4).hex()
        chip_pos = stream.get_int(2)
        node_pos = stream.get_int(1)
        num_regs = stream.get_int(4)

        # Get the chip description. To follow legacy output, pad the right side
        # with '*' characters.
        chip_desc = parser.get_chip_desc(model_ec, node_pos, chip_pos) + ' '
        dump.append(chip_desc.ljust(chip_desc_len, '*'))

        for r in range(0, num_regs):
            # Each register will have the following information:
            #   3 byte register ID
            #   1 byte register instance
            #   1 byte data size
            #   * byte data buffer (* depends on value of data size)
            reg_id    = stream.get_mem(3).hex()
            reg_inst  = stream.get_int(1)
            data_size = stream.get_int(1)
            data_buf  = stream.get_mem(data_size).hex()

            # Get the register data from the parser.
            reg_name, reg_addr = parser.get_reg_data(model_ec, reg_id, reg_inst)

            # Crop longer names and pad with spaces on the right.
            reg_name = reg_name[0 : reg_name_len]
            reg_name = reg_name.ljust(reg_name_len)

            # Split the data buffer up into chunks for readability.
            chunks = []
            for i in range(0, len(data_buf), data_chunk_len):
                chunks.append(data_buf[i : i + data_chunk_len])

            data_buf = ' '.join(chunks)

            # Add the register info.
            dump.append("  %s (%s) %s" % (reg_name, reg_addr, data_buf.upper()))

    out["Register Dump"] = dump

    # Convert to JSON format and dump to a string.
    return json.dumps(out)


def _parse_callout_ffdc(version: int, data: memoryview) -> str:
    """
    Parser for callout list FFDC.
    """

    # The data in this section is simply a string representation of JSON data.
    # When the JSON data is written to the section, it will include a null
    # character at the end because it is a string. Before converting the
    # memoryview of the data to a string the null character must be removed.
    # Otherwise, the json.loads() function will throw an exception due to the
    # unexpected character at the end.

    # Convert the data into a string.
    s = data.tobytes().rstrip(b'\0').decode('utf8')

    # It seems odd to convert the JSON string to python structures just to turn
    # around convert it back to a string. However, we still need to do this so
    # that the output looks nice. Otherwise, the data will all be in one line.

    # Convert to JSON format and dump to a string.
    return json.dumps( { "Callout List FFDC": json.loads(s) } )


def _parse_hb_scratch_regs(version: int, data: memoryview) -> str:
    """
    Parser for the Hostboot scratch registers.
    """

    stream = DataStream(data, byte_order='big', is_signed=False)

    # Extract the hex string values of the data.
    cfamAddr  = '0x' + stream.get_mem(4).hex()
    cfamValue = '0x' + stream.get_mem(4).hex()
    scomAddr  = '0x' + stream.get_mem(8).hex()
    scomValue = '0x' + stream.get_mem(8).hex()

    # Just make a simple list for now.
    out = {
        cfamAddr: cfamValue,
        scomAddr: scomValue
    }

    # Convert to JSON format and dump to a string.
    return json.dumps({"Hostboot Scratch Registers": out})

def _parse_scratch_reg_sig(version: int, data: memoryview) -> str:
    """
    Parser for the error signature stored in the Hostboot scratch registers.
    """

    stream = DataStream(data, byte_order='big', is_signed=False)

    # Extract the hex string values of the data.
    chipId = '0x' + stream.get_mem(4).hex()
    sigId = '0x' + stream.get_mem(4).hex()

    out = {
        'Chip ID': chipId,
        'Signature ID': sigId
    }

    # Convert to JSON format and dump to a string.
    return json.dumps({"Scratch Register Error Signature": out})

def _parse_default(version: int, data: memoryview) -> str:
    """
    Default parser for user data sections that are not currently supported.
    """

    return json.dumps(None)


def parseUDToJson(subtype: int, version: int, data: memoryview) -> str:
    """
    Default function required by all component PEL user data parsers.
    """

    # Determine which parser to use.
    parsers = {
        1: _parse_signature_list,
        2: _parse_register_dump,
        3: _parse_callout_ffdc,
        4: _parse_hb_scratch_regs,
        5: _parse_scratch_reg_sig,
    }
    subtype_func = parsers.get(subtype, _parse_default)

    # Return the parsed output of this data.
    return subtype_func(version, data)


