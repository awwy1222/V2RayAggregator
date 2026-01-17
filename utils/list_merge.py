import requests
import base64
import os
import json

def get_content(url):
    try:
        # 设置超时，防止某个坏链接卡死整个流程
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.text
    except:
        return ""
    return ""

def start():
    # 1. 自动从 sub_list.json 读取开启的链接
    with open('./sub/sub_list.json', 'r', encoding='utf-8') as f:
        sub_list = [item for item in json.load(f) if item.get('enabled')]

    all_nodes = []
    for item in sub_list:
        urls = item['url'] if isinstance(item['url'], list) else [item['url']]
        for url in urls:
            print(f"正在直接抓取: {url}")
            content = get_content(url)
            if content:
                # 尝试简单识别：如果是 Base64 就解码，否则直接存
                try:
                    # 去掉空格和换行再解码
                    decoded = base64.b64decode(content.strip()).decode('utf-8')
                    all_nodes.append(decoded)
                except:
                    all_nodes.append(content)

    # 2. 汇总并简单清洗
    merged = "\n".join(all_nodes)
    lines = merged.split('\n')
    valid_nodes = [l.strip() for l in lines if any(l.startswith(p) for p in ["vmess://", "ss://", "ssr://", "trojan://", "vless://"])]
    
    # 去重
    valid_nodes = list(set(valid_nodes))
    print(f"成功收割有效节点数量: {len(valid_nodes)}")

    # 3. 强制写入文件
    os.makedirs('./sub', exist_ok=True)
    final_text = "\n".join(valid_nodes[:500]) # 最多留500个
    
    with open('./sub/sub_merge.txt', 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    # 生成 Base64 版
    with open('./sub/sub_merge_base64.txt', 'w', encoding='utf-8') as f:
        f.write(base64.b64encode(final_text.encode('utf-8')).decode('utf-8'))

if __name__ == '__main__':
    start()
