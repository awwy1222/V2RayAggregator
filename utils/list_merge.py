import requests, base64, os, json, urllib.parse, time

def get_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        # 增加超时时间到 45 秒，因为转换上千个节点比较慢
        r = requests.get(url, headers=headers, timeout=45)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def start():
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    
    # 1. 加载源并收割
    sub_list_path = './sub/sub_list.json'
    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在收割: {item.get('remarks', '未知源')}")
        content = get_content(item['url'])
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

    # 2. 保存原始节点
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(valid_nodes))

    # 3. 自动转换配置 (增加多服务器轮询)
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    encoded_raw_url = urllib.parse.quote(raw_url)
    
    # 定义多个转换后端，防止一个挂掉
    apis = [
        f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini",
        f"https://sub.id9.cc/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini",
        f"https://sub.xeton.dev/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true"
    ]
    
    clash_config_content = ""
    for api in apis:
        print(f"尝试从转换服务器获取配置: {api[:30]}...")
        clash_config_content = get_content(api)
        if "proxies:" in clash_config_content:
            print("🚀 获取配置成功！")
            break
        else:
            print("⚠️ 当前服务器忙，切换下一个...")
            time.sleep(2) # 稍微停顿一下

    # 4. 保存结果
    if "proxies:" in clash_config_content:
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config_content)
        print("✅ 已经更新完整配置文件：sub/config.yaml")
    else:
        # 如果所有服务器都挂了，保留旧文件或写个提示
        print("❌ 所有转换服务器均未响应。TXT 已更新，你可以稍后在 GitHub 手动重跑 Action。")

if __name__ == '__main__':
    start()
