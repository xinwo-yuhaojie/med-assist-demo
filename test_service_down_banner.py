# -*- coding: utf-8 -*-
"""验证 v42：后端函数宕机时，前端必须**说人话**，而不是让用户干瞪眼。

【要验证的真实缺陷（2026-10-19）】
    用户登录网站后"啥都点不了"，且看不出任何原因。
    根因链：云端函数实例启动失败 → 阿里云网关**照样返回 HTTP 响应**
    （412 CAExited）→ 走不到前端"网络异常"分支（那是 _status:0 才触发的）
    → 响应体是 {RequestId,Code,Message}，没有 ok 字段、还是英文堆栈
    → 业务代码只看到 r.ok 为假 → 每个按钮停在原地，无任何解释。

【为什么这个测试不 mock 网关】
    线上后端**此刻正是** 412 宕机状态，天然就是最真实的复现环境。
    所以这里直接打开页面让它去打真实云端，用真故障验证真修复。
    （若线上已恢复，本用例会因拿不到 412 而 FAIL —— 那属于环境变化，
      此时应改为本地起一个返回 412 的 mock 服务再验。）

【为什么必须用真实 Chrome】
    这段逻辑依赖 DOM、CSSOM 与 fetch 重写层，静态检查和 jsdom 都验不出来。

跑法（脚本依赖 http.server 提供页面，必须先起）：
    python -m http.server 8899
    python test_service_down_banner.py
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8899/index.html"
PORT = 9351
PROFILE = os.path.join(os.environ.get("TEMP", "."), "kb_down_test")

try:
    import websocket
except ImportError:
    print("需要 websocket-client：pip install websocket-client"); sys.exit(2)
if not os.path.exists(CHROME):
    print("未找到 Chrome"); sys.exit(2)

# 只杀本脚本的 headless Chrome，不动用户自己的浏览器
ps = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
     "Where-Object { $_.CommandLine -like '*kb_down_test*' }).ProcessId"],
    capture_output=True, text=True, timeout=20)
for p in (ps.stdout or "").split():
    if p.strip().isdigit():
        subprocess.run(["taskkill", "/F", "/PID", p.strip()], capture_output=True)
time.sleep(1)

proc = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--remote-debugging-port=%d" % PORT, "--remote-allow-origins=*",
     "--user-data-dir=" + PROFILE, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

OK = True
_msg_id = [0]


def ck(desc, cond, extra=""):
    global OK
    print(("  PASS  " if cond else "  FAIL  ") + desc + (("  -> " + str(extra)) if extra else ""))
    OK = OK and bool(cond)


try:
    t0 = time.time()
    while time.time() - t0 < 25:
        try:
            socket.create_connection(("127.0.0.1", PORT), 1).close(); break
        except OSError:
            time.sleep(0.4)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json" % PORT, timeout=8).read())
    page = next(t for t in tabs if t.get("type") == "page")
    s = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=25)

    events = []

    def cmd(method, params=None):
        _msg_id[0] += 1
        s.send(json.dumps({"id": _msg_id[0], "method": method, "params": params or {}}))
        while True:
            m = json.loads(s.recv())
            if m.get("id") == _msg_id[0]:
                return m.get("result", {})
            # 非本次回包的 CDP 事件先攒起来，事后用来查网络请求
            if "method" in m:
                events.append(m)

    def js(expr):
        r = cmd("Runtime.evaluate",
                {"expression": expr, "returnByValue": True, "awaitPromise": True})
        res = r.get("result", {})
        if res.get("subtype") == "error" or res.get("type") == "error":
            return {"__err": res.get("description", "?")}
        return res.get("value")

    cmd("Page.enable"); cmd("Runtime.enable"); cmd("Network.enable")
    # 必须禁用缓存：否则 headless 可能复用上一轮的 index.html，
    # 会把"修复没生效"和"加载了旧文件"混为一谈。
    cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    cmd("Page.navigate", {"url": BASE})
    time.sleep(4)

    print("=== 1. 页面自身可用（不是页面没加载）===")
    ck("页面标题已渲染", bool(js("document.title && document.title.length")))
    ck("存在 data-tab 导航（证明 DOM 正常）",
       (js("document.querySelectorAll('[data-tab]').length") or 0) > 0,
       "count=%s" % js("document.querySelectorAll('[data-tab]').length"))

    print("\n=== 2. 云端是否真的处于故障（否则本用例无意义）===")
    st = js("(function(){return fetch('https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run/api/me',"
            "{cache:'no-store'}).then(function(r){return r.status;}).catch(function(e){return 'NET:'+e.message;});})()")
    ck("云端确实不可用（返回 5xx/412 等故障码）", st != 200,
       "status=%s —— 若已是 200，说明后端已恢复，本用例需改用本地 mock 复现" % st)

    print("\n=== 3. 核心：真实登录路径能否识别网关故障 ===")
    # 注意：api() 并不在全局作用域（它在 IIFE 里），Runtime.evaluate 调不到，
    # 所以这里走**真实用户路径**：打开登录弹窗 → 填表 → 提交。
    # 这比直接调函数更可信 —— 验的是用户实际会遇到的那条链路。
    js("document.getElementById('accountBtn').click();")
    time.sleep(1.0)
    ck("登录弹窗已打开", bool(js("(function(){var e=document.getElementById('authUser');"
                                "if(!e) return false; var b=e.closest('[class*=modal],[class*=dialog],.mask,.overlay]')"
                                "|| e.offsetParent !== null; return !!b;})()")))
    # 必须先切到「登录」页签：弹窗默认可能是「注册」，
    # 那样提交会走注册校验（要填 authPwd2 确认密码），请求根本发不出去 ——
    # 这一点是本用例第一次跑就踩的坑：不切页签会误判成"修复无效"。
    js("(function(){var t=document.getElementById('authTabLogin'); if(t) t.click();})()")
    time.sleep(0.6)
    js("(function(){var u=document.getElementById('authUser'),p=document.getElementById('authPwd');"
       "u.value='kbprobe_notreal'; u.dispatchEvent(new Event('input',{bubbles:true}));"
       "u.dispatchEvent(new Event('change',{bubbles:true}));"
       "p.value='Test123456'; p.dispatchEvent(new Event('input',{bubbles:true}));"
       "p.dispatchEvent(new Event('change',{bubbles:true}));})()")
    time.sleep(0.3)
    js("document.getElementById('authSubmit').click();")

    # 轮询等待提示条出现：登录要经过 CORS 预检 + fetch 失败，时序不稳定，
    # 固定 sleep 会偶发读到"还没渲染"的页面（第一版就是这么误判的）。
    print("\n=== 3b. 诊断：登录请求到底发生了什么 ===")
    bar = None
    shown = ""
    for i in range(30):                      # 最多等 15 秒
        time.sleep(0.5)
        bar = js("(function(){var e=document.querySelector('.service-down-bar');"
                 "if(!e) return null; var s=getComputedStyle(e);"
                 "return {text:(e.textContent||'').slice(0,80), display:s.display,"
                 " visible:e.offsetHeight>0, pos:s.position};})()")
        if bar:
            break
        shown = js("(function(){var e=document.getElementById('authMsg');"
                   "return e ? (e.textContent||'').slice(0,80) : '';})()")
    reqs = [(e.get("params", {}).get("request", {}).get("url", ""),
             e.get("params", {}).get("response", {}).get("status"))
            for e in events if e.get("method") == "Network.responseReceived"]
    api_reqs = [(u.split("?")[0].split("/")[-1], st) for u, st in reqs if "/api/" in u]
    print("   CDP 捕获到 /api 响应 =", api_reqs[-6:] if api_reqs else "（无）")
    print("   —— CORS 预检失败时 CDP 也看不到响应，这是预期现象，不是缺陷")
    print("   #authMsg =", repr(shown))

    print("\n=== 4. 界面上是否真的有可见提示 ===")
    ck("页面出现故障提示条", bool(bar), bar)
    if bar:
        print("   提示条内容 =", bar.get("text"))
        ck("提示条内容为中文且说明了原因",
           ("云端" in (bar.get("text") or "")) and ("不可用" in (bar.get("text") or "")), bar.get("text"))
        ck("提示条确实可见（有高度、未 display:none）",
           bar.get("visible") is True and bar.get("display") != "none", bar)
        ck("提示条是浮层（fixed），不挤动页面布局", bar.get("pos") == "fixed", bar)
        ck("提示条被提升到最顶层（不被遮挡）",
           (js("getComputedStyle(document.querySelector('.service-down-bar')).zIndex") or "") in
           ("2147483000", "2147483000px"), None)
    toast_txt = js("(function(){var t=document.querySelectorAll('.toast');"
                   "return Array.prototype.map.call(t,function(e){return e.textContent;}).join(' | ');})()")
    print("   toast =", repr(toast_txt)[:160])

    print("\n=== 5. 旧行为对照：修复前这类响应会静默失败 ===")
    raw = js("(function(){return fetch('https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run/api/me',"
             "{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){return {hasOk:('ok' in j)};});})()")
    ck("裸 fetch 拿到的网关响应确实没有 ok 字段（这正是旧代码误判的来源）",
       raw.get("hasOk") is False, raw)

finally:
    try:
        s.close()
    except Exception:
        pass
    proc.kill()
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                    "Where-Object { $_.CommandLine -like '*kb_down_test*' }).ProcessId | "
                    "ForEach-Object { Stop-Process -Id $_ -Force }"],
                   capture_output=True)
    subprocess.run(["taskkill", "/F", "/PID", str(proc.pid)], capture_output=True)

print("\n" + "=" * 58)
print("前端故障提示验证通过" if OK else "验证未通过")
print("=" * 58)
sys.exit(0 if OK else 1)
