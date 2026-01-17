import requests, base64, os, json, urllib.parse

def get_content(url):
    try:
        # 模拟浏览器头部，防止被屏蔽
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=30)
        return r.text if r.status_code == 200 else ""
    except: return ""

def start():
    # 1. 自动识别 GitHub 仓库路径 (用于构造 Raw 链接供 API 读取)
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    
    # 2. 从 sub_list.json 加载源并收割节点
    sub_list_path = './sub/sub_list.json'
    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在收割: {item.get('remarks', '未知源')}")
        content = get_content(item['url'])
        if content:
            try:
                # 兼容处理：尝试 Base64 解码，失败则按明文处理
                pure_data = content.replace('\n','').replace('\r','').strip()
                decoded = base64.b64decode(pure_data).decode('utf-8')
                nodes = decoded.split('\n')
            except:
                nodes = content.split('\n')
            
            for n in nodes:
                n = n.strip()
                if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                    all_nodes.append(n)

    # 去重处理
    valid_nodes = list(set(all_nodes))
    total_count = len(valid_nodes)
    print(f"\n✅ 节点收割完成：共计 {total_count} 个节点")

    # 3. 保存原始节点到 sub_merge.txt (这是给 API 读的“原材料”)
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(valid_nodes))

    # 4. 【核心步骤】向转换 API 请求完整的 Clash 配置文件
    # 构造你仓库中 sub_merge.txt 的原始地址
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    encoded_raw_url = urllib.parse.quote(raw_url)
    
    # 使用 ACL4SSR 远程配置，会自动帮你分好：香港、美国、日本、自动选择等策略组
    # 这是目前最美观、最稳的转换 API
    convert_api = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini"
    
    print("正在抓取 Clash 完整配置代码...")
    clash_config_content = get_content(convert_api)
    
    # 5. 将抓取回来的配置代码保存为本地文件
    if "proxies:" in clash_config_content:
        # 保存为 config.yaml (这个就是你直接可以 Raw 的文件)
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config_content)
        print("🚀 大功告成！已经生成完整配置文件：sub/config.yaml")
    else:
        # 如果 API
