# -*- coding: utf-8 -*-
"""验证后端 loadEnv() 的 .env 解析规则。
改动 loadEnv 时请跑一遍：python test_env_parse.py"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_env(text, existing=None):
    """复刻 server.js 里 loadEnv 的解析规则（保持同步）"""
    env = dict(existing or {}); n = 0
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if (len(v) > 1 and v[0] == '"' and v[-1] == '"') or (len(v) > 1 and v[0] == "'" and v[-1] == "'"):
            v = v[1:-1]                      # 带引号：原样保留（可含空格与 #）
        else:
            h = v.find("#")
            if h >= 0:
                v = v[:h].strip()             # 无引号：# 之后是注释
        if not v:
            continue
        if k in env:
            continue                          # 环境变量优先，不被覆盖
        env[k] = v; n += 1
    return env, n

TXT = '\n# 注释行\nADMIN_PASSWORD = kb2026gate\nMANAGER_PASSWORD="带 空格的 密码#123"\nNAME_PASSWORD=\'single#quoted\'\nSPACED   =   trim-me\nHASHY=abc#def\nEMPTY=\nNOT_IN_ENV=from-file\nDASH-NOT-OK=should-skip\n中文=不该被读入\n'

CASES = [
    ("ADMIN_PASSWORD", "kb2026gate", "等号两侧空格被去掉"),
    ("MANAGER_PASSWORD", "带 空格的 密码#123", "双引号内空格与 # 原样保留"),
    ("NAME_PASSWORD", "single#quoted", "单引号内 # 原样保留"),
    ("SPACED", "trim-me", "键名与等号间多空格"),
    ("HASHY", "abc", "无引号时 # 之后视为注释"),
    ("NOT_IN_ENV", "from-file", "仅在文件中 → 应被读入"),
    ("EMPTY", None, "空值被跳过"),
    ("DASH-NOT-OK", None, "非法键名（含连字符）被跳过"),
    ("中文", None, "非 ASCII 键名被跳过"),
]

def main():
    env, _ = load_env(TXT)
    ok = True
    for k, want, desc in CASES:
        got = env.get(k)
        good = (got == want)
        print(("  PASS  " if good else "  FAIL  ") + f"{k:18s} {desc}")
        ok &= good
    env2, _ = load_env(TXT, existing={"ADMIN_PASSWORD": "from-console"})
    good = env2.get("ADMIN_PASSWORD") == "from-console"
    print(("  PASS  " if good else "  FAIL  ") + "控制台已设的值不被 .env 覆盖")
    ok &= good
    print()
    print("全部通过" if ok else "存在失败")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
