import requests, base64, os, json, urllib.parse

def get_content(url):
    try:
        # 模拟浏览器头部，防止被屏蔽
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=30)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def start():
    # 1. 自动识别 GitHub 仓库路径
    repo = os.getenv('GITHUB_REPOSITORY', 'awwy1222/V2RayAggregator')
    
    # 2. 加载源并收割节点
    sub_list_path = './sub/sub_list.json'
    if not os.path.exists(sub_list_path):
        print("错误：找不到 sub/sub_list.json")
        return

    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在收割: {item.get('remarks', '未知源')}")
        content = get_content(item['url'])
        if content:
            try:
                # 兼容处理：尝试 Base64 解码
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

    # 3. 保存原始节点到 sub_merge.txt
    os.makedirs('./sub', exist_ok=True)
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(valid_nodes))

    # 4. 向转换 API 请求完整的 Clash 配置文件
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/sub/sub_merge.txt"
    encoded_raw_url = urllib.parse.quote(raw_url)
    
    # 使用 ACL4SSR 远程配置
    convert_api = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Full.ini"
    
    print("正在向转换服务器请求 Clash 完整配置...")
    clash_config_content = get_content(convert_api)
    
    # 5. 将结果保存为 config.yaml
    if "proxies:" in clash_config_content:
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write(clash_config_content)
        print("🚀 大功告成！已经生成完整配置文件：sub/config.yaml")
    else:
        # 修复此处的缩进错误
        with open('./sub/config.yaml', 'w', encoding='utf-8') as f:
            f.write("# 转换 API 暂时繁忙，请稍后在 Actions 中重跑\nproxies: []")
        print("⚠️ 转换失败：API 未返回内容，请检查节点数量或稍后再试。")

if __name__ == '__main__':
    start()
