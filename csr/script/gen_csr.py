#!/usr/bin/env python3
import os, csv, sys
import re
import math
import pdb

from gen_func import *

gen_srdata_wire = True

def gen_rwdata_wires(name):
  return ' '*4 + 'uint_<{XLEN}>' + ' '*4 + f's_rdata_{name};\n'

def reg_proc_pattern(autogen, name, is_struct, is_ro64, is_ro32, rowx_updt_by_hw, rowx_prj_roz64, rowx_prj_roz32, rd_en_roz):
    if autogen:
        reg_proc_str_comm = ''
        reg_proc_str64 = ''
        reg_proc_str32 = ''
        if rowx_rv64_physical and rowx_rv32_physical: #A71/H71 and L71
            if rowx_prj_roz64 and rowx_prj_roz32: #both defined as roz
                reg_proc_str_comm = pattern_id(name, is_struct, True, rowx_updt_by_hw, True, rd_en_roz)
            elif rowx_prj_roz64 and not rowx_prj_roz32: #A71/H71 roz
                reg_proc_str64 = pattern_id(name, is_struct, is_ro64, rowx_updt_by_hw, rowx_prj_roz64, rd_en_roz)
            elif not rowx_prj_roz64 and rowx_prj_roz32: #L71 roz
                reg_proc_str32 = pattern_id(name, is_struct, is_ro32, rowx_updt_by_hw, rowx_prj_roz32, rd_en_roz)
            else: #both not defined as roz
                if is_ro64 and is_ro32: #both defined as ro
                    reg_proc_str_comm = pattern_id(name, is_struct, True, rowx_updt_by_hw, False, rd_en_roz)
                elif is_ro64 and not is_ro32: #A71/H71 ro
                    reg_proc_str64 = pattern_id(name, is_struct, is_ro64, rowx_updt_by_hw, False, rd_en_roz)
                elif not is_ro64 and is_ro32: #L71 ro
                    reg_proc_str32 = pattern_id(name, is_struct, is_ro32, rowx_updt_by_hw, False, rd_en_roz)
                else: #not ro
                    reg_proc_str_comm = pattern_id(name, is_struct, False, rowx_updt_by_hw, False, rd_en_roz)
        elif rowx_rv64_physical and not rowx_rv32_physical:
            reg_proc_str64 = pattern_id(name, is_struct, is_ro64, rowx_updt_by_hw, rowx_prj_roz64, rd_en_roz)
        elif not rowx_rv64_physical and rowx_rv32_physical:
            reg_proc_str32 = pattern_id(name, is_struct, is_ro32, rowx_updt_by_hw, rowx_prj_roz32, rd_en_roz)
        return reg_proc_str_comm, reg_proc_str64, reg_proc_str32
    else:
        return '', '', ''


