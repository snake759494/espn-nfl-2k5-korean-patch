"""공용 한글 폰트 리소스 'fontk' 생성 + FONT 묶음(8ee9eeed)에 끼워 넣기.
font1 리소스의 머리(0x100)를 본떠 이름 fontk, 범위 0xE000~0xE000+N-1, 글리프 레코드 N개, PSMT4 텍스처(1024 x H).
레코드 좌표는 베이스라인 기준(y 음수=위)이고, 스텁(codepatch)이 그리는 폰트의 어센트/베이스라인으로 변환한다."""
import os, sys, struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__)); import lz
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT = os.path.join(ROOT, os.environ.get('KO_FONT', 'NanumSquareNeo-cBd.ttf'))
CELL = int(os.environ.get('KO_CELL', 16))     # 텍스처 칸(텍셀) - pick_cell 로 자동 조정
PX = int(os.environ.get('KO_PX', 15))         # 글꼴 크기 (CELL-1)
ASC = 18                                      # fontk 어센트 (스텁의 크기 기준)
TOP = -17.5                                   # 글리프 상자 위(베이스라인 기준, 대문자 16 기준)
BOX = 20.0                                    # 글리프 상자 크기(대문자 16 기준 단위)
ADV = 20.0                                    # 한 글자 진행폭(대문자 16 기준)
TW = int(os.environ.get('KO_TW', 512))
KBASE = 0xE000
FONT_HASH = 0x8ee9eeed

def _tex0(tw, th, pixbytes, ref):
    v = ref & ~((0x3fff) | (0x3f << 14) | (0xf << 26) | (0xf << 30) | (0x3fff << 37))
    v |= (tw // 64) << 14 | (tw.bit_length() - 1) << 26 | (th.bit_length() - 1) << 30 | (pixbytes // 256) << 37
    return v

def render(sylls):
    font = ImageFont.truetype(FONT, PX)
    per = TW // CELL
    rows = (len(sylls) + per - 1) // per
    th = 1
    while th < rows * CELL: th *= 2
    assert th <= 512, f'texture too tall: {len(sylls)} syllables'
    img = np.zeros((th, TW), np.uint8)
    cells = []
    for i, s in enumerate(sylls):
        x, y = (i % per) * CELL, (i // per) * CELL
        im = Image.new('L', (CELL, CELL), 0)
        dr = ImageDraw.Draw(im)
        bb = dr.textbbox((0, 0), '한', font=font)
        ox = (CELL - (bb[2] - bb[0])) // 2 - bb[0]
        oy = (CELL - (bb[3] - bb[1])) // 2 - bb[1]
        dr.text((ox, oy), s, font=font, fill=255)
        img[y:y + CELL, x:x + CELL] = np.round(np.array(im).astype(int) * 15 / 255).astype(np.uint8)
        cells.append((x, y))
    return img, cells, th

def build_resource(sylls, font1_res):
    """font1 압축 리소스(헤더 0x20 포함)를 본떠 fontk 압축 리소스 바이트."""
    A, B1, C1, F, D = struct.unpack_from('<5I', font1_res, 4)
    u1, _ = lz.decompress(font1_res[0x20:0x20 + A])
    n = len(sylls)
    img, cells, th = render(sylls)
    hdr = bytearray(u1[:0x100])
    hdr[0x20:0x2c] = 'fontk\0'.encode('utf-16-le')
    struct.pack_into('<HH', hdr, 0x30, KBASE, KBASE)
    struct.pack_into('<5i', hdr, 0x3c, int(ADV), 24, ASC, -6, 22)
    pixbytes = TW * th // 2
    tex0 = _tex0(TW, th, pixbytes, struct.unpack_from('<Q', u1, 0x50)[0])
    struct.pack_into('<Q', hdr, 0x50, tex0)
    struct.pack_into('<HH', hdr, 0x7c, TW, th)          # 업로드 폭·높이
    struct.pack_into('<HHI', hdr, 0xf0, KBASE, KBASE, 0x0d)
    recs = struct.pack('<I', int(ADV)) + bytes([0xff]) * 12 + bytes(64) + bytes(16)   # 자리표시 1개(스텁이 직접 계산)
    body = hdr + recs
    body += b'\xff' * ((-len(body)) % 16)
    B = len(body)
    if os.environ.get('KO_SOLID'): img[:] = 15
    flat = img.reshape(-1)
    pix = (flat[0::2] | (flat[1::2] << 4)).astype(np.uint8).tobytes()
    pal = u1[B1 + (C1 - 64):B1 + C1]
    u = bytes(body) + pix + pal
    C = len(pix) + 64
    comp = lz.compress(u, nb=12)
    chk, _ = lz.decompress(comp); assert chk == u
    comp += bytes((-len(comp)) % 16)
    res = b'FONT' + struct.pack('<5I', len(comp), B, C, 0xfeedbeef, D) + bytes(8) + comp
    return res, img, th

def build_fontfile(orig, sylls):
    """FONT 묶음 파일: font9 다음에 fontk 를 끼운다."""
    ch, end = lz.chain(orig)
    assert [c[1] for c in ch[:9]] == [b'FONT'] * 9
    o9 = ch[8][0] + 0x20 + ch[8][2]
    res, img, th = build_resource(sylls, orig[ch[0][0]:ch[0][0] + 0x20 + ch[0][2]])
    return orig[:o9] + res + orig[o9:], img, th

def geometry(n):
    per = TW // CELL
    rows = (n + per - 1) // per
    th = 1
    while th < rows * CELL: th *= 2
    return dict(per=per, cu=CELL / TW, cv=CELL / th, adv=ADV, box=BOX, top=TOP)

def pick_cell(n):
    """512x512 에 n 자가 들어가는 가장 큰 칸."""
    global CELL, PX
    for c in (16, 15, 14, 13):
        per = TW // c
        if ((n + per - 1) // per) * c <= 512:
            CELL, PX = c, c - 1
            return c
    raise ValueError(f'too many syllables {n}')
