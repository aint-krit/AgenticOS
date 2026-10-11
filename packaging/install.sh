#!/usr/bin/env bash
# AgenticOS v0.1 Alpha - Linux Installation & Deployment Script
# Target: Ubuntu 22.04 / 24.04 LTS & Debian 12

set -euo pipefail

# Always deploy from the AgenticOS project root.
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -f "requirements.txt" ] || [ ! -f "packaging/agenticos.service" ] || [ ! -d "src" ]; then
    echo "[!] Error: AgenticOS project files are missing."
    echo "[!] Run this installer from a complete AgenticOS checkout."
    exit 1
fi

echo "=================================================="
echo "    AgenticOS v0.1 Alpha - Linux Installer       "
echo "=================================================="

# Check root privileges
if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run as root (e.g. sudo ./install.sh)"
  exit 1
fi

INSTALL_DIR="/opt/agenticos"
AGENT_USER="agenticos"

# 1. Ensure required system packages
echo "[+] Checking system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl

# 2. Create service user if not exists
if ! id "$AGENT_USER" &>/dev/null; then
    echo "[+] Creating dedicated system user: $AGENT_USER"
    useradd --system --no-create-home --shell /bin/false "$AGENT_USER"
fi

# 3. Setup installation directory
echo "[+] Deploying files to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

for item in src tests docs packaging benchmarks demos requirements.txt pyproject.toml setup.py; do
    if [ -e "$PROJECT_ROOT/$item" ]; then
        cp -a "$PROJECT_ROOT/$item" "$INSTALL_DIR/"
    fi
done

mkdir -p "$INSTALL_DIR/workspace"

# 4. Create Python Virtual Environment
echo "[+] Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo "[+] Installing AgenticOS dependencies..."
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
fi

# 5. Fix permissions
echo "[+] Configuring ownership and sandboxing permissions..."
chown -R "$AGENT_USER:$AGENT_USER" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 770 "$INSTALL_DIR/workspace"

# 6. Install systemd unit
echo "[+] Installing systemd service..."
cp "$INSTALL_DIR/packaging/agenticos.service" /etc/systemd/system/agenticos.service
systemctl daemon-reload
systemctl enable agenticos.service
systemctl restart agenticos.service

echo "[+] Verifying AgenticOS service startup..."
if ! systemctl is-active --quiet agenticos.service; then
    echo "[!] AgenticOS service failed to start."
    systemctl --no-pager --full status agenticos.service || true
    journalctl -u agenticos.service -n 50 --no-pager || true
    exit 1
fi

echo "[+] AgenticOS service is active."

# 7. Create Global CLI Launcher
cat << 'EOF' > /usr/local/bin/agenticos
#!/usr/bin/env bash
set -e
INSTALL_DIR="/opt/agenticos"

if [ ! -x "$INSTALL_DIR/venv/bin/python" ]; then
    echo "[!] AgenticOS is not installed correctly at $INSTALL_DIR." >&2
    exit 1
fi

exec "$INSTALL_DIR/venv/bin/python" -m src.ui.cli "$@"
EOF
chmod 755 /usr/local/bin/agenticos

echo "=================================================="
echo " [OK] AgenticOS Installed & Started Successfully! "
echo " - Daemon Status : systemctl status agenticos"
echo " - Web Dashboard : http://localhost:8001/ui"
echo " - Terminal CLI  : agenticos"
echo "=================================================="
