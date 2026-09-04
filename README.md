# QNAir 优选IP

精简版 Cloudflare 优选IP 聚合项目（源自 [wanwushequ/cfyxip](https://github.com/wanwushequ/cfyxip) 的思路）：

- ✅ 只保留**优选IP**功能（剔除 WARP / 随机地区 / 优选域名 / CIDR / 工具箱等）
- ✅ 只接入**活跃上游**：数据更新在 **24 小时内**的接口才保留，失效来源自动剔除
- ✅ 统一格式输出：`IP:端口#QNAir | <地区> | <运营商>`，缺省用 `未知` 填充
- ✅ GitHub Actions 每 3 小时自动抓取更新，无需人工干预

## 数据格式

**合并输出** `data/QNAir-all.txt`（序号格式）：

```
001-QNAir | 香港 | 移动
002-QNAir | 奥地利 | 未知
003-QNAir | 未知 | 移动
```

**上游明细** `data/raw/*.txt`（含完整 IP，可直接导入客户端）：

```
104.16.10.10:443#QNAir | 香港 | 电信
152.53.67.190:443#QNAir | 奥地利 | 未知
```

- `地区`：从上游备注归一化（含社群趣味名、国旗 emoji、国家代码、机场代码），无法识别 → `未知`
- `运营商`：移动 / 电信 / 联通，上游未提供 → `未知`

## 输出文件（data/）

| 文件 | 说明 |
|---|---|
| `QNAir-all.txt` | 合并去重，序号格式 `序号-QNAir | 地区 | 运营商` |
| `raw/*.txt` | 各上游明细，含完整 `IP:端口#QNAir | 地区 | 运营商` |
| `sources.json` | 上游活跃状态元数据（前端状态栏使用） |
| `state.json` | 各上游最近成功抓取时间（24h 活跃判定依据） |

## 活跃上游（13 个）

| 上游 | 类型 | 抓取方式 |
|---|---|---|
| CM (cmliu) | 订阅 | Secret `CMLIU_URL` |
| CM 2 (cmliu2) | 订阅 | Secret `CMLIU2_URL` |
| 洛璃 | 订阅 | Secret `LUOLI_URL` |
| 辣子鸡 (lzj) | 订阅 | Secret `LZJ_URL` |
| Mia (xinyitang3) | 订阅 | Secret `XINYITANG3_URL` |
| CFYes | API | api.hostmonit.com |
| vvHan | API | api.4ce.cn |
| WeTest | 网页 | wetest.vip |
| 麒麟 (uouin) | 网页 | api.uouin.com（cloudscraper） |
| NiREvil | JSON | GitHub Raw |
| Gslege | 文本 | GitHub Raw |
| ZhiXuan | 文本 | GitHub Raw |
| S5公益 | 订阅 | sub.995677.xyz（cloudscraper） |

**部署到你的 GitHub 后**，在 `Settings → Secrets and variables → Actions` 按需配置
上表 5 个订阅型 Secret（与源项目同名即可；未配置的来源会被自动跳过，不影响其它上游）。

新增/删除上游：编辑 `scripts/update.py` 里的 `SOURCES` 列表即可。

## 部署

1. 将本仓库推送到你的 GitHub
2. （可选）配置上表中的 Secrets
3. 手动触发一次 Actions 工作流 `Update QNAir`，确认 `data/` 生成成功
4. Cloudflare Dashboard → Workers & Pages → 创建 Pages → **连接到 Git**，选择本仓库
   - 构建命令：留空
   - 输出目录：`/`（根目录）
5. 绑定自定义域名（可选），完成

之后 Pages 每次工作流提交数据都会自动重新部署，前端 `index.html` 会实时展示
活跃上游状态与各文件链接。

## 本地运行

```bash
pip install requests cloudscraper beautifulsoup4
python scripts/update.py
```
