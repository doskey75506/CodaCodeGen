#!/usr/bin/env python3

import os, csv, sys
import re
import math
import pdb
#pdb.set_trace()

from gen_csr_func import *

# CSR length table
#dict_reg_len = {"XLEN":64, "SXLEN":64, "MXLEN":64, "DXLEN":64, "XLEN*TRIGGERS":256, "clog2(VLEN)":7, "TRIGGERS":4}
dict_reg_len["XLEN"] = 64
dict_reg_len["SXLEN"] = 64
dict_reg_len["MXLEN"] = 64
dict_reg_len["DXLEN"] = 64
dict_reg_len["XLEN*TRIGGERS"] = 256
dict_reg_len["TRIGGERS"] = 4

#################################### MAIN ####################################
if __name__ == "__main__":
    
    input_file = sys.argv[1]
    output_file_struct = sys.argv[2]
    output_file_csr_bank = sys.argv[3]
    output_file_csr_port_declare = sys.argv[4]
    output_file_csr_port_connect = sys.argv[5]

    with open(input_file, newline='') as csrFile:
        reader = csv.reader(csrFile, delimiter=',')# read in a list per row
        header = next(reader)
        #print(header)

        #generate code

# ------------ module start code ------------
        csr_bank_reg_declare="""

#include "shared_defines.hcodal"
#include "csr_define.hcodal"

#define SXLEN           XLEN
#define MXLEN           XLEN
#define DXLEN           XLEN
#define VLEN            OPTION_VLEN
#define TRIGGERS        4

module csr_bank_t
{
"""
# ------------ function code ------------
        csr_bank_func_rd_instr_io = """
    public always void rd_access(
        //input
        uint1               read,
        uint12              raddr,
        //dynamic enables
"""
        csr_bank_func_instr_rd_start = """
        read_err = 0;
        read_only = 0;
        
        if (read)
        {
            switch (raddr)
            {
"""
        csr_bank_func_instr_rd_body = "" 
        csr_bank_func_instr_rd_end = """
                default: 
                    read_err = 1;
                    read_only = 0;
                    break;
            }
        }
    }
"""

        csr_bank_func_wr_instr_io = """
    public always void wr_access(
        //sw input
        uint1               write,
        uint12              waddr,
        uint64              wdata,
        //hw input
"""
        csr_bank_func_wr_instr_wire = """
        //local wires
"""
        csr_bank_func_instr_wire_init = """

        //Set initial value
"""

        csr_bank_func_instr_wr_start = """
        if (write)
        {
            switch (waddr)
            {
"""
        csr_bank_func_instr_wr_body = "" 
        csr_bank_func_instr_wr_end = """
                default: 
                    //eprintf("Unknown CSR 0x%x for writing!", waddr);        
                    break; 
            }
        }
"""
#        csr_bank_func_instr_we_clr_start = """
#        else
#        {
#"""
#        csr_bank_func_instr_we_clr_body = ""
#        csr_bank_func_instr_we_clr_end = """
#        }
#"""        

        csr_bank_func_updt_reg = "\n\n" + ' '*8 + "//Register write selection\n"
        csr_bank_func_updt_assert = "\n\n" + ' '*8 + "//Add assertions\n"
        csr_bank_func_instr_end = """
    }

"""
        csr_port_declare = ""
        csr_port_connect = ""


        #collect info on every row read from the CSR table; generate csr_struct.codal & csr_define.codal
        with open(output_file_struct, mode='w', newline = '') as codal_struct:
          
          first_item = [True]
          for row in reader:
            rowx_name = row[header.index('Name')]
            rowx_addr = row[header.index('Address (Hex)')]
            rowx_width = row[header.index('Width')]
            rowx_updt_by_hw = row[header.index('Updated by\n(direct write, not via instructions)')]
            rowx_reset = row[header.index('Reset Impl A')]
            #If both Enable/Disable values are equal, no need to create Access Enable inputs
            rowx_enable_access = row[header.index('Access Enable')]
            rowx_disable_access = row[header.index('Disable Action')]
            if row[header.index('Access Enable')] not in ['', '-']:
              rowx_enable = 1
            else:
              rowx_enable = 0
            rowx_ro = (row[header.index('Field Type')] == 'RO')
                
            if dict_reg_len["XLEN"] == 64:
                rowx_prj_ro = (row[header.index('A71/H71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
                rowx_prj_roz = (row[header.index('A71/H71')] == 'ROZ')
            else:
                rowx_prj_ro = (row[header.index('L71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
                rowx_prj_roz = (row[header.index('A71/H71')] == 'ROZ')

        
            #generate valid CSRs (not related to structured/unstructured declaration)
            if row[header.index('A71/H71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']:

              #declare dynamic enable inputs
              csr_bank_func_rd_instr_io += gen_rd_enable(rowx_name, rowx_enable)
      
              #generate structured CSRs
              if row[header.index('Field Access')].lower() == 'yes':
                if rowx_name.find('<') != -1:#Name contains '<'
                    struct_name_list, struct_addr_list = parse_name(rowx_name, rowx_addr)
                    for k in range(0, len(struct_name_list)):
                       rowx_struct, rowx_io, rowx_conn, rowx_wire, rowx_wire_init, rowx_updt, rowx_updt_assert, rowx_rd, rowx_we, rowx_we_clr = gen_struct(struct_name_list[k], header, row, first_item)
                       codal_struct.write(rowx_struct)
                       csr_bank_reg_declare += gen_reg_struct(struct_name_list[k], struct_addr_list[k], rowx_reset, rowx_prj_roz)
                       csr_bank_func_wr_instr_io += rowx_io
                       csr_bank_func_wr_instr_wire += rowx_wire
                       csr_bank_func_instr_wire_init += rowx_wire_init
                       csr_bank_func_instr_rd_body += rowx_rd
                       csr_bank_func_instr_wr_body += rowx_we
                       csr_bank_func_updt_reg += rowx_updt
                       csr_bank_func_updt_assert += rowx_updt_assert
                       csr_port_declare += rowx_io
                       csr_port_connect += rowx_conn
                else:
                    rowx_struct, rowx_io, rowx_conn, rowx_wire, rowx_wire_init, rowx_updt, rowx_updt_assert, rowx_rd, rowx_we, rowx_we_clr = gen_struct(rowx_name, header, row, first_item)
                    codal_struct.write(rowx_struct)
                    csr_bank_reg_declare += gen_reg_struct(rowx_name, rowx_addr, rowx_reset, rowx_prj_roz)
                    csr_bank_func_wr_instr_io += rowx_io
                    csr_bank_func_wr_instr_wire += rowx_wire
                    csr_bank_func_instr_wire_init += rowx_wire_init
                    csr_bank_func_instr_rd_body += rowx_rd
                    csr_bank_func_instr_wr_body += rowx_we
                    csr_bank_func_updt_reg += rowx_updt
                    csr_bank_func_updt_assert += rowx_updt_assert
                    csr_port_declare += rowx_io
                    csr_port_connect += rowx_conn

              #generate un-structured CSRs
              else:
                  if rowx_name.find('<') != -1:#Name contains '<'
                    reg_name_list, reg_addr_list = parse_name(rowx_name, rowx_addr)
                    for k in range(0, len(reg_name_list)):
                      rowx_reg, rowx_io, rowx_conn, rowx_wire, rowx_wire_init, rowx_updt, rowx_updt_assert = gen_reg(rowx_width, reg_name_list[k], reg_addr_list[k], rowx_updt_by_hw, rowx_reset, first_item, rowx_prj_roz)
                      csr_bank_reg_declare += rowx_reg
                      csr_bank_func_wr_instr_io += rowx_io
                      csr_bank_func_wr_instr_wire += rowx_wire
                      csr_bank_func_instr_wire_init += rowx_wire_init
                      is_list = True
                      bit_index = k
                      csr_bank_func_instr_rd_body += gen_rd_mux(is_list, bit_index, rowx_name, reg_name_list[k], rowx_width, rowx_enable_access, rowx_disable_access, rowx_ro, rowx_prj_roz)
                      csr_bank_func_instr_wr_body += gen_wena(reg_name_list[k], rowx_updt_by_hw, rowx_width, rowx_ro, rowx_prj_ro)
                      csr_bank_func_updt_reg += rowx_updt
                      csr_bank_func_updt_assert += rowx_updt_assert
                      csr_port_declare += rowx_io
                      csr_port_connect += rowx_conn
                  else:
                    rowx_reg, rowx_io, rowx_conn, rowx_wire, rowx_wire_init, rowx_updt, rowx_updt_assert = gen_reg(rowx_width, rowx_name, rowx_addr, rowx_updt_by_hw, rowx_reset, first_item, rowx_prj_roz)
                    csr_bank_reg_declare += rowx_reg
                    csr_bank_func_wr_instr_io += rowx_io
                    csr_bank_func_wr_instr_wire += rowx_wire
                    csr_bank_func_instr_wire_init += rowx_wire_init
                    is_list = False
                    csr_bank_func_instr_rd_body += gen_rd_mux(is_list, 0, rowx_name, rowx_name, rowx_width, rowx_enable_access, rowx_disable_access, rowx_ro, rowx_prj_roz)
                    csr_bank_func_instr_wr_body += gen_wena(rowx_name, rowx_updt_by_hw, rowx_width, rowx_ro, rowx_prj_ro)
                    csr_bank_func_updt_reg += rowx_updt
                    csr_bank_func_updt_assert += rowx_updt_assert
                    csr_port_declare += rowx_io
                    csr_port_connect += rowx_conn

          #complete read function io declare
          csr_bank_func_rd_instr_io += """
        //output
        uint64&             rdata,
        uint1&              read_err,
        uint1&              read_only)
    {
"""

          #complete write function io declare
          csr_bank_func_wr_instr_io += """
        )
  {
"""

          #generate csr_bank.codal all together
          with open(output_file_csr_bank, mode='w', newline = '') as codal_csr_bank:
            codal_csr_bank.write(csr_bank_reg_declare)
            codal_csr_bank.write(csr_bank_func_rd_instr_io)
            codal_csr_bank.write(csr_bank_func_instr_rd_start)
            codal_csr_bank.write(csr_bank_func_instr_rd_body)
            codal_csr_bank.write(csr_bank_func_instr_rd_end)

            codal_csr_bank.write(csr_bank_func_wr_instr_io)
            codal_csr_bank.write(csr_bank_func_wr_instr_wire)
            codal_csr_bank.write(csr_bank_func_instr_wire_init)
            codal_csr_bank.write(csr_bank_func_instr_wr_start)
            codal_csr_bank.write(csr_bank_func_instr_wr_body)
            codal_csr_bank.write(csr_bank_func_instr_wr_end)
            #codal_csr_bank.write(csr_bank_func_instr_we_clr_start)            
            #codal_csr_bank.write(csr_bank_func_instr_we_clr_body)
            #codal_csr_bank.write(csr_bank_func_instr_we_clr_end)
            codal_csr_bank.write(csr_bank_func_updt_reg)
            codal_csr_bank.write(csr_bank_func_updt_assert)
            codal_csr_bank.write(csr_bank_func_instr_end)
            codal_csr_bank.write(gen_end_code())

          #generate port declaration
          with open(output_file_csr_port_declare, mode='w', newline = '') as codal_csr_port_declare:
            codal_csr_port_declare.write(csr_port_declare)

          #generate port connection
          with open(output_file_csr_port_connect, mode='w', newline = '') as codal_csr_port_connect:
            codal_csr_port_connect.write(csr_port_connect)

##############################################################################