"""
실거래 루프 상태 웹 대시보드 + 사이클 기록(ledger).

외부 알림 서비스 대신 봇 프로세스 안에서 작은 HTTP 서버를 띄워 브라우저로 상태를 본다:
  - 건강 상태(정상/주의/위험/멈춤), 코드 브랜치·커밋, 모델 파일
  - 운용자산, 목표 vs 실제 위험자산 비중, 목표-실제 괴리(최소주문금액 때문에 못 낸 주문 포함)
  - 서킷브레이커·연속 실패·다른 봇 감지 상태
  - WARNING 이상 로그(재시작해도 유지), 사이클별 기록 표·운용자산 추이

기본은 127.0.0.1에만 열어 그 컴퓨터에서만 볼 수 있다. 다른 기기에서 보려면 SSH 터널
(ssh -L 8787:localhost:8787 서버)을 쓰거나, --dashboard-host 0.0.0.0과 DASHBOARD_TOKEN 환경변수를
함께 지정한다(토큰 없이 외부에 여는 것은 거부한다 — 잔고·주문 내역이 노출되므로).
"""

from __future__ import annotations

import csv
import hmac
import json
import logging
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

log = logging.getLogger("live_monitor")

LEDGER_FIELDS = [
    "time_utc", "equity", "target_exposure", "actual_exposure", "tracking_gap",
    "skipped_usdt", "orders", "filled_orders", "rho", "note", "exposure_gap", "n_hold",
]
# 목표-실제 위험자산 비중(총 노출) 차이가 이보다 크면 실행 목표가 노출을 맞추지 못하는 상태 — 종목별 L1 괴리는
# 소액 운용에서 상위 종목 집중(crypto/live_execution.py) 때문에 원리상 크게 남으므로 경고 기준으로 쓰지 않는다
EXPOSURE_GAP_WARN = 0.03
UNTRADABLE_WARN_RATIO = 0.10  # 유니버스 중 거래불가 비율이 이 이상이면 재학습 필요


