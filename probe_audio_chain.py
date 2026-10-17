# -*- coding: utf-8 -*-
"""定位千问女声为什么不出声：网络 / CSP / 自动播放 / 开关，四选一。"""
import json, os, socket, subprocess, sys, time, urllib.request
import websocket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8090, 9350
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
prof = os.path.join(os.environ.get("TEMP", "."), "kb-audio-%d" % os.getpid())
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
    cdp.send("Network.enable")
    cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % P_HTTP)
    time.sleep(5)

    # 先向服务端要一段音频
    j = json.loads(cdp.ev("""
      (function(){
        return fetch('/api/ai/tts', {method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({text:'语音链路诊断', voice:'Cherry'})})
          .then(function(r){ return r.json(); });
      })()
    """))
    su = j.get("streamUrl")
    print("拿到 streamUrl =", (su or "无")[:70])

    print("")
    print("=== A. 同源音频能否加载（CSP/网络）===")
    d = cdp.ev("""
      (function(){
        return new Promise(function(res){
          var a = new Audio(%s);
          var out = {src: (a.src||'').slice(0,60)};
          var done = function(extra){
            out.readyState = a.readyState; out.dur = a.duration;
            out.networkState = a.networkState;
            Object.keys(extra||{}).forEach(function(k){ out[k]=extra[k]; });
            res(JSON.stringify(out));
          };
          a.onloadedmetadata = function(){ out.metaLoaded = true; done(); };
          a.onerror = function(){
            out.err = a.error ? (a.error.code + ' ' + a.error.message) : 'no-error-obj';
            out.code = a.error ? a.error.code : -1;
            done();
          };
          a.oncanplay = function(){ out.canPlay = true; done(); };
          var pr = a.play();
          if (pr && pr.catch) pr.catch(function(e){ out.playRejected = String(e.name)+': '+String(e.message); });
          setTimeout(function(){ if(!out.readyState && !out.err) done({timeout:true}); }, 9000);
        });
      })()
    """ % json.dumps(su))
    print("  ", d)
    dd = json.loads(d)
    print("  CSP/网络:", "OK（音频已加载，metadata 就绪）" if dd.get("metaLoaded") or dd.get("canPlay")
          else ("失败 err=%s code=%s" % (dd.get("err"), dd.get("code"))))
    print("  自动播放:", "被拦截 -> " + dd["playRejected"] if dd.get("playRejected") else "未被拦截")

    print("")
    print("=== B. 应用的云端语音开关状态 ===")
    print("  ", cdp.ev("""
      (function(){
        try {
          var s = JSON.parse(localStorage.getItem('emc_s') || '{}');
          return JSON.stringify({cloudVoice: s.cloudVoice, voice: s.voice, ttsVoice: s.ttsVoice});
        } catch(e){ return 'no-local-settings: ' + e.message; }
      })()
    """))
finally:
    if cdp: cdp.close()
    for p in (proc, srv):
        try: p.terminate()
        except Exception: pass