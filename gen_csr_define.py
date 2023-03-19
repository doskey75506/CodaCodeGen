#!/usr/bin/env python3

import os, csv, sys
import re
import pdb
#pdb.set_trace()

from gen_csr_func import *

#################################### MAIN ####################################
if __name__ == "__main__":
    
    input_file = sys.argv[1]
    output_file_define = sys.argv[2]

    with open(input_file, newline='') as csrFile:
        reader = csv.reader(csrFile, delimiter=',')# read in a list per row
        header = next(reader)
        #print(header)

        #generate code

        #collect info on every row read from the CSR table; generate csr_define.codal
        with open(output_file_define, mode='w', newline='') as codal_def:
          
          first_item = [True]
          for row in reader:
            rowx_name = row[header.index('Name')]
            rowx_addr = row[header.index('Address (Hex)')]

            #generate defines (for all HW configurations A71/H71/L71 including shadow registers)
            if row[header.index('A71/H71')] not in ['', '-'] or row[header.index('L71')] not in ['', '-']: 
              if rowx_name.find('<') != -1:#Name contains '<': generate a list of names
                def_name_list, def_addr_list = parse_name(rowx_name, rowx_addr)
                for j in range(0, len(def_name_list)):
                  codal_def.write(gen_define(def_name_list[j], def_addr_list[j]))

              else:
                codal_def.write(gen_define(rowx_name, rowx_addr))
            
##############################################################################