"""동영상(PSS) 대사 한국어 더빙: 분리한 배경음(work/pss/sep/htdemucs/<id>/no_vocals.wav) + 한국어 합성 음성 → 원래 길이 그대로 재인코딩.
대본: translation/dub/video.json {영상id: [{s, e, ko, sp}]}. 결과 동영상 바이트는 work/pss/out/<id>.pss 에 캐시."""
import os, sys, json, hashlib, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import pss, dub
from scipy.signal import resample_poly
import scipy.io.wavfile as wavfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
VOICE = {'M': 'M2', 'F': 'F2'}
def load():
    p = os.path.join(ROOT, 'translation', 'dub', 'video.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
def _wav(p, rate):
    r, x = wavfile.read(p); x = x.astype(np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    if r != rate: x = resample_poly(x, rate, r, axis=0).astype(np.float32)
    return x
def _say(text, voice, n):
    """text 를 n 샘플(48kHz) 안에 들어가게 합성."""
    t = dub.tts()
    if voice not in t._styles: t._styles[voice] = t.get_voice_style(voice)
    text = dub.ko_num(text); sp = 1.0
    for _ in range(3):
        w, _ = t.synthesize(text, voice_style=t._styles[voice], lang='ko', speed=sp, silence_duration=0.05)
        w = dub.trim(np.asarray(w, np.float32).squeeze(), 0.005)
        w = resample_poly(w, 48000, 44100).astype(np.float32)
        if len(w) <= n or sp >= 1.5: break
        sp = min(1.5, sp * len(w) / (n * 0.97))
    if len(w) > n: w = resample_poly(w, n, len(w)).astype(np.float32) if len(w) <= n * 1.15 else w[:n]
    return w
def build(vid, segs):
    d = pss.read(int(vid, 16)); pk, info, s = pss.audio(d)
    rate = info['rate']; orig = pss.decode(s, info).astype(np.float32)
    sep = os.path.join(ROOT, 'work', 'pss', 'sep', 'htdemucs', vid)
    bg = _wav(os.path.join(sep, 'no_vocals.wav'), rate); vo = _wav(os.path.join(sep, 'vocals.wav'), rate)
    n = len(orig); bg = np.pad(bg, ((0, max(0, n - len(bg))), (0, 0)))[:n]; vo = np.pad(vo, ((0, max(0, n - len(vo))), (0, 0)))[:n]
    out = bg.copy()
    segs = sorted(segs, key=lambda g: g['s'])
    for k, g in enumerate(segs):
        if not g.get('ko'): continue
        a = int(g['s'] * rate); nxt = segs[k + 1]['s'] if k + 1 < len(segs) else n / rate
        room = int(min(max(g['e'], g['s'] + 0.3) + 0.4, nxt) * rate) - a        # 끝 시각 + 0.4초까지 허용(다음 대사 전까지)
        if room <= 0: continue
        w = _say(g['ko'], VOICE.get(g.get('sp', 'M'), 'M2'), room)
        ref = vo[a:a + max(1, int((g['e'] - g['s']) * rate))].mean(1)
        rr = float(np.sqrt(np.mean(ref ** 2))) if len(ref) else 3000.0
        wr = float(np.sqrt(np.mean(w ** 2))) or 1.0
        w = w * (max(rr, 1500.0) / wr)
        out[a:a + len(w)] += w[:, None]
    out = np.clip(out, -32768, 32767).astype(np.int16)
    return pss.patch(d, pss.encode(out, info), info, pk)
def patch_iso(f, isop):
    """ISO 핸들 f 의 동영상들을 더빙본으로 제자리 교체. 반환: 교체한 영상 수"""
    import vc
    E = {e[0]: e for e in vc.table(isop)}; P = vc.parts(isop); od = os.path.join(ROOT, 'work', 'pss', 'out'); os.makedirs(od, exist_ok=True)
    n = 0
    for vid, segs in sorted(load().items()):
        if not any(g.get('ko') for g in segs): continue
        key = hashlib.md5(json.dumps(segs, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        cp = os.path.join(od, '%s_%s.pss' % (vid, key))
        if not os.path.exists(cp): open(cp, 'wb').write(build(vid, segs))
        b = open(cp, 'rb').read(); e = E[int(vid, 16)]; assert len(b) == e[1]
        f.seek(vc.iso_off(e[2], isop, P)); f.write(b); n += 1
    return n
if __name__ == '__main__':
    # 미리 만들어 두기: python tools/viddub.py [영상id]
    import iso
    for vid, segs in sorted(load().items()):
        if len(sys.argv) > 1 and vid != sys.argv[1]: continue
        b = build(vid, segs); p = os.path.join(ROOT, 'work', 'pss', 'test_%s.wav' % vid)
        pk, info, s = pss.audio(b); wavfile.write(p, info['rate'], pss.decode(s, info).astype(np.int16)); print(vid, p)
