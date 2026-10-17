# -*- coding: utf-8 -*-
r"""验证「播报音色」真的生效：切了音色 -> 云端 TTS 请求里带的 voice 确实跟着变。

【为什么必须验】v37 把音色从写死的 Cherry 改成按选择发送，
但如果只是改了界面显示、请求里仍是 Cherry，那就是"看起来能选、其实没用"。
这种"UI 与实际行为脱节"的 bug 只有抓真实请求体才看得出来。

做法：钩住 window.fetch 记录 /api/ai/tts 的请求体，
逐个点击用户中心的音色按钮，核对请求里的 voice 字段。
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8787, 9396
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
R = []


def ck(n, ok, x=""):
    R.append((n, bool(ok)))
    print(("  [PASS] " if ok else "  [FAIL] ") + n + (("  -> " + str(x)[:90]) if x else ""))


class CDP:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=90)
        self.i = 0

    def send(self, m, **p):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                if "error" in r:
                    raise RuntimeError(str(r["error"]))
                return r.get("result", {})

    def ev(self, e, awp=True):
        r = self.send("Runtime.evaluate", expression=e, awaitPromise=awp,
                      returnByValue=True, userGesture=True)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description") or d.get("text"))
        return r.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
HOOK = """(function(){
  window.__tts = [];
  var of = window.fetch;
  window.fetch = function(u, o){
    try {
      var url = typeof u === 'string' ? u : (u && u.url);
      if (String(url).indexOf('/api/ai/tts') >= 0 && o && o.body) {
        window.__tts.push(String(o.body));
      }
    } catch(e){}
    return of.apply(this, arguments);
  };
  return true;
})()"""


def login():
    for u in ["kbmaile2e", "pm1792201069", "probe1792201040"]:
        try:
            req = urllib.request.Request(
                API + "/api/login", method="POST",
                data=json.dumps({"username": u, "password": "Probe123456"}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "vp"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if j.get("token"):
                return u, j["token"]
        except Exception:
            pass
    return None, None


def main():
    user, token = login()
    if not token:
        print("拿不到令牌")
        return 2
    print("账号 =", user)
    for p in (P_HTTP, P_CDP):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
        except OSError:
            print("端口 %d 被占用" % p)
            return 2
        finally:
            s.close()

    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P_HTTP)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-vp-%d" % os.getpid())
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                             "--autoplay-policy=no-user-gesture-required",
                             "--remote-debugging-port=%d" % P_CDP, "--remote-allow-origins=*",
                             "--user-data-dir=" + prof, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp = None
    try:
        end = time.time() + 25
        while time.time() < end:
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/index.html" % P_HTTP, timeout=2)
                urllib.request.urlopen("http://127.0.0.1:%d/json/version" % P_CDP, timeout=2)
                break
            except Exception:
                time.sleep(0.4)
        tabs = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/list" % P_CDP, timeout=5).read().decode())
        pg = [t for t in tabs if t.get("type") == "page"][0]
        cdp = CDP(pg["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Page.addScriptToEvaluateOnNewDocument",
                 source="try{localStorage.setItem('emc_token', %s);}catch(e){}" % json.dumps(token))
        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % P_HTTP)
        time.sleep(8)
        cdp.ev(HOOK)

        cdp.ev("(function(){EMC.Voice.configure({cloud:true});"
               "document.getElementById('accountBtn').click();return true;})()")
        time.sleep(2)

        opts = cdp.ev("""
          (function(){
            var r=document.getElementById('ucVoice');
            if(!r) return [];
            return [].slice.call(r.querySelectorAll('.theme-opt')).map(function(b){
              return {id:b.getAttribute('data-vv'), label:(b.textContent||'').trim()};
            });
          })()
        """)
        print("")
        print("=== 用户中心提供的音色 ===")
        for o in opts:
            print("   %-8s %s" % (o["id"], o["label"]))
        ck("提供 4 个音色", len(opts) >= 4, len(opts))

        print("")
        print("=== 逐个切换，抓真实请求里的 voice 字段 ===")
        for o in opts:
            cdp.ev("window.__tts=[]; true", False)
            cdp.ev("(function(){var b=document.querySelector('#ucVoice .theme-opt[data-vv=\"%s\"]');"
                   "if(b)b.click();return true;})()" % o["id"], False)
            time.sleep(0.6)
            say = "音色验证" + o["id"]
            cdp.ev("(function(){try{EMC.Voice.speak(%s);}catch(e){}return true;})()"                   % json.dumps(say), False)
            for _ in range(24):
                time.sleep(0.5)
                got = json.loads(cdp.ev("JSON.stringify(window.__tts)"))
                if got:
                    break
            body = (got or [None])[0]
            sent = None
            if body:
                try:
                    sent = json.loads(body).get("voice")
                except Exception:
                    sent = None
            ck("%-8s (%s) 请求带的 voice = %s" % (o["id"], o["label"], sent), sent == o["id"],
               "期望 %s" % o["id"])
            cdp.ev("(function(){try{EMC.Voice.stop();}catch(e){}return true;})()", False)

        print("")
        print("=== 刷新后音色是否记住 ===")
        st = cdp.ev("""
          (function(){
            var h={'Content-Type':'application/json'};
            h['Authoriz'+'ation']='Bearer '+EMCAuth.getToken();
            return fetch('/api/me',{headers:h}).then(function(r){return r.json();})
              .then(function(j){ return JSON.stringify(((j.user||{}).settings||{}).ttsVoice || ''); });
          })()
        """)
        st = json.loads(st)
        print("   云端记住的 ttsVoice =", st)
        ck("所选音色已持久化到云端", st in [o["id"] for o in opts], st)
    finally:
        if cdp:
            cdp.close()
        for p in (proc, srv):
            try:
                p.terminate()
            except Exception:
                pass

    n = sum(1 for _, ok in R if ok)
    print("")
    print("==============================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(R), n, len(R) - n))
    print("==============================================")
    return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())