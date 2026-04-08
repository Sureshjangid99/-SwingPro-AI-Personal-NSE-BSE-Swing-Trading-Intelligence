# 📈 SwingPro AI — Personal NSE/BSE Swing Trading Intelligence

<div align="center">

![SwingPro AI](https://img.shields.io/badge/SwingPro-AI-00ff88?style=for-the-badge&logo=chart-line&logoColor=black)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI-ff6b35?style=for-the-badge)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Deployed-yellow?style=for-the-badge&logo=huggingface&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

### 🚀 Your Personal AI-Powered Swing Trading Assistant for Indian Markets

*Built for NSE • BSE • Nifty 50 • Sensex*

[Live Demo](https://huggingface.co/spaces/suresh9970/Chetak.trade) • [Report Bug](https://github.com/suresh9970/SwingPro-AI/issues) • [Request Feature](https://github.com/suresh9970/SwingPro-AI/issues)

</div>

---

## 🌟 What is SwingPro AI?

SwingPro AI is a **personal AI-powered swing trading assistant** built specifically for Indian stock markets (NSE/BSE). It combines **live market data**, **real-time news analysis**, and **AI intelligence** to give you actionable swing trade signals with precise Entry, Stop Loss, and Target levels — just like having a professional trading analyst working for you 24/7.

> *"The best trading assistant you'll ever have — built by a trader, for traders."*

---

## ✨ Current Features

### 🤖 AI Trading Intelligence
- **Real-time swing trade signals** with Entry Price, SL, Target 1 & Target 2
- **Sector trend analysis** — IT, Pharma, Banking, Auto, Energy, FMCG
- **Global news impact detection** — How world events affect Indian markets
- **Risk:Reward calculation** — Only suggests trades with minimum 1:2 R:R
- **Signal strength rating** — Strong / Moderate / Weak

### 📊 Live Market Data
- **Real-time NSE/BSE prices** via Yahoo Finance API
- **Live market news** from global sources
- **Nifty 50 & Sensex tracking**
- **Top stock monitoring** — Reliance, TCS, HDFC, Infosys, SunPharma

### 📋 Smart Trade Journal
- **Record every trade** with Entry, SL, Target levels
- **Mark results** — Win ✅ or Loss ❌
- **Auto P&L calculation**
- **Performance statistics** — Win rate, total trades, net P&L

### 🧠 Self-Learning Engine
- **Learns from your trades** — Gets smarter every day
- **Pattern recognition** — Discovers what works for YOU
- **Win rate improvement** over time
- **Personalized strategy** based on your trading history

### 👑 Boss Admin Dashboard
- **Complete agent control** — Turn ON/OFF, maintenance mode
- **Market settings** — Customize sectors, SL%, R:R ratio
- **Blacklist/Whitelist stocks** — Full control over what agent suggests
- **User management** — Add, activate, deactivate users
- **Payment tracking** — Manual UPI payment system
- **Revenue dashboard** — Track earnings from subscriptions
- **Emergency stop** — Halt all signals instantly
- **Learning engine monitor** — Track AI improvement

### 🔐 Security
- **Password protected** — Nobody can access without your permission
- **Token-based authentication** — Works inside HuggingFace iframes
- **Separate admin panel** — Extra security layer
- **Private deployment** — Your data, your server

---

## 🛠️ Tech Stack

```
Backend:     Python + FastAPI
AI Brain:    Groq API (Llama 3.3 70B)
Market Data: Yahoo Finance API
News:        NewsAPI
Database:    SQLite
Frontend:    HTML + CSS + JavaScript
Deployment:  HuggingFace Spaces (Docker)
Auth:        Token-based (localStorage)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Groq API Key (free at console.groq.com)
- News API Key (free at newsapi.org)

### Local Setup
```bash
# Clone the repository
git clone https://github.com/suresh9970/SwingPro-AI.git
cd SwingPro-AI

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_groq_key"
export NEWS_API_KEY="your_news_key"
export APP_PASSWORD="your_password"
export ADMIN_PASSWORD="your_admin_password"

# Run the application
python app.py
```

### Deploy to HuggingFace Spaces
```bash
# Clone your HuggingFace space
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE

# Copy all files maintaining folder structure
# templates/ → HTML files
# static/css/ → style.css
# static/js/ → main.js

# Push to deploy
git add .
git commit -m "deploy SwingPro AI"
git push
```

---

## 📱 How to Use

```
1. Open your SwingPro AI link
2. Enter your password
3. Ask anything:
   → "Best swing trades today?"
   → "Which sectors are trending?"
   → "Analyze Reliance for swing trade"
   → "Market mood today?"
4. Get signals with Entry, SL, Targets
5. Record your trades in journal
6. Mark Win/Loss after trade closes
7. Agent learns and improves!
```

---

## 🗺️ Roadmap — Future Upgrades

> *"We are building this to become the most powerful personal trading AI in India. This is just the beginning."*

### Phase 2 — Coming Soon 🔜
- [ ] **Telegram Bot Integration** — Get signals directly on Telegram
- [ ] **Zerodha Kite API** — Real-time professional market data
- [ ] **Technical Chart Analysis** — RSI, MACD, Bollinger Bands
- [ ] **Candlestick Pattern Recognition** — Auto detect patterns
- [ ] **Volume Analysis** — Confirm signals with volume
- [ ] **Backtesting Engine** — Test strategies on historical data
- [ ] **Portfolio Tracker** — Track all your holdings
- [ ] **Options Chain Analysis** — F&O signals

### Phase 3 — Advanced Intelligence 🧠
- [ ] **Multi-timeframe Analysis** — 15min + Daily + Weekly
- [ ] **FII/DII Data Integration** — Follow big money
- [ ] **Earnings Calendar** — Avoid holding during results
- [ ] **Sector Rotation Detection** — Know when money moves
- [ ] **Support & Resistance Auto-detection**
- [ ] **Price Action Analysis**
- [ ] **Global Market Correlation** — US, Asia impact on India

### Phase 4 — Professional Grade 💎
- [ ] **Bloomberg/Reuters News Integration**
- [ ] **Sentiment Analysis** — Social media + news mood
- [ ] **AI Pattern Learning** — Deep learning on charts
- [ ] **Auto Risk Management** — Position sizing calculator
- [ ] **Multi-user SaaS Platform** — Sell subscriptions
- [ ] **Mobile App** — iOS + Android
- [ ] **WhatsApp Integration** — Signals on WhatsApp
- [ ] **Advanced Backtesting** — Monte Carlo simulation

### Phase 5 — Extreme Top Level 🚀
- [ ] **Algorithmic Trading** — Auto execute trades (SEBI compliant)
- [ ] **Hedge Fund Grade Analytics**
- [ ] **Custom AI Model** — Trained specifically on Indian markets
- [ ] **Predictive Analytics** — AI market forecasting
- [ ] **Real-time Options Pricing**
- [ ] **Institutional Grade Risk Management**
- [ ] **Multi-broker Integration**
- [ ] **IPO Analysis** — AI-powered IPO recommendations

---

## 💰 Monetization Model

```
Free Tier:    5 queries/day
Basic Plan:   ₹199/month — 20 queries/day
Pro Plan:     ₹499/month — Unlimited queries
Premium Plan: ₹999/month — Unlimited + Priority support
```

---

## ⚠️ Disclaimer

> SwingPro AI is a **research and analysis tool** only. It is NOT a SEBI-registered investment advisor. All trading signals are for educational and research purposes. Always verify before trading. Use strict Stop Loss. The creator is not responsible for any trading losses. Trade at your own risk.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Share feedback

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

## 👨‍💻 Author

**Suresh Jangid** (suresh9970)

*"Built this from scratch with passion for trading and AI. This is just v1.0 — the best is yet to come."*

---

<div align="center">

**⭐ Star this repo if you find it useful!**

*Built with ❤️ for Indian traders*

![Made in India](https://img.shields.io/badge/Made%20in-India%20🇮🇳-orange?style=for-the-badge)

</div>
