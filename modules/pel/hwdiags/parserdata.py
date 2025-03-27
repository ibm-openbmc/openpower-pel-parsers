from collections import OrderedDict
import glob
import json
import os
import re

import pel.hwdiags.data

class ParserData:
    """
    The human readable output for registers, addresses, signature descriptions,
    etc. are stored in JSON data files. This class is simply a wrapper to access
    the data files and provide functions for data needed by openpower-hw-diags.
    """

    def __init__(self):
        """
        Reads and stores all the JSON data files from `pel.hwdiags.data`.
        """
        self._data = {}

        data_path = os.path.dirname(pel.hwdiags.data.__file__)

        for data_file in glob.glob(os.path.join(data_path, '*.json')):
            with open(data_file, 'r') as fp:
                data = json.load(fp)

            self._data[data["model_ec"]["id"]] = data


    _re_1byte_hex = re.compile('[0-9A-Fa-f]{2}')
    _re_2byte_hex = re.compile('[0-9A-Fa-f]{4}')
    _re_3byte_hex = re.compile('[0-9A-Fa-f]{6}')
    _re_4byte_hex = re.compile('[0-9A-Fa-f]{8}')

    def _check_hex(self, data: str, num_bytes: int) -> None:
        re_map = {
            1: self._re_1byte_hex,
            2: self._re_2byte_hex,
            3: self._re_3byte_hex,
            4: self._re_4byte_hex,
        }

        assert re_map[num_bytes].fullmatch(data), "invalid hex data"

    def _check_int(self, data: int, num_bytes: int) -> None:
        lb = 0
        ub = (1 << (8 * num_bytes)) - 1
        assert lb <= data <= ub, "integer must in the range %d-%d" % (lb, ub)


    def query_model_ec(self, model_ec: str) -> bool:
        """
        True if data exists for this model_ec. False, otherwise.
        """
        # All keys are strings. Hex keys are lowercase.
        model_ec = model_ec.lower()

        # Check parameters
        self._check_hex(model_ec, 4)

        return True if model_ec in self._data else False


    def get_attn_desc(self, model_ec: str, attn_type: int) -> str:
        """
        Returns a human readable string description of the given attention type
        info.
        """
        # Check parameters.
        self._check_hex(model_ec, 4)

        # All keys are strings. Hex keys are lowercase.
        model_ec  = model_ec.lower()
        attn_type = str(attn_type)

        # Extract the attention type.
        try:
            out = self._data[model_ec]["attn_types"][attn_type]
        except KeyError:
            out = attn_type

        return out


    def get_chip_desc(self, model_ec: str, node_pos: int, chip_pos: int) -> str:
        """
        Returns a human readable string description of the given chip info.
        """
        # Check parameters.
        self._check_hex(model_ec, 4)
        self._check_int(node_pos, 1)
        self._check_int(chip_pos, 2)

        # All keys are strings. Hex keys are lowercase.
        model_ec = model_ec.lower()

        # Extract chip type.
        try:
            chip_type = self._data[model_ec]["model_ec"]["type"]
        except KeyError:
            chip_type = "unknown"

        # Using the model_ec value instead of the chip description to avoid
        # exposing internal code words.
        chip_desc = model_ec.upper()

        return "node %d %s %d (0x%s)" % (
            node_pos,
            chip_type,
            chip_pos,
            chip_desc,
        )

    def get_sig_desc(self, model_ec: str, sig_id: str, sig_inst: int,
                     sig_bit: int) -> str:
        """
        Returns a human readable string description of the given signature info.
        """
        # Check parameters.
        self._check_hex(model_ec, 4)
        self._check_hex(sig_id,   2)
        self._check_int(sig_inst, 1)
        self._check_int(sig_bit,  1)

        # All keys are strings. Hex keys are lowercase.
        model_ec = model_ec.lower()
        sig_id  = sig_id.lower()
        sig_bit = str(sig_bit)

        # Extract signature name.
        try:
            sig_name = self._data[model_ec]["signatures"][sig_id][0]
        except KeyError:
            sig_name = "id:" + sig_id.upper()

        # Extract signature description.
        try:
            sig_desc = self._data[model_ec]["signatures"][sig_id][1][sig_bit]
        except KeyError:
            sig_desc = ""

        return "%s(%d)[%s] %s" % (sig_name, sig_inst, sig_bit, sig_desc)


    def get_signature(self, word_a: str, word_b: str,
                      word_c: str) -> OrderedDict:
        """
        A complete signature is contained within 12 bytes of data. Signatures
        will be parsed with the SRC parser (Hex Words 6-8) and user data
        parsers. So the data will be passed to this function in three word
        chunks in order of word a, word b, and word c. This function will then
        parse the information and return data for the chip description,
        signature details, and attention type.
        """
        self._check_hex(word_a, 4)
        self._check_hex(word_b, 4)
        self._check_hex(word_c, 4)

        model_ec  = word_a

        chip_pos  = int(word_b[0:4], base=16)
        node_pos  = int(word_b[4:6], base=16)
        attn_type = int(word_b[6:8], base=16)

        sig_id    =     word_c[0:4]
        sig_inst  = int(word_c[4:6], base=16)
        sig_bit   = int(word_c[6:8], base=16)

        out = OrderedDict()

        out["Chip Desc"] = self.get_chip_desc(model_ec, node_pos, chip_pos)

        out["Signature"] = self.get_sig_desc(model_ec, sig_id, sig_inst,
                                             sig_bit)

        out["Attn Type"] = self.get_attn_desc(model_ec, attn_type)

        return out


    def get_reg_data(self, model_ec: str, reg_id: str,
                     reg_inst: int) -> (str, str):
        """
        Returns the register name and address for the given register data.
        """
        # Check parameters.
        self._check_hex(model_ec, 4)
        self._check_hex(reg_id,   3)
        self._check_int(reg_inst, 1)

        # All keys are strings. Hex keys are lowercase.
        model_ec = model_ec.lower()
        reg_id   = reg_id.lower()
        reg_inst = str(reg_inst)

        # Extract register name.
        try:
            reg_name = self._data[model_ec]["registers"][reg_id][0]
        except KeyError:
            reg_name = "id:%s inst:%s" % (reg_id.upper(), reg_inst)

        # Extract register address.
        try:
            reg_addr = self._data[model_ec]["registers"][reg_id][1][reg_inst]
            reg_addr = int(reg_addr, base=16)
        except KeyError:
            reg_addr = 0

        return reg_name, "0x%08X" % reg_addr


