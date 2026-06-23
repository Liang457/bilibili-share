import re
import sys
from urllib.parse import urlencode

import requests
from clipboard_util import set_html

# 自定义 User-Agent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"
API_HEADERS = {
    'User-Agent': UA,
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
}

def extract_short_url(text: str) -> str | None:
    """
    从文本中提取 b23.tv 短链接（返回完整的 URL）。
    匹配格式如：b23.tv/xxxxxx 或 https://b23.tv/xxxxxx
    """
    # 匹配 b23.tv/ 后跟字母数字，可能带路径参数
    pattern = r'https?://b23\.tv/[\w]+|b23\.tv/[\w]+'
    match = re.search(pattern, text)
    if match:
        url = match.group(0)
        # 如果没有协议头，补上 https://
        if not url.startswith('http'):
            url = 'https://' + url
        return url
    return None

def extract_bv_number(text: str) -> str | None:
    """从文本中提取 B 站视频 BV 号（BV 后跟 10 个字母数字）"""
    pattern = r'BV[a-zA-Z0-9]{10}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def resolve_from_short_url(short_url: str) -> dict | None:
    """
    访问短链接，跟随重定向，从最终 URL 中提取 video/PGC 信息。
    返回 {'type': 'bv', 'id': '...'} 或 {'type': 'ep', 'id': '...'} 或 {'type': 'ss', 'id': '...'}
    失败返回 None。
    """
    headers = {'User-Agent': UA}
    try:
        resp = requests.get(short_url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"短链接访问失败: {e}")
        return None

    final_url = resp.url

    # 方法1：检测最终 URL 是否为番剧页 (PGC: ep 或 ss)
    pgc = re.search(r'/bangumi/play/(ep|ss)(\d+)', final_url)
    if pgc:
        return {'type': pgc.group(1), 'id': pgc.group(2)}

    # 方法2：从最终 URL 中提取 BV 号
    bv = extract_bv_number(final_url)
    if bv:
        return {'type': 'bv', 'id': bv}

    # 方法3：从响应 HTML 中的链接提取 BV 号
    href_pattern = r'<a\s+[^>]*href="([^"]+)"'
    for href in re.findall(href_pattern, resp.text, re.IGNORECASE):
        bv = extract_bv_number(href)
        if bv:
            return {'type': 'bv', 'id': bv}

    return None

