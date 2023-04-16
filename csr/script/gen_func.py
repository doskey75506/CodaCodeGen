#!/usr/bin/env python3
import os, csv, sys
import re
import math
import pdb
#pdb.set_trace()

#Don't display reserved bits in structure
wpri_in_struct = False
struct_rd_middle_only = True
struct_wr_middle_only = True
s_rdata_is_struct_in_pattern = False
gen_struct_conv = True

#--------------------------------------------------------------------------------
# Register Read/Write Patterns
#--------------------------------------------------------------------------------
# Identify pattern
def pattern_id(reg_name, is_struct, is_ro, is_hw, is_roz, rdata_en):
    #print(reg_name, ', is_struct:', is_struct, ', is_ro:', is_ro, ', is_hw:', is_hw, ', is_roz:', is_roz, ', rdata_en: ', rdata_en)
    if not is_roz: #is_roz belongs to is_ro
        if not is_struct: #xlen-bit
            if not is_ro and not is_hw:
                if reg_name == 'tdata2':
                    return pattern1t(reg_name)
                else:
                    if not rdata_en:
                        return pattern1(reg_name)
                    else:
                        return pattern1e(reg_name)
            elif is_ro and is_hw:
                return pattern2(reg_name)
            elif not is_ro and is_hw:
                if reg_name == 'tdata1':
                    return pattern3t(reg_name)
                else:
                    return pattern3(reg_name)
            elif is_ro and not is_hw:
                return pattern5(reg_name)
        else: #struct
            if not is_ro and not is_hw:
                if not rdata_en:
                    return pattern1s(reg_name)
                else:
                    return pattern1es(reg_name)
            elif is_ro and is_hw:
                return pattern2s(reg_name)
            elif not is_ro and is_hw:
                return pattern3s(reg_name)
            elif is_ro and not is_hw:
                return pattern5s(reg_name)
    else: #roz
      return pattern4(reg_name)
    
    return ''

# Pattern 1: SRW, XLEN
def pattern1(reg_name):
    pattern_num = ' '*4  + '// Pattern 1: SRW, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name};\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name};\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = s_swdata;\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 1T: SRW, XLEN, tdata2
def pattern1t(reg_name):
    pattern_num = ' '*4  + '// Pattern 1T: SRW, XLEN, tdata2\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name}[r_tselect.idx];\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name}[r_tselect.idx];\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name}[r_tselect.idx] = s_swdata;\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 1E: SRW/RD-EN, XLEN
def pattern1e(reg_name):
    pattern_num = ' '*4  + '// Pattern 1E: SRW + RD-EN/ROZ, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
        read_str += ' '*8  + f'if (s_{reg_name}_en)\n'
        read_str += ' '*12 + f's_rdata.{reg_name} = r_{reg_name};\n'
        read_str += ' '*8  + 'else\n'
        read_str += ' '*12 + f's_rdata.{reg_name} = 0;\n'
    else:
        read_str += ' '*8  + f'if (s_{reg_name}_en)\n'
        read_str += ' '*12 + f's_rdata_{reg_name} = r_{reg_name};\n'
        read_str += ' '*8  + 'else\n'
        read_str += ' '*12 + f's_rdata_{reg_name} = 0;\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = s_swdata;\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 1S: SRW, STRUCT
def pattern1s(reg_name):
    pattern_num = ' '*4  + '// Pattern 1S: SRW, STRUCT\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = m_data_conv.struct_wdata_pack_{reg_name}(s_swdata);\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 1ES: SRW/RD-EN, STRUCT
def pattern1es(reg_name):
    pattern_num = ' '*4  + '// Pattern 1ES: SRW + RD-EN/ROZ, STRUCT\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
        read_str += ' '*8  + f'if (s_{reg_name}_en)\n'
        read_str += ' '*12 + f's_rdata.{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
        read_str += ' '*8  + 'else\n'
        read_str += ' '*12 + f's_rdata.{reg_name} = 0;\n'
    else:
        read_str += ' '*8  + f'if (s_{reg_name}_en)\n'
        read_str += ' '*12 + f's_rdata_{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
        read_str += ' '*8  + 'else\n'
        read_str += ' '*12 + f's_rdata_{reg_name} = 0;\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = m_data_conv.struct_wdata_pack_{reg_name}(s_swdata);\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close


# Pattern 2: SRO-HW, XLEN
def pattern2(reg_name):
    pattern_num = ' '*4  + '// Pattern 2: SRO-HW, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name};\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name};\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_hwr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = s_hwdata.{reg_name};\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 2S: SRO-HW, STRUCT
def pattern2s(reg_name):
    pattern_num = ' '*4  + '// Pattern 2S: SRO-HW, STRUCT\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_hwr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = m_data_conv.struct_wdata_pack_{reg_name}(s_hwdata.{reg_name});\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 3: SRW-HW, XLEN
def pattern3(reg_name):
    pattern_num = ' '*4  + '// Pattern 3: SRW-HW, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name};\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name};\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = s_swdata;\n'
    write_str  += ' '*8  + f'else if (s_hwr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = s_hwdata.{reg_name};\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 3T: SRW-HW, XLEN, tdata1
def pattern3t(reg_name):
    pattern_num = ' '*4  + '// Pattern 3T: SRW-HW, XLEN, tdata1\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name}[r_tselect.idx];\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name}[r_tselect.idx];\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name}[r_tselect.idx] = s_swdata;\n'
    write_str  += ' '*8  + f'else if (s_hwr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name}[s_hwidx_tdata1] = s_hwdata.{reg_name};\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 3S: SRW-HW, STRUCT
