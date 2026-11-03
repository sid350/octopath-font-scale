#!/usr/bin/env python3
# Larger text for OCTOPATH TRAVELER (Switch, update 1.0.5): a patch pak that loads over the game's own and scales its Latin fonts.
#
# The game draws its text with FreeType from the font files in its paks (Kingship/Content/UI/Font/*.ufont, plain TrueType). Each font's
# unitsPerEm is divided by the factor, so every glyph and advance grows by it while windows, frames and pictures keep their size. Unreal
# Engine 4.18 takes a line's height and baseline from the font's bounding box (head yMin / yMax), so the box is scaled back down and the
# lines keep their spacing; hhea and OS/2 line metrics follow it for other readers. Only the Latin text fonts are changed.
#
# Usage: octopath_font_scale.py <folder with the game's paks> [-s 1.5] [-o Kingship-Switch_9_P.pak]
#   the folder is RomFS/Kingship/Content/Paks of the game with its update (Kingship-Switch.pak and Kingship-Switch_0_P.pak)
# The output goes beside them: the engine mounts the paks named *_<n>_P.pak after the game's own, the higher n last.
# Needs only Python 3.8+.
import argparse, hashlib, os, struct, sys, zlib

FONTS = ['Kingship/Content/UI/Font/' + n + '.ufont' for n in ('KS_Meldir_B', 'KS_Meldir_Default', 'KS_NewCinema_Std_D', 'KS_Skech_B', 'KS_Skech_Default', 'KS_Skech_I')]
MAGIC = 0x5A6F12E1


# ---- legacy Unreal paks (version 4 and older: one index entry per file) ----
class Reader:
    def __init__(self, b): self.b, self.o = b, 0
    def take(self, fmt): v = struct.unpack_from(fmt, self.b, self.o); self.o += struct.calcsize(fmt); return v if len(v) > 1 else v[0]
    def fstr(self):
        n = self.take('<i')
        if n < 0: s = self.b[self.o:self.o - 2 * n].decode('utf-16-le'); self.o -= 2 * n
        else: s = self.b[self.o:self.o + n].decode('latin-1'); self.o += n
        return s.rstrip('\0')


def read_pak(path):
    """{path in the game: bytes} of the wanted files a pak holds (stored or zlib-compressed)"""
    with open(path, 'rb') as f:
        f.seek(-45, 2); enc, magic, ver, ioff, isz = struct.unpack('<BIiqq', f.read(25))
        if magic != MAGIC or ver > 4: sys.exit(f'{path}: not a legacy Unreal pak (magic {magic:#x}, version {ver})')
        if enc: sys.exit(f'{path}: the index is encrypted')
        f.seek(ioff); r = Reader(f.read(isz))
        mount = r.fstr(); out = {}
        for _ in range(r.take('<i')):
            name = r.fstr(); off, size, raw, meth = r.take('<qqqi'); r.take('20s')
            blocks = [r.take('<qq') for _ in range(r.take('<i'))] if meth else []
            r.take('<BI')
            full = os.path.normpath(os.path.join(mount, name)).replace('\\', '/').lstrip('./')
            if full not in FONTS: continue
            if not meth: f.seek(off + 53); data = f.read(size)
            elif meth == 1:   # zlib, block by block (offsets from the file start before version 5)
                data = b''
                for s, e in blocks: f.seek(s if ver < 5 else off + s); data += zlib.decompress(f.read(e - s))
            else: sys.exit(f'{path}: {name} uses compression method {meth}, not zlib')
            if len(data) != raw: sys.exit(f'{path}: {name} came out {len(data)} bytes, not {raw}')
            out[full] = data
    return out


