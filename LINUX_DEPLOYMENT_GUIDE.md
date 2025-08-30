# Linux 部署指南

本指南将帮助您在 Linux 环境中部署投资管理系统，简化部署过程并解决可能遇到的问题。

## 环境准备

### 1. 安装 Python 3.9+ 和 pip

```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip python3-venv

# CentOS/RHEL
yum install -y python3 python3-pip
```

### 2. 安装 Git（如果需要克隆代码）

```bash
# Ubuntu/Debian
apt install -y git

# CentOS/RHEL
yum install -y git
```

## 项目设置

### 1. 获取项目代码

```bash
# 克隆代码（如果使用Git）
git clone <项目仓库地址>
cd treasure

# 或者直接上传项目文件到服务器
```

### 2. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 安装基础依赖
pip install --upgrade pip
pip install flask sqlalchemy flask-login

# 安装数据处理相关依赖
pip install pandas numpy

# 如果使用基金数据爬取功能
pip install akshare requests beautifulsoup4
```

> 注意：如果遇到 akshare 或 pandas 安装问题，可以尝试指定版本：
> ```bash
> pip install akshare==1.7.52 pandas==1.5.3 numpy==1.24.2
> ```

## 数据库设置

### 1. 初始化数据库

```bash
# 确保已激活虚拟环境
python db_init.py
```

### 2. 创建管理员账户

```bash
python create_admin.py
```

## 部署模式选择

### 简化版部署（推荐用于快速启动）

简化版包含基本功能，依赖较少，适合快速部署：

```bash
# 直接运行简化版应用
source .venv/bin/activate
python simple_app.py
```

> 注意：应用默认配置为绑定到所有网卡地址（0.0.0.0），可以通过公网IP访问。

### 模块化版本部署

模块化版本功能更完整，但依赖较多：

```bash
# 安装所有依赖
pip install -r requirements.txt

# 启动应用
python -m app.run
```

## 公网访问安全注意事项

如果您计划将应用部署到公网环境，请务必注意以下安全措施：

1. **不要在公网环境中使用debug=True模式**：
   - debug模式会暴露应用的敏感信息
   - 会允许执行任意代码（通过调试器）

2. **配置防火墙**：
   如果您要允许公网访问，请确保服务器防火墙已开放5000端口。以下是常见Linux发行版的防火墙配置方法：
   
   ```bash
   # Ubuntu/Debian (使用UFW防火墙)
   sudo ufw allow 5000/tcp  # 允许所有IP访问5000端口
   # 或者只允许特定IP访问
   # sudo ufw allow from 您的IP地址 to any port 5000
   sudo ufw status  # 检查防火墙状态
   sudo ufw enable  # 如果防火墙未启用，请启用它
   
   # CentOS/RHEL (使用firewalld)
   sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
   sudo firewall-cmd --reload
   ```

3. **使用HTTPS**：
   - 通过Nginx配置SSL证书
   - 使用Let's Encrypt等免费证书服务

4. **修改默认密码**：
   - 登录系统后立即修改管理员密码
   - 为所有用户设置强密码

5. **生产环境推荐使用Nginx+Gunicorn组合**：
   - 提供更好的安全性和性能

## 使用 Gunicorn + Nginx 进行生产环境部署

### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

### 2. 使用 Gunicorn 启动应用

```bash
# 启动简化版应用
gunicorn -w 4 -b 0.0.0.0:5000 "simple_app:app"

# 或启动模块化应用
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

### 3. 配置 Nginx 反向代理

```bash
# 安装 Nginx
apt install -y nginx  # Ubuntu/Debian
yum install -y nginx  # CentOS/RHEL

# 创建 Nginx 配置文件
nano /etc/nginx/sites-available/treasure
```

在配置文件中添加：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件配置（可选）
    location /static {
        alias /path/to/treasure/app/static;
        expires 30d;
    }
}
```

启用配置并重启 Nginx：

```bash
ln -s /etc/nginx/sites-available/treasure /etc/nginx/sites-enabled/
nginx -t
nginx -s reload
```

## 使用 Systemd 管理服务

### 1. 创建 Systemd 服务文件

```bash
nano /etc/systemd/system/treasure.service
```

添加以下内容：

```ini
[Unit]
Description=Investment Management System
After=network.target

[Service]
User=your_user
Group=your_group
WorkingDirectory=/path/to/treasure
Environment="PATH=/path/to/treasure/.venv/bin"
ExecStart=/path/to/treasure/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "simple_app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. 启动并启用服务

```bash
systemctl daemon-reload
systemctl start treasure
systemctl enable treasure
```

## 定时任务配置

如果需要设置基金净值自动更新的定时任务，可以使用 Linux 的 cron：

```bash
# 编辑当前用户的 crontab
crontab -e

# 添加每天 15:30 执行更新的任务
30 15 * * * cd /path/to/treasure && .venv/bin/python -c "from simple_app import update_all_funds_nav; update_all_funds_nav()"
```

## 常见问题及解决方案

### 1. 依赖安装问题

**症状**：安装 pandas 或 akshare 时出现编译错误

**解决方法**：
- 安装系统依赖：`apt install -y gcc g++ python3-dev libpq-dev`
- 指定较低版本：`pip install pandas==1.5.3 numpy==1.24.2`

### 2. 数据库连接问题

**症状**：无法连接到 SQLite 数据库

**解决方法**：
- 确保数据库文件有正确的读写权限：`chmod 664 database.db`
- 检查文件所有权：`chown your_user:your_group database.db`

### 3. 端口被占用

**症状**：启动时提示端口已被占用

**解决方法**：
- 查找占用端口的进程：`lsof -i :5000`
- 杀死占用进程：`kill -9 <PID>`
- 或使用其他端口：`gunicorn -w 4 -b 0.0.0.0:8000 "simple_app:app"`

## 访问应用

部署完成后，可以通过以下方式访问应用：
- 直接访问：http://服务器IP:5000
- 通过 Nginx：http://your_domain.com

默认账户：
- 管理员账户：username=admin, password=admin123
- 次级账户：username=user1/user2/user3, password=user123

## 维护建议

1. 定期备份数据库：`cp database.db database_backup_$(date +%Y%m%d).db`
2. 定期更新依赖：`pip install --upgrade -r requirements.txt`
3. 监控应用日志：`journalctl -u treasure -f` (使用 systemd 时)

祝您使用愉快！