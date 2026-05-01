# Codex Stock Transcript Build

Second-pass comparison app that follows the YouTube Codex walkthrough in detail.

Live URL: https://hub.nightray.ai/stock-v2/

Local/Tailscale:
- Local: http://127.0.0.1:3025
- Tailscale: http://100.104.4.21:3025

Run:
```bash
cd apps/codex-stock-transcript-build
PORT=3025 BASE_PATH=/stock-v2 ./server.py
```

Features:
- Five UI options before build
- Chosen command-center UI with portfolio alongside chart/research/news
- Live ticker search, chart, latest news
- Company research brief
- SQLite portfolio DB with shares and cost basis
- AI stock research-agent tab
- Remotion-style marketing video asset
- Dark mode annotation feature
- Transcript checklist and reverse-prompt roadmap

See `docs/transcript_checklist.md` for exact transcript mapping.