def pattern3s(reg_name):
    pattern_num = ' '*4  + '// Pattern 3S: SRW-HW, STRUCT\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    write_str  =  ' '*8  + '// Write\n'
    write_str  += ' '*8  + f'if (s_swr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = m_data_conv.struct_wdata_pack_{reg_name}(s_swdata);\n'
    write_str  += ' '*8  + f'else if (s_hwr.{reg_name})\n'
    write_str  += ' '*12 + f'r_{reg_name} = m_data_conv.struct_wdata_pack_{reg_name}(s_hwdata.{reg_name});\n'
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 4: ROZ, XLEN
def pattern4(reg_name):
    pattern_num = ' '*4  + '// Pattern 4: ROZ, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = 0;\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = 0;\n'
    write_str  =  ''
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 5: SRO-preset, XLEN
def pattern5(reg_name):
    pattern_num = ' '*4  + '// Pattern 5: SRO-Preset, XLEN\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = r_{reg_name};\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = r_{reg_name};\n'
    write_str  =  ''
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

# Pattern 5S: SRO-preset, STRUCT
def pattern5s(reg_name):
    pattern_num = ' '*4  + '// Pattern 5S: SRO-Preset, STRUCT\n'
    func_start =  ' '*4  + f'automatic void proc_{reg_name}(void) {{\n'
    read_str   =  ' '*8  + '// Read\n'
    if s_rdata_is_struct_in_pattern:
      read_str   += ' '*8  + f's_rdata.{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    else:
      read_str   += ' '*8  + f's_rdata_{reg_name} = m_data_conv.struct_rdata_unpack_{reg_name}(r_{reg_name});\n'
    write_str  =  ''
    func_close =  ' '*4  + '}\n\n'
    return pattern_num + func_start + read_str + write_str + func_close

#--------------------------------------------------------------------------------
# Search "AUTOGEN BEGIN/END" pairs in a file and insert stuff in between
#--------------------------------------------------------------------------------
def auto_insert(filename, autogen_dict):

    with open(filename, 'r') as read_file:
        lines = read_file.readlines()

    in_autogen_region = False
    insert_lines = []

    for line in lines:
        if not in_autogen_region: #outside 'autogen' region
            if line.find("AUTOGEN BEGIN") >= 0: #found AUTOGEN BEGIN
                convert_begin_line = line.replace('BEGIN', 'END').replace(' ','') #AUTOGEN BEGIN -> AUTOGEN END and remove spaces
                in_autogen_region = True
                insert_lines.append(line) #keep the line of 'AUTOGEN BEGIN'
                for key, value in autogen_dict.items():
                    if line.find(key) >= 0:
                        insert_lines.append(value)
            else: #not found AUTOGEN BEGIN
                insert_lines.append(line) #keep the line no change
        else: #in 'autogen' region
            if (line.replace(' ','') == convert_begin_line): #found matched 'autogen end' line with spaces removed
                in_autogen_region = False
                insert_lines.append(line) #keep the line of 'AUTOGEN END'

    with open(filename, 'w') as write_file:
        write_file.writelines(insert_lines)

#--------------------------------------------------------------------------------
# New CSR functions
#--------------------------------------------------------------------------------
def gen_final_str(final_str_comm, final_str64, final_str32, str64, str32):
    if (str64 == str32):
        final_str_comm += str64
    else:
        final_str64 += str64
        final_str32 += str32
    return final_str_comm, final_str64, final_str32

# -------- unpack struct to xlen-bit --------
def unpack_struct_to_xlen_middle(name, read_str):
    if read_str != '': 
        unpack_str =  ' '*8 + 'rdata = ' + read_str + '\n'
    else:
        unpack_str = ''
    return unpack_str
    
def unpack_struct_to_xlen_wrap(name, rd_str_middle):
    if rd_str_middle != '':
        unpack_str =   '//*************************\n'
        unpack_str += f'//  read {name}\n'
        unpack_str +=  '//*************************\n'
        unpack_str += ' '*4 + f'public always uint_<{{XLEN}}> struct_rdata_unpack_{name}(\n'
        unpack_str += ' '*8 + f'struct {name}_t {name})\n'
        unpack_str += ' '*4 + '{\n'
        unpack_str += ' '*8 + f'uint_<{{XLEN}}> rdata;\n'

        unpack_str += rd_str_middle

        unpack_str +=  ' '*8 + 'return rdata;\n'
        unpack_str += ' '*4 + '}\n\n'
    else:
        unpack_str = ''
    return unpack_str

# -------- pack xlen-bit to struct --------
def pack_xlen_to_struct_middle(name, write_str):
    if write_str != '': 
        pack_str =  write_str
    else:
        pack_str = ''
    return pack_str

def pack_xlen_to_struct_wrap(name, wr_str_middle):
    if wr_str_middle != '':
        pack_str =  '//*************************\n'
        pack_str += f'//  write {name}\n'
        pack_str +=  '//*************************\n'
        pack_str += ' '*4 + f'public struct {name}_t struct_wdata_pack_{name}(\n'
        pack_str += ' '*8 + f'uint_<{{XLEN}}> wdata)\n'
        pack_str += ' '*4 + '{\n'
        pack_str += ' '*8 + f'struct {name}_t {name};\n'

        pack_str += wr_str_middle

        pack_str += ' '*8 + f'return {name};\n'
        pack_str += ' '*4 + '}\n\n'
    else:
        pack_str = ''
    return pack_str

# def pack_xlen_to_struct(name, write_str64, write_str32, add_ifdef):
    
#     pack_str =  '\n'
#     pack_str += '//*************************\n'
#     pack_str += f'//  write {name}\n'
#     pack_str +=  '//*************************\n'
    
#     if write_str64 != '':     
#         str64 = ' '*4 + f'public struct {name}_t struct_wdata_pack_{name}(\n'
#         str64 += ' '*8 + f'uint_<{{XLEN}}> wdata)\n'
#         str64 += ' '*4 + '{\n'
#         str64 += ' '*8 + f'struct {name}_t {name};\n'
#         str64 += write_str64
#         str64 += ' '*8 + f'return {name};\n'
#         str64 += ' '*4 + '}\n'
#         if add_ifdef:
#             pack_str += hw_config_ifdef(str64, True)
#         else:
#             pack_str += str64
    
