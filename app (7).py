import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import uvicorn
 
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("database", exist_ok=True)
os.makedirs("templates", exist_ok=True)
 
if not os.path.exists("static/css/style.css"):
    with open("static/css/style.css", "w") as f:
        f.write("/* SwingPro AI */")
 
app = FastAPI(title="SwingPro AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
 
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")
APP_PASSWORD  = os.getenv("APP_PASSWORD", "@Suresh9970")
ADMIN_PASSWORD= os.getenv("ADMIN_PASSWORD", "Admin@Suresh9970")
DB_PATH       = "database/trading.db"
 
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            role TEXT DEFAULT 'user',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT, entry REAL, sl REAL, target1 REAL, target2 REAL,
            sector TEXT, signal_strength TEXT, result TEXT DEFAULT 'pending',
            profit_loss REAL DEFAULT 0, notes TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT, message TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT UNIQUE, plan TEXT DEFAULT 'free',
            active INTEGER DEFAULT 1, queries_today INTEGER DEFAULT 0,
            total_queries INTEGER DEFAULT 0, joined_at TEXT, expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, amount REAL, plan TEXT, upi_ref TEXT,
            status TEXT DEFAULT 'pending', created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT, active INTEGER DEFAULT 1, created_at TEXT
        );
    """)
    defaults = {
        "agent_status": "on", "min_signal_strength": "all", "rr_ratio": "1:2",
        "sl_percent": "2", "scan_sectors": "IT,Pharma,Banking,Auto,Energy,FMCG",
        "blacklisted_stocks": "", "whitelisted_stocks": "", "free_daily_limit": "5",
        "maintenance_mode": "off", "agent_name": "SwingPro AI"
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()
 
init_db()
 
def get_setting(key):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None
 
def set_setting(key, value):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
 
def get_token(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.query_params.get("token", "")
 
def verify_token(token: str, role="user"):
    if not token:
        return None
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    conn.close()
    if not row:
        return None
    if role == "admin" and row["role"] != "admin":
        return None
    return dict(row)
 
@app.post("/api/login")
async def api_login(request: Request):
    body = await request.json()
    if body.get("password") == APP_PASSWORD:
        token = secrets.token_hex(32)
        conn = get_db()
        conn.execute("INSERT INTO sessions (token, role, created_at) VALUES (?, 'user', ?)",
                     (token, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return JSONResponse({"success": True, "token": token})
    return JSONResponse({"success": False, "error": "Wrong password!"}, status_code=401)
 
@app.post("/api/admin/login")
async def api_admin_login(request: Request):
    body = await request.json()
    if body.get("password") == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        conn = get_db()
        conn.execute("INSERT INTO sessions (token, role, created_at) VALUES (?, 'admin', ?)",
                     (token, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return JSONResponse({"success": True, "token": token})
    return JSONResponse({"success": False, "error": "Wrong admin password!"}, status_code=401)
 
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
 
@app.get("/agent", response_class=HTMLResponse)
async def agent_page(request: Request):
    return templates.TemplateResponse("agent.html", {"request": request})
 
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
 
async def get_stock_data(symbol: str):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev  = meta.get("chartPreviousClose", price)
        return {
            "symbol": symbol,
            "price": round(price, 2),
            "change_pct": round(((price-prev)/prev*100) if prev else 0, 2),
            "volume": meta.get("regularMarketVolume", 0),
            "high": meta.get("regularMarketDayHigh", price),
            "low": meta.get("regularMarketDayLow", price)
        }
    except:
        return None
 
async def get_market_news():
    if not NEWS_API_KEY:
        return [
            "Markets showing mixed trends today",
            "FII activity continues to influence Nifty",
            "Sector rotation observed in broader markets",
            "Global cues mixed ahead of key data releases",
            "RBI policy stance remains key market driver"
        ]
    try:
        url = f"https://newsapi.org/v2/everything?q=NSE+BSE+India+stock+market&language=en&sortBy=publishedAt&pageSize=10&apiKey={NEWS_API_KEY}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
        articles = r.json().get("articles", [])
        return [a["title"] for a in articles[:8] if a.get("title")]
    except:
        return ["Unable to fetch news — using cached data"]
 
async def ask_groq(messages, system=""):
    if not GROQ_API_KEY:
        return "Please add GROQ_API_KEY in HuggingFace Settings -> Secrets and Tokens."
    try:
        groq_messages = []
        if system:
            groq_messages.append({"role": "system", "content": system})
        for msg in messages:
            groq_messages.append({"role": msg["role"], "content": msg["content"]})
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": groq_messages,
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
            )
        resp = r.json()
        if "choices" in resp and resp["choices"]:
            return resp["choices"][0]["message"]["content"]
        elif "error" in resp:
            return f"Groq Error: {resp['error'].get('message', 'Unknown error')}"
        else:
            return f"Unexpected response: {resp}"
    except Exception as e:
        return f"Connection error: {str(e)}"
 
@app.post("/api/chat")
async def chat(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    if get_setting("agent_status") == "off":
        return JSONResponse({"reply": "Agent is currently offline."})
    body = await request.json()
    user_msg = body.get("message", "").strip()
    if not user_msg:
        raise HTTPException(400)
 
    conn = get_db()
    conn.execute("INSERT INTO chat_history (role, message, created_at) VALUES ('user', ?, ?)",
                 (user_msg, datetime.now().isoformat()))
    conn.commit()
    rows = conn.execute("SELECT role, message FROM chat_history ORDER BY id DESC LIMIT 10").fetchall()
    trades_data = conn.execute("SELECT result FROM trades WHERE result != 'pending' ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
 
    history = [{"role": r["role"], "content": r["message"]} for r in reversed(rows)]
    wins = sum(1 for t in trades_data if t["result"] == "win")
    total = len(trades_data)
    win_rate = f"{round(wins/total*100)}%" if total > 0 else "No trades yet"
    news = await get_market_news()
 
    system = f"""You are SwingPro AI, an expert Indian stock market swing trading assistant.
 
