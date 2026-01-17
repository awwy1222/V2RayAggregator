#!/usr/bin/env python3

from sub_convert import sub_convert
from list_update import update_url
from get_subs import subs

import json
import re
import os
import yaml
from urllib import request

# 文件路径定义
Eterniy = './Eternity'
readme = './README.md'
sub_list_json = './sub/sub_list.json'
sub_merge_path = './sub/'
sub_list_path = './sub/list/'

ipv4 = r"([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})"
ipv6 = r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'

def add_valid(line):
    if (line.__contains__("ssr://") or line.__contains__("ss://")
            or line.__contains__("trojan://") or line.__contains__("vmess://")):
        return line
    return ''

class sub_merge():
    def sub_merge(url_list):
        content_list = []
        for t in os.walk(sub_list_path):
            for f in t[2]:
                f = t[0]+f
                os.remove(f)

        for (index, url_container) in enumerate(url_list):
            ids = url_list[index]['id']
            remarks = url_list[index]['remarks']
            if type(url_container['url']) == list:
                for each_url in url_container["url"]:
                    content = ''
                    print("gather server from " + each_url)
                    content += sub_convert.convert_remote(each_url, 'url', 'http://127.0.0.1:25500')
                    
                    if content == 'Url 解析错误':
                        content = sub_convert.main(each_url, 'url', 'url')
                        if content != 'Url 解析错误' and add_valid(content) != '':
                            content_list.append(content)
                    elif content != 'Url 订阅内容无法解析' and content != None:
                        if add_valid(content) != '':
                            content_list.append(content)
                    
                    file = open(f'{sub_list_path}{ids:0>2d}.txt', 'a+', encoding='utf-8')
                    file.write(str(content))
                    file.close()

        print('Merging nodes and Applying Filters...\n')
        content_list = list(filter(lambda x: x != '', "".join(content_list).split("\n")))
        content_list = list(filter(lambda x: any(x.startswith(p) for p in ["ssr://", "ss://", "trojan://", "vmess://"]), content_list))
        
        content_raw = "\n".join(content_list)
        content_yaml = sub_convert.main(content_raw, 'content', 'YAML', {'dup_rm_enabled': True, 'format_name_enabled': True})

        # --- 核心过滤逻辑：严选 ---
        yaml_proxies = content_yaml.split('\n')[1:]
        temp = list(filter(lambda x: re.search(ipv6, x) == None or re.search(ipv4, x) != None, yaml_proxies))
        black_list = ['广告', '剩余', '流量', '官网', '有效期', '到期', '限制', '超时', 'fail', '重置', '购买', '订阅']
        temp = [p for p in temp if not any(word in p for word in black_list)]
        if len(temp) > 100:
            temp = temp[:100]
        # --- 严选结束 ---

        content_yaml = 'proxies:\n' + "\n".join(temp)
        content_raw = sub_convert.yaml_decode(content_yaml)
        content_base64 = sub_convert.base64_encode(content_raw)

        write_list = [f'{sub_merge_path}/sub_merge.txt', f'{sub_merge_path}/sub_merge_base64.txt', f'{sub_merge_path}/sub_merge_yaml.yml']
        content_type = (content_raw, content_base64, content_yaml)
        for i in range(len(write_list)):
            with open(write_list[i], 'w+', encoding='utf-8') as f:
                f.write(content_type[i])
        print('Done!\n')

    def read_list(json_file, remote=False):
        with open(json_file, 'r', encoding='utf-8') as f:
            raw_list = json.load(f)
        input_list = []
        for index in range(len(raw_list)):
            if raw_list[index]['enabled']:
                urls = re.split('\|', raw_list[index]['url']) if remote == False else raw_list[index]['url']
                raw_list[index]['url'] = urls
                input_list.append(raw_list[index])
        return input_list

    def geoip_update(url):
        print('Downloading Country.mmdb...')
        try:
            request.urlretrieve(url, './utils/Country.mmdb')
            print('Success!\n')
        except:
            print('Failed!\n')

    def readme_update(readme_file='./README.md', sub_list=[]):
        print('Update README.md file...')
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            with open('./sub/sub_merge.txt', 'r', encoding='utf-8') as f:
                total_nodes = len(f.readlines())
            
            # 更新 README 中的总数和来源列表
            thanks = []
            for repo in sub_list:
                if repo.get('enabled'):
                    sub_file = f'./sub/list/{repo["id"]:0>2d}.txt'
                    amount = 0
                    if os.path.exists(sub_file):
                        with open(sub_file, 'r', encoding='utf-8') as f:
                            proxies = f.readlines()
                            amount = 0 if any(err in str(proxies) for err in ['解析错误', '无法解析']) else len(proxies)
                    thanks.append(f'- [{repo["remarks"]}]({repo["site"]}), nodes: `{amount}`\n')

            # 写入逻辑
            for i, line in enumerate(lines):
                if '### all nodes' in line:
                    if i + 1 < len(lines): lines[i+1] = f'merge nodes w/o dup: `{total_nodes}`\n'
                if '### node sources' in line:
                    # 清除旧来源并插入新来源
                    start = i + 1
                    while start < len(lines) and lines[start] != '\n':
                        lines.pop(start)
                    for link in reversed(thanks):
                        lines.insert(start, link)

            with open(readme_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print('Finish!\n')
        except Exception as e:
            print(f'README update error: {e}\n')

if __name__ == '__main__':
    # 完整流程启动
    update_url.update_main(use_airport=False, airports_id=[5], sub_list_json="./sub/sub_list.json")
    sub_merge.geoip_update('https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb')
    sub_list = sub_merge.read_list(sub_list_json)
    
    # 获取订阅（对应你原版执行的 v3 逻辑）
    subs.get_subs_v3(list(filter(lambda x: x['id'] != 5, sub_list)))
    sub_merge.readme_update(readme, sub_list)
