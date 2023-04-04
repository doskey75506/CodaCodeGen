#!/usr/bin/env python3

import os, csv, sys
import re
import pdb
#pdb.set_trace()

from gen_func import *

def gen_def_mask(name, mask):
  def_str = f"#define CSR_MASK_{name.upper()}"
  def_str +=' '*(32-len(def_str))
  def_str +=f"{mask}\n"
  return def_str

#################################### MAIN ####################################
if __name__ == "__main__":
    
    input_file = sys.argv[1]
    output_file_define = sys.argv[2]

    def_header = '#include "shared_defines.hcodal"\n\n'
    def_mask64 = '#if (OPTION_XLEN == 64)\n'
    def_mask32 = '#if (OPTION_XLEN == 32)\n'

    with open(input_file, newline='') as csrFile:
        reader = csv.reader(csrFile, delimiter=',')# read in a list per row
        header = next(reader)

        #collect info on every row read from the CSR table; generate csr_define.codal
        with open(output_file_define, mode='w', newline = '') as codal_def:
          
          first_item = [True]
          for row in reader:
            rowx_name = row[header.index('Name')]
            rowx_addr = row[header.index('Address (Hex)')]
            #temporarily assign 0s to masks
            rowx_mask64 = '(0x0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000)'
            rowx_mask32 = '(0x0000_0000_0000_0000_0000_0000_0000_0000)'

            #generate defines (for all HW configurations A71/H71/L71 including shadow registers)
            if row[header.index('A71/H71')] not in ['', '-'] or row[header.index('L71')] not in ['', '-']: 
              if rowx_name.find('<') != -1:#Name contains '<': generate a list of names
                def_name_list, def_addr_list = parse_name(rowx_name, rowx_addr)
                for j in range(0, len(def_name_list)):
                  if row[header.index('A71/H71')] not in ['', '-']:
                    def_mask64 += gen_def_mask(def_name_list[j], rowx_mask64)
                  if row[header.index('L71')] not in ['', '-']: 
                    def_mask32 += gen_def_mask(def_name_list[j], rowx_mask32)

              else:
                if row[header.index('A71/H71')] not in ['', '-']:
                  def_mask64 += gen_def_mask(rowx_name, rowx_mask64)
                if row[header.index('L71')] not in ['', '-']: 
                  def_mask32 += gen_def_mask(rowx_name, rowx_mask32)
        
          def_mask64 += '#endif //(OPTION_XLEN == 64)\n\n'
          def_mask32 += '#endif //(OPTION_XLEN == 32)\n\n'
          def_mask = def_header + def_mask64 + def_mask32
          codal_def.write(def_mask)

##############################################################################