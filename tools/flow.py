"""검증 흐름: 부팅 → VIP 생성 → 빠른 경기 → 경기 진입. 화면을 work/<tag>_N.png 로 저장하고 에뮬레이터 종료."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__)); import emu
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ISO = os.path.join(ROOT, 'ESPN NFL 2K5 (USA) (Korean).iso')
def run(tag, game_wait=(45, 25, 25), keep=False):
    emu.start(ISO); time.sleep(70)
    shots = []
    def sh(n):
        p = os.path.join(ROOT, 'work', f'{tag}_{n}.png'); emu.shot(p); shots.append(p)
    emu.keys('start w3 start w4'); sh(1)               # 메인 메뉴 + VIP 팝업
    emu.keys('x w4'); emu.keys('start w5'); sh(2)      # 이름 → 응원 팀
    emu.keys('x w5'); sh(3)                            # 저장 여부 팝업
    emu.keys('x w4'); emu.keys('x w6'); sh(4)          # 빠른 경기 → 팀 선택
    emu.keys('x w8'); sh(5)                            # 코치 매치업
    emu.keys('x')
    for i, w in enumerate(game_wait):
        time.sleep(w); sh(6 + i)
    if not keep: emu.stop()
    return shots
if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'f')
