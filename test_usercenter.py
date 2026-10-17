# -*- coding: utf-8 -*-
"""复现"点击已登录账号弹出错误恢复界面"，抓出真正的异常。

关键：之前的点击测试都是**游客态**（走 openLogin 分支）；
用户遇到的是**已登录态**（走 openUserCenter 分支）—— 两条不同路径，必须分开验。
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
PORT_HTTP = 8090
PORT_CDP = 9345
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
TEST_PWD = "Probe123456"
USERS = ["kbmaile2e", "pm1792201069", "probe1792201040"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def free_port(p):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def get_token():
    for u in USERS:
        try:
            req = urllib.request.Request(
                API + "/api/login", method="POST",
                data=json.dumps({"username": u, "password": TEST_PWD}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "uc"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if j.get("token"):
                return u, j["token"]
        except Exception:
            pass
    return None, None


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.i = 0

    def send(self, method, **p):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": method, "params": p}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError(str(m["error"]))
                return m.get("result", {})

    def ev(self, expr, awp=True):
        r = self.send("Runtime.evaluate", expression=expr, awaitPromise=awp,
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


def wait(url, t=25):
    end = time.time() + t
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.3)
    return False


HOOK = ("(function(){window.__errs=[];window.addEventListener('error',function(e){"
        "window.__errs.push({msg:e.message,src:e.filename,line:e.lineno,col:e.colno,"
        "stack:e.error&&String(e.error.stack)});});return true;})()")


RESULTS = []


def ck(name, ok, extra=""):
    RESULTS.append((name, bool(ok), extra))
    print(("  [PASS] " if ok else "  [FAIL] ") + name
          + (("  -> " + str(extra)) if extra else ""))


def main():
    user, token = get_token()
    print("登录账号 =", user)
    if not token:
        print("拿不到令牌")
        return 2
    if not free_port(PORT_HTTP) or not free_port(PORT_CDP):
        print("端口被占用")
        return 2

    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT_HTTP)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-uc-p-%d" % os.getpid())
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                             "--remote-debugging-port=%d" % PORT_CDP,
                             "--remote-allow-origins=*", "--user-data-dir=" + prof,
                             "about:blank"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    cdp = None
    try:
        wait("http://127.0.0.1:%d/index.html" % PORT_HTTP)
        wait("http://127.0.0.1:%d/json/version" % PORT_CDP)
        tabs = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/list" % PORT_CDP, timeout=5).read().decode())
        pg = [t for t in tabs if t.get("type") == "page"][0]
        cdp = CDP(pg["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % PORT_HTTP)
        time.sleep(4)
        # 钩子必须**在导航之后**装：先装再导航会被页面跳转冲掉，
        # 结果恢复遮罩弹了、__errs 却始终是 0 —— 看着像"没异常"，其实漏抓。
        cdp.ev(HOOK, False)

        print("\n=== 1) 游客态点账号按钮（对照组）===")
        g = json.loads(cdp.ev("(function(){try{var b=document.getElementById('accountBtn');"
                              "if(!b)return '{\"err\":\"no accountBtn\"}';b.click();"
                              "var m=document.getElementById('authModal');"
                              "return JSON.stringify({auth:m?m.style.display:'none'});}"
                              "catch(e){return '{\"threw\":\"'+e.message+'\"}';}})()"))
        print("  ", g)
        ck("游客态点账号弹出登录窗(authModal)", g.get("auth") == "flex", str(g))

        print("\n=== 2) 登录态点账号按钮：应打开用户中心且不弹恢复遮罩 ===")
        r = cdp.ev("(function(){EMCAuth.setToken(%s);window.__errs=[];"
                   "try{document.getElementById('accountBtn').click();}"
                   "catch(e){return '{\"clickThrew\":\"'+e.message+'\"}';}"
                   "return new Promise(function(res){setTimeout(function(){"
                   "var ov=[].slice.call(document.querySelectorAll('div')).filter(function(d){"
                   "return d.textContent.indexOf('出了点小问题')>=0&&d.children.length<6;});"
                   "var uc=document.getElementById('ucModal');"
                   "res(JSON.stringify({errs:window.__errs,recovery:ov.length>0,"
                   "uc:uc?uc.style.display:'no-modal',"
                   "voices:(document.getElementById('ucVoice')||{children:[]}).children.length,"
                   "engines:(document.getElementById('ucAsrEngine')||{children:[]}).children.length,"
                   "tip:(document.getElementById('ucAsrTip')||{}).textContent}));},1500);});})()"
                   % json.dumps(token))
        try:
            d = json.loads(r)
        except Exception:
            print("  ", r)
            d = {}
        errs = d.get("errs") or []
        print("   恢复遮罩 =", d.get("recovery"), "| ucModal =", repr(d.get("uc")))
        print("   识别引擎按钮数 =", d.get("engines"), "| 引擎说明 =", str(d.get("tip"))[:70])
        for e in errs[:3]:
            print("   msg  :", e.get("msg"))
            print("   at   :", "%s:%s" % (e.get("src"), e.get("line")))
            print("   stack:", (e.get("stack") or "")[:500])
        ck("登录态点账号：用户中心打开", d.get("uc") == "flex", repr(d.get("uc")))
        ck("★ 不弹「页面出了点小问题」恢复遮罩", d.get("recovery") is False,
           "遮罩弹出，异常：%s" % (errs[0].get("msg") if errs else "?"))
        ck("零未捕获异常（跨作用域漏网函数的典型症状）", len(errs) == 0,
           "%d 个：%s" % (len(errs), errs[0].get("msg") if errs else ""))
        ck("v37 播报音色选择器已按音色表渲染",
                  (d.get("voices") or 0) >= 4, "voice buttons = %s" % d.get("voices"))
        ck("语音识别引擎列表已渲染", (d.get("engines") or 0) >= 2, d.get("engines"))
        ck("引擎说明文案非空", bool(d.get("tip")), str(d.get("tip"))[:80])
    finally:
        if cdp:
            cdp.close()
        for p in (proc, srv):
            try:
                p.terminate()
            except Exception:
                pass
    npass = sum(1 for x in RESULTS if x[1])
    print("")
    print("==============================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(RESULTS), npass, len(RESULTS) - npass))
    for n, ok, x in RESULTS:
        if not ok:
            print("  x", n, "->", str(x)[:150])
    print("==============================================")
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())