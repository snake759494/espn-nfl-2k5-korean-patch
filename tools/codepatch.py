"""SLUS_209.19 한글 출력 패치.
한글 음절은 UTF-16 코드 0xE000+i 로 넣는다. 글리프·텍스처는 공용 한글 폰트 리소스 'fontk'(FONT 묶음에 추가) 하나에 있고,
그리는 폰트의 어센트에 맞춰 크기를 바꾼 글리프 레코드를 KBUF 에 만들어 쓴다.
- 폭 함수(0x1286a8) 실패 경로, 글자 그리기 2곳(0x139910, 0x13a430)의 레코드 실패 경로,
  그리고 두 곳의 텍스처 선택(0x1286a0 호출)을 스텁으로 돌린다.
코드 동굴: 0xbe9400 (런타임에 항상 0 인 정적 영역)"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from asm import *
CAVE = 0xbe9400
KBUF = 0xbe9800
FKC = 0xbe9860            # fontk 범위 객체 캐시
CNT = 0xbe9870            # 디버그 카운터(KO_DEBUG)
DEBUG = bool(os.environ.get('KO_DEBUG'))
KBASE = 0xE000
CAPK = 16.0              # fontk 기준 대문자 높이(글리프 칸 20 = 대문자 1.25배)
FONT_MAGIC = 0x544e4f46
def hi(a): return ((a + 0x8000) >> 16) & 0xffff
def lo(a): return a & 0xffff
def cvt_w_s_raw(fd, fs): return (17 << 26) | (16 << 21) | (fs << 11) | (fd << 6) | 0x24

class A:
    def __init__(s, org): s.org = org; s.c = []; s.lab = {}; s.fix = []
    def pc(s): return s.org + 4 * len(s.c)
    def L(s, n): s.lab[n] = s.pc()
    def __call__(s, *w): s.c += w
    def br(s, kind, rs, rt, lab):
        s.fix.append((len(s.c), kind, rs, rt, lab)); s.c.append(0)
    def done(s):
        for i, kind, rs, rt, lab in s.fix:
            off = (s.lab[lab] - (s.org + 4 * i + 4)) >> 2
            s.c[i] = (beq if kind == 'beq' else bne)(rs, rt, off)
        return b''.join(struct.pack('<I', w) for w in s.c)

def build(nk, G):
    a = A(CAVE); E = {}
    def cnt(k):
        if DEBUG: a(lui('k0', hi(CNT)), lw('k1', lo(CNT) + 4 * k, 'k0'), addiu('k1', 'k1', 1), sw('k1', lo(CNT) + 4 * k, 'k0'))
    # ---- findFK(a0=font range obj) -> v0 = fontk range obj | 0   (t2..t5, v1)
    E['findfk'] = a.pc()
    a(lui('t2', hi(FKC)), lw('v0', lo(FKC), 't2'))
    a.br('bne', 'v0', 'zero', 'ff_ret'); a(NOP)
    a(addiu('t3', 'a0', 0x10000 - 0x30), addiu('t4', 'zero', 64))
    a.L('ff_loop')
    a(lw('t3', 4, 't3'))
    a.br('beq', 't3', 'zero', 'ff_ret'); a(move('v0', 'zero'))
    a(lw('t5', 0x28, 't3'), xori('t5', 't5', 0x6b))
    a.br('bne', 't5', 'zero', 'ff_next'); a(NOP)
    a(lw('t5', 0xc, 't3'), lui('v1', FONT_MAGIC >> 16), ori('v1', 'v1', FONT_MAGIC & 0xffff))
    a.br('bne', 't5', 'v1', 'ff_next'); a(NOP)
    a(addiu('v0', 't3', 0x30), sw('v0', lo(FKC), 't2'))
    a.br('beq', 'zero', 'zero', 'ff_ret'); a(NOP)
    a.L('ff_next')
    a(addiu('t4', 't4', -1))
    a.br('bne', 't4', 'zero', 'ff_loop'); a(NOP)
    a(move('v0', 'zero'))
    a.L('ff_ret'); a(jr('ra'), NOP)
    # ---- klook(a0=font range obj, a1=char) -> v0 = KBUF | 0   (t1..t9, v0, v1, f4..f9)
    E['klook'] = a.pc()
    a(ori('t1', 'zero', KBASE), subu('t1', 'a1', 't1'))      # t1 = c - 0xE000
    a(sltiu('t6', 't1', nk))
    a.br('beq', 't6', 'zero', 'kl_none'); a(NOP)
    a(move('t9', 'ra'), move('t8', 'a0'))
    a(jal(E['findfk']), NOP)
    a(move('ra', 't9'))
    a.br('beq', 'v0', 'zero', 'kl_none'); a(NOP)
    def fconst(fr, v):
        w = struct.unpack('<I', struct.pack('<f', v))[0]
        a(lui('t7', w >> 16), ori('t7', 't7', w & 0xffff), mtc1('t7', fr))
    # 텍스처 칸 위치: 한 줄 PER(2의 거듭제곱)자
    a(addiu('t6', 'zero', G['per']), divu('t1', 't6'), mfhi('t6'), mtc1('t6', 10), cvt_s_w(10, 10))   # 열
    a(mflo('t6'), mtc1('t6', 11), cvt_s_w(11, 11))                                                    # 행
    fconst(7, G['cu']); a(mul_s(10, 10, 7))                       # u0
    fconst(7, G['cv']); a(mul_s(11, 11, 7))                       # v0
    # 그리는 폰트의 'A' 글리프: 대문자 높이(아래y-위y)와 베이스라인(아래y)
    a(lw('t7', 8, 't8'), lhu('t2', 0, 't7'), lw('t3', 4, 't7'))
    a(addiu('t4', 'zero', 0x41), subu('t2', 't4', 't2'))
    a(sll('t4', 't2', 1), addu('t4', 't4', 't2'), sll('t4', 't4', 5), addu('t3', 't3', 't4'))
    a(lwc1(5, 0x14, 't3'), lwc1(6, 0x34, 't3'), sub_s(4, 6, 5))           # f4 = cap
    fconst(5, 1.0 / CAPK); a(mul_s(4, 4, 5))                              # s
    a(lui('t5', hi(KBUF)), addiu('t5', 't5', lo(KBUF)))
    fconst(7, G['adv']); a(mul_s(7, 7, 4), cvt_w_s_raw(7, 7), mfc1('t7', 7), sw('t7', 0, 't5'))
    a(addiu('t7', 'zero', -1), sw('t7', 4, 't5'), sw('t7', 8, 't5'), sw('t7', 12, 't5'))
    fconst(8, G['box']); a(mul_s(8, 8, 4))                                # x1
    fconst(9, G['top']); a(mul_s(9, 9, 4), add_s(9, 9, 6))                # y0
    fconst(5, G['top'] + G['box']); a(mul_s(5, 5, 4), add_s(5, 5, 6))     # y1
    for k, (fx, fy) in enumerate(((None, 9), (8, 9), (None, 5), (8, 5))):
        o = 0x10 + 16 * k
        a(sw('zero', o, 't5') if fx is None else swc1(fx, o, 't5'), swc1(fy, o + 4, 't5'), sw('zero', o + 8, 't5'), sw('zero', o + 12, 't5'))
    a(swc1(10, 0x50, 't5'), swc1(11, 0x54, 't5'))
    fconst(7, G['cu']); a(add_s(10, 10, 7), swc1(10, 0x58, 't5'))
    fconst(7, G['cv']); a(add_s(11, 11, 7), swc1(11, 0x5c, 't5'))
    a(jr('ra'), move('v0', 't5'))
    a.L('kl_none'); a(jr('ra'), move('v0', 'zero'))
    # ---- 폭 함수 실패 경로 (a0=char, t0=font)
    E['w'] = a.pc(); cnt(0)
    a(move('a3', 'ra'), move('a2', 't0'), move('a1', 'a0'), move('a0', 't0'))
    a(jal(E['klook']), NOP)
    a.br('beq', 'v0', 'zero', 'w_def'); a(NOP)
    a(jr('a3'), lw('v0', 0, 'v0'))
    a.L('w_def'); a(jr('a3'), lw('v0', 0xc, 'a2'))
    # ---- DrawChar 레코드 (s1=rec, s2=ctx, s4=char); 끝에서 밀어낸 2명령 수행
    E['d1'] = a.pc(); cnt(1)
    a(move('a3', 'ra'))
    a.br('bne', 's1', 'zero', 'd1_ret'); a(NOP)
    a(lw('a0', 0, 's2'), move('a1', 's4'), jal(E['klook']), NOP, move('s1', 'v0'))
    a.L('d1_ret'); a(cvt_w_s_raw(3, 1), mfc1('v1', 3), jr('a3'), NOP)
    # ---- DrawChar2 레코드 (s2=rec, s5=ctx, a0=char, t0 보존); 실패면 0x13a910
    E['d2'] = a.pc(); cnt(2)
    a.br('bne', 's2', 'zero', 'd2_ok'); a(NOP)
    a(move('a3', 'ra'), move('a2', 't0'), move('a1', 'a0'), lw('a0', 0, 's5'), jal(E['klook']), NOP)
    a(move('s2', 'v0'), move('t0', 'a2'), move('ra', 'a3'), move('v0', 'zero'))
    a.br('bne', 's2', 'zero', 'd2_ok'); a(NOP)
    a(j(0x13a910), NOP)
    a.L('d2_ok'); a(jr('ra'), NOP)
    # ---- 텍스처 선택: 레코드가 KBUF 면 fontk 텍스처
    for nm, rr in (('t1', 's1'), ('t2', 's2')):
        E[nm] = a.pc(); cnt(3 if nm == 't1' else 5)
        a(lui('v1', hi(KBUF)), addiu('v1', 'v1', lo(KBUF)))
        a.br('bne', rr, 'v1', nm + '_n'); a(addiu('v0', 'a0', 0x60))
        cnt(4 if nm == 't1' else 6)
        a(lui('v1', hi(FKC)), lw('v0', lo(FKC), 'v1'), jr('ra'), addiu('v0', 'v0', 0x60))
        a.L(nm + '_n'); a(jr('ra'), NOP)
    code = a.done()
    assert CAVE + len(code) <= KBUF, hex(len(code))
    return code, E

def patch(elf, nk, G):
    import edis
    d = bytearray(elf)
    def put(va, w): struct.pack_into('<I', d, edis.v2o(va), w)
    def get(va): return struct.unpack_from('<I', d, edis.v2o(va))[0]
    code, E = build(nk, G)
    o = edis.v2o(CAVE); assert d[o:o + 0x500] == bytes(0x500)
    d[o:o + len(code)] = code
    assert get(0x128764) == jr('ra') and get(0x128768) == lw('v0', 0xc, 't0')
    put(0x128764, j(E['w'])); put(0x128768, NOP)
    assert get(0x1399e4) == cvt_w_s_raw(3, 1) and get(0x1399e8) == mfc1('v1', 3), hex(get(0x1399e4))
    put(0x1399e4, jal(E['d1'])); put(0x1399e8, NOP)
    assert get(0x139a20) == jal(0x1286a0); put(0x139a20, jal(E['t1']))
    assert get(0x13a50c) == beq('s2', 'zero', (0x13a910 - 0x13a510) >> 2), hex(get(0x13a50c))
    put(0x13a50c, jal(E['d2']))
    assert get(0x13a6a8) == jal(0x1286a0); put(0x13a6a8, jal(E['t2']))
    return bytes(d), E

if __name__ == '__main__':
    import capstone, edis
    G = dict(per=32, cu=1/32, cv=16/512, adv=20.0, box=20.0, top=-17.5)
    code, E = build(1000, G)
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS64 + capstone.CS_MODE_LITTLE_ENDIAN)
    inv = {v: k for k, v in E.items()}
    for i in md.disasm(code, CAVE):
        print(('%-8s' % inv.get(i.address, '')) + '%08x: %s %s' % (i.address, i.mnemonic, i.op_str))
    p, E = patch(edis.D, 1000, G)
    print('patch ok', {k: hex(v) for k, v in E.items()}, len(code))
