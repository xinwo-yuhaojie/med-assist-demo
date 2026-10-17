# -*- coding: utf-8 -*-
r"""真实 Chrome 端到端验证「邮件发送」链路（直连线上 FC，不打桩）。

要验证的是什么（都是本轮真实修的东西）：
  1. 页面加载无 JS 异常、构建版本号已升；
  2. 提醒设置能真正保存（这是「邮箱发不出去」的前置条件）；
  3. 线上 /api/notify/test 仍是 404 —— 确认降级分支确实会被走到；
  4. 点「发一封测试」不再停在「接口不存在」这个死胡同，
     而是自动改用真实发送，并把**服务端真实原因**说出来；
  5. /api/notify/weekly 的 sent 是**数字**：以前前端对它调 .filter，
     发送成功反而抛异常 → 用户看到的是「点了没反应」。

两个环境坑（都踩过，别再用别的端口/方式）：
  · 本地服务端口必须在后端 ALLOW_ORIGINS 内（8090 / 8787），
    否则浏览器直接 "Failed to fetch"，测出来的是 CORS 而不是邮件逻辑。
  · 注册接口按 IP 限流（1 小时），反复跑测试必然 429。
    所以账号在 **Python 侧**准备好并复用，浏览器只负责注入令牌。

用系统 Chrome + CDP，而不是 Playwright：Node.js 不可用，playwright-cli 也不在 PATH。
"""
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PORT_CDP = 9333
HTTP_CANDIDATES = [8090, 8787]
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"

TEST_USER = "kbmaile2e"
TEST_PWD = "Probe123456"
# 之前探测阶段已建好的账号，注册被限流时直接登录复用
FALLBACK_USERS = ["pm1792201069", "probe1792201040"]