class Monitor:
    """루프가 갱신하는 상태 저장소. HTTP 핸들러 스레드와 공유하므로 lock으로 보호한다."""

    def __init__(self, ledger_path: Path | None, events_path: Path | None, interval_sec: int):
        self.ledger_path = ledger_path
        self.events_path = events_path
        self.interval_sec = interval_sec
        self._lock = threading.Lock()
        self.status: dict = {"started_at": time.time(), "consecutive_failures": 0}
        self.cycles: deque[dict] = deque(maxlen=500)
        self.events: deque[dict] = deque(maxlen=300)
        self._load_history()

    def _load_history(self) -> None:
        if self.ledger_path is not None and self.ledger_path.exists():
            with self.ledger_path.open(newline="") as f:
                reader = csv.DictReader(f)
                self.cycles.extend(reader)
                header = reader.fieldnames
            if header != LEDGER_FIELDS:
                # 열이 추가되기 전의 기록 파일 — 새 열 순서로 다시 써서 이후 행과 열이 어긋나지 않게 한다
                tmp = self.ledger_path.with_suffix(".tmp")
                with tmp.open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
                    w.writeheader()
                    w.writerows(self.cycles)
                tmp.replace(self.ledger_path)
        if self.events_path is not None and self.events_path.exists():
            for line in self.events_path.read_text().splitlines()[-self.events.maxlen:]:
                try:
                    self.events.append(json.loads(line))
                except ValueError:
                    continue

    def update(self, **kw) -> None:
        with self._lock:
            self.status.update(kw)

    def record_cycle(self, row: dict) -> None:
        row = {k: row.get(k, "") for k in LEDGER_FIELDS}
        with self._lock:
            self.cycles.append(row)
            self.status["last_cycle_at"] = time.time()
            if self.ledger_path is not None:
                new = not self.ledger_path.exists()
                with self.ledger_path.open("a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
                    if new:
                        w.writeheader()
                    w.writerow(row)

    def add_event(self, level: str, message: str) -> None:
        ev = {"ts": time.time(), "level": level, "message": message}
        with self._lock:
            self.events.append(ev)
            if self.events_path is not None:
                with self.events_path.open("a") as f:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def health(self) -> tuple[str, list[str]]:
        """(등급, 사유 목록). 등급: ok / warn / critical / stale."""
        s = self.status
        reasons: list[str] = []
        last = s.get("last_cycle_at")
        if last is None or time.time() - last > 2.5 * self.interval_sec:
            if time.time() - s["started_at"] > 2.5 * self.interval_sec:
                return "stale", ["사이클이 예정 시간보다 오래 돌지 않음 — 프로세스 멈춤/절전/네트워크 확인"]
        critical = []
        if s.get("consecutive_failures", 0) >= 3:
            critical.append(f"{s['consecutive_failures']}사이클 연속 실패")
        if s.get("breaker_tripped"):
            critical.append("서킷브레이커 발동 — 당일 주문 중단")
        if s.get("other_bot_orders"):
            critical.append("다른 봇의 주문 감지 — 중복 실행 의심, 주문 중단")
        if critical:
            return "critical", critical
        if s.get("api_key_warnings"):
            reasons += s["api_key_warnings"]
        if s.get("untradable_ratio", 0) >= UNTRADABLE_WARN_RATIO:
            reasons.append(f"유니버스 {s['untradable_ratio']:.0%}가 거래불가 — 현재 시장 기준으로 재학습 필요")
        if s.get("exposure_gap", 0) > EXPOSURE_GAP_WARN:
            reasons.append(
                f"목표-실제 위험자산 비중 차이 {s['exposure_gap']:.1%} — 주문하지 못한 비중(최소주문금액 미달·거래정지·"
                "스프레드 보류·부분체결)이 커서 정책 목표 노출과 다르게 운용 중"
            )
        if s.get("small_capital_warning"):
            reasons.append(s["small_capital_warning"])
        if s.get("last_cycle_warnings"):
            reasons.append(f"직전 사이클 경고 {s['last_cycle_warnings']}건 — 아래 로그 확인")
        return ("warn" if reasons else "ok"), reasons

    def snapshot(self) -> dict:
        with self._lock:
            grade, reasons = self.health()
            return {
                "now": time.time(),
                "interval_sec": self.interval_sec,
                "health": grade,
                "reasons": reasons,
                "status": dict(self.status),
                "cycles": list(self.cycles)[-200:],
                "events": list(self.events)[-100:][::-1],
            }


class MonitorLogHandler(logging.Handler):
    """WARNING 이상 로그를 대시보드 이벤트로 보낸다."""

    def __init__(self, monitor: Monitor):
        super().__init__(level=logging.WARNING)
        self.monitor = monitor
        self.cycle_warnings = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.cycle_warnings += 1
            self.monitor.add_event(record.levelname, record.getMessage())
        except Exception:  # 로깅 핸들러가 루프를 죽이면 안 된다
            self.handleError(record)


def serve_dashboard(monitor: Monitor, host: str, port: int) -> ThreadingHTTPServer | None:
    """대시보드 HTTP 서버를 데몬 스레드로 띄운다. 실패해도(포트 사용 중 등) 봇은 계속 돈다."""
    token = os.environ.get("DASHBOARD_TOKEN", "")
    if host not in ("127.0.0.1", "localhost", "::1") and not token:
        log.error("대시보드를 %s에 열려면 DASHBOARD_TOKEN 환경변수가 필요합니다 — 대시보드 비활성화", host)
        return None

    class Handler(BaseHTTPRequestHandler):
        def _authorized(self, query: dict) -> bool:
            if not token:
                return True
            given = (query.get("token") or [""])[0]
            return hmac.compare_digest(given, token)

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802 — BaseHTTPRequestHandler 규약
            url = urlparse(self.path)
            if not self._authorized(parse_qs(url.query)):
                self._send(403, "토큰이 필요합니다 (?token=...)".encode(), "text/plain; charset=utf-8")
                return
            if url.path == "/":
                self._send(200, DASHBOARD_HTML.encode(), "text/html; charset=utf-8")
            elif url.path == "/api/status":
                body = json.dumps(monitor.snapshot(), ensure_ascii=False, default=str).encode()
                self._send(200, body, "application/json; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, *args):  # 접속마다 stderr에 찍히는 기본 로그를 끈다
            pass

    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as e:
        log.warning("대시보드를 %s:%d에 열지 못함(%s) — 대시보드 없이 계속", host, port, e)
        return None
    threading.Thread(target=server.serve_forever, daemon=True, name="dashboard").start()
    log.info("대시보드: http://%s:%d/%s", "localhost" if host in ("127.0.0.1", "::1") else host, port,
             "?token=…" if token else "")
    return server


DASHBOARD_HTML = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>실거래 봇 상태</title>
<style>
:root {
  --bg: #f7f7f5; --panel: #ffffff; --ink: #1d1d1b; --muted: #6b6b66; --line: #e3e2dc;
  --ok: #1f7a4d; --ok-bg: #e4f3ea; --warn: #8a5a00; --warn-bg: #fbf0d9;
  --crit: #b3261e; --crit-bg: #fbe4e2; --stale: #5b5b8a; --stale-bg: #e9e9f5; --accent: #2f5bd3;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #141413; --panel: #1e1e1c; --ink: #ecebe6; --muted: #9c9b94; --line: #33332f;
    --ok: #6fd19c; --ok-bg: #173325; --warn: #f0c060; --warn-bg: #3a2e12;
    --crit: #ff8a80; --crit-bg: #3d1a18; --stale: #a9a9e0; --stale-bg: #25253a; --accent: #8fb0ff;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 14px/1.5 -apple-system, "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 48px; }
header { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 16px; }
h1 { font-size: 18px; margin: 0; }
h2 { font-size: 14px; margin: 0 0 10px; color: var(--muted); font-weight: 600; }
.badge { padding: 4px 12px; border-radius: 999px; font-weight: 700; }
.ok { color: var(--ok); background: var(--ok-bg); } .warn { color: var(--warn); background: var(--warn-bg); }
.critical { color: var(--crit); background: var(--crit-bg); } .stale { color: var(--stale); background: var(--stale-bg); }
.meta { color: var(--muted); font-size: 12px; width: 100%; overflow-wrap: anywhere; }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; }
.reasons { margin: 0; padding-left: 18px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-bottom: 14px; }
.tile { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; }
.tile .k { color: var(--muted); font-size: 12px; } .tile .v { font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }
.tile .s { color: var(--muted); font-size: 12px; }
svg { width: 100%; height: 120px; display: block; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 12px; font-variant-numeric: tabular-nums; }
th, td { text-align: right; padding: 5px 8px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th:first-child, td:first-child, td.l { text-align: left; }
th { color: var(--muted); font-weight: 600; }
.ev { display: flex; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 13px; }
.ev time { color: var(--muted); white-space: nowrap; font-size: 12px; }
.lv { font-weight: 700; font-size: 11px; min-width: 64px; }
.lv.WARNING { color: var(--warn); } .lv.ERROR, .lv.CRITICAL { color: var(--crit); }
.empty { color: var(--muted); }
</style>
</head>
<body>
<main>
  <header>
    <h1>실거래 봇 상태</h1>
    <span id="badge" class="badge">불러오는 중…</span>
    <div id="meta" class="meta"></div>
  </header>
  <section id="reasonsPanel" class="panel" hidden><h2>확인 필요</h2><ul id="reasons" class="reasons"></ul></section>
  <section class="tiles" id="tiles"></section>
  <section class="panel"><h2>운용자산 추이 (USDT)</h2><div id="sparkRange" class="meta"></div><svg id="spark" viewBox="0 0 600 120" preserveAspectRatio="none"></svg></section>
  <section class="panel"><h2>경고·오류 로그 (최근 100건)</h2><div id="events"></div></section>
  <section class="panel"><h2>사이클 기록 (최근 50건)</h2><div class="scroll"><table id="cycles"></table></div></section>
</main>
<script>
const token = new URLSearchParams(location.search).get("token");
const LABEL = { ok: "정상", warn: "주의", critical: "위험", stale: "멈춤" };
const fmtT = (ts) => new Date(ts * 1000).toLocaleString("ko-KR", { hour12: false });
const pct = (x) => (x === "" || x == null || isNaN(+x)) ? "–" : (+x * 100).toFixed(1) + "%";
const num = (x, d = 2) => (x === "" || x == null || isNaN(+x)) ? "–" : (+x).toLocaleString("ko-KR", { maximumFractionDigits: d, minimumFractionDigits: d });
// 사이클 기록의 time_utc("YYYY-MM-DD HH:MM", UTC)를 보는 사람의 현지 시각으로 바꿔 표시한다
const fmtUtc = (s) => { const d = new Date(String(s).replace(' ', 'T') + ':00Z'); return isNaN(d) ? String(s) : d.toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }); };
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function tile(k, v, s = "") { return `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`; }

function render(d) {
  const st = d.status, badge = document.getElementById("badge");
  badge.className = "badge " + d.health; badge.textContent = LABEL[d.health] || d.health;
  document.getElementById("meta").textContent = [
    st.mode, st.code_version, st.model_info, "갱신 " + fmtT(d.now),
  ].filter(Boolean).join(" · ");
  const rp = document.getElementById("reasonsPanel");
  rp.hidden = !d.reasons.length;
  document.getElementById("reasons").innerHTML = d.reasons.map((r) => `<li>${esc(r)}</li>`).join("");

  const last = d.cycles[d.cycles.length - 1] || {};
  const next = st.last_cycle_at ? Math.max(0, Math.round((Math.floor(d.now / d.interval_sec) + 1) * d.interval_sec - d.now) / 60) : null;
  document.getElementById("tiles").innerHTML = [
    tile("운용자산", num(last.equity) + " <small>USDT</small>", st.max_capital ? `상한 ${num(st.max_capital, 0)}` : ""),
    tile("위험자산 비중", `${pct(last.actual_exposure)}`, `목표 ${pct(last.target_exposure)} · ρ ${num(last.rho, 3)}`),
    tile("노출 괴리", pct(last.exposure_gap), `보유 ${last.n_hold ?? "–"}종목 · 종목별 괴리 ${pct(last.tracking_gap)}`),
    tile("주문", `${last.filled_orders ?? "–"} / ${last.orders ?? "–"}`, "체결 / 시도 (직전 사이클)"),
    tile("서킷브레이커", st.breaker_tripped ? "발동" : "정상", st.day_pnl_pct != null ? `당일 ${pct(st.day_pnl_pct)} (입출금 제외)` : ""),
    tile("마지막 사이클", st.last_cycle_at ? new Date(st.last_cycle_at * 1000).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false }) : "–", next != null ? `다음까지 약 ${next.toFixed(0)}분` : ""),
    tile("연속 실패", st.consecutive_failures ?? 0, ""),
    tile("거래불가 종목", st.untradable ? st.untradable.length : 0, (st.untradable || []).join(", ")),
  ].join("");

  const ys = d.cycles.map((c) => +c.equity).filter((v) => !isNaN(v) && v > 0);
  const svg = document.getElementById("spark"), range = document.getElementById("sparkRange");
  svg.hidden = ys.length < 2;
  if (ys.length > 1) {
    const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
    const pts = ys.map((v, i) => `${(i / (ys.length - 1)) * 600},${110 - ((v - lo) / span) * 100}`).join(" ");
    svg.innerHTML = `<polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2" vector-effect="non-scaling-stroke"/>`;
    range.textContent = `최저 ${num(lo)} · 최고 ${num(hi)} · 최근 ${ys.length}사이클`;
  } else range.textContent = "기록이 2건 이상 쌓이면 표시됩니다";

  document.getElementById("events").innerHTML = d.events.length
    ? d.events.map((e) => `<div class="ev"><time>${fmtT(e.ts)}</time><span class="lv ${e.level}">${e.level}</span><span>${esc(e.message)}</span></div>`).join("")
    : `<div class="empty">경고 없음</div>`;

  const rows = d.cycles.slice(-50).reverse();
  document.getElementById("cycles").innerHTML =
    `<tr><th>시각</th><th>운용자산</th><th>목표 노출</th><th>실제 노출</th><th>노출 괴리</th><th>종목 괴리</th><th>보유</th><th>주문</th><th>ρ</th><th style="text-align:left">비고</th></tr>`
    + rows.map((c) => `<tr><td>${esc(fmtUtc(c.time_utc))}</td><td>${num(c.equity)}</td><td>${pct(c.target_exposure)}</td><td>${pct(c.actual_exposure)}</td>`
      + `<td>${pct(c.exposure_gap)}</td><td>${pct(c.tracking_gap)}</td><td>${c.n_hold || "–"}</td><td>${c.filled_orders}/${c.orders}</td><td>${num(c.rho, 3)}</td><td class="l">${esc(c.note || "")}</td></tr>`).join("");
}

async function refresh() {
  try {
    const r = await fetch("api/status" + (token ? "?token=" + encodeURIComponent(token) : ""), { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    render(await r.json());
  } catch (e) {
    const b = document.getElementById("badge");
    b.className = "badge stale"; b.textContent = "봇 응답 없음";
  }
}
refresh(); setInterval(refresh, 15000);
</script>
</body>
</html>
"""
