# -*- coding: utf-8 -*-
"""v44\uff1a\u98ce\u9669\u8d8b\u52bf\u56fe\u7684\u79bb\u7ebf\u6e32\u67d3\u9a8c\u8bc1\u3002

\u76ee\u6807\uff1a\u4e0d\u5f00\u6d4f\u89c8\u5668\u5c31\u80fd\u786e\u8ba4\u300c\u98ce\u9669\u8d8b\u52bf\u56fe\u6709\u6570\u636e\u300d\u3002
  \u2460 \u62bd\u51fa Chart.lines / riskSeries / renderRiskTrend \u7684\u771f\u5b9e\u4ee3\u7801\uff08\u4e0d\u4f2a\u9020\uff09
  \u2461 \u9971\u5408\u5047\u6570\u636e\uff1a14 \u5929\u91cc\u6709\u6f0f\u670d\u3001\u6709\u8840\u538b\u5f02\u5e38
  \u2462 \u68c0\u67e5\u8f93\u51fa SVG\uff1a
       - polyline \u7684 y \u5750\u6807**\u4e0d\u80fd\u5168\u90e8\u8d34\u5728\u5e95\u90e8**\uff08\u65e7\u7248\u7684 Y \u8f74 0~100 \u5c31\u662f\u8fd9\u4e2a\u75c5\uff09
       - \u5206\u6570\u975e 0
       - \u7a7a\u6001\u65f6\u7684\u63d0\u793a\u6587\u6848\u51fa\u73b0
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  -> " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


html = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# \u62bd\u51fa\u771f\u5b9e\u4ee3\u7801\u7247\u6bb5
m_lines = re.search(r"  function lines\(labels, series, opts\) \{.*?\n  \}\n", html, re.S)
m_series = re.search(r"  function riskSeries\(records, health, days\) \{.*?\n  \}\n", html, re.S)
m_fmt = re.search(r"  function fmtDate\(d\) \{.*?\n  \}", html, re.S)
m_bp = re.search(r"  function bpStatus\(sys, dia\) \{.*?\n  \}", html, re.S)
m_glu = re.search(r"  function gluStatus\(val, meal\) \{.*?\n  \}", html, re.S)
m_health = re.search(r"EMC\.HEALTH = \{[^;]*\}", html, re.S)
for nm, mm in [("lines", m_lines), ("riskSeries", m_series), ("fmtDate", m_fmt),
               ("bpStatus", m_bp), ("gluStatus", m_glu), ("HEALTH", m_health)]:
    ck("\u627e\u5230 %s \u5b9e\u73b0" % nm, mm is not None)
if not all([m_lines, m_series, m_fmt, m_bp, m_glu, m_health]):
    sys.exit(1)

# renderRiskTrend \u7684\u8f93\u51fa\u903b\u8f91\uff08\u91cd\u5199\u4e00\u4efd\u7b49\u4ef7\u5b9e\u73b0\uff0c\u4fdd\u6301\u4e0e\u524d\u8005\u4e00\u81f4\uff09
m_rt = re.search(r"  function renderRiskTrend\(\) \{.*?\n  \}\n", html, re.S)
ck("\u627e\u5230 renderRiskTrend", m_rt is not None)

# \u4ece renderRiskTrend \u91cc\u53d6\u51fa\u56fe\u8868\u8c03\u7528\u4e0e\u7a7a\u6001\u63d0\u793a\u7684\u5b9e\u9645\u53c2\u6570
rt = m_rt.group(0)
m_chart = re.search(r"EMC\.Chart\.lines\(.*?yMax: Math\.max\(3, maxScore\)\s*\}\)", rt, re.S)
ck("renderRiskTrend \u91cc\u6709 Chart.lines \u8c03\u7528", m_chart is not None)
m_tip = re.search(r"if \(!hasAny\) \{", rt)
ck("renderRiskTrend \u6709\u7a7a\u6001\u5206\u652f", m_tip is not None)

JS = """
var EMC = {};
function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }
%s
%s
%s
%s
%s
%s
var EMC2 = { HEALTH: %s };
EMC.Chart = { lines: lines };

function riskTrendSvg(records, health) {
  var series = riskSeries(records, health, 14);
  var labels = series.map(function (d) { return d.label; });
  var data = series.map(function (d) { return d.score; });
  var maxScore = 0;
  series.forEach(function (d) { if (d.score > maxScore) maxScore = d.score; });
  var svg = lines(labels, [{ name: 'x', data: data, color: '#B4402F' }], { height: 220, yMax: Math.max(3, maxScore) });
  return { svg: svg, scores: data, max: maxScore };
}

