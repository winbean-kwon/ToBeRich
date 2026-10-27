---
name: live-bot-setup
description: Binance live bot runs on Windows server desktop-u6si9ta from main; dashboard via Tailscale; this Mac's IP not whitelisted
metadata:
  type: reference
---
Live bot: Windows server desktop-u6si9ta, branch main, β=30 rt1006 policy, ~330 USDT. Dashboard https://desktop-u6si9ta.tail1ae2f7.ts.net/ (Tailscale; this Mac is logged in; JSON at /api/status). Binance API key is IP-restricted — calls from this Mac get -2015, so use the dashboard. Push both audit-fix-1004 and audit-fix-1004:main; server does git pull + restart. User asked to recheck dashboard around 2026-11-02. See [[project-state-2026-10-26]].
