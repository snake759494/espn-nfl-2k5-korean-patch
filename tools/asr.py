"""해설 클립 받아쓰기(faster-whisper) → work/asr_<name>.jsonl  (이어하기 지원)
python tools/asr.py comm [model] [k/n]
환경변수 ASR_IDS=번호목록파일(그 클립만), ASR_TAG=출력 이름 접두(기본 asr), ASR_BEAM=빔 폭(기본 1), ASR_PROMPT=0 이면 안내 문구 없음"""
import os, sys, json, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import speech
from scipy.signal import resample_poly
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def main(name, model='small.en', shard='0/1'):
    k_, n_ = (int(x) for x in shard.split('/'))
    from faster_whisper import WhisperModel
    out = os.path.join(ROOT, 'work', '%s_%s_%d.jsonl' % (os.environ.get('ASR_TAG', 'asr'), name, k_))
    ids = set(json.load(open(os.environ['ASR_IDS']))) if os.environ.get('ASR_IDS') else None
    beam = int(os.environ.get('ASR_BEAM', '1')); prompt = None if os.environ.get('ASR_PROMPT') == '0' else 'American football TV play-by-play commentary.'
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            try: done.add(json.loads(l)['i'])
            except Exception: pass
    S = speech.Speech()
    m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=max(1, 4 // n_))
    f = open(out, 'a', encoding='utf-8'); t0 = time.time(); k = 0
    for i in range(S.count(name)):
        if i in done or i % n_ != k_ or (ids is not None and i not in ids): continue
        pcm = S.pcm(name, i).astype(np.float32) / 32768
        dur = len(pcm) / speech.RATE
        a = resample_poly(pcm, 160, 441).astype(np.float32)        # 22050 → 16000
        rms = float(np.sqrt(np.mean(pcm ** 2))) if len(pcm) else 0.0
        if dur < 0.15 or rms < 1e-3:
            text = ''
        else:
            segs, _ = m.transcribe(a, language='en', beam_size=beam, vad_filter=False, condition_on_previous_text=False,
                                   initial_prompt=prompt)
            text = ' '.join(s.text.strip() for s in segs).strip()
        f.write(json.dumps({'i': i, 'dur': round(dur, 3), 'rms': round(rms, 4), 'en': text}, ensure_ascii=False) + '\n')
        k += 1
        if k % 200 == 0:
            f.flush(); el = time.time() - t0
            print('%d/%d  %.1f clips/s' % (len(done) + k, S.count(name), k / el), flush=True)
    f.close()
if __name__ == '__main__': main(*sys.argv[1:])
