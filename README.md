# Bili Share - B站富文本分享工具

篡改猴插件 + Python CLI，替代B站网页端自带的分享功能，可复制标题、作者、短链和封面图（HTML 格式）。

## 版本说明

| 目录 | 语言 | 说明 |
|------|------|------|
| `js/` | JavaScript | 篡改猴(Tampermonkey)油猴脚本，替换页面分享按钮 |
| `python/` | Python | CLI 工具 + 自定义协议注册 |

## 安装

### JS 油猴脚本

[安装链接](https://github.com/Liang457/bilibili-share/raw/refs/heads/main/js/src/main.js)

> 由于使用了 B 站 API，提示「脚本试图访问跨域资源」请勾选「始终允许」。

### Python CLI

```bash
cd python
python -m venv venv
venv/Scripts/pip install -r requirements.txt
python register.py  # 注册 gkbilishare:// 协议
```

## 支持的页面类型

| 页面 | URL 格式 | 分享链接 |
|------|----------|----------|
| 普通视频 | `/video/BVxxx` | `b23.tv/BVxxx` |
| 活动页 | `/festival/...` | `b23.tv/BVxxx` |
| 番剧单集 | `/bangumi/play/ep123` | `b23.tv/ep123` |
| 番剧季度 | `/bangumi/play/ss123` | `b23.tv/ss123` |

## 支持的输入格式（Python CLI）

- `BV1xx411c7mD`
- `https://www.bilibili.com/video/BV1xx411c7mD`
- `https://b23.tv/BV1xx411c7mD`
- `https://www.bilibili.com/bangumi/play/ep1183104`
- `https://b23.tv/ss73077`
