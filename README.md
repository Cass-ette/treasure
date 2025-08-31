# 投资管理系统

## 项目状态说明

经过开发和演进，本项目已将 `simple_app.py` 作为**正式版本**使用，原有的模块化应用（`app/run.py`）已被弃用。

这一决定是基于以下原因：
- `simple_app.py` 包含了所有必要的功能，并且已经在实际使用中稳定运行
- 模块化版本存在一些历史遗留问题，导致无法正常启动
- 简化版应用使用了更直接的代码组织方式，易于维护和扩展

## 如何启动应用

### Windows环境

```powershell
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次运行）
python create_admin.py

# 生成模拟数据（可选）
python generate_mock_data.py

# 启动应用
python simple_app.py
```

### Linux环境

```bash
# 为脚本添加执行权限
chmod +x start_app.sh

# 运行启动脚本
./start_app.sh

# 然后选择选项1启动应用
```

## 主要功能

- 基金管理（添加、编辑、更新净值）
- 账户管理（主账户和次级账户）
- 持仓管理
- 盈亏统计
- 基金净值自动爬取和更新
- 前三十日净值平均值计算

## 访问方式

应用启动后，可以通过以下方式访问：
- 本地访问：http://127.0.0.1:5000
- 局域网访问：http://您的IP地址:5000

## 默认账户

- 管理员账户：username=admin, password=admin123
- 次级账户：username=user1/user2/user3, password=user123

## 注意事项

1. 首次登录后请修改管理员密码
2. 应用默认配置为绑定到所有网卡地址（0.0.0.0:5000）
3. 如果在公网环境中使用，请确保配置了适当的安全措施
4. 定时任务会在每日15:30自动更新基金净值