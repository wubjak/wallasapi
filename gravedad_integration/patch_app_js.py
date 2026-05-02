"""Patch Gravedad static/app.js to add virtual models + toggles."""
import os, shutil, sys

src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gravedad", "static", "app.js"))
if not os.path.exists(src):
    print("[ERROR] gravedad/static/app.js not found"); sys.exit(1)

with open(src, "r", encoding="utf-8") as f:
    code = f.read()

if "VIRTUAL_MODELS" in code:
    print("[WARN] Already patched"); sys.exit(0)

shutil.copy2(src, src + ".backup.wallas")

# 1. Make loadModels() fetch /v1/models (WallasAPI endpoint)
code = code.replace('const res = await fetch("/models");', 'const res = await fetch("/v1/models");')

# 2. Prepend virtual optgroup in renderModelSelector
old_opt = '    html += \'<option value="">Automático ⚡</option>\';'
new_opt = '''    // ---- Virtual models (WallasAPI) ----
    html += '<optgroup label="Virtuales ⚡">';
    html += '<option value="auto" selected>auto — Selección inteligente</option>';
    html += '<option value="rapido">rapido — Más rápido</option>';
    html += '<option value="standard">standard — Equilibrado</option>';
    html += '<option value="razonamiento">razonamiento — Razonamiento profundo</option>';
    html += '</optgroup>';
    html += '<option value="">Automático (Gravedad)</option>';
    // --------------------------------------
'''
code = code.replace(old_opt, new_opt)

# 3. Add web_search + fork_mode flags to sendMessage payload
old_send = '        body: JSON.stringify({ messages, model: selectedModel, provider: selectedProvider, temperature, web_search: useWebSearch, reasoning: reasoningMode, project_id: currentProjectId })'
new_send = '        body: JSON.stringify({ messages, model: selectedModel, provider: selectedProvider, temperature, web_search: useWebSearch, reasoning: reasoningMode, project_id: currentProjectId, fork_mode: useForkMode })'
code = code.replace(old_send, new_send)

# 4. Add toggles to chat header (insert before model selector)
old_header = '            <div class="model-selector-wrapper">'
new_header = '''            <div class="chat-toggles" style="display:flex;gap:8px;align-items:center;margin-right:10px;">
                <label class="toggle-chip" title="Buscar en web antes de responder">
                    <input type="checkbox" id="web-search-toggle" style="margin-right:4px;">
                    🔍 Web
                </label>
                <label class="toggle-chip" title="Ejecutar 3 modelos en paralelo y devolver el mejor">
                    <input type="checkbox" id="fork-mode-toggle" style="margin-right:4px;">
                    🍴 Fork
                </label>
            </div>
            <div class="model-selector-wrapper">'''
code = code.replace(old_header, new_header)

# 5. Wire toggles in sendMessage() — read their state
old_temp = '        const temperature = parseFloat(document.getElementById("temperature-slider").value);'
new_temp = '''        const temperature = parseFloat(document.getElementById("temperature-slider").value);
        const useWebSearch = document.getElementById("web-search-toggle")?.checked || false;
        const useForkMode = document.getElementById("fork-mode-toggle")?.checked || false;'''
code = code.replace(old_temp, new_temp)

with open(src, "w", encoding="utf-8") as f:
    f.write(code)

print("[OK] app.js patched successfully")
