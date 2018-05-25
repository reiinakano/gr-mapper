/* -*- c++ -*- */
/* 
 * Copyright 2015 Free Software Foundation, Inc
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "preamble_strip_impl.h"

namespace gr {
  namespace mapper {

    preamble_strip::sptr
    preamble_strip::make(int user_len, const std::vector<uint8_t> &preamble)
    {
      return gnuradio::get_initial_sptr
        (new preamble_strip_impl(user_len, preamble));
    }

    /*
     * The private constructor
     */
    preamble_strip_impl::preamble_strip_impl(int user_len, const std::vector<uint8_t> &preamble)
      : gr::block("preamble_strip",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t))),
        d_users(1),
        d_userLength(user_len),
        d_pattern(preamble),
        d_mode(0),
        d_offset(0),
        d_purge(0),
        d_search(preamble.size(),255)
    {}

    /*
     * Our virtual destructor.
     */
    preamble_strip_impl::~preamble_strip_impl()
    {
    }

    void
    preamble_strip_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
        ninput_items_required[0] = d_users*noutput_items;
    }

    int
    preamble_strip_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
        const uint8_t *in = (const uint8_t *) input_items[0];
        uint8_t *out = (uint8_t *) output_items[0];

        int ii(0), oo(0);
  
        while((ii<ninput_items[0])&&(oo<noutput_items)){
          //printf("ii: %d\n", ii);
          switch(d_mode)
          {
            case 0:{//starting up
              d_search[ii%d_pattern.size()] = in[ii];
              ii++;
              if(ii >= d_pattern.size()) {
              d_mode = 1;
              //printf("Changing to mode 1\n");
              }
              break;
            }
            case 1:{//start up completed -> search
              //printf("case 1\n");
              int count = 0;
              for(int i=0; i < d_pattern.size(); i++){
                count += (d_pattern[i]==d_search[i]);
              }
              if(count == d_pattern.size()){
                //printf("Match! moving to mode 2\n");
                d_mode = 2;
                d_offset = 0;
              }
              else{
                for(int i=0; i < d_search.size(); i++){
                  d_search[i] = d_search[i+1];
                }
                d_search[d_search.size()-1] = in[ii];
                ii++;
              }
              break;
            }
            case 2:{//search complete -> move
              //ii is first to oo
              //printf("case 2\n");
              int max_copy = d_userLength - d_pattern.size() - d_offset;
              max_copy = ((noutput_items-oo) < max_copy) ? (noutput_items-oo) : max_copy;
              max_copy = ((ninput_items[0]-ii) < max_copy) ? (ninput_items[0]-ii) : max_copy;
              //printf("maxX_copy: %d\n", max_copy);
              d_offset = (d_offset+max_copy)%(d_userLength-d_pattern.size());
              memcpy( &out[oo], &in[ii], sizeof(uint8_t)*max_copy );
              oo += max_copy;
              ii += max_copy;
              if(d_offset==0){//remove other users now
                //printf("no offset. moving to mode 3\n");
                d_mode = 3;
              }
              break;
            }
            case 3:{
              //printf("case 3\n");
              /*
              int max_purge = d_purge - d_offset;
              max_purge = ((ninput_items[0]-ii) < max_purge) ? (ninput_items[0]-ii) : max_purge;
              printf("doffset %d max_purge %d d_purge %d", d_offset, max_purge, d_purge);
              d_offset = (d_offset+max_purge)%(d_purge);
              printf("case 3\n");
              ii += max_purge;*/
              //printf("d_offset %d\n", d_offset);
              if(d_offset==0){//reset d_search and search
              //printf("Resetting to mode 1\n");
                for(int i=0; i<d_search.size(); i++) d_search[i] = 255;
                d_mode = 1;
              }
              break;
            }
            default:{
              for(int i=0; i< d_search.size(); i++) d_search[i] = 255;
              d_mode = 1;
            }
          }
        }

        //printf("%d %d\n", ii, oo);
        
        consume_each (ii);

        // Tell runtime system how many output items we produced.
        return oo;
    }

  } /* namespace mapper */
} /* namespace gr */

