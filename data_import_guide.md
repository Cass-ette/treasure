# 投资管理系统数据导入指南

本指南将帮助您使用数据导入工具将真实数据导入到投资管理系统中。

## 数据导入工具介绍

我们已经为您创建了一个专用的数据导入脚本 `data_import.py`，该工具允许您从CSV文件导入以下类型的数据：

- 基金数据
- 次级账户数据
- 持仓数据
- 盈亏数据

## 准备工作

1. 确保您已经创建了数据导入模板文件：
   ```
   python data_import.py --create-templates
   ```

2. 模板文件将被创建在 `data_templates` 目录下，包含以下文件：
   - `funds_template.csv` - 基金数据模板
   - `accounts_template.csv` - 次级账户数据模板
   - `positions_template.csv` - 持仓数据模板
   - `profits_template.csv` - 盈亏数据模板

## 数据格式说明

### 1. 基金数据 (funds_template.csv)

```csv
code,name,fund_type,latest_nav,nav_date
161725,招商中证白酒指数,股票型,1.5234,2023-06-15
```

- **code**: 基金代码（必填，唯一）
- **name**: 基金名称（必填）
- **fund_type**: 基金类型（如：股票型、混合型、指数型等）
- **latest_nav**: 最新净值
- **nav_date**: 净值日期（格式：YYYY-MM-DD）

### 2. 次级账户数据 (accounts_template.csv)

```csv
username,password,principal
nailoong,user123,300000.00
```

- **username**: 用户名（必填，唯一）
- **password**: 密码（必填，将自动加密存储）
- **principal**: 本金金额

### 3. 持仓数据 (positions_template.csv)

```csv
username,fund_code,shares,cost_price,created_at
nailoong,161725,10000,1.5234,2023-01-15
```

- **username**: 用户名（必须已存在于系统中）
- **fund_code**: 基金代码（必须已存在于系统中）
- **shares**: 持仓份额
- **cost_price**: 成本价
- **created_at**: 持仓创建日期（格式：YYYY-MM-DD）

### 4. 盈亏数据 (profits_template.csv)

```csv
username,date,daily_profit,cumulative_profit
nailoong,2023-06-15,1500.50,15000.75
```

- **username**: 用户名（必须已存在于系统中）
- **date**: 盈亏记录日期（格式：YYYY-MM-DD）
- **daily_profit**: 当日盈亏金额
- **cumulative_profit**: 累计盈亏金额

## 导入数据的步骤

### 1. 准备您的数据文件

- 复制模板文件并根据您的实际数据进行编辑
- 确保数据格式与模板一致
- 注意CSV文件的编码应为UTF-8

### 2. 按顺序导入数据

**推荐的导入顺序：**

1. 首先导入基金数据
2. 然后导入次级账户数据
3. 接着导入持仓数据
4. 最后导入盈亏数据

### 3. 执行导入命令

**导入基金数据：**
```
python data_import.py --import-funds 数据文件路径.csv
```

**导入次级账户数据：**
```
python data_import.py --import-accounts 数据文件路径.csv
```

**导入持仓数据：**
```
python data_import.py --import-positions 数据文件路径.csv
```

**导入盈亏数据：**
```
python data_import.py --import-profits 数据文件路径.csv
```

## 示例导入命令

```bash
# 导入基金数据
python data_import.py --import-funds data_templates/funds_template.csv

# 导入次级账户数据
python data_import.py --import-accounts data_templates/accounts_template.csv

# 导入持仓数据
python data_import.py --import-positions data_templates/positions_template.csv

# 导入盈亏数据
python data_import.py --import-profits data_templates/profits_template.csv
```

## 注意事项

1. 数据导入过程中，脚本会自动检查数据的有效性和重复性
2. 如果数据已存在，脚本会自动更新现有数据
3. 导入持仓数据前，请确保相关的用户和基金已存在于系统中
4. 导入盈亏数据前，请确保相关的用户已存在于系统中
5. 如果导入过程中出现错误，脚本会显示详细的错误信息

## 数据验证

导入完成后，您可以通过以下方式验证数据是否正确导入：

1. 启动投资管理系统：
   ```
   python simple_app.py
   ```

2. 访问 http://127.0.0.1:5000 并登录

3. 查看仪表盘，确认数据已正确显示

## 常见问题解答

**Q: 导入数据时提示"未找到用户"或"未找到基金"怎么办？**
A: 请确保您已先导入相关的用户或基金数据，然后再导入依赖这些数据的持仓或盈亏数据。

**Q: 我可以多次导入相同的数据吗？**
A: 可以，系统会自动更新现有数据，不会创建重复记录。

**Q: 导入的数据不显示在仪表盘上怎么办？**
A: 请确认您使用的是正确的数据库文件路径，并重启Flask应用后再次尝试。

如果您在数据导入过程中遇到任何问题，请检查CSV文件格式是否正确，并确保所有必填字段都已填写。