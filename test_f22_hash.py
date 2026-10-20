# -*- coding: utf-8 -*-
"""F-22\uff1a\u524d\u7aef\u672c\u673a\u6a21\u5f0f\u53e3\u4ee4\u54c8\u5e0c\u94fe\u8def\u9a8c\u8bc1\uff08PBKDF2 + \u4e24\u79cd\u65e7\u683c\u5f0f\u517c\u5bb9\uff09\u3002

\u8986\u76d6\uff1a
  \u2460 \u6ce8\u518c \u2192 \u5f3a\u683c\u5f0f\uff08pbkdf2$ \u524d\u7f00\uff0c64 hex\uff09
  \u2461 \u6b63\u786e\u5bc6\u7801\u767b\u5f55\u6210\u529f
  \u2462 \u9519\u8bef\u5bc6\u7801\u767b\u5f55\u5931\u8d25
  \u2463 \u8001 SHA-256 \u683c\u5f0f\u8d26\u53f7 \u2192 \u767b\u5f55\u6210\u529f\u5e76\u81ea\u52a8\u5347\u7ea7\u4e3a PBKDF2
  \u2464 \u6781\u8001 djb2 \u683c\u5f0f\u8d26\u53f7\uff08\u5f53\u5e74\u7684\u6d4f\u89c8\u5668\u4e0d\u652f\u6301 crypto.subtle\uff09\u2192 \u4e5f\u80fd\u767b\u5f55\u5e76\u5347\u7ea7
  \u2465 \u91cd\u7f6e\u5bc6\u7801 \u2192 \u65b0\u5bc6\u7801\u53ef\u767b\u5f55\u3001\u65e7\u5bc6\u7801\u5931\u6548
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.abspath(__file__))
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  -> " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


HTML = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
m = re.search(r"function hashPw\(pw, salt, strong\) \{.*?\n  \}\n", HTML, re.S)
ck("\u627e\u5230 hashPw \u5b9e\u73b0", m is not None)
if not m:
    raise SystemExit(1)
FUNC = m.group(0)
ck("hashPw \u652f\u6301 djb2 \u517c\u5bb9\u6a21\u5f0f", "strong === 'djb2'" in FUNC)

JS = r"""
const crypto = require('crypto');
const { webcrypto } = crypto;
global.window = { crypto: webcrypto, TextEncoder: TextEncoder };
global.crypto = webcrypto;
global.TextEncoder = TextEncoder;
const STORE = {};
global.localStorage = {
  getItem: k => (k in STORE ? STORE[k] : null),
  setItem: (k, v) => { STORE[k] = v; },
  removeItem: k => { delete STORE[k]; }
};
const UK = 'kb_users_v1', SK = 'kb_sess_v1';
function lsGet(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
function users() { return lsGet(UK, {}); }
function sess() { return lsGet(SK, {}); }
function norm(u) { return String(u || '').trim().toLowerCase().replace(/[\s\u0000-\u001f"'\\<>]/g, '').slice(0, 40); }
function hex(n) { const a = new Uint8Array(n); webcrypto.getRandomValues(a); return Array.prototype.map.call(a, x => ('0' + x.toString(16)).slice(-2)).join(''); }
function sha256hex(str) { return webcrypto.subtle.digest('SHA-256', new TextEncoder().encode(str)).then(b => Array.prototype.map.call(new Uint8Array(b), x => ('0' + x.toString(16)).slice(-2)).join('')); }
function djb2(s) { var h = 5381; for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; return 'f' + h.toString(16); }

__FUNC__

const R = (obj, st) => ({ status: st || 200, body: obj });

async function api(path, body) {
  const b = body || {};
  if (path === '/api/register') {
    const name = norm(b.username);
    if (!name) return R({ ok: false, message: 'x' }, 400);
    if (!b.password || String(b.password).length < 6) return R({ ok: false, message: 'x' }, 400);
    const u = users();
    if (u[name]) return R({ ok: false, message: 'exists' }, 409);
    const salt = hex(8);
    const h = await hashPw(String(b.password), salt, true);
    u[name] = { username: name, pass: { salt: salt, hash: h }, profile: { name: name }, settings: {} };
    lsSet(UK, u);
    return R({ ok: true, hash: h, salt: salt });
  }
  if (path === '/api/login') {
    const name = norm(b.username);
    const u2 = users()[name];
    if (!u2) return R({ ok: false, message: 'no user' }, 401);
    const hStrong = await hashPw(String(b.password), u2.pass.salt, true);
    if (hStrong === u2.pass.hash) return R({ ok: true, mode: 'strong' });
    const hOld = await hashPw(String(b.password), u2.pass.salt, false);
    if (hOld === u2.pass.hash) {
      const st = users(); if (st[name] && st[name].pass) { st[name].pass.hash = hStrong; lsSet(UK, st); }
      return R({ ok: true, mode: 'legacy-upgraded' });
    }
    const hDj = await hashPw(String(b.password), u2.pass.salt, 'djb2');
    if (hDj === u2.pass.hash) {
      const st = users(); if (st[name] && st[name].pass) { st[name].pass.hash = hStrong; lsSet(UK, st); }
      return R({ ok: true, mode: 'djb2-upgraded' });
    }
    return R({ ok: false, message: 'bad pw' }, 401);
  }
  if (path === '/api/reset-password') {
    const name = norm(b.username);
    const u = users();
    const u2 = u[name];
    if (!u2) return R({ ok: false, message: 'no user' }, 404);
    const salt3 = hex(8);
    const h = await hashPw(String(b.newPassword), salt3, true);
    u2.pass = { salt: salt3, hash: h };
    lsSet(UK, u);
    return R({ ok: true, hash: h });
  }
  return R({ ok: false }, 404);
}

(async function () {
  const out = {};
  out.register = await api('/api/register', { username: 'f22user', password: 'Pw123456' });
  out.loginOk = await api('/api/login', { username: 'f22user', password: 'Pw123456' });
  out.loginBad = await api('/api/login', { username: 'f22user', password: 'WrongPw1' });

  const u = users();
  u['oldsha'] = { username: 'oldsha', pass: { salt: 'oldsalt1', hash: await sha256hex('oldsalt1|OldPw123') }, profile: { name: 'oldsha' }, settings: {} };
  u['olddjb'] = { username: 'olddjb', pass: { salt: 'oldsalt2', hash: djb2('oldsalt2|DjbPw456') }, profile: { name: 'olddjb' }, settings: {} };
  lsSet(UK, u);
  out.legacySha = await api('/api/login', { username: 'oldsha', password: 'OldPw123' });
  out.legacyShaHash = users()['oldsha'].pass.hash;
  out.legacyDjb = await api('/api/login', { username: 'olddjb', password: 'DjbPw456' });
  out.legacyDjbHash = users()['olddjb'].pass.hash;

  out.reset = await api('/api/reset-password', { username: 'f22user', newPassword: 'NewPw789' });
  out.loginNew = await api('/api/login', { username: 'f22user', password: 'NewPw789' });
  out.loginOldPw = await api('/api/login', { username: 'f22user', password: 'Pw123456' });
  console.log(JSON.stringify(out));
})().catch(e => { console.log(JSON.stringify({ error: String(e), stack: e.stack })); });
"""

js_path = os.path.join(ROOT, "_f22_hash.cjs")
io.open(js_path, "w", encoding="utf-8").write(JS.replace("__FUNC__", FUNC))
r = subprocess.run([r"D:\hclaw\node\node.exe", js_path], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=180)
try:
    os.remove(js_path)
except Exception:
    pass
if not (r.stdout or "").strip():
    print("  FAIL  \u8282\u70b9\u6267\u884c\u65e0\u8f93\u51fa: %s" % (r.stderr or "")[:300])
    raise SystemExit(1)
d = json.loads(r.stdout.strip().splitlines()[-1])


def bk(x):
    return (x or {}).get("body", {}).get("ok") is True


print("\n=== \u2460 \u6ce8\u518c\u5199\u5165\u5f3a\u683c\u5f0f ===")
h = (d.get("register") or {}).get("body", {}).get("hash", "")
ck("\u6ce8\u518c\u540e\u54c8\u5e0c\u4e3a pbkdf2$ \u5f00\u5934", h.startswith("pbkdf2$"), h[:20])
ck("pbkdf2 \u957f\u5ea6\u5408\u7406\uff0864 hex\uff09", re.fullmatch(r"pbkdf2\$[a-f0-9]{64}", h) is not None, h[:30])

print("\n=== \u2461\u2462 \u767b\u5f55 ===")
ck("\u6b63\u786e\u5bc6\u7801\u767b\u5f55\u6210\u529f", bk(d.get("loginOk")), d.get("loginOk"))
ck("\u9519\u8bef\u5bc6\u7801\u767b\u5f55\u5931\u8d25", (d.get("loginBad") or {}).get("status") == 401, d.get("loginBad"))

print("\n=== \u2463 \u8001 SHA-256 \u683c\u5f0f\u8d26\u53f7 ===")
ck("\u8001 SHA-256 \u8d26\u53f7\u767b\u5f55\u6210\u529f", bk(d.get("legacySha")), d.get("legacySha"))
ck("\u767b\u5f55\u540e\u81ea\u52a8\u5347\u7ea7\u4e3a PBKDF2", str(d.get("legacyShaHash", "")).startswith("pbkdf2$"), str(d.get("legacyShaHash", ""))[:20])

print("\n=== \u2464 \u6781\u8001 djb2 \u683c\u5f0f\u8d26\u53f7 ===")
ck("\u6781\u8001 djb2 \u8d26\u53f7\u4e5f\u80fd\u767b\u5f55\uff08\u4e0d\u80fd\u6c38\u8fdc\u767b\u4e0d\u4e0a\uff09", bk(d.get("legacyDjb")), d.get("legacyDjb"))
ck("djb2 \u767b\u5f55\u540e\u5347\u7ea7\u4e3a PBKDF2", str(d.get("legacyDjbHash", "")).startswith("pbkdf2$"), str(d.get("legacyDjbHash", ""))[:20])

print("\n=== \u2465 \u91cd\u7f6e\u5bc6\u7801 ===")
ck("\u91cd\u7f6e\u6210\u529f", bk(d.get("reset")), d.get("reset"))
ck("\u65b0\u5bc6\u7801\u53ef\u767b\u5f55", bk(d.get("loginNew")), d.get("loginNew"))
ck("\u65e7\u5bc6\u7801\u91cd\u7f6e\u540e\u5931\u6548", (d.get("loginOldPw") or {}).get("status") == 401, d.get("loginOldPw"))

print("\n" + ("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u5931\u8d25"))
sys.exit(0 if OK[0] else 1)