#     if write_str32 != '':     
#         str32 = ' '*4 + f'public struct {name}_32_t struct_wdata_pack_{name}(\n'
#         str32 += ' '*8 + f'uint_<{{XLEN}}> wdata)\n'
#         str32 += ' '*4 + '{\n'
#         str32 += ' '*8 + f'struct {name}_t {name};\n'
#         str32 += write_str32
#         str32 += ' '*8 + f'return {name};\n'
#         str32 += ' '*4 + '}\n'
#         if add_ifdef:
#             pack_str += hw_config_ifdef(str32, False)
#         else:
#             pack_str += str32
    
#     return pack_str

# -------- wrap string with #ifdef-#endif --------
def hw_config_ifdef(str_in, is_rv64):
    if str_in != '':
        if is_rv64:
            str_out = '#if (OPTION_XLEN == 64)\n'
            str_out += str_in
            str_out += '#endif //(OPTION_XLEN == 64)\n'
        else:
            str_out = '#if (OPTION_XLEN == 32)\n'
            str_out += str_in
            str_out += '#endif //(OPTION_XLEN == 32)\n'
    else:
       str_out = ''
    return str_out

# -------- read data mux --------
def rdata_mux_case(name):
    a = ' '*12 + f'case CSR_{name.upper()}:'
    str_out = f'{a:<44}'
    if s_rdata_is_struct_in_pattern:
      a = f's_rdata = s_rdata.{name};'
    else:
      a = f's_rdata = s_rdata_{name};'
    str_out += f'{a:<36}'
    str_out += 'break;\n'
    return str_out

# -------- read error mux --------
def rerror_mux_case(name, en_acc, dis_act):
    a = ' '*12 + f'case CSR_{name.upper()}:'
    str_out = f'{a:<44}'
    if en_acc not in ['', '-'] and dis_act == '-':
        a = f's_access_err = ~s_{name}_en;'
    else:
        a = ''
    str_out += f'{a:<36}'
    str_out += 'break;\n'
    return str_out

# -------- read only mux --------
def ronly_mux_case(name, is_ro):
    a = ' '*12 + f'case CSR_{name.upper()}:'
    str_out = f'{a:<44}'
    if is_ro:
        a = f's_read_only = 1;'
    else:
        a = ''
    str_out += f'{a:<36}'
    str_out += 'break;\n'
    return str_out

# -------- write decoder --------
def write_dec_case(name):
    a = ' '*16 + f'case CSR_{name.upper()}:'
    str_out = f'{a:<50}'
    a = f's_swr.{name} = 1;'
    str_out += f'{a:<36}'
    str_out += 'break;\n'
    return str_out

#--------------------------------------------------------------------------------
# Original CSR functions
#--------------------------------------------------------------------------------
# CSR length table
dict_reg_len64 = {"XLEN":64, "SXLEN":64, "MXLEN":64, "DXLEN":64, "XLEN*TRIGGERS":256, "clog2(VLEN)":7, "TRIGGERS":4}
dict_reg_len32 = {"XLEN":32, "SXLEN":32, "MXLEN":32, "DXLEN":32, "XLEN*TRIGGERS":128, "clog2(VLEN)":7, "TRIGGERS":4}

#Example: name_str='NAME<3-6>', addr_str='0x303-0x306'
def parse_name(name_str, addr_str):
  name_list=[]
  addr_list=[]
  name_split=re.split('[<>-]', name_str)
  addr_split=re.split('[x-]', addr_str)
  j=0
  for i in range(int(name_split[1]), int(name_split[2])+1):
    if (name_split[3] == ''):
      name=f'{name_split[0]}{i}'
    else:
      name=f'{name_split[0]}{i}{name_split[3]}'
    addr=hex(int(addr_split[1], 16)+j)
    j += 1
    name_list.append(name)
    addr_list.append(addr)
  return name_list, addr_list


#marchid reset value
def marchid_reset():
  reset_value = """{5, //obilix
                                                                  #if (OPTION_XLEN == 64)
                                                                      #ifdef OPTION_HAS_VM
                                                                                     5, //arch: rv64/VM (A71)
                                                                      #else
                                                                                     4, //arch: rv64/noVM (H71)
                                                                      #endif
                                                                  #else
                                                                                     0, //arch: rv32/noVM (L71)
                                                                  #endif
                                                                                     0, //fusa
                                                                  #ifdef OPTION_HAS_CHERI
                                                                                     1, //cheri on
                                                                  #else
                                                                                     0, //cheri off
                                                                  #endif
                                                                  #ifdef OPTION_EXTENSION_V
                                                                      #if (OPTION_VLEN == 128)
                                                                                     1, //vector128
                                                                      #else
                                                                                     2, //vector256
                                                                      #endif
                                                                  #else
                                                                                     0, //no vector
                                                                  #endif
                                                                                     1}"""

  return reset_value;




# ------------ dynamic enable input declare ------------
def gen_rd_enable(name, enable):
  if (enable):
    rd_en = ' '*8
    if name.find('<') != -1:#Name contains '<'
      name_split=re.split('[<>-]', name)
      a = f"uint{(int(name_split[2])-int(name_split[1])+1)}"
      rd_en += f"{a:<20}"
      rd_en += f"{name_split[0]}_{name_split[2]}_{name_split[1]}_en,\n"
    else:
      a = "uint1"
      rd_en += f"{a:<20}"
      rd_en += f"{name}_en,\n"
  else:
    rd_en = ''
  return rd_en

