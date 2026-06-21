# Ball X Pit Save Converter Tool

Script to Convert Game Pass / Nintendo Switch save files to Steam-compatible format for **BALL x PIT**.
(Plus an utility to auto-press annoying gold button when picking up Fission)

## Requirements

- Python 3.6+
- No external dependencies

## Usage

```bash
python3 save_converter.py <input_file> [output_file]
```

If no output file is specified, the script creates `<input_name>.steam` in the same directory.

### Examples

```bash
# Convert a Game Pass save
python3 save_converter.py meta1.yankai

# Convert with custom output name
python3 save_converter.py meta1.yankai my_save.yankai
```

## Save File Locations

### Source (input)

**Game Pass:**
```
%LocalAppData%\Packages\DevolverDigital.BallxPit_6kzv4j18v0c96\SystemAppData\wgs\
```
Open the folder with the long random name, then open the folder inside. The save file is a single binary file with a random UUID name (e.g., `FEF42718C7A7493CBF54A30FF4F2806E`).

**Nintendo Switch (via DBI MTP):**
1. Install [DBI](https://github.com/likono/switch-livergame-manager/releases) on your Switch
2. Connect Switch to PC via USB and launch DBI
3. Select **MTP responder** in DBI
4. Your Switch will appear as a drive on your PC
5. Navigate to the BALL x PIT save directory
6. Copy the save file to your PC

### Destination (output)

```
%LocalAppData%Low\Kenny Sun\BALL x PIT\
```

## How It Works

Game Pass and Switch saves are wrapped in a container format. The script locates the actual save data by searching for hex markers:

**Start marker** — Unity serialized `MetaData, Assembly-CSharp` header:
```
02 2F 00 00 00 00 01 1D 00 00 00 4D 00 65 00 74
00 61 00 53 00 61 00 76 00 65 00 44 00 61 00 74
00 61
```

**End marker** — `NumBossBlueprintsDropped` field with terminator:
```
4E 00 75 00 6D 00 42 00 6F 00 73 00 73 00 42 00
6C 00 75 00 65 00 70 00 72 00 69 00 6E 00 74 00
73 00 44 00 72 00 6F 00 70 00 70 00 65 00 64 00
00 00 00 00 05
```

Everything between these markers is extracted and written as a standalone Steam-compatible file.

## License

[MIT](https://github.com/vloeibaarglas/ballxpit-save-converter/blob/main/LICENSE)
