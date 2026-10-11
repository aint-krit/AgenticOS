# AgenticOS Linux Integration & Packaging Guide

This guide covers the deployment, systemd integration, and boot configuration for the AgenticOS v0.1 Alpha operating system release.

## Architecture & Service Daemon
AgenticOS runs as a background service managed by `systemd`. The default service configuration binds the web server to `127.0.0.1:8001`, making it accessible locally on the host.

It exposes:
1. REST API and WebSocket endpoints on port `8001`, subject to the application's configured routes.
2. Web dashboard at `http://127.0.0.1:8001/` or `http://127.0.0.1:8001/ui`, if those routes are enabled.
3. Command-line shell through `agenticos` or `python -m src.ui.cli`.

## Fast Installation
To install on an existing Ubuntu/Debian Linux system:
```bash
sudo bash packaging/install.sh
```

## Manual Service Setup
If installing manually:
1. Copy `packaging/agenticos.service` to `/etc/systemd/system/agenticos.service`
2. Run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agenticos.service
sudo systemctl start agenticos.service
```
3. Check status:
```bash
systemctl status agenticos.service
journalctl -u agenticos.service -f
```

## ISO Customization & Autostart
To bundle into an ISO:
1. Include `agenticos.service` in the live overlay filesystem at `/etc/systemd/system/agenticos.service`.
2. Enable it by symlinking to `/etc/systemd/system/multi-user.target.wants/agenticos.service`.
3. To launch the interactive prompt shell on desktop boot, place a desktop entry in `/etc/xdg/autostart/agenticos-prompt.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=AgenticOS Prompt
Exec=gnome-terminal -- /usr/local/bin/agenticos
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```