def write_pak(path, files):
    """A version 4 pak of stored files, mounted at ../../../ as the game's own"""
    def fstr(s): b = s.encode() + b'\0'; return struct.pack('<i', len(b)) + b
    def entry(off, d): return struct.pack('<qqqi', off, len(d), len(d), 0) + hashlib.sha1(d).digest() + struct.pack('<BI', 0, 0)
    body, index = bytearray(), bytearray(fstr('../../../') + struct.pack('<i', len(files)))
    for name, d in files:
        off = len(body); body += entry(0, d) + d; index += fstr(name) + entry(off, d)
    with open(path, 'wb') as f:
        f.write(bytes(body) + bytes(index) + struct.pack('<BIiqq', 0, MAGIC, 4, len(body), len(index)) + hashlib.sha1(index).digest())


# ---- TrueType ----
def checksum(d, off, ln, head):
    b = bytes(d[off:off + ln]) + b'\0' * (-ln % 4)
    if head: b = b[:8] + b'\0\0\0\0' + b[12:]   # head's checkSumAdjustment counts as 0
    return sum(struct.unpack(f'>{len(b) // 4}I', b)) & 0xffffffff


def scale_font(data, factor):
    d = bytearray(data); tables = {}
    for i in range(struct.unpack_from('>H', d, 4)[0]):
        tag, _, off, ln = struct.unpack_from('>4sIII', d, 12 + 16 * i); tables[tag] = (i, off, ln)
    for t in (b'head', b'hhea', b'OS/2'):
        if t not in tables: sys.exit(f'the font has no {t.decode()} table')
    _, h, _ = tables[b'head']
    upm = struct.unpack_from('>H', d, h + 18)[0]; new = round(upm / factor); k = new / upm
    struct.pack_into('>H', d, h + 18, new)
    ymin, ymax = struct.unpack_from('>h', d, h + 38)[0], struct.unpack_from('>h', d, h + 42)[0]
    struct.pack_into('>h', d, h + 38, round(ymin * k)); struct.pack_into('>h', d, h + 42, round(ymax * k))
    _, o, _ = tables[b'hhea']
    struct.pack_into('>hhh', d, o + 4, *(round(v * k) for v in struct.unpack_from('>hhh', d, o + 4)))
    _, o, _ = tables[b'OS/2']
    ta, td, tg, wa, wd = struct.unpack_from('>hhhHH', d, o + 68)
    struct.pack_into('>hhhHH', d, o + 68, round(ta * k), round(td * k), round(tg * k), round(wa * k), round(wd * k))
    for t in (b'head', b'hhea', b'OS/2'):
        i, off, ln = tables[t]; struct.pack_into('>I', d, 12 + 16 * i + 4, checksum(d, off, ln, t == b'head'))
    return bytes(d), upm, new


def main():
    ap = argparse.ArgumentParser(description='A patch pak with OCTOPATH TRAVELER\'s Latin fonts scaled up')
    ap.add_argument('paks', help='the game\'s RomFS/Kingship/Content/Paks folder (with the update\'s Kingship-Switch_0_P.pak)')
    ap.add_argument('-s', '--scale', type=float, default=1.5, help='text scale (default 1.5)')
    ap.add_argument('-o', '--out', help='output pak (default: Kingship-Switch_9_P.pak in the paks folder)')
    a = ap.parse_args()
    if not 1 <= a.scale <= 3: sys.exit('the scale must be between 1 and 3')
    fonts = {}
    for n in ('Kingship-Switch.pak', 'Kingship-Switch_0_P.pak'):   # the update's pak wins
        p = os.path.join(a.paks, n)
        if os.path.isfile(p): fonts.update(read_pak(p))
        elif n == 'Kingship-Switch.pak': sys.exit(f'{p} not found')
    missing = [f for f in FONTS if f not in fonts]
    if missing: sys.exit('fonts not found in the paks: ' + ', '.join(missing))
    out = []
    for name in FONTS:
        d, upm, new = scale_font(fonts[name], a.scale); out.append((name, d))
        print(f'{name.rsplit("/", 1)[1]}: units per em {upm} → {new}')
    path = a.out or os.path.join(a.paks, 'Kingship-Switch_9_P.pak')
    write_pak(path, out)
    print(f'{path}: {os.path.getsize(path):,} bytes')


if __name__ == '__main__':
    main()
