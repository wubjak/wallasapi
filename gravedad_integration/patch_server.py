"""Patch Gravedad server.py to add WallasAPI proxy endpoints."""
import os, shutil, sys

src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gravedad", "server.py"))
if not os.path.exists(src):
    print("[ERROR] gravedad/server.py not found"); sys.exit(1)

with open(src, "r", encoding="utf-8") as f:
    code = f.read()

if "WALLASAPI_BASE" in code:
    print("[WARN] Already patched"); sys.exit(0)

shutil.copy2(src, src + ".backup.wallas")

imports = '''# === WALLASAPI INTEGRATION ===
import requests as _wallas_requests
WALLASAPI_BASE = os.environ.get("WALLASAPI_URL", "http://localhost:8001")
WALLASAPI_KEY  = os.environ.get("WALLASAPI_KEY", "wallasapi-local")
_VIRT_MODELS = {"auto", "rapido", "standard", "razonamiento"}

def _wallas(method, path, json=None, stream=False):
    url = f"{WALLASAPI_BASE}{path}"
    h = {"Authorization": f"Bearer {WALLASAPI_KEY}", "Content-Type": "application/json"}
    if method == "GET":
        r = _wallas_requests.get(url, headers=h, timeout=60, stream=stream)
    else:
        r = _wallas_requests.post(url, headers=h, json=json, timeout=120, stream=stream)
    return r

# --- Proxy endpoints ---
@app.route("/v1/models", methods=["GET"])
def wallas_models():
    r = _wallas("GET", "/v1/models")
    return jsonify(r.json()), r.status_code

@app.route("/v1/search/web", methods=["POST"])
def wallas_search():
    r = _wallas("POST", "/v1/search/web", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/chat/completions/fork", methods=["POST"])
def wallas_fork():
    r = _wallas("POST", "/v1/chat/completions/fork", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/diligence/compare", methods=["POST"])
def wallas_diligence():
    r = _wallas("POST", "/v1/diligence/compare", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/health", methods=["GET"])
def wallas_browser_health():
    r = _wallas("GET", "/v1/browser/health")
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/open", methods=["POST"])
def wallas_browser_open():
    r = _wallas("POST", "/v1/browser/open", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/act", methods=["POST"])
def wallas_browser_act():
    r = _wallas("POST", "/v1/browser/act", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/search", methods=["POST"])
def wallas_browser_search():
    r = _wallas("POST", "/v1/browser/search", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/summarize", methods=["POST"])
def wallas_browser_summarize():
    r = _wallas("POST", "/v1/browser/summarize", request.json)
    return jsonify(r.json()), r.status_code

@app.route("/v1/browser/youtube/transcript", methods=["POST"])
def wallas_browser_yt():
    r = _wallas("POST", "/v1/browser/youtube/transcript", request.json)
    return jsonify(r.json()), r.status_code

# --- /chat virtual-model proxy (prepend in original function below) ---

'''

# Insert imports right after "import os" line
marker = "import os\n"
if marker in code:
    code = code.replace(marker, marker + imports, 1)
else:
    code = imports + code

# Now patch /chat to proxy virtual models
old_chat_logic = '    preferred_provider = data.get("provider")\n    preferred_model = data.get("model")\n    thread_id = data.get("thread_id", "playground_session")'
new_chat_logic = '''    preferred_provider = data.get("provider")
    preferred_model = data.get("model")
    thread_id = data.get("thread_id", "playground_session")

    # ---- WallasAPI virtual-model proxy ----
    if preferred_model in _VIRT_MODELS:
        payload = {
            "model": preferred_model,
            "messages": data.get("messages", []),
            "stream": True,
            "temperature": data.get("temperature", 0.7),
            "web_search": data.get("web_search", False),
        }
        def _gen():
            r = _wallas("POST", "/v1/chat/completions", payload, stream=True)
            for line in r.iter_lines():
                if line:
                    yield line.decode("utf-8") + "\\n\\n"
        return Response(stream_with_context(_gen()), mimetype="text/event-stream")
    # ---- end WallasAPI proxy ----
'''

code = code.replace(old_chat_logic, new_chat_logic)

with open(src, "w", encoding="utf-8") as f:
    f.write(code)

print("[OK] server.py patched successfully")
