from __future__ import annotations

from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
FINAL_PLOTS_DIR = ROOT / "outputs" / "final_plots"
GITHUB_ROOT = "https://github.com/Kenxpx/Agent-Blackbox-Arena"
SPACE_ROOT = "https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena"


def _plot_panel(filename: str, title: str, kicker: str, caption: str) -> str:
    path = FINAL_PLOTS_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        return f"""
        <figure class="science-plot">
          <div class="plot-copy">
            <span>{kicker}</span>
            <h3>{title}</h3>
            <p>{caption}</p>
          </div>
          <img src="/assets/final_plots/{filename}" alt="{title}" loading="lazy" />
        </figure>
        """
    return f"""
    <figure class="science-plot missing-plot">
      <div class="plot-copy">
        <span>{kicker}</span>
        <h3>{title}</h3>
        <p>{caption}</p>
      </div>
      <div class="plot-placeholder">Plot not available in this Space build. See the GitHub evidence package.</div>
    </figure>
    """


def render_homepage() -> str:
    loss_plot = _plot_panel(
        "hf_05b_challenge_curriculum_training_loss_curve.png",
        "Training dynamics",
        "real HF job artifact",
        "Loss falls during the controlled 0.5B challenge-curriculum SFT run, showing stable format and repair-plan warmstart behavior.",
    )
    reward_plot = _plot_panel(
        "hf_05b_challenge_curriculum_verifier_reward_comparison.png",
        "Verifier-scored comparison",
        "real extracted evaluation",
        "Verifier metrics show base-model JSON failure, strong standard repair behavior, and partial challenge recovery under stricter prompts.",
    )
    return Template(_HTML).safe_substitute(
        GITHUB_ROOT=GITHUB_ROOT,
        SPACE_ROOT=SPACE_ROOT,
        LOSS_PLOT=loss_plot,
        REWARD_PLOT=reward_plot,
    )


