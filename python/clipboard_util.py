"""HTML 剪贴板工具 — 使用 win32clipboard"""
import win32clipboard


def set_html(html: str):
    """将 HTML 内容写入 Windows 剪贴板"""
    cf_html = win32clipboard.RegisterClipboardFormat("HTML Format")

    head_fmt = "Version:0.9\r\nStartHTML:{:08d}\r\nEndHTML:{:08d}\r\nStartFragment:{:08d}\r\nEndFragment:{:08d}\r\n"
    prefix = "<html><body>\r\n<!--StartFragment-->"
    suffix = "<!--EndFragment-->\r\n</body></html>"

    body = html.encode('utf-8')
    p = prefix.encode('utf-8')
    s = suffix.encode('utf-8')

    placeholder = head_fmt.format(0, 0, 0, 0)
    hdr_len = len(placeholder.encode('utf-8'))

    start_html = hdr_len
    start_frag = hdr_len + len(p)
    end_frag = start_frag + len(body)
    end_html = end_frag + len(s)

    header = head_fmt.format(start_html, end_html, start_frag, end_frag)
    data = header.encode('utf-8') + p + body + s

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(cf_html, data)
    win32clipboard.CloseClipboard()
