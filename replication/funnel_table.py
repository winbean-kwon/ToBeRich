# -*- coding: utf-8 -*-
# 재현 깔때기 표(프로토콜 notes/funnel_protocol.md 2장): 논문마다 첫 탈락 단계만 집계하고, 표본(S56·S-Q·보충·T1~T4)을 나눠 센다.
# 입력: notes/lit/f1/f1_status.csv(F1), notes/lit/f1/static_layer.csv(F0·F2·F6·F3), 아래 RUN(F4·F5·F7, 노트 출처 병기).
# 출력: notes/lit/f1/funnel_table.csv, 화면 요약. 재현율 한 수치로 합치지 않는다.
import csv, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
F1 = list(csv.DictReader(open(ROOT / 'notes/lit/f1/f1_status.csv')))
ST = {r['id']: r for r in csv.DictReader(open(ROOT / 'notes/lit/f1/static_layer.csv'))}

# 실행 층 결과(각 노트의 판정 그대로). F7 결과는 판정 후 채운다.
RUN = {
    'P24-01': ('F5', '한도 초과', 'A=32.26h(T4)', 'notes/funnel_f4_earnmore.md'),
    'W22_PPN': ('F5', '한도 초과', 'A_lb=101.8h(T4, 하한)', 'notes/funnel_f4_ppn.md'),
    'xu2020rat': ('F7', '부분 재현', 'R1 실패(위쪽: fAPV 평균 378.3, 폭 [88.11,224.95]), R2 통과(5/5); GTX 1650 P·R 각 5회', 'notes/funnel_f7_rat_result.md'),
    'SQ-MarginTrader': ('F4', 'F4 통과(F7 자리 없음)', '맥 CPU 177초, 저자 스크립트 기본 인자 1회(A2C 50k), 재수집 28종목', 'notes/funnel_f4_margintrader.md'),
    'Y25-02': ('F4', 'F4 통과(F7 자리 없음)', '맥 CPU 1.41시간, Colab 각주 2 노트북 전체 1회(감성 시뮬레이션)', 'notes/funnel_f4_harlf.md'),
    'yang2020ensemble': ('F7', '부분 재현', 'R1 통과(Sharpe 평균 1.008, 폭 [0.885,1.715]), R2 실패(1/5 > 1.12); 5회 CPU', 'notes/funnel_f7_ensemble_result.md'),
    'W21_WaveCorr': ('F5', '한도 초과', 'A=39.4h(CPU)', 'notes/funnel_f4_wavecorr.md'),
    'li2019adaptive': ('F4', 'F4 통과(F7 자리 없음)', '서버 CPU 76.5초, 1에폭(25,000스텝)+시험 경로', 'notes/funnel_f4_li2019adaptive.md'),
    'xiong2018ddpg': ('F4', 'F4 통과(F7 자리 없음)', '서버 CPU 69.2초, 1에폭(25,000스텝)+시험 경로, baselines master', 'notes/funnel_f4_xiong2018ddpg.md'),
    'jiang2017eiie': ('F4', '실행 불가', 'Poloniex 레거시 API 403', 'notes/funnel_f4_jiang2017eiie.md'),
    'SUP-ADRL': ('F4', '실행 불가', '공개 코드에 모듈 누락(stable_baselines/__init__가 a2c_original 등 5개 import, 이력에도 .py 없음); 시도 1 rc 1·1초, 서버 CPU', 'notes/funnel_f4_adrl.md'),
}
PRESELECTED = {'Y25-01', 'P23-02', 'W21_FinRL', 'Y25-03'}  # T1~T4, 별도 집계(프로토콜 1.5)

F1_LABEL = {'not_found': '찾지 못함(문의 안 함)', 'link_dead': '링크 사망', 'link_dead_copy': '링크 사망(사본)',
            'third_party_only': '제3자만', 'original_missing': '원문 미확보', 'placeholder': '자리표시 링크',
            'check': '확인 중', 'pass_check': '확인 중'}

rows = []
for r in F1:
    pid, s = r['id'], r['sample']
    grp = 'T1~T4' if pid in PRESELECTED else s
    st = ST.get(pid, {})
    f1 = r['F1']
    if f1 in F1_LABEL:
        stage, res = 'F1', F1_LABEL[f1]
    elif st.get('status', '').startswith('탈락('):
        stage = st['status'][3:5]
        res = st['status']
    elif pid in RUN:
        stage, res = RUN[pid][0], RUN[pid][1]
    elif pid in PRESELECTED:
        stage, res = 'F7', '별도(T1~T4 결과 노트)'
    elif st.get('status', '') in ('수동 PDF 필요',):
        stage, res = 'F0', '원문 미확보(PDF 대기)'
    elif 'F4까지만' in st.get('status', ''):
        stage, res = 'F4', 'F4까지만(미실행)'
    elif f1.startswith('pass'):
        stage, res = '?', '정적 층 미기재'
    else:
        stage, res = '?', f1
    rows.append({'group': grp, 'id': pid, 'paper': r['title_short'], 'F1': f1, 'stage': stage, 'result': res,
                 'detail': RUN.get(pid, ('', '', '', ''))[2], 'source': RUN.get(pid, ('', '', '', ''))[3]})

out = ROOT / 'notes/lit/f1/funnel_table.csv'
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)

for g in ('S56', 'S-Q', '보충', 'T1~T4'):
    c = collections.Counter((x['stage'], x['result']) for x in rows if x['group'] == g)
    print(f'== {g} (n={sum(c.values())})')
    for (stg, res), n in sorted(c.items()):
        print(f'  {stg}  {res}: {n}')
