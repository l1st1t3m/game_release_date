import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def fetch_all_games():
    """
    依次请求 202501 ~ 202512 的页面，解析并返回所有游戏信息列表。
    """
    # 设置请求头，使用 identity 防止返回压缩导致乱码
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "identity",  # 避免返回压缩
        "Referer": "https://ku.gamersky.com/release/ps5_202503/",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive"
    }

    all_games = []

    for month in range(1, 13):
        month_str = f"{month:02d}"
        url = f"https://ku.gamersky.com/release/ps5_2025{month_str}/"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'  # 强制按 UTF-8 解析
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 提取游戏列表（根据你给出的选择器）
                game_items = soup.select('ul.PF li.lx1')
                for item in game_items:
                    game = {}
                    title_element = item.select_one('div.tit a')
                    if not title_element:
                        continue
                    game['name'] = title_element.get_text(strip=True)
                    game['link'] = title_element.get('href', '')

                    # 发行日期处理
                    release_date_element = item.select_one('div.txt')
                    if release_date_element:
                        release_date_text = release_date_element.get_text(strip=True).replace('发行日期：', '')
                    else:
                        release_date_text = ''

                    # 检查发行日期格式
                    if re.match(r'\d{4}-\d{2}-\d{2}', release_date_text):
                        game['release_date'] = release_date_text
                    else:
                        # 如果格式不是YYYY-MM-DD，尝试解析为YYYY年MM月并设置为当月1日
                        match = re.match(r'(\d{4})年(\d{1,2})月', release_date_text)
                        if match:
                            year = match.group(1)
                            month_ = match.group(2).zfill(2)
                            game['release_date'] = f"{year}-{month_}-01"
                        else:
                            # 如果无法解析，设置为默认日期
                            game['release_date'] = "2025-03-01"

                    # 游戏类型
                    game_type_element = item.select_one('div.txt a[href^="http://ku.gamersky.com/sp/"]')
                    game['type'] = game_type_element.get_text(strip=True) if game_type_element else '未知类型'

                    # 详细信息链接
                    more_link = item.select_one('div.more a')
                    game['more_link'] = more_link['href'] if more_link else ''

                    all_games.append(game)

                print(f"成功解析：{url}，共找到 {len(game_items)} 条游戏信息")
            else:
                print(f"请求 {url} 失败，状态码：{response.status_code}")
        except Exception as e:
            print(f"处理 {url} 时出错：{e}")

    return all_games

def write_ics(games, output_path):
    """
    将抓取到的游戏列表转换为 ICS 格式并写入 output_path。
    """
    # 生成ICS文件头
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gamersky//PS5 Game Release Schedule//CN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:PS5游戏发售表
X-WR-TIMEZONE:Asia/Shanghai
"""

    for idx, game in enumerate(games, start=1):
        uid = f"game_{idx}@gamersky.com"
        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        try:
            dtstart = datetime.strptime(game['release_date'], "%Y-%m-%d").strftime("%Y%m%d")
        except ValueError:
            dtstart = "20250301"  # 若解析失败，给个默认值

        description = f"类型：{game['type']}; 详细信息：{game['more_link']}"

        ics_event = f"""
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART;VALUE=DATE:{dtstart}
SUMMARY:{game['name']}
DESCRIPTION:{description}
END:VEVENT
"""
        ics_content += ics_event

    ics_content += """
END:VCALENDAR
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ics_content)

def main():
    # 确保保存ICS的目录存在
    if not os.path.exists('./ics'):
        os.makedirs('./ics')

    # 1. 抓取并解析所有月份的游戏数据
    all_games = fetch_all_games()

    # 2. 将结果写入 ICS 文件
    output_ics_path = './ics/game_release.ics'
    write_ics(all_games, output_ics_path)
    print(f"已生成 {output_ics_path} 文件，共包含 {len(all_games)} 条游戏信息。")

if __name__ == "__main__":
    main()