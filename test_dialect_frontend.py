# -*- coding: utf-8 -*-
"""v43 前端方言链路端到端测试（真实 Chrome + 假麦克风 + mock 后端）。

【验的是什么】
    后端那侧已单独验过 8 个方言音色真的能合成出不同音频（dialect_tts_test.py）。
    这里验的是**前端这一段**：识别结果里的 dialect 到底有没有被记住、
    记住后有没有真的带进 TTS 请求、以及用户把开关关掉后会不会失效。
    这三处任何一处漏掉，功能都是"看起来接好了、实际不响"。

【为什么 mock 后端而不是打线上】
    线上后端此刻还没部署方言版；而且真调 ASR 需要真人录音。
    这里用 Chrome 的假麦克风设备走**真实的 MediaRecorder 录音 → base64 → fetch**
    链路，只把服务端响应换成假的，既能跑通全流程又不花钱。

【关键断言】
    ① 识别为四川话后，EMC.Voice.dialectInfo() 显示 sc 且 active=true
    ② 随之发往 /api/ai/tts 的请求体里确实带上了 dialect:'sc'
    ③ 关掉 cfg.dialectFollow 后，同一状态下请求体**不再**带方言（开关真的生效）
    ④ 普通话（zh）时不带方言 —— 即需求里的"识别不到就用普通话"

跑法（需先起本地静态服务）：
    python -m http.server 8899
    python test_dialect_frontend.py
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
PORT = 9352
PROFILE = os.path.join(os.environ.get("TEMP", "."), "kb_dialect_fe")

try:
    import websocket
except ImportError:
    print("需要 websocket-client：pip install websocket-client"); sys.exit(2)
if not os.path.exists(CHROME):
    print("未找到 Chrome"); sys.exit(2)

ps = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
     "Where-Object { $_.CommandLine -like '*kb_dialect_fe*' }).ProcessId"],
    capture_output=True, text=True, timeout=20)
for p in (ps.stdout or "").split():
    if p.strip().isdigit():
        subprocess.run(["taskkill", "/F", "/PID", p.strip()], capture_output=True)
time.sleep(1)

proc = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
     "--autoplay-policy=no-user-gesture-required",
     "--remote-debugging-port=%d" % PORT, "--remote-allow-origins=*",
     "--user-data-dir=" + PROFILE, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

OK = True
MID = [0]


def ck(desc, cond, extra=""):
    global OK
    print(("  PASS  " if cond else "  FAIL  ") + desc + (("  -> " + str(extra)) if extra else ""))
    OK = OK and bool(cond)


# 页面加载前注入：替换 window.fetch。
# 页面自己的重写层在加载时抓取 window.fetch 作为 _fetch，
# 所以这里替换得够早，整条 /api/ 链路最终都会落到这个 mock 上。
MOCK_JS = r"""
(function () {
  window.__calls = [];
  var realFetch = window.fetch.bind(window);
  // 44 字节标准 WAV 头 + 少量静音：足够让 new Audio() 不抛异常
  var WAV = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YQAAAAA=';
  window.fetch = function (input, init) {
    var url = (typeof input === 'string') ? input
            : (input && input.url ? input.url : String(input));
    var body = null;
    try { body = (init && init.body) ? JSON.parse(init.body) : null; } catch (e) {}
    // 只拦截**识别**接口，不能连 /status 一起拦：
    // 页面初始化时会探测 /api/asr/local/status 决定用哪个识别引擎，
    // 一并 mock 掉会返回错格式，导致语音模块初始化异常（曾表现为
    // EMC.Voice.dialectInfo 整个查不到 —— 实为 mock 副作用，不是代码缺陷）。
    if (url.indexOf('/api/asr/local') >= 0 && url.indexOf('/status') < 0) {
      window.__calls.push({ kind: 'asr' });
      var dialect = window.__mockDialect || 'zh';
      return Promise.resolve({
        ok: true, status: 200,
        json: function () { return Promise.resolve({
          ok: true, text: '莫得问题', dialect: dialect,
          dialectLabel: dialect === 'zh' ? '普通话' : '四川话'
        }); },
        text: function () { return Promise.resolve('{}'); }
      });
    }
    if (url.indexOf('/api/ai/tts') >= 0) {
      window.__calls.push({ kind: 'tts', dialect: body ? body.dialect : undefined,
                            voice: body ? body.voice : undefined });
      return Promise.resolve({
        ok: true, status: 200,
        json: function () { return Promise.resolve({ ok: true, streamUrl: WAV, url: WAV }); }
      });
    }
    return realFetch(input, init);
  };
})();
"""

try:
    t0 = time.time()
    while time.time() - t0 < 25:
        try:
            socket.create_connection(("127.0.0.1", PORT), 1).close(); break
        except OSError:
            time.sleep(0.4)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json" % PORT, timeout=8).read())
    page = next(t for t in tabs if t.get("type") == "page")
    s = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)

    def cmd(method, params=None):
        MID[0] += 1
        s.send(json.dumps({"id": MID[0], "method": method, "params": params or {}}))
        while True:
            m = json.loads(s.recv())
            if m.get("id") == MID[0]:
                return m.get("result", {})

    def js(expr):
        r = cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        res = r.get("result", {})
        if res.get("type") == "error":
            return {"__err": res.get("description", "?")}
        return res.get("value")

    cmd("Page.enable"); cmd("Runtime.enable")
    cmd("Page.addScriptToEvaluateOnNewDocument", {"source": MOCK_JS})
    cmd("Page.navigate", {"url": BASE})
    time.sleep(5)

    print("=== 1. 语音模块就绪 ===")
    # speak() 有解锁门槛：未解锁时只把文本塞进 voicePending 队列等待，
    # 根本不会发出 TTS 请求。测方言必须先解锁，否则测的是"没播报"而非"没带方言"。
    js("window.__kbVoiceUnlocked = true;")
    ck("V 模块已加载", bool(js("typeof EMC !== 'undefined' && !!EMC.Voice")))
    ck("EMC.Voice.dialectInfo 可用", bool(js("typeof EMC !== 'undefined' && typeof EMC.Voice.dialectInfo === 'function'")))
    ck("方言跟随默认开启", js("EMC.Voice.getConfig().dialectFollow") is True, js("EMC.Voice.getConfig().dialectFollow"))

    print("\n=== 2. 识别为四川话 -> 应被记住 ===")
    js("window.__mockDialect = 'sc'; window.__calls = [];")
    started = js("(function(){ try {"
                " window.__asrDone = false;"
                " window.__ctl = EMC.Voice.listen({ onEnd: function(t){ window.__asrDone = true; window.__asrText = t; },"
                "            onError: function(c){ window.__asrErr = c; } });"
                " return true; } catch(e){ return {err: String(e)}; } })()")
    ck("录音流程已启动", started is True, started)
    # 录音是持续进行的：listen() 只负责开始，必须主动 stop 才会产出结果并回调 onEnd。
    # 第一版忘了 stop，就一直等 onEnd，等到超时只能报"没返回"——那是测试的错，不是代码的错。
    time.sleep(2.5)
    js("(function(){ try { window.__ctl && window.__ctl.stop && window.__ctl.stop(); } catch(e){} })()")
    for _ in range(30):
        time.sleep(0.5)
        if js("window.__asrDone === true") or js("!!window.__asrErr"):
            break
    info = js("EMC.Voice.dialectInfo()") or {}
    print("   dialectInfo =", json.dumps(info, ensure_ascii=False))
    ck("识别文本已返回", js("window.__asrDone === true") is True,
       "text=%s err=%s" % (js("window.__asrText"), js("window.__asrErr")))
    ck("方言被记为四川话 sc", info.get("dialect") == "sc", info)
    ck("方言处于生效状态(active)", info.get("active") is True, info)

    print("\n=== 3. 朗读时必须把方言带进 TTS 请求 ===")
    js("window.__calls = [];")
    js("(function(){ try { EMC.Voice.speak('该按时吃药了'); } catch(e) { window.__speakErr = String(e); } })()")
    for _ in range(20):
        time.sleep(0.5)
        calls = js("(function(){return (window.__calls||[]).filter(function(c){return c.kind==='tts';});})()")
        if calls:
            break
    calls = js("(function(){return (window.__calls||[]).filter(function(c){return c.kind==='tts';});})()") or []
    print("   TTS 请求 =", json.dumps(calls, ensure_ascii=False)[:200])
    ck("确实向 TTS 发起了合成请求", len(calls) > 0, js("window.__speakErr"))
    if calls:
        ck("请求体带上 dialect='sc'（关键）", calls[0].get("dialect") == "sc", calls[0])

    print("\n=== 4. 关掉开关后不应再带方言 ===")
    js("EMC.Voice.configure({ dialectFollow: false }); window.__calls = [];")
    info2 = js("EMC.Voice.dialectInfo()") or {}
    ck("关闭后 active 变 false", info2.get("active") is False, info2)
    js("(function(){ try { EMC.Voice.speak('再念一次'); } catch(e) {} })()")
    for _ in range(20):
        time.sleep(0.5)
        calls2 = js("(function(){return (window.__calls||[]).filter(function(c){return c.kind==='tts';});})()")
        if calls2:
            break
    calls2 = js("(function(){return (window.__calls||[]).filter(function(c){return c.kind==='tts';});})()") or []
    ck("关闭后 TTS 请求不再带方言", (not calls2) or calls2[0].get("dialect") in (None, ""), calls2[:1])

    print("\n=== 5. 识别为普通话时用普通话（需求的兜底）===")
    js("EMC.Voice.configure({ dialectFollow: true }); EMC.Voice.resetDialect(); window.__mockDialect = 'zh'; window.__calls = [];")
    js("(function(){ try { window.__ctl5 = EMC.Voice.listen({ onEnd: function(){}, onError: function(){} }); } catch(e){} })()")
    time.sleep(2.5)
    js("(function(){ try { window.__ctl5 && window.__ctl5.stop && window.__ctl5.stop(); } catch(e){} })()")
    for _ in range(30):
        time.sleep(0.5)
        if js("EMC.Voice.dialectInfo().label") == "普通话":
            break
    info3 = js("EMC.Voice.dialectInfo()") or {}
    print("   dialectInfo =", json.dumps(info3, ensure_ascii=False))
    ck("普通话被正确识别且不启用方言", info3.get("dialect") == "zh" and info3.get("active") is False, info3)

finally:
    try:
        s.close()
    except Exception:
        pass
    proc.kill()
    subprocess.run(["taskkill", "/F", "/PID", str(proc.pid)], capture_output=True)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                    "Where-Object { $_.CommandLine -like '*kb_dialect_fe*' }).ProcessId | "
                    "ForEach-Object { Stop-Process -Id $_ -Force }"], capture_output=True)

print("\n" + "=" * 58)
print("前端方言链路验证通过" if OK else "前端方言链路验证未通过")
print("=" * 58)
sys.exit(0 if OK else 1)
