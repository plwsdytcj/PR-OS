#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/wangming-workbench/projects/PR-OS"
WORKBENCH_DIR="/opt/wangming-workbench/projects/wm-cloud-server"
WORKBENCH_PUBLIC="$WORKBENCH_DIR/public"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_FILE="/opt/wangming-workbench/logs/pr-os-deploy.log"
ENV_FILE="$PROJECT_DIR/.env"
SECRETS_ENV="/opt/wangming-workbench/secrets/pr-os.env"
NGINX_SITE="/etc/nginx/sites-enabled/wm-workbench"
SERVICE_NAME="pr-os"
# Set PR_OS_PUBLIC=true when re-opening public access via deploy.sh
PR_OS_PUBLIC="${PR_OS_PUBLIC:-false}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

if [ ! -f "$PROJECT_DIR/web/server.py" ]; then
  log "ERROR: 未找到 FastAPI 应用，请先从本机同步代码到 $PROJECT_DIR"
  exit 1
fi

log "开始部署 PR-OS (FastAPI)"

cd "$PROJECT_DIR"
mkdir -p /opt/wangming-workbench/logs data/processed data/objects data/uploads

if [ ! -d "$VENV_DIR" ]; then
  log "创建 Python 虚拟环境..."
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q -U pip
pip install -q -r requirements.txt

if [ -f "$SECRETS_ENV" ]; then
  log "使用 secrets/pr-os.env"
  cp "$SECRETS_ENV" "$ENV_FILE"
elif [ ! -f "$ENV_FILE" ]; then
  log "从 .env.example 生成 .env"
  cp .env.example .env
fi

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=PR AI OS Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/python3 -m uvicorn web.server:app --host 127.0.0.1 --port 8601
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

if [ ! -f "$WORKBENCH_PUBLIC/index.html" ]; then
  log "WARN: 工作台首页未找到 ($WORKBENCH_PUBLIC/index.html)"
fi

if [ "$PR_OS_PUBLIC" = "true" ]; then
  cat > "$NGINX_SITE" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;
    root ${WORKBENCH_PUBLIC};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ ^/(api|static|login|app|creator-kit|creator|client|openclaw|showcase|cases|favicon\.ico)(/|$) {
        proxy_pass http://127.0.0.1:8601;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location /pr-os/ {
        proxy_pass http://127.0.0.1:8601/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 600s;
        proxy_buffering off;
    }

    location = /pr-os {
        return 301 /pr-os/;
    }
}
EOF
else
  cat > "$NGINX_SITE" <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;
    root ${WORKBENCH_PUBLIC};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ ^/(api|static|login|app|creator|client|openclaw|favicon\.ico|pr-os)(/|$) {
        default_type text/html;
        return 403 '<html><head><meta charset="utf-8"><title>403</title></head><body style="font-family:system-ui;max-width:480px;margin:4rem auto;padding:0 1rem;color:#333"><h1>服务未开放</h1><p>PR-OS 工作台暂不对外提供访问。</p></body></html>';
    }

    location = /pr-os {
        return 403;
    }
}
EOF
fi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

nginx -t
systemctl reload nginx

sleep 2
if curl -fsS http://127.0.0.1:8601/api/status >/dev/null; then
  log "健康检查通过"
else
  log "WARN: 本地健康检查失败，请查看 journalctl -u ${SERVICE_NAME}"
  journalctl -u "$SERVICE_NAME" -n 30 --no-pager || true
  exit 1
fi

if [ "$PR_OS_PUBLIC" = "true" ]; then
  log "部署完成（公网开放）: http://101.47.77.91/pr-os/"
else
  log "部署完成（公网已关闭）: /app /login /pr-os 对外返回 403"
fi
