#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QNAir 共享模块：源定义、抓取器、解析与格式化工具。

目录约定（参考源项目的组织方式）：每个上游一个根目录文件夹，
数据统一写入 <folder>/all.txt，首行带更新时间，一眼可见。
"""

import base64
import ipaddress
import os
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRESH_HOURS = 24          # 数据超过该时长未更新即视为不活跃，合并时剔除
BRAND = "QNAir"

BJ = timezone(timedelta(hours=8))
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
UA_CLASH = "Clash"

S5GY_URL = ("https://sub.995677.xyz/sub?uuid=00000000-0000-4000-8000-"
            "000000000000&host=example.com")
NIREVIL_URLS = [
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/Cf-ipv4.json",
    "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/Cf-ipv6.json",
]
GSLEGE_URLS = {
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/Cfxyz.txt": None,
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/JP.txt": "日本",
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/NL.txt": "荷兰",
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/US.txt": "美国",
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/DE.txt": "德国",
    "https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/SG.txt": "新加坡",
}
ZHIXUANWANG_URL = ("https://raw.githubusercontent.com/ZhiXuanWang/cf-speed-dns/"
                   "refs/heads/main/ipTop10.html")
WETEST_URL = "https://www.wetest.vip/page/cloudflare/address_v4.html"
CFYES_URL = "https://api.hostmonit.com/get_optimization_ip"
VVHAN_URL = "https://api.4ce.cn/api/bestCFIP"
UOUIN_URL = "https://api.uouin.com/cloudflare.html"

# 13 个上游：每个一个文件夹
# code = 输出模板里的上游简称，如 QNAir-LL | 香港 | 001
# mirror 类型直接抓源项目公开发布站 bestcf.pages.dev 的同步镜像，无需 Secret
SOURCES = [
    {"name": "cmliu",       "label": "CM",      "code": "CM",  "type": "mirror",
     "url": "https://bestcf.pages.dev/cmliu/all.txt",       "folder": "cmliu"},
    {"name": "cmliu2",      "label": "CM 2",    "code": "CM",  "type": "mirror",
     "url": "https://bestcf.pages.dev/cmliu2/all.txt",      "folder": "cmliu2"},
    {"name": "luoli",       "label": "洛璃",    "code": "LL",  "type": "mirror",
     "url": "https://bestcf.pages.dev/luoli/all.txt",       "folder": "luoli"},
    {"name": "lzj",         "label": "辣子鸡",  "code": "LZ",  "type": "mirror",
     "url": "https://bestcf.pages.dev/lzj/all.txt",         "folder": "lzj"},
    {"name": "mia",         "label": "Mia",     "code": "MIA", "type": "mirror",
     "url": "https://bestcf.pages.dev/xinyitang3/ipv4.txt", "folder": "mia"},
    {"name": "cfyes",       "label": "CFYes",   "code": "CFY", "type": "cfyes",       "folder": "cfyes"},
    {"name": "vvhan",       "label": "vvHan",   "code": "VH",  "type": "vvhan",       "folder": "vvhan"},
    {"name": "wetest",      "label": "WeTest",  "code": "WT",  "type": "wetest",      "folder": "wetest"},
    {"name": "uouin",       "label": "麒麟",    "code": "QL",  "type": "uouin",       "folder": "uouin"},
    {"name": "nirevil",     "label": "NiREvil", "code": "NR",  "type": "nirevil",     "folder": "nirevil"},
    {"name": "gslege",      "label": "Gslege",  "code": "GS",  "type": "gslege",      "folder": "gslege"},
    {"name": "zhixuanwang", "label": "ZhiXuan", "code": "ZX",  "type": "zhixuanwang", "folder": "zhixuanwang"},
    {"name": "s5gy",        "label": "S5公益",  "code": "S5",  "type": "s5gy",        "folder": "s5gy"},
]

# ---------------------------------------------------------------- 时间工具

def now_bj():
    return datetime.now(BJ)


def bj_compact():
    return now_bj().strftime("%m-%d %H:%M")


def bj_iso(dt=None):
    return (dt or now_bj()).isoformat()


def parse_embedded_time(text):
    """解析数据头里的北京时间（MM-DD HH:MM，默认当前年份），失败返回 None"""
    m = re.search(r"\b(\d{2})-(\d{2})\s+(\d{2}):(\d{2})\b", text or "")
    if not m:
        return None
    try:
        return datetime(now_bj().year, int(m.group(1)), int(m.group(2)),
                        int(m.group(3)), int(m.group(4)), tzinfo=BJ)
    except ValueError:
        return None


def file_header_time(path):
    """读取数据文件首行里的更新时间"""
    try:
        first = (path if isinstance(path, Path) else Path(path)
                 ).read_text(encoding="utf-8").splitlines()[0]
        return parse_embedded_time(first)
    except Exception:
        return None


def is_fresh(t):
    """文件头时间是否在 FRESH_HOURS 内"""
    if not t:
        return False
    if isinstance(t, str):
        t = parse_embedded_time(t)
    if not t:
        return False
    if t.tzinfo is None:
        t = t.replace(tzinfo=BJ)
    return now_bj() - t <= timedelta(hours=FRESH_HOURS)


# ---------------------------------------------------------------- 地区/运营商归一化

ISP_EXACT = {"CM": "移动", "CU": "联通", "CT": "电信",
             "CMCC": "移动", "CTCC": "电信", "CUCC": "联通"}

REGION_NAMES = [
    "印度尼西亚", "哈萨克斯坦", "斯里兰卡", "孟加拉国", "尼日利亚",
    "澳大利亚", "马来西亚", "阿根廷", "阿联酋", "比利时", "葡萄牙",
    "香港", "澳门", "台湾", "日本", "韩国", "新加坡", "美国", "英国",
    "德国", "法国", "荷兰", "俄罗斯", "加拿大", "土耳其", "越南",
    "菲律宾", "泰国", "印度", "奥地利", "拉脱维亚", "多哥", "中国",
    "巴西", "墨西哥", "瑞典", "瑞士", "意大利", "西班牙", "波兰",
    "芬兰", "挪威", "爱尔兰", "捷克", "乌克兰", "以色列", "蒙古",
    "柬埔寨", "缅甸", "尼泊尔", "巴基斯坦", "沙特", "卡塔尔", "埃及",
    "南非", "智利", "哥伦比亚", "秘鲁", "印尼", "新西兰", "伊拉克",
]

# 社群趣味名 → 标准地区名
FUN_NAMES = {
    "小日本儿": "日本", "港岛茶记": "香港", "港岛古惑": "香港",
    "印加坡县": "新加坡", "宝岛正妹": "台湾", "战争贩子": "美国",
    "大嘤帝国": "英国", "战斗毛子": "俄罗斯", "元首复活": "德国",
    "大马榴莲": "马来西亚", "西贡咖啡": "越南", "菲氏叶猴": "菲律宾",
    "萨瓦迪卡": "泰国", "干净卫生": "印度", "每日乳法": "法国",
    "枫叶之国": "加拿大", "烤肉火鸡": "土耳其", "土澳袋鼠": "澳大利亚",
    "风车郁金": "荷兰", "泡菜欧巴": "韩国",
}

REGION_CODE = {
    "HK": "香港", "MO": "澳门", "TW": "台湾", "JP": "日本", "KR": "韩国",
    "SG": "新加坡", "US": "美国", "GB": "英国", "UK": "英国", "DE": "德国",
    "FR": "法国", "NL": "荷兰", "RU": "俄罗斯", "CA": "加拿大",
    "AU": "澳大利亚", "TR": "土耳其", "MY": "马来西亚", "VN": "越南",
    "PH": "菲律宾", "TH": "泰国", "IN": "印度", "AT": "奥地利",
    "LV": "拉脱维亚", "TG": "多哥", "ID": "印尼", "BR": "巴西",
    "MX": "墨西哥", "SE": "瑞典", "CH": "瑞士", "IT": "意大利",
    "ES": "西班牙", "PL": "波兰", "FI": "芬兰", "NO": "挪威",
    "IE": "爱尔兰", "BE": "比利时", "CZ": "捷克", "UA": "乌克兰",
    "AE": "阿联酋", "IL": "以色列", "KZ": "哈萨克斯坦", "MN": "蒙古",
    "KH": "柬埔寨", "MM": "缅甸", "PK": "巴基斯坦", "SA": "沙特",
    "QA": "卡塔尔", "EG": "埃及", "ZA": "南非", "CL": "智利",
    "CO": "哥伦比亚", "PE": "秘鲁", "AR": "阿根廷", "CN": "中国",
    "NZ": "新西兰",
}

# Cloudflare 机场代码 → 地区
COLO_MAP = {
    "HKG": "香港", "SIN": "新加坡", "NRT": "日本", "KIX": "日本",
    "HND": "日本", "ICN": "韩国", "LAX": "美国", "SJC": "美国",
    "SFO": "美国", "SEA": "美国", "ORD": "美国", "DFW": "美国",
    "IAD": "美国", "MIA": "美国", "EWR": "美国", "MSP": "美国",
    "ATL": "美国", "DEN": "美国", "PHX": "美国", "SLC": "美国",
    "YYZ": "加拿大", "YVR": "加拿大", "LHR": "英国", "FRA": "德国",
    "AMS": "荷兰", "CDG": "法国", "SVO": "俄罗斯", "DME": "俄罗斯",
    "SYD": "澳大利亚", "MEL": "澳大利亚", "AKL": "新西兰",
    "BOM": "印度", "MAA": "印度", "DEL": "印度", "BKK": "泰国",
    "KUL": "马来西亚", "MNL": "菲律宾", "CGK": "印尼", "HAN": "越南",
    "SGN": "越南", "GRU": "巴西", "MEX": "墨西哥", "EZE": "阿根廷",
    "SCL": "智利", "BOG": "哥伦比亚", "JNB": "南非", "DXB": "阿联酋",
    "TLV": "以色列", "IST": "土耳其", "WAW": "波兰", "ARN": "瑞典",
    "ZRH": "瑞士", "MXP": "意大利", "MAD": "西班牙", "VIE": "奥地利",
    "RIX": "拉脱维亚", "LGG": "比利时",
}

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\uFE0F]+")

# 明确不算地区的标记（避免误判）
REGION_BLACKLIST = {"CF", "VPN", "CDN", "IP", "OK", "MAX", "PRO", "TEST", "NODES"}


def match_isp(text):
    """从文本中识别运营商：移动/电信/联通，识别失败返回 None"""
    if not text:
        return None
    s = str(text).strip()
    if re.search(r"移动|CMCC|China\s*Mobile", s, re.I):
        return "移动"
    if re.search(r"电信|CTCC|China\s*Telecom", s, re.I):
        return "电信"
    if re.search(r"联通|CUCC|China\s*Unicom", s, re.I):
        return "联通"
    t = re.sub(r"[^A-Za-z]", "", s).upper()
    return ISP_EXACT.get(t)


def normalize_region(text):
    """从文本中归一化出标准地区名，识别失败返回 None"""
    if not text:
        return None
    s = _EMOJI_RE.sub(" ", str(text))
    s = re.sub(r"[^\w\u4e00-\u9fff]+", " ", s, flags=re.UNICODE).strip()
    if not s:
        return None

    # 运营商文本不是地区
    if match_isp(s):
        return None

    # 中文地区名（长词优先）
    for name in sorted(REGION_NAMES, key=len, reverse=True):
        if name in s:
            return name

    # 社群趣味名
    for k, v in FUN_NAMES.items():
        if k in str(text):
            return v

    # 二~四字母代码 / 机场代码
    for tok in re.findall(r"[A-Za-z]{2,4}", s):
        t = tok.upper()
        if t in REGION_BLACKLIST:
            continue
        if t in COLO_MAP:
            return COLO_MAP[t]
        if t in REGION_CODE:
            return REGION_CODE[t]
    return None


# ---------------------------------------------------------------- IP 工具

def valid_ip(ip):
    try:
        addr = ipaddress.ip_address(ip.strip("[]"))
    except ValueError:
        return False
    if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_multicast:
        return False
    return True


def fmt_ip(ip):
    ip = ip.strip()
    if ":" in ip and not ip.startswith("["):
        return f"[{ip}]"
    return ip


# ---------------------------------------------------------------- 节点解析

class Node:
    __slots__ = ("ip", "port", "region", "isp", "code")

    def __init__(self, ip, port, region, isp, code=None):
        self.ip = ip
        self.port = port
        self.region = region or "未知"
        self.isp = isp or "未知"
        self.code = code

    @property
    def key(self):
        return f"{self.ip}:{self.port}"

    def line(self, code, idx):
        """统一输出行：IP:端口#QNAir-简称 | 地区 | 序号"""
        brand = f"{BRAND}-{code}" if code else BRAND
        return f"{fmt_ip(self.ip)}:{self.port}#{brand} | {self.region} | {idx:03d}"


