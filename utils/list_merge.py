import requests, base64, os, json, urllib.parse, time

def get_content(url, timeout_sec=60):
    """
    专门封装的内容抓取函数，支持自定义超时
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # 这里就是你要求的：转换请求时，设置 60 秒超时
        r = requests.get(url, headers=headers, timeout=timeout_sec)
        return r.text if r.status_code == 200 else ""
    except Exception as e:
        print(f"请求超时或出错 (设定限制为 {timeout_sec}s): {e}")
        return ""

def start():
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    
    # 1. 加载源并收割
    sub_list_path = './sub/sub_list.json'
    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在收割: {item.get('remarks', '未知源')}")
        # 抓取源的列表通常很快，默认 30 秒够了
        content = get_content(item['url'], timeout_sec=30)
        if content:
            try:
                pure_data = content.replace('\n','').replace('\r','').strip()
                decoded = base64.b64decode(pure_data).decode('utf-8')
                nodes = decoded.split('\n')
            except:
                nodes = content.split('\n')
            for n in nodes:
                n = n.strip()
                if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                    all_nodes.append(n)

    valid_nodes = list(set(all_nodes))
    print(f"\n✅ 节点收割完成：共计 {len(valid_nodes)} 个节点")

    # 2. 保存原始文本
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(valid_nodes))

    # 3. 核心：在线转换配置 (设置 60 秒超时)
    encoded_raw_url = urllib.parse.quote(raw_url)
    online_api = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini"
    
    print(f"🔄 正在尝试在线转换，已设置 60 秒超时等待...")
    
    # 【关键点】这里调用函数，传入 60 秒
    clash_config = get_content(online_api, timeout_sec=60)

    if "proxies:" in clash_config:
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config)
        print("🚀 [精修版] 在线转换成功！")
    else:
        print("⚠️ 1 分钟内未收到在线 API 响应，启用本地保底方案...")
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
  - name: 🚀 自动选择
    type: url-test
    use: [my_nodes]
  - name: 🎯 手动切换
    type: select
    use: [my_nodes]
rules:
  - GEOIP,CN,DIRECT
  - MATCH,🚀 自动选择
"""
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(local_template)
        print("📦 [本地版] 保底配置已生成！")

if __name__ == '__main__':
    start()
