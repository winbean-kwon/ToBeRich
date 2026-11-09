# 서버 노트북(GTX 1650)에서 PPN·RAT F4·F5 측정 — 실행 지침 (2026-11-07)

이 문서는 서버 노트북(DESKTOP-U6SI9TA)에서 도는 Claude 세션이 이어받아 실행하기 위한 것이다. 맥 세션이 작성했다. **먼저 `CLAUDE.md`, 이 문서, `notes/funnel_protocol.md`, `notes/funnel_f4_ppn.md`(특히 개정 기록 4·5와 실행 계정 변경), `notes/funnel_f4_rat.md`(개정 기록 2), `replication/funnel_f4_ppn.ipynb`, `replication/funnel_f4_rat.ipynb`를 읽는다.** Claude 메모리 백업은 `notes/claude_memory/`에 있다.

## 0. 이 기기에서 지킬 것
- 사용자와는 한국어로, 직설적으로 대화한다. 부풀리지 않는다.
- **사전 등록:** 판정 식·기준·상한·스텝·배치는 이미 고정돼 있다. 결과를 본 뒤 바꾸지 않는다. 바꿔야 할 게 생기면 측정 전에 개정 기록을 쓰고 커밋한다. 개정 기록에는 경위를 적는다.
- **성과 비노출:** `smoke*.log`, `programlog`, `train_summary.csv`, 모델 파일, RAT의 `S_smoke.log`를 열지 않는다. 화면과 보고에는 설치 결과, 시간 이벤트, traceback만 쓴다. 시간 기록 파일(`times_*.jsonl` 등)은 열어도 된다.
- **봇 폴더를 건드리지 않는다.** 실계좌 봇은 기존 저장소 폴더에서 `main`을 pull해 재시작한다. 재현 작업은 **WSL2 안에 따로 clone한 저장소**에서 한다. 봇 폴더의 파일을 바꾸거나 브랜치를 바꾸지 않는다. 봇을 멈춰야 하면(메모리 부족 등) 사용자에게 먼저 묻는다. 사용자는 봇 우선순위가 낮다고 했지만, 멈추는 결정은 사용자가 한다.
- `paper/`, `README.md`, `results/`, `submissions/`는 사용자 파일이다. 편집하지 않는다.
- 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`를 넣는다. 작업 브랜치는 `audit-fix-1004`다. 푸시 전에 반드시 `git pull --rebase origin audit-fix-1004`를 한다. 맥에서도 MARS 기록을 커밋하기 때문이다. 푸시는 `git push origin audit-fix-1004 && git push origin audit-fix-1004:main`로 한다. main에 푸시하면 봇이 pull해 재시작한다. 문서만 바뀌므로 동작에는 영향이 없다.
- 맥의 MARS 본 실행(`data/mars_t4/`)은 이 기기와 무관하다. 손대지 않는다.

## 1. 사전 확인(측정 전)
1. **반박 검토:** 별도 에이전트(심사자·반박 역할)에게 PPN 개정 기록 5와 RAT 개정 기록 2를 검토시킨다. 장치 추가가 사전 등록 취지에 맞는지, 채택 규칙에 결과 고르기 여지가 있는지, GTX 1650 측정이 F5 판정에 갖는 의미를 묻는다. 반론을 사용자에게 그대로 보고한다. 개정이 필요하면 **측정 전에** 고치고 커밋한다.
2. **자원:** C 드라이브 여유 공간이 15GB 이상이어야 한다(WSL Ubuntu, conda 환경 2개, CUDA 10.0 약 3GB, 데이터). 이 기기는 RAM 8GB이고, 사용자가 확인했을 때 이미 89% 사용 중이었다. WSL2는 기본으로 RAM의 절반까지 쓴다. 메모리 상황을 보고, 부족하면 사용자에게 무엇을 닫을지 묻는다.
3. **Colab 진행 확인:** 사용자가 다른 Google 계정으로 Colab PPN을 이미 돌리고 있는지 묻는다. 둘 다 돌면 채택 규칙(먼저 끝난 쪽)이 적용된다.

## 2. 환경(사용자 조작 포함)
1. **NVIDIA 드라이버 갱신(사용자):** 현재 드라이버는 457.49(2020-11)라 WSL2에서 CUDA를 쓸 수 없다. NVIDIA 사이트나 GeForce Experience에서 GTX 1650용 최신 드라이버를 설치하고 재시작한다. 봇도 같이 멈춘다.
2. **WSL2 설치(사용자, 관리자 PowerShell):** `wsl --install -d Ubuntu-22.04` 후 재시작하고 사용자 계정을 만든다. Windows 10 22H2(빌드 19045)는 WSL2 GPU를 지원한다.
3. **WSL 안에서 확인:** `nvidia-smi`에 GTX 1650이 보여야 한다. 안 보이면 드라이버 단계를 다시 한다. WSL에서는 리눅스용 드라이버를 설치하지 않는다(Windows 드라이버를 그대로 쓴다).
4. **저장소:** WSL 안에서 `git clone https://github.com/winbean-kwon/ToBeRich.git ~/ToBeRich && cd ~/ToBeRich && git checkout audit-fix-1004`를 실행한다. 푸시 권한(gh 로그인이나 토큰)은 사용자에게 받는다.
5. **긴 실행:** `tmux`(또는 `nohup`) 안에서 돌린다. SSH나 창이 끊겨도 실행이 계속돼야 한다. 노트북의 절전·화면 꺼짐 설정이 실행을 멈추지 않는지 사용자와 확인한다.

