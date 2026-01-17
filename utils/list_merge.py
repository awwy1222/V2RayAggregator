import requests, base64, os, json, urllib.parse, re, socket

def get_content(url, timeout_sec=60):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=timeout_sec)
        return r.text if r.status_code == 200 else ""
    except: return ""

def resolve_and_check(host, port):
    """
    深度去重与初筛：通过真实IP去重，并剔除死节点。
    """
    try:
        actual_ip = socket.gethostbyname(host)
        # TCP 握手探测，只要能连通就保留，不管它能不能上 Gemini
        with socket.create_connection((actual_ip, int(port)), timeout=1.5):
            return actual_ip, True
    except:
        return None, False

def extract_info(node_str):
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
            h = host_port.split(":")[0]
            p = host_port.split(":")[1].split("/")[0]
            return h, p
    except: pass
    return None, None

def start():
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    
    with open('./sub/sub_list.json', 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    seen_features = set() 

    print("🔍 正在物理级筛选（保留所有活节点，合并重复 IP）...")
    for item in sub_list:
        content = get_content(item['url'], 20)
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
                actual_ip, is_alive = resolve_and_check(host, port)
                if is_alive:
                    feature = f"{actual_ip}:{port}"
                    if feature not in seen_features:
                        all_nodes.append(n)
                        seen_features.add(feature)

    print(f"✅ 筛选完成，共有 {len(all_nodes)} 个唯一活节点已进入池子")
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(all_nodes))

    # 生成 config.yaml：包含全量组和 Gemini 专项组
    local_config = f"""
mixed-port: 7890
allow-lan: true
mode: rule
log-level: info
ipv6: false

proxy-providers:
  my_nodes:
    type: http
    url: "https://mirror.ghproxy.com/{raw_url}"
    interval: 3600
    path: ./nodes_data.txt
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204

proxy-groups:
  # --- 1. Gemini 专项组：只在这里用专项探测 ---
  - name: 🤖 Gemini 专用
    type: url-test
    use: [my_nodes]
    url: 'https://generativelanguage.googleapis.com/v1beta/models?key=CHECK'
    interval: 300
    tolerance: 50
  
  # --- 2. 自动选择组：全量节点参与测速 ---
  - name: 🚀 全球自动
    type: url-test
    use: [my_nodes]
    url: 'http://www.gstatic.com/generate_204'
    interval: 300

  # --- 3. 手动切换组：全量节点可见 ---
  - name: 🎯 手动切换
    type: select
    use: [my_nodes]

rules:
  # 分流逻辑
  - DOMAIN-SUFFIX,gemini.google.com,🤖 Gemini 专用
  - DOMAIN-SUFFIX,generativelanguage.googleapis.com,🤖 Gemini 专用
  - DOMAIN-SUFFIX,aistudio.google.com,🤖 Gemini 专用
  - GEOIP,CN,DIRECT
  - MATCH,🚀 全球自动
"""
    with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
        f.write(local_config)
    print("🚀 配置生成成功：Gemini 已独立成组，其他节点均在全局组中保留。")

if __name__ == '__main__':
    start()
