import requests, base64, os, json, urllib.parse

def get_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=20)
        return r.text if r.status_code == 200 else ""
    except: return ""

def start():
    # 自动识别仓库信息
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    
    # 1. 抓取所有源
    with open('./sub/sub_list.json', 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在横扫: {item['remarks']}")
        content = get_content(item['url'])
        if content:
            try:
                # 尝试Base64解码
                decoded = base64.b64decode(content.strip().replace('\n','')).decode('utf-8')
                nodes = decoded.split('\n')
            except:
                nodes = content.split('\n')
            
            for n in nodes:
                n = n.strip()
                if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                    all_nodes.append(n)

    # 2. 去重与清洗
    valid_nodes = list(set(all_nodes))
    # 简单过滤广告
    valid_nodes = [n for n in valid_nodes if "群" not in n and "广告" not in n]
    print(f"\n===== 收割完成：共计 {len(valid_nodes)} 个节点 =====")

    # 3. 保存为 TXT 供转换器读取
    os.makedirs('./sub', exist_ok=True)
    raw_text = "\n".join(valid_nodes)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write(raw_text)

    # 4. 自动生成 Clash 配置文件 (调用转换 API)
    # 构造 Raw 链接
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    # 使用支持大流量的转换后端
    convert_api = f"https://api.v1.mk/sub?target=clash&url={urllib.parse.quote(raw_url)}&insert=false&emoji=true&list=true&tfo=false&scv=false&fdn=false&sort=false"
    
    print("正在生成自动分组的 Clash 配置文件...")
    clash_yaml = get_content(convert_api)
    
    if "proxies:" in clash_yaml:
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_yaml)
        print("✅ 成功！生成了 sub/config.yaml")
    else:
        print("❌ 转换 API 忙，但 TXT 已更新，你可以手动用外部转换器。")

if __name__ == '__main__':
    start()
