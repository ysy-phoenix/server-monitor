# BDAA Server Monitor

本项目使用 FastAPI 作为后端，Vue.js 作为前端，并部署在 Microsoft Azure 上的 Ubuntu 云服务器上。

> 本项目为深度体验 Cursor 的产物，90% 内容由 Cursor 生成，开发用时 6 h。

## 资源一览

- Microsoft Azure 上的 Ubuntu 1 核 1 G云服务器（来自 Student Pack）
- Cloudflare 上的域名 (eviloder.win)

## 配置流程

### 1. 域名设置

在 Cloudflare 添加一条 A 记录:
 - 类型: A
 - 名称: server
 - IPv4 地址: [Azure 服务器 IP]
 - 代理状态: 已代理 (橙色云朵)

### 2. 云服务器环境配置

1. 更新系统包:
   ```
   sudo apt update && sudo apt upgrade -y
   ```

2. 安装必要的系统依赖:
   ```
   sudo apt install -y python3-pip python3-venv nginx
   ```

3. 安装 Node.js 和 npm
   ```
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    nvm install 20
   ```

### 3. 后端设置

1. 安装 Python 依赖:
   ```
   pip install -r requirements.txt
   ```

2. 注意修改 backend/utils.py 中的 fake 信息。

3. 设置系统服务以运行后端:
   创建文件 `/etc/systemd/system/server-monitor-backend.service`:
   ```
   [Unit]
   Description=Server Monitor Backend
   After=network.target

   [Service]
   User=azureuser
   WorkingDirectory=/home/azureuser/server-monitor/backend
   ExecStart=/home/azureuser/server-monitor/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8086
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. 启动后端服务:
   ```
   sudo systemctl start server-monitor-backend
   sudo systemctl enable server-monitor-backend
   ```

### 4. 前端构建

1. 进入前端目录:
   ```
   cd frontend
   ```

2. 安装依赖:
   ```
   npm install
   ```

3. 构建前端:
   ```
   npm run build
   ```


### 5. Nginx 配置

1. 在服务器上,创建 Nginx 配置文件:
   ```
   sudo vim /etc/nginx/sites-available/server-monitor
   ```

2. 添加以下配置:
   ```nginx
   server {
       listen 80;
       server_name server.eviloder.win;

       location / {
           root /home/azureuser/server-monitor/frontend/dist;
           index index.html;
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8086;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. 启用站点配置:
   ```
   sudo ln -s /etc/nginx/sites-available/server-monitor /etc/nginx/sites-enabled/
   ```

4. 测试 Nginx 配置:
   ```
   sudo nginx -t
   ```

5. 重启 Nginx:
   ```
   sudo systemctl restart nginx
   ```

### 6. 防火墙配置

确保 Azure 安全组允许以下入站流量:
- HTTP (80)
- HTTPS (443)
- SSH (22)
- 后端 API (8086)


### 故障排除

- 检查后端日志: `sudo journalctl -u server-monitor-backend`
- 检查 Nginx 日志: `sudo tail -f /var/log/nginx/error.log`

