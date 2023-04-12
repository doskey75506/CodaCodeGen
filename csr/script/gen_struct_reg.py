#!/usr/bin/env python3
import os, csv, sys
import re
import math
import pdb

from gen_func import *

#################################### MAIN ####################################
if __name__ == "__main__":

  input_file = sys.argv[1]
  output_file_struct = sys.argv[2]
  if gen_struct_conv:
    output_file_struct_conv = sys.argv[3]

  with open(input_file, newline='') as csrFile:
    reader = csv.reader(csrFile, delimiter=',')# read in a list per row
    header = next(reader)
    #print(header)

#----------------------------------------------------------------------------
# Structure declaration
#----------------------------------------------------------------------------

    rowx_struct_rd64 = ''
    rowx_struct_rd32 = ''
    rowx_struct_wr64 = ''
    rowx_struct_wr32 = ''
    
    with open(output_file_struct, mode='w', newline = '') as codal_struct, open(output_file_struct_conv, mode='w', newline = '') as codal_struct_conv:
    #with open(output_file_struct, mode='w', newline = '') as codal_struct:

        final_struct64 = ''
        final_struct32 = ''
        final_struct_comm = ''
        
        csr_data_conv_start = '#include "shared_defines.hcodal"\n\n'
        csr_data_conv_start += 'module csr_data_conv_t\n'
        csr_data_conv_start += '{\n'
        if gen_struct_conv:
            codal_struct_conv.write(csr_data_conv_start)
        
        first_item = [True]
        for row in reader:
            #row attributes
            rowx_name = row[header.index('Name')]
            rowx_addr = row[header.index('Address (Hex)')]
            rowx_rv64_valid = row[header.index('A71/H71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']
            rowx_rv32_valid = row[header.index('L71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']
            rowx_struct_type = row[header.index('Field Access')].lower() == 'yes'
            
            #generate structured CSRs
            if rowx_struct_type:
                if rowx_name.find('<') != -1:#Name contains '<'
                    struct_name_list, _ = parse_name(rowx_name, rowx_addr)
                    for k in range(0, len(struct_name_list)):

                        struct_name = struct_name_list[k]

                        if rowx_rv64_valid:
                            rowx_struct64, _, _, _, _, _, _, rowx_struct_rd, rowx_struct_wr, _ = gen_struct(struct_name_list[k], header, row, first_item, True)
                            rowx_struct_rd64 = rowx_struct_rd
                            rowx_struct_wr64 = rowx_struct_wr
                            if not rowx_rv32_valid:
                                rowx_struct32 = ''
                                rowx_struct_rd32 = ''
                                rowx_struct_rd32 = ''
                        
                        if rowx_rv32_valid:
                            rowx_struct32, _, _, _, _, _, _, rowx_struct_rd, rowx_struct_wr, _ = gen_struct(struct_name_list[k], header, row, first_item, False)
                            rowx_struct_rd32 = rowx_struct_rd
                            rowx_struct_wr32 = rowx_struct_wr
                            if not rowx_rv64_valid:
                                rowx_struct64 = ''
                                rowx_struct_rd64 = ''
                                rowx_struct_wr64 = ''

                        if not rowx_rv64_valid and not rowx_rv32_valid:
                            #clear before comparison
                            rowx_struct64 = ''
                            rowx_struct32 = ''
                            rowx_struct_rd64 = ''
                            rowx_struct_wr64 = ''
                            rowx_struct_rd32 = ''
                            rowx_struct_wr32 = ''

                        #compare rowx_struct64 and rowx_struct32
                        if (rowx_struct64 == rowx_struct32):
                            final_struct_comm += rowx_struct64
                            final_struct64 += ''
                            final_struct32 += ''
                        else:
                            final_struct_comm += ''
                            final_struct64 += rowx_struct64
                            final_struct32 += rowx_struct32
                        
                        #compare rowx_struct_rd64 and rowx_struct_rd32
                        if (rowx_struct_rd64 == rowx_struct_rd32):
                            final_unpack_comm = rowx_struct_rd64
                            final_unpack64 = ''
                            final_unpack32 = ''
                        else:
                            final_unpack_comm = ''
                            final_unpack64 = rowx_struct_rd64
                            final_unpack32 = rowx_struct_rd32
                        
                        if rowx_rv64_valid and rowx_rv32_valid:
                            final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack_comm)
                            final_unpack_middle += hw_config_ifdef(unpack_struct_to_xlen_middle(struct_name, final_unpack64), True) 
                            final_unpack_middle += hw_config_ifdef(unpack_struct_to_xlen_middle(struct_name, final_unpack32), False)
                            final_unpack = unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle)
                        elif rowx_rv64_valid and not rowx_rv32_valid: 
                            final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack64) #no ifdef
                            final_unpack = hw_config_ifdef(unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle), True)
                        elif not rowx_rv64_valid and rowx_rv32_valid: 
                            final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack32) #no ifdef
                            final_unpack = hw_config_ifdef(unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle), False)
                        else:
                            final_unpack = ''
                        if gen_struct_conv:
                            codal_struct_conv.write(final_unpack)


                        #compare rowx_struct_wr64 and rowx_struct_wr32
                        if (rowx_struct_wr64 == rowx_struct_wr32):
                            final_pack_comm = rowx_struct_wr64
                            final_pack64 = ''
                            final_pack32 = ''
                        else:
                            final_pack_comm = ''
                            final_pack64 = rowx_struct_wr64
                            final_pack32 = rowx_struct_wr32
                        
                        if rowx_rv64_valid and rowx_rv32_valid:
                            final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack_comm)
                            final_pack_middle += hw_config_ifdef(pack_xlen_to_struct_middle(struct_name, final_pack64), True) 
                            final_pack_middle += hw_config_ifdef(pack_xlen_to_struct_middle(struct_name, final_pack32), False)
                            final_pack = pack_xlen_to_struct_wrap(struct_name, final_pack_middle)
                        elif rowx_rv64_valid and not rowx_rv32_valid: 
                            final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack64) #no ifdef
                            final_pack = hw_config_ifdef(pack_xlen_to_struct_wrap(struct_name, final_pack_middle), True)
                        elif not rowx_rv64_valid and rowx_rv32_valid: 
                            final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack32) #no ifdef
                            final_pack = hw_config_ifdef(pack_xlen_to_struct_wrap(struct_name, final_pack_middle), False)
                        else:
                            final_pack = ''
                        if gen_struct_conv:
                            codal_struct_conv.write(final_pack)

               
                else:#Name doesn't contain '<'
                    struct_name = rowx_name
                    
                    if rowx_rv64_valid:
                        rowx_struct64,  _, _, _, _, _, _, rowx_struct_rd, rowx_struct_wr, _ = gen_struct(rowx_name, header, row, first_item, True)
                        rowx_struct_rd64 = rowx_struct_rd
                        rowx_struct_wr64 = rowx_struct_wr

                        if not rowx_rv32_valid:
                            rowx_struct32 = ''
                            rowx_struct_rd32 = ''
                            rowx_struct_wr32 = ''
                    
                    if rowx_rv32_valid:
                        rowx_struct32, _, _, _, _, _, _, rowx_struct_rd, rowx_struct_wr, _ = gen_struct(rowx_name, header, row, first_item, False)
                        rowx_struct_rd32 = rowx_struct_rd
                        rowx_struct_wr32 = rowx_struct_wr
                        if not rowx_rv64_valid:
                            rowx_struct64 = ''
                            rowx_struct_rd64 = ''
                            rowx_struct_wr64 = '' 

                    if not rowx_rv64_valid and not rowx_rv32_valid:
                        #clear before comparison
                        rowx_struct64 = ''
                        rowx_struct32 = ''
                        rowx_struct_rd64 = ''
                        rowx_struct_wr64 = ''
                        rowx_struct_rd32 = ''
                        rowx_struct_wr32 = ''

                    #compare rowx_struct64 and rowx_struct32
                    # if (rowx_struct64 == rowx_struct32):
                    #     final_struct_comm += rowx_struct64
                    #     final_struct64 += ''
                    #     final_struct32 += ''
                    # else:
                    #     final_struct_comm += ''
                    #     final_struct64 += rowx_struct64
                    #     final_struct32 += rowx_struct32


                    #compare rowx_struct_rd64 and rowx_struct_rd32
                    # if (rowx_struct_rd64 == rowx_struct_rd32):
                    #     final_unpack_comm = rowx_struct_rd64
                    #     final_unpack64 = ''
                    #     final_unpack32 = ''
                    # else:
                    #     final_unpack_comm = ''
                    #     final_unpack64 = rowx_struct_rd64
                    #     final_unpack32 = rowx_struct_rd32

                    c, t64, t32 = longest_common_leader(rowx_struct64, rowx_struct32)
                    final_struct_comm += c
                    final_struct64 += t64
                    final_struct32 += t32

                    c, t64, t32 = longest_common_leader(rowx_struct_rd64, rowx_struct_rd32)
                    final_unpack_comm = c
                    final_unpack64 = t64
                    final_unpack32 = t32

                    if rowx_rv64_valid and rowx_rv32_valid:
                        final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack_comm)
                        final_unpack_middle += hw_config_ifdef(unpack_struct_to_xlen_middle(struct_name, final_unpack64), True) 
                        final_unpack_middle += hw_config_ifdef(unpack_struct_to_xlen_middle(struct_name, final_unpack32), False)
                        final_unpack = unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle)
                    elif rowx_rv64_valid and not rowx_rv32_valid: 
                        final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack64) #no ifdef
                        final_unpack = hw_config_ifdef(unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle), True)
                    elif not rowx_rv64_valid and rowx_rv32_valid: 
                        final_unpack_middle = unpack_struct_to_xlen_middle(struct_name, final_unpack32) #no ifdef
                        final_unpack = hw_config_ifdef(unpack_struct_to_xlen_wrap(struct_name, final_unpack_middle), False)
                    else:
                        final_unpack = ''
                    if gen_struct_conv:
                        codal_struct_conv.write(final_unpack)

                    #compare rowx_struct_wr64 and rowx_struct_wr32
                    if (rowx_struct_wr64 == rowx_struct_wr32):
                        final_pack_comm = rowx_struct_wr64
                        final_pack64 = ''
                        final_pack32 = ''
                    else:
                        final_pack_comm = ''
                        final_pack64 = rowx_struct_wr64
                        final_pack32 = rowx_struct_wr32
                    
                    if rowx_rv64_valid and rowx_rv32_valid:
                        final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack_comm)
                        final_pack_middle += hw_config_ifdef(pack_xlen_to_struct_middle(struct_name, final_pack64), True) 
                        final_pack_middle += hw_config_ifdef(pack_xlen_to_struct_middle(struct_name, final_pack32), False)
                        final_pack = pack_xlen_to_struct_wrap(struct_name, final_pack_middle)
                    elif rowx_rv64_valid and not rowx_rv32_valid: 
                        final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack64) #no ifdef
                        final_pack = hw_config_ifdef(pack_xlen_to_struct_wrap(struct_name, final_pack_middle), True)
                    elif not rowx_rv64_valid and rowx_rv32_valid: 
                        final_pack_middle = pack_xlen_to_struct_middle(struct_name, final_pack32) #no ifdef
                        final_pack = hw_config_ifdef(pack_xlen_to_struct_wrap(struct_name, final_pack_middle), False)
                    else:
                        final_pack = ''
                    if gen_struct_conv:
                        codal_struct_conv.write(final_pack)
                
        #write to file: struct declaration
        codal_struct.write(final_struct_comm + hw_config_ifdef(final_struct64, True) + hw_config_ifdef(final_struct32, False))
        
        #write to file: struct-xlen data conversion

        #write to file: endmodule
        csr_data_conv_end = '}; //endmodule csr_data_conv_t\n'
        if gen_struct_conv:
            codal_struct_conv.write(csr_data_conv_end)