# -*- coding: utf-8 -*-
"""v44\uff1a\u4fee\u6b63\u836f\u540d/\u6162\u75c5\u540d\u7684\u7801\u4f4d\u9519\u8bef\uff0c\u5e76\u8865\u4e0a 4 \u79cd\u6162\u75c5\u3002

\u80cc\u666f\uff1a\u4e0a\u4e00\u8f6e\u7528 `\\uXXXX` \u8f6c\u4e49\u5199\u4e2d\u6587\u65f6\u6709\u51e0\u4e2a\u7801\u4f4d\u8bb0\u9519\uff08\u4f26\u2192\u4f26\u7684\u7801\u4f4d
\u5199\u6210\u4f26\u7684\u540c\u97f3\u5b57\u3001\u5766\u2192\u3001\u5766\u2192\u3001\u6d3b\u2192\u3001\u9887\u2192\u9887\u3001\u78b0\u2192\u78b0\u3001\u6d2b\u2192\u6d2b\u3001\u7a7a\u2192\u7a7a\u3001\u6930\u2192\u6930\u7b49\uff09\uff0c
\u4e14\u6d4b\u8bd5\u4e0e\u6570\u636e\u540c\u6e90\uff0c\u5bfc\u81f4\u300c\u81ea\u8bc1\u901a\u8fc7\u300d\u3002
\u73b0\u5728\u5168\u90e8\u6539\u7528**\u771f\u5b9e\u4e2d\u6587**\u5199\uff0c\u5e76\u7528\u771f\u5b9e\u4e2d\u6587\u7684\u65ad\u8a00\u6765\u9a8c\u8bc1\u3002
\u540c\u65f6\uff1akb.js \u7684 idx \u952e\u662f\u836f\u540d\u5c0f\u5199\uff0c\u6539\u540d\u5fc5\u987b**\u540c\u6b65\u6539 idx \u952e**\uff0c\u5426\u5219\u65b0\u836f\u67e5\u4e0d\u5230\u3002
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
LOG = []
FAILED = []

# ==================== \u7801\u4f4d\u8bef\u53d8\u5bf9\u7167\u8868 ====================
# (\u9519\u8bef\u5199\u6cd5, \u6b63\u786e\u5199\u6cd5)
FIX = [
    ("伦贝沙樿", "厄贝沙坦"),
    ("替米沙樿", "替米沙坦"),
    ("辛例他滙", "辛伐他汀"),
    ("依托考昞", "依托考昔"),
    ("尿毒清颇粒", "尿毒清颗粒"),
    ("苯硫酸氨水地平", "苯磺酸氨氯地平"),
    ("硕芬地平", "硝苯地平"),
    ("阿司林肠溶片", "阿司匹林肠溶片"),
    ("氢氯喆噈", "氢氯噻嗪"),
    ("缬沙沟", "缬沙坦"),
    ("单工酸异山梠酯", "单硝酸异山梨酯"),
    ("奥美拉唡", "奥美拉唑"),
    ("氯莉地平", "氨氯地平"),
]

# ==================== 1) index.html ====================
P = BASE + r"\index.html"
raw = io.open(P, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t = raw.replace("\r\n", "\n")

for bad, good in FIX:
    n = t.count(bad)
    if n:
        t = t.replace(bad, good)
        LOG.append("  OK   index: %s -> %s (%d)" % (bad, good, n))
    else:
        LOG.append("  --   index: %s \u672a\u51fa\u73b0" % bad)

# ---- \u8865 4 \u79cd\u6162\u75c5 ----
CHRONIC_NEW = """  {
    key: 'osteoarthritis', name: '骨关节炎', icon: '🦠',
    cls: ['nsaid', 'cox2', 'analgesic'],
    monitor: '负重与活动后疼痛、活动度、有无僵直、关节肿胀积液',
    tips: '非甾体抗炎药能缓解痛但会伤胃，应优先选择休息、减重、游泳等非药物措施；若同时用阿司匹林和激素类药，必须告知医生。',
    drugs: ['ibuprofen', 'diclofenac', 'etoricoxib', 'paracetamol'],
    alias: ['关节炎', '骨关节炎']
  },
  {
    key: 'knee_osteoarthritis', name: '膝骨关节炎', icon: '🦿',
    cls: ['nsaid', 'cox2', 'analgesic'],
    monitor: '上下楼时膝痛、下楼需不停坐下休息、关节是否红肿热',
    tips: '膝关节负重多，减肥、增加肌力、水温游泳很重要；上楼可用微斜梯或坐位缓冲避免膝体受力；一旦关节红得快、自发热或活动受限到尽快就医。',
    drugs: ['ibuprofen', 'diclofenac', 'etoricoxib', 'paracetamol'],
    alias: ['膝关节炎', '膝关节骨关节炎']
  },
  {
    key: 'chronic_bronchitis', name: '慢性支气管炎', icon: '🫁',
    cls: ['bronchodilator'],
    monitor: '痰性咳嗽、痰量、喘息音与动作后气短；有无发烧、痰中带血',
    tips: '平时做呼吸操练、多喝温水；屏每、烟雾、冷风是典型诱发因素；常用平喘药应在病重时按医嘱使用，不要自行加量。',
    drugs: ['doxofylline'],
    alias: ['慢性支气管炎', '老慢咳']
  },
  {
    key: 'chronic_gastritis', name: '慢性胃炎', icon: '🫄',
    cls: ['ppi', 'antacid'],
    monitor: '上腹隐痛、胃酸、烧灼、饮食后不适；大便是否带血、是否体重下降',
    tips: '抑酸药（PPI）通常在早餐前半小时服用，一次疗程之前用一次，不要随意停；避免辛辣刺激饮食、浓茶、酒精和过冷食物。',
    drugs: ['omeprazole'],
    alias: ['慢性活动性胃炎', '胃炎']
  },
