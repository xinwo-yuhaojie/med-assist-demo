# -*- coding: utf-8 -*-
"""v44 \u6536\u5c3e\uff1a\u9010\u9879\u6838\u5bf9\u524d\u9762\u6240\u6709\u58f0\u79f0\u4fee\u8fc7\u7684\u4e1c\u897f\u662f\u5426\u771f\u5728\u6587\u4ef6\u91cc\u3002

\u80cc\u666f\uff1a\u8fd9\u4e00\u8f6e\u5bf9\u8bdd\u91cc\u53d1\u751f\u8fc7 **3 \u6b21\u811a\u672c\u8986\u76d6\u4e8b\u6545**\uff08\u811a\u672c\u5185\u90e8 exit(1) \u5bfc\u81f4\u6587\u4ef6\u672a\u5199\u5165\uff09\uff0c
\u4e5f\u53d1\u751f\u8fc7 1 \u6b21 **index.html \u88ab\u622a\u65ad\u4e3a 0 \u5b57\u8282**\u3002\u6240\u4ee5\u4e0d\u80fd\u53ea\u770b\u300c\u6211\u8bf4\u4fee\u597d\u4e86\u300d\uff0c
\u5fc5\u987b\u9010\u9879\u6bd4\u5bf9\u6587\u4ef6\u5b9e\u9645\u5185\u5bb9\u3002"""
import io
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"D:\网站专用\网站式老人慢性病用药辅助智能体"
FE = os.path.join(BASE, "my-first-site")
BE = os.path.join(BASE, "backend", "fc-web")

files = {
    "index.html": io.open(os.path.join(FE, "index.html"), encoding="utf-8").read(),
    "kb.js": io.open(os.path.join(FE, "kb.js"), encoding="utf-8").read(),
    "sw.js": io.open(os.path.join(FE, "sw.js"), encoding="utf-8").read(),
    "dashboard.html": io.open(os.path.join(FE, "dashboard.html"), encoding="utf-8").read(),
    "server.js": io.open(os.path.join(BE, "server.js"), encoding="utf-8").read(),
    "store.js": io.open(os.path.join(BE, "store.js"), encoding="utf-8").read(),
}
OK = [True]


def ck(label, where, needle):
    hay = files[where]
    hit = needle in hay
    OK[0] = OK[0] and hit
    print(("  [OK]   " if hit else "  [MISS] ") + label + "  (" + where + ")")
    return hit