## 3. 이식 스크립트(측정 전 커밋)
`replication/funnel_f4_ppn_local.py`와 `replication/funnel_f4_rat_local.py`를 만든다. 원칙은 **노트북 칸의 코드를 그대로 옮기고, 아래만 바꾸는 것**이다.
- `google.colab` 드라이브 마운트를 제거한다. `OUT`은 `~/ToBeRich/data/funnel/ppn_gtx1650`(RAT은 `rat_gtx1650`)로 바꾼다. 이 경로는 `.gitignore`에 들어 있다.
- `/content` 경로는 `~/f4work`(저장소 밖)로 바꾼다. `%%bash` 칸은 `bash -c`나 별도 `.sh` 파일로 옮긴다. 설치 명령, 버전 고정, 해시 확인은 그대로 둔다.
- 장치 판정은 `HAS_T4` 대신 `HAS_GPU = 'GTX 1650' in nvidia-smi -L`로 한다.
  - PPN은 `DEVICE = 'gpu' if (HAS_GPU and TF_GPU) else 중단`으로 한다. GPU가 아니면 **S와 P 모두 시작하지 않고 멈춘다**(개정 5).
  - RAT은 GPU 시험이 실패하면 멈춘다(개정 2). 노트북 CPU로는 재지 않는다.
- 장치 표기 문자열은 `'T4'` 대신 `'GTX 1650(노트북)'`으로 바꾼다.
- 데이터는 `gdown`으로 받고, 해시 확인 줄을 그대로 둔다. PPN은 `40829bc8b7730f64`로 시작해야 하고, RAT은 첫 다운로드 해시를 기록한다.
- 측정 함수, 상한(S 3시간, P 4시간), 환산식(`A=(startup+100×block+tail+bt×94/82)/3600` 등), 재개(ckpt) 로직, 5분 진행 표시, 판정 칸은 바꾸지 않는다.
- 커밋 메시지에 "prereg(funnel): PPN·RAT 로컬 이식(경로·장치만 변경), 측정 전"처럼 적는다. 노트북과의 차이 목록을 `notes/funnel_f4_ppn.md` 개정 기록 5 아래에 한 단락으로 덧붙인다.

