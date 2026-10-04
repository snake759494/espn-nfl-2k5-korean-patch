"""번역 데이터 → 게임 UTF-16.
번역: translation/ko/<묶음>.json {id: 한국어} + 원문 묶음 work/batches/<묶음>.json [{id, en, max, src}]
수동 보정: translation/fix/*.json {원문: 번역 | null}
한글 음절은 0xE000+순번(자주 쓰는 순), 나머지는 그대로(UTF-16)."""
import os, sys, json, glob, struct, re
sys.path.insert(0, os.path.dirname(__file__)); import wstrs
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TR = os.path.join(ROOT, 'translation')
KBASE = 0xE000
SUBST = {'·': '.', '…': '...', '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-', '　': ' '}
def is_syl(ch): return 0xAC00 <= ord(ch) <= 0xD7A3

SCOPES = {'elf': ('elf_', 'elfx_', 'elfa_', 'elft_'), 'manu': ('manu_',), 'triv': ('triv_',), 'lay': ('lay_',), 'nm': ('nm_',), 'drct': ('drct_',), 'abbr': ('abbr_',)}
def load_map(prefixes=None):
    m = {}
    for bp in sorted(glob.glob(os.path.join(ROOT, 'work', 'batches', '*.json'))):
        name = os.path.splitext(os.path.basename(bp))[0]
        if prefixes and not name.startswith(prefixes): continue
        kp = os.path.join(TR, 'ko', name + '.json')
        if not os.path.exists(kp): continue
        K = json.load(open(kp, encoding='utf-8'))
        for it in json.load(open(bp, encoding='utf-8')):
            v = K.get(str(it['id']))
            if v and v != it['en']: m[it['en']] = v
    for fp in sorted(glob.glob(os.path.join(TR, 'fix', '*.json'))):
        for k, v in json.load(open(fp, encoding='utf-8')).items():
            if v is None: m.pop(k, None)
            else: m[k] = v
    return m
NAME2 = re.compile(r"([A-Z][A-Za-z.'\-]+) ([A-Z][A-Za-z.'\-]+(?: Jr\.)?)")

class Translator:
    def __init__(self, extra_text=()):
        self.maps = {sc: load_map(px) for sc, px in SCOPES.items()}
        used = {}
        for mp in self.maps.values():
            for v in mp.values():
                for ch in v:
                    if is_syl(ch): used[ch] = used.get(ch, 0) + 1
        for v in extra_text:
            for ch in v:
                if is_syl(ch): used[ch] = used.get(ch, 0) + 1
        self.sylls = sorted(used, key=lambda c: (-used[c], c))
        self.code = {s: chr(KBASE + i) for i, s in enumerate(self.sylls)}
    def syllables(self): return self.sylls
    def enc(self, s):
        out = []
        for ch in s:
            ch = SUBST.get(ch, ch)
            for c in ch:
                if is_syl(c): out.append(self.code[c])
                elif ord(c) < 0x7f or c in '®™©é': out.append(c)
                else: raise ValueError(f'unencodable {c!r} in {s!r}')
        return ''.join(out)
    def compose_name(self, en):
        """'First Last' 를 로스터 번역 조각으로 조합."""
        m = NAME2.fullmatch(en)
        if not m: return None
        nm = self.maps['nm']
        a, b = nm.get(m.group(1)), nm.get(m.group(2))
        if a and b: return a + ' ' + b
        return None
    def getter(self, scope, names=False):
        mp = self.maps[scope]
        def g(en):
            v = mp.get(en)
            if v is None and names: v = self.compose_name(en)
            return None if v is None else self.enc(v)
        return g
    def get(self, en):          # 호환용(ELF 범위)
        return self.getter('elf')(en)

def elf_strings(elf):
    """ELF 데이터 세그먼트의 UTF-16 문자열 (파일 오프셋, 문자열, 최대 글자수)."""
    import edis
    out = []
    for va, off, fs, ms in edis.SEG:
        if va < 0xa38580: continue          # 코드 세그먼트 제외
        seg = elf[off:off + fs]
        for o, s in wstrs.find(seg, 2):
            # 다음 문자열 시작 전까지(0 패딩)가 여유 칸
            e = o + 2 * len(s)
            k = e
            while k + 2 <= len(seg) and seg[k:k + 2] == b'\0\0': k += 2
            room = (k - o) // 2 - 1          # 종결 0 한 칸 남김
            # 4바이트 정렬 다음 데이터를 침범하지 않도록: 원래 문자열 끝 이후 정렬 경계까지만
            limit = ((e + 2 + 3) // 4 * 4 - o) // 2 - 1
            out.append((off + o, s, max(len(s), min(room, limit))))
    return out

def playset():
    out = set()
    for bp in glob.glob(os.path.join(ROOT, 'work', 'batches', 'nm_play_*.json')):
        out |= {it['en'] for it in json.load(open(bp, encoding='utf-8'))}
    return out
def patch_elf(elf, tr, allow=None):
    g0, gn, PS = tr.getter('elf'), tr.getter('nm'), playset()
    def g(s):
        if s in PS:                       # 작전명은 플레이북과 같은 번역(이름 검색 일치)
            v = gn(s)
            if v is not None: return v
        return g0(s)
    d = bytearray(elf); n = 0
    for o, s, mx in elf_strings(elf):
        if allow and not allow(s): continue
        v = g(s)
        if v is None: continue
        if len(v) > mx:
            print('  [too long]', repr(s), len(v), '>', mx); continue
        b = v.encode('utf-16-le')
        d[o:o + 2 * len(s) + 2] = bytes(2 * len(s) + 2)
        d[o:o + len(b)] = b
        n += 1
    return bytes(d), n
