import requests, base64, os, json, urllib.parse, re

def get_content(url, timeout_sec=60):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=timeout_sec)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def extract_ip_port(node_str):
    """
    极简解析：从节点链接中提取关键特征（IP/域名+端口）用于深度去重
    """
    try:
        if node_str.startswith("ss://"):
            # ss://base64(method:password@host:port)#name
            content = node_str.split("//")[1].split("#")[0]
            if "@" in content:
                host_port = content.split("@")[1]
            else:
                decoded = base64.b64decode(content + "==").decode('utf-8')
                host_port = decoded.split("@")[1]
            return host_port
        elif "://" in node_str:
            # 简单处理 vmess/trojan 等，提取 server 和 port 的关键部分
            # 这只是为了去重，不需要完美解析
            return re.search(r'@(.*?)\?', node_str).group(1) if '@' in node_str else node_str[:50]
    except:
        return node_str # 解析失败则返回原串
    return node_str

def start():
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    
    with open('./sub/sub_list.json', 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    seen_features = set() # 用于 IP 级去重

    for item in sub_list:
        print(f"正在收割: {item.get('remarks')}")
        content = get_content(item['url'], 30)
        if content:
            try:
                decoded = base64.b64decode(content.replace('\n','').replace('\r','') + "==").decode('utf-8')
                nodes = decoded.split('\n')
            except:
                nodes = content.split('\n')
            
            for n in nodes:
                n = n.strip()
                if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                    # 深度去重逻辑
                    feature = extract_ip_port(n)
                    if feature not in seen_features:
                        all_nodes.append(n)
                        seen_features.add(feature)

    print(f"\n✅ 深度去重完成：剩余 {len(all_nodes)} 个唯一节点")

    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(all_nodes))

    # 配置专用的 Gemini 规则
    # 策略：Gemini 走专门的组，该组包含美国、新加坡等可能解锁的节点
    encoded_raw_url = urllib.parse.quote(raw_url)
    online_api = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini"
    
    print(f"🔄 尝试在线转换...")
    clash_config = get_content(online_api, 60)

    if "proxies:" in clash_config:
        # 在线版由于是远程生成的，很难动态插入 Gemini 分组，但我们可以在规则里引导
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config)
    else:
        # 本地保底版：增加 Gemini 专项分组
        print("⚠️ 启用本地保底（含 Gemini 专项分组）")
        local_template = f"""
mixed-port: 7890
allow-lan: true
mode: rule
log-level: info

proxy-providers:
  my_nodes:
    type: http
    url: "{raw_url}"
    interval: 3600
    path: ./sub_merge.txt
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204

proxy-groups:
  - name: 🤖 Gemini 专用
    type: url-test
    use: [my_nodes]
    # 筛选关键词：这里你可以自定义，Clash 会在 provider 中筛选匹配的节点
    filter: "(?i)美国|US|United States|新加坡|SG|Singapore|日本|JP|Japan"
    url: 'https://gemini.google.com'
    interval: 300
  
  - name: 🚀 自动选择
    type: url-test
    use: [my_nodes]
    url: 'http://www.gstatic.com/generate_204'
    interval: 300

  - name: 🎯 手动切换
    type: select
    use: [my_nodes]

rules:
  # Gemini 域名走专用组
  - DOMAIN-SUFFIX,gemini.google.com,🤖 Gemini 专用
  - DOMAIN-KEYWORD,generativelanguage,🤖 Gemini 专用
  - DOMAIN-SUFFIX,google.com,🚀 自动选择
  - GEOIP,CN,DIRECT
  - MATCH,🚀 自动选择
"""
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(local_template)

if __name__ == '__main__':
    start()
