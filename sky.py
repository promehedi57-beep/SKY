import os
import re
import logging
import time
import requests
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv

# .env ফাইল লোড (Vercel এ অটো লোড হয়)
load_dotenv()

# লগিং কনফিগার
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ======================== কনফিগারেশন (ENV) ========================
API_BASE_URL = os.getenv("API_BASE_URL", "http://2.58.82.137:5000/api/v1")
API_KEY = os.getenv("API_KEY", "nxa_99f2f67b13e0e02bca175b1cbc40d57128958702")
HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

# ক্যাশিং (সরল ইন-মেমরি, প্রোডাকশনে Redis ব্যবহার করা ভালো)
CACHE = {"data": [], "timestamp": 0}
CACHE_TTL = 5  # সেকেন্ড

# ======================== দেশের কোড ও পতাকা ========================
COUNTRY_CODES = {
    "+93": ("🇦🇫", "AF"), "+355": ("🇦🇱", "AL"), "+213": ("🇩🇿", "DZ"), "+376": ("🇦🇩", "AD"),
    "+244": ("🇦🇴", "AO"), "+54": ("🇦🇷", "AR"), "+374": ("🇦🇲", "AM"), "+61": ("🇦🇺", "AU"),
    "+43": ("🇦🇹", "AT"), "+994": ("🇦🇿", "AZ"), "+973": ("🇧🇭", "BH"), "+880": ("🇧🇩", "BD"),
    "+375": ("🇧🇾", "BY"), "+32": ("🇧🇪", "BE"), "+501": ("🇧🇿", "BZ"), "+229": ("🇧🇯", "BJ"),
    "+975": ("🇧🇹", "BT"), "+591": ("🇧🇴", "BO"), "+387": ("🇧🇦", "BA"), "+267": ("🇧🇼", "BW"),
    "+55": ("🇧🇷", "BR"), "+673": ("🇧🇳", "BN"), "+359": ("🇧🇬", "BG"), "+226": ("🇧🇫", "BF"),
    "+257": ("🇧🇮", "BI"), "+855": ("🇰🇭", "KH"), "+237": ("🇨🇲", "CM"), "+1": ("🇺🇸/🇨🇦", "US/CA"),
    "+238": ("🇨🇻", "CV"), "+236": ("🇨🇫", "CF"), "+235": ("🇹🇩", "TD"), "+56": ("🇨🇱", "CL"),
    "+86": ("🇨🇳", "CN"), "+57": ("🇨🇴", "CO"), "+269": ("🇰🇲", "KM"), "+242": ("🇨🇬", "CG"),
    "+243": ("🇨🇩", "CD"), "+506": ("🇨🇷", "CR"), "+385": ("🇭🇷", "HR"), "+53": ("🇨🇺", "CU"),
    "+357": ("🇨🇾", "CY"), "+420": ("🇨🇿", "CZ"), "+45": ("🇩🇰", "DK"), "+253": ("🇩🇯", "DJ"),
    "+593": ("🇪🇨", "EC"), "+20": ("🇪🇬", "EG"), "+503": ("🇸🇻", "SV"), "+240": ("🇬🇶", "GQ"),
    "+291": ("🇪🇷", "ER"), "+372": ("🇪🇪", "EE"), "+251": ("🇪🇹", "ET"), "+679": ("🇫🇯", "FJ"),
    "+358": ("🇫🇮", "FI"), "+33": ("🇫🇷", "FR"), "+241": ("🇬🇦", "GA"), "+220": ("🇬🇲", "GM"),
    "+995": ("🇬🇪", "GE"), "+49": ("🇩🇪", "DE"), "+233": ("🇬🇭", "GH"), "+30": ("🇬🇷", "GR"),
    "+502": ("🇬🇹", "GT"), "+224": ("🇬🇳", "GN"), "+245": ("🇬🇼", "GW"), "+592": ("🇬🇾", "GY"),
    "+509": ("🇭🇹", "HT"), "+504": ("🇭🇳", "HN"), "+36": ("🇭🇺", "HU"), "+354": ("🇮🇸", "IS"),
    "+91": ("🇮🇳", "IN"), "+62": ("🇮🇩", "ID"), "+98": ("🇮🇷", "IR"), "+964": ("🇮🇶", "IQ"),
    "+353": ("🇮🇪", "IE"), "+972": ("🇮🇱", "IL"), "+39": ("🇮🇹", "IT"), "+225": ("🇨🇮", "CI"),
    "+81": ("🇯🇵", "JP"), "+962": ("🇯🇴", "JO"), "+7": ("🇷🇺/🇰🇿", "RU/KZ"), "+254": ("🇰🇪", "KE"),
    "+686": ("🇰🇮", "KI"), "+383": ("🇽🇰", "XK"), "+965": ("🇰🇼", "KW"), "+996": ("🇰🇬", "KG"),
    "+856": ("🇱🇦", "LA"), "+371": ("🇱🇻", "LV"), "+961": ("🇱🇧", "LB"), "+266": ("🇱🇸", "LS"),
    "+231": ("🇱🇷", "LR"), "+218": ("🇱🇾", "LY"), "+423": ("🇱🇮", "LI"), "+370": ("🇱🇹", "LT"),
    "+352": ("🇱🇺", "LU"), "+261": ("🇲🇬", "MG"), "+265": ("🇲🇼", "MW"), "+60": ("🇲🇾", "MY"),
    "+960": ("🇲🇻", "MV"), "+223": ("🇲🇱", "ML"), "+356": ("🇲🇹", "MT"), "+222": ("🇲🇷", "MR"),
    "+230": ("🇲🇺", "MU"), "+52": ("🇲🇽", "MX"), "+691": ("🇫🇲", "FM"), "+373": ("🇲🇩", "MD"),
    "+377": ("🇲🇨", "MC"), "+976": ("🇲🇳", "MN"), "+382": ("🇲🇪", "ME"), "+212": ("🇲🇦", "MA"),
    "+258": ("🇲🇿", "MZ"), "+95": ("🇲🇲", "MM"), "+264": ("🇳🇦", "NA"), "+674": ("🇳🇷", "NR"),
    "+977": ("🇳🇵", "NP"), "+31": ("🇳🇱", "NL"), "+64": ("🇳🇿", "NZ"), "+505": ("🇳🇮", "NI"),
    "+227": ("🇳🇪", "NE"), "+234": ("🇳🇬", "NG"), "+850": ("🇰🇵", "KP"), "+389": ("🇲🇰", "MK"),
    "+47": ("🇳🇴", "NO"), "+968": ("🇴🇲", "OM"), "+92": ("🇵🇰", "PK"), "+680": ("🇵🇼", "PW"),
    "+970": ("🇵🇸", "PS"), "+507": ("🇵🇦", "PA"), "+675": ("🇵🇬", "PG"), "+595": ("🇵🇾", "PY"),
    "+51": ("🇵🇪", "PE"), "+63": ("🇵🇭", "PH"), "+48": ("🇵🇱", "PL"), "+351": ("🇵🇹", "PT"),
    "+974": ("🇶🇦", "QA"), "+40": ("🇷🇴", "RO"), "+250": ("🇷🇼", "RW"), "+966": ("🇸🇦", "SA"),
    "+221": ("🇸🇳", "SN"), "+381": ("🇷🇸", "RS"), "+248": ("🇸🇨", "SC"), "+232": ("🇸🇱", "SL"),
    "+65": ("🇸🇬", "SG"), "+421": ("🇸🇰", "SK"), "+386": ("🇸🇮", "SI"), "+677": ("🇸🇧", "SB"),
    "+252": ("🇸🇴", "SO"), "+27": ("🇿🇦", "ZA"), "+82": ("🇰🇷", "KR"), "+211": ("🇸🇸", "SS"),
    "+34": ("🇪🇸", "ES"), "+94": ("🇱🇰", "LK"), "+249": ("🇸🇩", "SD"), "+597": ("🇸🇷", "SR"),
    "+268": ("🇸🇿", "SZ"), "+46": ("🇸🇪", "SE"), "+41": ("🇨🇭", "CH"), "+963": ("🇸🇾", "SY"),
    "+886": ("🇹🇼", "TW"), "+992": ("🇹🇯", "TJ"), "+255": ("🇹🇿", "TZ"), "+66": ("🇹🇭", "TH"),
    "+228": ("🇹🇬", "TG"), "+676": ("🇹🇴", "TO"), "+216": ("🇹🇳", "TN"), "+90": ("🇹🇷", "TR"),
    "+993": ("🇹🇲", "TM"), "+688": ("🇹🇻", "TV"), "+256": ("🇺🇬", "UG"), "+380": ("🇺🇦", "UA"),
    "+971": ("🇦🇪", "AE"), "+44": ("🇬🇧", "GB"), "+598": ("🇺🇾", "UY"), "+998": ("🇺🇿", "UZ"),
    "+678": ("🇻🇺", "VU"), "+379": ("🇻🇦", "VA"), "+58": ("🇻🇪", "VE"), "+84": ("🇻🇳", "VN"),
    "+967": ("🇾🇪", "YE"), "+260": ("🇿🇲", "ZM"), "+263": ("🇿🇼", "ZW")
}

