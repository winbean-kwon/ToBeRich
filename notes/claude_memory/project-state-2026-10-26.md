---
name: project-state-2026-10-26
description: "Thesis direction as of 10-27 night — single-track reproduction/re-evaluation of published RL portfolio methods (prereg v3 committed 6f8f512); T1 DeepAries pilot+O5 done, T2 AlphaMix+ and T3 FinRL notebooks pending user runs"
metadata:
  node_type: memory
  type: project
  originSessionId: 0a7ccb26-4acc-4d42-9319-b6350d753d20
  modified: 2026-10-27T14:33:05.397Z
---

EarnHFT-style hierarchical RL crypto thesis; original returns claim failed (start-state artifact). 2026-10-27 the user rejected the narrow v2 audit as "graduation-only" and chose direction A, single track (thesis = first version of the journal paper): reproduce published RL portfolio methods with official code (O1 grades), then test whether advantage survives a unified protocol (O2: correct cost impl, rolling windows, seed distribution, daily-EW baseline). Prereg `notes/prereg_reeval_v3.md` committed 6f8f512 (only §9 budget and §1.1 T2 confirm may be filled later). Targets T1 DeepAries (CIKM'25; pilot ok, 20 min/run CPU; O5 found cost under-charged 0.021× on alternating actions, first-buy cost one step late — 4a968c4), T2 AlphaMix+ (pilot notebook replication/alphamix_pilot.ipynb, GPU), T3 FinRL ICAIF'21 (replication/finrl_t3_timing.ipynb). Key prior art: Kruthof & Müller FRL 2025 (SAC can't beat 1/N). T3 O1 done 10-28 (PPO·TD3 재현, A2C·DDPG 부분, 계보 부분 재현; notes/finrl_t3_o1_result.md); O5 T3 env cost not applied (4/4 match). T3 O2 160 runs: `sh replication/run_t3_o2.sh` (resumable, nohup+caffeinate, env in repo .t3env/ git-excluded, log .t3env/logs/o2.log) then `finrl_t3_run.py judge2`. Session scratchpad gets wiped between sessions — keep long-run envs in .t3env. finrl_start_state.ipynb on Colab stalled at 21/24 models (session limit); user to rerun. Google Drive connector works again (read results via search_files/download_file_content).

**Why:** user wants journal-acceptance quality, disliked plans that "ossify" without results — prefers acting on pilots over more planning rounds.
**How to apply:** read HANDOFF_2026-10-27.md + this; run adversarial review once per prereg, not per idea; keep [[pre-registration-rule]], [[no-inflation-independent-review]]; live bot in [[live-bot-setup]].

**2026-10-29 T3 O2 완료** (notes/finrl_t3_o2_result.md, 01d73f2): 유지 0, 소실 2(A2C·PPO), 불확정 2(DDPG·TD3). 탐색적 진단: DDPG/TD3 시드로 정해지는 고정 비중, PPO 초기화 분포와 구별 안 됨, A2C 학습됐으나 deterministic=False 회전율 비용. deterministic=True 확인은 별도 사전 등록 필요(모델 미저장).
- 2026-10-29: T3 O6(결정적 예측) 완료 97c75c2 — E1 60/60, E2 PPO 미학습 지지, E3 A2C 불확정/PPO 소실(모두 차이 작음). T2 O1 노트북 94a4ac6(실행기 e2cfe8f) 사용자 Colab 실행 대기 → 끝나면 Drive data/alphamix_t2/t2_o1_bundle.zip 받아 `alphamix_t2.py judge1`. T1 O1 맥에서 실행 중(.t1env/logs/t1.log).
- 2026-10-30: T1 DeepAries O1 **미재현** (선택 시드 2 CAGR 5.04/MDD −22.5, R2 2/10), notes/deeparies_o1_result.md aa4873f. O2 실행 안 함(사전 규칙). 맥 1회 2–4시간(Colab 20분과 다름). 논문 지수 6.15% 불일치·README 10 epoch 단서 = 후속 후보(사전 등록 필요). 맥 유휴.
- 2026-10-30 T2 AlphaMix+ O1 = 미재현(R1 1/3, R2 0/3; eaebe7c 데이터, 1de9121 노트). O2 안 함. 민감도: vbest epoch면 '재현'(R2 +0.03%p), 매수후보유 market average면 '부분 재현'. 학습 전(e0)=29칸 균등과 일치, 학습 후 평균 비슷(탐색적). 일간수익 점검은 zip(Drive 6.8MB, 커넥터로 못 받음) 확보 후.
- 2026-10-30 계획 확정 notes/plan_2026-10-30.md(반박 심사 반영): 집필 우선(thesis/OUTLINE_KR.md), 저자 문의 초안 notes/author_inquiry_draft.md(사용자 확인 전 발송 금지), 다음 = 1/N 근접 정적 분석 + CI·MDE 표. TOST 제외. DeepAries 10ep는 사용자 결정.
- 2026-10-30 T1 변형 E(10 epoch, Colab T4) = 미재현(e10 선택 6.38%, R2 3/10; e1 9.87%, 4/10), notes/deeparies_e10_result.md. 다음: EarnMore 정적 읽기(.t4env/EarnMore, 수익식 이중 축소 의심·T=0.1) → 사전 등록, 깔때기 표, 원인 실험.
- 2026-10-30 실계좌 래칫 수정 커밋 ee88e7a(로컬만, 푸시는 자동 분류기가 Production Deploy로 거부 → 사용자가 직접 푸시·서버 pull 필요). 상위 n종목 집중으로 총 노출 맞춤, 대시보드 경고는 노출 괴리 3%. notes/live_min_lot_rule.md.
- 2026-11-01 확장 방향 탐색(자산 목록·문헌 공백·반박 심사 에이전트): 졸업 = 재현 3편+코드 동적 감사 + Lo(2008) 정적/동적 분해(기술적 분석, 맹검 아님 — e0≈1/N 이미 봄). 투고판 유일 후보 = 56편 중 코드 공개 논문 '서술 비용 vs 구현 비용' 대조(사전 등록·2차 코더 κ), 착수 전 Yao&Zheng 2606.08285·Kong 2602.14233 본문 확인 필요. 기각: 비용 on/off 재학습(자명), 크립토 생존편향(Ammann 외 선점), 고정비중 '신규 제안'(Lo 2008). MLRC 2026 마감 지남. 반박 총평: 졸업 충분, TMLR엔 약함. 사용자 결정 대기.
- 2026-11-02 CI·MDE 사전 등록 notes/prereg_stat_power.md 커밋 919be84(F=FinRL O2 주, D·D′·A 보조, LW2008 b=5, 보정 점검 먼저). 저자 문의 초안 문체 수정(미발송). 다음 = replication/stat_power/run.py 작성·실행. 2026-11-03 계정 전환용 인수인계 HANDOFF_2026-11-03.md 작성.
- 2026-11-02 반박 심사: 919be84판 **실행 보류**(notes/review_prereg_stat_power.md) — DeepAries 간격 서술 오류(시드별 보유기간 → expand() 사용), O2 보조 통계 기존 공개 미기재, MDE≤δ 범주는 power approach → 비우월성 상한(10-30 계획의 'TOST 제외'와 충돌, 사용자 결정 필요), δ=원 논문 우위 3.17%p 고정, 보정 점검·알고리즘 단위 집계 보완. 다음 = v2 개정 → 재심사 → run.py.
