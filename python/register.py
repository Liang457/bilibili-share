import winreg
import os

# ================== 配置区域 ==================
PROTOCOL = "gkbilishare"  # 自定义协议名，如 bili://xxx

PYTHON_PATH = r"D:\Users\23386\项目\else\bilibili_tools\share\python\venv\Scripts\python.exe"
SCRIPT_PATH = r"D:\Users\23386\项目\else\bilibili_tools\share\python\main.py"
# ==============================================

def register():
    # 构建命令：解释器 脚本 "%1"（%1 是传入的完整 URL）
    # 例如：bili://video?id=123 会作为参数传给 main.py
    cmd = f'"{PYTHON_PATH}" "{SCRIPT_PATH}" "%1"'
    
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{PROTOCOL}") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{PROTOCOL} Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        
        with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
            winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd)
    
    print(f"✅ 协议 {PROTOCOL}:// 注册成功！")
    print(f"命令: {cmd}")
    
    # 生成测试文件
    test_html = f"""
    <h2>点击测试链接</h2>
    <a href="{PROTOCOL}://share/video?id=BV1xx411c7mD">测试链接1（带参数）</a><br><br>
    <a href="{PROTOCOL}://open">测试链接2（无参数）</a>
    """
    with open("test_protocol.html", "w", encoding='utf-8') as f:
        f.write(test_html)
    os.startfile("test_protocol.html")

if __name__ == "__main__":
    register()