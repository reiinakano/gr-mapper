#!/usr/bin/env python
# -*- coding: utf-8 -*-
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy
from gnuradio import gr
import prbs_base
import Levenshtein
import pmt

class prbs_sink_2_b(gr.sync_block):
    """
    docstring for block prbs_sink_2_b
    """
    def __init__(self, which_mode, reset_len, title):
        gr.sync_block.__init__(self,
            name="prbs_sink_2_b",
            in_sig=None,
            out_sig=None)
        self.base = prbs_base.prbs_base(which_mode, reset_len)
        self.gen = self.base.gen_n(reset_len)
        self.nbits = 0.0
        self.nerrs = 0.0
        self.seen = 0
        self.array_nbits = []
        self.array_ber = []
        self.title = title
        self.clear = 20
        self.messages_so_far = 0

        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.calculate_error)

    def calculate_error(self, msg):
        if self.clear > self.messages_so_far:
            self.messages_so_far += 1
            return
        if not pmt.is_u8vector(msg):
            print('wrong type of PMT')
            return
        vec = pmt.to_python(msg)
        self.nerrs += Levenshtein.distance(''.join(map(str, vec.tolist())), ''.join(map(str, self.gen.tolist())))
        self.nbits += len(self.gen)
        if self.nbits > 0:
            print "-NBits: %d \tNErrs: %d \tBER: %.4E"%(int(self.nbits), int(self.nerrs), self.nerrs/self.nbits)
            self.array_nbits.append(int(self.nbits))
            self.array_ber.append(self.nerrs/self.nbits)

    def stop(self):
        fig = Figure()
        FigureCanvas(fig)

        ax = fig.add_subplot(111)

        ax.plot(self.array_nbits, self.array_ber)
        if len(self.array_ber) != 0:
            ax.plot(self.array_nbits, numpy.full([len(self.array_ber)], self.array_ber[-1]),
                     linestyle=':', label='average BER = {}'.format(self.array_ber[-1]))
        ax.set_xlabel('Number of bits sent')
        ax.set_ylabel('BER')
        ax.set_title('BER vs. Number of bits sent ({})'.format(self.title))
        ax.legend()
        fig.savefig('ber_{}.png'.format(self.title))
        return True

    def get_ber(self):
        if self.nbits == 0:
            return 1.
        else:
            return self.nerrs/self.nbits