UNIFIED_RE = re.compile(r"^(\[[0-9A-Fa-f:]+\]|[0-9A-Fa-f.]+):(\d{1,5})#(.+)$")
BRAND_RE = re.compile(r"^QNAir(?:-([A-Za-z0-9]+))?$")


def classify_segs(segs):
    """按顺序识别片段中的运营商与地区"""
    region, isp = None, None
    for s in segs:
        s = s.strip()
        if not s:
            continue
        if isp is None:
            i = match_isp(s)
            if i:
                isp = i
                continue
        if region is None:
            r = normalize_region(s)
            if r:
                region = r
    return region, isp


def parse_unified_line(line, default_code=None):
    """解析统一格式行：IP:端口#QNAir-简称 | 地区 | 序号"""
    m = UNIFIED_RE.match(line.strip())
    if not m:
        return None
    ip, port, rest = m.group(1), m.group(2), m.group(3)
    segs = [x.strip() for x in rest.split("|")]
    # 跳过头/尾行（含时间戳、分享语）
    joined = " ".join(segs)
    if re.search(r"\d{2}-\d{2} \d{2}:\d{2}", joined):
        return None
    if "BestCF" in joined or "pages.dev" in joined or "分享" in joined:
        return None
    if not valid_ip(ip):
        return None
    bm = BRAND_RE.match(segs[0])
    code = (bm.group(1) if bm else None) or default_code
    region, isp = classify_segs(segs[1:])
    return Node(ip.strip("[]"), port, region, isp, code)