OTP_REGEX = re.compile(r'\b\d{4,10}\b')

def get_country_info(phone: str) -> tuple:
    if not phone: return "🌍", "GLOBAL"
    phone_str = str(phone).strip()
    if not phone_str.startswith("+"): phone_str = "+" + phone_str
    for code, (flag, short_name) in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if phone_str.startswith(code): return flag, short_name
    return "🌍", "GLOBAL"

def generate_skypro_number(phone: str) -> str:
    p = str(phone).strip().replace("+", "")
    return f"{p[:3]}SKYPRO{p[-3:]}" if len(p) >= 6 else f"SKYPRO{p}"

# ================= API রাউট =================
@app.route('/api/otps')
def get_otps():
    global CACHE
    now = time.time()
    if CACHE["data"] and (now - CACHE["timestamp"]) < CACHE_TTL:
        return jsonify({"status": "success", "data": CACHE["data"], "cached": True})

    max_retries = 2
    for attempt in range(max_retries):
        try:
            url = f"{API_BASE_URL}/console/logs?limit=50"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                logs = data.get("data", []) if isinstance(data, dict) else data

                result_list = []
                for log in logs:
                    sms_text = log.get("sms", "")
                    otp_match = OTP_REGEX.search(sms_text)
                    if otp_match:
                        phone = str(log.get("phone", log.get("number", "")))
                        raw_cat = log.get("service") or log.get("app") or log.get("service_name")
                        category = "FACEBOOK" if not raw_cat or str(raw_cat).strip().lower() in ["null", "none", ""] else str(raw_cat).strip().upper()
                        flag, country_short = get_country_info(phone)
                        skypro_number = generate_skypro_number(phone)

                        result_list.append({
                            "id": log.get("id", ""),
                            "otp": otp_match.group(0),
                            "phone": phone,
                            "country_flag": flag,
                            "country_code": country_short,
                            "service": category,
                            "skypro_number": skypro_number
                        })

                CACHE["data"] = result_list
                CACHE["timestamp"] = now
                return jsonify({"status": "success", "data": result_list})
            else:
                logger.warning(f"API responded with {resp.status_code}")
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            time.sleep(1)
    # সব রিট্রাই শেষে ব্যর্থ হলে
    return jsonify({"status": "error", "data": [], "message": "API unreachable"}), 503

