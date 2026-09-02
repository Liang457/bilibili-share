// ==UserScript==
// @name         Bilibili 富文本分享
// @namespace    https://cool-gk.cn/
// @version      0.8
// @description  从分享链接提取 BV 号/av 号并复制视频信息（HTML 格式）——替换原分享按钮行为
// @author       cool-gk
// @match        https://www.bilibili.com/video/*
// @match        https://www.bilibili.com/festival/*
// @match        https://www.bilibili.com/bangumi/play/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @grant        GM_registerMenuCommand
// @grant        GM_setClipboard
// @grant        GM_getValue
// @grant        GM_setValue
// ==/UserScript==

(function () {
    'use strict';

    const NOTIFY_KEY = 'notifyEnabled';

    /**
     * 是否开启消息通知弹窗
     */
    function isNotificationEnabled() {
        return GM_getValue(NOTIFY_KEY, true);
    }

    /**
     * 统一通知出口：始终写入控制台；仅当开关开启时额外弹出通知
     * @param {string} text - 通知内容
     */
    function showNotification(text) {
        console.info('[Bilibili 富文本分享]', text);
        if (!isNotificationEnabled()) return;
        GM_notification({
            text: text,
            title: 'Bilibili 富文本分享',
            timeout: 3000
        });
    }

    /**
     * 切换消息通知开关
     */
    function toggleNotification() {
        const enabled = !isNotificationEnabled();
        GM_setValue(NOTIFY_KEY, enabled);
        showNotification(enabled ? '消息通知已开启' : '消息通知已关闭（仍会写入控制台）');
    }

    // 注册油猴菜单命令（手动触发）
    GM_registerMenuCommand("📤 富文本分享视频", doShare);
    GM_registerMenuCommand(isNotificationEnabled() ? '🔔 消息通知：开启（点击关闭）' : '🔔 消息通知：关闭（点击开启）', toggleNotification);

    /**
     * 核心分享函数：获取视频信息并复制 HTML 到剪贴板
     */
    async function doShare() {
        try {
            const url = window.location.href;

            // 检测番剧/电影/电视剧页面 (PGC)
            const pgcMatch = url.match(/\/bangumi\/play\/(ep|ss)(\d+)/);
            if (pgcMatch) {
                const param = pgcMatch[1] === 'ep' ? `ep_id=${pgcMatch[2]}` : `season_id=${pgcMatch[2]}`;
                const info = await fetchBangumiInfo(param);
                if (!info) {
                    showNotification('获取番剧信息失败，请检查网络');
                    return;
                }
                const shortUrl = `https://b23.tv/${pgcMatch[1]}${pgcMatch[2]}`;
                const html = `「${info.title}」<br><a href="${shortUrl}">${shortUrl}</a><br><img src="${info.pic}" alt="${info.title}">`;
                GM_setClipboard(html, 'html');
                showNotification('番剧信息已复制到剪贴板（HTML 格式）');
                return;
            }

            const BV_number = extractBV(url);
            const avNumber = BV_number ? null : extractAV(url);
            if (!BV_number && !avNumber) {
                showNotification('未能在当前页面找到 BV 号或 av 号');
                return;
            }

            const kind = BV_number ? 'bv' : 'av';
            const videoId = BV_number || avNumber;

            const info = await fetchBilibiliInfo(videoId, kind);
            if (!info) {
                showNotification('获取视频信息失败，请检查网络或 BV/av 号');
                return;
            }

            // 分享链接输出随页面形式：av 页输出 b23.tv/av…，BV 页输出 b23.tv/BV…
            const shareId = kind === 'av' ? `av${videoId}` : videoId;
            const shortLink = `https://b23.tv/${shareId}`;
            const html = `「${info.title}」——${info.owner}<br><a href="${shortLink}">${shortLink}</a><br><img src="${info.pic}" alt="${info.title}">`;

            GM_setClipboard(html, 'html');
            showNotification('视频信息已复制到剪贴板（HTML 格式）');
        } catch (err) {
            console.error('分享失败:', err);
            showNotification('操作失败: ' + err.message);
        }
    }

    /**
     * 从文本中提取 BV 号
     * @param {string} text - 要搜索的文本
     * @returns {string|null} 提取到的 BV 号，未找到则返回 null
     */
    function extractBV(text) {
        const match = text.match(/BV[a-zA-Z0-9]{10}/);
        return match ? match[0] : null;
    }

    /**
     * 从文本中提取 av 号后的数字部分
     * @param {string} text - 要搜索的文本
     * @returns {string|null} 提取到的数字（如 "170001"），未找到则返回 null
     */
    function extractAV(text) {
        const match = text.match(/av(\d+)/i);
        return match ? match[1] : null;
    }

    /**
     * 通过视频编号调用 Bilibili API 获取视频信息
     * @param {string} id - 视频编号（BV 号或 av 号数字部分）
     * @param {string} kind - 'bv' 用 bvid 查询，'av' 用 aid 查询
     * @returns {Promise<{title:string, owner:string, pic:string}|null>}
     */
    function fetchBilibiliInfo(id, kind = 'bv') {
        const param = kind === 'av' ? `aid=${id}` : `bvid=${id}`;
        return new Promise((resolve) => {
            GM_xmlhttpRequest({
                method: 'GET',
                url: `https://api.bilibili.com/x/web-interface/view?${param}`,
                onload: function (resp) {
                    try {
                        const data = JSON.parse(resp.responseText);
                        if (data.code === 0 && data.data) {
                            resolve({
                                title: data.data.title,
                                owner: data.data.owner.name,
                                pic: data.data.pic
                            });
                        } else {
                            console.error('API 返回错误:', data);
                            resolve(null);
                        }
                    } catch (e) {
                        console.error('解析 JSON 失败:', e);
                        resolve(null);
                    }
                },
                onerror: function (err) {
                    console.error('请求 API 失败:', err);
                    resolve(null);
                }
            });
        });
    }

    /**
     * 调用 PGC API 获取番剧/电影/电视剧信息
     * @param {string} params - 查询参数，如 "ep_id=1183104" 或 "season_id=73077"
     * @returns {Promise<{title:string, pic:string}|null>}
     */
    function fetchBangumiInfo(params) {
        return new Promise((resolve) => {
            GM_xmlhttpRequest({
                method: 'GET',
                url: `https://api.bilibili.com/pgc/view/web/season?${params}`,
                onload: function (resp) {
                    try {
                        const data = JSON.parse(resp.responseText);
                        if (data.code === 0 && data.result) {
                            const r = data.result;
                            // ponytail: title 拼接番剧名+集标题，cover 作封面
                            resolve({
                                title: (r.season_title && r.title) ? `${r.season_title} - ${r.title}` : (r.season_title || r.title || '未知标题'),
                                pic: r.cover || ''
                            });
                        } else {
                            console.error('PGC API 返回错误:', data);
                            resolve(null);
                        }
                    } catch (e) {
                        console.error('解析 PGC JSON 失败:', e);
                        resolve(null);
                    }
                },
                onerror: function (err) {
                    console.error('请求 PGC API 失败:', err);
                    resolve(null);
                }
            });
        });
    }

    // ----- 页面内分享按钮增强：附加延迟触发，保留原功能 -----
    // ponytail: 按页面类型匹配不同分享按钮，新增页面类型只需加选择器
    const SHARE_BTN_SELECTORS = [
        '.video-share-wrap.video-toolbar-left-item',                // 普通视频页 /video/*
        '.video-toolbar-content_item.video-toolbar-hover.share',    // 活动页 /festival/*
        '#share-container-id.share'                                 // 番剧/电影/电视剧 /bangumi/play/*
    ];

    function initShareButton() {
        for (const sel of SHARE_BTN_SELECTORS) {
            const shareBtn = document.querySelector(sel);
            if (shareBtn && !shareBtn.hasAttribute('data-custom-share-attached')) {
                shareBtn.setAttribute('data-custom-share-attached', 'true');
                shareBtn.addEventListener('click', function () {
                    // 延迟执行，让 B 站默认分享逻辑先完成
                    setTimeout(() => {
                        doShare();
                    }, 500);
                });
            }
        }
    }

    // 使用 MutationObserver 处理动态加载的分享按钮
    const observer = new MutationObserver(() => {
        initShareButton();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // 立即尝试一次
    initShareButton();
})();