def reparse_nodes(path, default_code=None):
    """从数据文件中重新解析节点"""
    nodes = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            node = parse_unified_line(line, default_code)
            if node:
                nodes.append(node)
    except Exception:
        pass
    return nodes


# ---------------------------------------------------------------- HTTP

def _requests_get(url, timeout, retries, headers):
    import requests
    last_err = None
    for _ in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            if r.status_code == 200 and r.text.strip():
                return r.text
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"GET 失败: {url} ({last_err})")


def _requests_post_json(url, payload, timeout, retries):
    import requests
    last_err = None
    for _ in range(retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout,
                              headers={"Content-Type": "application/json"})
            if r.status_code == 200:
                return r.json()
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"POST 失败: {url} ({last_err})")


def _scraper_get(url, timeout, retries):
    """通过 cloudscraper 抓取带 CF 防护的页面"""
    try:
        import cloudscraper
    except ImportError:
        return _requests_get(url, timeout, retries, {"User-Agent": UA_BROWSER})
    last_err = None
    for _ in range(retries + 1):
        try:
            scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "desktop": True})
            r = scraper.get(url, timeout=timeout)
            if r.status_code == 200 and r.text.strip():
                return r.text
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"scraper GET 失败: {url} ({last_err})")


def env_url(name):
    return (os.environ.get(name) or "").strip()


