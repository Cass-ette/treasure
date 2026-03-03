# 数据导入指南

使用 `data_import.py` 从 CSV 文件导入基金、账户、持仓和盈亏数据。

## 准备模板

```bash
python data_import.py --create-templates
```

模板文件生成在 `data_templates/` 目录下。

## 数据格式

### 基金数据 (funds_template.csv)

```csv
code,name,fund_type,latest_nav,nav_date
161725,招商中证白酒指数,股票型,1.5234,2023-06-15
```

### 次级账户数据 (accounts_template.csv)

```csv
username,password,principal
nailoong,user123,300000.00
```

### 持仓数据 (positions_template.csv)

```csv
username,fund_code,shares,cost_price,created_at
nailoong,161725,10000,1.5234,2023-01-15
```

### 盈亏数据 (profits_template.csv)

```csv
username,date,daily_profit,cumulative_profit
nailoong,2023-06-15,1500.50,15000.75
```

## 导入（按顺序）

```bash
# 1. 基金
python data_import.py --import-funds data_templates/funds_template.csv

# 2. 账户
python data_import.py --import-accounts data_templates/accounts_template.csv

# 3. 持仓（依赖基金和账户）
python data_import.py --import-positions data_templates/positions_template.csv

# 4. 盈亏（依赖账户）
python data_import.py --import-profits data_templates/profits_template.csv
```

## 验证

导入后启动应用检查：

```bash
python run.py
```

访问仪表盘确认数据已正确显示。

## 注意事项

- CSV 编码使用 UTF-8
- 持仓/盈亏导入前，确保对应的基金和账户已导入
- 重复导入会更新已有数据，不会创建重复记录
