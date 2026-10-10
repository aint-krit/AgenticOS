"""
AgenticOS Web Dashboard - Production UI for AgenticOS v0.1 Alpha.
Provides an interactive web console, telemetry cards, and agent observability.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgenticOS v0.1 Alpha</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --success: #3fb950;
      --warning: #d29922;
      --danger: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
    body { background: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
    .logo { font-size: 22px; font-weight: bold; color: #fff; letter-spacing: 0.5px; }
    .badge { background: #238636; color: #fff; font-size: 12px; padding: 2px 8px; border-radius: 12px; }
    .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
    @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    .card-title { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
    .prompt-box { display: flex; gap: 10px; margin-bottom: 12px; }
    input[type="text"] { flex: 1; background: #090d13; border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; color: #fff; font-size: 14px; outline: none; }
    input[type="text"]:focus { border-color: var(--accent); }
    button { background: var(--accent); color: #0d1117; font-weight: 600; border: none; border-radius: 6px; padding: 12px 20px; cursor: pointer; transition: opacity 0.2s; }
    button:hover { opacity: 0.9; }
    .samples { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
    .chip { background: #21262d; border: 1px solid var(--border); font-size: 12px; padding: 5px 10px; border-radius: 14px; cursor: pointer; color: var(--accent); }
    .chip:hover { border-color: var(--accent); }
    .pipeline { display: flex; justify-content: space-between; margin: 16px 0; border: 1px solid var(--border); border-radius: 6px; background: #090d13; padding: 12px; }
    .step { font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
    .step.active { color: var(--accent); font-weight: bold; }
    .step.done { color: var(--success); }
    .terminal { background: #040608; border: 1px solid var(--border); border-radius: 6px; padding: 14px; font-size: 13px; font-family: monospace; min-height: 180px; max-height: 350px; overflow-y: auto; white-space: pre-wrap; }
    .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; font-size: 13px; }
    .stat-val { color: #fff; font-weight: 500; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo">AgenticOS <span class="badge">v0.1 Alpha</span></div>
      <div style="font-size: 13px; color: var(--text-muted);">Autonomous Operating System Runtime</div>
    </header>

    <div class="grid">
      <div>
        <div class="card">
          <div class="card-title">Prompt Interface</div>
          <div class="prompt-box">
            <input type="text" id="prompt-input" placeholder="What would you like me to do? (e.g., Open Chrome, create file notes.txt)" />
            <button onclick="submitPrompt()" id="send-btn">Execute</button>
          </div>
          <div class="samples">
            <span class="chip" onclick="setPrompt('Open Chrome and create file Project/demo.txt with content Hello AgenticOS')">Open Chrome & create file</span>
            <span class="chip" onclick="setPrompt('Show my CPU and memory usage')">Show CPU & RAM</span>
            <span class="chip" onclick="setPrompt('remember user workspace is active')">Store memory</span>
          </div>

          <div class="pipeline">
            <div class="step" id="step-understand"><span>1.</span> Understanding</div>
            <div class="step" id="step-plan"><span>2.</span> Planning</div>
            <div class="step" id="step-execute"><span>3.</span> Executing</div>
            <div class="step" id="step-verify"><span>4.</span> Verified</div>
          </div>

          <div class="terminal" id="terminal-out">AgenticOS ready. Enter a prompt to begin.</div>
        </div>
      </div>

      <div>
        <div class="card">
          <div class="card-title">System Intelligence</div>
          <div id="telemetry-box">
            <div class="stat-row"><span>Platform:</span><span class="stat-val" id="stat-os">Loading...</span></div>
            <div class="stat-row"><span>CPU Usage:</span><span class="stat-val" id="stat-cpu">Loading...</span></div>
            <div class="stat-row"><span>Memory Used:</span><span class="stat-val" id="stat-mem">Loading...</span></div>
            <div class="stat-row"><span>System Status:</span><span class="stat-val" style="color: var(--success);">Operational</span></div>
          </div>
          <button style="margin-top: 12px; width: 100%; padding: 8px; font-size: 12px;" onclick="refreshTelemetry()">Refresh Telemetry</button>
        </div>

        <div class="card">
          <div class="card-title">Agent Ecosystem</div>
          <div class="stat-row"><span>Global Manager:</span><span class="stat-val" style="color: var(--success);">Active</span></div>
          <div class="stat-row"><span>Core Agents:</span><span class="stat-val">9 Registered</span></div>
          <div class="stat-row"><span>Capability Gate:</span><span class="stat-val" style="color: var(--accent);">Authorized</span></div>
          <div class="stat-row"><span>Workspace:</span><span class="stat-val">Restricted (Safe)</span></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function setPrompt(text) {
      document.getElementById('prompt-input').value = text;
    }

    async function refreshTelemetry() {
      try {
        const res = await fetch('/api/system');
        const data = await res.json();
        document.getElementById('stat-os').innerText = data.platform + ' ' + (data.platform_version || '');
        document.getElementById('stat-cpu').innerText = (data.cpu.percent !== null && data.cpu.percent !== undefined) ? data.cpu.percent + '%' : 'Monitored';
        if (data.memory.total_mb) {
          const used = Math.round(data.memory.total_mb - (data.memory.available_mb || 0));
          document.getElementById('stat-mem').innerText = used + ' / ' + Math.round(data.memory.total_mb) + ' MB (' + Math.round(data.memory.percent || 0) + '%)';
        }
      } catch (e) {
        console.error(e);
      }
    }

    async function submitPrompt() {
      const input = document.getElementById('prompt-input');
      const prompt = input.value.trim();
      if (!prompt) return;

      const term = document.getElementById('terminal-out');
      const btn = document.getElementById('send-btn');
      btn.disabled = true;

      // Update pipeline indicators
      document.getElementById('step-understand').className = 'step active';
      document.getElementById('step-plan').className = 'step';
      document.getElementById('step-execute').className = 'step';
      document.getElementById('step-verify').className = 'step';

      term.innerText = '> ' + prompt + '\\nUnderstanding...\\n';

      try {
        const res = await fetch('/api/prompt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: prompt })
        });
        const data = await res.json();

        if (res.ok) {
          document.getElementById('step-understand').className = 'step done';
          document.getElementById('step-plan').className = 'step done';
          document.getElementById('step-execute').className = 'step done';
          document.getElementById('step-verify').className = 'step done';

          let out = '> ' + prompt + '\\n';
          out += '✓ Understanding completed (Intents: ' + (data.intents.map(i => i.intent).join(', ')) + ')\\n';
          out += '✓ Planning completed (Goal ID: ' + (data.goal ? data.goal.goal_id : 'N/A') + ')\\n';
          out += '✓ Execution finished (Verified: ' + data.verified + ')\\n';
          out += '----------------------------------------------------\\n';
          out += 'Request ID: ' + data.request_id + '\\n';
          out += 'Status: ' + data.status + '\\n';

          if (data.clarification_prompt) {
            out += '\\n[Clarification Needed]: ' + data.clarification_prompt + '\\n';
          }

          term.innerText = out;
        } else {
          term.innerText += '✗ Error (' + res.status + '): ' + (data.detail || JSON.stringify(data));
        }
      } catch (err) {
        term.innerText += '✗ Network failure: ' + err.message;
      } finally {
        btn.disabled = false;
        refreshTelemetry();
      }
    }

    document.getElementById('prompt-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') submitPrompt();
    });

    refreshTelemetry();
  </script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    return DASHBOARD_HTML