## 4. 실행 순서
1. **PPN:** 설치, 관문(`python 2.7`, `tf 1.15.0`, `import main ok`, `gpu True`), 데이터, S, P, 판정 순으로 진행한다.
   - GPU 메모리 부족(OOM)이면 설정을 바꾸지 않고 개정 5대로 기록한 뒤 멈춘다.
   - S가 오류로 실패하면 traceback을 사용자에게 보고한다. 설치·실행 오류나 끊김일 때만 다시 돌린다(측정 1회 원칙).
2. **결과 기록:** 판정 JSON(`f5_result.json`)을 `notes/funnel_f4_ppn.md`의 "## 3. 결과"에 적는다.
   - 순서는 사전 판정 → 냉정한 해석 → 한계다.
   - 장치, 시도 번호, Colab 시도 합산, 대상 예산(8시간) 사용량을 함께 적는다.
   - 결과 파일 자체는 커밋하지 않는다.
3. **F5 통과(A ≤ 10)면** 멈추고 사용자에게 보고한다. F7 사전 등록은 사용자와 정한다.
4. **RAT:** PPN의 F5 결과가 나온 뒤 같은 방식으로 실행한다. 설치(Python 3.7, torch 0.4.1.post2 cu92), 관문(CUDA 시험), 데이터, S, 판정 순이다.
5. 마감은 F7 시작 11-10, 정적 층 11-12다. 전체 F4 예산은 40시간이고, 11-24에 멈춘다(프로토콜).

## 5. 보고
사용자에게는 짧게 쓴다. 사전 판정을 먼저 쓰고, 그다음 해석, 한계 순으로 쓴다. "핵심 증거" 같은 과장은 쓰지 않는다. 새 주장이나 다음 방향은 보고 전에 반박 에이전트로 검증하고, 그 반론을 함께 적는다.

## 6. RAT F7 실행(2026-11-09 추가, 맥 세션 작성)
사전 등록은 `notes/funnel_f7_rat_prereg.md`(확정)이다. 먼저 이 문서를 읽는다. 장치는 이 노트북의 GTX 1650이고, 사용자가 정했다.
1. `git pull --rebase origin audit-fix-1004`.
2. WSL 안에서 F4 환경(`~/f4work`)이 그대로 있는지 확인한다. 스크립트가 main.py와 Data.db의 해시를 검사한다.
3. **점검:** `python3 replication/funnel_f7_rat_local.py --check`. 출력 JSON에서 `check_status: ok`, `missing_events: []`, `ucrp_input_saved: true`여야 한다. 실패하면 traceback만 보고하고 멈춘다. 고쳐야 하면 성과를 보기 전에 사전 등록 문서에 경위를 적고 커밋한다.
4. **본 실행:** tmux 안에서 `python3 replication/funnel_f7_rat_local.py`. 순서는 P1→P5, 그다음 R1→R5다. P는 실행마다 약 4.5시간, R은 약 2.8시간 걸린다. 다시 시작하면 끝난 실행은 건너뛴다.
5. **열지 않는 것:** `data/funnel/rat_f7_gtx1650/` 안의 `train_summary.csv`, `final_summary.csv`, `stdout.*.log`, 모델 파일. 진행 상황은 `done.json`, `attempts.jsonl`, `times.*.jsonl`만 보고 확인한다.
6. **판정:** P 5회가 끝나면(또는 11-24에) **사용자에게 먼저 알리고**, 사용자가 승인하면 `python3 replication/funnel_f7_rat_judge.py ~/ToBeRich/data/funnel/rat_f7_gtx1650`을 한 번 돌린다. 결과는 사전 판정, 냉정한 해석, 한계 순으로 사전 등록 문서 아래에 적는다. 보고하기 전에 반박 에이전트로 검토한다. R은 끝나는 대로 병기한다.
7. 동시 실행 금지: 이 실행이 도는 동안에는 이 GPU에서 다른 측정을 돌리지 않는다. Ensemble F7 같은 CPU 작업은 사용자와 정한 뒤에 돌린다.
