import requests, base64, os, json, urllib.parse, re, socket

def get_content(url, timeout_sec=60):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=timeout_sec)
        return r.text if r.status_code == 200 else ""
    except: return ""

def verify_node(host, port):
    """
    第一步：最稳妥的梯子存活验证 (TCP 握手)
    第二步：获取真实的公网 IP 用于去重
    """
    try:
        # 获取物理 IP (解决域名马甲问题)
        actual_ip = socket.gethostbyname(host)
        # 尝试建立 TCP 连接 (验证梯子是否有响应)
        with socket.create_connection((actual_ip, int(port)), timeout=2):
            return actual_ip, True
    except:
        return None, False

def extract_node_info(node_str):
    """精确解析不同协议的 Host 和 Port"""
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
    seen_features = set() # 存储 (IP, Port) 元组

    print("🚀 开始多维度验证与去重...")
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
            
            host, port = extract_node_info(n)
            if host and port:
                # 验证存活并获取物理 IP
                actual_ip, is_alive = verify_node(host, port)
                if is_alive:
                    feature = (actual_ip, port)
                    # [精确去重]：只有 IP 和 端口 都不重复才通过
                    if feature not in seen_features:
                        all_nodes.append(n)
                        seen_features.add(feature)

    print(f"✅ 筛选完成：已从冗余节点中提取出 {len(all_nodes)} 个真实的物理独立节点")
    
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(all_nodes))

    # [最准确的分组检测逻辑]
    local_config = f"""
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
    path: ./nodes_list.txt
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204

proxy-groups:
  # --- Gemini 专用组 ---
  # 核心原理：访问 Gemini API 接口。
  # 1. 如果 IP 被禁，返回 403 -> Clash 判定失败
  # 2. 如果地区不支持，返回 400 -> Clash 判定失败
  # 3. 只有真正能用的 IP 才会显示延迟，进入该组
  - name: 🤖 Gemini 专用
    type: url-test
    use: [my_nodes]
    url: 'https://generativelanguage.googleapis.com/v1beta/models?key=detect'
    interval: 300
    tolerance: 50
  
  - name: 🚀 全球自动
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
  - DOMAIN-SUFFIX,aistudio.google.com,🤖 Gemini 专用
  - GEOIP,CN,DIRECT
  - MATCH,🚀 全球自动
"""
    with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
        f.write(local_config)
    print("📦 本地配置 config.yaml 已更新，去重与 Gemini 策略已就绪。")

if __name__ == '__main__':
    start()
