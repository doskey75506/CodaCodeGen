#!/usr/bin/env python3
import os, csv, sys
import re
import math
import pdb

from gen_func import *

gen_srdata_struct = False

def gen_rwdata_wires(name):
  return ' '*4 + 'uint_<{XLEN}>' + ' '*4 + f'{name};\n'

def gen_wr_wires(name):
  return ' '*4 + 'uint1' + ' '*6 + f'{name};\n'

#################################### MAIN ####################################
if __name__ == "__main__":

  input_file = sys.argv[1]
  output_file_struct = sys.argv[2]

  with open(input_file, newline='') as csrFile:
    reader = csv.reader(csrFile, delimiter=',')# read in a list per row
    header = next(reader)
    #print(header)

  #////////////////////////////////////////////////////////
  #                   Struct declaration
  #////////////////////////////////////////////////////////
    def_rv64_start = '#if (OPTION_XLEN == 64)\n'
    def_rv32_start = '#if (OPTION_XLEN == 32)\n'

    struct_srdata64 = def_rv64_start + 'struct srdata_t\n{\n'
    struct_srdata32 = def_rv32_start + 'struct srdata_t\n{\n'    

    struct_swr64  = def_rv64_start + 'struct swr_t\n{\n'
    struct_swr32  = def_rv32_start + 'struct swr_t\n{\n'

    struct_hwr64  = def_rv64_start + 'struct hwr_t\n{\n'
    struct_hwr32  = def_rv32_start + 'struct hwr_t\n{\n'

    struct_hwdata64 = def_rv64_start + 'struct hwdata_t\n{\n'
    struct_hwdata32 = def_rv32_start + 'struct hwdata_t\n{\n'    

    with open(output_file_struct, mode='w', newline = '') as codal_struct:
      first_item = [True]
      for row in reader:

  #////////////////////////////////////////////////////////
  #                      Defines
  #////////////////////////////////////////////////////////

        #Register attributes
        rowx_name = row[header.index('Name')]
        rowx_addr = row[header.index('Address (Hex)')]
        #Struct-type: to remove wpri and to allow HW accessing individual register field
        rowx_struct_type = (row[header.index('Field Access')].lower() == 'yes')

        #define project supported registers
        rowx_rv64 = row[header.index('A71/H71')] not in ['', '-']
        rowx_rv32 = row[header.index('L71')] not in ['', '-']
        #define physical registers (not shadow/subset)
        rowx_rv64_physical = row[header.index('A71/H71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']
        rowx_rv32_physical = row[header.index('L71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']

        #HW write access
        rowx_updt_by_hw = row[header.index('Updated by\n(direct write, not via instructions)')] not in ['', '-']
        #Reset values
        rowx_reset64 = row[header.index('Reset Impl A')]
        rowx_reset32 = row[header.index('Reset Impl L')]
        #Read-only register group (RISC-V defined)
        rowx_ro = (row[header.index('Field Type')] == 'RO')
        rowx_rw = not rowx_ro
        #Project defined read-only registers
        rowx_prj_ro64 = (row[header.index('A71/H71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
        rowx_prj_roz64 = (row[header.index('A71/H71')] == 'ROZ')
        rowx_prj_ro32 = (row[header.index('L71')] == 'RO' or row[header.index('L71')] == 'ROZ')
        rowx_prj_roz32 = (row[header.index('L71')] == 'ROZ')
        
        
  #////////////////////////////////////////////////////////
  #                   Generate code
  #////////////////////////////////////////////////////////

        #-----------------------------------------------------------------------------------------
        #generate srdata wires (for all HW configurations A71/H71/L71 excluding shadow registers)
        #-----------------------------------------------------------------------------------------
        if rowx_name.find('<') != -1:#Name contains '<': generate a list of names
            reg_name_list, reg_addr_list = parse_name(rowx_name, rowx_addr)
            for j in range(0, len(reg_name_list)):
                if rowx_rv64_physical:
                    struct_srdata64 += gen_rwdata_wires(reg_name_list[j])
                if rowx_rv32_physical: 
                    struct_srdata32 += gen_rwdata_wires(reg_name_list[j])
        else:
            if rowx_rv64_physical:
                struct_srdata64 += gen_rwdata_wires(rowx_name)
            if rowx_rv32_physical: 
                struct_srdata32 += gen_rwdata_wires(rowx_name)

        #-------------------------------------------------------------------------------
        #generate swr, hwr and hwdata wires (for those registers supporting hW write)
        #-------------------------------------------------------------------------------
        #generate structured CSRs
        if rowx_struct_type: #struct-type
            if rowx_name.find('<') != -1:#Name contains '<'
                reg_name_list, _ = parse_name(rowx_name, rowx_addr)
                for k in range(0, len(reg_name_list)):
                    #generate swr
                    if rowx_rv64_physical:
                        if not rowx_prj_ro64 and not rowx_ro:
                            struct_swr64 += gen_wr_wires(reg_name_list[k])
                    if rowx_rv32_physical:
                        if not rowx_prj_ro32 and not rowx_ro:
                            struct_swr32 += gen_wr_wires(reg_name_list[k])
                    #generate hwr and hwdata
                    if rowx_updt_by_hw:
                        if rowx_rv64_physical:
                            struct_hwr64 += gen_wr_wires(reg_name_list[k])
                            struct_hwdata64 += gen_rwdata_wires(reg_name_list[k])
                        if rowx_rv32_physical:
                            struct_hwr32 += gen_wr_wires(reg_name_list[k])
                            struct_hwdata32 += gen_rwdata_wires(reg_name_list[k])   
            else: #Name doesn't contain '<'
              #generate swr
                if rowx_rv64_physical:
                    if not rowx_prj_ro64 and not rowx_ro:
                        struct_swr64 += gen_wr_wires(rowx_name)
                if rowx_rv32_physical:
                    if not rowx_prj_ro32 and not rowx_ro:
                        struct_swr32 += gen_wr_wires(rowx_name)
                #generate hwr and hwdata
                if rowx_updt_by_hw:
                    if rowx_rv64_physical:
                        struct_hwr64 += gen_wr_wires(rowx_name)
                        struct_hwdata64 += gen_rwdata_wires(rowx_name)
                    if rowx_rv32_physical:
                        struct_hwr32 += gen_wr_wires(rowx_name)
                        struct_hwdata32 += gen_rwdata_wires(rowx_name)
        
        #generate un-structured CSRs
        else: #un-structured
            if rowx_name.find('<') != -1: #Name contains '<'
                reg_name_list, _ = parse_name(rowx_name, rowx_addr)
                for k in range(0, len(reg_name_list)):
                    #generate swr
                    if rowx_rv64_physical:
                        if not rowx_prj_ro64 and not rowx_ro:
                            struct_swr64 += gen_wr_wires(reg_name_list[k])
                    if rowx_rv32_physical:
                        if not rowx_prj_ro32 and not rowx_ro:
                            struct_swr32 += gen_wr_wires(reg_name_list[k])
                    #generate hwr and hwdata
                    if rowx_updt_by_hw:
                        if rowx_rv64_physical:
                            struct_hwr64 += gen_wr_wires(reg_name_list[k])
                            struct_hwdata64 += gen_rwdata_wires(reg_name_list[k])
                        if rowx_rv32_physical:
                            struct_hwr32 += gen_wr_wires(reg_name_list[k])
                            struct_hwdata32 += gen_rwdata_wires(reg_name_list[k])  
            else: #Name doesn't contain '<'
                #generate swr
                if rowx_rv64_physical:
                    if not rowx_prj_ro64 and not rowx_ro:
                        struct_swr64 += gen_wr_wires(rowx_name)
                if rowx_rv32_physical:
                    if not rowx_prj_ro32 and not rowx_ro:
                        struct_swr32 += gen_wr_wires(rowx_name)
                #generate hwr and hwdata
                if rowx_updt_by_hw:
                    if rowx_rv64_physical:
                        struct_hwr64 += gen_wr_wires(rowx_name)
                        struct_hwdata64 += gen_rwdata_wires(rowx_name)
                    if rowx_rv32_physical:
                        struct_hwr32 += gen_wr_wires(rowx_name)
                        struct_hwdata32 += gen_rwdata_wires(rowx_name)

  #////////////////////////////////////////////////////////
  #                   Write to file
  #////////////////////////////////////////////////////////
      struct_end = '};\n'
      def_rv64_end = '#endif //(OPTION_XLEN == 64)\n\n'
      def_rv32_end = '#endif //(OPTION_XLEN == 32)\n\n'

      struct_srdata64 += struct_end + def_rv64_end
      struct_srdata32 += struct_end + def_rv32_end
      struct_srdata = struct_srdata64 + struct_srdata32

      struct_hwr64 += struct_end + def_rv64_end
      struct_hwr32 += struct_end + def_rv32_end
      struct_hwr = struct_hwr64 + struct_hwr32

      struct_swr64 += struct_end + def_rv64_end
      struct_swr32 += struct_end + def_rv32_end
      struct_swr = struct_swr64 + struct_swr32

      struct_hwdata64 += struct_end + def_rv64_end
      struct_hwdata32 += struct_end + def_rv32_end
      struct_hwdata = struct_hwdata64 + struct_hwdata32

      codal_struct.write('#include "shared_defines.hcodal"\n\n')
      if gen_srdata_struct:
        codal_struct.write(struct_srdata)
      codal_struct.write(struct_swr)
      codal_struct.write(struct_hwr)
      codal_struct.write(struct_hwdata)