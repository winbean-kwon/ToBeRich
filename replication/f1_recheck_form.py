# -*- coding: utf-8 -*-
"""F1 재확인 입력 화면(로컬 HTML) 생성·가져오기. 판정 절차·값은 notes/f1_recheck_prereg.md 그대로이고, 시트 열도 바꾸지 않는다.

python3 replication/f1_recheck_form.py build                 → notes/lit/f1/f1_recheck_form.html, f1_second_coder_form.html
python3 replication/f1_recheck_form.py import <받은 CSV> [main|second]
      → 화면에서 저장한 CSV를 검사(열·id·허용값)한 뒤 원래 시트 파일에 덮어쓴다(main: f1_recheck_sheet.csv, second: f1_second_coder_sheet.csv).

화면은 브라우저 저장소에 자동 저장하고, 'CSV 저장' 버튼으로 시트와 같은 열 순서의 CSV를 내려받는다. Claude 판정은 넣지 않는다.
"""
import csv, html, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / 'notes/lit/f1'
SHEETS = {'main': (D / 'f1_recheck_sheet.csv', D / 'f1_recheck_form.html', 'F1 재확인 (54편)'),
          'second': (D / 'f1_second_coder_sheet.csv', D / 'f1_second_coder_form.html', 'F1 두 번째 판정 (15편)')}
COLS = ["순번", "id", "제목", "1저자", "연도", "학회", "식별자", "판정", "URL", "근거 위치", "소요(분)", "확인일", "메모"]
LABELS = ["찾음", "제3자만", "링크 사망", "요청 시 제공", "없음", "원문 미확보"]