print("=" * 74)
print("### A. \u7528\u6237\u529f\u80fd\u9700\u6c42\uff08\u6bcf\u4e00\u6761\u90fd\u8981\u80fd\u5728\u6587\u4ef6\u91cc\u627e\u5230\uff09")
print("=" * 74)
ck("A1 \u770b\u677f\u8868\u5934\u6709\u8840\u538b\u5217", "dashboard.html", "血压(7天均值)")
ck("A2 \u770b\u677f\u8868\u5934\u6709\u8840\u7cd6\u5217", "dashboard.html", "血糖(7天均值)")
ck("A3 \u770b\u677f\u6e32\u67d3\u7528 bpSys7", "dashboard.html", "bpSys7")
ck("A4 \u770b\u677f\u7528\u504f\u9ad8\u6807\u8bb0", "dashboard.html", "warnflag")
ck("A5 \u98ce\u9669\u8d8b\u52bf Y \u8f74\u663e\u5f0f\u91cf\u7a0b", "index.html", "yMax: Math.max(3, maxScore)")
ck("A6 \u98ce\u9669\u8d8b\u52bf\u6570\u636e\u6458\u8981\u884c", "index.html", "最高风险分")
ck("A7 \u98ce\u9669\u8d8b\u52bf\u7a7a\u6001\u63d0\u793a", "index.html", "近 14 天还没有用药打卡")
ck("A8 \u5206\u6bb5\u6717\u8bfb\uff1a\u6309\u94ae\u5728\u6bb5\u843d\u524d\uff08\u4ea4\u9519\u6e32\u67d3\uff09", "index.html", "renderParaWithSpeak")
ck("A9 \u5206\u6bb5\u6717\u8bfb\uff1a\u6587\u5b57\u53ea\u7528\u300c\u8bfb\u300d", "index.html", "b.textContent = '📢读'")
hit10 = "appendParaSpeak" not in files["index.html"]
OK[0] = OK[0] and hit10
print(("  [OK]   " if hit10 else "  [MISS] ") + "A10 split-speak: old fn removed  (index.html)")
ck("A11 \u5242\u578b\u5f52\u4e00\u5316\uff08\u4fbf\u4e8e\u5339\u914d\u300cXX\u7f13\u91ca\u7247\u300d\uff09", "index.html", "function normDrugForm")
ck("A12 \u65b0\u589e\u836f\u54c1 gliclazide", "index.html", "id: 'gliclazide'")
ck("A13 \u65b0\u589e\u836f\u54c1 irbesartan", "index.html", "id: 'irbesartan'")
ck("A14 \u65b0\u589e\u836f\u54c1 telmisartan", "index.html", "id: 'telmisartan'")
ck("A15 \u65b0\u589e\u836f\u54c1 simvastatin", "index.html", "id: 'simvastatin'")
ck("A16 \u65b0\u589e\u836f\u54c1 doxofylline", "index.html", "id: 'doxofylline'")
ck("A17 \u65b0\u589e\u836f\u54c1 etoricoxib", "index.html", "id: 'etoricoxib'")
ck("A18 \u65b0\u589e\u836f\u54c1 diclofenac", "index.html", "id: 'diclofenac'")
ck("A19 \u65b0\u589e\u836f\u54c1 ureaclear", "index.html", "id: 'ureaclear'")
ck("A20 \u65b0\u589e\u836f\u54c1 ketoacid", "index.html", "id: 'ketoacid'")
ck("A21 \u65b0\u589e\u6162\u75c5 \u9aa8\u5173\u8282\u82ef", "index.html", "key: 'osteoarthritis'")
ck("A22 \u65b0\u589e\u6162\u75c5 \u819d\u9aa8\u5173\u8282\u82ef", "index.html", "key: 'knee_osteoarthritis'")
ck("A23 \u65b0\u589e\u6162\u75c5 \u6162\u6027\u652f\u6c14\u7ba1\u708e", "index.html", "key: 'chronic_bronchitis'")
ck("A24 \u65b0\u589e\u6162\u75c5 \u6162\u6027\u80c3\u708e", "index.html", "key: 'chronic_gastritis'")
ck("A25 \u7cd6\u5c3f\u75c5\u6539\u540d 2 \u578b\u7cd6\u5c3f\u75c5", "index.html", "name: '2型糖尿病'")
ck("A26 \u9ad8\u8102\u8840\u75c7\u6539\u540d\u9ad8\u8840\u8102", "index.html", "name: '高血脂'")
ck("A27 \u6162\u75c5\u522b\u540d\u652f\u6301", "index.html", "(EMC.CHRONIC_DISEASES[i].alias || [])")

print()
print("=" * 74)
print("### B. \u540c\u6b65 / \u4e00\u81f4\u6027\uff08\u7528\u6237\u4e0a\u4e2d\u4f1a\u53d1\u751f\u7684\u95ee\u9898\uff09")
print("=" * 74)
c1 = files["index.html"].count("try { markLocalWrite(); } catch (e) {}")
hitB1 = c1 >= 6
OK[0] = OK[0] and hitB1
print(("  [OK]   " if hitB1 else "  [MISS] ") + "B1 cloud write ops call markLocalWrite (x%d, need >=6)  (index.html)" % c1)
ck("B2 \u4e91\u7aef addHealth \u8865 markLocalWrite", "index.html", "addHealth: function (rec) {\n        try { markLocalWrite(); }")
ck("B3 \u4e91\u7aef addCheckin \u8865 markLocalWrite", "index.html", "addCheckin: function (rec) {\n        try { markLocalWrite(); }")
ck("B4 \u4e91\u7aef updateMed \u8865 markLocalWrite", "index.html", "updateMed: function (id, patch) {\n        try { markLocalWrite(); }")
ck("B5 \u4e91\u7aef deleteMed \u8865 markLocalWrite", "index.html", "deleteMed: function (id) {\n        try { markLocalWrite(); }")
ck("B6 \u4e91\u7aef refillMed \u8865 markLocalWrite", "index.html", "refillMed: function (id) {\n        try { markLocalWrite(); }")
ck("B7 todayPending \u8fc7\u6ee4\u5df2\u5220\u9664\u836f", "index.html", "alive[r.mid]")
ck("B8 \u5220\u9664\u836f\u540e\u53cd\u9988\u6d88\u606f", "index.html", "今日待服已取消")
hitB9 = "function saveMeds() { lsSave(KEY.meds, cache.meds); } try { markLocalWrite(); } catch (e) {}" in files["index.html"]
OK[0] = OK[0] and hitB9
print(("  [OK]   " if hitB9 else "  [MISS] ") + "B9 markLocalWrite sunk into persistence fns  (index.html)")
ck("B10 sw \u5199\u7f13\u5b58\u65f6\u5265\u6389 query", "sw.js", "u.pathname.endsWith('.js')")
ck("B11 sw activate \u6e05\u7406\u5b58\u91cf query \u53d8\u4f53", "sw.js", "u.search && (u.pathname.endsWith('.js')")
ck("B12 \u5f3a\u63d0\u9192\u5f39\u5c42 footer \u836f\u540d\u7528 esc", "index.html", "esc(n.name) + '（' + esc(n.dose) + '）'")