var out = {};

// \u2461 \u9971\u5408\u6570\u636e\uff1a\u8fd1 7 \u5929\u6709\u6f0f\u670d\uff0c\u6709\u4e24\u5929\u8840\u538b\u5f02\u5e38
var recs = [], hs = [];
var today = new Date();
for (var i = 0; i < 14; i++) {
  var d = new Date(today.getTime() - i * 86400000);
  var key = fmtDate(d);
  if (i < 7) {
    recs.push({ date: key, mid: 'm1', slot: 'morning', status: 'missed' });
    recs.push({ date: key, mid: 'm1', slot: 'evening', status: 'taken' });
  }
  if (i === 1 || i === 3) {
    hs.push({ type: 'bp', date: key, sys: 165, dia: 102 });
  }
}
out.data = riskTrendSvg(recs, hs);
out.hasAny = !!(recs.length || hs.length);
out.recent = out.data.scores.filter(function (x) { return x > 0; }).length;

// \u2462 \u68c0\u67e5 SVG\uff1a\u5206\u6570\u975e 0\uff0cy \u5750\u6807\u4e0d\u5168\u8d34\u5e95
var pts = (out.data.svg.match(/points="([^"]+)"/) || [])[1] || '';
var ys = pts.split(/\\s+/).map(function (p) { return Number(String(p).split(',')[1]); });
var finite = ys.filter(function (y) { return isFinite(y); });
out.ys = finite;
out.minY = finite.length ? Math.min.apply(null, finite) : null;
out.maxY = finite.length ? Math.max.apply(null, finite) : null;
out.maxScore = out.data.max;

// \u7a7a\u6001\uff1a\u65e0\u4efb\u4f55\u6570\u636e
out.empty = riskTrendSvg([], []);
out.emptyMax = out.empty.max;
console.log(JSON.stringify(out));
""" % (m_fmt.group(0), m_bp.group(0), m_glu.group(0), m_health.group(0),
       m_lines.group(0), m_series.group(0), m_health.group(0))

p = os.path.join(ROOT, "_risktrend_test.js")
io.open(p, "w", encoding="utf-8").write(JS)
r = subprocess.run([r"D:\hclaw\node\node.exe", p], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=60)
try:
    os.remove(p)
except Exception:
    pass
if not (r.stdout or "").strip():
    print("node \u65e0\u8f93\u51fa: %s" % (r.stderr or "")[:400])
    sys.exit(1)
d = json.loads(r.stdout.strip().splitlines()[-1])

print("\n=== \u2461 \u6570\u636e\u94fe\u8def ===")
ck("\u6709\u975e\u96f6\u5206\u6570", d["maxScore"] >= 1, d["maxScore"])
ck("\u6709\u6f0f\u670d + \u8840\u538b\u5f02\u5e38\u65f6\u6709\u591a\u5929\u975e\u96f6", d["recent"] >= 2, d["recent"])
ck("\u65e0\u6570\u636e\u65f6\u6700\u5927\u5206\u6570\u4e3a 0", d["emptyMax"] == 0, d["emptyMax"])

print("\n=== \u2462 Y \u8f74\u91cf\u7a0b\uff08\u65e7\u7248\u7684\u75c5\uff09===")
ck("SVG \u6709 polyline", bool(d["ys"]), len(d["ys"]))
ck("y \u5750\u6807\u6709\u591a\u4e2a\u4e0d\u540c\u503c\uff08\u66f2\u7ebf\u6ca1\u88ab\u538b\u6210\u4e00\u6761\u76f4\u7ebf\uff09",
   len(set(d["ys"])) >= 2, sorted(set(d["ys"])))
ck("\u66f2\u7ebf\u6ca1\u6709\u5168\u90e8\u8d34\u5728\u5e95\u90e8\uff08\u65e7\u7248\u5c31\u662f\u8fd9\u4e2a\u75c5\uff09",
   d["minY"] is not None and d["maxY"] is not None and (d["maxY"] - d["minY"]) > 30,
   "minY=%s maxY=%s" % (d["minY"], d["maxY"]))

print("\n" + ("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u5931\u8d25"))
sys.exit(0 if OK[0] else 1)
