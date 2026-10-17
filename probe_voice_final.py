# -*- coding: utf-8 -*-
"""决定性验证：真实浏览器能否真的拿到并播放千问音频。
之前两次失败分别死在 CORS 预检与 http 音频直链，这次逐环确认。"""
import json, os, socket, subprocess, sys, time, urllib.request, urllib.parse
import websocket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8090, 9351
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def free(p):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p)); return True
    except OSError:
        return False
    finally:
        s.close()

class CDP:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=90); self.i = 0
    def send(self, m, **p):
        self.i += 1; mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                if "error" in r: raise RuntimeError(str(r["error"]))
                return r.get("result", {})
    def ev(self, e, awp=True):
        r = self.send("Runtime.evaluate", expression=e, awaitPromise=awp,
                      returnByValue=True, userGesture=True)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description") or d.get("text"))
        return r.get("result", {}).get("value")
    def close(self):
        try: self.ws.close()
        except Exception: pass

def wait(u, t=25):
    end = time.time() + t
    while time.time() < end:
        try:
            urllib.request.urlopen(u, timeout=2); return True
        except Exception:
            time.sleep(0.3)
    return False

srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P_HTTP)],
                       cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
prof = os.path.join(os.environ.get("TEMP", "."), "kb-v-%d" % os.getpid())
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
    "--autoplay-policy=no-user-gesture-required",
    "--remote-debugging-port=%d" % P_CDP, "--remote-allow-origins=*",
    "--user-data-dir=" + prof, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cdp = None
try:
    wait("http://127.0.0.1:%d/index.html" % P_HTTP); wait("http://127.0.0.1:%d/json/version" % P_CDP)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/list" % P_CDP, timeout=5).read().decode())
    pg = [t for t in tabs if t.get("type") == "page"][0]
    cdp = CDP(pg["webSocketDebuggerUrl"])
    cdp.send("Page.enable"); cdp.send("Runtime.enable")
    cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % P_HTTP)
    time.sleep(5)

    print("=== 环1：应用自己的 fetch 能否打通 CORS 预检 ===")
    j = (cdp.ev("""
      (function(){
        return fetch('/api/ai/tts', {method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({text:'康伴语音已恢复', voice:'Cherry'})})
          .then(function(r){ return r.json(); });
      })()
    """))
    direct = j.get("url")
    # 线上还是旧包(streamUrl 是相对路径)，这里手工拼出**新逻辑**会给的绝对地址，
    # 以便在上传新包之前就验证 CSP + 代理这一段。
    su = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run/api/ai/tts/audio?u=" + urllib.parse.quote(direct or "", safe="")
    print("  成功拿到音频(说明 CORS 预检已通过) =", bool(direct))
    print("  拼出的同源代理绝对地址 =", su[:96] + "...")

    print("")
    print("=== 环2：同源音频能否加载并播放 ===")
    d = json.loads(cdp.ev("""
      (function(){
        return new Promise(function(res){
          var a = new Audio(%s);
          var out = {srcScheme: (a.src||'').split(':')[0]};
          a.onloadedmetadata = function(){
            out.meta = true; out.dur = Math.round((a.duration||0)*10)/10;
            var pr = a.play();
            if (pr && pr.then) pr.then(function(){ out.played = true; })
                                 .catch(function(e){ out.playErr = e.name; });
            setTimeout(function(){ res(JSON.stringify(out)); }, 1200);
          };
          a.onerror = function(){
            out.err = a.error ? a.error.code : -1;
            out.msg = a.error ? a.error.message : '';
            res(JSON.stringify(out));
          };
          setTimeout(function(){ if(!out.meta && !out.err) res(JSON.stringify({timeout:true})); }, 12000);
        });
      })()
    """ % json.dumps(su)))
    print("  ", d)
    ok = isinstance(d, dict) and d.get("meta") is True and d.get("err") is None
    print("  判定:", "PASS 跨源音频加载成功" if ok else "FAIL " + str(d))
    if isinstance(d, dict):
        print("")
        print("  时长 =", d.get("dur"), "秒 | 播放 =", d.get("played"),
              "| 自动播放被拒 =", d.get("playErr"))
finally:
    if cdp: cdp.close()
    for p in (proc, srv):
        try: p.terminate()
        except Exception: pass