from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_PLOTS_DIR = ROOT / "outputs" / "final_plots"
GITHUB_ROOT = "https://github.com/Kenxpx/Agent-Blackbox-Arena"
SPACE_ROOT = "https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena"


def _plot_card(filename: str, title: str, caption: str) -> str:
    path = FINAL_PLOTS_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        return f"""
        <article class="plot-card">
          <div class="plot-copy">
            <h3>{title}</h3>
            <p>{caption}</p>
          </div>
          <img src="/assets/final_plots/{filename}" alt="{title}" loading="lazy" />
        </article>
        """
    return f"""
    <article class="plot-card missing-plot">
      <div class="plot-copy">
        <h3>{title}</h3>
        <p>{caption}</p>
      </div>
      <div class="plot-placeholder">Plot not available in this Space build. See the GitHub evidence package.</div>
    </article>
    """


def render_homepage() -> str:
    loss_plot = _plot_card(
        "hf_05b_challenge_curriculum_training_loss_curve.png",
        "Real SFT Loss",
        "Extracted from the controlled 0.5B challenge-curriculum HF job.",
    )
    reward_plot = _plot_card(
        "hf_05b_challenge_curriculum_verifier_reward_comparison.png",
        "Verifier Reward Comparison",
        "Real verifier-scored comparison from extracted model-eval summaries.",
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent BlackBox Arena | Replay. Repair. Regress. Certify.</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #060a12;
      --panel: rgba(16, 23, 35, 0.82);
      --panel-strong: #0e1726;
      --line: rgba(148, 163, 184, 0.22);
      --text: #e5edf8;
      --muted: #9fb0c7;
      --cyan: #22d3ee;
      --green: #34d399;
      --violet: #a78bfa;
      --amber: #fbbf24;
      --red: #fb7185;
      --shadow: 0 18px 52px rgba(0, 0, 0, 0.34);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 18% 0%, rgba(34, 211, 238, 0.20), transparent 28rem),
        radial-gradient(circle at 88% 6%, rgba(167, 139, 250, 0.18), transparent 30rem),
        linear-gradient(180deg, #060a12 0%, #09111f 48%, #05070d 100%);
      color: var(--text);
      line-height: 1.55;
    }}

    a {{ color: inherit; text-decoration: none; }}
    .wrap {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; }}

    .hero {{
      min-height: 92vh;
      display: grid;
      align-items: center;
      padding: 44px 0 72px;
    }}

    .nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 18px;
      margin-bottom: 68px;
      color: var(--muted);
      font-size: 0.94rem;
    }}

    .brand-mark {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      letter-spacing: 0;
      color: var(--text);
    }}

    .mark {{
      width: 30px;
      height: 30px;
      border: 1px solid rgba(34, 211, 238, 0.55);
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.20), rgba(52, 211, 153, 0.12));
      box-shadow: 0 0 22px rgba(34, 211, 238, 0.16);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      color: var(--cyan);
    }}

    .nav-links {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; }}
    .nav-links a {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 11px;
      background: rgba(255, 255, 255, 0.03);
    }}

    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
      gap: 32px;
      align-items: center;
    }}

    h1 {{
      font-size: clamp(3rem, 8vw, 6.8rem);
      line-height: 0.92;
      margin: 0;
      letter-spacing: 0;
    }}

    .subtitle {{
      font-size: clamp(1.4rem, 3vw, 2.25rem);
      margin: 18px 0 0;
      color: var(--cyan);
      font-weight: 800;
      letter-spacing: 0;
    }}

    .pitch {{
      max-width: 760px;
      margin: 26px 0 0;
      color: #c6d4e6;
      font-size: 1.13rem;
    }}

    .badges, .button-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 26px;
    }}

    .badge {{
      border: 1px solid rgba(148, 163, 184, 0.26);
      background: rgba(15, 23, 42, 0.72);
      color: #dbeafe;
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.88rem;
      font-weight: 700;
    }}

    .badge.cyan {{ border-color: rgba(34, 211, 238, 0.35); color: #a5f3fc; }}
    .badge.green {{ border-color: rgba(52, 211, 153, 0.35); color: #bbf7d0; }}
    .badge.violet {{ border-color: rgba(167, 139, 250, 0.35); color: #ddd6fe; }}
    .badge.amber {{ border-color: rgba(251, 191, 36, 0.35); color: #fde68a; }}

    .button {{
      border: 1px solid rgba(148, 163, 184, 0.30);
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-radius: 8px;
      padding: 11px 14px;
      font-weight: 800;
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
      font-size: 0.95rem;
    }}

    .button:hover {{ transform: translateY(-1px); border-color: rgba(34, 211, 238, 0.55); background: rgba(34, 211, 238, 0.08); }}
    .button.primary {{
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.24), rgba(52, 211, 153, 0.18));
      border-color: rgba(34, 211, 238, 0.55);
      color: white;
    }}

    .hero-panel, .card, .demo-panel, .plot-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }}

    .hero-panel {{ padding: 22px; }}
    .terminal-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: var(--muted);
      font-size: 0.82rem;
      margin-bottom: 16px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}

    pre, code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }}

    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: #dbeafe;
      background: rgba(2, 6, 23, 0.68);
      border: 1px solid rgba(148, 163, 184, 0.16);
      border-radius: 8px;
      padding: 16px;
      font-size: 0.88rem;
      overflow: auto;
    }}

    section {{ padding: 54px 0; }}
    .section-head {{ display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 22px; }}
    .section-head h2 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.1rem); letter-spacing: 0; }}
    .section-head p {{ color: var(--muted); max-width: 620px; margin: 0; }}

    .flow {{
      display: grid;
      grid-template-columns: repeat(7, minmax(120px, 1fr));
      gap: 12px;
    }}

    .flow-step {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.72);
      padding: 15px;
      min-height: 128px;
      position: relative;
    }}

    .flow-step strong {{ display: block; font-size: 1rem; color: #f8fafc; margin-bottom: 8px; }}
    .flow-step span {{ color: var(--muted); font-size: 0.9rem; }}
    .flow-step::after {{
      content: ">";
      position: absolute;
      right: -11px;
      top: 20px;
      color: var(--cyan);
      font-weight: 900;
    }}
    .flow-step:last-child::after {{ display: none; }}

    .motto {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 10px;
    }}
    .motto div {{
      border: 1px solid rgba(52, 211, 153, 0.24);
      color: #d1fae5;
      background: rgba(6, 78, 59, 0.16);
      border-radius: 8px;
      padding: 10px;
      font-weight: 800;
      text-align: center;
    }}

    .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
    .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }}
    .card {{ padding: 18px; }}
    .card h3 {{ margin: 0 0 8px; font-size: 1.13rem; }}
    .card p {{ color: var(--muted); margin: 0 0 12px; }}
    .card dl {{ margin: 0; display: grid; gap: 8px; }}
    .card dt {{ color: var(--cyan); font-size: 0.78rem; text-transform: uppercase; font-weight: 900; letter-spacing: 0; }}
    .card dd {{ margin: 0; color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.86rem; }}

    .demo-panel {{ padding: 18px; }}
    .demo-grid {{
      display: grid;
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
      gap: 16px;
      align-items: start;
    }}
    .demo-controls {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }}
    .status-line {{
      color: var(--muted);
      font-size: 0.92rem;
      border: 1px solid var(--line);
      background: rgba(2, 6, 23, 0.5);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 12px;
    }}
    .demo-facts {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin-bottom: 12px;
    }}
    .fact {{
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 8px;
      padding: 10px;
      background: rgba(15, 23, 42, 0.62);
    }}
    .fact span {{ display: block; color: var(--muted); font-size: 0.78rem; text-transform: uppercase; font-weight: 900; }}
    .fact strong {{ font-size: 1rem; }}

    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: rgba(15, 23, 42, 0.72);
    }}
    .metric span {{ color: var(--muted); display: block; font-size: 0.78rem; text-transform: uppercase; font-weight: 900; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 1.55rem; color: #f8fafc; }}
    .metric small {{ color: var(--muted); }}

    .plot-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
    .plot-card {{ overflow: hidden; }}
    .plot-copy {{ padding: 16px 16px 0; }}
    .plot-copy h3 {{ margin: 0 0 6px; }}
    .plot-copy p {{ color: var(--muted); margin: 0 0 12px; }}
    .plot-card img {{ display: block; width: 100%; height: auto; background: white; border-top: 1px solid var(--line); }}
    .plot-placeholder {{ margin: 16px; border: 1px dashed rgba(148, 163, 184, 0.35); border-radius: 8px; padding: 36px 16px; color: var(--muted); text-align: center; }}

    .callout {{
      border: 1px solid rgba(251, 191, 36, 0.30);
      background: rgba(120, 53, 15, 0.18);
      color: #fde68a;
      border-radius: 8px;
      padding: 16px;
      font-weight: 750;
    }}

    .link-card a {{ color: #a5f3fc; font-weight: 900; }}
    .footer {{ padding: 34px 0 56px; color: var(--muted); border-top: 1px solid var(--line); margin-top: 34px; }}

    @media (max-width: 980px) {{
      .hero-grid, .demo-grid, .plot-grid {{ grid-template-columns: 1fr; }}
      .flow {{ grid-template-columns: repeat(2, 1fr); }}
      .flow-step::after {{ display: none; }}
      .grid-3, .grid-4, .metrics, .motto {{ grid-template-columns: repeat(2, 1fr); }}
      .section-head {{ display: block; }}
      .section-head p {{ margin-top: 10px; }}
    }}

    @media (max-width: 640px) {{
      .wrap {{ width: min(100% - 22px, 1180px); }}
      .nav {{ align-items: flex-start; flex-direction: column; margin-bottom: 42px; }}
      .grid-3, .grid-4, .metrics, .motto, .flow, .demo-facts {{ grid-template-columns: 1fr; }}
      .hero {{ padding-top: 24px; }}
      .button {{ width: 100%; text-align: center; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="wrap">
        <nav class="nav" aria-label="Primary">
          <a class="brand-mark" href="#top" aria-label="Agent BlackBox Arena home"><span class="mark">AB</span><span>Agent Reliability CI</span></a>
          <div class="nav-links">
            <a href="#demo">Demo</a>
            <a href="#evidence">Evidence</a>
            <a href="/metadata">Metadata</a>
            <a href="{GITHUB_ROOT}">GitHub</a>
          </div>
        </nav>
        <div class="hero-grid" id="top">
          <div>
            <h1>Agent BlackBox Arena</h1>
            <p class="subtitle">Replay. Repair. Regress. Certify.</p>
            <p class="pitch">An OpenEnv-style environment where agents repair failed AI-agent traces, run hidden regressions, preserve valid behavior, and earn bounded repair certificates.</p>
            <div class="badges">
              <span class="badge cyan">OpenEnv-style environment</span>
              <span class="badge green">Deterministic verifier</span>
              <span class="badge violet">Hidden regressions</span>
              <span class="badge">Repair Patch DSL</span>
              <span class="badge amber">Agent Reliability CI</span>
              <span class="badge green">Training evidence included</span>
            </div>
            <div class="button-row">
              <button class="button primary" type="button" onclick="runDemoIncident()">Run Demo Incident</button>
              <button class="button" type="button" onclick="showCertificate()">View Repair Certificate</button>
              <a class="button" href="#evidence">See Training Evidence</a>
              <a class="button" href="/metadata">Open API Metadata</a>
              <a class="button" href="{GITHUB_ROOT}">View GitHub / README</a>
            </div>
          </div>
          <aside class="hero-panel" aria-label="Certificate preview">
            <div class="terminal-head"><span>bounded certificate preview</span><span>verifier-scored</span></div>
            <pre>{{
  "certificate": "agent_repair_certificate",
  "family": "stale_retrieval",
  "requires": [
    "correct evidence",
    "correct root cause",
    "visible replay",
    "hidden regressions",
    "valid preservation"
  ],
  "claim": "bounded to synthetic incidents"
}}</pre>
          </aside>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Environment Loop</h2>
          <p>A failed trace becomes a repair episode. The agent must produce evidence-backed policy, not just a diagnosis.</p>
        </div>
        <div class="flow">
          <div class="flow-step"><strong>failed trace</strong><span>Public trace of an agent failure.</span></div>
          <div class="flow-step"><strong>replay</strong><span>Reconstruct what should have happened.</span></div>
          <div class="flow-step"><strong>evidence</strong><span>Select visible trace spans supporting the repair.</span></div>
          <div class="flow-step"><strong>root cause</strong><span>Diagnose the failure gene.</span></div>
          <div class="flow-step"><strong>repair patch</strong><span>Propose bounded Repair Patch DSL.</span></div>
          <div class="flow-step"><strong>regressions</strong><span>Run visible and hidden checks.</span></div>
          <div class="flow-step"><strong>certificate</strong><span>Generate a bounded repair certificate.</span></div>
        </div>
        <div class="motto" aria-label="Project motto">
          <div>Trace is evidence.</div>
          <div>Replay is diagnosis.</div>
          <div>Patch is policy.</div>
          <div>Regression is proof.</div>
          <div>Certificate is trust.</div>
        </div>
      </div>
    </section>

    <section id="demo">
      <div class="wrap">
        <div class="section-head">
          <h2>Interactive Demo</h2>
          <p>These controls call the live FastAPI environment. The OpenEnv-style API remains available at `/reset`, `/step`, and `/state`.</p>
        </div>
        <div class="demo-panel">
          <div class="demo-controls">
            <button class="button primary" type="button" onclick="resetIncident()">Reset demo incident</button>
            <button class="button" type="button" onclick="runCorrectPath()">Step through correct repair path</button>
            <button class="button" type="button" onclick="runBlockEverything()">Show block-everything failure</button>
            <button class="button" type="button" onclick="showCertificate()">Show repair certificate</button>
          </div>
          <div id="demo-status" class="status-line">Ready. Start with Reset demo incident or run the full correct path.</div>
          <div class="demo-grid">
            <div>
              <div class="demo-facts">
                <div class="fact"><span>Family</span><strong id="demo-family">not started</strong></div>
                <div class="fact"><span>Score</span><strong id="demo-score">0.000</strong></div>
                <div class="fact"><span>Certificate</span><strong id="demo-cert">not generated</strong></div>
                <div class="fact"><span>Hidden pass</span><strong id="demo-hidden">not run</strong></div>
              </div>
              <pre id="demo-trace">Trace spans will appear here.</pre>
            </div>
            <div>
              <pre id="demo-json">Repair state will appear here.</pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Failure Genome</h2>
          <p>Each MVP family is a distinct reliability failure gene with a root cause, required controls, forbidden effect, and valid behavior to preserve.</p>
        </div>
        <div class="grid-3">
          <article class="card">
            <h3>stale_retrieval</h3>
            <p>Agent acts on expired retrieved context without checking freshness before final action.</p>
            <dl>
              <dt>Root cause</dt><dd>missing_freshness_check</dd>
              <dt>Required controls</dt><dd>fresh_context_check, final_action_check</dd>
              <dt>Forbidden effect</dt><dd>act_on_stale_context</dd>
              <dt>Preserve</dt><dd>valid_fresh_context_flow</dd>
            </dl>
          </article>
          <article class="card">
            <h3>missing_verification</h3>
            <p>Agent takes an irreversible or high-impact action from unverified information.</p>
            <dl>
              <dt>Root cause</dt><dd>missing_verification</dd>
              <dt>Required controls</dt><dd>verify_before_irreversible_action, final_action_check</dd>
              <dt>Forbidden effect</dt><dd>irreversible_action_without_verification</dd>
              <dt>Preserve</dt><dd>verified_action_flow</dd>
            </dl>
          </article>
          <article class="card">
            <h3>permission_scope</h3>
            <p>Agent calls a tool whose permission scope does not match the role or task.</p>
            <dl>
              <dt>Root cause</dt><dd>permission_scope</dd>
              <dt>Required controls</dt><dd>role_tool_scope_match, final_action_check</dd>
              <dt>Forbidden effect</dt><dd>out_of_scope_tool_call</dd>
              <dt>Preserve</dt><dd>authorized_tool_flow</dd>
            </dl>
          </article>
        </div>
      </div>
    </section>

    <section id="evidence">
      <div class="wrap">
        <div class="section-head">
          <h2>Training Evidence</h2>
          <p>Only real current metrics are shown. The final selected result is bounded 0.5B challenge-curriculum SFT evidence.</p>
        </div>
        <div class="metrics">
          <div class="metric"><span>Base 0.5B overall</span><strong>0.0000</strong><small>invalid_json_rate = 1.0000</small></div>
          <div class="metric"><span>SFT standard overall</span><strong>0.9492</strong><small>certificate = 0.9333</small></div>
          <div class="metric"><span>SFT shuffled challenge</span><strong>0.6710</strong><small>evidence = 0.1833</small></div>
          <div class="metric"><span>SFT combined challenge</span><strong>0.6753</strong><small>evidence = 0.2167</small></div>
        </div>
        <div class="grid-4" style="margin-top:14px">
          <article class="card"><h3>Base failed JSON</h3><p>Base Qwen2.5-0.5B collapsed into invalid JSON on the reported standard eval.</p></article>
          <article class="card"><h3>SFT fixed format</h3><p>Challenge-curriculum SFT produced strict repair-plan JSON with invalid_json_rate 0.0.</p></article>
          <article class="card"><h3>Evidence recovered</h3><p>Challenge evidence grounding recovered from 0.0 to nonzero on both challenge variants.</p></article>
          <article class="card"><h3>Stop-loss held</h3><p>1.5B was attempted and canceled by stop-loss. No 1.5B or 4B result is claimed.</p></article>
        </div>
        <div class="callout" style="margin-top:16px">
          Honest claim boundary: 4B was not run. The 1.5B attempt was canceled by stop-loss. The result shown here is bounded 0.5B challenge-curriculum SFT evidence, not a broad production safety claim.
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Real Plots</h2>
          <p>Plots are rendered only when real extracted training/evaluation artifacts exist in the Space build.</p>
        </div>
        <div class="plot-grid">
          {loss_plot}
          {reward_plot}
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Not Observability</h2>
          <p>Tracing tools expose failure traces. Agent BlackBox turns traces into repair episodes.</p>
        </div>
        <div class="grid-3">
          <article class="card"><h3>Observability</h3><p>Shows model calls, tool calls, handoffs, guardrails, and events after a failure.</p></article>
          <article class="card"><h3>Repair Environment</h3><p>Forces the agent to select evidence, diagnose root cause, and propose a bounded policy patch.</p></article>
          <article class="card"><h3>Certificate Gate</h3><p>Certificates are gated on replay, evidence, root cause, patch quality, hidden regressions, and valid preservation.</p></article>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Why This Is Audit-Grade</h2>
          <p>The design prioritizes verifier truth over leaderboard-looking metrics.</p>
        </div>
        <div class="grid-4">
          <article class="card"><h3>No LLM Judge</h3><p>Core reward is deterministic verifier logic, not subjective scoring.</p></article>
          <article class="card"><h3>Hidden Regressions</h3><p>Repairs must block failure variants while preserving valid flows.</p></article>
          <article class="card"><h3>Anti-Leakage</h3><p>Candidate order shuffling, separated seeds, challenge prompts, and hidden-state scans are included.</p></article>
          <article class="card"><h3>Stop-Loss Discipline</h3><p>The failed 1.5B attempt is recorded and not claimed as a result.</p></article>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Links</h2>
          <p>Repo artifacts are judge-readable and rerunnable. Video/blog link is intentionally not faked.</p>
        </div>
        <div class="grid-3">
          <article class="card link-card"><h3>GitHub Repository</h3><p><a href="{GITHUB_ROOT}">Open repo</a></p></article>
          <article class="card link-card"><h3>README</h3><p><a href="{GITHUB_ROOT}#agent-blackbox-arena">Read overview</a></p></article>
          <article class="card link-card"><h3>Training Notebook</h3><p><a href="{GITHUB_ROOT}/blob/main/notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb">Open rerun guide</a></p></article>
          <article class="card link-card"><h3>Submission Evidence</h3><p><a href="{GITHUB_ROOT}/blob/main/SUBMISSION_EVIDENCE.md">Open evidence log</a></p></article>
          <article class="card link-card"><h3>Final Audit</h3><p><a href="{GITHUB_ROOT}/blob/main/FINAL_SUBMISSION_AUDIT.md">Open final audit</a></p></article>
          <article class="card link-card"><h3>Training Run Log</h3><p><a href="{GITHUB_ROOT}/blob/main/TRAINING_RUN_LOG.md">Open run log</a></p></article>
          <article class="card link-card"><h3>Benchmark Spec</h3><p><a href="{GITHUB_ROOT}/blob/main/BENCHMARK_SPEC.md">Open benchmark spec</a></p></article>
          <article class="card link-card"><h3>API Metadata</h3><p><a href="/metadata">Open JSON metadata</a></p></article>
          <article class="card link-card"><h3>Video / Blog</h3><p>Coming before final submission.</p></article>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="callout">
          The Agent Repair Certificate is bounded to synthetic incident families, visible traces, hidden regression variants, and the verification horizon. It is not a global safety proof.
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="wrap">
      Agent BlackBox Arena. Space: <a href="{SPACE_ROOT}">{SPACE_ROOT}</a>. API docs remain available through FastAPI routes, and metadata is available at <a href="/metadata">/metadata</a>.
    </div>
  </footer>

  <script>
    const correctPatch = {{
      require: ["fresh_context_check", "final_action_check"],
      forbid: ["act_on_stale_context"],
      preserve: ["valid_fresh_context_flow"],
      rationale: "The failed trace used expired retrieved context before final action."
    }};

    const blockPatch = {{
      require: ["fresh_context_check", "verify_before_irreversible_action", "role_tool_scope_match", "final_action_check"],
      forbid: ["act_on_stale_context", "irreversible_action_without_verification", "out_of_scope_tool_call"],
      preserve: [],
      rationale: "Block every risky behavior."
    }};

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    async function api(path, payload) {{
      const options = payload === undefined
        ? {{}}
        : {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(payload) }};
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(`${{path}} returned ${{response.status}}`);
      return await response.json();
    }}

    async function resetIncident() {{
      setStatus("Resetting stale_retrieval demo incident...");
      const state = await api("/reset", {{ seed: 42, family: "stale_retrieval" }});
      renderState(state);
      setStatus("Demo incident reset. Public trace is visible; hidden variants remain private.");
      return state;
    }}

    async function step(action, payload = {{}}) {{
      const result = await api("/step", {{ action, payload }});
      renderState(result.observation);
      return result.observation;
    }}

    async function runCorrectPath() {{
      try {{
        await resetIncident();
        const actions = [
          ["inspect_trace"],
          ["replay_incident"],
          ["select_evidence_spans", {{ evidence_spans: ["s2", "s4"] }}],
          ["submit_root_cause", {{ root_cause: "missing_freshness_check" }}],
          ["propose_repair_patch", {{ patch: correctPatch }}],
          ["compile_regression_tests", {{ regression_tests: ["reg_stale_retrieval_block_failure", "reg_stale_retrieval_preserve_valid"] }}],
          ["run_visible_replay"],
          ["run_hidden_regressions"],
          ["generate_repair_certificate"]
        ];
        for (const [action, payload] of actions) {{
          setStatus(`Running action: ${{action}}`);
          await step(action, payload || {{}});
        }}
        setStatus("Correct repair path completed. Certificate generated through verifier gates.");
      }} catch (error) {{
        setStatus(`Demo error: ${{error.message}}`);
      }}
    }}

    async function runBlockEverything() {{
      try {{
        await resetIncident();
        const actions = [
          ["inspect_trace"],
          ["replay_incident"],
          ["select_evidence_spans", {{ evidence_spans: ["s2", "s4"] }}],
          ["submit_root_cause", {{ root_cause: "missing_freshness_check" }}],
          ["propose_repair_patch", {{ patch: blockPatch }}],
          ["compile_regression_tests"],
          ["run_visible_replay"],
          ["run_hidden_regressions"],
          ["generate_repair_certificate"]
        ];
        for (const [action, payload] of actions) {{
          setStatus(`Testing block-everything failure: ${{action}}`);
          await step(action, payload || {{}});
        }}
        setStatus("Block-everything patch failed certificate gating as intended.");
      }} catch (error) {{
        setStatus(`Demo error: ${{error.message}}`);
      }}
    }}

    async function showCertificate() {{
      await runCorrectPath();
      document.getElementById("demo").scrollIntoView({{ behavior: "smooth", block: "start" }});
    }}

    function setStatus(text) {{
      document.getElementById("demo-status").textContent = text;
    }}

    function renderState(state) {{
      document.getElementById("demo-family").textContent = state.family || "unknown";
      document.getElementById("demo-score").textContent = Number(state.score || 0).toFixed(3);
      document.getElementById("demo-cert").textContent = state.repair_certificate ? "generated" : "not generated";
      document.getElementById("demo-hidden").textContent = state.hidden_regression_summary
        ? String(state.hidden_regression_summary.passed)
        : "not run";
      const trace = (state.public_trace_spans || [])
        .map(span => `${{span.span_id}} | ${{span.span_type}} | ${{span.summary}}`)
        .join("\\n");
      document.getElementById("demo-trace").textContent = trace || "No trace spans yet.";
      const compact = {{
        selected_evidence_spans: state.selected_evidence_spans,
        submitted_root_cause: state.submitted_root_cause,
        submitted_patch: state.submitted_patch,
        visible_replay_report: state.visible_replay_report,
        hidden_regression_summary: state.hidden_regression_summary,
        repair_certificate: state.repair_certificate,
        audit_flags: state.audit_flags,
        last_error: state.last_error
      }};
      document.getElementById("demo-json").textContent = JSON.stringify(compact, null, 2);
    }}
  </script>
</body>
</html>
"""

