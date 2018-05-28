#!/usr/bin/env python
import matplotlib
matplotlib.use('agg')

import numpy
from gnuradio import gr
import prbs_base
import matplotlib.pyplot as plt
import Levenshtein

class prbs_sink_b(gr.sync_block):
    def __init__(self, which_mode="PRBS31", reset_len=100000, title='', skip=100000):
        gr.sync_block.__init__(self,
            name="prbs_sink_b",
            in_sig=[numpy.int8],
            out_sig=[])
        self.base = prbs_base.prbs_base(which_mode, reset_len)
        self.nbits = 0.0
        self.nerrs = 0.0
        self.skip = skip
        self.title = title
        self.array_nbits = []
        self.array_ber = []

    def work(self, input_items, output_items):
        inb = input_items[0]
        gen = self.base.gen_n(len(inb))
        if self.nitems_read(0) > self.skip:
            # only count bit errors after first skip bits
            self.nerrs += Levenshtein.distance(''.join(map(str, inb.tolist())), ''.join(map(str, gen.tolist())))
            self.nbits += len(inb)
        if self.nbits > 0:
            print "NBits: %d \tNErrs: %d \tBER: %.4E"%(int(self.nbits), int(self.nerrs), self.nerrs/self.nbits)
            self.array_nbits.append(int(self.nbits))
            self.array_ber.append(self.nerrs/self.nbits)
        return len(inb)

    def stop(self):
        plt.plot(self.array_nbits, self.array_ber)
        if len(self.array_ber) != 0:
            plt.plot(self.array_nbits, numpy.full([len(self.array_ber)], self.array_ber[-1]),
                     linestyle=':', label='average BER = {}'.format(self.array_ber[-1]))
        plt.xlabel('Number of bits sent')
        plt.ylabel('BER')
        plt.title('BER vs. Number of bits sent ({})'.format(self.title))
        plt.legend()
        plt.savefig('ber_{}.png'.format(self.title))
        return True