# ------------ structure declare, io & internal wire ------------
def gen_struct(struct_name, header, row, first_item, is_rv64):
  is_ro = (row[header.index('Field Type')] == 'RO')
  if is_rv64:
    proj_ro = (row[header.index('A71/H71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
  else:
    proj_ro = (row[header.index('L71')] == 'RO' or row[header.index('L71')] == 'ROZ')
  
  def gen_func_io(reg_name, field_name, field_width, updt_by_hw, first_item, is_rv64):
    if updt_by_hw not in ['', '-']:
      #generate write enables
      if (first_item[0]):
        io_we = ''
        first_item[0] = False
      else:
        io_we = ',\n'
      io_we += ' '*8
      a = "uint1"
      io_we += f"{a:<20}"
      io_we += ' '*(28-len(io_we))
      io_we += f"{reg_name}_{field_name.lower()}_we,\n"

      #generate write data
      io_we += ' '*8 
      a = f"uint{field_width}"
      io_we += f"{a:<20}"
      io_we += f"{reg_name}_{field_name.lower()}_val"
    else:
      io_we = ''
    return io_we

  def gen_func_connect(reg_name, field_name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      #generate write enables
      conn_we = ' '*8
      conn_we += f"{reg_name}_{field_name.lower()}_we,\n"

      #generate write data
      conn_we += ' '*8 
      conn_we += f"{reg_name}_{field_name.lower()}_val,\n"
    else:
      conn_we = ''
    return conn_we

  def gen_func_wire(reg_name, field_name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      wire_we = ' '*8
      a = "uint1"
      wire_we += f"{a:<20}"
      wire_we += f"sw_{reg_name}_{field_name.lower()}_we;\n" 
    else:
      wire_we = ''
    return wire_we

  def gen_func_wire_init(reg_name, field_name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      wire_we_clr = ' '*8
      a = f"sw_{reg_name}_{field_name.lower()}_we"
      wire_we_clr += f"{a:<24}"
      wire_we_clr += "= 0;\n" 
    else:
      wire_we_clr = ''
    return wire_we_clr

  # Use if/else (connect write enables to FF.WE pin) instead of A = B ? C : D (all logic connects to FF.D pin, FF.WE=1) 
  def gen_func_updt(reg_name, field_name, field_width, updt_by_hw, bit_offset):
    if updt_by_hw not in ['', '-']:
        updt_str = ' '*8
        a = f"if (sw_{reg_name}_{field_name.lower()}_we"
        updt_str += f"{a:<24}"
        updt_str += ") { "
        a = f"r_{reg_name}.{field_name.lower()}"
        updt_str += f"{a:<20}"
        a = f"= wdata[{bit_offset}..{bit_offset+1-field_width}];"
        updt_str += f"{a:<24}"
        updt_str += f"}} else if ("
        a = f"{reg_name}_{field_name.lower()}_we"
        updt_str += f"{a:<20}"
        a = f") {{ r_{reg_name}.{field_name.lower()}"
        updt_str += f"{a:<24}"
        a = f" = {reg_name}_{field_name.lower()}_val;"
        updt_str += f"{a:<24}"
        updt_str += f"}}\n"

    else:
      updt_str = ''
    return updt_str

  def gen_updt_assert(reg_name, field_name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      updt_assert = ' '*8
      updt_assert += f"if (sw_{reg_name}_{field_name.lower()}_we & {reg_name}_{field_name.lower()}_we)\n"
      updt_assert += ' '*8 + f"{{\n"
      updt_assert += ' '*12 + f'codal_assert(false, "Attempts to write {reg_name}_{field_name.lower()} during CSR write!");\n'
      # updt_assert += ' '*12 + f'codal_warning(2, "Attempts to write {reg_name}_{field_name.lower()} during CSR write!");\n'
      updt_assert += ' '*8 + f"}}\n"
    else:
      updt_assert = ''
    return updt_assert

  def gen_func_we(reg_name, field_name, field_width, updt_by_hw, bit_offset, is_ro):
    if not struct_wr_middle_only:
        if updt_by_hw not in ['', '-']: #generate write enable
          if is_ro or proj_ro:
            a = f"sw_{reg_name.lower()}_{field_name.lower()}_we = 0;"
          else:
            a = f"sw_{reg_name.lower()}_{field_name.lower()}_we = 1;"
          we_str = f"{a:<64}\n"
          we_str += ' '*48
        else: #update register if csr instruction is the only source of write
          if is_ro or proj_ro:
            we_str = ''
          else:
            a = f"r_{reg_name.lower()}.{field_name.lower()} = wdata[{bit_offset}..{bit_offset+1-field_width}];"
            we_str = f"{a:<64}\n"
            we_str += ' '*48
    else:
        we_str = ' '*8
        a = f"{reg_name}.{field_name.lower()}"
        we_str += f"{a:<22}"
        we_str += f"= wdata[{bit_offset}..{bit_offset+1-field_width}];\n"
    return we_str

  def gen_func_we_clr(reg_name, field_name, updt_by_hw):
    if updt_by_hw not in ['', '-']: #generate write enable
      we_clr_str = f"sw_{reg_name.lower()}_{field_name.lower()}_we = 0;\n"
    else: #update register if csr instruction is the only source of write
      we_clr_str = ''
    return we_clr_str

  def gen_func_rd_start(reg_name, acc_en, is_ro):
    rd_mux_start = ' '*16
    a = f"case CSR_{reg_name.upper()}: "
    rd_mux_start += f"{a:<24}"
    if is_ro: #proj_ro doesn't assert read_only error
      rd_mux_start += "read_only = 1;\n"
      rd_mux_start += " "*40
    if acc_en not in ['', '-']:
      rd_mux_start += "if" + f"({reg_name}_en) {{\n"
      rd_mux_start += " "*44 + "rdata = "
    else:
      rd_mux_start += "rdata = "
    return rd_mux_start
  
  struct_str = f"""
struct {struct_name}_t
{{
"""
    
  struct_io = ""
  struct_conn = ""
  struct_wire = ""
  struct_wire_init = ""
  struct_updt = ""
  struct_updt_assert = ""
  struct_we = ""
  struct_we_start = ' '*16
  a = f"case CSR_{struct_name.upper()}: "
  struct_we_start += f"{a:<32}"
  struct_we_middle = ""
  struct_we_end = "break;\n"
  struct_we_clr = ""
  struct_rd = ""
  struct_rd_start = gen_func_rd_start(struct_name, row[header.index('Access Enable')], is_ro)
  struct_rd_middle = ""
  struct_rd_end = ""
  if row[header.index('Access Enable')] not in ['', '-'] and row[header.index('Disable Action')] == 'ROZ':
    struct_rd_end += """
                                        }
                                        else {
"""
    if is_rv64:
      struct_rd_end += ' '*44 + f"rdata = {row[header.index('Reset Impl A')]};\n"
    else:
      struct_rd_end += ' '*44 + f"rdata = {row[header.index('Reset Impl L')]};\n"
    struct_rd_end += """
                                        }"""
  else:
    if row[header.index('Access Enable')] not in ['', '-'] and row[header.index('Disable Action')] == '-':
      struct_rd_end += """
                                        }
                                        else {
                                            read_err = 1; //Access is disabled. Register is reserved.
                                        }"""      
  a = " "
  struct_rd_end += f"\n{a:<40}break;\n" 

  if is_rv64:
    start_ptr = header.index('bit00')
  else:
    start_ptr = header.index('L00')
  reg_len=row[header.index('Width')]
  if is_rv64:
    if reg_len in dict_reg_len64:
      end_ptr = start_ptr - dict_reg_len64[reg_len] + 1
    else:
      end_ptr = start_ptr - int(reg_len) + 1
  else:
    if reg_len in dict_reg_len32:
      end_ptr = start_ptr - dict_reg_len32[reg_len] + 1
    else:
      end_ptr = start_ptr - int(reg_len) + 1    

  curr_val = row[start_ptr]
  curr_len = 1
  j = 0
  first_element = 1

  for i in range(start_ptr, end_ptr-1, -1): #loop from right to left
    bit_offset = start_ptr - i
    if i != start_ptr and row[i] != row[i+1]:
      first_element = 0 #clear it when pointer moves to the 2nd field
    if i != end_ptr and row[i] == row[i-1]:
      curr_len += 1
    else:
      if curr_val.lower() != 'wpri':
        struct_str += ' '*4
        a = f"uint{curr_len}"
        struct_str += f"{a:<16}"
      if curr_val.lower() == 'wpri':
        if wpri_in_struct:
            struct_str += ' '*4
            a = f"uint{curr_len}"
            struct_str += f"{a:<16}"
            struct_str += f"{curr_val.lower()}_{j};\n"
        if first_element == 1:
          struct_rd_middle += f"(uint{curr_len})0;"
        else:
          struct_rd_middle = f"(uint{curr_len})0 :: " + struct_rd_middle 
        j += 1
      else:
        
        struct_str += f"{curr_val.lower()};\n"
        struct_io += gen_func_io(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], first_item, is_rv64)
        struct_conn += gen_func_connect(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_wire += gen_func_wire(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_wire_init += gen_func_wire_init(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_updt += gen_func_updt(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], bit_offset)
        struct_updt_assert += gen_updt_assert(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        if first_element == 1:
          struct_rd_middle += f"{struct_name.lower()}.{curr_val.lower()};"
        else:
          struct_rd_middle = f"{struct_name.lower()}.{curr_val.lower()} :: " + struct_rd_middle
        struct_we_middle += gen_func_we(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], bit_offset, is_ro)
        struct_we_clr += gen_func_we_clr(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
      
      #print("start_ptr = %d, end_ptr = %d, bit_ofst = %d, curr_ptr(i) = %d, curr_val = %s, curr_len = %d, field name = %s, first_element: %d" % (start_ptr, end_ptr, bit_offset, i, curr_val, curr_len, row[i], first_element))

      if i != end_ptr:
        curr_val = row[i-1] #move to the next bit
        curr_len = 1

  #ROZ registers
  if is_rv64:
    struct_rd_zero = row[header.index('Reset Impl A')]
    if (row[header.index('A71/H71')] == 'ROZ'): 
      if not struct_rd_middle_only:
        struct_rd += struct_rd_start + struct_rd_zero + struct_rd_end
      else:
        struct_rd += struct_rd_zero
    else: 
      if not struct_rd_middle_only:
        struct_rd += struct_rd_start + struct_rd_middle + struct_rd_end
      else:
        struct_rd += struct_rd_middle
  else:
    struct_rd_zero = row[header.index('Reset Impl L')]
    if (row[header.index('L71')] == 'ROZ'): 
      if not struct_rd_middle:
        struct_rd += struct_rd_start + struct_rd_zero + struct_rd_end
      else:
        struct_rd += struct_rd_zero
    else: 
      if not struct_rd_middle:
        struct_rd += struct_rd_start + struct_rd_middle + struct_rd_end
      else:
        struct_rd += struct_rd_middle

  if not struct_wr_middle_only:
    struct_we += struct_we_start + struct_we_middle + struct_we_end
  else:
    struct_we = struct_we_middle
    

  #close struct statement
  struct_str += "};\n\n"

  return struct_str, struct_io, struct_conn, struct_wire, struct_wire_init, struct_updt, struct_updt_assert, struct_rd, struct_we, struct_we_clr

# ------------ registers, io & wire declaration ------------
def gen_reg(width, name, addr, updt_by_hw, reset, first_item, prj_roz, is_rv64):

  def gen_func_io(name, width, updt_by_hw, first_item, is_rv64):
    if updt_by_hw not in ['', '-']:
      #generate write enables
      if (first_item[0]):
        io_we = ''
        first_item[0] = False
      else:
        io_we = ',\n'
      io_we += ' '*8
      a = "uint1"
      io_we += f"{a:<20}"
      io_we += f"{name}_we,\n"

      #generate data signals
      io_we += ' '*8
      
      if name != 'tdata1':
        if is_rv64:
          if width in dict_reg_len64:
            a = f"uint_<{{{width}}}>"
          else:
            a = f"uint{width}"
        else:
          if width in dict_reg_len32:
            a = f"uint_<{{{width}}}>"
          else:
            a = f"uint{width}"
        io_we += f"{a:<20}"
        io_we += f"{name}_val"
      else:
        if is_rv64:
          a = f"uint{dict_reg_len64['XLEN']}"
        else:
          a = f"uint{dict_reg_len32['XLEN']}"
        io_we += f"{a:<20}"
        io_we += f"{name}_val,\n"
        
        io_we += ' '*8
        if is_rv64:
          a = f"uint{int(math.log2(dict_reg_len64['TRIGGERS']))}"
        else:
          a = f"uint{int(math.log2(dict_reg_len32['TRIGGERS']))}"
        io_we += f"{a:<20}"
        io_we += f"{name}_idx"
    else:
      io_we = ''
    return io_we

  def gen_func_connect(name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      #generate write enables
      conn_we = ' '*8
      conn_we += f"{name}_we,\n"

      #generate data signals
      conn_we += ' '*8
      conn_we += f"{name}_val,\n"
    else:
      conn_we = ''
    return conn_we

  def gen_func_wire(name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      wire_we = ' '*8
      wire_we += "uint1"
      wire_we += ' '*(28-len(wire_we))
      wire_we += f"sw_{name}_we;\n"
    else:
      wire_we = ''
    return wire_we

  def gen_func_wire_init(name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      wire_we_clr = ' '*8
      a = f"sw_{name}_we"
      wire_we_clr += f"{a:<24}"
      wire_we_clr += "= 0;\n"
    else:
      wire_we_clr = ''
    return wire_we_clr

  # Use if/else (connect write enables to FF.WE pin) instead of A = B ? C : D (all logic connects to FF.D pin, FF.WE=1) 
  def gen_func_updt(name, width, updt_by_hw, is_rv64):
    if updt_by_hw not in ['', '-']:
      updt_str = ' '*8
      a = f"if (sw_{name}_we"
      updt_str += f"{a:<24}"
      updt_str += ") { "
      a = f"r_{name}"
      updt_str += f"{a:<20}"
      if is_rv64:
        if width in dict_reg_len64:
          a = f"= wdata[{dict_reg_len64[width]-1}..0];"
        else:
          a = f"= wdata[{int(width)-1}..0];"
      else:
        if width in dict_reg_len32:
          a = f"= wdata[{dict_reg_len32[width]-1}..0];"
        else:
          a = f"= wdata[{int(width)-1}..0];"
      updt_str += f"{a:<24}"
      updt_str += f"}} else if ("
      a = f"{name}_we"
      updt_str += f"{a:<20}"
      a = f") {{ r_{name}"
      updt_str += f"{a:<24}"
      a = f" = {name}_val;"
      updt_str += f"{a:<24}"
      updt_str += f"}}\n"
    else:
      updt_str = ''
    return updt_str

  def gen_func_updt_tdata1(name, width, updt_by_hw, is_rv64):
    if updt_by_hw not in ['', '-']:
      updt_str = ' '*8
      a = f"if (sw_{name}_we"
      updt_str += f"{a:<24}"
      updt_str += ") { "
      a = f"r_{name}[r_tselect.idx]"
      updt_str += f"{a:<20}"
      if is_rv64:
        if width in dict_reg_len64:
          a = f"= wdata[{int(dict_reg_len64.get('XLEN', 0))-1}..0];" #TODO: temporary solution
        else:
          a = f"= wdata[{int(width)-1}..0];"
      else:
        if width in dict_reg_len32:
          a = f"= wdata[{int(dict_reg_len32.get('XLEN', 0))-1}..0];" #TODO: temporary solution
        else:
          a = f"= wdata[{int(width)-1}..0];"
      updt_str += f"{a:<24}"
      updt_str += f"}} else if ("
      a = f"{name}_we"
      updt_str += f"{a:<20}"
      a = f") {{ r_{name}[{name}_idx]"
      updt_str += f"{a:<24}"
      a = f" = {name}_val;"
      updt_str += f"{a:<24}"
      updt_str += f"}}\n"
    else:
      updt_str = ''
    return updt_str       

  def gen_updt_assert(name, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      updt_assert = ' '*8
      updt_assert += f"if (sw_{name}_we & {name}_we)\n"
      updt_assert += ' '*8 + f"{{\n"
      updt_assert += ' '*12 + f'codal_assert(false, "Attempts to write {name} during CSR write!");\n'
      # updt_assert += ' '*12 + f'codal_warning(2, "Attempts to write {name} during CSR write!");\n'
      updt_assert += ' '*8 + f"}}\n"
    else:
      updt_assert = ''
    return updt_assert

  def finish_reg_str(reg_str, split, reset, name, is_rv64):
    if split == 1:
      a = f"r_{name}[{width_split[1]}]"
      reg_str = f"{a:<20}"
    else:
      a = f"r_{name}"
      reg_str = f"{a:<20}"
    
    if (name != 'marchid'):
      if reset == '-':
        a = f"{{ reset = false; }}; "
        reg_str += f"{a:<72}"
        reg_str += f"//{addr}\n"
      else:
        a = f"{{ default = {reset}; }}; "
        reg_str += f"{a:<72}"
        reg_str += f"//{addr}\n"
    else: #reset marchid
        a = f"{{ default = {marchid_reset()}; }}; "
        reg_str += f"{a:<72}"
        reg_str += f"//{addr}\n"
    return reg_str

  if not prj_roz:
    reg_str = ' '*4 #align first element
    if is_rv64:
      if width in dict_reg_len64:
        if width.find('*') != -1: 
          width_split = re.split('[*]', width) #split XLEN*TRIGGERS to [XLEN, TRIGGERS]
          a = f"register uint_<{{{width_split[0]}}}>"
          reg_str += f"{a:<48}"
          reg_str += finish_reg_str(reg_str, 1, reset, name, is_rv64)
        else:
          a = f"register uint_<{{{width}}}>"
          reg_str += f"{a:<48}"
          reg_str += finish_reg_str(reg_str, 0, reset, name, is_rv64)
      else:
        a = f"register uint{width}"
        reg_str += f"{a:<48}"
        reg_str += finish_reg_str(reg_str, 0, reset, name, is_rv64)
    else:
      if width in dict_reg_len32:
        if width.find('*') != -1: 
          width_split = re.split('[*]', width) #split XLEN*TRIGGERS to [XLEN, TRIGGERS]
          a = f"register uint_<{{{width_split[0]}}}>"
          reg_str += f"{a:<48}"
          reg_str += finish_reg_str(reg_str, 1, reset, name, is_rv64)
        else:
          a = f"register uint_<{{{width}}}>"
          reg_str += f"{a:<48}"
          reg_str += finish_reg_str(reg_str, 0, reset, name, is_rv64)
      else:
        a = f"register uint{width}"
        reg_str += f"{a:<48}"
        reg_str += finish_reg_str(reg_str, 0, reset, name, is_rv64)
  else:
    reg_str = ''
    
  #return values
  reg_io = gen_func_io(name, width, updt_by_hw, first_item, is_rv64)
  reg_conn = gen_func_connect(name, updt_by_hw)
  reg_wire = gen_func_wire(name, updt_by_hw)
  reg_wire_init = gen_func_wire_init(name, updt_by_hw)
  if name == 'tdata1':
    reg_updt = gen_func_updt_tdata1(name, width, updt_by_hw, is_rv64)
  else:
    reg_updt = gen_func_updt(name, width, updt_by_hw, is_rv64)
  reg_updt_assert = gen_updt_assert(name, updt_by_hw)

  return reg_str, reg_io, reg_conn, reg_wire, reg_wire_init, reg_updt, reg_updt_assert

def gen_reg_struct(name, addr, reset, prj_roz):
  if not prj_roz:
    struct_str =  ' '*4
    a = f"register struct {name}_t"
    struct_str += f"{a:<48}"
    a = f"r_{name}"
    struct_str += f"{a:<20}"
  
    if (name != 'marchid'):
      if reset == '-':
        a = f"{{ reset = false; }}; "
        struct_str += f"{a:<72}"
        struct_str += f"//{addr}\n" 
      else:   
        a = f"{{ default = {reset}; }}; "
        struct_str += f"{a:<72}"
        struct_str += f"//{addr}\n"
    else: #marchid
      a = f"{{ default = {marchid_reset()}; }}; "
      struct_str += f"{a:<72}"
      struct_str += f"//{addr}\n"
  else:
    struct_str = ''
  return struct_str

# ------------ defines ------------

# ------------ read MUX (for unstructured registers) ------------
def gen_rd_mux(is_list, bit_index, orig_name, name, width, en_acc, dis_act, is_ro, prj_roz, is_rv64):#if orig_name contains <>, is_list=True, split it to get enable names
  rd_mux = ' '*16
  a = f"case CSR_{name.upper()}: "
  rd_mux += f"{a:<24}"
  if is_ro: #proj_ro doesn't assert read_only
    rd_mux += "read_only = 1;\n"
    rd_mux += " "*40
  if (en_acc not in ['','-']):
    if (is_list):#Name contains '<'
      name_split=re.split('[<>-]', orig_name)
      rd_mux += "if" + f"({name_split[0]}_{name_split[2]}_{name_split[1]}_en[{bit_index}]) {{\n"
    else:
      rd_mux += "if" + f"({name}_en) {{\n"

    a = " "
    rd_mux += f"{a:<44}"
  
  if (en_acc == 'ROZ' or prj_roz):
    a = "rdata = 0;"
  else:
    if width in dict_reg_len64: #no need to check dict_reg_len32, same result
      if width.find('*') != -1: 
        a = f"rdata = r_{name.lower()}[r_tselect.idx];"#temporary solution
      else:
        a = f"rdata = r_{name.lower()};"
    else:
      if is_rv64 & dict_reg_len64["XLEN"] == 64:
        if int(width, base=0) == 64:
          a = f"rdata = r_{name.lower()};"
        else:
          a = f"rdata = (uint{64-int(width, base=0)})0 :: r_{name.lower()};"
      if not is_rv64 & dict_reg_len32["XLEN"] == 32:
        if int(width, base=0) == 32:
          a = f"rdata = r_{name.lower()};"
        else:
          a = f"rdata = (uint{32-int(width, base=0)})0 :: r_{name.lower()};" 
  

  if (dis_act == '-'):
    rd_mux += a + """
                                        }
                                        else {
                                            read_err = 1;
                                        }                                                               """
  else:
    if (dis_act == 'ROZ'):
      rd_mux += a + """
                                        }
                                        else {
                                            rdata = 0;
                                        }                                                               """
    else:
      rd_mux += f"{a:<64}"
  rd_mux += "break;\n" 
  return rd_mux

# ------------ write enable ------------
def gen_wena(name, updt_by_hw, width, is_ro, prj_ro, is_rv64): 
  wr_ena = ' '*16
  a = f"case CSR_{name.upper()}: "
  wr_ena += f"{a:<32}"
  
  if updt_by_hw not in ['', '-']: #generate write enable
    if is_ro or prj_ro:
      a = f"sw_{name.lower()}_we = 0;"
    else:
      a = f"sw_{name.lower()}_we = 1;"
  else: #update register if csr instruction is the only source of write
    if is_ro or prj_ro:
      a = ''
    else:
      if is_rv64:
        if width in dict_reg_len64:
          if width.find('*') != -1:
            a = f"r_{name.lower()}[r_tselect.idx] = wdata;" #for unstructured tdata1/2, temporary solution
          else:
            a = f"r_{name.lower()} = wdata;" #for unstructured registers
        else:
          a = f"r_{name.lower()} = wdata[{int(width, base=0)-1}..0];" #for unstructured registers
      else:
        if width in dict_reg_len32:
          if width.find('*') != -1:
            a = f"r_{name.lower()}[r_tselect.idx] = wdata;" #for unstructured tdata1/2, temporary solution
          else:
            a = f"r_{name.lower()} = wdata;" #for unstructured registers
        else:
          a = f"r_{name.lower()} = wdata[{int(width, base=0)-1}..0];" #for unstructured registers
  wr_ena += f"{a:<64}"
  wr_ena += "break;\n" 
  return wr_ena

def gen_we_clr(name, updt_by_hw): 
  wr_clr = ' '*16
  if updt_by_hw not in ['', '-']: #generate write enable
    wr_clr = f"sw_{name.lower()}_we = 0;\n"
  else:
    wr_clr = ''
  return wr_clr

# ------------ register update ------------
# def gen_updt_reg(name, updt_by_hw):
  
#   if updt_by_hw not in ['', '-']: #generate register write statement
#     updt_str = ' '*8
#     updt_str += f"r_{name.lower()} = "
#   else:
#     updt_reg_str = ''
#   return updt_reg_str

# ------------ end code ------------
def gen_end_code():
  end_str="""

};
  """
  return end_str


def longest_common_leader(str1, str2):    # 示例字符串
    def isdigit(string):
        return re.match("^[0-9]+$", string)

    # 正则表达式模式
    still_common = True
    pattern = r'(\d+|\D+)'
    # 使用re.findall()方法获取匹配的子串
    lineList1  = str1.split('\n')
    lineList2 = str2.split('\n')

    idx = min(len(lineList1), len(lineList2))
    common_header = ''
    for i in range(idx):
        if lineList1[i] == lineList2[i]:
            common_header += lineList1[i] + '\n'
        else:
            # Find a line that not equal:
            #   if the only unequal part of these two lines are digits and the value has a different of 32,
            #   we still think them as equal ,but replace the digits with the expression of XLEN.
            subList1 = re.findall(pattern, lineList1[i])
            subList2 = re.findall(pattern, lineList2[i])
            if len(subList1) != len(subList2):
                still_common = False
                idx = i
                break


            # Create a temp common line for this line.  Return it if successful, otherwise drop it.
            common_line = ''
            for j in range(len(subList1)):
                if subList1[j] == subList2[j]:
                    common_line += subList1[j]
                    continue
                else:
                    if isdigit(subList1[j]) and isdigit(subList2[j]):
                        int1 = int(subList1[j])
                        int2 = int(subList2[j])
                        if (abs(int1 - int2) == 32):
                            varExpressiong = f'XLEN-{64 - max(int1, int2)}'
                            if (subList1[j-1].endswith('uint')  or subList1[j-1].endswith('int') ):
                                common_line += '_<{' + varExpressiong +' }'
                            else:
                                common_line += varExpressiong
                        else:
                            still_common = False
                            break
                    else:
                        still_common = False
                        break
            if  still_common:
                common_header += common_line + '\n'
            else:
                idx = i
                break

    tail1 = '\n'.join(lineList1[idx:])
    tail2 = '\n'.join(lineList2[idx:])
    return common_header, tail1, tail2


def gen_strings_to_append(rowx_name, header, row, first_item, gen64, gen32):
    if gen64:
        rowx_struct64, _, _, _, _, _, _, rowx_struct_rd64, rowx_struct_wr64, _ = \
            gen_struct(rowx_name, header, row, first_item, True)
    else:
        rowx_struct64 = ""
        rowx_struct_rd64 = ""
        rowx_struct_wr64 = ""
    if gen32:
        rowx_struct32, _, _, _, _, _, _, rowx_struct_rd32, rowx_struct_wr32, _ = \
            gen_struct(rowx_name, header, row, first_item, False)
    else:
        rowx_struct32 = ""
        rowx_struct_rd32 = ""
        rowx_struct_wr32 = ""

    strct_comm, struct64, struct32 = longest_common_leader(rowx_struct64, rowx_struct32)
    unpack_comm, unpack64, unpack32 = longest_common_leader(rowx_struct_rd64, rowx_struct_rd32)
    return strct_comm, struct64, struct32, unpack_comm, unpack64, unpack32


if __name__ == '__main__':
    # Test longest_common_leader

    str1 = """    public always uint_<{XLEN}> struct_rdata_unpack_medeleg(
        struct medeleg_t medeleg)
    {
        uint_<{XLEN}> rdata;
        rdata = (uint48)0 :: medeleg.st_pg_fault :: (uint1)0 :: medeleg.ld_pg_fault :: medeleg.inst_pg_fault :: medeleg.ecall_m :: (uint1)0 :: medeleg.ecall_s :: medeleg.ecall_u :: medeleg.st_fault :: medeleg.st_mis_algn :: medeleg.ld_fault :: medeleg.ld_mis_algn :: medeleg.breakpoint :: medeleg.illegal_inst :: medeleg.pc_fault :: medeleg.pc_mis_algn;
        return rdata;
    }"""

    str2 = """    public always uint_<{XLEN}> struct_rdata_unpack_medeleg(
        struct medeleg_t medeleg)
    {
        uint_<{XLEN}> rdata;
        rdata = (uint16)0 :: medeleg.st_pg_fault :: (uint1)0 :: medeleg.ld_pg_fault :: medeleg.inst_pg_fault :: medeleg.ecall_m :: (uint1)0 :: medeleg.ecall_s :: medeleg.ecall_u :: medeleg.st_fault :: medeleg.st_mis_algn :: medeleg.ld_fault :: medeleg.ld_mis_algn :: medeleg.breakpoint :: medeleg.illegal_inst :: medeleg.pc_fault :: medeleg.pc_mis_algn;
        return rdata;
    }"""
    str3 = """line 1
    line2
    line[63..60]
    line: uint0
    line4 Diff1
    line5"""

    str4 = """line 1
    line2
    line[31..28]
    line: uint32
    line4 Diff2
    """


    c, t1, t2 = longest_common_leader(str1, str2)

    print('c12',c)
    print('1', t1)
    print('2', t2)

    print('*******************')
    c, t1, t2 = longest_common_leader(str3, str4)

    print('c34',c)
    print('3', t1)
    print('4', t2)