#################################### MAIN ####################################
if __name__ == "__main__":

    input_file = sys.argv[1]
    updt_file_csr = sys.argv[2]

 
    with open(input_file, newline='') as csrFile:
        reader = csv.reader(csrFile, delimiter=',')# read in a list per row
        header = next(reader)
        #print(header)

        #initial values
        reg_declare_header = '#include "shared_defines.hcodal"\n\n'
        
        reg_proc_str64 = ''
        reg_proc_str32 = ''
        reg_proc_str_comm = ''

        csr_reg_declare64 = ''
        csr_reg_declare32 = ''
        csr_reg_declare_comm = ''

        wire_srdata64 = ''
        wire_srdata32 = '' 
        wire_srdata_comm = '' 

        rdata_mux_str64 = ''
        rdata_mux_str32 = ''
        rdata_mux_str_comm = ''
        rerror_mux_str64 = ''
        rerror_mux_str32 = ''
        rerror_mux_str_comm = ''
        ronly_mux_str64 = ''
        ronly_mux_str32 = ''
        ronly_mux_str_comm = ''      
        write_dec_str64 = ''
        write_dec_str32 = ''
        write_dec_str_comm = ''

        first_item = [True]
        for row in reader:
            rowx_autogen = row[header.index('Auto Gen')].lower() != 'no'

            #define physical registers (not shadow/subset)
            rowx_rv64_physical = row[header.index('A71/H71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']
            rowx_rv32_physical = row[header.index('L71')] not in ['', '-'] and row[header.index('Shadow of')] in ['', '-']
            
            #Register attributes
            rowx_name = row[header.index('Name')]
            rowx_addr = row[header.index('Address (Hex)')]
            rowx_width = row[header.index('Width')]
            #Struct-type: to remove wpri and to allow HW accessing individual register field
            rowx_struct_type = row[header.index('Field Access')].lower() == 'yes'

            #HW write access
            rowx_updt_by_hw = row[header.index('Updated by\n(direct write, not via instructions)')] not in ['', '-']

            #Reset values
            rowx_reset64 = row[header.index('Reset Impl A')]
            rowx_reset32 = row[header.index('Reset Impl L')]

            #Read-only register group (RISC-V defined)
            rowx_riscv_ro = (row[header.index('Field Type')] == 'RO')
            rowx_riscv_rw = not rowx_riscv_ro
            #Project defined read-only registers
            rowx_prj_ro64 = (row[header.index('A71/H71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
            rowx_prj_roz64 = (row[header.index('A71/H71')] == 'ROZ')
            rowx_prj_ro32 = (row[header.index('L71')] == 'RO' or row[header.index('L71')] == 'ROZ')
            rowx_prj_roz32 = (row[header.index('L71')] == 'ROZ')
            #Overall read-only 
            rowx_ro64 = rowx_riscv_ro or rowx_prj_ro64
            rowx_ro32 = rowx_riscv_ro or rowx_prj_ro32
            
            #Dynamic enables
            rowx_en_acc = row[header.index('Access Enable')] not in ['', '-']
            rowx_dis_act = row[header.index('Disable Action')] #'ROZ' or '-'
            rd_en_roz = rowx_en_acc and (rowx_dis_act == 'ROZ')

            #generate structured CSRs
            if rowx_struct_type: #structed
                if rowx_name.find('<') != -1:#Name contains '<'
                    struct_name_list, struct_addr_list = parse_name(rowx_name, rowx_addr)
                    
                    for k in range(0, len(struct_name_list)):
                        
                        if rowx_rv64_physical: #A71/H71
                            rowx_reg_declare64 = gen_reg_struct(struct_name_list[k], struct_addr_list[k], rowx_reset64, rowx_prj_roz64)
                            rowx_wire_srdata64 = gen_rwdata_wires(struct_name_list[k])
                            rowx_rdata_mux_str64  = rdata_mux_case(struct_name_list[k])
                            rowx_rerror_mux_str64 = rerror_mux_case(struct_name_list[k], rowx_en_acc, rowx_dis_act)
                            rowx_ronly_mux_str64  = ronly_mux_case(struct_name_list[k], rowx_ro64)
                            if not rowx_ro64:
                                rowx_write_dec_str64 = write_dec_case(struct_name_list[k])
                            else:
                                rowx_write_dec_str64 = ''

                            if not rowx_rv32_physical:
                                rowx_reg_declare32 = ''
                                rowx_wire_srdata32 = ''
                                rowx_rdata_mux_str32  = ''
                                rowx_rerror_mux_str32 = ''
                                rowx_ronly_mux_str32  = ''
                                rowx_write_dec_str32  = ''
                            
                        if rowx_rv32_physical: #L71   
                            rowx_reg_declare32 = gen_reg_struct(struct_name_list[k], struct_addr_list[k], rowx_reset32, rowx_prj_roz32)
                            rowx_wire_srdata32 = gen_rwdata_wires(struct_name_list[k])                            
                            rowx_rdata_mux_str32 = rdata_mux_case(struct_name_list[k])
                            rowx_rerror_mux_str32 = rerror_mux_case(struct_name_list[k], rowx_en_acc, rowx_dis_act)
                            rowx_ronly_mux_str32 = ronly_mux_case(struct_name_list[k], rowx_ro32)
                            if not rowx_ro32:
                                rowx_write_dec_str32 = write_dec_case(struct_name_list[k])
                            else:
                                rowx_write_dec_str32 = ''

                            if not rowx_rv64_physical:
                                rowx_reg_declare64 = ''
                                rowx_wire_srdata64 = ''
                                rowx_rdata_mux_str64  = ''
                                rowx_rerror_mux_str64 = ''
                                rowx_ronly_mux_str64  = ''
                                rowx_write_dec_str64  = ''

                            ##read MUXes on all physical registers
                            #rdata_mux_str32 += rdata_mux_case(struct_name_list[k])
                            #rerror_mux_str32 += rerror_mux_case(struct_name_list[k], rowx_en_acc, rowx_dis_act)
                            #ronly_mux_str32 += ronly_mux_case(struct_name_list[k], rowx_ro32)
                            #if not rowx_ro32:
                            #    write_dec_str32 += write_dec_case(struct_name_list[k])
                            
                        #clear before comparison
                        if not rowx_rv64_physical and not rowx_rv32_physical:
                            rowx_reg_declare64 = ''
                            rowx_reg_declare32 = ''
                            rowx_wire_srdata64 = ''
                            rowx_wire_srdata32 = ''
                            rowx_rdata_mux_str64  = ''
                            rowx_rerror_mux_str64 = ''
                            rowx_ronly_mux_str64  = ''
                            rowx_write_dec_str64  = ''
                            rowx_rdata_mux_str32  = ''
                            rowx_rerror_mux_str32 = ''
                            rowx_ronly_mux_str32  = ''
                            rowx_write_dec_str32  = ''

                        #register declaration
                        csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32 = gen_final_str(csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32, rowx_reg_declare64, rowx_reg_declare32)

                        #wire declaration
                        wire_srdata_comm, wire_srdata64, wire_srdata32 = gen_final_str(wire_srdata_comm, wire_srdata64, wire_srdata32, rowx_wire_srdata64, rowx_wire_srdata32)

                        #register process pattern
                        str_comm, str64, str32 = reg_proc_pattern(rowx_autogen, struct_name_list[k], True, rowx_ro64, rowx_ro32, rowx_updt_by_hw, rowx_prj_roz64, rowx_prj_roz32, rd_en_roz)
                        reg_proc_str_comm += str_comm
                        reg_proc_str64 += str64
                        reg_proc_str32 += str32

                        #Read MUXes and Write Decoder
                        rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32 = gen_final_str(rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32, rowx_rdata_mux_str64, rowx_rdata_mux_str32)
                        rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32 = gen_final_str(rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32, rowx_rerror_mux_str64, rowx_rerror_mux_str32)
                        ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32 = gen_final_str(ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32, rowx_ronly_mux_str64, rowx_ronly_mux_str32)
                        write_dec_str_comm, write_dec_str64, write_dec_str32 = gen_final_str(write_dec_str_comm, write_dec_str64, write_dec_str32, rowx_write_dec_str64, rowx_write_dec_str32)

                else: #Name doesn't contain '<'
                    if rowx_rv64_physical: #A71/H71
                        rowx_reg_declare64 = gen_reg_struct(rowx_name, rowx_addr, rowx_reset64, rowx_prj_roz64)
                        rowx_wire_srdata64 = gen_rwdata_wires(rowx_name)
                        rowx_rdata_mux_str64  = rdata_mux_case(rowx_name)
                        rowx_rerror_mux_str64 = rerror_mux_case(rowx_name, rowx_en_acc, rowx_dis_act)
                        rowx_ronly_mux_str64  = ronly_mux_case(rowx_name, rowx_ro64)
                        if not rowx_ro64:
                            rowx_write_dec_str64 = write_dec_case(rowx_name)
                        else:
                            rowx_write_dec_str64 = ''

                        if not rowx_rv32_physical:
                            rowx_reg_declare32 = ''
                            rowx_wire_srdata32 = ''
                            rowx_rdata_mux_str32  = ''
                            rowx_rerror_mux_str32 = ''
                            rowx_ronly_mux_str32  = ''
                            rowx_write_dec_str32  = ''

                    if rowx_rv32_physical: #L71    
                        rowx_reg_declare32 = gen_reg_struct(rowx_name, rowx_addr, rowx_reset32, rowx_prj_roz32)
                        rowx_wire_srdata32 = gen_rwdata_wires(rowx_name)
                        rowx_rdata_mux_str32  = rdata_mux_case(rowx_name)
                        rowx_rerror_mux_str32 = rerror_mux_case(rowx_name, rowx_en_acc, rowx_dis_act)
                        rowx_ronly_mux_str32  = ronly_mux_case(rowx_name, rowx_ro32)
                        if not rowx_ro32:
                            rowx_write_dec_str32 = write_dec_case(rowx_name)
                        else:
                            rowx_write_dec_str32 = ''

                        if not rowx_rv64_physical:
                            rowx_reg_declare64 = ''
                            rowx_wire_srdata64 = '' 
                            rowx_rdata_mux_str64  = ''
                            rowx_rerror_mux_str64 = ''
                            rowx_ronly_mux_str64  = ''
                            rowx_write_dec_str64  = ''

                    #clear before comparison
                    if not rowx_rv64_physical and not rowx_rv32_physical:
                        rowx_reg_declare64 = ''
                        rowx_reg_declare32 = ''
                        rowx_wire_srdata64 = ''
                        rowx_wire_srdata32 = ''
                        rowx_rdata_mux_str64  = ''
                        rowx_rerror_mux_str64 = ''
                        rowx_ronly_mux_str64  = ''
                        rowx_write_dec_str64  = ''
                        rowx_rdata_mux_str32  = ''
                        rowx_rerror_mux_str32 = ''
                        rowx_ronly_mux_str32  = ''
                        rowx_write_dec_str32  = '' 
                    
                    #register declaration
                    csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32 = gen_final_str(csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32, rowx_reg_declare64, rowx_reg_declare32)

                    #wire declaration
                    wire_srdata_comm, wire_srdata64, wire_srdata32 = gen_final_str(wire_srdata_comm, wire_srdata64, wire_srdata32, rowx_wire_srdata64, rowx_wire_srdata32)

                    #register process pattern
                    str_comm, str64, str32 = reg_proc_pattern(rowx_autogen, rowx_name, True, rowx_ro64, rowx_ro32, rowx_updt_by_hw, rowx_prj_roz64, rowx_prj_roz32, rd_en_roz)
                    reg_proc_str_comm += str_comm
                    reg_proc_str64 += str64
                    reg_proc_str32 += str32

                    #Read MUXes and Write Decoder
                    rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32 = gen_final_str(rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32, rowx_rdata_mux_str64, rowx_rdata_mux_str32)
                    rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32 = gen_final_str(rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32, rowx_rerror_mux_str64, rowx_rerror_mux_str32)
                    ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32 = gen_final_str(ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32, rowx_ronly_mux_str64, rowx_ronly_mux_str32)
                    write_dec_str_comm, write_dec_str64, write_dec_str32 = gen_final_str(write_dec_str_comm, write_dec_str64, write_dec_str32, rowx_write_dec_str64, rowx_write_dec_str32)

            #generate un-structured CSRs
            else: #un-structured
                if rowx_name.find('<') != -1: #Name contains '<'
                    reg_name_list, reg_addr_list = parse_name(rowx_name, rowx_addr)
                    for k in range(0, len(reg_name_list)):
                        if rowx_rv64_physical: #A71/H71
                            rowx_reg_declare64, _, _, _, _, _, _ = gen_reg(rowx_width, reg_name_list[k], reg_addr_list[k], rowx_updt_by_hw, rowx_reset64, first_item, rowx_prj_roz64, True)
                            rowx_wire_srdata64 = gen_rwdata_wires(reg_name_list[k])                            
                            rowx_rdata_mux_str64  = rdata_mux_case(reg_name_list[k])
                            rowx_rerror_mux_str64 = rerror_mux_case(reg_name_list[k], rowx_en_acc, rowx_dis_act)
                            rowx_ronly_mux_str64  = ronly_mux_case(reg_name_list[k], rowx_ro64)
                            if not rowx_ro64:
                                rowx_write_dec_str64 = write_dec_case(reg_name_list[k])
                            else:
                                rowx_write_dec_str64 = ''

                            if not rowx_rv32_physical:
                                rowx_reg_declare32 = ''
                                rowx_wire_srdata32 = ''
                                rowx_rdata_mux_str32  = ''
                                rowx_rerror_mux_str32 = ''
                                rowx_ronly_mux_str32  = ''
                                rowx_write_dec_str32  = ''
                            
                        if rowx_rv32_physical: #L71
                            rowx_reg_declare32, _, _, _, _, _, _ = gen_reg(rowx_width, reg_name_list[k], reg_addr_list[k], rowx_updt_by_hw, rowx_reset32, first_item, rowx_prj_roz32, False)
                            rowx_wire_srdata32 = gen_rwdata_wires(reg_name_list[k])
                            rowx_rdata_mux_str32  = rdata_mux_case(reg_name_list[k])
                            rowx_rerror_mux_str32 = rerror_mux_case(reg_name_list[k], rowx_en_acc, rowx_dis_act)
                            rowx_ronly_mux_str32  = ronly_mux_case(reg_name_list[k], rowx_ro32)
                            if not rowx_ro32:
                                rowx_write_dec_str32 = write_dec_case(reg_name_list[k])
                            else:
                                rowx_write_dec_str32 = ''

                            if not rowx_rv64_physical:
                                rowx_reg_declare64 = ''
                                rowx_wire_srdata64 = ''
                                rowx_rdata_mux_str64  = ''
                                rowx_rerror_mux_str64 = ''
                                rowx_ronly_mux_str64  = ''
                                rowx_write_dec_str64  = ''

                        #clear before comparison
                        if not rowx_rv64_physical and not rowx_rv32_physical:
                            rowx_reg_declare64 = ''
                            rowx_reg_declare32 = ''
                            rowx_wire_srdata64 = ''
                            rowx_wire_srdata32 = ''
                            rowx_rdata_mux_str64  = ''
                            rowx_rerror_mux_str64 = ''
                            rowx_ronly_mux_str64  = ''
                            rowx_write_dec_str64  = ''
                            rowx_rdata_mux_str32  = ''
                            rowx_rerror_mux_str32 = ''
                            rowx_ronly_mux_str32  = ''
                            rowx_write_dec_str32  = ''

                        #register declaration
                        csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32 = gen_final_str(csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32, rowx_reg_declare64, rowx_reg_declare32)

                        #wire declaration
                        wire_srdata_comm, wire_srdata64, wire_srdata32 = gen_final_str(wire_srdata_comm, wire_srdata64, wire_srdata32, rowx_wire_srdata64, rowx_wire_srdata32)

                        #register process pattern
                        str_comm, str64, str32 = reg_proc_pattern(rowx_autogen, reg_name_list[k], False, rowx_ro64, rowx_ro32, rowx_updt_by_hw, rowx_prj_roz64, rowx_prj_roz32, rd_en_roz)
                        reg_proc_str_comm += str_comm
                        reg_proc_str64 += str64
                        reg_proc_str32 += str32

                        #Read MUXes and Write Decoder
                        rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32 = gen_final_str(rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32, rowx_rdata_mux_str64, rowx_rdata_mux_str32)
                        rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32 = gen_final_str(rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32, rowx_rerror_mux_str64, rowx_rerror_mux_str32)
                        ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32 = gen_final_str(ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32, rowx_ronly_mux_str64, rowx_ronly_mux_str32)
                        write_dec_str_comm, write_dec_str64, write_dec_str32 = gen_final_str(write_dec_str_comm, write_dec_str64, write_dec_str32, rowx_write_dec_str64, rowx_write_dec_str32)

                else: #Name doesn't contain '<'
                    if rowx_rv64_physical: #A71/H71
                        rowx_reg_declare64, _, _, _, _, _, _ = gen_reg(rowx_width, rowx_name, rowx_addr, rowx_updt_by_hw, rowx_reset64, first_item, rowx_prj_roz64, True)
                        rowx_wire_srdata64 = gen_rwdata_wires(rowx_name)
                        rowx_rdata_mux_str64  = rdata_mux_case(rowx_name)
                        rowx_rerror_mux_str64 = rerror_mux_case(rowx_name, rowx_en_acc, rowx_dis_act)
                        rowx_ronly_mux_str64  = ronly_mux_case(rowx_name, rowx_ro64)
                        if not rowx_ro64:
                            rowx_write_dec_str64 = write_dec_case(rowx_name)
                        else:
                            rowx_write_dec_str64 = ''

                        if not rowx_rv32_physical:
                            rowx_reg_declare32 = ''
                            rowx_wire_srdata32 = ''
                            rowx_rdata_mux_str32  = ''
                            rowx_rerror_mux_str32 = ''
                            rowx_ronly_mux_str32  = ''
                            rowx_write_dec_str32   = ''

                    if rowx_rv32_physical: #L71
                        rowx_reg_declare32, _, _, _, _, _, _ = gen_reg(rowx_width, rowx_name, rowx_addr, rowx_updt_by_hw, rowx_reset32, first_item, rowx_prj_roz32, False)
                        rowx_wire_srdata32 = gen_rwdata_wires(rowx_name)
                        rowx_rdata_mux_str32  = rdata_mux_case(rowx_name)
                        rowx_rerror_mux_str32 = rerror_mux_case(rowx_name, rowx_en_acc, rowx_dis_act)
                        rowx_ronly_mux_str32  = ronly_mux_case(rowx_name, rowx_ro32)
                        if not rowx_ro32:
                            rowx_write_dec_str32 = write_dec_case(rowx_name)
                        else:
                            rowx_write_dec_str32 = ''

                        if not rowx_rv64_physical:
                            rowx_reg_declare64 = ''
                            rowx_wire_srdata64 = ''
                            rowx_rdata_mux_str64  = ''
                            rowx_rerror_mux_str64 = ''
                            rowx_ronly_mux_str64  = ''
                            rowx_write_dec_str64  = ''
                        
                    #clear before comparison
                    if not rowx_rv64_physical and not rowx_rv32_physical:
                        rowx_reg_declare64 = ''
                        rowx_reg_declare32 = ''
                        rowx_wire_srdata64 = ''
                        rowx_wire_srdata32 = ''
                        rowx_rdata_mux_str64  = ''
                        rowx_rerror_mux_str64 = ''
                        rowx_ronly_mux_str64  = ''
                        rowx_write_dec_str64  = ''
                        rowx_rdata_mux_str32  = ''
                        rowx_rerror_mux_str32 = ''
                        rowx_ronly_mux_str32  = ''
                        rowx_write_dec_str32  = ''

                    #register declaration
                    csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32 = gen_final_str(csr_reg_declare_comm, csr_reg_declare64, csr_reg_declare32, rowx_reg_declare64, rowx_reg_declare32)
                    
                    #wire declaration
                    wire_srdata_comm, wire_srdata64, wire_srdata32 = gen_final_str(wire_srdata_comm, wire_srdata64, wire_srdata32, rowx_wire_srdata64, rowx_wire_srdata32)
                    
                    #register process pattern
                    str_comm, str64, str32 = reg_proc_pattern(rowx_autogen, rowx_name, False, rowx_ro64, rowx_ro32, rowx_updt_by_hw, rowx_prj_roz64, rowx_prj_roz32, rd_en_roz)
                    reg_proc_str_comm += str_comm
                    reg_proc_str64 += str64
                    reg_proc_str32 += str32

                    #Read MUXes and Write Decoder
                    rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32 = gen_final_str(rdata_mux_str_comm, rdata_mux_str64, rdata_mux_str32, rowx_rdata_mux_str64, rowx_rdata_mux_str32)
                    rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32 = gen_final_str(rerror_mux_str_comm, rerror_mux_str64, rerror_mux_str32, rowx_rerror_mux_str64, rowx_rerror_mux_str32)
                    ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32 = gen_final_str(ronly_mux_str_comm, ronly_mux_str64, ronly_mux_str32, rowx_ronly_mux_str64, rowx_ronly_mux_str32)
                    write_dec_str_comm, write_dec_str64, write_dec_str32 = gen_final_str(write_dec_str_comm, write_dec_str64, write_dec_str32, rowx_write_dec_str64, rowx_write_dec_str32)

#----------------------------------------------------------------------------
# Insert generated code into csr.codal
#----------------------------------------------------------------------------
    #filename1 = './model/csr/modules/test.codal'
    filename1 = updt_file_csr
    
    #temporary assignments begin
    reg_declare_str = csr_reg_declare_comm + hw_config_ifdef(csr_reg_declare64, True) + hw_config_ifdef(csr_reg_declare32, False)
    if gen_srdata_wire:
        wire_declare_str = wire_srdata_comm + hw_config_ifdef(wire_srdata64, True) + hw_config_ifdef(wire_srdata32, False)
    else:
        wire_declare_str = ''
    reg_proc_str = reg_proc_str_comm + hw_config_ifdef(reg_proc_str64, True) + hw_config_ifdef(reg_proc_str32, False)

    rdata_mux_str  = rdata_mux_str_comm  + hw_config_ifdef(rdata_mux_str64, True)  + hw_config_ifdef(rdata_mux_str32, False)
    rerror_mux_str = rerror_mux_str_comm + hw_config_ifdef(rerror_mux_str64, True) + hw_config_ifdef(rerror_mux_str32, False)
    ronly_mux_str  = ronly_mux_str_comm  + hw_config_ifdef(ronly_mux_str64, True)  + hw_config_ifdef(ronly_mux_str32, False)
    write_dec_str  = write_dec_str_comm  + hw_config_ifdef(write_dec_str64, True)  + hw_config_ifdef(write_dec_str32, False)
   
    #temporary assignments end
    autogen_dict_csr = {'reg_declare': reg_declare_str,
                        'wire_declare': wire_declare_str,
                        'reg_proc': reg_proc_str,
                        'rdata_mux': rdata_mux_str,
                        'rerror_mux': rerror_mux_str,
                        'ronly_mux': ronly_mux_str,
                        'write_dec': write_dec_str}
    
    auto_insert(filename1,autogen_dict_csr)
