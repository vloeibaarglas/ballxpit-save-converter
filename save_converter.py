#!/usr/bin/env python3
"""
BALL x PIT Save Converter
Converts GamePass/Switch save files to Steam-compatible format.
Usage: python3 save_converter.py <input_file> [output_file]
"""
import sys
import os

# Start marker: serialized "MetaData, Assembly-CSharp" header
START_MARKER = bytes.fromhex(
    '022F00000000011D0000004D0065007400610053'
    '0061007600650044006100740061'
)

# End marker: field name "NumBossBlueprintsDropped" + terminator
END_MARKER = bytes.fromhex(
    '4E0075006D0042006F007300730042006C0075006500'
    '7000720069006E0074007300440072006F0070007000'
    '650064000000000005'
)

def find_save_data(data):
    start = data.find(START_MARKER)
    if start == -1:
        return None, None, "Start marker not found"

    end = data.find(END_MARKER, start)
    if end == -1:
        return None, None, "End marker not found"

    end += len(END_MARKER)
    return start, end, None

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file> [output_file]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'rb') as f:
        data = f.read()

    print(f"Input: {input_path} ({len(data):,} bytes)")

    # Check if already a Steam save
    if data[:len(START_MARKER)] == START_MARKER:
        print("Format: Already Steam-compatible")
        save_data = data
    else:
        print("Format: GamePass/Switch container detected")
        start, end, err = find_save_data(data)
        if err:
            print(f"Error: {err}")
            sys.exit(1)
        print(f"Save data: offset 0x{start:X} - 0x{end:X} ({end - start:,} bytes)")
        save_data = data[start:end]

    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}.steam{ext}" if ext else f"{base}.steam"

    with open(output_path, 'wb') as f:
        f.write(save_data)

    print(f"Output: {output_path} ({len(save_data):,} bytes)")
    print("Done. Copy to: %appdata%\\..\\LocalLow\\Kenny Sun\\BALL x PIT\\")

if __name__ == "__main__":
    main()
