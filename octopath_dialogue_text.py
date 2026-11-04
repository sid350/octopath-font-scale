#!/usr/bin/env python3
# Larger dialogue text for OCTOPATH TRAVELER (Switch, update 1.0.5): a patch pak that raises the font size in the speech balloons only.
#
# Dialogue, tutorials and most menus share one font (FONT_KS_NewCinema), so changing the font files, as octopath_font_scale.py does, changes them all.
# This script leaves the fonts alone and changes the Size of the font in the balloon widgets: the text (21) and the speaker's name (18).
# A line's height grows with the font, so LineHeightPercentage of the text is scaled back and its lines keep their spacing, as in the other script.
# Do not use it together with octopath_font_scale.py's pak: the two scales would multiply.
#
# Usage: octopath_dialogue_text.py <folder with the game's paks> [-s 1.5] [-o Kingship-Switch_8_P.pak]
#   the folder is RomFS/Kingship/Content/Paks of the game with its update (Kingship-Switch.pak and Kingship-Switch_0_P.pak)
# Needs only Python 3.8+ and octopath_font_scale.py beside this script.
import argparse, os, re, struct, sys
import octopath_font_scale as pak

WIDGETS = ['Kingship/Content/UI/Balloon/BP/' + n for n in ('TalkText_Balloon', 'TalkText_DeepThink', 'Balloon_00', 'Balloon_01', 'BalloonManagerBP')]
TEXT_SIZE, NAME_SIZE = 21, 18
SIZES = (TEXT_SIZE, NAME_SIZE)


def names(asset):
    """The package's name table"""
    custom = struct.unpack_from('<i', asset, 20)[0]; o = 24 + custom * 20 + 4
    folder = struct.unpack_from('<i', asset, o)[0]; o += 4 + folder + 4
    count, o = struct.unpack_from('<ii', asset, o); out = []
    for _ in range(count):
        n = struct.unpack_from('<i', asset, o)[0]; o += 4
        if n < 0: out.append(asset[o:o - 2 * n - 2].decode('utf-16-le')); o -= 2 * n
        else: out.append(asset[o:o + n - 1].decode('latin-1')); o += n
        o += 4   # the name's hashes
    return out


def scale_sizes(asset, export, scale, label):
    """The widget's serialized data with each font Size scaled, and the line height of the text scaled back so its lines keep their spacing"""
    t = {n: i for i, n in enumerate(names(asset))}
    size_tag = struct.pack('<iiiiiib', t['Size'], 0, t['IntProperty'], 0, 4, 0, 0)
    line_tag = struct.pack('<iiiiiib', t['LineHeightPercentage'], 0, t['FloatProperty'], 0, 4, 0, 0)
    d = bytearray(export); found = []
    sizes = [m.end() for m in re.finditer(re.escape(size_tag), export)]
    lines = [m.end() for m in re.finditer(re.escape(line_tag), export)]
    if not sizes: sys.exit(f'{label}: no font size found')
    for k, at in enumerate(sizes):
        v = struct.unpack_from('<i', d, at)[0]
        if v not in SIZES: sys.exit(f'{label}: a Size of {v}, not one of {SIZES}: another game version?')
        new = round(v * scale + 0.001); struct.pack_into('<i', d, at, new)
        end = sizes[k + 1] if k + 1 < len(sizes) else len(d)
        line = next((x for x in lines if at < x < end), None)
        old = struct.unpack_from('<f', d, line)[0] if line else None
        if v == TEXT_SIZE:
            if line is None: sys.exit(f'{label}: a text block without a line height')
            struct.pack_into('<f', d, line, old * v / new)   # the height follows the real sizes, 21 to 32 is not exactly the scale
        found.append((v, new, None if old is None else round(old, 3), round(struct.unpack_from('<f', d, line)[0], 3) if line else None))
    return bytes(d), found


def main():
    ap = argparse.ArgumentParser(description="A patch pak with larger text in OCTOPATH TRAVELER's speech balloons only")
    ap.add_argument('paks', help="the game's RomFS/Kingship/Content/Paks folder (with the update's Kingship-Switch_0_P.pak)")
    ap.add_argument('-s', '--scale', type=float, default=1.5, help='text scale (default 1.5)')
    ap.add_argument('-o', '--out', help='output pak (default: Kingship-Switch_8_P.pak in the paks folder)')
    a = ap.parse_args()
    if not 1 <= a.scale <= 3: sys.exit('the scale must be between 1 and 3')
    pak.FONTS = [w + e for w in WIDGETS for e in ('.uasset', '.uexp')]   # the files read_pak picks out
    files = {}
    for n in ('Kingship-Switch.pak', 'Kingship-Switch_0_P.pak'):   # the update's pak wins
        p = os.path.join(a.paks, n)
        if os.path.isfile(p): files.update(pak.read_pak(p))
        elif n == 'Kingship-Switch.pak': sys.exit(f'{p} not found')
    missing = [f for f in pak.FONTS if f not in files]
    if missing: sys.exit('not found in the paks: ' + ', '.join(missing))
    out = []
    for w in WIDGETS:
        d, found = scale_sizes(files[w + '.uasset'], files[w + '.uexp'], a.scale, w)
        out += [(w + '.uasset', files[w + '.uasset']), (w + '.uexp', d)]
        print(f'{w.rsplit("/", 1)[1]}: (size, new, line height, new) {found}')
    path = a.out or os.path.join(a.paks, 'Kingship-Switch_8_P.pak')
    pak.write_pak(path, out)
    print(f'{path}: {os.path.getsize(path):,} bytes')


if __name__ == '__main__':
    main()
