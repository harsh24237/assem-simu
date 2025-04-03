import sys
import os

def s_extender(value, bits):
    sign_bit = 1 << (bits - 1)
    k=(value & (sign_bit - 1)) - (value & sign_bit)
    return k

def ft_binary(pc, rgs):
    pc_str = "0b" + format(pc & 0xFFFFFFFF, '032b')
    regs_str = " ".join("0b" + format(r & 0xFFFFFFFF, '032b') for r in rgs)
    return f"{pc_str} {regs_str}"

def win_registers(rgs, rd, value):
    if rd != 0:
        rgs[rd] = value & 0xFFFFFFFF

def ft_decimal(pc, rgs):
    val1 = [str(pc)]
    val2 = [str(signed_32(r)) for r in rgs]
    values=val1+val2
    return " ".join(values)

def signed_32(x):
    x = x & 0xFFFFFFFF
    return x if x < 0x80000000 else x - 0x100000000

def read_memory(data_mem, stack_mem, addr):
    """Read from either data memory or stack memory based on address"""
    if 0x00010000 <= addr <= 0x0001007C:
        mem_index = (addr - 0x00010000) // 4
        return data_mem[mem_index]
    else:  
        return stack_mem.get(addr, 0)  

def write_memory(data_mem, stack_mem, addr, value):
    """Write to either data memory or stack memory based on address"""
    if 0x00010000 <= addr <= 0x0001007C:  
        mem_index = (addr - 0x00010000) // 4
        data_mem[mem_index] = value & 0xFFFFFFFF
    else: 
        stack_mem[addr] = value & 0xFFFFFFFF
    return data_mem, stack_mem
