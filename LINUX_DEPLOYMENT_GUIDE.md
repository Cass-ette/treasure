# Linux 部署指南

## 环境准备

### 安装 Python 3.9+ 和 pip

```bash
# Ubuntu/Debian
apt update && apt install -y python3 python3-pip python3-venv

# CentOS/RHEL
yum install -y python3 python3-pip
```

### 安装 Git

```bash
# Ubuntu/Debian
apt install -y git

# CentOS/RHEL
yum install -y git
```

## 项目设置

### 获取代码

```bash
git clone <项目仓库地址>
cd treasure
```

### 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 初始化数据库

```bash
python db_init.py
python create_admin.py
```

### 启动应用

```bash
source .venv/bin/activate
python run.py
```

> 应用默认绑定 `0.0.0.0:5000`，可通过 `PORT=8000 python run.py` 修改端口。

## AI 助手配置（可选）

```bash
export DEEPSEEK_API_KEY=sk-xxx
export ANTHROPIC_API_KEY=sk-ant-xxx
```

也可在 AI 助手页面的「设置」按钮中直接配置。

## 生产环境部署（Gunicorn + Nginx）

### 安装 Gunicorn

```bash
pip install gunicorn
```

### 启动应用

```bash
gunicorn -w 4 -b 127.0.0.1:5000 "run:app"
```

### Nginx 反向代理

```bash
apt install -y nginx   # Ubuntu/Debian
```

创建配置文件 `/etc/nginx/sites-available/treasure`：

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

    location /static {
        alias /path/to/treasure/app/static;
        expires 30d;
    }
}
```

启用并重载：

```bash
ln -s /etc/nginx/sites-available/treasure /etc/nginx/sites-enabled/
nginx -t && nginx -s reload
```

## Systemd 服务管理

创建 `/etc/systemd/system/treasure.service`：

```ini
[Unit]
Description=Treasure Investment Management System
After=network.target

[Service]
User=your_user
Group=your_group
WorkingDirectory=/path/to/treasure
Environment="PATH=/path/to/treasure/.venv/bin"
ExecStart=/path/to/treasure/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "run:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start treasure
systemctl enable treasure
```

## 防火墙配置

```bash
# Ubuntu (UFW)
sudo ufw allow 5000/tcp

# CentOS (firewalld)
sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

## 公网部署安全注意事项

1. **禁用 debug 模式** — 生产环境不要使用 `debug=True`
2. **使用 HTTPS** — 通过 Nginx + Let's Encrypt 配置 SSL
3. **修改默认密码** — 登录后立即修改管理员密码
4. **设置 SECRET_KEY** — `export SECRET_KEY=你的随机密钥`

## 常见问题

### 依赖安装编译错误

```bash
apt install -y gcc g++ python3-dev
pip install pandas==1.5.3 numpy==1.24.2
```

### 数据库权限

```bash
chmod 664 instance/database.db
chown your_user:your_group instance/database.db
```

### 端口被占用

```bash
lsof -i :5000
kill -9 <PID>
# 或换端口
PORT=8000 python run.py
```

## 维护

- 备份数据库：`cp instance/database.db instance/database_backup_$(date +%Y%m%d).db`
- 查看日志：`journalctl -u treasure -f`
- 更新代码：`git pull && systemctl restart treasure`
