"""Web dashboard. Run separately from main:  python3 -m src.health_monitor.dashboard"""
import csv
import hmac
import json
import os
import time
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session, url_for, render_template_string

from . import config

load_dotenv()

USER = os.getenv("DASHBOARD_USER")
PASSWORD = os.getenv("DASHBOARD_PASSWORD")
SECRET = os.getenv("DASHBOARD_SECRET_KEY")
STALE_SECONDS = 15  # real sensor reads block for several seconds

app = Flask(__name__)
app.secret_key = SECRET or "unset"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def login_required(page):
    @wraps(page)
    def wrapper(*a, **kw):
        if not session.get("ok"):
            if request.path.startswith("/api/"):
                return jsonify(error="login required"), 401
            return redirect(url_for("login"))
        return page(*a, **kw)
    return wrapper


LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Health Monitor Login</title>
<style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;justify-content:center;padding-top:15vh}
form{background:#1e293b;padding:28px;border-radius:12px;width:280px}input,button{width:100%;box-sizing:border-box;padding:10px;margin-top:10px;border-radius:6px;border:0;font-size:16px}
button{background:#38bdf8;font-weight:600;cursor:pointer}.err{color:#f87171;margin-top:10px}</style></head><body>
<form method="post"><h2>Health Monitor</h2>
<input name="username" placeholder="Username" autocomplete="username" required>
<input name="password" type="password" placeholder="Password" autocomplete="current-password" required>
<button>Log in</button>{% if error %}<div class="err">{{ error }}</div>{% endif %}</form></body></html>"""

DASH_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Health Monitor</title>
<style>
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:16px;max-width:800px;margin:auto}
h1{font-size:20px;display:flex;justify-content:space-between;align-items:center}a{color:#38bdf8;font-size:14px}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}.card{background:#1e293b;border-radius:12px;padding:16px;text-align:center}
.big{font-size:48px;font-weight:700}.lab{color:#94a3b8;font-size:13px}
#status{margin:12px 0;padding:12px;border-radius:12px;text-align:center;font-weight:600;background:#334155}
.ok{background:#166534!important}.bad{background:#991b1b!important}
.leds{display:flex;gap:16px;justify-content:center;margin-top:8px}
.led{width:18px;height:18px;border-radius:50%;background:#334155}.g.on{background:#22c55e}.r.on{background:#ef4444}
canvas{width:100%;height:160px;background:#1e293b;border-radius:12px;margin-top:12px}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}th,td{padding:6px;border-bottom:1px solid #334155;text-align:left}
</style></head><body>
<h1>Health Monitor <a href="/logout">Log out</a></h1>
<div class="cards"><div class="card"><div class="big" id="bpm">--</div><div class="lab">BPM</div></div>
<div class="card"><div class="big" id="spo2">--</div><div class="lab">SpO2 %</div></div></div>
<div id="status">Waiting...</div>
<div class="leds"><div class="led g" id="g"></div><div class="led r" id="r"></div></div>
<canvas id="chart" width="760" height="160"></canvas>
<h3>Saved readings (button)</h3>
<table><thead><tr><th>Time</th><th>BPM</th><th>SpO2</th><th>Alert</th></tr></thead><tbody id="rows"></tbody></table>
<script>
const $=id=>document.getElementById(id);
const LABEL={ok:"Normal",bpm_abnormal:"Heart rate abnormal",spo2_abnormal:"SpO2 abnormal",both_abnormal:"Heart rate and SpO2 abnormal"};
const trail=[];
function draw(){const c=$("chart"),x=c.getContext("2d");x.clearRect(0,0,c.width,c.height);
 if(trail.length<2)return;x.strokeStyle="#38bdf8";x.lineWidth=2;x.beginPath();
 trail.forEach((v,i)=>{const px=i/(59)*c.width,py=c.height-((v-40)/(160-40))*c.height;i?x.lineTo(px,py):x.moveTo(px,py)});x.stroke();
 x.fillStyle="#94a3b8";x.fillText("BPM (last 60 readings)",8,14)}
async function latest(){
 try{const r=await fetch("/api/latest");if(r.status==401){location="/login";return}
 const d=await r.json();const st=$("status");
 if(d.age===null||d.age>%STALE%){st.className="bad";st.textContent="Monitor not running";$("bpm").textContent="--";$("spo2").textContent="--";
  $("g").className="led g";$("r").className="led r";return}
 if(!d.valid){st.className="";st.textContent="Place your finger on the sensor";$("bpm").textContent="--";$("spo2").textContent="--";
  $("g").className="led g";$("r").className="led r";return}
 $("bpm").textContent=d.bpm;$("spo2").textContent=d.spo2;
 st.textContent=LABEL[d.state]||d.state;st.className=d.state=="ok"?"ok":"bad";
 $("g").className="led g"+(d.state=="ok"?" on":"");$("r").className="led r"+(d.state!="ok"?" on":"");
 trail.push(d.bpm);if(trail.length>60)trail.shift();draw()}catch(e){}}
async function history(){
 try{const r=await fetch("/api/history");if(!r.ok)return;const rows=await r.json();const b=$("rows");b.textContent="";
 rows.forEach(row=>{const tr=document.createElement("tr");
  [row.timestamp,row.bpm,row.spo2,row.alert_state].forEach(v=>{const td=document.createElement("td");td.textContent=v;tr.appendChild(td)});b.appendChild(tr)})}catch(e){}}
latest();history();setInterval(latest,1000);setInterval(history,5000);
</script></body></html>""".replace("%STALE%", str(STALE_SECONDS))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        good = hmac.compare_digest(u.encode(), (USER or "").encode()) & \
               hmac.compare_digest(p.encode(), (PASSWORD or "").encode())
        if good:
            session["ok"] = True
            return redirect(url_for("index"))
        time.sleep(1)  # slows password guessing
        error = "Wrong username or password"
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return DASH_HTML


@app.route("/api/latest")
@login_required
def api_latest():
    path = os.path.join(config.LOCAL_DATA_DIR, "latest.json")
    try:
        with open(path) as f:
            d = json.load(f)
        d["age"] = round(time.time() - d["time"], 1)
    except (OSError, ValueError, KeyError):
        d = {"valid": False, "bpm": None, "spo2": None, "state": None, "age": None}
    return jsonify(d)


@app.route("/api/history")
@login_required
def api_history():
    path = os.path.join(config.LOCAL_DATA_DIR, config.LOCAL_READINGS_FILE)
    rows = []
    try:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        pass
    return jsonify(rows[-20:][::-1])  # newest first


if __name__ == "__main__":
    if not (USER and PASSWORD and SECRET):
        raise SystemExit("Set DASHBOARD_USER, DASHBOARD_PASSWORD and DASHBOARD_SECRET_KEY in .env first.")
    app.run(host="0.0.0.0", port=5000)
