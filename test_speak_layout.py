# -*- coding: utf-8 -*-
"""v44\uff1a\u5206\u6bb5\u6717\u8bfb\u6309\u94ae\u7684\u4f4d\u7f6e\u4e0e\u6587\u5b57\u9a8c\u8bc1\uff08\u79bb\u7ebf\uff0c\u62bd\u771f\u5b9e\u4ee3\u7801\uff09\u3002

\u9a8c\u8bc1\uff1a
  \u2460 \u6bcf\u4e2a\u81ea\u7136\u6bb5\u524d\u9762\u90fd\u6709\u4e00\u4e2a\u300c\U0001f4e2\u8bfb\u300d\u6309\u94ae\uff08\u4e0d\u518d\u5806\u5728\u672b\u5c3e\uff09
  \u2461 \u6309\u94ae\u6587\u5b57\u53ea\u662f\u300c\U0001f4e2\u8bfb\u300d\uff08\u4e0d\u518d\u662f\u300c\U0001f50a \u6717\u8bfb\u8fd9\u4e00\u6bb5\u300d\uff09
  \u2462 \u6309\u94ae\u4e0e\u6bb5\u843d\u6587\u5b57\u4ea4\u9519\u6392\u5217\uff08DOM \u987a\u5e8f\uff09
  \u2463 \u6bb5\u843d\u6587\u5b57\u4fdd\u7559\u539f\u6587\uff08\u4e0d\u4f1a\u88ab\u622a\u65ad\u6216\u4e22\u5931\uff09
  \u2464 \u8d85\u8fc7 6 \u6bb5\u65f6\uff1a\u524d 6 \u6bb5\u6709\u6309\u94ae\uff0c\u540e\u9762\u7684\u6bb5\u843d\u53ea\u663e\u793a\u6587\u5b57
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

m_fn = re.search(r"  function renderParaWithSpeak\(body, text\) \{.*?\n  \}\n", html, re.S)
ck("\u627e\u5230 renderParaWithSpeak", m_fn is not None)
if not m_fn:
    sys.exit(1)
fn = m_fn.group(0)

m_push = re.search(r"if \(role !== 'user' && !\(meta && meta\.thinking\)\) renderParaWithSpeak\(body, text\);", html)
ck("pushMsg \u5df2\u6539\u7528\u65b0\u6e32\u67d3", m_push is not None)
ck("\u65e7\u51fd\u6570 appendParaSpeak \u5df2\u79fb\u9664", "appendParaSpeak" not in html)

# \u6784\u9020\u4e00\u4e2a\u6700\u5c0f DOM \u6a21\u62df\uff08\u53ea\u9700\u8981 createElement/appendChild/textContent/className\uff09
JS = """
var document = {
  _mk: function (tag) {
    return {
      tagName: tag, children: [], _text: '', className: '',
      set textContent(v) { this._text = String(v); this.children = []; },
      get textContent() { return this._text; },
      set innerHTML(v) { this._html = String(v); this.children = []; },
      get innerHTML() { return this._html || ''; },
      setAttribute: function (k, v) { this['_' + k] = v; },
      appendChild: function (c) { this.children.push(c); return c; },
      addEventListener: function () {}
    };
  },
  createElement: function (tag) { return this._mk(tag); }
};
var V = { splitSegments: function (s) { return [s]; }, humanizeForTts: function (s) { return s; } };
%s
var out = {};
function run(text) {
  var body = document.createElement('div');
  renderParaWithSpeak(body, text);
  return body;
}
var b1 = run('\\u7b2c\\u4e00\\u6bb5\\u8bdd\\u3002\\n\\u7b2c\\u4e8c\\u6bb5\\u8bdd\\u3002');
out.blocks1 = b1.children.length;
out.btnText = b1.children.map(function (blk) {
  return (blk.children.filter(function (c) { return c.tagName === 'button'; })[0] || {}).textContent;
}).filter(Boolean);
out.order = b1.children.map(function (blk) {
  return blk.children.map(function (c) { return c.tagName; }).join(',');
});
out.texts = b1.children.map(function (blk) {
  return (blk.children.filter(function (c) { return c.tagName === 'span'; })[0] || {}).textContent;
});

var b2 = run('\\u53ea\\u6709\\u4e00\\u6bb5');
out.blocks2 = b2.children.length;
out.btns2 = b2.children.map(function (blk) {
  return blk.children.filter(function (c) { return c.tagName === 'button'; }).length;
});

var many = [];
for (var i = 1; i <= 8; i++) many.push('\\u7b2c' + i + '\\u6bb5');
var b3 = run(many.join('\\n'));
out.blocks3 = b3.children.length;
out.btns3 = b3.children.map(function (blk) {
  return blk.children.filter(function (c) { return c.tagName === 'button'; }).length;
}).reduce(function (a, b) { return a + b; }, 0);

console.log(JSON.stringify(out));
""" % fn

p = os.path.join(ROOT, "_speak_test.js")
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

print("\n=== \u2460\u2461 \u6309\u94ae\u6570\u91cf\u4e0e\u6587\u5b57 ===")
ck("2 \u4e2a\u6bb5\u843d \u2192 4 \u4e2a\u5143\u7d20\uff08\u6309\u94ae+\u6587\u5b57\uff09", d["blocks1"] == 2, d["blocks1"])
ck("\u6309\u94ae\u6587\u5b57\u53ea\u662f\u300c\\ud83d\\udce2\\u8bfb\u300d", all(x == "\U0001f4e2\u8bfb" for x in d["btnText"]), d["btnText"])
ck("\u6309\u94ae\u6587\u5b57\u4e0d\u542b\u300c\u6717\u8bfb\u8fd9\u4e00\u6bb5\u300d",
   all("\u6717\u8bfb\u8fd9\u4e00\u6bb5" not in x for x in d["btnText"]), d["btnText"])

print("\n=== \u2462 \u987a\u5e8f\uff1a\u6309\u94ae\u5728\u6bb5\u843d\u6587\u5b57\u524d\u9762 ===")
ck("\u4ea4\u9519\u6392\u5217 button/span/button/span", d["order"] == ["button,span", "button,span"], d["order"])

print("\n=== \u2463 \u6587\u5b57\u4fdd\u7559 ===")
ck("\u4e24\u6bb5\u6587\u5b57\u90fd\u5728", len([x for x in d["texts"] if x and x != "\U0001f4e2\u8bfb"]) == 2, d["texts"])

print("\n=== \u2464 \u5355\u6bb5\u4e0e\u8d85 6 \u6bb5 ===")
ck("\u5355\u6bb5 \u2192 2 \u4e2a\u5143\u7d20", d["blocks2"] == 1, d["blocks2"])
ck("8 \u6bb5 \u2192 16 \u4e2a\u5143\u7d20", d["blocks3"] == 8, d["blocks3"])
ck("8 \u6bb5\u53ea\u7ed9\u524d 6 \u6bb5\u6309\u94ae", d["btns3"] == 6, d["btns3"])

print("\n" + ("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u5931\u8d25"))
sys.exit(0 if OK[0] else 1)
