import os
import sqlite3
import secrets
import json
import random
from datetime import datetime, timedelta, timezone
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
        f.write("/* Chetak.trade AI */")

app = FastAPI(title="Chetak.trade — AI Swing Trading")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY   = os.getenv("NEWS_API_KEY", "")
APP_PASSWORD   = os.getenv("APP_PASSWORD", "trade123")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
UPI_ID         = os.getenv("UPI_ID", "your-upi@paytm")       # ← Set in HF Secrets
WHATSAPP_NUM   = os.getenv("WHATSAPP_NUM", "919999999999")    # ← Set in HF Secrets
DB_PATH        = "database/trading.db"

# ─────────────────────────────────────────────────────────────────────────────
# SUBSCRIPTION PLANS CONFIG
# ─────────────────────────────────────────────────────────────────────────────
PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "price_label": "₹0",
        "duration_days": 9999,
        "daily_query_limit": 3,
        "features": [
            "3 AI queries per day",
            "Basic stock analysis",
            "Market overview",
            "Watchlist (5 stocks)",
        ],
        "no_features": [
            "Daily AI Picks",
            "Crypto analysis",
            "Stock screener",
            "Fundamental analysis",
            "Price alerts",
        ],
        "badge": "",
        "color": "#6b7280",
    },
    "basic": {
        "name": "Basic",
        "price": 299,
        "price_label": "₹299",
        "duration_days": 30,
        "daily_query_limit": 25,
        "features": [
            "25 AI queries per day",
            "Daily AI stock picks (5/day)",
            "Full stock analysis",
            "Market overview & news",
            "Watchlist (unlimited)",
            "Price alerts (10 active)",
            "Trade journal",
            "Performance tracking",
        ],
        "no_features": [
            "Crypto analysis",
            "Advanced screener",
            "Priority support",
        ],
        "badge": "Popular",
        "color": "#3b82f6",
    },
    "pro": {
        "name": "Pro",
        "price": 599,
        "price_label": "₹599",
        "duration_days": 30,
        "daily_query_limit": 100,
        "features": [
            "100 AI queries per day",
            "Daily AI stock picks (5/day)",
            "Crypto analysis (BTC, ETH, SOL...)",
            "Advanced stock screener",
            "Fundamental analysis",
            "Unlimited price alerts",
            "All Basic features",
            "Email support",
        ],
        "no_features": [
            "WhatsApp alerts",
            "1-on-1 support",
        ],
        "badge": "Best Value",
        "color": "#8b5cf6",
    },
    "elite": {
        "name": "Elite",
        "price": 999,
        "price_label": "₹999",
        "duration_days": 30,
        "daily_query_limit": 999999,
        "features": [
            "Unlimited AI queries",
            "Everything in Pro",
            "WhatsApp trade alerts",
            "1-on-1 trading support",
            "Early access to new features",
            "Custom sector watchlists",
            "Priority AI responses",
            "Monthly portfolio review",
        ],
        "no_features": [],
        "badge": "Premium",
        "color": "#f59e0b",
    },
}

PLAN_PERMISSIONS = {
    "free":  {"screener": False, "fundamentals": False, "daily_picks": False, "alerts": False},
    "basic": {"screener": False, "fundamentals": True,  "daily_picks": True,  "alerts": True},
    "pro":   {"screener": True,  "fundamentals": True,  "daily_picks": True,  "alerts": True},
    "elite": {"screener": True,  "fundamentals": True,  "daily_picks": True,  "alerts": True},
}

