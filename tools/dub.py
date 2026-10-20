"""해설 한국어 더빙: Supertonic 3 합성 → 원본 클립 길이에 맞춤 → PS2 ADPCM 인코딩.
클립 바이트 길이를 원본과 같게 맞춰 해설 스트림의 같은 자리에 덮어쓴다(색인 표·ISO 크기 불변).
대본: translation/dub/*.json {클립번호: 한국어}, 화자: work/dub_speaker.json {클립번호: 'A'|'B'}"""
import os, sys, json, glob, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import speech, vagfast
from scipy.signal import resample_poly
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
VOICES = {'A': os.environ.get('DUB_VOICE_A', 'M1'), 'B': os.environ.get('DUB_VOICE_B', 'M3')}   # A=캐스터, B=해설위원
CACHE = os.path.join(ROOT, 'work', 'dub_cache')
_tts = None
def tts():
    global _tts
    if _tts is None:
        import supertonic
        _tts = supertonic.TTS(); _tts._styles = {}
    return _tts
def synth(text, voice, speed):
    t = tts()
    if voice not in t._styles: t._styles[voice] = t.get_voice_style(voice)
    w, _ = t.synthesize(text, voice_style=t._styles[voice], lang='ko', speed=speed, silence_duration=0.05)
    w = np.asarray(w, np.float32).squeeze()
    return resample_poly(w, 1, 2).astype(np.float32)             # 44100 → 22050
def trim(w, thr=0.01):
    idx = np.where(np.abs(w) > thr)[0]
    return w[idx[0]:idx[-1] + 1] if len(idx) else w[:0]
def fit(text, voice, n_samples, ref_rms):
    """n_samples 안에 들어가도록 속도를 고르고, 남으면 뒤를 무음으로 채움."""
    target = n_samples / speech.RATE
    w = trim(synth(text, voice, 1.05))
    if len(w) > n_samples * 0.97:
        sp = min(1.6, 1.05 * len(w) / (n_samples * 0.95))
        w = trim(synth(text, voice, sp))
    if len(w) > n_samples:                                         # 그래도 넘치면 리샘플로 압축(최대 1.2배)
        r = len(w) / n_samples
        if r <= 1.2: w = resample_poly(w, n_samples, len(w)).astype(np.float32)
        else: w = resample_poly(w, int(n_samples * 1.2), len(w)).astype(np.float32)[:n_samples]
    rms = float(np.sqrt(np.mean(w ** 2))) if len(w) else 1.0
    if rms > 0: w = w * (ref_rms / rms)
    fade = min(64, len(w) // 4)
    if fade: w[-fade:] *= np.linspace(1, 0, fade)
    out = np.zeros(n_samples, np.float32); out[:len(w)] = w[:n_samples]
    return np.clip(out * 32767, -32768, 32767).astype(np.int16)
def load_script():
    sc = {}
    for fp in sorted(glob.glob(os.path.join(ROOT, 'translation', 'dub', '*.json'))):
        for k, v in json.load(open(fp, encoding='utf-8')).items():
            if v: sc[int(k)] = v
    return sc
def load_speaker():
    p = os.path.join(ROOT, 'work', 'dub_speaker.json')
    return {int(k): v for k, v in json.load(open(p)).items()} if os.path.exists(p) else {}
_D = '영일이삼사오육칠팔구'
def _sino(n):
    if n == 0: return '영'
    out = ''
    for v, u in ((10000, '만'), (1000, '천'), (100, '백'), (10, '십')):
        q, n = divmod(n, v)
        if q: out += ('' if q == 1 else _sino(q)) + u
    return out + (_D[n] if n else '')
def ko_num(text):
    """합성기가 아라비아 숫자를 제대로 못 읽어서 한자어 수사로 바꾼다(콤마 숫자 포함)."""
    import re
    return re.sub(r'\d[\d,]*', lambda m: _sino(int(m.group().replace(',', ''))), text)
def clip_bytes(S, i, text, voice):
    """더빙된 클립 ADPCM 바이트(원본과 같은 길이). 결과는 캐시."""
    import hashlib
    text = ko_num(text)
    raw = S.raw('comm', i)
    key = hashlib.md5(('%d|%s|%s|%d' % (i, text, voice, len(raw))).encode()).hexdigest()
    cp = os.path.join(CACHE, key + '.vag')
    if os.path.exists(cp): return open(cp, 'rb').read()
    ref = S.pcm('comm', i).astype(np.float32) / 32768
    ref_rms = float(np.sqrt(np.mean(ref ** 2))) if len(ref) else 0.1
    n = len(raw) // 16 * 28
    pcm = fit(text, voice, n, ref_rms)
    b = vagfast.encode(pcm)
    assert len(b) == len(raw), (len(b), len(raw))
    os.makedirs(CACHE, exist_ok=True); open(cp, 'wb').write(b)
    return b
def patch_iso(f, isop, S=None):
    """ISO 파일 핸들 f(쓰기)에 더빙 클립을 제자리로 덮어쓴다. 반환: 교체 수"""
    import vc
    S = S or speech.Speech(isop)
    sc = load_script(); spk = load_speaker()
    h, size, sec = S.ent['comm']; off = S.tables['comm'][1]
    base = vc.iso_off(sec, isop, S.P)
    n = 0
    for i, text in sorted(sc.items()):
        b = clip_bytes(S, i, text, VOICES[spk.get(i, 'A')])
        f.seek(base + int(off[i])); f.write(b); n += 1
    return n
