"""경기 중 작은 점수판(쿼터 칸) 확인: 부팅 → 빠른 경기 → 킥오프 후 연속 캡처, 점수판 부분만 모아 work/<tag>_sb.png"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__)); import emu, flow
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def run(tag, iso=None):
    emu.start(iso or flow.ISO); time.sleep(70)
    emu.keys('start w3 start w4 x w4'); emu.keys('start w5 x w5 x w4 x w6 x w8 x'); time.sleep(70)
    shots = []
    for i in range(14):
        emu.keys('x w2'); p = os.path.join(ROOT, 'work', '%s_%02d.png' % (tag, i)); emu.shot(p); shots.append(p)
    emu.stop()
    ims = [Image.open(p).crop((560, 100, 1195, 250)) for p in shots]
    c = Image.new('RGB', (635 * 2, 150 * 7))
    for k, im in enumerate(ims): c.paste(im, ((k % 2) * 635, (k // 2) * 150))
    c.save(os.path.join(ROOT, 'work', tag + '_sb.png'))
if __name__ == '__main__': run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
