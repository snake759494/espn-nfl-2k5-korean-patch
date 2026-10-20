# 빌드
준비물: Python 3.11+ (numpy, Pillow, capstone), 원본 ISO, `NanumSquareNeo-cBd.ttf`, xdelta3

1. 저장소 루트에 원본 `ESPN NFL 2K5 (USA).iso` 와 `NanumSquareNeo-cBd.ttf` 를 둡니다.
2. `python tools/prepare.py` — 원본에서 파일 추출(extract/)과 원문 번역 묶음(work/batches)을 다시 만듭니다.
3. `python tools/build.py` — `ESPN NFL 2K5 (USA) (Korean).iso` 생성.
4. `xdelta3 -e -9 -S none -A -s "ESPN NFL 2K5 (USA).iso" "ESPN NFL 2K5 (USA) (Korean).iso" ESPN_NFL_2K5_KO_v1.0.xdelta`

검사: `python tools/audit.py`(한글 ISO 전수조사 → work/audit.json).
검증용 에뮬레이터 조작: `tools/emu.py`(휴대용 PCSX2, 환경변수 `NFL_EMU`), `tools/flow.py`(메뉴→경기 진입 자동 진행·화면 저장).
번역 추가: 원문 묶음은 `work/batches/*.json`, 번역은 `translation/ko/<묶음>.json`({번호: 한국어}), 새 묶음을 만든 뒤 `python tools/mkindex.py` 로 위치 색인 생성.
