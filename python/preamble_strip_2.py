#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gnuradio import gr
from gnuradio import digital
from extract_tagged_payload_bb import extract_tagged_payload_bb

class preamble_strip_2(gr.hier_block2):
    """
    Strips the given preamble from the bytestream and passes on the payload.
    This block makes sure that the payload begins and ends with the same preamble,
    and discards any payload that does not satisfy this condition. The start of a
    payload is tagged so this block can support payloads with missing/extra bits.
    """
    def __init__(self, payload_width, synch):
        gr.hier_block2.__init__(self,
            "preamble_strip_2",
            gr.io_signature(1, 1, gr.sizeof_char),  # Input signature
            gr.io_signature(1, 1, gr.sizeof_char)) # Output signature

        self.payload_width = payload_width
        self.synch = synch

        self.message_port_register_hier_out('packet_out')

        synch_string = ''.join(map(str, synch))

        self.correlate = digital.correlate_access_code_tag_bb(synch_string, 0, "payload")
        self.extract = extract_tagged_payload_bb(payload_width, len(synch))

        # Define blocks and connect them
        self.connect((self, 0), self.correlate)
        self.connect(self.correlate, self.extract)
        self.connect(self.extract, (self, 0))

        self.msg_connect(self.extract, 'packet_out', self, 'packet_out')