# ─────────────────────────────────────────────────────────────────────────────
# NSE VERIFIED SYMBOLS
# ─────────────────────────────────────────────────────────────────────────────
NSE_LARGE_CAP = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","HINDUNILVR","ITC","SBIN",
    "BHARTIARTL","KOTAKBANK","LT","AXISBANK","ASIANPAINT","MARUTI","NESTLEIND",
    "TITAN","BAJFINANCE","WIPRO","ULTRACEMCO","BAJAJFINSV","NTPC","POWERGRID",
    "SUNPHARMA","TECHM","HCLTECH","ONGC","COALINDIA","JSWSTEEL","TATASTEEL",
    "TATAMOTORS","ADANIENT","ADANIPORTS","GRASIM","DIVISLAB","CIPLA","DRREDDY",
    "BPCL","INDUSINDBK","M&M","HINDALCO","APOLLOHOSP","EICHERMOT","BRITANNIA",
    "SHREECEM","HEROMOTOCO","BAJAJ-AUTO","TATACONSUM","VEDL","IOC","LTIM"
]
NSE_MID_CAP = [
    "PERSISTENT","MPHASIS","COFORGE","LTTS","TATAELXSI","KPITTECH","ZOMATO",
    "NAUKRI","POLICYBZR","IRCTC","INDIAMART","DIXON","WHIRLPOOL","AMBER",
    "CROMPTON","HAVELLS","VOLTAS","BLUESTAR","VGUARD","POLYCAB","KANSAINER",
    "BERGER","PIIND","AARTIIND","DEEPAKNI","FINEORG","NAVINFLUOR","ASTRAL",
    "SUPREMEIND","ATUL","SYNGENE","ALKEM","IPCALAB","TORNTPHARM","AUROPHARMA",
    "LUPIN","BIOCON","GLAND","LALPATHLAB","METROPOLIS","MAXHEALTH","KIMS",
    "FORTIS","RAINBOW","SJVN","NHPC","IRFC","RVNL","RAILTEL","IRCON",
    "GMRINFRA","CONCOR","CESC","TPWR","NLCINDIA","SUZLON","INOXWIND",
    "EXIDEIND","AMARAJABAT","TVSMOTOR","MOTHERSON","BALKRISIND","APOLLOTYRE",
    "CEATLTD","MINDA","SUPRAJIT","CRAFTSMAN","SUNDRMFAST","ENDURANCE"
]
NSE_SMALL_CAP = [
    "RITES","HFCL","TEJASNET","STLTECH","OPTIEMUS","ROUTE","TANLA",
    "LATENTVIEW","MAPMYINDIA","NAZARA","CAMPUS","KAYNES",
    "SYRMA","AVALON","IDEAFORGE","ZAGGLE","ETHOS","SENCO",
    "GESHIP","SARDAEN","GALLANTT","MAITHANALL","LLOYDSME","PRAJIND",
    "ELECON","GREENPANEL","CENTURYPLY","GREENPLY","SKIPPER","KSB",
    "THERMAX","AIAENG","GRINDWELL","CARBORUNIV","KALPATARU",
    "KNRCON","PNCINFRA","HGINFRA","GPPL","ESABINDIA","WENDT"
]
ALL_NSE_SYMBOLS = NSE_LARGE_CAP + NSE_MID_CAP + NSE_SMALL_CAP


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
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
            user_id INTEGER,
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
            name TEXT, email TEXT UNIQUE,
            password TEXT DEFAULT '',
            plan TEXT DEFAULT 'free',
            active INTEGER DEFAULT 1,
            queries_today INTEGER DEFAULT 0,
            queries_reset_date TEXT,
            total_queries INTEGER DEFAULT 0,
            joined_at TEXT,
            expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            amount REAL,
            plan TEXT,
            upi_ref TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            approved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT, active INTEGER DEFAULT 1, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY, added_at TEXT, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, condition TEXT, target_price REAL,
            triggered INTEGER DEFAULT 0, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            started_at TEXT,
            expires_at TEXT,
            payment_id INTEGER,
            active INTEGER DEFAULT 1
        );
    """)
    defaults = {
        "agent_status": "on", "min_signal_strength": "all", "rr_ratio": "1:2",
        "sl_percent": "2", "scan_sectors": "IT,Pharma,Banking,Auto,Energy,FMCG,Metal,Capital Goods",
        "blacklisted_stocks": "", "whitelisted_stocks": "", "free_daily_limit": "3",
        "maintenance_mode": "off", "agent_name": "Chetak.trade AI",
        "upi_id": UPI_ID, "whatsapp_num": WHATSAPP_NUM,
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

def get_user_from_token(token: str):
    """Get full user record from session token"""
    if not token:
        return None
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    if not session:
        conn.close()
        return None
    user = None
    if session["user_id"]:
        user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        user = dict(user) if user else None
    conn.close()
    return user

def check_plan_permission(token: str, feature: str) -> tuple:
    """Returns (allowed: bool, reason: str, plan: str)"""
    user = get_user_from_token(token)
    if not user:
        # Guest with no account — check if it's a direct password login
        session = None
        conn = get_db()
        s = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        conn.close()
        if s and s["role"] == "admin":
            return True, "admin", "admin"
        # No user record = free plan
        plan = "free"
    else:
        plan = user.get("plan", "free")
        # Check subscription expiry
        expires_at = user.get("expires_at")
        if expires_at and plan != "free":
            try:
                exp = datetime.fromisoformat(expires_at)
                if datetime.now() > exp:
                    plan = "free"  # Expired — downgrade
            except:
                pass

    perms = PLAN_PERMISSIONS.get(plan, PLAN_PERMISSIONS["free"])
    allowed = perms.get(feature, False)
    if not allowed:
        upgrade_needed = {"screener": "Pro", "fundamentals": "Basic",
                          "daily_picks": "Basic", "alerts": "Basic"}.get(feature, "Basic")
        reason = f"🔒 This feature requires {upgrade_needed} plan. Visit /plans to upgrade."
        return False, reason, plan
    return True, "ok", plan

def check_query_limit(token: str) -> tuple:
    """Returns (allowed: bool, remaining: int, plan: str)"""
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    if not session:
        conn.close()
        return False, 0, "free"
    if session["role"] == "admin":
        conn.close()
        return True, 999, "admin"

    today = datetime.now().strftime("%Y-%m-%d")

    if session["user_id"]:
        user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if user:
            plan = user["plan"] or "free"
            # Check expiry
            expires_at = user.get("expires_at")
            if expires_at and plan != "free":
                try:
                    if datetime.now() > datetime.fromisoformat(expires_at):
                        plan = "free"
                except:
                    pass
            limit = PLANS.get(plan, PLANS["free"])["daily_query_limit"]
            # Reset counter if new day
            reset_date = user["queries_reset_date"] or ""
            if reset_date != today:
                conn.execute("UPDATE users SET queries_today=0, queries_reset_date=? WHERE id=?",
                             (today, user["id"]))
                conn.commit()
                conn.close()
                return True, limit, plan
            used = user["queries_today"] or 0
            remaining = max(0, limit - used)
            conn.close()
            if remaining <= 0:
                return False, 0, plan
            return True, remaining, plan

    # No user account (password-only login) = free
    limit = int(get_setting("free_daily_limit") or 3)
    conn.close()
    return True, limit, "free"

def increment_query_count(token: str):
    conn = get_db()
    session = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    if session and session["user_id"] and session["role"] != "admin":
        conn.execute("UPDATE users SET queries_today=queries_today+1, total_queries=total_queries+1 WHERE id=?",
                     (session["user_id"],))
        conn.commit()
    conn.close()

def req_admin(request: Request):
    if not verify_token(get_token(request), "admin"):
        raise HTTPException(403, "Admin access required")

def get_recent_stocks(days: int = 7) -> list:
    conn = get_db()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT stock FROM trades WHERE created_at > ? AND notes LIKE '%AGENT_PICK%'", (cutoff,)
    ).fetchall()
    rows2 = conn.execute(
        "SELECT stock FROM trades WHERE created_at > ?",
        ((datetime.now() - timedelta(days=3)).isoformat(),)
    ).fetchall()
    conn.close()
    return list(set([r["stock"] for r in rows] + [r["stock"] for r in rows2]))

# ─────────────────────────────────────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────────────────────────────────────
async def get_stock_data(symbol: str):
    headers_list = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         "Accept": "application/json", "Referer": "https://finance.yahoo.com/"},
        {"User-Agent": "python-requests/2.31.0", "Accept": "*/*"},
    ]
    for suffix in [".NS", ".BO", ""]:
        sym = f"{symbol}{suffix}"
        for hdrs in headers_list:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url, headers=hdrs)
                if r.status_code != 200:
                    continue
                data = r.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    continue
                meta = result[0]["meta"]
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                if price and price > 0:
                    return {
                        "symbol": symbol, "display_symbol": sym,
                        "price": round(price, 2),
                        "change_pct": round(((price - prev) / prev * 100) if prev else 0, 2),
                        "volume": meta.get("regularMarketVolume", 0),
                        "high": meta.get("regularMarketDayHigh", price),
                        "low": meta.get("regularMarketDayLow", price),
                        "prev_close": round(prev, 2)
                    }
            except:
                continue
    return None

async def get_market_news():
    if not NEWS_API_KEY:
        return [
            "Nifty 50 consolidating near key support levels",
            "FII net buyers in Indian equities this week",
            "RBI policy stance remains growth-supportive",
            "IT sector recovery on global demand signals",
            "PSU banks outperform on NPA improvement data"
        ]
    try:
        url = f"https://newsapi.org/v2/everything?q=NSE+BSE+India+stock+market&language=en&sortBy=publishedAt&pageSize=10&apiKey={NEWS_API_KEY}"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
        return [a["title"] for a in r.json().get("articles", [])[:8] if a.get("title")]
    except:
        return ["Unable to fetch news — using market intelligence"]

async def ask_groq(messages, system=""):
    if not GROQ_API_KEY:
        return "⚠️ GROQ_API_KEY not set. Add it in HuggingFace Space → Settings → Secrets."
    try:
        groq_messages = []
        if system:
            groq_messages.append({"role": "system", "content": system})
        for msg in messages:
            groq_messages.append({"role": msg["role"], "content": msg["content"]})
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": groq_messages,
                      "max_tokens": 2000, "temperature": 0.85}
            )
        resp = r.json()
        if "choices" in resp and resp["choices"]:
            return resp["choices"][0]["message"]["content"]
        elif "error" in resp:
            return f"Groq Error: {resp['error'].get('message', 'Unknown error')}"
        return f"Unexpected response: {resp}"
    except Exception as e:
        return f"Connection error: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/login")
async def api_login(request: Request):
    body = await request.json()
    password = body.get("password", "").strip()
    email    = body.get("email", "").strip().lower()

    # Admin login — only by admin password, no email needed
    if password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        conn = get_db()
        conn.execute("INSERT INTO sessions (token, role, user_id, created_at) VALUES (?, 'admin', NULL, ?)",
                     (token, datetime.now().isoformat()))
        conn.commit(); conn.close()
        return JSONResponse({"success": True, "token": token, "role": "admin", "plan": "admin"})

    # User login — email + their own chosen password
    if not email:
        return JSONResponse({"success": False, "error": "Please enter your email address."}, status_code=400)
    if not password:
        return JSONResponse({"success": False, "error": "Please enter your password."}, status_code=400)

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user:
        return JSONResponse({"success": False, "error": "No account found with this email. Please subscribe first."}, status_code=401)
    if not user["active"]:
        return JSONResponse({"success": False, "error": "Account deactivated. Contact support on WhatsApp."}, status_code=403)

    # Check user's own password
    stored_pw = user["password"] or ""
    if stored_pw != password:
        return JSONResponse({"success": False, "error": "Incorrect password. Use the password you set while subscribing."}, status_code=401)

    token = secrets.token_hex(32)
    conn = get_db()
    conn.execute("INSERT INTO sessions (token, role, user_id, created_at) VALUES (?, 'user', ?, ?)",
                 (token, user["id"], datetime.now().isoformat()))
    conn.commit(); conn.close()
    plan = user["plan"] or "free"
    return JSONResponse({"success": True, "token": token, "role": "user",
                         "plan": plan, "name": user["name"]})

@app.post("/api/admin/login")
async def api_admin_login(request: Request):
    body = await request.json()
    if body.get("password") == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        conn = get_db()
        conn.execute("INSERT INTO sessions (token, role, user_id, created_at) VALUES (?, 'admin', NULL, ?)",
                     (token, datetime.now().isoformat()))
        conn.commit(); conn.close()
        return JSONResponse({"success": True, "token": token})
    return JSONResponse({"success": False, "error": "Wrong admin password!"}, status_code=401)

# ─────────────────────────────────────────────────────────────────────────────
# SUBSCRIPTION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/plans")
async def get_plans():
    """Public endpoint — returns all plan details"""
    upi = get_setting("upi_id") or UPI_ID
    wa  = get_setting("whatsapp_num") or WHATSAPP_NUM
    return JSONResponse({"plans": PLANS, "upi_id": upi, "whatsapp_num": wa})

@app.post("/api/subscribe")
async def subscribe(request: Request):
    """User submits payment request — creates pending payment"""
    body = await request.json()
    name     = body.get("name", "").strip()
    email    = body.get("email", "").strip().lower()
    plan     = body.get("plan", "basic")
    upi_ref  = body.get("upi_ref", "").strip()

    user_password = body.get("password", "").strip()

    if not name or not email or not upi_ref:
        return JSONResponse({"success": False, "error": "Name, email, and UPI reference are required."}, status_code=400)
    if not user_password or len(user_password) < 6:
        return JSONResponse({"success": False, "error": "Please set a password (minimum 6 characters). You will use this to login."}, status_code=400)
    if plan not in PLANS:
        return JSONResponse({"success": False, "error": "Invalid plan selected."}, status_code=400)
    # For paid plans, validate UPI reference
    if plan != "free" and (not upi_ref or len(upi_ref) < 6):
        return JSONResponse({"success": False, "error": "Please enter a valid UPI transaction reference."}, status_code=400)

    amount = PLANS[plan]["price"] if plan != "free" else 0
    conn = get_db()

    # Create or find user
    existing = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        user_id = existing["id"]
        # Update password if re-subscribing
        conn.execute("UPDATE users SET name=?, password=? WHERE id=?",
                     (name, user_password, user_id))
        conn.commit()
    else:
        conn.execute(
            "INSERT INTO users (name, email, password, plan, active, queries_today, total_queries, joined_at, expires_at) VALUES (?,?,?,?,1,0,0,?,?)",
            (name, email, user_password, "free", datetime.now().isoformat(),
             (datetime.now() + timedelta(days=30)).isoformat())
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]

    # Check for duplicate UPI ref (skip for guest registrations)
    if not upi_ref.startswith("GUEST-"):
        dup = conn.execute("SELECT id FROM payments WHERE upi_ref=?", (upi_ref,)).fetchone()
        if dup:
            conn.close()
            return JSONResponse({"success": False, "error": "This UPI reference has already been submitted. Contact support if this is an error."}, status_code=400)

    # Create payment record (free plan auto-approved)
    pmt_status = "approved" if plan == "free" else "pending"
    conn.execute(
        "INSERT INTO payments (user_id, name, email, amount, plan, upi_ref, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (user_id, name, email, amount, plan, upi_ref, pmt_status, datetime.now().isoformat())
    )
    # Auto-activate free plan
    if plan == "free":
        conn.execute("UPDATE users SET plan='free', active=1 WHERE id=?", (user_id,))
    conn.commit(); conn.close()

    if plan == "free":
        return JSONResponse({
            "success": True,
            "message": f"✅ Guest account created! Login with Email: {email} and your password."
        })
    return JSONResponse({
        "success": True,
        "message": f"✅ Payment submitted for {PLANS[plan]['name']} plan! Your account will be activated within 2-4 hours after UPI verification. Login with: Email: {email} · Password: the one you just set."
    })

@app.get("/api/my-plan")
async def my_plan(request: Request):
    """Returns current user's plan, limits, usage"""
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)

    session_data = None
    conn = get_db()
    s = conn.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
    if s:
        session_data = dict(s)
    conn.close()

    if session_data and session_data["role"] == "admin":
        return JSONResponse({
            "plan": "admin", "name": "Admin", "email": "",
            "daily_limit": 999999, "used_today": 0, "remaining": 999999,
            "expires_at": None, "features": {"screener": True,
            "fundamentals": True, "daily_picks": True, "alerts": True}
        })

    user = get_user_from_token(token)
    if not user:
        limit = int(get_setting("free_daily_limit") or 3)
        return JSONResponse({
            "plan": "free", "name": "Guest", "email": "",
            "daily_limit": limit, "used_today": 0, "remaining": limit,
            "expires_at": None, "features": PLAN_PERMISSIONS["free"]
        })

    plan = user.get("plan", "free")
    expires_at = user.get("expires_at")
    if expires_at and plan != "free":
        try:
            if datetime.now() > datetime.fromisoformat(expires_at):
                plan = "free"
        except:
            pass

    limit = PLANS.get(plan, PLANS["free"])["daily_query_limit"]
    today = datetime.now().strftime("%Y-%m-%d")
    used = user.get("queries_today", 0)
    if user.get("queries_reset_date", "") != today:
        used = 0

    return JSONResponse({
        "plan": plan,
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "daily_limit": limit,
        "used_today": used,
        "remaining": max(0, limit - used),
        "expires_at": expires_at,
        "total_queries": user.get("total_queries", 0),
        "features": PLAN_PERMISSIONS.get(plan, PLAN_PERMISSIONS["free"])
    })