def fetch_video_info(bv: str) -> dict:
    """
    调用 B 站 API 获取视频信息。
    返回包含 title, owner, pic 的字典，失败时抛出异常。
    """
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv}"
    try:
        resp = requests.get(api_url, headers=API_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")

    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(f"API 返回非 JSON 格式: {e}")

    if data.get('code') != 0:
        msg = data.get('message', '未知错误')
        raise RuntimeError(f"API 返回错误 (code {data.get('code')}): {msg}")

    info = data.get('data')
    if not info:
        raise RuntimeError("API 返回数据缺失")

    return {
        'title': info.get('title', '无标题'),
        'owner': info.get('owner', {}).get('name', '未知作者'),
        'pic': info.get('pic', '')
    }

def fetch_bangumi_info(**kwargs) -> dict:
    """
    调用 PGC API 获取番剧/电影/电视剧信息。
    支持 ep_id=xxx 或 season_id=xxx。
    返回包含 title, pic 的字典，失败时抛出异常。
    """
    api_url = f"https://api.bilibili.com/pgc/view/web/season?{urlencode(kwargs)}"
    try:
        resp = requests.get(api_url, headers=API_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"网络请求失败: {e}")

    try:
        data = resp.json()
    except ValueError as e:
        raise RuntimeError(f"API 返回非 JSON 格式: {e}")

    if data.get('code') != 0:
        msg = data.get('message', '未知错误')
        raise RuntimeError(f"API 返回错误 (code {data.get('code')}): {msg}")

    result = data.get('result')
    if not result:
        raise RuntimeError("API 返回数据缺失")

    # ponytail: title 拼接番剧名+集标题，cover 作封面
    season_title = result.get('season_title', '')
    ep_title = result.get('title', '')
    display_title = f"{season_title} - {ep_title}" if (season_title and ep_title) else (season_title or ep_title or '无标题')

    return {
        'title': display_title,
        'pic': result.get('cover', '')
    }

def build_html_clip(bv: str, title: str, owner: str, pic_url: str) -> str:
    """生成要放入剪贴板的 HTML 内容"""
    short_url = f"https://b23.tv/{bv}"
    html = (
        f"「{title}」——{owner}<br>"
        f"<a href='{short_url}'>{short_url}</a><br>"
        f"<img src='{pic_url}' alt='{title}'>"
    )
    return html

def handle_pgc(pgc_type: str, pgc_id: str, input_text: str):
    """处理番剧/电影/电视剧：调 API、拼 HTML、写剪贴板。不返回（成功 exit，失败 sys.exit）。"""
    param = {'ep_id': pgc_id} if pgc_type == 'ep' else {'season_id': pgc_id}
    try:
        info = fetch_bangumi_info(**param)
    except RuntimeError as e:
        print(f"获取番剧信息失败: {e}")
        sys.exit(1)

    print(f"标题: {info['title']}")
    print(f"封面: {info['pic']}")

    short_url = f"https://b23.tv/{pgc_type}{pgc_id}"
    html_content = f"「{info['title']}」<br><a href='{short_url}'>{short_url}</a><br><img src='{info['pic']}' alt='{info['title']}'>"

    try:
        set_html(html_content)
        print("✅ 番剧信息已复制到剪贴板（HTML格式）。")
    except Exception as e:
        print(f"❌ 剪贴板写入失败: {e}")
        sys.exit(1)

def main():
    # 处理命令行参数：如果提供了参数，则将其作为输入文本；否则交互式输入
    if len(sys.argv) > 1:
        input_text = ' '.join(sys.argv[1:])
        print(f"使用命令行参数作为输入: {input_text}")
    else:
        print("B站视频信息提取助手")
        print("请输入分享链接或BV号：")
        input_text = sys.stdin.readline().strip()
        if not input_text:
            print("输入为空，程序退出。")
            sys.exit(1)

    # 步骤0：检测是否为番剧/电影/电视剧 URL (PGC: ep 或 ss)
    pgc_match = re.search(r'/bangumi/play/(ep|ss)(\d+)', input_text)
    if pgc_match:
        print(f"检测到番剧/电影/电视剧 ({pgc_match.group(0)})")
        handle_pgc(pgc_match.group(1), pgc_match.group(2), input_text)
        return

    # 步骤1：尝试从输入中提取短链接
    short_url = extract_short_url(input_text)
    bv = None

    if short_url:
        print(f"检测到短链接: {short_url}")
        print("正在解析短链接...")
        resolved = resolve_from_short_url(short_url)
        if resolved:
            if resolved['type'] in ('ep', 'ss'):
                print(f"通过短链接解析到番剧 ({resolved['type']}{resolved['id']})")
                handle_pgc(resolved['type'], resolved['id'], input_text)
                return
            else:
                bv = resolved['id']
                print(f"通过短链接解析到 BV 号: {bv}")
        else:
            print("短链接解析失败，将尝试直接从原始输入提取 BV 号。")

    # 步骤2：如果未通过短链接获得 BV 号，则直接从输入文本提取
    if not bv:
        bv = extract_bv_number(input_text)
        if bv:
            print(f"从输入中提取到 BV 号: {bv}")

    # 步骤3：若仍未获得 BV 号，报错退出
    if not bv:
        print("错误：未能从输入中识别出有效的 BV 号或番剧 ID。")
        print("支持的格式示例：")
        print("  - BV1xx411c7mD")
        print("  - https://www.bilibili.com/video/BV1xx411c7mD")
        print("  - https://b23.tv/xxxxxx")
        print("  - https://www.bilibili.com/bangumi/play/ep1183104")
        print("  - https://b23.tv/ss73077")
        sys.exit(1)

    # 获取视频信息
    try:
        info = fetch_video_info(bv)
    except RuntimeError as e:
        print(f"获取视频信息失败: {e}")
        sys.exit(1)

    print(f"标题: {info['title']}")
    print(f"UP主: {info['owner']}")
    print(f"封面: {info['pic']}")

    # 生成 HTML 内容并放入剪贴板
    html_content = build_html_clip(bv, info['title'], info['owner'], info['pic'])
    try:
        set_html(html_content)
        print("✅ 视频信息已复制到剪贴板（HTML格式）。")
    except Exception as e:
        print(f"❌ 剪贴板写入失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()