"""SLUS_209.19 디스어셈블 (va 기준)."""
import capstone, sys, os, struct
D = open(os.path.join(os.path.dirname(__file__), '..', 'extract', 'SLUS_209.19'), 'rb').read()
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
SEG = []
ph = struct.unpack_from('<I', D, 0x1c)[0]
for i in range(struct.unpack_from('<H', D, 0x2c)[0]):
    t, off, va, pa, fs, ms, fl, al = struct.unpack_from('<8I', D, ph + 32 * i)
    SEG.append((va, off, fs, ms))
def v2o(va):
    for v, o, fs, ms in SEG:
        if v <= va < v + fs: return va - v + o
    return None
def o2v(off):
    for v, o, fs, ms in SEG:
        if o <= off < o + fs: return off - o + v
def r32(va): return struct.unpack_from('<I', D, v2o(va))[0]
def dis(va, n):
    out = []
    for i in range(n):
        a = va + 4 * i; o = v2o(a)
        ins = list(md.disasm(D[o:o + 4], a))
        out.append(f'{a:08x}: ' + (ins[0].mnemonic + ' ' + ins[0].op_str if ins else '.word ' + D[o:o + 4].hex()))
    return '\n'.join(out)
if __name__ == '__main__': print(dis(int(sys.argv[1], 16), int(sys.argv[2])))
