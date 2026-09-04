# QNAir

Cloudflare 优选 IP 聚合。定时抓取一批公开接口的优选数据，把失效的来源剔掉，统一格式后发布。页面展示各来源的更新地址和更新时间，数据文件可以直接给客户端用。

页面托管在 Cloudflare Pages，数据靠 GitHub Actions 定时更新，不需要自己的服务器。

## 部署

1. 把这个仓库 Fork 或者导入到你的 GitHub 账号下
2. 到仓库的 Actions 页面手动触发一次 Update QNAir，确认 `data/` 目录正常生成了数据
3. Cloudflare Dashboard → Workers & Pages → Pages → 连接到 Git，选中这个仓库
   - 构建命令：留空
   - 输出目录：`/`
4. 第一次部署完成后就不用管了。之后 Actions 每 3 小时更新一次数据，每次提交都会自动触发 Pages 重新部署

### 可选：订阅来源

有 5 个来源的地址需要自己填，在仓库 Settings → Secrets and variables → Actions 里配置：

| Secret | 来源 |
|---|---|
| CMLIU_URL | CM |
| CMLIU2_URL | CM 2 |
| LUOLI_URL | 洛璃 |
| LZJ_URL | 辣子鸡 |
| XINYITANG3_URL | Mia |

不配置也能跑，只是这几个来源没有数据，其余来源不受影响。

## 数据

每个上游一个文件，放在 `data/raw/` 下，格式统一为 `IP:端口#QNAir-简称 | 地区 | 序号`：

```
104.16.10.10:443#QNAir-LL | 香港 | 001
104.16.10.11:443#QNAir-LL | 香港 | 002
```

- 末尾是三位序号，每个上游的文件各自从 001 开始重排
- 识别不出的地区用"未知"占位
- `QNAir-all.txt` 是全部上游合并去重的结果，序号连续编号，每行保留它原本来自哪个上游的简称

上游简称对照（页面"简称"列也会显示）：

| 简称 | 上游 | 简称 | 上游 |
|---|---|---|---|
| CM | CM / CM 2 | WT | WeTest |
| LL | 洛璃 | QL | 麒麟 |
| LZ | 辣子鸡 | NR | NiREvil |
| MIA | Mia | GS | Gslege |
| CFY | CFYes | ZX | ZhiXuan |
| VH | vvHan | S5 | S5公益 |

## 更新机制

- 每 3 小时跑一次，来源分组轮流抓取，不会频繁请求同一批接口
- 抓取失败的来源自动回退到 24 小时内的旧数据
- 超过 24 小时拿不到任何数据的来源会被剔除
- 手动触发工作流时可以勾选"强制更新全部上游"，忽略轮换一次抓完

## 本地运行

```bash
pip install requests cloudscraper beautifulsoup4
python scripts/update.py
```

本地跑默认全部实抓，想模拟轮换可以加环境变量 `QNAIR_ROTATE_GROUPS=3`。
