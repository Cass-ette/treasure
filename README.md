# Treasure - 多账户投资管理系统

基于 Flask 的基金投资管理系统，支持多账户持仓管理、净值追踪、收益分析和 AI 智能助手。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库和管理员账户
python db_init.py
python create_admin.py

# 启动应用
# macOS 上 5000 被 AirPlay 占用；如本机运行了 TUN 代理（如 mihomo），
# 5001 也可能被劫持返回 426/403，此时换一个端口即可
HOST=127.0.0.1 PORT=5077 python run.py
```

访问 http://127.0.0.1:5077 ，默认管理员账户：`admin` / `admin123`

`HOST` 默认 `0.0.0.0`，`PORT` 默认 `5000`，按需覆盖。

## 主要功能

- **仪表盘** — 总览持仓市值、盈亏、收益率
- **基金管理** — 添加/编辑基金，自动爬取净值
- **持仓管理** — 多账户持仓记录，成本与市值追踪
- **投资报告** — 收益走势、K 线图、持仓分布
- **图片识别** — OCR 识别基金截图，快速导入持仓
- **AI 分析助手** — 基于投资数据的智能问答（支持 DeepSeek / Claude 双模型）
- **多账户体系** — 主账户 + 次级账户，分成协议管理
- **净值自动更新** — 每日 15:30 定时爬取最新净值
- **筹码分布估算** — 使用日线换手率递推，可切换三角/均匀分布与旧版衰减模型；[模型说明](docs/chip-model.md)
- **股票筛选** — 基于公开行情快照按市场、价格、涨跌幅、换手率、成交额、PE、PB 和市值筛选

## AI 助手配置

支持通过环境变量或页面内设置配置 API Key：

```bash
export DEEPSEEK_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
```

也可在 AI 助手页面点击「设置」按钮直接配置，无需重启。

## 界面设计

前端不依赖组件库的默认外观，`app/static/css/style.css` 里维护了一套设计 token：

- **中性色**偏冷灰（`--color-bg` / `--color-surface` / `--color-raised`），文字三级（`--color-text` / `-secondary` / `-muted`）
- **一个强调色** `--color-accent`（teal），只用在主操作、当前导航和图表里"最重要的那条线"
- **红绿只表示盈亏**，且随 `data-color-mode` 在 A 股/国际配色之间切换
- **数字是签名细节**：金额、净值、收益率全部走 `font-mono` + `tabular-nums`，表格数字列右对齐（`.num`）
- 圆角按层级：控件 8、卡片 12；动效统一 `cubic-bezier(0.22, 1, 0.36, 1)`，只过渡颜色/背景/边框/透明度

图表配色与 token 对齐：饼图用"强调色 + 灰阶"、图例直接带百分比；K 线图的现价线用强调色、成本线用灰虚线、坐标轴和 tooltip 走同一套灰色。

写新页面时沿用 `.page-header` / `.kpi-card` / `.data-table` / `.section-title` / `.chart-box` 这几个结构类，不要重新发明一套。

## 项目结构

```
app/
├── models/          # 数据模型（User, Fund, Position, Profit 等）
├── routes/          # 路由蓝图（auth, dashboard, funds, positions, ai 等）
├── services/        # 业务逻辑（计算、爬虫、定时任务）
├── templates/       # Jinja2 模板
├── static/          # 前端资源（CSS, JS）
├── config.py        # 配置
└── extensions.py    # Flask 扩展实例
run.py               # 应用入口
tests/               # 测试用例
```

## 开发

```bash
# 运行测试
pytest tests/

# 生成模拟数据（可选）
python generate_mock_data.py
```