# ---------------------------------------------------------------- 各上游抓取器

def fetch_sub(src):
    """订阅型上游：返回已是社区通用格式的文本，原样解析"""
    url = env_url(src["env"])
    if not url:
        raise RuntimeError(f"未配置 Secret: {src['env']}")
    text = _requests_get(url, 15, 2, {"User-Agent": UA_CLASH})
    nodes = []
    for line in text.splitlines():
        node = parse_unified_line(line)
        if node:
            nodes.append(node)
    if not nodes:
        raise RuntimeError("订阅内容解析结果为空")
    return nodes


def fetch_mirror(src):
    """公开发布镜像：抓社区通用格式文本并解析。

    首行带上游自己的更新时间（如 09-06 21:33），提取出来记到 src["upstream_time"]，
    写文件时用作首行时间——这样 24h 有效性判断跟随上游的真实更新节奏。
    头/尾行（含时间戳或 BestCF/pages.dev 字样）由 parse_unified_line 自动跳过。
    """
    text = _requests_get(src["url"], 15, 2, {"User-Agent": UA_CLASH})
    nodes, header_time = [], None
    for line in text.splitlines():
        if header_time is None:
            m = re.search(r"\b(\d{2}-\d{2} \d{2}:\d{2})\b", line)
            if m:
                header_time = m.group(1)
        node = parse_unified_line(line)
        if node:
            nodes.append(node)
    if not nodes:
        raise RuntimeError("镜像内容解析结果为空")
    if header_time:
        src["upstream_time"] = header_time
    return nodes