print()
print("=" * 74)
print("### C. \u540e\u7aef\u5b89\u5168 / \u4e0d\u53ef\u7528")
print("=" * 74)
ck("C1 \u5220\u836f\u6e05 pending \u8bb0\u5f55", "server.js", "u.records = (u.records || []).filter(function (r) {")
ck("C2 ack \u6821\u9a8c\u836f\u54c1\u5b58\u5728", "server.js", "medAlive")
ck("C3 \u89c6\u89c9\u8bc6\u522b\u63a5\u53e3", "server.js", "/api/ai/vision")
ck("C4 \u89c6\u89c9\u53cc\u901a\u9053", "server.js", "function visionUrls()")
ck("C5 \u5ba2\u5bb6\u8bdd / \u6f6e\u6d32\u8bdd\u97f3\u8272", "server.js", "'hakka': { label: '客家话（汕尾话）'")
ck("C6 \u5f3a\u533a\u5206\u8bcd\u8868", "server.js", "const DIALECT_STRONG")
ck("C7 \u7ca4\u8bdd\u8865\u7b80\u4f53", "server.js", "'点解'")
ck("C8 \u6761\u4ef6\u5199\u53ef\u964d\u7ea7", "store.js", "COND_SUPPORTED = false")
ck("C9 \u9ed8\u8ba4\u5173\u95ed\u6761\u4ef6\u5199", "store.js", "OSS_CONDITIONAL || '1'")
ck("C10 catch \u5757\u4e0d\u518d\u5f15\u7528\u8d8a\u754c\u53d8\u91cf p", "server.js", "String((req && req.url) || '')")
ck("C11 \u8fdb\u7a0b\u7ea7\u5f02\u5e38\u4fdd\u62a4", "server.js", "process.on('unhandledRejection'")
ck("C12 mutateUser \u9519\u8bef\u5305\u88c5", "server.js", "mutateUser:save failed")
ck("C13 \u5e94\u7528\u7ea7\u5b89\u5168\u4fee\u590d\u5168\u90e8\u5728", "server.js", "async function mutateUser")
ck("C14 safeNameLookup \u517c\u5bb9\u5c42", "server.js", "function safeNameLookup(u)")
ck("C15 ACK_SECRET \u4e0d\u56de\u843d CRON_TOKEN", "server.js", "process.env.ACK_SECRET || ''")
ck("C16 family \u7edf\u4e00\u660e\u6587\u4e0b\u53d1", "server.js", "family: Array.isArray(u.family) ? u.family : [],")
ck("C17 \u62d2\u7edd\u6253\u7801\u53f7\u7801\u56de\u5199", "server.js", "手机号格式不对")
ck("C18 voice \u767d\u540d\u5355", "server.js", "VOICE_ALLOW.has(String(b.voice")
ck("C19 \u8d8a\u754c\u6574\u6761\u62d2\u7edd", "server.js", "测量数值不在合理范围")
ck("C20 mg/dL \u6362\u7b97", "server.js", "nv / 18")
ck("C21 TTS deadline", "server.js", "TTS_DEADLINE")
ck("C22 ASR deadline", "server.js", "ASR_DEADLINE")
ck("C23 withTimeout \u515c\u5e95", "server.js", "function withTimeout(ms)")
ck("C24 ack sig hex \u6821\u9a8c", "server.js", "/^[a-f0-9]{32}$/.test(sig)")
ck("C25 LRU \u6dd8\u6c70", "server.js", "(a[1].t || 0) - (b[1].t || 0)")
ck("C26 \u770b\u677f\u8840\u538b\u8840\u7cd6\u5b57\u6bb5", "server.js", "bpCount")
ck("C27 store \u6761\u4ef6\u5199 412", "store.js", "oss put conflict (412)")
ck("C28 store readJSONWithMeta", "store.js", "async function readJSONWithMeta")
ck("C29 file \u6a21\u5f0f\u4e5f\u505a\u6761\u4ef6\u5199", "store.js", "file put conflict")

