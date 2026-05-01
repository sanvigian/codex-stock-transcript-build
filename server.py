#!/usr/bin/env python3
import json, os, re, sqlite3, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
DB = ROOT / "data" / "portfolio.sqlite"
PORT = int(os.environ.get("PORT", "3025"))
BASE_PATH = os.environ.get("BASE_PATH", "")
CACHE = {}

AI_STOCKS = [
    {"ticker":"NVDA","name":"NVIDIA","why":"AI accelerators, CUDA ecosystem, data-center demand."},
    {"ticker":"MSFT","name":"Microsoft","why":"Azure AI, Copilot distribution, enterprise monetization."},
    {"ticker":"GOOGL","name":"Alphabet","why":"TPUs, Gemini, search/cloud cashflow."},
    {"ticker":"AMZN","name":"Amazon","why":"AWS AI infrastructure and retail/ads cash generation."},
    {"ticker":"AVGO","name":"Broadcom","why":"Custom AI silicon/networking exposure."},
    {"ticker":"TSM","name":"TSMC","why":"Foundry backbone for advanced AI chips."},
    {"ticker":"ASML","name":"ASML","why":"EUV lithography bottleneck for leading-edge semis."},
]

TRANSCRIPT_STEPS = [
    "Start a new project from scratch, not from a template.",
    "Ask for five UI concepts first, before coding the app.",
    "Choose the concept with portfolio visible alongside chart/research/news.",
    "Build front end, back end, and persistent database.",
    "Use parallel workstreams: app builder, marketing video builder, research agent.",
    "Research best AI stocks in browser/computer-use style and feed them into portfolio ideas.",
    "Implement live price/chart data with a simple free API.",
    "Add dark-mode button using an annotation-like requested edit.",
    "Reverse prompt: ask what next features should be built and show recommended next tasks.",
    "Allow adding stocks with share counts and cost basis; calculate portfolio value.",
    "Generate launch-video/marketing assets.",
    "Deploy to a shareable URL."
]

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute("""create table if not exists holdings(
            ticker text primary key,
            name text,
            shares real not null default 0,
            cost_basis real not null default 0,
            notes text default '',
            created_at text not null,
            updated_at text not null
        )""")
        con.execute("""create table if not exists settings(
            key text primary key,
            value text
        )""")

def clean_ticker(v):
    return re.sub(r"[^A-Z0-9.\-]", "", str(v or "").upper())[:12]

def json_response(handler, obj, status=200):
    data = json.dumps(obj, indent=2).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers(); handler.wfile.write(data)

def cache_get(k):
    hit = CACHE.get(k)
    return hit["value"] if hit and hit["expires"] > time.time() else None

def cache_set(k, value, ttl=300):
    CACHE[k] = {"value": value, "expires": time.time()+ttl}

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Kuatto Transcript Build/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def fallback_quote(ticker):
    seed = sum(ord(c) for c in ticker)
    points=[]
    base=60+(seed%260)
    for i in range(126):
        close=base + 0.2*i + 9*__import__('math').sin(i/8) + 4*__import__('math').cos(i/17)
        points.append({"date": datetime.fromtimestamp(time.time()-(125-i)*86400).strftime('%Y-%m-%d'), "close": round(close,2), "volume": 1000000+i*12345})
    prev=points[-2]["close"]; price=points[-1]["close"]
    return {"ticker":ticker,"name":f"{ticker} demo quote","price":price,"change":round(price-prev,2),"changePercent":round((price-prev)/prev*100,2),"currency":"USD","points":points,"source":"fallback-demo"}