SETTINGS:
- Sectors to scan: {get_setting('scan_sectors')}
- Stop Loss: {get_setting('sl_percent')}%
- Risk:Reward: {get_setting('rr_ratio')}
- Blacklisted stocks: {get_setting('blacklisted_stocks') or 'None'}
- Watchlist: {get_setting('whitelisted_stocks') or 'None'}
- Historical win rate: {win_rate} from {total} trades
 
LATEST MARKET NEWS:
{chr(10).join(f'- {n}' for n in news[:5])}
 
INSTRUCTIONS:
1. For stock signals, always use this format:
   Stock: [NAME]
   Entry: Rs [price]
   SL: Rs [price]
   Target 1: Rs [price]
   Target 2: Rs [price]
   Signal: Strong/Moderate/Weak
   Reason: [why this stock]
 
2. Give 3-5 stocks when asked for best trades
3. Always mention: Verify before trading. Use strict SL.
4. Focus only on NSE/BSE listed Indian stocks
5. Consider global news impact on Indian markets
6. Be friendly and clear"""
 
    reply = await ask_groq(history, system)
    conn = get_db()
    conn.execute("INSERT INTO chat_history (role, message, created_at) VALUES ('assistant', ?, ?)",
                 (reply, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return JSONResponse({"reply": reply})
 
@app.get("/api/market-overview")
async def market_overview(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    indices = ["^NSEI", "^BSESN", "RELIANCE", "TCS", "HDFCBANK", "INFY", "SUNPHARMA"]
    results = [d for d in [await get_stock_data(s) for s in indices] if d]
    return JSONResponse({"indices": results, "news": (await get_market_news())[:5]})
 
@app.post("/api/trades")
async def add_trade(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    body = await request.json()
    conn = get_db()
    conn.execute(
        "INSERT INTO trades (stock,entry,sl,target1,target2,sector,signal_strength,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (body.get("stock"), body.get("entry"), body.get("sl"),
         body.get("target1"), body.get("target2"), body.get("sector"),
         body.get("signal_strength"), body.get("notes"), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return JSONResponse({"success": True})
 
@app.get("/api/trades")
async def get_trades(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    trades = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return JSONResponse({"trades": [dict(t) for t in trades]})
 
@app.put("/api/trades/{tid}")
async def update_trade(tid: int, request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    body = await request.json()
    conn = get_db()
    conn.execute("UPDATE trades SET result=?, profit_loss=?, notes=? WHERE id=?",
                 (body.get("result"), body.get("profit_loss", 0), body.get("notes", ""), tid))
    conn.commit()
    conn.close()
    return JSONResponse({"success": True})
 
@app.get("/api/performance")
async def get_performance(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    trades = [dict(t) for t in conn.execute("SELECT * FROM trades WHERE result != 'pending'").fetchall()]
    conn.close()
    total = len(trades)
    wins = sum(1 for t in trades if t["result"] == "win")
    return JSONResponse({
        "total": total, "wins": wins, "losses": total-wins,
        "win_rate": round(wins/total*100,1) if total else 0,
        "total_pnl": round(sum(t["profit_loss"] for t in trades), 2),
        "trades": trades
    })
 
def req_admin(request: Request):
    if not verify_token(get_token(request), "admin"):
        raise HTTPException(403)
 
@app.get("/api/admin/dashboard")
async def admin_dashboard(request: Request):
    req_admin(request)
    conn = get_db()
    c = conn.execute
    wins = c("SELECT COUNT(*) as x FROM trades WHERE result='win'").fetchone()["x"]
    done = c("SELECT COUNT(*) as x FROM trades WHERE result!='pending'").fetchone()["x"]
    data = {
        "stats": {
            "total_users": c("SELECT COUNT(*) as x FROM users").fetchone()["x"],
            "active_users": c("SELECT COUNT(*) as x FROM users WHERE active=1").fetchone()["x"],
            "paid_users": c("SELECT COUNT(*) as x FROM users WHERE plan!='free'").fetchone()["x"],
            "pending_payments": c("SELECT COUNT(*) as x FROM payments WHERE status='pending'").fetchone()["x"],
            "total_revenue": c("SELECT SUM(amount) as x FROM payments WHERE status='approved'").fetchone()["x"] or 0,
            "total_trades": c("SELECT COUNT(*) as x FROM trades").fetchone()["x"],
            "wins": wins, "losses": done-wins,
            "win_rate": round(wins/done*100,1) if done else 0,
            "agent_status": get_setting("agent_status"),
            "maintenance_mode": get_setting("maintenance_mode")
        },
        "users": [dict(r) for r in c("SELECT * FROM users ORDER BY id DESC").fetchall()],
        "payments": [dict(r) for r in c("SELECT p.*,u.name,u.email FROM payments p LEFT JOIN users u ON p.user_id=u.id ORDER BY p.id DESC").fetchall()],
        "announcements": [dict(r) for r in c("SELECT * FROM announcements ORDER BY id DESC").fetchall()],
        "settings": {r["key"]: r["value"] for r in c("SELECT * FROM settings").fetchall()}
    }
    conn.close()
    return JSONResponse(data)
 
@app.post("/api/admin/settings")
async def update_settings(request: Request):
    req_admin(request)
    for k, v in (await request.json()).items():
        set_setting(k, str(v))
    return JSONResponse({"success": True})
 
@app.post("/api/admin/users")
async def add_user(request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name,email,plan,active,joined_at,expires_at) VALUES (?,?,?,1,?,?)",
            (body["name"], body["email"], body.get("plan","free"),
             datetime.now().isoformat(), (datetime.now()+timedelta(days=30)).isoformat()))
        conn.commit()
        return JSONResponse({"success": True})
    except:
        return JSONResponse({"success": False, "error": "Email exists"})
    finally:
        conn.close()
 
@app.put("/api/admin/users/{uid}")
async def update_user(uid: int, request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    fields, values = [], []
    for k in ["name","email","plan","active"]:
        if k in body:
            fields.append(f"{k}=?"); values.append(body[k])
    if "extend_days" in body:
        fields.append("expires_at=?")
        values.append((datetime.now()+timedelta(days=int(body["extend_days"]))).isoformat())
    values.append(uid)
    conn.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", values)
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.delete("/api/admin/users/{uid}")
async def delete_user(uid: int, request: Request):
    req_admin(request)
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (uid,))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.post("/api/admin/payments")
async def add_payment(request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (user_id,amount,plan,upi_ref,status,created_at) VALUES (?,?,?,?,?,?)",
        (body.get("user_id"), body.get("amount"), body.get("plan"),
         body.get("upi_ref"), body.get("status","pending"), datetime.now().isoformat()))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.put("/api/admin/payments/{pid}")
async def update_payment(pid: int, request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    conn.execute("UPDATE payments SET status=? WHERE id=?", (body["status"], pid))
    if body["status"] == "approved":
        pmt = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if pmt:
            conn.execute("UPDATE users SET plan=?,active=1,expires_at=? WHERE id=?",
                (pmt["plan"], (datetime.now()+timedelta(days=30)).isoformat(), pmt["user_id"]))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.post("/api/admin/announcement")
async def add_announcement(request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    conn.execute("INSERT INTO announcements (message,active,created_at) VALUES (?,1,?)",
                 (body["message"], datetime.now().isoformat()))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.delete("/api/admin/announcement/{aid}")
async def del_announcement(aid: int, request: Request):
    req_admin(request)
    conn = get_db()
    conn.execute("DELETE FROM announcements WHERE id=?", (aid,))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.delete("/api/admin/trades/reset")
async def reset_trades(request: Request):
    req_admin(request)
    conn = get_db()
    conn.execute("DELETE FROM trades")
    conn.execute("DELETE FROM chat_history")
    conn.commit(); conn.close()
    return JSONResponse({"success": True})
 
@app.get("/api/admin/trades")
async def admin_trades(request: Request):
    req_admin(request)
    conn = get_db()
    trades = conn.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()
    conn.close()
    return JSONResponse({"trades": [dict(t) for t in trades]})
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)