print()
print("=" * 74)
print("### E. 本轮审计修复（v44 收尾）")
print("=" * 74)
ck("E1 环境变量白名单含 OSS_CONDITIONAL", "server.js", "'OSS_CONDITIONAL',")
ck("E2 启动日志显示并发保护状态", "server.js", "[cfg] 并发保护: ")
ck("E3 server.on('error') -> exit", "server.js", "server.on('error', function (e) {")
ck("E4 mutateUser 脏数组归一", "server.js", "if (!Array.isArray(u[k])) u[k] = [];")
ck("E5 前端 503 retryable 自动重试", "index.html", "data.retryable && method !== 'GET'")
hitE6 = "req.url) || '').split('?')[0]" in files["server.js"] or ".split('?')[0], 'stage='" in files["server.js"]
OK[0] = OK[0] and hitE6
print(("  [OK]   " if hitE6 else "  [MISS] ") + "E6 log strips query  (server.js)")
ck("E7 打卡时间用 +8", "server.js", "cnParts().hhmm")
ck("E8 降级条件收紧", "store.js", "condUnsupported")
ck("E9 强区分词表", "server.js", "const DIALECT_STRONG")
ck("E10 wxpush 中继修复", "server.js", "const savedTok = String((user.notifySet && user.notifySet.wxpushToken)")
ck("E11 dispatch quota 事务化", "server.js", "const umQ = await mutateUser")
ck("E12 DELETE records 事务化", "server.js", "const umD = await mutateUser")
ck("E13 weekly 事务化", "server.js", "const umW = await mutateUser")
hitE14 = "'hakka': { label:" in files["server.js"]
OK[0] = OK[0] and hitE14
print(("  [OK]   " if hitE14 else "  [MISS] ") + "E14 hakka label present  (server.js)")

print()
print("=" * 74)
print("### D. \u7248\u672c\u4e0e\u5305")
print("=" * 74)
for f, pat, want in [("index.html", r"KB_BUILD\s*=\s*(\d+)", "2026102011"),
                     ("sw.js", r"const VER = '(\w+)'", "v63")]:
    m = re.search(pat, files[f])
    got = m.group(1) if m else "?"
    hit = (got == want)
    OK[0] = OK[0] and hit
    print(("  [OK]   " if hit else "  [MISS] ") + f + " \u7248\u672c = " + got + " (expect " + want + ")")

zp = os.path.join(BASE, "backend", "fc-web.zip")
try:
    z = zipfile.ZipFile(zp)
    zsrc = z.read("server.js").decode("utf-8", "replace")
    zstore = z.read("store.js").decode("utf-8", "replace")
    print("  \u5305\u5927\u5c0f = %.1f KB" % (os.path.getsize(zp) / 1024))
    for label, key, hay in [
            ("\u5305\u542b\u89c6\u89c9\u63a5\u53e3", "/api/ai/vision", zsrc),
            ("\u5305\u542b\u5ba2\u5bb6\u8bdd", "'hakka'", zsrc),
            ("\u5305\u542b\u5220\u836f\u6e05 pending", "u.records = (u.records || []).filter", zsrc),
            ("\u5305\u542b ack \u6821\u9a8c", "medAlive", zsrc),
            ("\u5305\u542b\u6761\u4ef6\u5199\u964d\u7ea7", "COND_SUPPORTED", zstore),
            ("\u5305\u542b\u8fdb\u7a0b\u4fdd\u62a4", "unhandledRejection", zsrc)]:
        hit = key in hay
        OK[0] = OK[0] and hit
        print(("  [OK]   " if hit else "  [MISS] ") + label)
except Exception as e:
    print("  [MISS] zip \u65e0\u6cd5\u8bfb\u53d6: %s" % e)
    OK[0] = False

# kb.js \u6761\u76ee\u6570
n = len(re.findall(r'"n":"([^"]+)"', files["kb.js"]))
hit = (n == 1605)
OK[0] = OK[0] and hit
print(("  [OK]   " if hit else "  [MISS] ") + "kb.js \u6761\u76ee\u6570 = %d (expect 1605)" % n)

print()
print("=" * 74)
print("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u9879\u76ee\u7f3a\u5931 \u2014\u2014 \u9700\u8981\u5904\u7406")
print("=" * 74)
sys.exit(0 if OK[0] else 1)
