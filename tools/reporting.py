"""Generate a self-contained, printable HTML research report."""
from __future__ import annotations

from html import escape


def _list(items: list) -> str:
    if not items:
        return "<p>No data available.</p>"
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def build_html_report(report: dict) -> str:
    product = report.get("product_analysis", {})
    market = report.get("market_research", {})
    profit = report.get("profitability", {})
    evidence = market.get("evidence", {})
    competitors = market.get("competitive_analysis", {}).get("competitors", [])
    actions = market.get("action_items", [])

    source_rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('title', '')))}</td>"
        f"<td>{escape(str(item.get('price_egp') or 'Not shown'))}</td>"
        f"<td>{int(float(item.get('confidence', 0)) * 100)}%</td>"
        f"<td><a href=\"{escape(item.get('url', ''), quote=True)}\">Open source</a></td>"
        "</tr>"
        for item in evidence.get("price_sources", [])
    ) or '<tr><td colspan="4">No price sources found.</td></tr>'

    competitor_rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('name', 'Unknown')))}</td>"
        f"<td>{escape(str(item.get('positioning', '')))}</td>"
        f"<td><a href=\"{escape(item.get('evidence_url', ''), quote=True)}\">Evidence</a></td>"
        "</tr>"
        for item in competitors
    ) or '<tr><td colspan="3">No competitors identified.</td></tr>'

    action_rows = "".join(
        f"<li><strong>{escape(str(item.get('priority', '')).title())}:</strong> "
        f"{escape(str(item.get('action', '')))} — {escape(str(item.get('impact', '')))}</li>"
        for item in actions
    ) or "<li>No action items generated.</li>"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Product Research Report</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1050px;margin:36px auto;color:#172033;line-height:1.5}}
h1,h2{{color:#132a55}} .card{{border:1px solid #dbe2ef;border-radius:10px;padding:18px;margin:14px 0}}
.metrics{{display:flex;gap:12px;flex-wrap:wrap}} .metric{{background:#f4f7fb;padding:12px 18px;border-radius:8px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}
th{{background:#f4f7fb}} .verdict{{font-size:20px;font-weight:bold;color:#0b6b3a}} small{{color:#667085}}
@media print{{body{{margin:12mm}} a{{color:inherit}}}}
</style></head><body>
<h1>Egypt Product Research Report</h1>
<small>Generated {escape(str(report.get('metadata', {}).get('timestamp', '')))}</small>
<div class="card"><h2>{escape(str(product.get('product_name', 'Unknown product')))}</h2>
<p>{escape(str(product.get('category', 'Unknown category')))}</p>
{_list(product.get('key_features', []))}</div>
<div class="card"><h2>Executive summary</h2><p>{escape(str(market.get('executive_summary', '')))}</p>
<p class="verdict">{escape(str(market.get('decision', {}).get('verdict', 'Needs more evidence')))}</p>
<p>{escape(str(market.get('decision', {}).get('rationale', '')))}</p></div>
<div class="card"><h2>Profitability</h2><div class="metrics">
<div class="metric">Net profit: <strong>{profit.get('net_profit', 0):,.2f} EGP</strong></div>
<div class="metric">Margin: <strong>{profit.get('profit_margin_percent', 0):.2f}%</strong></div>
<div class="metric">ROI: <strong>{profit.get('roi_percent', 0):.2f}%</strong></div>
<div class="metric">Target price: <strong>{profit.get('recommended_price') or 'N/A'} EGP</strong></div>
</div></div>
<div class="card"><h2>Verified price evidence</h2><table><thead><tr><th>Source</th><th>Price (EGP)</th><th>Confidence</th><th>Link</th></tr></thead><tbody>{source_rows}</tbody></table></div>
<div class="card"><h2>Competitor comparison</h2><table><thead><tr><th>Competitor</th><th>Positioning</th><th>Source</th></tr></thead><tbody>{competitor_rows}</tbody></table></div>
<div class="card"><h2>Recommended actions</h2><ol>{action_rows}</ol></div>
</body></html>"""
