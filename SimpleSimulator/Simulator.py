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

def simulator(inputf):
    instrs = []
    try:
        with open(inputf, 'r') as f:
            for line_no, ln in enumerate(f, 1):
                ln = ln.strip()
                if not ln:
                    continue
                if len(ln) != 32:
                    print(f"Error: Found in Line {line_no}: Instruction should be 32 bits")
                    sys.exit(1)
                instrs.append(ln)
    except FileNotFoundError:
        print(f"Error: Input file '{inputf}' not found")
        sys.exit(1)

    rgs = [0] * 32
    rgs[2] = 380 
    pc = 0
    data_mem = [0] * 32
    stack_mem = {}

    b_t = []
    d_t = []

    while True:
        inst_pos = pc // 4
        if inst_pos < 0 or inst_pos >= len(instrs):
            break

        curr_inst = instrs[inst_pos]

        if curr_inst == "00000000000000000000000001100011": # for virtual Halt
            b_t.append(ft_binary(pc, rgs))
            d_t.append(ft_decimal(pc, rgs))
            break

        new_pc = pc + 4 
        op_code = curr_inst[25:32]

        try:
            if op_code == "0110011":  # for R-type instructions
                function7 = curr_inst[0:7]
                rs2 = int(curr_inst[7:12], 2)
                rs1 = int(curr_inst[12:17], 2)
                function3 = curr_inst[17:20]
                rd = int(curr_inst[20:25], 2)
                val1 = rgs[rs1]
                val2 = rgs[rs2]

                if function3 == "000":
                    if function7 == "0000000":
                        res = val1 + val2
                    elif function7 == "0100000":
                        res = val1 - val2
                    else:
                        raise Exception(f"Unknown function7 {function7}")
                elif function3 == "110" and function7 == "0000000":
                    res = val1 | val2
                elif function3 == "101" and function7 == "0000000":
                    shift = val2 & 0x1F
                    res = val1 >> shift
                elif function3 == "010" and function7 == "0000000":
                    res = 1 if (val1 < val2) else 0
                elif function3 == "111" and function7 == "0000000":
                    res = val1 & val2
                else:
                    raise Exception(f"unsupported R-type function3={function3}, function7={function7}")
                win_registers(rgs, rd, res)

            elif op_code == "0010011":  # for I-type instructions (ADDI)
                imm = s_extender(int(curr_inst[0:12], 2), 12)
                rs1 = int(curr_inst[12:17], 2)
                function3 = curr_inst[17:20]
                rd = int(curr_inst[20:25], 2)
                if function3 == "000":
                    res = rgs[rs1] + imm
                else:
                    raise Exception(f"unsupported I-type function3: {function3}")
                win_registers(rgs, rd, res)

            elif op_code == "0000011":  # I-type (LW)
                imm = s_extender(int(curr_inst[0:12], 2), 12)
                rs1 = int(curr_inst[12:17], 2)
                function3 = curr_inst[17:20]
                rd = int(curr_inst[20:25], 2)
                if function3 == "010":
                    addr = rgs[rs1] + imm
                    value = read_memory(data_mem, stack_mem, addr)
                    win_registers(rgs, rd, value)

            elif op_code == "0100011":  # for S-type instructions (SW)
                imm_high = curr_inst[0:7]
                imm_low = curr_inst[20:25]
                imm = s_extender(int(imm_high + imm_low, 2), 12)
                rs1 = int(curr_inst[12:17], 2)
                rs2 = int(curr_inst[7:12], 2)
                function3 = curr_inst[17:20]
                if function3 == "010":
                    addr = rgs[rs1] + imm
                    data_mem, stack_mem = write_memory(data_mem, stack_mem, addr, rgs[rs2])

            elif op_code == "1100011":  # for B-type instructions
                imm = (int(curr_inst[0]) << 12) | (int(curr_inst[24]) << 11) | (int(curr_inst[1:7], 2) << 5) | (int(curr_inst[20:24], 2) << 1)
                imm = s_extender(imm, 13)
                rs1 = int(curr_inst[12:17], 2)
                rs2 = int(curr_inst[7:12], 2)
                function3 = curr_inst[17:20]
                branch = False
                if function3 == "000":
                    branch = (rgs[rs1] == rgs[rs2])
                elif function3 == "001":
                    branch = (rgs[rs1] != rgs[rs2])
                else:
                    raise Exception(f"unsupported B-type function3 found: {function3}")
                new_pc = pc + (imm if branch else 4)

            elif op_code == "1101111":  # JAL
                imm = (int(curr_inst[0]) << 20) | (int(curr_inst[1:11], 2) << 1) | (int(curr_inst[11]) << 11) | (int(curr_inst[12:20], 2) << 12)
                imm = s_extender(imm, 21)
                rd = int(curr_inst[20:25], 2)
                win_registers(rgs, rd, pc + 4)
                new_pc = pc + imm

            elif op_code == "1100111":  # JALR
                imm = s_extender(int(curr_inst[0:12], 2), 12)
                rs1 = int(curr_inst[12:17], 2)
                rd = int(curr_inst[20:25], 2)
                target = (rgs[rs1] + imm) & ~1
                win_registers(rgs, rd, pc + 4)
                new_pc = target

            else:
                raise Exception(f"It is a unknown op_code: {op_code}")

        except Exception as e:
            print(f"Error present in instruction ln {inst_pos+1} (PC=0x{pc:08X}): {e}")
            sys.exit(1)

        pc = new_pc
        b_t.append(ft_binary(pc, rgs))
        d_t.append(ft_decimal(pc, rgs))

    return (b_t, d_t, data_mem)

