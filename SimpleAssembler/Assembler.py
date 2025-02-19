import sys
import re

opcode_mapping = {
    # R-Type Instructions having formats (opcode, funct3, funct7)
    "sub":  ("0110011", "000", "0100000"),
    "add":  ("0110011", "000", "0000000"),
    "or":   ("0110011", "110", "0000000"),
    "srl":  ("0110011", "101", "0000000"),
    "slt":  ("0110011", "010", "0000000"),
    "xor":  ("0110011", "100", "0000000"),

    # I-Type Instructions having formats (opcode, funct3)
    "addi": ("0010011", "000"),
    "lw":   ("0000011", "010"),
    "jalr": ("1100111", "000"),
    
    # S-Type Instructions having formats (opcode, funct3)
    "sw":   ("0100011", "010"),
    
    # B-Type Instructions having formats (opcode, funct3)
    "beq":  ("1100011", "000"),
    "bne":  ("1100011", "001"),
    "blt":  ("1100011", "100"),
    "bge":  ("1100011", "101"),  
    "bltu": ("1100011", "110"),
    
    # J-Type Instructions having formats (only opcode)
    "jal":  ("1101111",)
}



register_mapping = {
    # Special Purpose Registers used for assembler
    "zero": 0, "ra": 1, "sp": 2, "gp": 3, "tp": 4,

    # Temporary Registers used for assembler
    "t0": 5, "t1": 6, "t2": 7, "t3": 28, "t4": 29, "t5": 30, "t6": 31,

    # Saved Registers used for assembler
    "s0": 8, "s1": 9, "s2": 18, "s3": 19, "s4": 20, "s5": 21,
    "s6": 22, "s7": 23, "s8": 24, "s9": 25, "s10": 26, "s11": 27,

    # Argument Registers used for assembler
    "a0": 10, "a1": 11, "a2": 12, "a3": 13, "a4": 14,
    "a5": 15, "a6": 16, "a7": 17
}
def instruction_parsing(instruction, curr_address, labels):
    pt = instruction.replace(',', ' ').split()
    if not pt:
        return None
    
    op_code = pt[0]

    if op_code in opcode_mapping:
        
        op = opcode_mapping[op_code]
        
        if op_code in ["add", "slt", "sub", "srl", "or", "xor"]:
            rd = register_mapping[pt[1]]
            rs1 = register_mapping[pt[2]]
            rs2 = register_mapping[pt[3]]
            op_bin, fun3, fun7 = op[0], op[1], op[2]
            return f"{fun7}{rs2:05b}{rs1:05b}{fun3}{rd:05b}{op_bin}"

        elif op_code in ["jalr", "addi"]:
            rd, rs1, imm = register_mapping[pt[1]], register_mapping[pt[2]], int(pt[3])
            imm_binary = f"{imm & 0xFFF:012b}"
            return f"{imm_binary}{rs1:05b}{op[1]}{rd:05b}{op[0]}"
        
        elif op_code in ["sw", "lw"]:
            matching = re.match(r'(-?\d+)\((\w+)\)', pt[2])
            if matching:
                offseting = int(matching.group(1))
                b_reg = register_mapping[matching.group(2)]
                rd_or_rs2 = register_mapping[pt[1]]
                imm_binary = f"{offseting & 0xFFF:012b}"
                if op_code != "lw":
                    return f"{imm_binary[:7]}{rd_or_rs2:05b}{b_reg:05b}{op[1]}{imm_binary[7:]}{op[0]}"
                else:
                    return f"{imm_binary}{b_reg:05b}{op[1]}{rd_or_rs2:05b}{op[0]}"
         elif op_code in ["bne", "beq", "blt", "bge", "bltu"]:
            rs1, rs2, label = register_mapping[pt[1]], register_mapping[pt[2]], pt[3]
            if label in labels:
                offseting = (labels[label] - curr_address) # <-- Change here from //4 to //2
            else:
                offseting = int(label)
            if offseting < 0:
                offseting = (1 << 13) + offseting  # Convert negative value to two's complement
            # imm_binary=f"{offseting:0{12}b}"  # Format as a binary string with leading zeros
            imm_binary = format(offseting, f'0{13}b')
            return f"{imm_binary[0]}{imm_binary[2:8]}{rs2:05b}{rs1:05b}{op[1]}{imm_binary[8:12]}{imm_binary[1]}{op[0]}"

        
        elif op_code == "jal":
            rd, label = register_mapping[pt[1]], pt[2]
            if label in labels:
                offseting = (labels[label] - curr_address)
            else:
                offseting = int(label)
            if offseting < 0:
                offseting = (1 << 21) + offseting  # Convert negative value to two's complement
            # imm_binary=f"{offseting:0{12}b}"  # Format as a binary string with leading zeros
            imm_binary = format(offseting, f'0{21}b')
            return f"{imm_binary[0]}{imm_binary[10:20]}{imm_binary[9]}{imm_binary[1:9]}{rd:05b}{op[0]}"
    
    return None
def assembler_code(output_file,input_file):
    f=open(input_file, 'r')
    lines = f.readlines()
    
    labels = {}
    instructs = []
    address = 0
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            label = line.split(':')[0].strip()
            labels[label] = address
            line = line.split(':')[1].strip()
        if line:
            instructs.append(line)
            address += 4
    
    bin_output = []
    address = 0
    for instruct in instructs:
        bin = instruction_parsing(instruct,address,labels)
        if bin:
            bin_output.append(bin)
        else:
            print(f"Error: Unable to parse instruction '{instruct}'")
        address += 4
    
    f=open(output_file, 'w')
    for bin in bin_output:
        f.write(bin + '\n')
    print("Assembly successful done. Output saved to", output_file)

if len(sys.argv) <=2:
    print("Command: python assembler.py input.asm output.txt")
else:
    assembler_code(sys.argv[2], sys.argv[1])
