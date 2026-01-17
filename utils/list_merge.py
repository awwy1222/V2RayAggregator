import requests
import base64
import os
import json
import urllib.parse

def get_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=20)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

def start():
    # --- 1. 获取当前仓库信息 (用于自动生成转换链接) ---
    # 自动获取 GitHub Actions 里的环境变量
    github_repository = os.getenv('GITHUB_REPOSITORY', '你的用户名/你的仓库名')
    
    # --- 2. 抓取节点 ---
    sub_list_path = './sub/sub_list.json'
    if not os.path.exists(sub_list_path):
        print("错误：找不到 sub/sub_list.json")
        return

    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        print(f"正在横扫: {item.get('remarks', '未知源')}")
        content = get_content(item['url'])
        if content:
            # 尝试 Base64 解码提取
            try:
                # 预处理：去掉换行符
                pure_data = content.replace('\n','').replace('\r','').strip()
                decoded = base64.b64decode(pure_data).decode('utf-8')
                nodes = decoded.split('\n')
            except:
                nodes = content.split('\n')
            
            count = 0
            for n in nodes:
                n = n.strip()
                if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                    all_nodes.append(n)
                    count += 1
            print(f"--- 成功提取 {count} 个节点")

    # --- 3. 清洗与去重 ---
    valid_nodes = list(set(all_nodes))
    # 过滤明显的广告节点
    valid_nodes = [n for n in valid_nodes if "广告" not in n and "官网" not in n]
    
    print(f"\n===== 统计：总共收割有效节点 {len(valid_nodes)} 个 =====")

    # --- 4. 强制存盘 (TXT 格式) ---
    os.makedirs('./sub', exist_ok=True)
    final_text = "\n".join(valid_nodes)
    
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    # 同时生成 Base64 版本
    with open('./sub/sub_merge_base64.txt', 'w', encoding='utf-8') as f:
        f.write(base64.b64encode(final_text.encode('utf-8')).decode('utf-8'))

    # --- 5. 自动生成 Clash 订阅链接 (核心步骤) ---
    # 我们不直接生成 YAML，因为节点太多本地处理太慢且容易错
    # 我们生成一个专用的 Clash 转换链接，你直接把这个链接填进 Clash 即可
    
    raw_url = f"https://raw.githubusercontent.com/{github_repository}/master/sub/sub_merge.txt"
    encoded_raw_url = urllib.parse.quote(raw_url)
    
    # 使用顶级转换后端：支持国旗、自动分组、去重
    clash_subscribe_url = f"https://api.v1.mk/sub?target=clash&url={encoded_raw_url}&insert=false&emoji=true&list=true&tfo=false&scv=false&fdn=false&sort=false"
    
    # 把这个链接存到一个文件里，方便你以后复制
    with open('./sub/clash_url.txt', 'w', encoding='utf-8') as f:
        f.write(clash_subscribe_url)

    print("\n✅ 已生成节点列表：sub/sub_merge.txt")
    print(f"✅ 已生成 Clash 专用订阅链接，请查看：sub/clash_url.txt")
    print("-" * 30)
    print(f"直接复制这个链接到 Clash 即可：\n{clash_subscribe_url}")
    print("-" * 30)

if __name__ == '__main__':
    start()
