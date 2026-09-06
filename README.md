# QNAir

Cloudflare 优选 IP 聚合。定时抓取一批公开接口的优选数据，统一格式后发布。页面展示各来源的更新地址和更新时间，数据文件可以直接给客户端用。

页面托管在 Cloudflare Pages，数据靠 GitHub Actions 定时更新，不需要自己的服务器。

## 目录结构

每个数据源一个独立的文件夹，文件夹里的 `all.txt` 首行就是最近的更新时间，进仓库一眼就能看到谁在什么时候更新过：

```
QNAir/
├── cmliu/all.txt          CM
├── cmliu2/all.txt         CM 2
├── luoli/all.txt          洛璃（简称 LL）
├── lzj/all.txt            辣子鸡（简称 LZ）
├── mia/all.txt            Mia
├── cfyes/all.txt          CFYes（简称 CFY）
├── vvhan/all.txt          vvHan（简称 VH）
├── wetest/all.txt         WeTest（简称 WT）
├── uouin/all.txt          麒麟（简称 QL）
├── nirevil/all.txt        NiREvil（简称 NR）
├── gslege/all.txt         Gslege（简称 GS）
├── zhixuanwang/all.txt    ZhiXuan（简称 ZX）
├── s5gy/all.txt           S5公益（简称 S5）
├── QNAir-all.txt          全部上游合并去重后的结果
├── sources.json           各上游状态汇总（页面读取）
└── scripts/
    ├── common.py          共享的抓取与解析代码
    ├── fetch.py           抓取单个上游
    └── merge.py           扫描所有文件夹做合并
```

`all.txt` 的内容长这样，第一行的 `09-06 21:00` 就是这份数据的更新时间：

```
QNAir-LL | 洛璃 | 09-06 21:00
107.191.53.228:443#QNAir-LL | 日本 | 001
107.191.53.84:443#QNAir-LL | 日本 | 002
...
QNAir-LL | 洛璃 | 数据来源公开上游接口
```

- 格式统一为 `IP:端口#QNAir-简称 | 地区 | 序号`，序号三位，每个上游各自从 001 开始
- 识别不出的地区用"未知"占位
- `QNAir-all.txt` 是合并去重结果，序号连续编号，每行带来源简称

## 工作流

`.github/workflows/` 下每个数据源一个工作流，各管各的：

- `cmliu.yml` 到 `s5gy.yml`：每 3 小时抓取对应的上游，刷新它自己的文件夹并提交。抓取失败时不动旧文件，旧数据照样可用
- `merge.yml`：每 3 小时在抓取之后运行一次，扫描全部文件夹——首行时间在 24 小时以内的算活跃来源，进合并结果；超过 24 小时没更新的自动剔除（文件夹里的数据保留，恢复更新后自动回归）

所有工作流都支持在 Actions 页面手动触发。

## 部署

1. Fork 或者导入这个仓库到你的 GitHub 账号
2. 到 Actions 页面手动触发各个工作流，确认各文件夹正常生成数据
3. Cloudflare Dashboard → Workers & Pages → Pages → 连接到 Git，选中这个仓库
   - 构建命令：留空
   - 输出目录：`/`
4. 之后不用管。Actions 会持续更新数据，每次提交都会触发 Pages 重新部署

### 可选：订阅来源

有 5 个来源的地址需要自己填，在仓库 Settings → Secrets and variables → Actions 里配置：

| Secret | 来源 | 对应工作流 |
|---|---|---|
| CMLIU_URL | CM | cmliu.yml |
| CMLIU2_URL | CM 2 | cmliu2.yml |
| LUOLI_URL | 洛璃 | luoli.yml |
| LZJ_URL | 辣子鸡 | lzj.yml |
| XINYITANG3_URL | Mia | mia.yml |

不配置也能跑，只是这几个来源没有数据，其余来源不受影响。

## 本地运行

```bash
pip install requests cloudscraper beautifulsoup4

# 抓取单个上游
python scripts/fetch.py luoli

# 扫描全部文件夹，重新合并
python scripts/merge.py
```
