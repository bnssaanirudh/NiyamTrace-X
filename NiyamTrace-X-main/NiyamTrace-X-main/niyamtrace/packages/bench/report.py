"""
packages/bench/report.py — NiyamTrace-Bench report generator (Week 8).

Produces:
  - benchmark_report.json — machine-readable full results
  - benchmark_report.html — human-readable HTML report in Hilden & Kaira aesthetic

Design: Deterministic, offline. No external HTTP calls. Uses only stdlib.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.bench.runner import BenchmarkResult

_DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "benchmark"


class BenchmarkReport:
    """
    Generates JSON + HTML reports from a BenchmarkResult.

    Args:
        result: The BenchmarkResult from BenchmarkRunner.run().
        output_dir: Directory to write reports into.
    """

    def __init__(self, result: "BenchmarkResult", output_dir: Path | str | None = None) -> None:
        self.result = result
        self.output_dir = Path(output_dir or _DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, filename: str = "benchmark_report.json") -> Path:
        """Write the full results as JSON."""
        path = self.output_dir / filename
        path.write_text(
            json.dumps(self.result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def write_html(self, filename: str = "benchmark_report.html") -> Path:
        """Write a styled HTML report in the Hilden & Kaira aesthetic."""
        path = self.output_dir / filename
        path.write_text(self._render_html(), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # HTML rendering
    # ------------------------------------------------------------------

    def _render_html(self) -> str:
        s = self.result.summary
        d = self.result.to_dict()

        accuracy_pct = f"{s.accuracy * 100:.1f}"
        accuracy_class = "metric-pass" if s.accuracy >= 0.80 else "metric-fail"

        verdict_rows = "".join(
            self._scenario_row(sc) for sc in self.result.scenarios
        )

        lang_rows = "".join(
            f"""<tr>
              <td>{lang}</td>
              <td>{acc * 100:.1f}%</td>
              <td class="bar-cell"><div class="bar" style="width:{acc*100:.1f}%"></div></td>
            </tr>"""
            for lang, acc in sorted(s.accuracy_by_language.items())
        )

        tag_rows = "".join(
            f"""<tr>
              <td><span class="tag">{tag}</span></td>
              <td>{acc * 100:.1f}%</td>
            </tr>"""
            for tag, acc in sorted(s.accuracy_by_tag.items(), key=lambda x: -x[1])
        )

        verdict_breakdown = ""
        for v, data in d["summary"]["verdict_breakdown"].items():
            pct = (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0
            verdict_breakdown += f"""
            <div class="stat-tile">
              <div class="stat-label">{v}</div>
              <div class="stat-value">{data['correct']}<span class="stat-denom">/{data['total']}</span></div>
              <div class="stat-sublabel">{pct:.1f}% correct</div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NiyamTrace-Bench Report · {self.result.run_id}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    /* ── Design system: Hilden & Kaira ─────────────────────────── */
    :root {{
      --bg:        #F2EFE8;
      --surface:   #FAFAF7;
      --ink:       #111111;
      --muted:     #5A5A5A;
      --border:    #D8D4CC;
      --lime:      #C8E64A;
      --lime-dark: #9CB230;
      --allow-bg:  #D6EDDF; --allow-ink: #1A4731;
      --block-bg:  #F5DADA; --block-ink: #7A1A1A;
      --esc-bg:    #F5EDD6; --esc-ink:   #5C3D00;
      --error-bg:  #EBEBEB; --error-ink: #444444;
      --radius:    3px;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 16px; }}
    body {{
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--ink);
      min-height: 100vh;
    }}

    /* ── Layout ─────────────────────────────────────────────────── */
    .page-header {{
      background: var(--ink);
      color: var(--lime);
      padding: 48px 64px 40px;
    }}
    .page-header h1 {{
      font-size: clamp(2rem, 5vw, 4rem);
      font-weight: 700;
      letter-spacing: -0.03em;
      line-height: 1;
      margin-bottom: 8px;
    }}
    .page-header .meta {{
      font-size: 0.8rem;
      font-weight: 400;
      color: rgba(200,230,74,0.55);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .content {{ max-width: 1280px; margin: 0 auto; padding: 56px 64px 120px; }}

    /* ── Hero stat row ──────────────────────────────────────────── */
    .hero-stats {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr 1fr;
      gap: 1px;
      background: var(--border);
      border: 1px solid var(--border);
      margin-bottom: 64px;
    }}
    .stat-tile {{
      background: var(--surface);
      padding: 32px 28px;
    }}
    .stat-tile:first-child {{ background: var(--lime); }}
    .stat-label {{
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 12px;
    }}
    .stat-tile:first-child .stat-label {{ color: rgba(0,0,0,0.5); }}
    .stat-value {{
      font-size: clamp(2.5rem, 5vw, 4rem);
      font-weight: 700;
      letter-spacing: -0.04em;
      line-height: 1;
      color: var(--ink);
    }}
    .stat-denom {{ font-size: 0.4em; font-weight: 400; color: var(--muted); }}
    .stat-sublabel {{ font-size: 0.75rem; color: var(--muted); margin-top: 6px; }}
    .metric-pass {{ color: #1A4731; }}
    .metric-fail {{ color: #7A1A1A; }}

    /* ── Section ────────────────────────────────────────────────── */
    section {{ margin-bottom: 64px; }}
    .section-label {{
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 24px;
    }}
    h2 {{
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-bottom: 24px;
    }}

    /* ── Verdict breakdown tiles ─────────────────────────────────── */
    .verdict-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1px;
      background: var(--border);
      border: 1px solid var(--border);
    }}
    .verdict-grid .stat-tile:nth-child(1) {{ background: var(--allow-bg); }}
    .verdict-grid .stat-tile:nth-child(1) .stat-label {{ color: var(--allow-ink); }}
    .verdict-grid .stat-tile:nth-child(1) .stat-value {{ color: var(--allow-ink); }}
    .verdict-grid .stat-tile:nth-child(2) {{ background: var(--block-bg); }}
    .verdict-grid .stat-tile:nth-child(2) .stat-label {{ color: var(--block-ink); }}
    .verdict-grid .stat-tile:nth-child(2) .stat-value {{ color: var(--block-ink); }}
    .verdict-grid .stat-tile:nth-child(3) {{ background: var(--esc-bg); }}
    .verdict-grid .stat-tile:nth-child(3) .stat-label {{ color: var(--esc-ink); }}
    .verdict-grid .stat-tile:nth-child(3) .stat-value {{ color: var(--esc-ink); }}

    /* ── Language bars ─────────────────────────────────────────── */
    .lang-table {{ width: 100%; border-collapse: collapse; }}
    .lang-table td {{ padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 0.875rem; }}
    .lang-table td:first-child {{ font-family: 'Courier New', monospace; font-size: 0.8rem; color: var(--muted); width: 140px; }}
    .lang-table td:nth-child(2) {{ width: 60px; font-weight: 600; }}
    .bar-cell {{ padding-right: 0 !important; }}
    .bar {{
      height: 8px;
      background: var(--lime);
      border-radius: 2px;
      min-width: 2px;
      transition: width 0.4s ease;
    }}

    /* ── Tag pills ──────────────────────────────────────────────── */
    .tag {{
      display: inline-block;
      padding: 2px 8px;
      background: var(--ink);
      color: var(--lime);
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      border-radius: var(--radius);
    }}
    .tag-table {{ width: 100%; border-collapse: collapse; }}
    .tag-table td {{ padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.875rem; }}
    .tag-table td:last-child {{ width: 80px; font-weight: 600; text-align: right; }}

    /* ── Scenario table ─────────────────────────────────────────── */
    .scenario-table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
    .scenario-table th {{
      text-align: left;
      padding: 8px 12px;
      background: var(--ink);
      color: var(--lime);
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }}
    .scenario-table td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    .scenario-table tr:hover td {{ background: rgba(200,230,74,0.08); }}
    .scenario-table .id {{ font-family: monospace; color: var(--muted); font-size: 0.75rem; white-space: nowrap; }}
    .scenario-table .desc {{ max-width: 340px; line-height: 1.4; color: var(--ink); }}
    .scenario-table .lang {{ font-family: monospace; font-size: 0.7rem; color: var(--muted); }}
    .row-pass td {{ background: rgba(214,237,223,0.25); }}
    .row-fail td {{ background: rgba(245,218,218,0.25); }}
    .row-error td {{ background: rgba(245,237,214,0.25); }}

    /* ── Verdict badges ─────────────────────────────────────────── */
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: var(--radius);
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .badge-ALLOW    {{ background: var(--allow-bg); color: var(--allow-ink); }}
    .badge-BLOCK    {{ background: var(--block-bg); color: var(--block-ink); }}
    .badge-ESCALATE {{ background: var(--esc-bg);   color: var(--esc-ink);   }}
    .badge-ERROR    {{ background: var(--error-bg); color: var(--error-ink); }}
    .badge-UNKNOWN  {{ background: var(--error-bg); color: var(--error-ink); }}

    /* ── Pass/fail icon ─────────────────────────────────────────── */
    .icon-pass {{ color: #1A4731; font-weight: 700; }}
    .icon-fail {{ color: #7A1A1A; font-weight: 700; }}
    .icon-error {{ color: #5C3D00; font-weight: 700; }}

    /* ── Footer ─────────────────────────────────────────────────── */
    footer {{
      background: var(--ink);
      color: rgba(255,255,255,0.3);
      padding: 24px 64px;
      font-size: 0.75rem;
    }}
    footer strong {{ color: var(--lime); }}
  </style>
</head>
<body>

<header class="page-header">
  <h1>NiyamTrace-Bench</h1>
  <div class="meta">Run · {self.result.run_id} &nbsp;·&nbsp; {self.result.timestamp[:19].replace("T"," ")} UTC</div>
</header>

<main class="content">

  <!-- Hero stats -->
  <div class="hero-stats">
    <div class="stat-tile">
      <div class="stat-label">Overall Accuracy</div>
      <div class="stat-value {accuracy_class}">{accuracy_pct}<span class="stat-denom">%</span></div>
      <div class="stat-sublabel">{s.passed} / {s.total} scenarios correct</div>
    </div>
    <div class="stat-tile">
      <div class="stat-label">Passed</div>
      <div class="stat-value">{s.passed}</div>
      <div class="stat-sublabel">of {s.total} scenarios</div>
    </div>
    <div class="stat-tile">
      <div class="stat-label">Failed</div>
      <div class="stat-value">{s.failed}</div>
      <div class="stat-sublabel">wrong verdict</div>
    </div>
    <div class="stat-tile">
      <div class="stat-label">Avg Latency</div>
      <div class="stat-value">{s.avg_latency_ms:.1f}<span class="stat-denom">ms</span></div>
      <div class="stat-sublabel">per scenario</div>
    </div>
  </div>

  <!-- Verdict breakdown -->
  <section>
    <div class="section-label">Verdict Breakdown</div>
    <div class="verdict-grid">
      {verdict_breakdown}
    </div>
  </section>

  <!-- Language accuracy -->
  <section>
    <div class="section-label">Accuracy by Language</div>
    <table class="lang-table">
      <tbody>{lang_rows}</tbody>
    </table>
  </section>

  <!-- Tag accuracy -->
  <section>
    <div class="section-label">Accuracy by Tag</div>
    <table class="tag-table">
      <tbody>{tag_rows}</tbody>
    </table>
  </section>

  <!-- Scenario table -->
  <section>
    <div class="section-label">All Scenarios</div>
    <table class="scenario-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Description</th>
          <th>Lang</th>
          <th>Expected</th>
          <th>Actual</th>
          <th>Result</th>
          <th>ms</th>
        </tr>
      </thead>
      <tbody>
        {verdict_rows}
      </tbody>
    </table>
  </section>

</main>

<footer>
  <strong>NiyamTrace-Bench</strong> · Deterministic · Offline · No LLMs ·
  Threshold: 80% accuracy · Run ID: {self.result.run_id}
</footer>

</body>
</html>"""

    def _scenario_row(self, sc) -> str:
        icon = (
            '<span class="icon-pass">✓</span>'
            if sc.passed
            else (
                '<span class="icon-error">!</span>'
                if sc.error
                else '<span class="icon-fail">✗</span>'
            )
        )
        row_class = "row-pass" if sc.passed else ("row-error" if sc.error else "row-fail")
        exp = sc.expected_verdict
        act = sc.actual_verdict
        return f"""<tr class="{row_class}">
          <td class="id">{sc.scenario_id}</td>
          <td class="desc">{sc.description}</td>
          <td class="lang">{sc.language}</td>
          <td><span class="badge badge-{exp}">{exp}</span></td>
          <td><span class="badge badge-{act}">{act}</span></td>
          <td style="text-align:center">{icon}</td>
          <td style="text-align:right;font-variant-numeric:tabular-nums">{sc.latency_ms:.1f}</td>
        </tr>"""
