# 部署指南

本文档说明如何将韩国半导体股票研究看板部署到生产环境。

## 临时预览（开发测试）

当前在Cloud Agent VM上的部署是**临时预览**，仅在VM运行期间可用。适合开发测试，不适合生产使用。

### 访问方式
- 仅限VM内部访问：`http://localhost:8000`
- VM生命周期：随Cloud Agent任务结束而停止

### 重启方法
```bash
cd /workspace/Korea-Semiconductor
.venv/bin/python -m uvicorn app.service:app --host 0.0.0.0 --port 8000 --workers 1
```

## 永久部署选项

### 1. Railway（推荐 - 有免费额度）

Railway提供免费试用额度，适合小型项目。

#### 部署步骤：

1. **注册Railway账号**
   - 访问 https://railway.app
   - 使用GitHub账号登录

2. **创建新项目**
   - 点击"New Project"
   - 选择"Deploy from GitHub repo"
   - 选择 `Tesy-oss/Korea-Semiconductor`

3. **配置环境变量**（可选）
   - `LIVE_UPDATE_SECONDS`: 3
   - `DASHBOARD_DATA_DIR`: `/app/runtime`

4. **配置启动命令**
   
   在Railway项目设置中：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.service:app --host 0.0.0.0 --port $PORT --workers 1`

5. **生成域名**
   - Railway会自动分配一个`.railway.app`域名
   - 也可以绑定自定义域名

#### 注意事项：
- Railway免费额度有限（每月$5或500小时）
- 数据库文件会存储在临时文件系统，重启后丢失
- 需要升级到持久化存储以保留数据

### 2. Render（推荐 - 有免费层）

Render提供免费Web Service层级，适合低流量应用。

#### 部署步骤：

1. **注册Render账号**
   - 访问 https://render.com
   - 使用GitHub账号登录

2. **创建Web Service**
   - Dashboard -> New Web Service
   - 连接GitHub仓库：`Tesy-oss/Korea-Semiconductor`

3. **配置设置**
   - Name: `korea-semiconductor-dashboard`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.service:app --host 0.0.0.0 --port $PORT --workers 1`

4. **环境变量**（可选）
   - 添加环境变量来自定义配置

#### 注意事项：
- 免费层服务在无活动15分钟后会休眠
- 冷启动可能需要30秒
- 免费层无持久化存储

### 3. Fly.io（适合全球访问）

Fly.io提供免费额度，支持全球边缘部署。

#### 部署步骤：

1. **安装Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **登录**
   ```bash
   fly auth login
   ```

3. **初始化应用**
   ```bash
   cd Korea-Semiconductor
   fly launch
   ```

4. **配置`fly.toml`**
   ```toml
   [build]
   
   [env]
     PORT = "8000"
   
   [[services]]
     internal_port = 8000
     protocol = "tcp"
   
     [[services.ports]]
       handlers = ["http"]
       port = 80
   
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

5. **部署**
   ```bash
   fly deploy
   ```

#### 注意事项：
- 需要信用卡验证（但不会收费，除非超额）
- 免费额度：3个VM，每个160GB出站流量/月

### 4. 自托管VPS

如需完全控制和持久化存储，可以使用VPS（需付费）。

#### 推荐服务商：
- DigitalOcean ($6/月起)
- Vultr ($6/月起)
- Linode ($5/月起)
- 腾讯云/阿里云（约¥10/月起）

#### 部署步骤：

1. **购买VPS并SSH登录**

2. **安装依赖**
   ```bash
   sudo apt update
   sudo apt install -y python3.12 python3.12-venv nginx
   ```

3. **克隆仓库**
   ```bash
   cd /opt
   sudo git clone https://github.com/Tesy-oss/Korea-Semiconductor.git
   cd Korea-Semiconductor
   ```

4. **设置虚拟环境**
   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

5. **配置systemd服务**
   
   创建 `/etc/systemd/system/korea-semi.service`:
   ```ini
   [Unit]
   Description=Korea Semiconductor Dashboard
   After=network.target
   
   [Service]
   User=www-data
   WorkingDirectory=/opt/Korea-Semiconductor
   Environment="PATH=/opt/Korea-Semiconductor/.venv/bin"
   ExecStart=/opt/Korea-Semiconductor/.venv/bin/uvicorn app.service:app --host 127.0.0.1 --port 8000 --workers 1
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **配置Nginx反向代理**
   
   创建 `/etc/nginx/sites-available/korea-semi`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **启动服务**
   ```bash
   sudo systemctl enable korea-semi
   sudo systemctl start korea-semi
   sudo ln -s /etc/nginx/sites-available/korea-semi /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

## 数据持久化

### SQLite数据库位置
- 默认：`runtime/dashboard.sqlite3`
- 包含：K线、资金流、新闻、翻译缓存

### 备份策略
应用自动在`runtime/backups/`目录创建每日备份（保留14天）。

### 生产环境建议
1. 定期备份`runtime/`目录到云存储
2. 使用外部SQLite备份工具
3. 考虑迁移到PostgreSQL（需修改代码）

## 数据源限制

### 正常工作的数据源
✅ **Naver实时行情** - 每3秒更新  
✅ **Toss资金流向** - 每30分钟更新  
✅ **K线历史数据** - 覆盖1996年至今  

### 受限的数据源
⚠️ **KIND回购数据** - 可能返回403禁止访问（取决于IP和访问频率）  
⚠️ **MyMemory翻译** - 有每日调用限制（4500字符）  

### 解决方案
1. 使用VPN或韩国服务器访问KIND
2. 升级到付费翻译API（DeepL、Google Translate）
3. 手动维护`data/title-overrides.json`提供翻译覆盖

## 监控和维护

### 健康检查端点
```bash
curl http://your-domain.com/api/health
```

### 关键指标
- `ok`: 后台任务是否运行
- `dataOk`: 数据采集是否正常
- `staleModules`: 失败或过期的模块
- `storedTradingDays`: 已存储的交易日数量

### 重启服务
- Railway/Render: 通过Dashboard重启
- Fly.io: `fly restart`
- VPS: `sudo systemctl restart korea-semi`

## 成本估算

| 平台 | 免费额度 | 付费价格 | 持久化存储 |
|------|---------|---------|-----------|
| Railway | $5/月试用 | $5/月起 | 需额外付费 |
| Render | 750小时/月 | $7/月起 | 免费层无 |
| Fly.io | 3个VM | $1.94/VM/月 | 需配置 |
| DigitalOcean | 无 | $6/月起 | 包含 |

## 常见问题

**Q: 为什么数据不更新？**  
A: 检查`/api/health`端点，查看`staleModules`字段。可能是数据源限流或网络问题。

**Q: 如何加快数据更新频率？**  
A: 设置环境变量`LIVE_UPDATE_SECONDS=1`，但要注意可能被源网站限流。

**Q: 数据会丢失吗？**  
A: Railway/Render免费层重启后会丢失。需要升级到持久化存储或使用自托管VPS。

**Q: 能否添加更多股票？**  
A: 需要修改`app/service.py`中的`STOCKS`配置，并确保数据源支持。
