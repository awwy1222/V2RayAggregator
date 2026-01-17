import requests
import base64
import os
import json
import re

def get_content(url):
    try:
        # 设置头部信息，伪装成浏览器，防止被对方网站拦截
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.text
    except:
        return ""
    return ""

def start():
    # 1. 自动从 sub_list.json 读取开启的链接
    sub_list_path = './sub/sub_list.json'
    if not os.path.exists(sub_list_path):
        print("错误：找不到 sub/sub_list.json 文件！")
        return

    with open(sub_list_path, 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        urls = item['url'] if isinstance(item['url'], list) else [item['url']]
        for url in urls:
            print(f"正在抓取: {url}")
            content = get_content(url)
            if content:
                # 尝试 Base64 解码逻辑
                try:
                    # 处理可能存在的混淆或换行
                    pure_content = content.replace('\n', '').replace('\r', '').strip()
                    decoded = base64.b64decode(pure_content).decode('utf-8')
                    nodes = decoded.split('\n')
                except:
                    nodes = content.split('\n')
                
                # 过滤出有效协议
                count = 0
                for n in nodes:
                    n = n.strip()
                    if any(n.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"]):
                        all_nodes.append(n)
                        count += 1
                print(f"--- 成功提取 {count} 个节点")

    # 2. 去重并清洗
    valid_nodes = list(set(all_nodes))
    # 过滤掉包含广告关键词的节点
    valid_nodes = [n for n in valid_nodes if not any(word in n for word in ["广告", "官网", "频道"])]
    
    print(f"\n===== 收割任务完成 =====")
    print(f"最终总有效节点数量: {len(valid_nodes)}")

    # 3. 强制写入文件
    os.makedirs('./sub', exist_ok=True)
    
    # 保存 TXT
    final_text = "\n".join(valid_nodes[:800]) # 最多保留 800 个
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    # 保存 Base64
    with open('./sub/sub_merge_base64.txt', 'w', encoding='utf-8') as f:
        f.write(base64.b64encode(final_text.encode('utf-8')).decode('utf-8'))

    # 生成一个基础的 Clash YAML (防止你之前的 sub_convert 报错)
    yaml_head = "proxies:\n"
    # 这里只是为了保证文件不为空，如果你需要完美的 YAML 转换，
    # 可以在 Actions 跑完后用第三方转换链接转换 sub_merge.txt
    with open('./sub/sub_merge_yaml.yml', 'w', encoding='utf-8') as f:
        f.write("# 节点已更新，请直接使用外部转换器转换 sub_merge.txt\n" + yaml_head)

if __name__ == '__main__':
    start()