def yahoo_quote(ticker):
    key="quote:"+ticker
    if (v:=cache_get(key)): return v
    try:
        data=fetch_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?range=6mo&interval=1d")
        result=data.get('chart',{}).get('result',[None])[0]
        if not result: raise RuntimeError('no chart')
        meta=result.get('meta',{})
        ts=result.get('timestamp') or []
        q=(result.get('indicators',{}).get('quote') or [{}])[0]
        closes=q.get('close') or []; vols=q.get('volume') or []
        points=[]
        for i,t in enumerate(ts):
            if i < len(closes) and closes[i] is not None:
                points.append({"date":datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%d'),"close":round(float(closes[i]),2),"volume": int(vols[i] or 0) if i < len(vols) else 0})
        price=float(meta.get('regularMarketPrice') or points[-1]['close'])
        prev=float(meta.get('previousClose') or points[-2]['close'])
        value={"ticker":ticker,"name":meta.get('longName') or meta.get('shortName') or ticker,"price":round(price,2),"change":round(price-prev,2),"changePercent":round((price-prev)/prev*100,2) if prev else 0,"currency":meta.get('currency','USD'),"points":points,"source":"yahoo-public"}
    except Exception:
        value=fallback_quote(ticker)
    cache_set(key,value,300); return value

def news(ticker):
    key="news:"+ticker
    if (v:=cache_get(key)): return v
    try:
        data=fetch_json(f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(ticker)}&newsCount=8&quotesCount=1")
        items=[]
        for n in data.get('news',[])[:8]:
            items.append({"title":n.get('title'),"publisher":n.get('publisher'),"link":n.get('link'),"published":datetime.fromtimestamp(n.get('providerPublishTime',0),timezone.utc).isoformat() if n.get('providerPublishTime') else None})
    except Exception:
        items=[{"title":f"{ticker}: verify earnings, guidance, valuation, and risk before investing","publisher":"Transcript Build fallback","link":"#","published":datetime.now(timezone.utc).isoformat()}]
    cache_set(key,items,300); return items

def research_brief(q, items):
    pts=q.get('points') or []
    first=pts[0]['close'] if pts else q['price']; last=pts[-1]['close'] if pts else q['price']
    move=(last-first)/first*100 if first else 0
    avg=sum(p['close'] for p in pts)/len(pts) if pts else last
    return {
        "headline": f"{q['ticker']} has {'positive' if move>8 else 'negative' if move<-8 else 'mixed/range-bound'} six-month momentum in this transcript-faithful build.",
        "bullets": [
            f"Live/fallback source: {q['source']}; last price {q['currency']} {q['price']} ({q['changePercent']:+.2f}% day move).",
            f"Six-month move: {move:+.1f}%; current price is {'above' if last>=avg else 'below'} the simple average of {avg:.2f}.",
            f"News agent found {len(items)} recent item(s); use them as catalyst prompts, not investment advice.",
            "Transcript mapping: this corresponds to the 'company research' and 'latest news' modules after live data was added."
        ],
        "nextQuestions": ["What changed in earnings/guidance?", "Is the move company-specific or sector-wide?", "What is my max position size?", "Where is my stop/review level?"]
    }

def holdings():
    with sqlite3.connect(DB) as con:
        con.row_factory=sqlite3.Row
        return [dict(r) for r in con.execute("select * from holdings order by updated_at desc")]

def save_holding(payload):
    ticker=clean_ticker(payload.get('ticker'))
    if not ticker: raise ValueError('ticker required')
    q=yahoo_quote(ticker); now=datetime.now(timezone.utc).isoformat()
    shares=float(payload.get('shares') or 0); cost=float(payload.get('cost_basis') or payload.get('costBasis') or 0)
    notes=str(payload.get('notes') or '')[:500]
    with sqlite3.connect(DB) as con:
        con.execute("""insert into holdings(ticker,name,shares,cost_basis,notes,created_at,updated_at)
        values(?,?,?,?,?,?,?) on conflict(ticker) do update set name=excluded.name,shares=excluded.shares,cost_basis=excluded.cost_basis,notes=excluded.notes,updated_at=excluded.updated_at""",(ticker,q['name'],shares,cost,notes,now,now))
    return portfolio_summary()

def portfolio_summary():
    rows=holdings(); enriched=[]; total=cost_total=0
    for h in rows:
        q=yahoo_quote(h['ticker']); value=(h['shares'] or 0)*q['price']; cost=(h['shares'] or 0)*(h['cost_basis'] or 0)
        total+=value; cost_total+=cost
        h.update({"lastPrice":q['price'],"marketValue":round(value,2),"gainLoss":round(value-cost,2),"gainLossPct":round((value-cost)/cost*100,2) if cost else None,"source":q['source']})
        enriched.append(h)
    return {"holdings":enriched,"totalValue":round(total,2),"totalCost":round(cost_total,2),"totalGainLoss":round(total-cost_total,2),"updatedAt":datetime.now(timezone.utc).isoformat()}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(PUBLIC),**kw)
    def log_message(self,*a): return
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path == '/api/health': return json_response(self,{"ok":True,"app":"codex-stock-transcript-build","port":PORT,"basePath":BASE_PATH})
        if path.startswith('/api/stock/'):
            ticker=clean_ticker(path.rsplit('/',1)[-1]); q=yahoo_quote(ticker); n=news(ticker); return json_response(self,{"quote":q,"news":n,"research":research_brief(q,n)})
        if path == '/api/portfolio': return json_response(self,portfolio_summary())
        if path == '/api/ai-stocks': return json_response(self,{"items":AI_STOCKS,"source":"Transcript research-agent reproduction: Nvidia, Microsoft, Google, Amazon, Broadcom, TSMC, ASML"})
        if path == '/api/transcript-steps': return json_response(self,{"steps":TRANSCRIPT_STEPS})
        if path == '/api/next-tasks': return json_response(self,{"tasks":["Add Alpha Vantage key management and server-side quote fallback.","Add Convex cloud database migration after account auth.","Add scheduled code-quality review automation against GitHub commits.","Add watchlists and alerts every 12 hours.","Improve chart reliability with provider failover."]})
        return super().do_GET()
    def do_POST(self):
        if self.path.split('?',1)[0] == '/api/portfolio':
            length=int(self.headers.get('Content-Length','0') or 0); payload=json.loads(self.rfile.read(length) or b'{}')
            try: return json_response(self,save_holding(payload),201)
            except Exception as e: return json_response(self,{"error":str(e)},400)
        return json_response(self,{"error":"not found"},404)
    def do_DELETE(self):
        path=self.path.split('?',1)[0]
        if path.startswith('/api/portfolio/'):
            ticker=clean_ticker(path.rsplit('/',1)[-1])
            with sqlite3.connect(DB) as con: con.execute('delete from holdings where ticker=?',(ticker,))
            return json_response(self,portfolio_summary())
        return json_response(self,{"error":"not found"},404)

if __name__ == '__main__':
    init_db()
    print(f"Codex transcript build on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
