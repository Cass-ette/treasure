# Treasure - 多账户投资管理系统

基于 Flask 的基金投资管理系统，支持多账户持仓管理、净值追踪、收益分析和 AI 智能助手。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库和管理员账户
python db_init.py
python create_admin.py

# 启动应用（macOS 需用 5001 端口，5000 被 AirPlay 占用）
PORT=5001 python run.py
```

访问 http://127.0.0.1:5001 ，默认管理员账户：`admin` / `admin123`

## 主要功能

- **仪表盘** — 总览持仓市值、盈亏、收益率
- **基金管理** — 添加/编辑基金，自动爬取净值
- **持仓管理** — 多账户持仓记录，成本与市值追踪
- **投资报告** — 收益走势、K 线图、持仓分布
- **图片识别** — OCR 识别基金截图，快速导入持仓
- **AI 分析助手** — 基于投资数据的智能问答（支持 DeepSeek / Claude 双模型）
- **多账户体系** — 主账户 + 次级账户，分成协议管理
- **净值自动更新** — 每日 15:30 定时爬取最新净值

## AI 助手配置

支持通过环境变量或页面内设置配置 API Key：

```bash
export DEEPSEEK_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
```

也可在 AI 助手页面点击「设置」按钮直接配置，无需重启。

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
