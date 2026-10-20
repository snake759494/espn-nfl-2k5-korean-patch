"""해설 클립 화자 특징(음높이 중앙값·MFCC 평균) 추출 → work/spk_feat.npy, 2개 군집 → work/dub_speaker.json"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import speech
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SR = speech.RATE
def f0_median(x):
    """프레임별 자기상관 피치(70~300Hz, FFT 로 한 번에), 유성 프레임 중앙값"""
    fl = 1024; hop = 512
    if len(x) < fl: return 0.0
    fr = np.lib.stride_tricks.sliding_window_view(x, fl)[::hop]
    fr = fr - fr.mean(1, keepdims=True)
    e = (fr ** 2).sum(1); fr = fr[e > 1e-3 * fl]
    if not len(fr): return 0.0
    sp = np.fft.rfft(fr, 2 * fl, axis=1)
    ac = np.fft.irfft(np.abs(sp) ** 2, axis=1)[:, :fl]
    ac /= ac[:, :1] + 1e-9
    lo, hi = SR // 300, SR // 70
    k = lo + ac[:, lo:hi].argmax(1)
    v = ac[np.arange(len(k)), k] > 0.45
    return float(np.median(SR / k[v])) if v.any() else 0.0
def mfcc_mean(x, n=13):
    from scipy.fft import rfft, dct
    fl = 512; hop = 256
    if len(x) < fl: return np.zeros(n)
    w = np.hanning(fl)
    fr = np.lib.stride_tricks.sliding_window_view(x, fl)[::hop] * w
    p = np.abs(rfft(fr, axis=1)) ** 2
    nm = 26; f = np.linspace(0, SR / 2, p.shape[1])
    mel = lambda h: 2595 * np.log10(1 + h / 700)
    pts = 700 * (10 ** (np.linspace(mel(80), mel(8000), nm + 2) / 2595) - 1)
    fb = np.zeros((nm, p.shape[1]))
    for i in range(nm):
        a, b, c = pts[i:i + 3]
        fb[i] = np.clip(np.minimum((f - a) / (b - a), (c - f) / (c - b)), 0, None)
    e = np.log(p @ fb.T + 1e-10)
    keep = p.sum(1) > np.percentile(p.sum(1), 40)              # 소리 있는 프레임만
    return dct(e[keep], norm='ortho', axis=1)[:, 1:n + 1].mean(0) if keep.any() else np.zeros(n)
def features():
    S = speech.Speech(); n = S.count('comm')
    out = np.zeros((n, 15), np.float32)
    for i in range(n):
        x = S.pcm('comm', i).astype(np.float32) / 32768
        out[i, 0] = f0_median(x); out[i, 1] = len(x) / SR; out[i, 2:] = mfcc_mean(x)
        if i % 2000 == 0: print(i, flush=True)
    np.save(os.path.join(ROOT, 'work', 'spk_feat.npy'), out)
    return out
if __name__ == '__main__':
    features()