PAGE = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#fafaf8;--card:#fff;--fg:#1d1d1b;--mut:#6b6b66;--line:#e2e1dc;--acc:#2f5d8a;--ok:#2e7d4f;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#1f1f1d;--fg:#ecebe6;--mut:#9d9c95;--line:#33332f;--acc:#8ab4e0;--ok:#7fc79a;--warn:#e0a85a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:2;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
header h1{font-size:16px;margin:0}#prog{color:var(--mut)}button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);cursor:pointer}
button.primary{background:var(--acc);color:#fff;border-color:var(--acc)}main{max-width:900px;margin:0 auto;padding:12px 16px 80px}
details.rule{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin-bottom:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0}.card.done{border-left:4px solid var(--ok)}
.t{font-weight:600}.meta{color:var(--mut);font-size:13px}.links a{margin-right:10px;font-size:13px;color:var(--acc)}
.steps{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media (max-width:640px){.grid{grid-template-columns:1fr}}label.f{display:flex;flex-direction:column;font-size:12px;color:var(--mut)}
select,input,textarea{font:inherit;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:5px 7px}
.need{color:var(--warn);font-size:12px}#filter{margin-left:auto}
</style></head><body>
<header><h1>__TITLE__</h1><span id="prog"></span>
<select id="filter"><option value="all">전체</option><option value="todo">미입력만</option><option value="done">입력 완료만</option></select>
<button class="primary" id="save">CSV 저장</button></header>
<main>
<details class="rule" open><summary><b>판정 방법</b> (사전 등록 notes/f1_recheck_prereg.md)</summary>
<ol>
<li><b>논문 PDF</b>에서 <code>github</code>, <code>code</code>, <code>available</code>, <code>repository</code>, <code>supplementary</code>, <code>request</code>를 검색한다.</li>
<li><b>학회 페이지</b>의 supplementary를 본다.</li>
<li><b>1저자·교신저자</b>의 GitHub와 개인 홈페이지를 본다.</li>
<li><b>Hugging Face 논문 페이지</b>를 본다.</li>
</ol>
<p>앞 단계에서 공식 저장소(저자 본인·저자 조직의 계정이거나 논문이 가리키는 저장소, 오늘 열림)를 찾으면 <b>거기서 멈추고</b> <code>찾음</code>. <code>찾음</code>이 아닌 판정은 <b>네 곳을 모두 본 뒤</b>에만 적는다. 편당 상한 20분, 넘으면 그때까지의 판정을 적는다.</p>
<p>값: <b>찾음</b>(URL·근거 위치 필수) · <b>제3자만</b>(저자와 무관한 재구현만) · <b>링크 사망</b>(논문이 가리키는 링크가 안 열림) · <b>요청 시 제공</b> · <b>없음</b> · <b>원문 미확보</b></p>
<p class="meta">입력은 이 브라우저에 자동 저장된다. 끝나면 'CSV 저장' → 터미널에서 <code>python3 replication/f1_recheck_form.py import ~/Downloads/__FILE__ __WHICH__</code></p>
</details>
<div id="list"></div></main>
<script>
const ROWS=__ROWS__, COLS=__COLS__, LABELS=__LABELS__, KEY='__KEY__', FILE='__FILE__';
let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}}
function g(id,k,dflt){return (st[id]&&st[id][k]!==undefined)?st[id][k]:dflt}
function s(id,k,v){st[id]=st[id]||{};st[id][k]=v;save();refresh(id)}
function esc(x){return String(x).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function links(r){const out=[];const idf=r['식별자']||'';
 const ax=idf.match(/arXiv:\s*([0-9]{4}\.[0-9]{4,5})/i);const doi=idf.match(/doi:\s*(\S+?)(;|$)/i);
 if(ax){out.push(['arXiv PDF','https://arxiv.org/pdf/'+ax[1]]);out.push(['Hugging Face','https://huggingface.co/papers/'+ax[1]])}
 else out.push(['Hugging Face 검색','https://huggingface.co/papers?q='+encodeURIComponent(r['제목'])]);
 if(doi)out.push(['DOI','https://doi.org/'+doi[1]]);
 out.push(['Google Scholar','https://scholar.google.com/scholar?q='+encodeURIComponent('"'+r['제목']+'"')]);
 out.push(['GitHub 검색(제목)','https://github.com/search?type=repositories&q='+encodeURIComponent(r['제목'])]);
 out.push(['1저자 GitHub 검색','https://github.com/search?type=users&q='+encodeURIComponent((r['1저자']||'').replace(/\(.*?\)/g,''))]);
 return out.map(([t,u])=>`<a href="${u}" target="_blank" rel="noopener">${t}</a>`).join('')}
function isDone(id){const v=g(id,'판정','');if(!v)return false;if(v==='찾음')return !!g(id,'URL','')&&!!g(id,'근거 위치','');return true}
function card(r){const id=r.id;const v=g(id,'판정',r['판정']||'');
 return `<div class="card" id="c_${esc(id)}"><div class="t">${esc(r['순번'])}. ${esc(r['제목'])}</div>
 <div class="meta">${esc(r['1저자'])} · ${esc(r['연도'])} · ${esc(r['학회'])} · ${esc(r['식별자'])} · id ${esc(id)}</div>
 <div class="links">${links(r)}</div>
 <div class="steps">${['① PDF 검색','② 학회 supplementary','③ 저자 GitHub·홈페이지','④ Hugging Face'].map((t,i)=>`<label><input type="checkbox" ${g(id,'s'+i,false)?'checked':''} onchange="s('${id}','s${i}',this.checked)"> ${t}</label>`).join('')}</div>
 <div class="grid">
 <label class="f">판정<select onchange="s('${id}','판정',this.value)"><option value="">—</option>${LABELS.map(l=>`<option ${l===v?'selected':''}>${l}</option>`).join('')}</select></label>
 <label class="f">URL (찾음이면 필수)<input value="${esc(g(id,'URL',r['URL']||''))}" onchange="s('${id}','URL',this.value)"></label>
 <label class="f">근거 위치 (예: 1쪽 각주, README)<input value="${esc(g(id,'근거 위치',r['근거 위치']||''))}" onchange="s('${id}','근거 위치',this.value)"></label>
 <label class="f">소요(분)<input inputmode="numeric" value="${esc(g(id,'소요(분)',r['소요(분)']||''))}" onchange="s('${id}','소요(분)',this.value)"></label>
 </div><label class="f" style="margin-top:8px">메모<textarea rows="2" onchange="s('${id}','메모',this.value)">${esc(g(id,'메모',r['메모']||''))}</textarea></label>
 <div class="need" id="n_${esc(id)}"></div></div>`}
function refresh(id){const c=document.getElementById('c_'+id);if(c){c.classList.toggle('done',isDone(id));
 const v=g(id,'판정','');const n=document.getElementById('n_'+id);
 n.textContent=(v==='찾음'&&!(g(id,'URL','')&&g(id,'근거 위치','')))?'찾음이면 URL과 근거 위치를 적어 주세요.':(v&&v!=='찾음'&&![0,1,2,3].every(i=>g(id,'s'+i,false)))?'찾음이 아닌 판정은 네 곳을 모두 확인한 뒤에 적습니다.':'';
 if(v&&!g(id,'확인일','')){st[id]['확인일']=new Date().toISOString().slice(0,10);save()}}
 const d=ROWS.filter(r=>isDone(r.id)).length;document.getElementById('prog').textContent=`${d} / ${ROWS.length} 완료`;applyFilter()}
function applyFilter(){const f=document.getElementById('filter').value;ROWS.forEach(r=>{const c=document.getElementById('c_'+r.id);const dn=isDone(r.id);
 c.style.display=(f==='all'||(f==='todo'&&!dn)||(f==='done'&&dn))?'':'none'})}
function csvCell(x){x=String(x??'');return /[",\n]/.test(x)?'"'+x.replace(/"/g,'""')+'"':x}
document.getElementById('list').innerHTML=ROWS.map(card).join('');ROWS.forEach(r=>refresh(r.id));
document.getElementById('filter').onchange=applyFilter;
document.getElementById('save').onclick=()=>{const lines=[COLS.join(',')];ROWS.forEach(r=>{const o={...r};
 ['판정','URL','근거 위치','소요(분)','확인일','메모'].forEach(k=>{const v=g(r.id,k,undefined);if(v!==undefined)o[k]=v});
 lines.push(COLS.map(c=>csvCell(o[c])).join(','))});
 const b=new Blob(['﻿'+lines.join('\n')+'\n'],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=FILE;a.click()};
</script></body></html>"""


def build():
    for which, (sheet, out, title) in SHEETS.items():
        rows = list(csv.DictReader(open(sheet, encoding='utf-8-sig')))
        assert list(rows[0].keys()) == COLS, sheet
        page = (PAGE.replace('__TITLE__', html.escape(title)).replace('__ROWS__', json.dumps(rows, ensure_ascii=False))
                .replace('__COLS__', json.dumps(COLS, ensure_ascii=False)).replace('__LABELS__', json.dumps(LABELS, ensure_ascii=False))
                .replace('__KEY__', f'f1form_{which}_v1').replace('__FILE__', sheet.name).replace('__WHICH__', which))
        out.write_text(page, encoding='utf-8')
        print('생성', out.relative_to(ROOT), len(rows), '편')


def do_import(src, which='main'):
    sheet = SHEETS[which][0]
    orig = list(csv.DictReader(open(sheet, encoding='utf-8-sig')))
    new = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    assert new and list(new[0].keys()) == COLS, '열이 시트와 다름'
    assert [r['id'] for r in new] == [r['id'] for r in orig], 'id 목록·순서가 시트와 다름'
    for o, n in zip(orig, new):
        for c in COLS[:7]:
            assert o[c] == n[c], ('고정 칸이 바뀜', o['id'], c)
    bad = [r['id'] for r in new if r['판정'] and r['판정'] not in LABELS]
    assert not bad, ('허용값이 아님', bad)
    miss = [r['id'] for r in new if r['판정'] == '찾음' and not (r['URL'] and r['근거 위치'])]
    with open(sheet, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator='\n'); w.writeheader(); w.writerows(new)
    done = sum(1 for r in new if r['판정'])
    print(f'{sheet.relative_to(ROOT)} 갱신: 판정 {done}/{len(new)}편' + (f', 찾음인데 URL·근거 없음: {miss}' if miss else ''))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['build']:
        build()
    elif a[:1] == ['import'] and len(a) >= 2:
        do_import(a[1], a[2] if len(a) > 2 else 'main')
    else:
        print(__doc__)