@app.get("/api/payment-status")
async def payment_status(request: Request):
    """Check payment status by email"""
    email = request.query_params.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "Email required")
    conn = get_db()
    payments = conn.execute(
        "SELECT * FROM payments WHERE email=? ORDER BY id DESC LIMIT 5", (email,)
    ).fetchall()
    conn.close()
    return JSONResponse({"payments": [dict(p) for p in payments]})

# ─────────────────────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/plans", response_class=HTMLResponse)
async def plans_page(request: Request):
    return templates.TemplateResponse("plans.html", {"request": request})

@app.get("/agent", response_class=HTMLResponse)
async def agent_page(request: Request):
    return templates.TemplateResponse("agent.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# ─────────────────────────────────────────────────────────────────────────────
# CHAT — WITH PLAN LIMIT ENFORCEMENT
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    if get_setting("agent_status") == "off":
        return JSONResponse({"reply": "⚠️ Agent is currently offline. Contact admin."})

    # Check daily query limit
    allowed, remaining, plan = check_query_limit(token)
    if not allowed:
        upgrade_plan = "Basic" if plan == "free" else "Pro"
        return JSONResponse({
            "reply": f"⏳ Daily query limit reached for your **{plan.title()} plan**.\n\n"
                     f"🔒 Upgrade to **{upgrade_plan}** for more queries.\n"
                     f"👉 Visit `/plans` to subscribe.",
            "limit_reached": True,
            "plan": plan
        })

    body = await request.json()
    user_msg = body.get("message", "").strip()
    if not user_msg:
        raise HTTPException(400)

    conn = get_db()
    conn.execute("INSERT INTO chat_history (role, message, created_at) VALUES ('user', ?, ?)",
                 (user_msg, datetime.now().isoformat()))
    conn.commit()
    rows = conn.execute("SELECT role, message FROM chat_history ORDER BY id DESC LIMIT 12").fetchall()
    trades_data = conn.execute("SELECT result FROM trades WHERE result != 'pending' ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    history = [{"role": r["role"], "content": r["message"]} for r in reversed(rows)]
    wins = sum(1 for t in trades_data if t["result"] == "win")
    total = len(trades_data)
    win_rate = f"{round(wins/total*100)}%" if total > 0 else "No history yet"
    news = await get_market_news()

    cap_filter    = body.get("cap_filter", "all")
    sector_filter = body.get("sector_filter", "all")
    market_mode   = body.get("market_mode", "stocks")
    recent_stocks = get_recent_stocks(days=7)
    recent_str    = ", ".join(recent_stocks) if recent_stocks else "None"

    sample_large = random.sample(NSE_LARGE_CAP, min(15, len(NSE_LARGE_CAP)))
    sample_mid   = random.sample(NSE_MID_CAP, min(20, len(NSE_MID_CAP)))
    sample_small = random.sample(NSE_SMALL_CAP, min(15, len(NSE_SMALL_CAP)))

    if cap_filter == "large":
        symbol_pool = sample_large
    elif cap_filter == "mid":
        symbol_pool = sample_mid
    elif cap_filter == "small":
        symbol_pool = sample_small
    else:
        symbol_pool = sample_large[:8] + sample_mid[:12] + sample_small[:5]

    cap_ctx = {
        "large": f"Focus ONLY on Large Cap NSE stocks. Pool: {', '.join(sample_large)}",
        "mid":   f"Focus ONLY on Mid Cap NSE stocks. Pool: {', '.join(sample_mid)}",
        "small": f"Focus ONLY on Small Cap NSE stocks. Pool: {', '.join(sample_small)}",
        "all":   f"Cover all market caps. Pool: {', '.join(symbol_pool)}"
    }.get(cap_filter, f"Cover all caps. Pool: {', '.join(symbol_pool)}")

    system = f"""You are the world's best professional swing trader — top 0.1% globally.
15+ years full-time profitable trading on Indian NSE/BSE markets.

YOUR EDGE:
- Price action + volume = your bible. Never trade against the trend.
- Minimum 1:2 Risk:Reward. No exceptions. Tight SL, wide targets.
- You NEVER repeat the same stock twice in a week.
- Macro drives direction, technicals drive timing, news is the catalyst.

TODAY'S CONTEXT:
- Mode: {market_mode.upper()} | Cap: {cap_filter.upper()} | Sector: {sector_filter}
- {cap_ctx}
- SL: {get_setting("sl_percent")}% | R:R: {get_setting("rr_ratio")}
- Sectors: {get_setting("scan_sectors")}
- Blacklisted: {get_setting("blacklisted_stocks") or "None"}
- Win Rate: {win_rate} from {total} trades

⚠️ DO NOT suggest these recently tracked stocks:
{recent_str}

NEWS: {chr(10).join(f"- {n}" for n in news[:5])}

FOR EVERY STOCK PICK USE EXACTLY THIS FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {{SYMBOL}} — {{Company Name}}
🏭 Sector: [sector] | 📊 Cap: [Large/Mid/Small]
💹 Entry Zone: ₹[min]–₹[max]
🛑 Stop Loss: ₹[price] ([x]% risk)
🎯 T1: ₹[price] — in [x–y] days (R:R 1:[x])
🎯 T2: ₹[price] — in [x–y] weeks (R:R 1:[x])
⏱ Hold: [x]–[y] days
📊 Signal: Strong/Moderate
📰 Why: [2 lines — technical + catalyst]
🔗 NSE Symbol: [EXACT] (searchable on Zerodha/Groww)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
1. Only real NSE-listed symbols. Must work on Zerodha/Groww.
2. Give 3-5 picks when asked for recommendations.
3. Never suggest stocks from the avoid list above.
4. Realistic 2025 NSE price levels.
5. Sharp, direct, zero fluff. Professional trader tone."""

    reply = await ask_groq(history, system)
    increment_query_count(token)

    conn = get_db()
    conn.execute("INSERT INTO chat_history (role, message, created_at) VALUES ('assistant', ?, ?)",
                 (reply, datetime.now().isoformat()))
    conn.commit(); conn.close()

    return JSONResponse({
        "reply": reply,
        "queries_remaining": remaining - 1,
        "plan": plan
    })

# ─────────────────────────────────────────────────────────────────────────────
# MARKET OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/market-overview")
async def market_overview(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    indices = ["RELIANCE","TCS","HDFCBANK","INFY","SUNPHARMA","SBIN","ITC","BHARTIARTL"]
    results = [d for d in [await get_stock_data(s) for s in indices] if d]
    return JSONResponse({"indices": results, "news": (await get_market_news())[:6]})

# ─────────────────────────────────────────────────────────────────────────────
# TRADES
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/trades")
async def add_trade(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    body = await request.json()
    conn = get_db()
    conn.execute("INSERT INTO trades (stock,entry,sl,target1,target2,sector,signal_strength,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (body.get("stock","").upper(), body.get("entry"), body.get("sl"), body.get("target1"),
         body.get("target2"), body.get("sector"), body.get("signal_strength"),
         body.get("notes"), datetime.now().isoformat()))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

@app.get("/api/trades")
async def get_trades(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    trades = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 100").fetchall()
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
    conn.commit(); conn.close()
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
    return JSONResponse({"total": total, "wins": wins, "losses": total - wins,
        "win_rate": round(wins / total * 100, 1) if total else 0,
        "total_pnl": round(sum(t["profit_loss"] for t in trades), 2), "trades": trades})

@app.post("/api/trades/auto-select")
async def auto_select_trade(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    body = await request.json()
    conn = get_db()
    inserted = []
    for stock in body.get("stocks", []):
        conn.execute("INSERT INTO trades (stock,entry,sl,target1,target2,sector,signal_strength,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (stock.get("stock","").upper(), stock.get("entry",0), stock.get("sl",0),
             stock.get("target1",0), stock.get("target2",0), stock.get("sector",""),
             stock.get("signal_strength","Moderate"),
             f"AUTO|cap:{stock.get('cap','mid')}|t1_days:{stock.get('t1_days',7)}|t2_days:{stock.get('t2_days',14)}",
             datetime.now().isoformat()))
        inserted.append(stock.get("stock","").upper())
    conn.commit(); conn.close()
    return JSONResponse({"success": True, "added": inserted})

# ─────────────────────────────────────────────────────────────────────────────
# STOCK ANALYSIS (plan-gated: Basic+)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/stock-analysis/{symbol}")
async def stock_analysis(symbol: str, request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    stock_data = await get_stock_data(symbol.upper())
    news = await get_market_news()
    messages = [{"role": "user", "content": f"Complete swing trade analysis for {symbol.upper()}"}]

    price_ctx = ""
    if stock_data:
        price_ctx = (f"LIVE: ₹{stock_data['price']} | {stock_data['change_pct']}% | "
                     f"H: ₹{stock_data['high']} | L: ₹{stock_data['low']} | Vol: {stock_data['volume']:,}")
    else:
        price_ctx = "Live price unavailable — use best-known recent market price"

    system = f"""You are Chetak.trade AI — elite Indian market analyst.

{price_ctx}
NEWS: {chr(10).join(f"- {n}" for n in news[:3])}

Full analysis for {symbol.upper()}:

📌 STOCK: {symbol.upper()}
💰 PRICE: ₹[price] | 📊 CAP: [Large/Mid/Small] | 🏭 SECTOR: [sector]
🔗 NSE Symbol: {symbol.upper()} (Zerodha/Groww/Upstox)

🎯 SWING SETUP:
💹 Entry: ₹[min]–₹[max]
🛑 SL: ₹[price] ([x]% risk)
🎯 T1: ₹[price] — [x–y] days (R:R 1:[x])
🎯 T2: ₹[price] — [x–y] weeks (R:R 1:[x])
⏱ Hold: [x]–[y] days | 📊 Signal: Strong/Moderate/Weak

📉 TECHNICALS:
• Trend: [Bullish/Bearish/Sideways]
• Support: ₹[price] | Resistance: ₹[price]
• RSI (14): ~[value] [status]
• Volume: [Surge/Normal/Low]
• Pattern: [pattern name]

📰 CATALYST: [key driver]
✅ BUY CASE: [2–3 reasons]
⚠️ RISKS: [2–3 key risks]
🏆 VERDICT: [Strong Buy/Buy/Hold/Avoid]"""
    analysis = await ask_groq(messages, system)
    return JSONResponse({"symbol": symbol.upper(), "analysis": analysis, "price_data": stock_data})

# ─────────────────────────────────────────────────────────────────────────────
# FUNDAMENTALS (Basic+ plan)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/fundamentals/{symbol}")
async def get_fundamentals(symbol: str, request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    allowed, reason, plan = check_plan_permission(token, "fundamentals")
    if not allowed:
        return JSONResponse({"error": reason, "upgrade_required": True, "plan": plan}, status_code=403)

    messages = [{"role": "user", "content": f"Complete fundamental analysis for {symbol.upper()} NSE"}]
    system = f"""Return complete fundamentals for {symbol.upper()} as VALID JSON only:
{{
  "pe_ratio": number, "eps": number, "market_cap": "string",
  "revenue": "string", "net_profit": "string", "roe": number, "roce": number,
  "debt_to_equity": number, "current_ratio": number, "dividend_yield": number,
  "52w_high": number, "52w_low": number, "book_value": number,
  "face_value": number, "promoter_holding": number, "fii_holding": number,
  "sector": "string", "industry": "string",
  "balance_sheet": {{"total_assets": "string","total_liabilities": "string","equity": "string","cash": "string"}},
  "pnl": {{"revenue": "string","ebitda": "string","net_profit": "string","profit_margin": "string"}},
  "verdict": "Strong Buy/Buy/Hold/Avoid",
  "summary": "2-3 line fundamental summary"
}}"""
    result = await ask_groq(messages, system)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return JSONResponse({"symbol": symbol.upper(), "data": json.loads(clean)})
    except:
        return JSONResponse({"symbol": symbol.upper(), "data": None, "raw": result})

# ─────────────────────────────────────────────────────────────────────────────
# SCREENER (Pro+ plan)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/screener")
async def screener(request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    allowed, reason, plan = check_plan_permission(token, "screener")
    if not allowed:
        return JSONResponse({"error": reason, "upgrade_required": True, "plan": plan}, status_code=403)

    body = await request.json()
    recent_stocks = get_recent_stocks(days=5)
    messages = [{"role": "user", "content": f"Screen NSE stocks: {body.get('filters','')}"}]
    system = f"""NSE stock screener. Avoid: {', '.join(recent_stocks) or 'None'}
Return TOP 10 real NSE stocks as VALID JSON only:
{{"stocks":[{{"symbol":"NSE_SYMBOL","name":"Full Name","sector":"sector","cap":"Large/Mid/Small","pe":0,"eps":0,"roe":0,"market_cap":"string","price":0,"verdict":"Strong Buy/Buy/Hold"}}]}}"""
    result = await ask_groq(messages, system)
    try:
        clean = result.strip().replace("```json","").replace("```","").strip()
        return JSONResponse(json.loads(clean))
    except:
        return JSONResponse({"stocks": [], "raw": result})

# ─────────────────────────────────────────────────────────────────────────────
# WATCHLIST
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/watchlist")
async def get_watchlist(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    items = conn.execute("SELECT * FROM watchlist ORDER BY added_at DESC").fetchall()
    conn.close()
    return JSONResponse({"watchlist": [dict(i) for i in items]})

@app.post("/api/watchlist")
async def add_watchlist(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    body = await request.json()
    conn = get_db()
    try:
        conn.execute("INSERT OR IGNORE INTO watchlist (symbol, added_at, notes) VALUES (?,?,?)",
            (body.get("symbol","").upper(), datetime.now().isoformat(), body.get("notes","")))
        conn.commit()
        return JSONResponse({"success": True})
    except:
        return JSONResponse({"success": False})
    finally:
        conn.close()

@app.delete("/api/watchlist/{symbol}")
async def remove_watchlist(symbol: str, request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    conn.execute("DELETE FROM watchlist WHERE symbol=?", (symbol.upper(),))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

# ─────────────────────────────────────────────────────────────────────────────
# ALERTS (Basic+ plan)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/alerts")
async def get_alerts(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    alerts = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    conn.close()
    return JSONResponse({"alerts": [dict(a) for a in alerts]})

@app.post("/api/alerts")
async def add_alert(request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    allowed, reason, plan = check_plan_permission(token, "alerts")
    if not allowed:
        return JSONResponse({"error": reason, "upgrade_required": True, "plan": plan}, status_code=403)
    body = await request.json()
    conn = get_db()
    conn.execute("INSERT INTO alerts (symbol,condition,target_price,triggered,created_at) VALUES (?,?,?,0,?)",
        (body.get("symbol","").upper(), body.get("condition","above"),
         body.get("target_price",0), datetime.now().isoformat()))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: int, request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    conn.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

@app.get("/api/alerts/check")
async def check_alerts(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    alerts = conn.execute("SELECT * FROM alerts WHERE triggered=0").fetchall()
    triggered = []
    for a in alerts:
        data = await get_stock_data(a["symbol"])
        if not data:
            continue
        price = data["price"]
        hit = ((a["condition"] == "above" and price >= a["target_price"]) or
               (a["condition"] == "below" and price <= a["target_price"]))
        if hit:
            conn.execute("UPDATE alerts SET triggered=1 WHERE id=?", (a["id"],))
            triggered.append({"symbol": a["symbol"], "condition": a["condition"],
                              "target": a["target_price"], "current": price})
    conn.commit(); conn.close()
    return JSONResponse({"triggered": triggered, "count": len(triggered)})

# ─────────────────────────────────────────────────────────────────────────────
# DAILY PICKS (Basic+ plan)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/agent/daily-picks")
async def generate_daily_picks(request: Request):
    token = get_token(request)
    if not verify_token(token):
        raise HTTPException(401)
    allowed, reason, plan = check_plan_permission(token, "daily_picks")
    if not allowed:
        return JSONResponse({"error": reason, "upgrade_required": True, "plan": plan}, status_code=403)

    news = await get_market_news()
    conn = get_db()
    wins   = conn.execute("SELECT COUNT(*) as x FROM trades WHERE result='win' AND notes LIKE '%AGENT_PICK%'").fetchone()["x"]
    losses = conn.execute("SELECT COUNT(*) as x FROM trades WHERE result='loss' AND notes LIKE '%AGENT_PICK%'").fetchone()["x"]
    total  = wins + losses
    win_rate = f"{round(wins/total*100)}%" if total > 0 else "No history yet"

    past_wins   = conn.execute("SELECT stock,sector FROM trades WHERE result='win' AND notes LIKE '%AGENT_PICK%' ORDER BY id DESC LIMIT 15").fetchall()
    past_losses = conn.execute("SELECT stock,sector FROM trades WHERE result='loss' AND notes LIKE '%AGENT_PICK%' ORDER BY id DESC LIMIT 15").fetchall()
    today = datetime.now().strftime("%Y-%m-%d")
    already_today = conn.execute("SELECT stock FROM trades WHERE notes LIKE '%AGENT_PICK%' AND created_at LIKE ?", (today+"%",)).fetchall()
    conn.close()

    already_stocks = [r["stock"] for r in already_today]
    recent_stocks  = get_recent_stocks(days=7)
    all_avoid      = list(set(recent_stocks + already_stocks + [r["stock"] for r in past_losses]))
    win_sectors    = list(set([r["sector"] for r in past_wins if r["sector"]]))
    loss_sectors   = list(set([r["sector"] for r in past_losses if r["sector"]]))

    available_pool = [s for s in ALL_NSE_SYMBOLS if s not in all_avoid]
    random.shuffle(available_pool)
    pool_sample = available_pool[:40]

    messages = [{"role": "user", "content": "Generate today's best NSE swing trades"}]
    system = f"""You are Chetak.trade AI — professional NSE swing trading engine.

Win Rate: {win_rate} from {total} trades
Winning sectors: {', '.join(win_sectors) if win_sectors else 'Building history'}
Avoid sectors (recent losses): {', '.join(loss_sectors) if loss_sectors else 'None'}

⚠️ DO NOT suggest: {', '.join(all_avoid) if all_avoid else 'None'}

PICK FROM THIS POOL ONLY (all verified NSE stocks):
{', '.join(pool_sample)}

NEWS: {chr(10).join(f"- {n}" for n in news[:6])}

Pick 5 high-conviction setups. Return ONLY JSON:
{{"picks":[{{"symbol":"NSE_SYMBOL","sector":"sector","cap":"Large/Mid/Small","entry":0.00,"sl":0.00,"target1":0.00,"target2":0.00,"t1_days":7,"t2_days":14,"sl_pct":2.0,"rr_ratio":"1:2","signal":"Strong/Moderate","reason":"technical + catalyst"}}]}}"""

    result = await ask_groq(messages, system)
    try:
        clean = result.strip().replace("```json","").replace("```","").strip()
        picks_data = json.loads(clean)
        conn = get_db()
        added = []
        for p in picks_data.get("picks", []):
            sym = p.get("symbol","").upper().strip()
            if not sym or sym in all_avoid:
                continue
            conn.execute("INSERT INTO trades (stock,entry,sl,target1,target2,sector,signal_strength,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (sym, float(p.get("entry",0)), float(p.get("sl",0)),
                 float(p.get("target1",0)), float(p.get("target2",0)),
                 p.get("sector",""), p.get("signal","Moderate"),
                 f"AUTO|AGENT_PICK|cap:{p.get('cap','mid')}|t1_days:{p.get('t1_days',7)}|t2_days:{p.get('t2_days',14)}|rr:{p.get('rr_ratio','1:2')}|sl_pct:{p.get('sl_pct',2)}|{p.get('reason','')}",
                 datetime.now().isoformat()))
            added.append(sym)
        conn.commit(); conn.close()
        return JSONResponse({"success": True, "picks": picks_data.get("picks",[]),
                             "added": added, "win_rate": win_rate, "total_trades": total})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e), "raw": result[:500]})

@app.post("/api/agent/check-prices")
async def check_prices(request: Request):
    if not verify_token(get_token(request)):
        raise HTTPException(401)
    conn = get_db()
    pending = conn.execute("SELECT * FROM trades WHERE result='pending' AND notes LIKE '%AGENT_PICK%'").fetchall()
    resolved = []
    still_tracking = []

    for t in pending:
        live = await get_stock_data(t["stock"])
        if not live:
            still_tracking.append({"stock": t["stock"], "status": "price_unavailable"})
            continue
        price = live["price"]
        entry = t["entry"] or 0; sl = t["sl"] or 0
        t1 = t["target1"] or 0; t2 = t["target2"] or 0
        notes = t["notes"] or ""
        pnl_pct = round((price - entry) / entry * 100, 2) if entry > 0 else 0
        try:
            days_elapsed = (datetime.now() - datetime.fromisoformat(t["created_at"])).days
        except:
            days_elapsed = 0
        t2_days = 14
        for part in notes.split("|"):
            if "t2_days:" in part:
                try: t2_days = int(part.split(":")[1])
                except: pass

        if sl > 0 and price <= sl:
            pl = round(sl - entry, 2)
            conn.execute("UPDATE trades SET result='loss', profit_loss=?, notes=? WHERE id=?",
                (pl, notes + f"|SL_HIT|exit:{price}|days:{days_elapsed}", t["id"]))
            resolved.append({"stock": t["stock"], "result": "loss", "reason": f"SL hit ₹{price}", "pl": pl})
        elif t2 > 0 and price >= t2:
            pl = round(t2 - entry, 2)
            conn.execute("UPDATE trades SET result='win', profit_loss=?, notes=? WHERE id=?",
                (pl, notes + f"|T2_HIT|exit:{price}|days:{days_elapsed}", t["id"]))
            resolved.append({"stock": t["stock"], "result": "win", "reason": f"T2 hit ₹{price}", "pl": pl})
        elif t1 > 0 and price >= t1 and "|T1_HIT" not in notes:
            conn.execute("UPDATE trades SET notes=? WHERE id=?",
                (notes + f"|T1_HIT|t1_price:{price}|day:{days_elapsed}", t["id"]))
            resolved.append({"stock": t["stock"], "result": "t1_hit", "reason": f"T1 ₹{price} hit, watching T2", "pl": round(t1-entry,2)})
        elif days_elapsed >= t2_days and "|T1_HIT" in notes:
            pl = round(price - entry, 2)
            conn.execute("UPDATE trades SET result='win', profit_loss=?, notes=? WHERE id=?",
                (pl, notes + f"|PARTIAL_WIN|exit:{price}|days:{days_elapsed}", t["id"]))
            resolved.append({"stock": t["stock"], "result": "win", "reason": f"Closed after T1 at ₹{price}", "pl": pl})
        elif days_elapsed >= t2_days + 5:
            pl = round(price - entry, 2)
            res = "win" if pl > 0 else "loss"
            conn.execute("UPDATE trades SET result=?, profit_loss=?, notes=? WHERE id=?",
                (res, pl, notes + f"|EXPIRED|exit:{price}|days:{days_elapsed}", t["id"]))
            resolved.append({"stock": t["stock"], "result": res, "reason": f"Expired at ₹{price}", "pl": pl})
        else:
            still_tracking.append({"stock": t["stock"], "price": price, "pnl_pct": pnl_pct,
                "days": days_elapsed, "status": "T1 hit" if "|T1_HIT" in notes else "Active"})

    conn.commit()
    wins_t = conn.execute("SELECT COUNT(*) as x FROM trades WHERE result='win' AND notes LIKE '%AGENT_PICK%'").fetchone()["x"]
    done_t = conn.execute("SELECT COUNT(*) as x FROM trades WHERE result!='pending' AND notes LIKE '%AGENT_PICK%'").fetchone()["x"]
    conn.close()
    return JSONResponse({"resolved": resolved, "count": len(resolved), "still_tracking": still_tracking,
        "tracking_count": len(still_tracking),
        "ai_win_rate": round(wins_t/done_t*100) if done_t > 0 else 0, "total_resolved": done_t})

# ─────────────────────────────────────────────────────────────────────────────
# CHART DATA
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/chart/{symbol}")
async def get_chart_data(symbol: str, period: str = "3mo", request: Request = None):
    if request and not verify_token(get_token(request)):
        raise HTTPException(401)
    period_map = {"1mo":"1mo","3mo":"3mo","6mo":"6mo","1y":"1y","2y":"2y",
                  "1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","2Y":"2y"}
    yf_period = period_map.get(period, "3mo")
    interval  = "1wk" if yf_period == "2y" else "1d"
    headers_list = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         "Accept": "application/json,text/plain,*/*", "Referer": "https://finance.yahoo.com/"},
        {"User-Agent": "python-requests/2.31.0", "Accept": "*/*"},
    ]
    for base in ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]:
        for sym in [f"{symbol}.NS", f"{symbol}.BO", symbol]:
            for hdrs in headers_list:
                try:
                    url = f"{base}/v8/finance/chart/{sym}?interval={interval}&range={yf_period}"
                    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                        r = await client.get(url, headers=hdrs)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    result = data.get("chart",{}).get("result",[])
                    if not result:
                        continue
                    meta = result[0].get("meta",{})
                    timestamps = result[0].get("timestamp",[])
                    quotes = result[0].get("indicators",{}).get("quote",[{}])[0]
                    if not timestamps:
                        continue
                    candles = []
                    for i, ts in enumerate(timestamps):
                        try:
                            o=quotes.get("open",[])[i]; h=quotes.get("high",[])[i]
                            l=quotes.get("low",[])[i];  c=quotes.get("close",[])[i]
                            v=quotes.get("volume",[])[i]
                        except IndexError:
                            continue
                        if o and h and l and c and o > 0:
                            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                            candles.append({"t": dt.strftime("%Y-%m-%d"),
                                "o":round(float(o),2),"h":round(float(h),2),
                                "l":round(float(l),2),"c":round(float(c),2),"v":int(v) if v else 0})
                    if candles:
                        return JSONResponse({"symbol":symbol.upper(),
                            "display_name":meta.get("longName",meta.get("shortName",symbol)),
                            "currency":meta.get("currency","INR"),
                            "current_price":round(float(meta.get("regularMarketPrice",candles[-1]["c"])),2),
                            "prev_close":round(float(meta.get("chartPreviousClose",candles[-2]["c"] if len(candles)>1 else 0)),2),
                            "candles":candles,"period":period,"source":sym})
                except Exception:
                    continue
    # Fallback
    n = {"1mo":22,"3mo":65,"6mo":130,"1y":252,"2y":504}.get(yf_period,65)
    price = 1000.0; candles = []
    for i in range(n):
        dt = datetime.now(tz=timezone.utc) - timedelta(days=n-i)
        change = (random.random()-0.48)*price*0.025
        o=round(price,2); c=round(max(price+change,1),2)
        h=round(max(o,c)*(1+random.random()*0.012),2); l=round(min(o,c)*(1-random.random()*0.012),2)
        candles.append({"t":dt.strftime("%Y-%m-%d"),"o":o,"h":h,"l":l,"c":c,"v":random.randint(500000,5000000)})
        price = c
    return JSONResponse({"symbol":symbol.upper(),"display_name":symbol,"currency":"INR",
        "current_price":candles[-1]["c"],"prev_close":candles[-2]["c"],"candles":candles,
        "period":period,"source":"simulated","note":"Live data unavailable"})

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/admin/dashboard")
async def admin_dashboard(request: Request):
    req_admin(request)
    conn = get_db()
    c = conn.execute
    wins = c("SELECT COUNT(*) as x FROM trades WHERE result='win'").fetchone()["x"]
    done = c("SELECT COUNT(*) as x FROM trades WHERE result!='pending'").fetchone()["x"]
    data = {
        "stats": {
            "total_users":      c("SELECT COUNT(*) as x FROM users").fetchone()["x"],
            "active_users":     c("SELECT COUNT(*) as x FROM users WHERE active=1").fetchone()["x"],
            "paid_users":       c("SELECT COUNT(*) as x FROM users WHERE plan!='free'").fetchone()["x"],
            "pending_payments": c("SELECT COUNT(*) as x FROM payments WHERE status='pending'").fetchone()["x"],
            "total_revenue":    c("SELECT SUM(amount) as x FROM payments WHERE status='approved'").fetchone()["x"] or 0,
            "total_trades":     c("SELECT COUNT(*) as x FROM trades").fetchone()["x"],
            "wins": wins, "losses": done - wins,
            "win_rate": round(wins/done*100,1) if done else 0,
            "agent_status": get_setting("agent_status"),
            "maintenance_mode": get_setting("maintenance_mode"),
        },
        "users":         [dict(r) for r in c("SELECT * FROM users ORDER BY id DESC").fetchall()],
        "payments":      [dict(r) for r in c("SELECT p.*,u.name,u.email FROM payments p LEFT JOIN users u ON p.user_id=u.id ORDER BY p.id DESC").fetchall()],
        "announcements": [dict(r) for r in c("SELECT * FROM announcements ORDER BY id DESC").fetchall()],
        "settings":      {r["key"]: r["value"] for r in c("SELECT * FROM settings").fetchall()},
        "plans":         PLANS,
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
        conn.execute("INSERT INTO users (name,email,password,plan,active,queries_today,total_queries,joined_at,expires_at) VALUES (?,?,?,?,1,0,0,?,?)",
            (body["name"], body["email"], body.get("password","changeme123"), body.get("plan","free"),
             datetime.now().isoformat(), (datetime.now()+timedelta(days=30)).isoformat()))
        conn.commit()
        return JSONResponse({"success": True})
    except:
        return JSONResponse({"success": False, "error": "Email already exists"})
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
    if "password" in body and body["password"]:
        fields.append("password=?"); values.append(body["password"])
    if "extend_days" in body:
        fields.append("expires_at=?")
        values.append((datetime.now()+timedelta(days=int(body["extend_days"]))).isoformat())
    values.append(uid)
    if fields:
        conn.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()
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
    conn.execute("INSERT INTO payments (user_id,name,email,amount,plan,upi_ref,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (body.get("user_id"), body.get("name",""), body.get("email",""),
         body.get("amount"), body.get("plan"), body.get("upi_ref"),
         body.get("status","pending"), datetime.now().isoformat()))
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

@app.put("/api/admin/payments/{pid}")
async def update_payment(pid: int, request: Request):
    req_admin(request)
    body = await request.json()
    conn = get_db()
    conn.execute("UPDATE payments SET status=?, approved_at=? WHERE id=?",
                 (body["status"], datetime.now().isoformat() if body["status"]=="approved" else None, pid))
    if body["status"] == "approved":
        pmt = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
        if pmt:
            plan = pmt["plan"]
            duration = PLANS.get(plan, PLANS["basic"])["duration_days"]
            expires = (datetime.now() + timedelta(days=duration)).isoformat()
            conn.execute("UPDATE users SET plan=?,active=1,expires_at=? WHERE id=?",
                         (plan, expires, pmt["user_id"]))
            conn.execute("INSERT INTO subscriptions (user_id,plan,started_at,expires_at,payment_id,active) VALUES (?,?,?,?,?,1)",
                         (pmt["user_id"], plan, datetime.now().isoformat(), expires, pid))
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
    conn.execute("DELETE FROM trades"); conn.execute("DELETE FROM chat_history")
    conn.commit(); conn.close()
    return JSONResponse({"success": True})

@app.get("/api/admin/trades")
async def admin_trades(request: Request):
    req_admin(request)
    conn = get_db()
    trades = conn.execute("SELECT * FROM trades ORDER BY id DESC").fetchall()
    conn.close()
    return JSONResponse({"trades": [dict(t) for t in trades]})

@app.get("/api/admin/subscriptions")
async def admin_subscriptions(request: Request):
    req_admin(request)
    conn = get_db()
    subs = conn.execute(
        "SELECT s.*, u.name, u.email FROM subscriptions s LEFT JOIN users u ON s.user_id=u.id ORDER BY s.id DESC"
    ).fetchall()
    conn.close()
    return JSONResponse({"subscriptions": [dict(s) for s in subs]})

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