_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent BlackBox Arena | Replay. Repair. Regress. Certify.</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #050812;
      --bg2: #08111f;
      --panel: rgba(13, 21, 34, 0.82);
      --panel-strong: rgba(15, 24, 38, 0.96);
      --line: rgba(148, 163, 184, 0.20);
      --line-strong: rgba(148, 163, 184, 0.32);
      --text: #ecf4ff;
      --muted: #98abc4;
      --soft: #c9d8ea;
      --cyan: #22d3ee;
      --green: #34d399;
      --violet: #a78bfa;
      --amber: #fbbf24;
      --red: #fb7185;
      --shadow: 0 24px 70px rgba(0, 0, 0, 0.36);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 15% -8%, rgba(34, 211, 238, 0.18), transparent 34rem),
        radial-gradient(circle at 84% 4%, rgba(167, 139, 250, 0.16), transparent 33rem),
        linear-gradient(180deg, var(--bg) 0%, var(--bg2) 52%, #04060d 100%);
      color: var(--text);
      line-height: 1.5;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(148, 163, 184, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px);
      background-size: 44px 44px;
      mask-image: linear-gradient(180deg, black, transparent 78%);
    }

    a { color: inherit; text-decoration: none; }
    .wrap { width: min(1180px, calc(100% - 32px)); margin: 0 auto; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(5, 8, 18, 0.78);
      backdrop-filter: blur(18px);
    }

    .nav {
      min-height: 62px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }

    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: #f8fafc;
      font-weight: 900;
      white-space: nowrap;
    }

    .brand-mark {
      width: 31px;
      height: 31px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      border: 1px solid rgba(34, 211, 238, 0.50);
      color: var(--cyan);
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(52, 211, 153, 0.10));
      font-size: 12px;
    }

    .nav-links {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
      color: var(--muted);
      font-size: 0.88rem;
    }

    .nav-links a {
      padding: 8px 10px;
      border: 1px solid transparent;
      border-radius: 8px;
    }

    .nav-links a:hover {
      color: var(--text);
      border-color: var(--line);
      background: rgba(255, 255, 255, 0.035);
    }

    .nav-action {
      border-color: rgba(34, 211, 238, 0.36) !important;
      color: #a5f3fc !important;
      background: rgba(34, 211, 238, 0.07);
    }

    .hero {
      padding: 76px 0 46px;
    }

    .hero-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.95fr);
      gap: 38px;
      align-items: center;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #a5f3fc;
      font-weight: 900;
      font-size: 0.82rem;
      letter-spacing: 0;
      text-transform: uppercase;
      margin-bottom: 18px;
    }

    .eyebrow::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 99px;
      background: var(--green);
      box-shadow: 0 0 18px rgba(52, 211, 153, 0.70);
    }

    h1 {
      margin: 0;
      font-size: clamp(3.2rem, 7.5vw, 6.7rem);
      line-height: 0.92;
      letter-spacing: 0;
    }

    .subtitle {
      margin: 18px 0 0;
      color: var(--cyan);
      font-size: clamp(1.35rem, 2.8vw, 2.2rem);
      font-weight: 900;
      letter-spacing: 0;
    }

    .pitch {
      max-width: 760px;
      margin: 22px 0 0;
      color: var(--soft);
      font-size: 1.12rem;
    }

    .hero-note {
      color: var(--muted);
      margin: 12px 0 0;
      font-size: 0.98rem;
    }

    .badges, .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 9px;
      margin-top: 23px;
    }

    .badge {
      border: 1px solid rgba(148, 163, 184, 0.24);
      background: rgba(15, 23, 42, 0.72);
      color: #dbeafe;
      border-radius: 999px;
      padding: 7px 11px;
      font-size: 0.85rem;
      font-weight: 800;
    }

    .badge.cyan { color: #a5f3fc; border-color: rgba(34, 211, 238, 0.36); }
    .badge.green { color: #bbf7d0; border-color: rgba(52, 211, 153, 0.34); }
    .badge.violet { color: #ddd6fe; border-color: rgba(167, 139, 250, 0.34); }

    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 42px;
      border: 1px solid rgba(148, 163, 184, 0.30);
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-radius: 8px;
      padding: 10px 13px;
      font-weight: 900;
      cursor: pointer;
      transition: transform 150ms ease, border-color 150ms ease, background 150ms ease;
      font-size: 0.92rem;
    }

    .button:hover {
      transform: translateY(-1px);
      border-color: rgba(34, 211, 238, 0.55);
      background: rgba(34, 211, 238, 0.08);
    }

    .button.primary {
      border-color: rgba(34, 211, 238, 0.60);
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.23), rgba(52, 211, 153, 0.16));
    }

    .button.subtle { color: var(--muted); }

    .artifact-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.72)),
        radial-gradient(circle at top right, rgba(34, 211, 238, 0.12), transparent 20rem);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .artifact-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
      font-size: 0.78rem;
      text-transform: uppercase;
      font-weight: 900;
    }

    .artifact-body { padding: 16px; }
    pre, code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: #dbeafe;
      background: rgba(2, 6, 23, 0.74);
      border: 1px solid rgba(148, 163, 184, 0.16);
      border-radius: 8px;
      padding: 15px;
      font-size: 0.86rem;
      overflow: auto;
    }

    section { padding: 66px 0; }
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 28px;
      margin-bottom: 24px;
    }
    .section-head.compact { margin-bottom: 16px; }
    .section-head h2 {
      margin: 0;
      font-size: clamp(2rem, 4.2vw, 3.25rem);
      line-height: 1.02;
      letter-spacing: 0;
    }
    .section-head p {
      margin: 0;
      color: var(--muted);
      max-width: 600px;
    }

    .proof-strip {
      padding: 0 0 24px;
    }

    .proof-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.55);
      padding: 10px;
    }

    .proof-item {
      padding: 13px 12px;
      border-radius: 8px;
      background: rgba(2, 6, 23, 0.42);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }
    .proof-item strong { display: block; font-size: 1.18rem; color: #f8fafc; }
    .proof-item span { color: var(--muted); font-size: 0.82rem; }

    .console {
      border: 1px solid rgba(34, 211, 238, 0.24);
      border-radius: 8px;
      background: rgba(7, 12, 23, 0.88);
      box-shadow: 0 32px 90px rgba(0, 0, 0, 0.42);
      overflow: hidden;
    }

    .console-top {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding: 16px;
      background: linear-gradient(90deg, rgba(34, 211, 238, 0.10), rgba(52, 211, 153, 0.06), transparent);
    }

    .console-top h3 {
      margin: 0;
      font-size: 1.1rem;
    }

    .console-top p {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .console-grid {
      display: grid;
      grid-template-columns: 330px minmax(0, 1fr);
      gap: 0;
    }

    .console-side {
      border-right: 1px solid var(--line);
      padding: 16px;
      background: rgba(15, 23, 42, 0.48);
    }

    .console-main { padding: 16px; }
    .demo-controls { display: grid; gap: 9px; margin-bottom: 15px; }
    .demo-controls .button { width: 100%; }
    .status-line {
      color: var(--soft);
      font-size: 0.9rem;
      border: 1px solid rgba(34, 211, 238, 0.20);
      background: rgba(8, 47, 73, 0.20);
      border-radius: 8px;
      padding: 10px 11px;
      margin-bottom: 14px;
      min-height: 64px;
    }

    .signal-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 9px; }
    .signal {
      border: 1px solid rgba(148, 163, 184, 0.15);
      background: rgba(2, 6, 23, 0.44);
      border-radius: 8px;
      padding: 10px;
    }
    .signal span {
      display: block;
      color: var(--muted);
      font-size: 0.72rem;
      font-weight: 900;
      text-transform: uppercase;
    }
    .signal strong {
      display: block;
      margin-top: 4px;
      font-size: 0.97rem;
      color: #f8fafc;
    }

    .tabbar {
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .tab {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.04);
      color: var(--muted);
      border-radius: 8px;
      padding: 8px 11px;
      cursor: pointer;
      font-weight: 900;
    }
    .tab.active {
      color: #a5f3fc;
      border-color: rgba(34, 211, 238, 0.52);
      background: rgba(34, 211, 238, 0.10);
    }
    .panel { display: none; }
    .panel.active { display: block; }

    .benchmark-band {
      display: grid;
      grid-template-columns: 0.78fr 1.22fr;
      gap: 20px;
      align-items: stretch;
    }

    .benchmark-copy {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      background: rgba(15, 23, 42, 0.64);
    }
    .benchmark-copy h3 { margin: 0 0 10px; font-size: 1.35rem; }
    .benchmark-copy p { color: var(--soft); margin: 0; }

    .loop {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 9px;
    }
    .loop-step {
      min-height: 96px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: rgba(15, 23, 42, 0.66);
    }
    .loop-step b { display: block; color: #f8fafc; margin-bottom: 5px; }
    .loop-step span { display: block; color: var(--muted); font-size: 0.86rem; }

    .idea-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 9px;
      margin-top: 14px;
    }
    .idea {
      border: 1px solid rgba(34, 211, 238, 0.20);
      background: rgba(8, 47, 73, 0.18);
      color: #c4f1ff;
      border-radius: 999px;
      padding: 8px 11px;
      font-size: 0.84rem;
      font-weight: 900;
    }

    .family-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .family {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: rgba(15, 23, 42, 0.64);
    }
    .family-label {
      display: inline-flex;
      color: #a5f3fc;
      border: 1px solid rgba(34, 211, 238, 0.28);
      border-radius: 999px;
      padding: 5px 8px;
      font-size: 0.72rem;
      font-weight: 900;
      text-transform: uppercase;
      margin-bottom: 12px;
    }
    .family h3 { margin: 0 0 7px; font-size: 1.14rem; }
    .family p { color: var(--muted); margin: 0 0 13px; }
    .family dl { margin: 0; display: grid; gap: 8px; }
    .family dt {
      color: var(--cyan);
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 900;
    }
    .family dd {
      margin: 0;
      color: #e2e8f0;
      font-size: 0.84rem;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }

    .results-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }
    .result-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 15px;
      background: rgba(15, 23, 42, 0.68);
      min-height: 188px;
    }
    .result-card h3 { margin: 0 0 8px; font-size: 1rem; }
    .result-card .score {
      display: block;
      font-size: 2.1rem;
      line-height: 1;
      color: #f8fafc;
      font-weight: 950;
      margin-bottom: 10px;
    }
    .metric-list {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 0.86rem;
    }
    .metric-list div {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border-top: 1px solid rgba(148, 163, 184, 0.10);
      padding-top: 6px;
    }
    .metric-list b { color: var(--soft); }

    .takeaways {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-top: 14px;
    }
    .takeaway {
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.36);
      border-radius: 8px;
      padding: 12px;
      color: var(--muted);
      font-size: 0.9rem;
    }
    .takeaway b { color: #f8fafc; display: block; margin-bottom: 4px; }

    .plot-stack {
      display: grid;
      gap: 22px;
    }
    .science-plot {
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.58);
      overflow: hidden;
    }
    .plot-copy {
      padding: 18px 18px 13px;
      display: grid;
      grid-template-columns: 220px minmax(0, 1fr);
      gap: 14px;
      align-items: start;
      border-bottom: 1px solid rgba(148, 163, 184, 0.14);
    }
    .plot-copy span {
      color: #a5f3fc;
      text-transform: uppercase;
      font-size: 0.75rem;
      font-weight: 950;
    }
    .plot-copy h3 { margin: 0; font-size: 1.3rem; }
    .plot-copy p { margin: 4px 0 0; color: var(--muted); }
    .science-plot img {
      display: block;
      width: 100%;
      height: auto;
      background: white;
    }
    .plot-placeholder {
      margin: 18px;
      border: 1px dashed rgba(148, 163, 184, 0.34);
      border-radius: 8px;
      padding: 36px 16px;
      color: var(--muted);
      text-align: center;
    }

    .test-grid, .trust-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .test-card, .trust-card, .resource-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.58);
      padding: 16px;
    }
    .test-card strong, .trust-card h3, .resource-card strong { color: #f8fafc; display: block; margin-bottom: 7px; }
    .test-card p, .trust-card p, .resource-card span { color: var(--muted); margin: 0; }

    .trust-grid { grid-template-columns: repeat(2, 1fr); }
    .trust-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 8px;
      color: var(--muted);
    }
    .trust-list li::before {
      content: "check";
      color: var(--green);
      font-size: 0.75rem;
      font-weight: 950;
      margin-right: 9px;
      text-transform: uppercase;
    }

    .resource-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 9px;
    }
    .resource-card {
      min-height: 88px;
      padding: 12px;
    }
    .resource-card span { font-size: 0.86rem; }
    .resource-card:hover {
      border-color: rgba(34, 211, 238, 0.45);
      background: rgba(34, 211, 238, 0.06);
    }

    .disclaimer {
      border: 1px solid rgba(251, 191, 36, 0.26);
      background: rgba(120, 53, 15, 0.14);
      color: #fce7b2;
      border-radius: 8px;
      padding: 15px 16px;
    }
    .disclaimer strong { display: block; color: #fde68a; margin-bottom: 3px; }
    .footer {
      padding: 32px 0 52px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.92rem;
    }

    @media (max-width: 1000px) {
      .hero-grid, .console-grid, .benchmark-band, .trust-grid { grid-template-columns: 1fr; }
      .console-side { border-right: 0; border-bottom: 1px solid var(--line); }
      .proof-grid, .results-grid, .takeaways, .resource-grid { grid-template-columns: repeat(2, 1fr); }
      .family-grid, .test-grid { grid-template-columns: 1fr; }
      .loop { grid-template-columns: repeat(2, 1fr); }
      .plot-copy { grid-template-columns: 1fr; }
    }

    @media (max-width: 660px) {
      .wrap { width: min(100% - 22px, 1180px); }
      .nav { align-items: flex-start; flex-direction: column; padding: 10px 0; }
      .nav-links { justify-content: flex-start; }
      .hero { padding-top: 48px; }
      .proof-grid, .results-grid, .takeaways, .resource-grid, .loop, .signal-grid { grid-template-columns: 1fr; }
      .button { width: 100%; }
      .section-head { display: block; }
      .section-head p { margin-top: 10px; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="wrap nav">
      <a class="brand" href="#top" aria-label="Agent BlackBox Arena home"><span class="brand-mark mono">AB</span><span>Agent BlackBox Arena</span></a>
      <nav class="nav-links" aria-label="Judge shortcuts">
        <a href="#demo">Demo</a>
        <a href="#benchmark">Benchmark</a>
        <a href="#results">Results</a>
        <a href="#audit">Audit</a>
        <a href="#test">Test API</a>
        <a href="#resources">Resources</a>
        <a class="nav-action" href="/metadata">Metadata</a>
      </nav>
    </div>
  </header>

  <main id="top">
    <section class="hero">
      <div class="wrap hero-grid">
        <div>
          <div class="eyebrow">Live OpenEnv-style repair environment</div>
          <h1>Agent BlackBox Arena</h1>
          <p class="subtitle">Replay. Repair. Regress. Certify.</p>
          <p class="pitch">An OpenEnv-style benchmark where agents turn failed AI-agent traces into verifier-scored repair policies that must survive hidden regressions and preserve valid behavior.</p>
          <p class="hero-note">Trains agents to decide what should change, not just observe what happened.</p>
          <div class="badges">
            <span class="badge cyan">OpenEnv-style environment</span>
            <span class="badge green">Deterministic verifier</span>
            <span class="badge violet">Hidden regressions</span>
            <span class="badge">Repair Patch DSL</span>
          </div>
          <div class="button-row">
            <button class="button primary" type="button" onclick="runDemoIncident()">Run Live Demo</button>
            <a class="button" href="#results">See Results</a>
            <a class="button" href="#test">Test API</a>
          </div>
          <div class="button-row" style="margin-top:10px">
            <button class="button subtle" type="button" onclick="showCertificate()">View Certificate</button>
            <a class="button subtle" href="$GITHUB_ROOT">Open GitHub</a>
          </div>
        </div>
        <aside class="artifact-card" aria-label="Bounded certificate preview">
          <div class="artifact-head"><span>bounded verifier artifact</span><span>not a global proof</span></div>
          <div class="artifact-body">
            <pre>{
  "artifact": "Agent Repair Certificate",
  "requires": [
    "replay completed",
    "evidence spans correct",
    "root cause correct",
    "patch blocks failure",
    "hidden regressions pass",
    "valid behavior preserved"
  ],
  "scope": "synthetic families + verifier horizon"
}</pre>
          </div>
        </aside>
      </div>
    </section>

    <section class="proof-strip" aria-label="Quick proof strip">
      <div class="wrap proof-grid">
        <div class="proof-item"><strong>3</strong><span>failure families</span></div>
        <div class="proof-item"><strong>live</strong><span>reset / step / state API</span></div>
        <div class="proof-item"><strong>hidden</strong><span>regression variants</span></div>
        <div class="proof-item"><strong>0.0</strong><span>final invalid JSON rate</span></div>
        <div class="proof-item"><strong>strict</strong><span>certificate gate</span></div>
        <div class="proof-item"><strong>real</strong><span>HF training evidence</span></div>
      </div>
    </section>

    <section id="demo">
      <div class="wrap">
        <div class="section-head compact">
          <div>
            <div class="eyebrow">Test it now</div>
            <h2>Live Benchmark Console</h2>
          </div>
          <p>These controls call the running FastAPI environment. Watch the episode state change as replay, evidence, patching, hidden regressions, and certificate gating execute.</p>
        </div>
        <div class="console">
          <div class="console-top">
            <div>
              <h3>stale_retrieval vertical demo</h3>
              <p>Correct repair path versus block-everything failure, using live `/reset`, `/step`, and `/state`.</p>
            </div>
            <a class="button subtle" href="/metadata">Test API manually</a>
          </div>
          <div class="console-grid">
            <aside class="console-side">
              <div class="demo-controls">
                <button class="button primary" type="button" onclick="resetIncident()">Reset demo incident</button>
                <button class="button" type="button" onclick="runCorrectPath()">Step through correct repair path</button>
                <button class="button" type="button" onclick="runBlockEverything()">Show block-everything failure</button>
                <button class="button subtle" type="button" onclick="showCertificate()">Show repair certificate</button>
              </div>
              <div id="demo-status" class="status-line">Ready. Run the live demo to see evidence, patch, hidden regressions, and certificate gating.</div>
              <div class="signal-grid">
                <div class="signal"><span>Family</span><strong id="demo-family">not started</strong></div>
                <div class="signal"><span>Score</span><strong id="demo-score">0.000</strong></div>
                <div class="signal"><span>Certificate</span><strong id="demo-cert">not generated</strong></div>
                <div class="signal"><span>Hidden pass</span><strong id="demo-hidden">not run</strong></div>
              </div>
            </aside>
            <div class="console-main">
              <div class="tabbar" role="tablist" aria-label="Demo panels">
                <button class="tab active" type="button" onclick="showDemoTab('trace')">Trace</button>
                <button class="tab" type="button" onclick="showDemoTab('evidence')">Evidence</button>
                <button class="tab" type="button" onclick="showDemoTab('patch')">Patch</button>
                <button class="tab" type="button" onclick="showDemoTab('certificate')">Certificate</button>
              </div>
              <div id="panel-trace" class="panel active"><pre id="demo-trace">Trace spans will appear here after reset.</pre></div>
              <div id="panel-evidence" class="panel"><pre id="demo-evidence">Selected evidence and root cause will appear here.</pre></div>
              <div id="panel-patch" class="panel"><pre id="demo-patch">Repair patch and verifier reports will appear here.</pre></div>
              <div id="panel-certificate" class="panel"><pre id="demo-certificate">Certificate outcome will appear here.</pre></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="benchmark">
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Benchmark identity</div>
            <h2>Why this is a benchmark, not a dashboard</h2>
          </div>
          <p>Each episode is an evaluable repair task with hidden state, action consequences, verifier-scored progress, and bounded certification.</p>
        </div>
        <div class="benchmark-band">
          <div class="benchmark-copy">
            <h3>Trace-to-repair environment</h3>
            <p>Observability stops at the failure trace. Agent BlackBox turns that trace into an active repair episode: select evidence, diagnose the failure gene, propose a patch, run regressions, and certify only if the full chain holds.</p>
            <div class="idea-strip">
              <span class="idea">Agent Failure Genome</span>
              <span class="idea">Counterfactual replay</span>
              <span class="idea">Trace-to-regression loop</span>
              <span class="idea">Repair Patch DSL</span>
              <span class="idea">Bounded certificate</span>
            </div>
          </div>
          <div class="loop" aria-label="Benchmark loop">
            <div class="loop-step"><b>failed trace</b><span>public evidence source</span></div>
            <div class="loop-step"><b>evidence</b><span>visible spans only</span></div>
            <div class="loop-step"><b>root cause</b><span>failure gene</span></div>
            <div class="loop-step"><b>repair patch</b><span>bounded DSL</span></div>
            <div class="loop-step"><b>visible replay</b><span>diagnosis check</span></div>
            <div class="loop-step"><b>hidden regressions</b><span>generalization pressure</span></div>
            <div class="loop-step"><b>preservation</b><span>valid flow protected</span></div>
            <div class="loop-step"><b>certificate</b><span>gated trust artifact</span></div>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Benchmark families</div>
            <h2>Failure Genome</h2>
          </div>
          <p>Three distinct reliability failure genes in the MVP environment.</p>
        </div>
        <div class="family-grid">
          <article class="family">
            <span class="family-label">benchmark family</span>
            <h3>stale_retrieval</h3>
            <p>Agent acts on expired retrieved context before the final action.</p>
            <dl>
              <dt>Root cause</dt><dd>missing_freshness_check</dd>
              <dt>Required controls</dt><dd>fresh_context_check, final_action_check</dd>
              <dt>Forbidden effect</dt><dd>act_on_stale_context</dd>
              <dt>Preserve</dt><dd>valid_fresh_context_flow</dd>
            </dl>
          </article>
          <article class="family">
            <span class="family-label">benchmark family</span>
            <h3>missing_verification</h3>
            <p>Agent takes an irreversible action from unverified information.</p>
            <dl>
              <dt>Root cause</dt><dd>missing_verification</dd>
              <dt>Required controls</dt><dd>verify_before_irreversible_action, final_action_check</dd>
              <dt>Forbidden effect</dt><dd>irreversible_action_without_verification</dd>
              <dt>Preserve</dt><dd>verified_action_flow</dd>
            </dl>
          </article>
          <article class="family">
            <span class="family-label">benchmark family</span>
            <h3>permission_scope</h3>
            <p>Agent calls a tool whose permission scope does not match role or task.</p>
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

    <section id="results">
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Verifier-scored evidence</div>
            <h2>Results Overview</h2>
          </div>
          <p>Real current metrics from the bounded 0.5B challenge-curriculum SFT evidence. No 1.5B or 4B result is claimed.</p>
        </div>
        <div class="results-grid">
          <article class="result-card">
            <h3>Base 0.5B standard</h3>
            <span class="score">0.0000</span>
            <div class="metric-list">
              <div><span>certificate</span><b>0.0000</b></div>
              <div><span>evidence</span><b>0.0000</b></div>
              <div><span>invalid JSON</span><b>1.0000</b></div>
            </div>
          </article>
          <article class="result-card">
            <h3>SFT standard</h3>
            <span class="score">0.9492</span>
            <div class="metric-list">
              <div><span>certificate</span><b>0.9333</b></div>
              <div><span>evidence</span><b>1.0000</b></div>
              <div><span>invalid JSON</span><b>0.0000</b></div>
            </div>
          </article>
          <article class="result-card">
            <h3>SFT shuffled challenge</h3>
            <span class="score">0.6710</span>
            <div class="metric-list">
              <div><span>certificate</span><b>0.1833</b></div>
              <div><span>evidence</span><b>0.1833</b></div>
              <div><span>invalid JSON</span><b>0.0000</b></div>
            </div>
          </article>
          <article class="result-card">
            <h3>SFT combined challenge</h3>
            <span class="score">0.6753</span>
            <div class="metric-list">
              <div><span>certificate</span><b>0.2167</b></div>
              <div><span>evidence</span><b>0.2167</b></div>
              <div><span>invalid JSON</span><b>0.0000</b></div>
            </div>
          </article>
        </div>
        <div class="takeaways">
          <div class="takeaway"><b>Base failed JSON</b>Base Qwen2.5-0.5B could not emit usable repair plans.</div>
          <div class="takeaway"><b>SFT fixed action format</b>Challenge curriculum produced strict JSON repair-plan outputs.</div>
          <div class="takeaway"><b>Challenge recovered</b>Evidence grounding recovered from zero to nonzero on blinded variants.</div>
          <div class="takeaway"><b>Stop-loss prevented hype</b>1.5B was canceled by quality gate; no larger-model claim is made.</div>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Experimental proof</div>
            <h2>Experimental Results</h2>
          </div>
          <p>The plots are generated from extracted HF Jobs evidence and verifier summaries, not placeholders.</p>
        </div>
        <div class="plot-stack">
          $LOSS_PLOT
          $REWARD_PLOT
        </div>
      </div>
    </section>

    <section id="test">
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Rerunnable artifact</div>
            <h2>How to test this environment</h2>
          </div>
          <p>Judges can inspect the artifact at three levels: live interaction, raw API, or reproducible scripts.</p>
        </div>
        <div class="test-grid">
          <article class="test-card"><strong>1. Use the live demo</strong><p>Run the benchmark console above and watch trace, evidence, patch, hidden regressions, and certificate state update.</p></article>
          <article class="test-card"><strong>2. Call the API directly</strong><p>Use <code>/metadata</code>, <code>/reset</code>, <code>/step</code>, and <code>/state</code>. The raw metadata endpoint remains JSON.</p></article>
          <article class="test-card"><strong>3. Re-run evidence</strong><p>Use the notebook or repo scripts to run smoke checks, baselines, and training/eval scaffolds.</p></article>
        </div>
      </div>
    </section>

    <section id="audit">
      <div class="wrap">
        <div class="section-head">
          <div>
            <div class="eyebrow">Trust boundary</div>
            <h2>Why judges can trust this artifact</h2>
          </div>
          <p>The benchmark is designed to make weak repairs fail instead of making demos look easy.</p>
        </div>
        <div class="trust-grid">
          <article class="trust-card">
            <h3>Not just observability</h3>
            <p>Traces are the starting point, not the output. The agent must act: select evidence, diagnose, patch, run regressions, and certify through verifier gates.</p>
          </article>
          <article class="trust-card">
            <h3>Audit-grade design</h3>
            <ul class="trust-list">
              <li>deterministic verifier, no LLM judge</li>
              <li>hidden regressions and valid preservation checks</li>
              <li>candidate order shuffling and separated seeds</li>
              <li>challenge prompts and leakage audits</li>
              <li>overblocking and hardcoding penalties</li>
              <li>stop-loss discipline, no fake training claims</li>
            </ul>
          </article>
        </div>
      </div>
    </section>

    <section id="resources">
      <div class="wrap">
        <div class="section-head compact">
          <h2>Resources</h2>
          <p>Support material for a 3-minute audit. Kept compact so the environment and evidence stay central.</p>
        </div>
        <div class="resource-grid">
          <a class="resource-card" href="$GITHUB_ROOT"><strong>GitHub Repository</strong><span>source and scripts</span></a>
          <a class="resource-card" href="$GITHUB_ROOT#agent-blackbox-arena"><strong>README</strong><span>overview and run commands</span></a>
          <a class="resource-card" href="$GITHUB_ROOT/blob/main/BENCHMARK_SPEC.md"><strong>Benchmark Spec</strong><span>environment contract</span></a>
          <a class="resource-card" href="$GITHUB_ROOT/blob/main/notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb"><strong>Training Notebook</strong><span>rerun guide</span></a>
          <a class="resource-card" href="$GITHUB_ROOT/blob/main/TRAINING_RUN_LOG.md"><strong>Training Run Log</strong><span>jobs and stop-loss</span></a>
          <a class="resource-card" href="$GITHUB_ROOT/blob/main/SUBMISSION_EVIDENCE.md"><strong>Submission Evidence</strong><span>artifact manifest</span></a>
          <a class="resource-card" href="$GITHUB_ROOT/blob/main/FINAL_SUBMISSION_AUDIT.md"><strong>Final Audit</strong><span>claims and limits</span></a>
          <a class="resource-card" href="/metadata"><strong>API Metadata</strong><span>machine-readable JSON</span></a>
        </div>
        <p style="color: var(--muted); margin: 14px 0 0;">Video/blog: coming before final submission. No placeholder link is claimed.</p>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="disclaimer">
          <strong>Bounded certificate disclaimer</strong>
          The Agent Repair Certificate is bounded to synthetic incident families, visible traces, hidden regression variants, and the verification horizon. It is not a global safety proof.
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="wrap">
      Agent BlackBox Arena. Space: <a href="$SPACE_ROOT">$SPACE_ROOT</a>. Metadata: <a href="/metadata">/metadata</a>. API: <code>/reset</code>, <code>/step</code>, <code>/state</code>.
    </div>
  </footer>

  <script>
    const correctPatch = {
      require: ["fresh_context_check", "final_action_check"],
      forbid: ["act_on_stale_context"],
      preserve: ["valid_fresh_context_flow"],
      rationale: "The failed trace used expired retrieved context before final action."
    };

    const blockPatch = {
      require: ["fresh_context_check", "verify_before_irreversible_action", "role_tool_scope_match", "final_action_check"],
      forbid: ["act_on_stale_context", "irreversible_action_without_verification", "out_of_scope_tool_call"],
      preserve: [],
      rationale: "Block every risky behavior."
    };

    async function api(path, payload) {
      const options = payload === undefined
        ? {}
        : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) };
      const response = await fetch(path, options);
      if (!response.ok) throw new Error(`${path} returned ${response.status}`);
      return await response.json();
    }

    async function runDemoIncident() {
      document.getElementById("demo").scrollIntoView({ behavior: "smooth", block: "start" });
      return await resetIncident();
    }

    async function resetIncident() {
      setStatus("Resetting stale_retrieval demo incident...");
      const state = await api("/reset", { seed: 42, family: "stale_retrieval" });
      renderState(state);
      showDemoTab("trace");
      setStatus("Incident reset. Public trace is visible; hidden regression variants remain private.");
      return state;
    }

    async function step(action, payload = {}) {
      const result = await api("/step", { action, payload });
      renderState(result.observation);
      return result.observation;
    }

    async function runCorrectPath() {
      try {
        await resetIncident();
        const actions = [
          ["inspect_trace"],
          ["replay_incident"],
          ["select_evidence_spans", { evidence_spans: ["s2", "s4"] }],
          ["submit_root_cause", { root_cause: "missing_freshness_check" }],
          ["propose_repair_patch", { patch: correctPatch }],
          ["compile_regression_tests", { regression_tests: ["reg_stale_retrieval_block_failure", "reg_stale_retrieval_preserve_valid"] }],
          ["run_visible_replay"],
          ["run_hidden_regressions"],
          ["generate_repair_certificate"]
        ];
        for (const [action, payload] of actions) {
          setStatus(`Running verifier action: ${action}`);
          await step(action, payload || {});
        }
        showDemoTab("certificate");
        setStatus("Correct repair path completed. Certificate generated only after evidence, patch, replay, hidden regressions, and preservation passed.");
      } catch (error) {
        setStatus(`Demo error: ${error.message}`);
      }
    }

    async function runBlockEverything() {
      try {
        await resetIncident();
        const actions = [
          ["inspect_trace"],
          ["replay_incident"],
          ["select_evidence_spans", { evidence_spans: ["s2", "s4"] }],
          ["submit_root_cause", { root_cause: "missing_freshness_check" }],
          ["propose_repair_patch", { patch: blockPatch }],
          ["compile_regression_tests"],
          ["run_visible_replay"],
          ["run_hidden_regressions"],
          ["generate_repair_certificate"]
        ];
        for (const [action, payload] of actions) {
          setStatus(`Testing anti-overblocking gate: ${action}`);
          await step(action, payload || {});
        }
        showDemoTab("certificate");
        setStatus("Block-everything repair fails certificate gating because valid behavior preservation is part of the verifier.");
      } catch (error) {
        setStatus(`Demo error: ${error.message}`);
      }
    }

    async function showCertificate() {
      await runCorrectPath();
      document.getElementById("demo").scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function showDemoTab(name) {
      for (const panel of document.querySelectorAll(".panel")) panel.classList.remove("active");
      for (const tab of document.querySelectorAll(".tab")) tab.classList.remove("active");
      document.getElementById(`panel-${name}`).classList.add("active");
      const labels = { trace: 0, evidence: 1, patch: 2, certificate: 3 };
      document.querySelectorAll(".tab")[labels[name]].classList.add("active");
    }

    function setStatus(text) {
      document.getElementById("demo-status").textContent = text;
    }

    function renderState(state) {
      document.getElementById("demo-family").textContent = state.family || "unknown";
      document.getElementById("demo-score").textContent = Number(state.score || 0).toFixed(3);
      document.getElementById("demo-cert").textContent = state.repair_certificate ? "generated" : "not generated";
      document.getElementById("demo-hidden").textContent = state.hidden_regression_summary
        ? String(state.hidden_regression_summary.passed)
        : "not run";

      const trace = (state.public_trace_spans || [])
        .map(span => `${span.span_id} | ${span.span_type} | ${span.summary}`)
        .join("\\n");
      document.getElementById("demo-trace").textContent = trace || "No trace spans yet.";

      document.getElementById("demo-evidence").textContent = JSON.stringify({
        selected_evidence_spans: state.selected_evidence_spans,
        submitted_root_cause: state.submitted_root_cause,
        score_channels: state.score_channels
      }, null, 2);

      document.getElementById("demo-patch").textContent = JSON.stringify({
        submitted_patch: state.submitted_patch,
        visible_replay_report: state.visible_replay_report,
        hidden_regression_summary: state.hidden_regression_summary,
        audit_flags: state.audit_flags
      }, null, 2);

      document.getElementById("demo-certificate").textContent = JSON.stringify({
        repair_certificate: state.repair_certificate,
        certificate_status: state.repair_certificate ? "generated" : "blocked_or_not_requested",
        last_error: state.last_error,
        last_action_summary: state.last_action_summary,
        score: state.score
      }, null, 2);
    }
  </script>
</body>
</html>
"""