# ================= ওয়েবসাইট রাউট (HTML) =================
@app.route('/')
def serve_html():
    return render_template_string(HTML_CODE)

# HTML টেমপ্লেট (নিচে সম্পূর্ণ আপডেটেড ভার্সন)
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SKY SMS PRO · OTP Vault</title>
    <!-- Telegram Web App (optional, safe fallback) -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* ----- আধুনিক প্রিমিয়াম ডিজাইন ----- */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: #0b0c10;
            color: #ffffff;
            min-height: 100vh;
            background-image: radial-gradient(circle at 10% 20%, rgba(0, 240, 255, 0.08) 0%, transparent 30%),
                              radial-gradient(circle at 90% 80%, rgba(138, 43, 226, 0.08) 0%, transparent 30%);
        }

        .app-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(11, 12, 16, 0.85);
            backdrop-filter: blur(20px);
            padding: 18px 20px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .logo {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        .logo h1 {
            font-size: 1.8rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00f0ff, #a855f7);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: -0.5px;
        }
        .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(0,240,255,0.1);
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(0,240,255,0.2);
        }
        .pulse {
            width: 10px;
            height: 10px;
            background: #00f0ff;
            border-radius: 50%;
            box-shadow: 0 0 8px #00f0ff;
            animation: pulse 1.8s infinite;
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

        .search-section {
            position: relative;
            margin: 8px 0 4px;
        }
        .search-box {
            width: 100%;
            padding: 16px 20px 16px 50px;
            background: rgba(20, 25, 35, 0.7);
            border: 1.5px solid rgba(255,255,255,0.08);
            border-radius: 40px;
            font-size: 16px;
            color: #fff;
            outline: none;
            transition: all 0.25s;
            font-weight: 500;
        }
        .search-box:focus {
            border-color: #00f0ff;
            background: rgba(20, 30, 45, 0.9);
            box-shadow: 0 0 20px rgba(0,240,255,0.2);
        }
        .search-icon {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: #00f0ff;
            font-size: 18px;
        }

        .filter-row {
            display: flex;
            gap: 10px;
            margin: 15px 0 5px;
            overflow-x: auto;
            padding-bottom: 6px;
            scrollbar-width: none;
        }
        .filter-chip {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 600;
            color: #b0b8c5;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s;
            backdrop-filter: blur(4px);
        }
        .filter-chip.active {
            background: #00f0ff10;
            border-color: #00f0ff;
            color: #00f0ff;
            box-shadow: 0 4px 12px rgba(0,240,255,0.1);
        }

        .container {
            padding: 15px 18px 30px;
        }

        /* কার্ড স্টাইল */
        .otp-card {
            background: rgba(20, 25, 35, 0.65);
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 28px;
            padding: 18px 20px;
            margin-bottom: 18px;
            transition: transform 0.2s;
            box-shadow: 0 15px 30px -10px rgba(0,0,0,0.5);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 16px;
        }
        .badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.3px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .badge-country { background: #1e2632; color: #cdd5e0; border: 1px solid #2f3a4a; }
        .badge-service { background: #0f1a26; }
        .service-fb { color: #1877F2; border: 1px solid #1877F240; background: #1877F210; }
        .service-wa { color: #25D366; border: 1px solid #25D36640; background: #25D36610; }
        .service-tg { color: #0088cc; border: 1px solid #0088cc40; background: #0088cc10; }

        .info-row {
            background: #0d121c;
            border-radius: 18px;
            padding: 12px 16px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            border: 1px solid #1e2a36;
        }
        .label-sm { font-size: 12px; color: #8a95a5; text-transform: uppercase; letter-spacing: 1px; }
        .value-mono { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 18px; font-weight: 600; }

        .otp-action {
            display: flex;
            gap: 12px;
        }
        .otp-display {
            flex: 1;
            background: #0a101a;
            border: 2px solid #00f0ff30;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: 800;
            font-family: 'SF Mono', monospace;
            color: #00f0ff;
            letter-spacing: 6px;
            padding: 8px 0;
        }
        .copy-btn {
            background: linear-gradient(145deg, #00c8ff, #0066ff);
            border: none;
            border-radius: 18px;
            width: 70px;
            font-size: 22px;
            color: white;
            cursor: pointer;
            transition: all 0.15s;
            box-shadow: 0 6px 14px #0066ff40;
        }
        .copy-btn:active { transform: scale(0.94); }

        /* লোডিং / এরর */
        .state-message {
            text-align: center;
            padding: 40px 20px;
            color: #a0aec0;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 13px;
            color: #6c7a8e;
        }
        .footer a { color: #00f0ff; text-decoration: none; font-weight: 700; }
        .toast {
            position: fixed;
            bottom: 25px;
            left: 50%;
            transform: translateX(-50%);
            background: #1e2a3a;
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            font-weight: 600;
            box-shadow: 0 10px 30px #00000050;
            backdrop-filter: blur(12px);
            border: 1px solid #00f0ff40;
            opacity: 0;
            transition: opacity 0.2s;
            pointer-events: none;
            z-index: 999;
        }
        .toast.show { opacity: 1; }
    </style>
</head>
<body>

<div class="app-header">
    <div class="logo">
        <h1><i class="fa-solid fa-shield-halved" style="margin-right: 8px;"></i>SKY·OTP</h1>
        <div class="status-badge"><span class="pulse"></span> LIVE</div>
    </div>
    <div class="search-section">
        <i class="fa-solid fa-magnifying-glass search-icon"></i>
        <input type="text" id="searchInput" class="search-box" placeholder="Search by number, service or country...">
    </div>
    <div class="filter-row">
        <div class="filter-chip active" data-filter="all"><i class="fa-regular fa-circle-dot"></i> All</div>
        <div class="filter-chip" data-filter="fb"><i class="fa-brands fa-facebook"></i> Facebook</div>
        <div class="filter-chip" data-filter="wa"><i class="fa-brands fa-whatsapp"></i> WhatsApp</div>
        <div class="filter-chip" data-filter="tg"><i class="fa-brands fa-telegram"></i> Telegram</div>
    </div>
</div>

<div class="container" id="logsContainer">
    <!-- dynamic content -->
    <div class="state-message"><i class="fa-solid fa-spinner fa-pulse"></i> Connecting to secure servers...</div>
</div>

<div class="footer">
    🔐 Encrypted by <a href="https://t.me/SKYSMSOWNER" target="_blank">SKY NETWORKS</a> · Real‑time OTP
</div>

<div class="toast" id="liveToast">📋 OTP copied</div>

<script>
    (function() {
        // Telegram Web App initialization (safe)
        if (window.Telegram?.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.expand();
            tg.setHeaderColor('#0b0c10');
        }

        const container = document.getElementById('logsContainer');
        const searchInput = document.getElementById('searchInput');
        const filterChips = document.querySelectorAll('.filter-chip');
        const toastEl = document.getElementById('liveToast');
        let allLogs = [];
        let activeFilter = 'all';
        let searchTerm = '';

        function showToast(msg) {
            toastEl.textContent = msg || '📋 OTP copied';
            toastEl.classList.add('show');
            setTimeout(() => toastEl.classList.remove('show'), 2000);
        }

        // ফেচ ডেটা
        async function fetchLogs() {
            try {
                const res = await fetch('/api/otps');
                if (!res.ok) throw new Error('Server error');
                const json = await res.json();
                if (json.status === 'success') {
                    allLogs = json.data || [];
                } else {
                    allLogs = [];
                }
            } catch (e) {
                console.warn('API error:', e);
                allLogs = [];
            } finally {
                renderCards();
            }
        }

        function getServiceMeta(serviceName) {
            const s = String(serviceName).toUpperCase();
            if (s.includes('FACEBOOK')) return { id: 'fb', icon: 'fa-facebook', css: 'service-fb', label: 'Facebook' };
            if (s.includes('WHATSAPP')) return { id: 'wa', icon: 'fa-whatsapp', css: 'service-wa', label: 'WhatsApp' };
            if (s.includes('TELEGRAM')) return { id: 'tg', icon: 'fa-telegram', css: 'service-tg', label: 'Telegram' };
            return { id: 'other', icon: 'fa-globe', css: '', label: serviceName || 'App' };
        }

        function renderCards() {
            let filtered = allLogs.filter(log => {
                // service filter
                if (activeFilter !== 'all') {
                    const meta = getServiceMeta(log.service);
                    if (meta.id !== activeFilter) return false;
                }
                // text search
                if (searchTerm.trim() !== '') {
                    const haystack = (log.phone + ' ' + log.service + ' ' + log.country_code).toLowerCase();
                    if (!haystack.includes(searchTerm.toLowerCase())) return false;
                }
                return true;
            });

            if (filtered.length === 0) {
                container.innerHTML = `<div class="state-message"><i class="fa-regular fa-folder-open"></i> No OTPs found</div>`;
                return;
            }

            let html = '';
            filtered.forEach(log => {
                const meta = getServiceMeta(log.service);
                html += `
                    <div class="otp-card">
                        <div class="card-header">
                            <span class="badge badge-country">${log.country_flag} ${log.country_code}</span>
                            <span class="badge badge-service ${meta.css}"><i class="fa-brands ${meta.icon}"></i> ${meta.label}</span>
                        </div>
                        <div class="info-row">
                            <span class="label-sm">SECURE LINE</span>
                            <span class="value-mono">${log.skypro_number}</span>
                        </div>
                        <div class="otp-action">
                            <div class="otp-display">${log.otp}</div>
                            <button class="copy-btn" data-otp="${log.otp}"><i class="fa-regular fa-copy"></i></button>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;

            // Copy button event
            document.querySelectorAll('.copy-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const otp = btn.dataset.otp;
                    navigator.clipboard?.writeText(otp).then(() => {
                        showToast(`✅ OTP ${otp} copied`);
                        if (window.Telegram?.WebApp?.HapticFeedback) {
                            window.Telegram.WebApp.HapticFeedback.notificationOccurred('success');
                        }
                    }).catch(() => showToast('❌ Copy failed'));
                });
            });
        }

        // Event listeners
        searchInput.addEventListener('input', (e) => {
            searchTerm = e.target.value;
            renderCards();
        });

        filterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                filterChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                activeFilter = chip.dataset.filter;
                renderCards();
            });
        });

        // Auto refresh every 5 sec
        fetchLogs();
        setInterval(fetchLogs, 5000);
    })();
</script>
</body>
</html>
"""

# Vercel সার্ভারলেস এন্ট্রি পয়েন্ট
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