def fetch_cfyes(_src):
    nodes = []
    line_map = {"CM": "移动", "CU": "联通", "CT": "电信"}
    for ip_type in ("v4", "v6"):
        data = _requests_post_json(CFYES_URL, {"key": "iDetkOys", "type": ip_type}, 12, 2)
        for item in data.get("info", []):
            ip = (item.get("ip") or "").strip()
            if not ip or not valid_ip(ip):
                continue
            nodes.append(Node(ip, 443, None, line_map.get(item.get("line"))))
    if not nodes:
        raise RuntimeError("CFYes 数据为空")
    return nodes


def fetch_vvhan(_src):
    import json
    res = json.loads(_requests_get(VVHAN_URL, 15, 2, {"User-Agent": UA_BROWSER}))
    if not res.get("success"):
        raise RuntimeError("vvHan API 返回失败")
    nodes = []
    data = res.get("data", {})
    for ver in ("v4", "v6"):
        for key, label in (("CM", "移动"), ("CU", "联通"), ("CT", "电信")):
            for item in data.get(ver, {}).get(key, []):
                ip = (item.get("ip") or "").strip()
                if not ip or not valid_ip(ip):
                    continue
                nodes.append(Node(ip, 443, normalize_region(item.get("colo")), label))
    if not nodes:
        raise RuntimeError("vvHan 数据为空")
    return nodes


def fetch_wetest(_src):
    html = _requests_get(WETEST_URL, 15, 2, {"User-Agent": UA_BROWSER})
    cells = re.findall(
        r'data-label="(?:线路名称|优选地址|数据中心)"[^>]*>\s*([^<\r\n]+?)\s*<', html)
    if len(cells) < 3:
        raise RuntimeError("WeTest 页面未解析到数据")
    nodes = []
    for i in range(0, len(cells) - 2, 3):
        line_name, addr, colo = cells[i], cells[i + 1], cells[i + 2]
        ip = addr.strip()
        if not valid_ip(ip):
            continue
        nodes.append(Node(ip, 443, normalize_region(colo), match_isp(line_name)))
    if not nodes:
        raise RuntimeError("WeTest 数据为空")
    return nodes


def fetch_uouin(_src):
    html = _scraper_get(UOUIN_URL, 20, 2)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr") if table else []
        cells_of = [[td.get_text(strip=True) for td in row.find_all("td")]
                    for row in rows]
    except ImportError:
        cells_of = []
        for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            cells_of.append([re.sub(r"<[^>]+>", "", c).strip()
                             for c in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.S)])
    nodes = []
    ipv4_re = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
    for cells in cells_of:
        if len(cells) < 5:
            continue
        if "IPv6" in cells[0].upper():
            continue
        m = ipv4_re.search(" ".join(cells))
        if not m or not valid_ip(m.group(0)):
            continue
        nodes.append(Node(m.group(0), 443, None, match_isp(cells[0])))
    if not nodes:
        raise RuntimeError("麒麟数据为空")
    return nodes


def fetch_nirevil(_src):
    import json
    nodes = []
    for url in NIREVIL_URLS:
        try:
            data = json.loads(_requests_get(url, 15, 2, {"User-Agent": UA_BROWSER}))
        except RuntimeError:
            continue
        line_map = {"CM": "移动", "CU": "联通", "CT": "电信"}
        for item in data:
            ip = (item.get("ip") or "").strip()
            if not ip or not valid_ip(ip):
                continue
            nodes.append(Node(ip, 443, normalize_region(item.get("colo")),
                              line_map.get(item.get("line"), match_isp(item.get("line")))))
    if not nodes:
        raise RuntimeError("NiREvil 数据为空")
    return nodes


