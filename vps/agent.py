import urllib.request
import json
import os
import time
import subprocess

CONF_FILE = "/opt/kui/config.json"
SINGBOX_CONF_PATH = "/etc/sing-box/config.json"

with open(CONF_FILE, 'r') as f:
    env = json.load(f)

API_URL = env["api_url"]
REPORT_URL = env["report_url"]
VPS_IP = env["ip"]
TOKEN = env["token"]

def get_system_status():
    try:
        cpu = float(os.popen("top -bn1 | grep load | awk '{printf \"%.2f\", $(NF-2)}'").read().strip())
        mem = float(os.popen("free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2 }'").read().strip())
        return {"cpu": int(cpu), "mem": mem}
    except:
        return {"cpu": 0, "mem": 0}

def report_status():
    status = get_system_status()
    status["ip"] = VPS_IP
    req = urllib.request.Request(REPORT_URL, data=json.dumps(status).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

def fetch_and_apply_configs():
    req = urllib.request.Request(f"{API_URL}?ip={VPS_IP}", headers={'Authorization': TOKEN})
    try:
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read().decode('utf-8'))
        if data.get("success"):
            build_singbox_config(data["configs"])
    except Exception as e:
        pass

def build_singbox_config(kui_nodes):
    singbox_config = {
        "log": {"level": "warn"},
        "inbounds": [],
        "outbounds": [{"type": "direct", "tag": "direct"}],
        "route": {"rules": []}
    }

    for node in kui_nodes:
        if node["protocol"] == "Reality":
            singbox_config["inbounds"].append({
                "type": "vless",
                "tag": f"in-{node['id']}",
                "listen": "::",
                "listen_port": int(node["port"]),
                "users": [{"uuid": node["uuid"], "flow": "xtls-rprx-vision"}],
                "tls": {
                    "enabled": True,
                    "server_name": node["sni"],
                    "reality": {
                        "enabled": True,
                        "handshake": {"server": node["sni"], "server_port": 443},
                        "private_key": node["private_key"],
                        "short_id": [node["short_id"]]
                    }
                }
            })
        elif node["protocol"] == "VLESS":
            singbox_config["inbounds"].append({
                "type": "vless",
                "tag": f"in-{node['id']}",
                "listen": "::",
                "listen_port": int(node["port"]),
                "users": [{"uuid": node["uuid"]}]
            })
        elif node["protocol"] == "Hysteria2":
            # Hysteria2 需要证书，此处简化为自签或依赖用户预配置
            singbox_config["inbounds"].append({
                "type": "hysteria2",
                "tag": f"in-{node['id']}",
                "listen": "::",
                "listen_port": int(node["port"]),
                "users": [{"password": node["uuid"]}],
                "tls": {"enabled": True, "alpn": ["h3"]}
            })

    new_config_str = json.dumps(singbox_config, indent=2)
    old_config_str = ""
    if os.path.exists(SINGBOX_CONF_PATH):
        with open(SINGBOX_CONF_PATH, "r") as f:
            old_config_str = f.read()

    if new_config_str != old_config_str:
        with open(SINGBOX_CONF_PATH, "w") as f:
            f.write(new_config_str)
        subprocess.run(["systemctl", "restart", "sing-box"])

if __name__ == "__main__":
    while True:
        report_status()
        fetch_and_apply_configs()
        time.sleep(60)
