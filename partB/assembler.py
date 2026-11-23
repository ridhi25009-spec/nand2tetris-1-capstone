import sys
import os


# --------------------------------------------------
# Predefined Hack symbols
# --------------------------------------------------

SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
}


# --------------------------------------------------
# Hack instruction tables
# --------------------------------------------------

DEST = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

COMP = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",

    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101",
}

JUMP = {
    "":    "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


# --------------------------------------------------
# Remove comments and blank lines
# --------------------------------------------------

def clean_lines(filename):
    lines = []

    with open(filename, "r") as f:
        for line_number, line in enumerate(f, start=1):

            # Remove comments
            line = line.split("//")[0].strip()

            # Ignore blank lines
            if line == "":
                continue

            lines.append((line, line_number))

    return lines


# --------------------------------------------------
# First pass:
# Find labels and their instruction addresses
# --------------------------------------------------

def first_pass(lines, symbols):

    instruction_address = 0
    label_addresses = {}

    for line, line_number in lines:

        # Label
        if line.startswith("(") and line.endswith(")"):

            label = line[1:-1].strip()

            if not label:
                raise ValueError(
                    f"Line {line_number}: invalid empty label"
                )

            if label in label_addresses:
                raise ValueError(
                    f"Line {line_number}: duplicate label '{label}'"
                )

            label_addresses[label] = instruction_address

        else:
            instruction_address += 1

    symbols.update(label_addresses)

    return label_addresses


# --------------------------------------------------
# Convert A-instruction
# --------------------------------------------------

def assemble_a_instruction(value, symbols, variables):

    # Numeric address
    if value.isdigit():
        number = int(value)

    else:
        # Existing symbol
        if value in symbols:
            number = symbols[value]

        else:
            # New variable
            if value not in variables:
                variables[value] = 16 + len(variables)
                symbols[value] = variables[value]

            number = symbols[value]

    if number < 0 or number > 32767:
        raise ValueError(
            f"Invalid A-instruction value: {value}"
        )

    return format(number, "016b")


# --------------------------------------------------
# Convert C-instruction
# --------------------------------------------------

def assemble_c_instruction(instruction):

    dest_part = ""
    comp_jump_part = instruction

    if "=" in instruction:
        dest_part, comp_jump_part = instruction.split("=", 1)

    jump_part = ""

    if ";" in comp_jump_part:
        comp_part, jump_part = comp_jump_part.split(";", 1)
    else:
        comp_part = comp_jump_part

    comp_part = comp_part.strip()
    dest_part = dest_part.strip()
    jump_part = jump_part.strip()

    if comp_part not in COMP:
        raise ValueError(
            f"invalid comp instruction '{comp_part}'"
        )

    if dest_part not in DEST:
        raise ValueError(
            f"invalid destination '{dest_part}'"
        )

    if jump_part not in JUMP:
        raise ValueError(
            f"invalid jump '{jump_part}'"
        )

    return (
        "111"
        + COMP[comp_part]
        + DEST[dest_part]
        + JUMP[jump_part]
    )


# --------------------------------------------------
# Second pass
# Convert instructions into 16-bit machine code
# --------------------------------------------------

def second_pass(lines, symbols):

    machine_code = []
    variables = {}

    for line, line_number in lines:

        # Ignore labels
        if line.startswith("(") and line.endswith(")"):
            continue

        try:

            # A-instruction
            if line.startswith("@"):

                value = line[1:].strip()

                if value == "":
                    raise ValueError("empty A-instruction")

                binary = assemble_a_instruction(
                    value,
                    symbols,
                    variables
                )

            # C-instruction
            else:

                binary = assemble_c_instruction(line)

            machine_code.append(binary)

        except ValueError as error:

            raise ValueError(
                f"Line {line_number}: {error}"
            )

    return machine_code


# --------------------------------------------------
# Save symbols.txt
# --------------------------------------------------

def save_symbols(symbols, output_file):

    with open(output_file, "w") as f:

        for name, address in sorted(
            symbols.items(),
            key=lambda item: (item[1], item[0])
        ):
            f.write(f"{name} = {address}\n")


# --------------------------------------------------
# Main assembler
# --------------------------------------------------

def assemble(input_file):

    lines = clean_lines(input_file)

    # Copy predefined symbols
    symbols = SYMBOLS.copy()

    # First pass
    label_addresses = first_pass(lines, symbols)

    # Second pass
    machine_code = second_pass(lines, symbols)

    # Output .hack filename
    base_name = os.path.splitext(input_file)[0]
    hack_file = base_name + ".hack"

    # Save .hack
    with open(hack_file, "w") as f:

        for instruction in machine_code:
            f.write(instruction + "\n")

    # K = 78
    # 78 mod 3 = 0
    # Save symbols and variables
    symbols_file = os.path.join(
        os.path.dirname(input_file),
        "symbols.txt"
    )

    save_symbols(symbols, symbols_file)

    print("Assembly completed successfully!")
    print("Input:", input_file)
    print("Output:", hack_file)
    print("Total instructions:", len(machine_code))
    print("Symbols saved to:", symbols_file)


# --------------------------------------------------
# Program entry point
# --------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage:")
        print("python assembler.py program.asm")
        sys.exit(1)

    try:

        assemble(sys.argv[1])

    except Exception as error:

        print("Assembly failed!")
        print(error)
        sys.exit(1)