def fetch_gslege(_src):
    nodes = []
    for url, default_region in GSLEGE_URLS.items():
        try:
            text = _requests_get(url, 15, 2,
                                 {"User-Agent": UA_BROWSER, "Cache-Control": "no-cache"})
        except RuntimeError:
            continue
        for line in text.splitlines():
            line = line.strip().replace("\r", "")
            if not line or "#" not in line:
                continue
            head, remark = line.split("#", 1)
            m = re.match(r"^(\[[0-9A-Fa-f:]+\]|[0-9A-Fa-f.]+):(\d{1,5})$", head.strip())
            if not m:
                # 无端口时补 443
                m2 = re.match(r"^(\[[0-9A-Fa-f:]+\]|[0-9A-Fa-f.]+)$", head.strip())
                if not m2:
                    continue
                ip, port = m2.group(1), "443"
            else:
                ip, port = m.group(1), m.group(2)
            if not valid_ip(ip):
                continue
            region = normalize_region(remark.split("|")[0]) or default_region
            nodes.append(Node(ip.strip("[]"), port, region, None))
    if not nodes:
        raise RuntimeError("Gslege 数据为空")
    return nodes


def fetch_zhixuanwang(_src):
    text = _requests_get(ZHIXUANWANG_URL, 15, 2, {"User-Agent": UA_BROWSER})
    nodes = []
    for tok in text.replace(",", "\n").split():
        tok = tok.strip()
        if not tok:
            continue
        m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?$", tok)
        if m and valid_ip(m.group(1)):
            nodes.append(Node(m.group(1), m.group(2) or "443", None, None))
    if not nodes:
        raise RuntimeError("ZhiXuan 数据为空")
    return nodes


def fetch_s5gy(_src):
    text = _scraper_get(S5GY_URL, 15, 3)
    if "<pre" in text:
        m = re.search(r"<pre[^>]*>(.*?)</pre>", text, re.S)
        if m:
            text = m.group(1)
    text = text.strip()
    try:
        decoded = base64.b64decode(text).decode("utf-8", "ignore")
    except Exception:
        decoded = text
    nodes = []
    for line in decoded.splitlines():
        line = line.strip()
        if not line.startswith("vless://"):
            continue
        m = re.search(r"@(\[[0-9A-Fa-f:.]+\]|[^@?/]+):(\d{1,5})\?", line)
        if not m:
            continue
        ip, port = m.group(1), m.group(2)
        raw_tag = line.split("#", 1)[1] if "#" in line else ""
        tag = urllib.parse.unquote(urllib.parse.unquote(raw_tag)).strip()
        if not tag or "s5gydl" in tag:
            continue
        if not valid_ip(ip):
            continue
        nodes.append(Node(ip.strip("[]"), port,
                          normalize_region(tag), match_isp(tag)))
    if not nodes:
        raise RuntimeError("S5公益数据为空")
    return nodes


FETCHERS = {
    "mirror": fetch_mirror,
    "sub": fetch_sub,
    "cfyes": fetch_cfyes,
    "vvhan": fetch_vvhan,
    "wetest": fetch_wetest,
    "uouin": fetch_uouin,
    "nirevil": fetch_nirevil,
    "gslege": fetch_gslege,
    "zhixuanwang": fetch_zhixuanwang,
    "s5gy": fetch_s5gy,
}


# ---------------------------------------------------------------- 路径与输出

def get_source(name):
    for s in SOURCES:
        if s["name"] == name:
            return s
    return None


def source_file(src):
    """该上游的数据文件：<folder>/all.txt"""
    return ROOT / src["folder"] / "all.txt"


def write_source_file(src, nodes, header_time=None):
    """写入该上游文件夹：首行带更新时间，正文统一格式，尾行标注来源。

    header_time：上游数据自带的更新时间（mirror 源），缺省用当前北京时间。
    """
    path = source_file(src)
    path.parent.mkdir(parents=True, exist_ok=True)
    brand = f"{BRAND}-{src['code']}"
    lines = [f"{brand} | {src['label']} | {header_time or bj_compact()}"]
    lines += [n.line(src["code"], i) for i, n in enumerate(nodes, 1)]
    lines.append(f"{brand} | {src['label']} | 数据来源公开上游接口")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
