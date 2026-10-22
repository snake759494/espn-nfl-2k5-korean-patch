"""전체 빌드: 원본 ISO → 한글 ISO.
1) SLUS_209.19: 한글 출력 코드 패치 + UTF-16 문자열 제자리 번역(길이 이내)
2) FONT 묶음(8ee9eeed)에 fontk 추가, 번역된 데이터 파일들 → VC_20919/4. 끝에 덧붙이고 아카이브 표 갱신
3) VC_20919/4. 크기·ISO9660·UDF·볼륨 크기·앵커 갱신"""
import os, sys, struct, shutil, json, time
sys.path.insert(0, os.path.dirname(__file__))
import iso, isoedit, vc, codepatch, kfont, ktext, lz
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'ESPN NFL 2K5 (USA).iso')
DST = os.path.join(ROOT, 'ESPN NFL 2K5 (USA) (Korean).iso')
SEC = 2048
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def main():
    tr = ktext.Translator()
    ents = {p: (l, s) for p, l, s, r in iso.walk(SRC)}
    T = vc.table(SRC); P = vc.parts(SRC)
    byh = {e[0]: list(e) for e in T}
    def get(h): return vc.read(tuple(byh[h]), SRC, P)
    # --- 데이터 파일 ---
    new = {}
    import datafiles
    for h, fn in ({} if os.environ.get('KO_NODATA') else datafiles.HANDLERS).items():
        d2, n = fn(get(h), tr)
        if n: new[h] = d2; log('data %08x strings %d' % (h, n))
    import layout, names
    nn = 0
    for h, ty, f in ([] if os.environ.get('KO_NODATA') or os.environ.get('KO_NONAMES') else names.files()):
        d2, n = names.apply(new.get(h) or get(h), tr)
        if n: new[h] = d2; nn += n
    log('name/play strings', nn)
    nl = 0
    for h, f in ([] if os.environ.get('KO_NODATA') else layout.raw_files()):
        d2, n = layout.apply(new.get(h) or get(h), tr)
        if n: new[h] = d2; nl += n
    log('layout strings', nl)
    # --- ELF ---
    el, es = ents['SLUS_209.19']
    elf = iso.read(el, es, SRC)
    elf2, n = (elf, 0) if os.environ.get('KO_NOELF') else ktext.patch_elf(elf, tr)
    log('ELF strings', n)
    sylls = tr.syllables()
    if os.environ.get('KO_MAXSYL'): sylls = sylls[:int(os.environ['KO_MAXSYL'])]
    log('syllables', len(sylls))
    kfont.pick_cell(len(sylls)); log('cell', kfont.CELL)
    G = kfont.geometry(len(sylls))
    elf2, E = codepatch.patch(elf2, len(sylls), G)
    assert len(elf2) == len(elf)
    # --- 폰트 ---
    ff, img, th = kfont.build_fontfile(get(kfont.FONT_HASH), sylls)
    # FONT 묶음 비압축 꼬리의 문구
    import datafiles as _df
    _ch, _end = lz.chain(ff)
    _gl = tr.getter('lay')
    _tail, _k = _df.inplace(ff[_end:], _gl, [(a, b, t) for a, b, t in _df.u16_runs(ff[_end:]) if ' ' in t.strip()])
    ff = ff[:_end] + _tail; log('font tail strings', _k)
    new[kfont.FONT_HASH] = ff
    log('fontk texture %dx%d, font file %d -> %d' % (kfont.TW, th, byh[kfont.FONT_HASH][1], len(ff)))
    # --- ISO ---
    log('copy iso')
    shutil.copyfile(SRC, DST)
    l4, s4 = ents['VC_20919/4.']
    old_secs4 = (s4 + SEC - 1) // SEC
    with open(DST, 'r+b') as f:
        f.seek(el * SEC); f.write(elf2)
        # 해설 한국어 더빙(같은 길이로 제자리 교체)
        if not os.environ.get('KO_NODUB'):
            import dub
            log('dub clips', dub.patch_iso(f, DST))
            import viddub
            log('dub videos', viddub.patch_iso(f, DST))
        # 덧붙이기
        sec4 = old_secs4
        for h in sorted(new):
            d = new[h]
            f.seek((l4 + sec4) * SEC); f.write(d); f.write(bytes((-len(d)) % SEC))
            byh[h][1] = len(d); byh[h][2] = 4 * vc.PART + sec4
            sec4 += (len(d) + SEC - 1) // SEC
        # 아카이브 표 + 파트 크기
        hdr_off = ents['VC_20919/0.'][0] * SEC
        for i, e in enumerate(T):
            f.seek(hdr_off + 0x9c + 12 * i); f.write(struct.pack('<3I', *byh[e[0]]))
        f.seek(hdr_off + 0xc + 4 * 4); old = struct.unpack('<I', f.read(4))[0]
        assert old == old_secs4, (old, old_secs4)
        f.seek(hdr_off + 0xc + 4 * 4); f.write(struct.pack('<I', sec4))
        isoedit.relocate(f, DST, 'VC_20919/4.', l4, sec4 * SEC)
        # 볼륨 끝 + UDF 앵커
        nsec = l4 + sec4 + 1
        with open(SRC, 'rb') as g:
            g.seek(os.path.getsize(SRC) - SEC); avdp = bytearray(g.read(SEC))
        struct.pack_into('<I', avdp, 12, nsec - 1)
        isoedit._fix_tag(avdp, 0, struct.unpack_from('<H', avdp, 10)[0])
        f.seek((nsec - 1) * SEC); f.write(avdp)
        f.truncate(nsec * SEC)
        isoedit.set_volume_size(f, nsec)
    log('done', DST, nsec, 'sectors')
    json.dump({'syllables': len(sylls), 'elf_strings': n, 'stubs': {k: hex(v) for k, v in E.items()}},
              open(os.path.join(ROOT, 'work', 'build_report.json'), 'w'), indent=1)
if __name__ == '__main__': main()
