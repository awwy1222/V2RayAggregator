import requests, base64, os, json, urllib.parse, re, socket

def get_content(url, timeout_sec=60):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=timeout_sec)
        return r.text if r.status_code == 200 else ""
    except: return ""

def check_port(host, port):
    """轻量级 TCP 端口检测：筛选掉绝对不能用的死节点"""
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except: return False

def extract_info(node_str):
    """解析节点 IP 和端口，用于去重和存活检测"""
    try:
        if node_str.startswith("ss://"):
            content = node_str.split("//")[1].split("#")[0]
            if "@" in content: host_port = content.split("@")[1]
            else:
                padding = '=' * (4 - len(content) % 4)
                decoded = base64.b64decode(content + padding).decode('utf-8', errors='ignore')
                host_port = decoded.split("@")[1] if "@" in decoded else decoded
        elif "://" in node_str:
            parts = node_str.split("@")
            if len(parts) > 1: host_port = parts[1].split("?")[0]
            else: return None, None
        
        if ":" in host_port:
            h, p = host_port.split(":")[0], host_port.split(":")[1].split("/")[0]
            return h, p
    except: pass
    return None, None

def start():
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    
    # 1. 加载源并收割
    with open('./sub/sub_list.json', 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    seen_features = set() 

    for item in sub_list:
        print(f"收割并筛选: {item.get('remarks')}")
        content = get_content(item['url'], 30)
        if not content: continue
        
        try:
            padding = '=' * (4 - len(content.strip()) % 4)
            nodes = base64.b64decode(content.strip() + padding).decode('utf-8', errors='ignore').split('\n')
        except: nodes = content.split('\n')
        
        for n in nodes:
            n = n.strip()
            if not any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]): continue
            
            host, port = extract_info(n)
            if host and port:
                feature = f"{host}:{port}"
                # [要求1] 根据 IP 和端口去重
                if feature not in seen_features:
                    # [要求2] 筛选掉不能用的（端口不通的直接踢出）
                    if check_port(host, port):
                        all_nodes.append(n)
                        seen_features.add(feature)

    print(f"✅ 筛选去重完成：剩余 {len(all_nodes)} 个可用节点")
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(all_nodes))

    # [要求4] 转换问题：先 API 转换，设置 2 分钟超时
    encoded_raw_url = urllib.parse.quote(raw_url)
    online_api = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini"
    
    print(f"🔄 正在发起在线转换，设置 120 秒超时等待...")
    clash_config = get_content(online_api, timeout_sec=120)

    # 判断 API 返回是否有效
    if "proxies:" in clash_config:
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config)
        print("🚀 [精修版] 在线转换成功！")
    else:
        # [要求4] 2 分钟不给结果，切换成本地
        print("⚠️ API 超时或失败，切换成本地保底配置...")
        # [要求3] Gemini 专属组逻辑
        local_template = f"""
mixed-port: 7890
allow-lan: true
mode: rule
log-level: info
ipv6: false

proxy-providers:
  my_nodes:
    type: http
    url: "{raw_url}"
    interval: 3600
    path: ./nodes_data.txt
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204

proxy-groups:
  - name: 🤖 Gemini 专用
    type: url-test
    use: [my_nodes]
    url: 'https://generativelanguage.googleapis.com/v1beta/models'
    interval: 300
    tolerance: 50
  
  - name: 🚀 自动选择
    type: url-test
    use: [my_nodes]
    url: 'http://www.gstatic.com/generate_204'
    interval: 300

  - name: 🎯 手动切换
    type: select
    use: [my_nodes]

rules:
  - DOMAIN-SUFFIX,gemini.google.com,🤖 Gemini 专用
  - DOMAIN-SUFFIX,generativelanguage.googleapis.com,🤖 Gemini 专用
  - DOMAIN-SUFFIX,ai.google.dev,🤖 Gemini 专用
  - GEOIP,CN,DIRECT
  - MATCH,🚀 自动选择
"""
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(local_template)
        print("📦 [本地版] 保底配置已生成！已包含 Gemini 专用探测组。")

if __name__ == '__main__':
    start()
