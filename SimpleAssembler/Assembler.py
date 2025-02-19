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
