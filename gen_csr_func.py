#!/usr/bin/env python3

import os, csv, sys
import re
import math
import pdb
#pdb.set_trace()

# CSR length table
dict_reg_len = {"XLEN":64, "SXLEN":64, "MXLEN":64, "DXLEN":64, "XLEN*TRIGGERS":256, "clog2(VLEN)":7, "TRIGGERS":4}

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
def gen_struct(struct_name, header, row, first_item):
  is_ro = (row[header.index('Field Type')] == 'RO')
  if dict_reg_len["XLEN"] == 64:
    proj_ro = (row[header.index('A71/H71')] == 'RO' or row[header.index('A71/H71')] == 'ROZ')
  else:
    proj_ro = (row[header.index('L71')] == 'RO' or row[header.index('L71')] == 'ROZ')
  
  def gen_func_io(reg_name, field_name, field_width, updt_by_hw, first_item):
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

  # def gen_func_updt(reg_name, field_name, field_width, updt_by_hw, bit_offset):
  #   if updt_by_hw not in ['', '-']:
  #     updt_str = ' '*8
  #     a = f"r_{reg_name}.{field_name.lower()} "
  #     updt_str += f"{a:<20}"
  #     a = f"= sw_{reg_name}_{field_name.lower()}_we"
  #     updt_str += f"{a:<24}"
  #     a = f"? wdata[{bit_offset}..{bit_offset+1-field_width}]"
  #     updt_str += f"{a:<24}"
  #     a = f": (r_{reg_name}_{field_name.lower()}_we" 
  #     updt_str += f"{a:<24}"
  #     a = f"? r_{reg_name}_{field_name.lower()}_val"
  #     updt_str += f"{a:<24}"
  #     updt_str += f": r_{reg_name}.{field_name.lower()});\n"
  #   else:
  #     updt_str = ''
  #   return updt_str

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

  if dict_reg_len["XLEN"] == 64:
    struct_str = f"""
struct {struct_name}_t
    {{
"""
  else:
    struct_str = f"""
struct {struct_name}_32_t
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
    if dict_reg_len["XLEN"] == 64:
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

  if dict_reg_len["XLEN"] == 64:
    start_ptr = header.index('bit00')
  else:
    start_ptr = header.index('L00')
  reg_len=row[header.index('Width')]
  if reg_len in dict_reg_len:
    end_ptr = start_ptr - dict_reg_len[reg_len] + 1
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
        struct_str += ' '*12
        a = f"uint{curr_len}"
        struct_str += f"{a:<16}"
      if curr_val.lower() == 'wpri':
      #  struct_str += f"{curr_val.lower()}_{j};\n" #Don't show reserved bits in Struct declaration
        if first_element == 1:
          struct_rd_middle += f"(uint{curr_len})0;"
        else:
          struct_rd_middle = f"(uint{curr_len})0 :: " + struct_rd_middle 
        j += 1
      else:
        
        struct_str += f"{curr_val.lower()};\n"
        struct_io += gen_func_io(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], first_item)
        struct_conn += gen_func_connect(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_wire += gen_func_wire(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_wire_init += gen_func_wire_init(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        struct_updt += gen_func_updt(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], bit_offset)
        struct_updt_assert += gen_updt_assert(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
        if first_element == 1:
          struct_rd_middle += f"r_{struct_name.lower()}.{curr_val.lower()};"
        else:
          struct_rd_middle = f"r_{struct_name.lower()}.{curr_val.lower()} :: " + struct_rd_middle
        struct_we_middle += gen_func_we(struct_name, curr_val, curr_len, row[header.index('Updated by\n(direct write, not via instructions)')], bit_offset, is_ro)
        struct_we_clr += gen_func_we_clr(struct_name, curr_val, row[header.index('Updated by\n(direct write, not via instructions)')])
      
      #print("start_ptr = %d, end_ptr = %d, bit_ofst = %d, curr_ptr(i) = %d, curr_val = %s, curr_len = %d, field name = %s, first_element: %d" % (start_ptr, end_ptr, bit_offset, i, curr_val, curr_len, row[i], first_element))

      if i != end_ptr:
        curr_val = row[i-1] #move to the next bit
        curr_len = 1

  #ROZ registers
  if dict_reg_len["XLEN"] == 64:
    struct_rd_zero = row[header.index('Reset Impl A')]
    if (row[header.index('A71/H71')] == 'ROZ'): 
      struct_rd += struct_rd_start + struct_rd_zero + struct_rd_end
    else: 
      struct_rd += struct_rd_start + struct_rd_middle + struct_rd_end
  else:
    struct_rd_zero = row[header.index('Reset Impl L')]
    if (row[header.index('L71')] == 'ROZ'): 
      struct_rd += struct_rd_start + struct_rd_zero + struct_rd_end
    else: 
      struct_rd += struct_rd_start + struct_rd_middle + struct_rd_end    

  struct_we += struct_we_start + struct_we_middle + struct_we_end
    

  #close struct statement
  struct_str += "};\n\n"
  return struct_str, struct_io, struct_conn, struct_wire, struct_wire_init, struct_updt, struct_updt_assert, struct_rd, struct_we, struct_we_clr

# ------------ registers, io & wire declaration ------------
def gen_reg(width, name, addr, updt_by_hw, reset, first_item, prj_roz):

  def gen_func_io(name, width, updt_by_hw, first_item):
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
        if width in dict_reg_len:
          a = f"uint_<{{{width}}}>"
        else:
          a = f"uint{width}"
        io_we += f"{a:<20}"
        io_we += f"{name}_val"
      else:
        a = f"uint{dict_reg_len['XLEN']}"
        io_we += f"{a:<20}"
        io_we += f"{name}_val,\n"
        
        io_we += ' '*8
        a = f"uint{int(math.log2(dict_reg_len['TRIGGERS']))}" 
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

  # def gen_func_updt(name, width, updt_by_hw):
  #   if updt_by_hw not in ['', '-']:
  #     updt_str = ' '*8
  #     a = f"r_{name}"
  #     updt_str += f"{a:<20}"
  #     a = f"= sw_{name}_we"
  #     updt_str += f"{a:<24}"
  #     if width in dict_reg_len:
  #       a = f"? wdata[63..0]"
  #     else:
  #       a = f"? wdata[{int(width)-1}..0]"
  #     updt_str += f"{a:<24}"
  #     a = f": (r_{name}_we" 
  #     updt_str += f"{a:<24}"
  #     a = f"? r_{name}_val" 
  #     updt_str += f"{a:<24}"
  #     updt_str += f": r_{name});\n"

  #   else:
  #     updt_str = ''
  #   return updt_str

  # Use if/else (connect write enables to FF.WE pin) instead of A = B ? C : D (all logic connects to FF.D pin, FF.WE=1) 
  def gen_func_updt(name, width, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      updt_str = ' '*8
      a = f"if (sw_{name}_we"
      updt_str += f"{a:<24}"
      updt_str += ") { "
      a = f"r_{name}"
      updt_str += f"{a:<20}"
      if width in dict_reg_len:
        a = f"= wdata[{dict_reg_len[width]-1}..0];"
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

  def gen_func_updt_tdata1(name, width, updt_by_hw):
    if updt_by_hw not in ['', '-']:
      updt_str = ' '*8
      a = f"if (sw_{name}_we"
      updt_str += f"{a:<24}"
      updt_str += ") { "
      a = f"r_{name}[r_tselect.idx]"
      updt_str += f"{a:<20}"
      if width in dict_reg_len:
        a = f"= wdata[{int(dict_reg_len.get('XLEN', 0))-1}..0];" #TODO: temporary solution
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

  def finish_reg_str(reg_str, split, reset, name):
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
    if width in dict_reg_len:
      if width.find('*') != -1: 
        width_split = re.split('[*]', width) #split XLEN*TRIGGERS to [XLEN, TRIGGERS]
        a = f"public register uint_<{{{width_split[0]}}}>"
        reg_str += f"{a:<48}"
        reg_str += finish_reg_str(reg_str, 1, reset, name)
      else:
        a = f"public register uint_<{{{width}}}>"
        reg_str += f"{a:<48}"
        reg_str += finish_reg_str(reg_str, 0, reset, name)
    else:
      a = f"public register uint{width}"
      reg_str += f"{a:<48}"
      reg_str += finish_reg_str(reg_str, 0, reset, name)
  else:
    reg_str = ''
    
  #return values
  reg_io = gen_func_io(name, width, updt_by_hw, first_item)
  reg_conn = gen_func_connect(name, updt_by_hw)
  reg_wire = gen_func_wire(name, updt_by_hw)
  reg_wire_init = gen_func_wire_init(name, updt_by_hw)
  if name == 'tdata1':
    reg_updt = gen_func_updt_tdata1(name, width, updt_by_hw)
  else:
    reg_updt = gen_func_updt(name, width, updt_by_hw)
  reg_updt_assert = gen_updt_assert(name, updt_by_hw)

  return reg_str, reg_io, reg_conn, reg_wire, reg_wire_init, reg_updt, reg_updt_assert

def gen_reg_struct(name, addr, reset, prj_roz):
  if not prj_roz:
    struct_str =  ' '*4
    if dict_reg_len["XLEN"] == 64:
      a = f"public register struct {name}_t"
    else:
      a = f"public register struct {name}_32_t"
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
def gen_define(name, addr):
  def_str = f"#define CSR_{name.upper()}"
  def_str +=' '*(30-len(def_str))
  def_str +=f"{addr}\n"
  return def_str

# ------------ read MUX (for unstructured registers) ------------
def gen_rd_mux(is_list, bit_index, orig_name, name, width, en_acc, dis_act, is_ro, prj_roz):#if orig_name contains <>, is_list=True, split it to get enable names
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
    if width in dict_reg_len:
      if width.find('*') != -1: 
        a = f"rdata = r_{name.lower()}[r_tselect.idx];"#temporary solution
      else:
        a = f"rdata = r_{name.lower()};"
    else:
      if dict_reg_len["XLEN"] == 64:
        if int(width, base=0) == 64:
          a = f"rdata = r_{name.lower()};"
        else:
          a = f"rdata = (uint{64-int(width, base=0)})0 :: r_{name.lower()};"
      if dict_reg_len["XLEN"] == 32:
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
def gen_wena(name, updt_by_hw, width, is_ro, prj_ro): 
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
      if width in dict_reg_len:
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