"""
anchor = "  {\n    key: 'other', name: '其他基础病'"
i = t.find(anchor)
if i < 0:
    FAILED.append("other 慢病锚点未找到")
else:
    t = t[:i] + CHRONIC_NEW + t[i:]
    LOG.append("  OK   新增 4 种慢病")

# ---- 现有慢病的 drugs 挂上新药 ----
OLD_DRUGS = {
    "    drugs: ['amlodipine', 'valsartan', 'benazepril', 'metoprolol', 'hydrochlorothiazide']":
        "    drugs: ['amlodipine', 'valsartan', 'benazepril', 'metoprolol', 'hydrochlorothiazide', 'irbesartan', 'telmisartan']",
    "    drugs: ['metformin', 'acarbose', 'glimepiride']":
        "    drugs: ['metformin', 'acarbose', 'glimepiride', 'gliclazide']",
    "    drugs: ['atorvastatin']":
        "    drugs: ['atorvastatin', 'simvastatin']",
}
for o, nw in OLD_DRUGS.items():
    if t.count(o) == 1:
        t = t.replace(o, nw)
        LOG.append("  OK   drugs 关联: %s" % nw[:46])
    else:
        FAILED.append("drugs 未匹配: %s (%d)" % (o[:40], t.count(o)))

# ckd 的 drugs
m = re.search(r"(key: 'ckd'.*?\n    drugs: \[)([^\]]*)(\])", t, re.S)
if m and "'ureaclear'" not in m.group(2):
    t = t[:m.start(2)] + m.group(2).rstrip() + "', 'ureaclear', 'ketoacid" + t[m.end(2):]
    LOG.append("  OK   ckd drugs += ureaclear/ketoacid")
elif m:
    LOG.append("  --   ckd drugs 已有")

if FAILED:
    print("\n".join(LOG))
    print("FAILED: " + "; ".join(FAILED))
    sys.exit(1)

out = t.replace("\n", "\r\n") if CRLF else t
io.open(P, "w", encoding="utf-8", newline="").write(out)
LOG.append("  OK   index.html 写入")

# ==================== 2) kb.js ====================
KB = BASE + r"\kb.js"
kb = io.open(KB, encoding="utf-8").read()
for bad, good in FIX:
    if kb.count(bad):
        kb = kb.replace(bad, good)
        LOG.append("  OK   kb: %s -> %s" % (bad, good))

# idx \u952e\u540c\u6b65\uff1a\u5148\u6539 drugs \u91cc\u7684 n\uff0c\u518d\u6539 idx \u91cc\u7684\u952e
m = re.search(r"\bidx\s*:\s*\{", kb)
assert m, "idx 未找到"
ks = m.start()
k2 = kb.find("{", ks)
depth = 0
m2 = k2
while m2 < len(kb):
    if kb[m2] == "{":
        depth += 1
    elif kb[m2] == "}":
        depth -= 1
        if depth == 0:
            break
    m2 += 1
seg = kb[k2:m2 + 1]
for bad, good in FIX:
    if '"%s":' % bad.lower() in seg:
        seg = seg.replace('"%s":' % bad.lower(), '"%s":' % good.lower())
        LOG.append("  OK   idx: %s -> %s" % (bad.lower(), good.lower()))
kb = kb[:k2] + seg + kb[m2 + 1:]
io.open(KB, "w", encoding="utf-8", newline="").write(kb)
LOG.append("  OK   kb.js 写入")

print("\n".join(LOG))
