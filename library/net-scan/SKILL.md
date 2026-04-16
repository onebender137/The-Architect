# Network Scanner (OpenClaw)

A lightweight, multi-threaded subnet and port scanner built using Python's standard `socket` and `subprocess` libraries. No external dependencies required.

## Capabilities
- Automatically detects the local IP and assumes a `/24` subnet for discovery.
- Scans the subnet for active hosts using `ping`.
- Performs TCP port scans on discovered hosts for common services.

## Usage
```bash
python3 -c '
import socket
import threading
import subprocess
import os
from queue import Queue

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def ping_host(host):
    # Use ping -c 1 -W 1 for Linux/WSL
    res = subprocess.call(["ping", "-c", "1", "-W", "1", host],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res == 0

def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except:
        return False

def worker_discovery(q, active_hosts):
    while not q.empty():
        host = q.get()
        if ping_host(host):
            print(f"[+] Found active host: {host}")
            active_hosts.append(host)
        q.task_done()

local_ip = get_local_ip()
subnet = ".".join(local_ip.split(".")[:-1]) + "."
print(f"[*] Local IP: {local_ip} | Scanning subnet: {subnet}0/24")

active_hosts = []
discovery_queue = Queue()
for i in range(1, 255):
    discovery_queue.put(subnet + str(i))

threads = []
for _ in range(20):
    t = threading.Thread(target=worker_discovery, args=(discovery_queue, active_hosts))
    t.daemon = True
    t.start()
    threads.append(t)

discovery_queue.join()

COMMON_PORTS = [22, 80, 443, 8080]
for host in active_hosts:
    print(f"[*] Scanning ports on {host}...")
    for port in COMMON_PORTS:
        if scan_port(host, port):
            print(f"  [!] {host}:{port} is OPEN")

print(f"[*] Scan complete. Found {len(active_hosts)} active hosts.")
'
```

## Source
- Custom OpenClaw Implementation.
- Designed for subnet discovery without `scapy` or `nmap` dependencies.