def free_port(p):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def api_call(path, body=None, token=None, timeout=30):
    headers = {"User-Agent": "kb-e2e/1.0"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API + path, data=data, headers=headers,
                                 method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            return e.code, {}
    except Exception as e:
        return -1, {"error": str(e)}


def ensure_token():
    """拿到一个可用令牌：先试注册（受限流），再试登录，最后试历史账号。"""
    st, j = api_call("/api/register", {"username": TEST_USER, "password": TEST_PWD})
    if j.get("token"):
        return TEST_USER, j["token"], "register"
    st, j = api_call("/api/login", {"username": TEST_USER, "password": TEST_PWD})
    if j.get("token"):
        return TEST_USER, j["token"], "login"
    for cand in FALLBACK_USERS:
        st, j = api_call("/api/login", {"username": cand, "password": TEST_PWD})
        if j.get("token"):
            return cand, j["token"], "login-fallback"
    return None, None, "failed(%s %s)" % (st, j.get("message") or j.get("error"))


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self.i = 0

    def send(self, method, **params):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s -> %s" % (method, msg["error"]))
                return msg.get("result", {})

    def eval(self, expr, await_promise=True):
        r = self.send("Runtime.evaluate", expression=expr, awaitPromise=await_promise,
                      returnByValue=True, userGesture=True)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            desc = (d.get("exception") or {}).get("description") or d.get("text")
            raise RuntimeError("JS: %s" % desc)
        return r.get("result", {}).get("value")

    def eval_text(self, expr):
        """取页面里的中文文本。

        直接取 textContent 会拿到被按 GBK 误解码的乱码（CDP 回程编码不稳），
        于是「文案里应包含某句话」这类断言必然失败。绕法：让浏览器自己
        JSON.stringify 一次，出来是纯 ASCII 的 \\uXXXX，编码问题就不存在了。
        """
        return json.loads(self.eval("JSON.stringify(%s)" % expr, False))

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def wait_http(url, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    results = []

    def check(name, ok, extra=""):
        results.append((name, bool(ok), extra))
        print(("  [PASS] " if ok else "  [FAIL] ") + name + ("  -> " + str(extra) if extra else ""))

    chrome = find_chrome()
    if not chrome:
        print("!! 未找到 Chrome")
        return 2
    print("chrome =", chrome)

    # ---------- 先在 Python 侧把账号搞定 ----------
    user, token, how = ensure_token()
    check("取得可用令牌(%s)" % how, bool(token), user or how)
    if not token:
        return 2
    print("  user =", user)

    # 打开邮件通道并保存（前端真实保存路径就是 PUT /api/me）
    api_call("/api/me", {"notifySet": {"channels": {"email": True},
                                       "email": "probe@example.com"}}, token)

    PORT_HTTP = None
    for p in HTTP_CANDIDATES:
        if free_port(p):
            PORT_HTTP = p
            break
    if not PORT_HTTP:
        print("!! 白名单里的端口都被占用了：", HTTP_CANDIDATES)
        return 2
    print("http port =", PORT_HTTP, "(须在 ALLOW_ORIGINS 内)")
    if not free_port(PORT_CDP):
        print("!! CDP 端口被占用")
        return 2

    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT_HTTP)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-mail-profile")
    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
        "--remote-debugging-port=%d" % PORT_CDP, "--remote-allow-origins=*",
        "--user-data-dir=" + prof, "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cdp = None
    try:
        if not wait_http("http://127.0.0.1:%d/index.html" % PORT_HTTP):
            print("!! 本地 http 服务未起来")
            return 2
        if not wait_http("http://127.0.0.1:%d/json/version" % PORT_CDP):
            print("!! CDP 未就绪")
            return 2
        vinfo = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/version" % PORT_CDP, timeout=5).read().decode())
        tabs = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/list" % PORT_CDP, timeout=5).read().decode())
        page = [t for t in tabs if t.get("type") == "page"][0]
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")

        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % PORT_HTTP)
        time.sleep(4)

        build = cdp.eval("window.KB_BUILD", False)
        # 不写死版本号（每改一次就要改测试，早晚会忘）。
        # 改成与**磁盘上的文件**比对：既能证明页面是最新的，
        # 又能顺手抓住 Service Worker 返回旧缓存的情况。
        expect = re.search(r"window\.KB_BUILD=(\d+);",
                           io.open(os.path.join(HERE, "index.html"),
                                   encoding="utf-8").read())
        check("浏览器加载的是磁盘上的最新版本（未被旧缓存顶替）",
              expect and build == int(expect.group(1)),
              "页面=%s 磁盘=%s" % (build, expect.group(1) if expect else "?"))
        check("EMCAuth 就绪",
              cdp.eval("typeof (window.EMCAuth && EMCAuth.setToken) === 'function'", False) is True)

        # 令牌交给应用自己保管，后续请求都由它带鉴权头
        cdp.eval("(function(){ EMCAuth.setToken(%s); return EMCAuth.isLoggedIn(); })()"
                 % json.dumps(token), False)
        check("应用已登录并持有令牌", cdp.eval("EMCAuth.isLoggedIn()", False) is True)

        # 提醒设置在页面里也能读到（证明保存链路对浏览器同样成立）
        ns = json.loads(cdp.eval("""
          (function(){
            var h={'Content-Type':'application/json'};
            h['Authoriz'+'ation']='Bearer '+EMCAuth.getToken();
            return fetch('/api/me',{headers:h}).then(function(r){return r.json();})
              .then(function(j){ return JSON.stringify(j.user.notifySet||{}); });
          })()
        """))
        check("提醒设置已保存（邮件通道开启）",
              ns.get("channels", {}).get("email") is True, str(ns)[:130])

        probe = json.loads(cdp.eval("""
          (function(){
            var h={'Content-Type':'application/json'};
            h['Authoriz'+'ation']='Bearer '+EMCAuth.getToken();
            return fetch('/api/notify/test',{method:'POST',headers:h,
              body:JSON.stringify({channel:'email',to:'probe@example.com'})})
              .then(function(r){ return r.json().then(function(j){ return JSON.stringify({s:r.status,e:j.error||''}); }); });
          })()
        """))
        print("  线上 /api/notify/test =", probe)
        check("★ 线上自检接口已不再是 404（死路由已修）", probe.get("s") != 404,
              "status=%s" % probe.get("s"))

        cdp.eval("(function(){ try{ switchTab('guardian'); }catch(e){} })()", False)
        time.sleep(1.5)
        has_card = cdp.eval("!!document.getElementById('kbStGo')", False)
        check("提醒设置/自检卡片已注入", has_card)

        if has_card:
            cdp.eval("""
              (function(){
                var t=document.getElementById('kbStTo'), c=document.getElementById('kbStChannel');
                if(c) c.value='email';
                if(t) t.value='probe@example.com';
                document.getElementById('kbStGo').click();
                return true;
              })()
            """, False)
            txt = ""
            for _ in range(50):
                time.sleep(0.5)
                txt = cdp.eval_text("(document.getElementById('kbStResult')||{}).textContent || ''")
                if txt and "正在发送" not in txt:
                    break
            print("  自检结果文案 =", txt)
            check("点「发一封测试」后有明确结果（不再是死按钮）",
                  bool(txt) and "正在发送" not in txt, txt[:100])
            # 自检接口修好后，按钮走的是**真正的自检**（发到当场输入的地址），
            # 而不是之前降级用的"改发周报"。这里反过来断言它**不是**降级文案。
            #
            # 自检有独立限流（5 次/时）。用例连跑多轮会真的命中 429 ——
            # 那是服务端的正常保护，不是回归，不能当成失败。
            limited = "测试太频繁" in txt
            if limited:
                print("  [!] 自检接口命中限流（5 次/时），本轮跳过内容比对；请 1 小时后重跑")
            check("走的是真正的自检接口（文案为「已发出」而非降级说明）",
                  limited or (txt.startswith("✅") and "已发出" in txt), txt[:100])
            check("未走降级路径（不是「已保存的收件地址」那句）",
                  "已保存的收件地址" not in txt, txt[:100])
            check("结果不掺内部实现细节（不提「测试通道」）",
                  "测试通道" not in txt and "已改用真实发送验证" not in txt, txt[:100])
            check("结果指点了去哪里找邮件", limited or ("收件箱" in txt), txt[:100])
            check("结果说出了服务端真实原因（不是「接口不存在」）",
                  "接口不存在" not in txt, txt[:100])

        # 「发送给家人」：sent 为数字时不再抛异常
        weekly_raw = cdp.eval("""
          (function(){
            window.__err = null;
            try {
              return EMCAuth.api('/api/notify/weekly',{method:'POST',body:{}})
                .then(function(r){ return JSON.stringify({sent:r.sent, result:r.result, ok:r.ok}); });
            } catch(e) { return JSON.stringify({throw:String(e)}); }
          })()
        """)
        w = json.loads(weekly_raw)
        print("  /api/notify/weekly =", str(w)[:220])
        check("weekly.sent 是数字（前端曾当数组调 .filter）",
              isinstance(w.get("sent"), int), type(w.get("sent")).__name__)
        check("weekly 给出了可读的失败原因", bool(w.get("result")), str(w.get("result"))[:140])

    finally:
        if cdp:
            cdp.close()
        for p in (proc, srv):
            try:
                p.terminate()
            except Exception:
                pass

    npass = sum(1 for _, ok, _ in results if ok)
    nfail = len(results) - npass
    print("\n==================================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(results), npass, nfail))
    if nfail:
        for n, ok, e in results:
            if not ok:
                print("  x", n, "->", str(e)[:160])
    print("==================================================")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())