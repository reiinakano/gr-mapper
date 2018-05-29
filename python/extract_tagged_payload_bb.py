#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string,
# Python comments, other future statements, or blank lines before the __future__ line.
try:
    import __builtin__
except ImportError:
    # Python 3
    import builtins as __builtin__

import numpy as np
from gnuradio import gr
from enum import Enum
import pmt


class Mode(Enum):
    SEARCHING_SYNC = 1
    FOUND_SYNC = 2


verbose = False


def print(*args, **kwargs):
    global verbose
    if not verbose:
        return
    return __builtin__.print(*args, **kwargs)


class extract_tagged_payload_bb(gr.basic_block):
    """
    docstring for block extract_tagged_payload_bb
    """
    def __init__(self, payload_width, synch_length):
        gr.basic_block.__init__(self,
                                name="extract_tagged_payload_bb",
                                in_sig=[np.uint8],
                                out_sig=[np.uint8])
        self.payload_width = payload_width
        self.synch_length = synch_length
        self.mode = Mode.SEARCHING_SYNC

        self.set_output_multiple(int(self.payload_width*1.05))

        self.message_port_register_out(pmt.intern('packet_out'))

    def forecast(self, noutput_items, ninput_items_required):
        #setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = ((noutput_items // self.payload_width) + 1) * (self.payload_width + self.synch_length)

    def general_work(self, input_items, output_items):
        print(len(self.get_tags_in_window(0, 0, len(input_items[0]))))

        for tag in self.get_tags_in_window(0, 0, len(input_items[0])):
            print(tag.offset)
            if self.mode == Mode.SEARCHING_SYNC:
                print('Found starting preamble')
                self.mode = Mode.FOUND_SYNC
                self.last_preamble = tag.offset
                consumed_so_far = tag.offset - self.nitems_read(0)
                self.consume(0, consumed_so_far)
                print('consumed {}'.format(consumed_so_far))
                return 0
            elif self.mode == Mode.FOUND_SYNC:
                if tag.offset == self.last_preamble: # same preamble
                    print('same as last preamble. continuing')
                    continue
                width = tag.offset - self.last_preamble - self.synch_length
                consumed_so_far = tag.offset - self.nitems_read(0)
                self.last_preamble = tag.offset
                if width < int(self.payload_width*1.05): # valid payload
                    print('found valid payload with length {}'.format(width))
                    output_items[0][:width] = input_items[0][:width]
                    self.message_port_pub(pmt.intern('packet_out'),
                                          pmt.to_pmt(input_items[0][:width]))
                    self.consume(0, consumed_so_far)
                    print('consumed {}'.format(consumed_so_far))
                    return self.payload_width
                else:
                    print('invalid payload with length {}.'
                          ' musta skipped a few'.format(width))
                    self.consume(0, consumed_so_far)
                    print('consumed {}'.format(consumed_so_far))
                    return 0

        print('no new preambles found here')
        if self.mode == Mode.SEARCHING_SYNC:
            self.consume(0, len(input_items[0]))
            print('consumed {}'.format(len(input_items[0])))
            return 0
        elif self.mode == Mode.FOUND_SYNC:
            width = len(input_items[0])
            if width < int(self.payload_width*1.05) - self.synch_length: # Could still be valid
                print('could still be valid, wait for the next work()')
                self.consume(0, 0)
                print('consumed 0')
                return 0
            else:
                print('missed next preamble. reset')
                self.mode = Mode.SEARCHING_SYNC
                self.consume(0, len(input_items[0]))
                print('consumed {}'.format(len(input_items[0])))
                return 0
