# Full Transcript Second-Pass Checklist

This app intentionally follows the video as a workflow, not just as inspiration.

| Transcript moment | Implemented in v2 |
|---|---|
| New project from scratch | Separate app `apps/codex-stock-transcript-build` |
| Ask for five UI options | `/stock-v2/` tab: “5 UI Options” |
| Choose option with portfolio alongside | Chosen “Command Center” layout; portfolio shown beside chart/research/news |
| Build front end + back end | Static app + Python API server |
| Database for portfolio | SQLite database at `data/portfolio.sqlite` |
| Convex database | Documented as migration path; not auto-created because it needs account auth |
| Multi-agent workflow | App includes separate tabs/workstreams: app, research agent, marketing video, checklist |
| Browser/computer-use research | Research Agent tab with AI-stock candidates from transcript |
| Live stock price/chart data | Yahoo public chart endpoint; fallback demo if blocked |
| Latest news | Yahoo finance search/news endpoint; fallback if blocked |
| Company research | Rule-based research brief from price/news data |
| Dark mode annotation | Working dark mode button |
| Reverse prompting | Checklist tab has next tasks roadmap |
| Add shares / portfolio value | Add/update holding with shares + cost basis, P/L and market value |
| Remotion launch video | Generated Remotion-style poster + MP4 marketing asset |
| Deploy live | `https://hub.nightray.ai/stock-v2/` |
| GitHub repository | `sanvigian/codex-stock-transcript-build` |

## Why not exact Convex/Remotion accounts?
The transcript assumes the human can click through account/setup flows in Codex. I did not create third-party accounts or store new API secrets without explicit credentials. The deployed comparison build stays fully functional with local SQLite and local video assets.
