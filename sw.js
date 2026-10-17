/* ==========================================================
 * 康伴 App 离线缓存（Service Worker）
 * ==========================================================
 * 【v28 重写：修掉一个「一升版就白屏」的致命自动更新漏洞】
 *
 * 【原实现的致命链路】
 *   sw.js:26   return r || caches.match('./index.html');
 *   caches.match(req) 是**精确 URL 匹配**，缓存键里带 query string。
 *   ① 我把 KB_BUILD 从 2026101517 升到 2026101701
 *   ② 老人手机上次访问时缓存的键是  kb.js?v=2026101517
 *   ③ 这次页面请求的是              kb.js?v=2026101701  →  缓存 miss
 *   ④ 于是回退到 caches.match('./index.html')  →  命中，返回 **HTML**
 *   ⑤ 浏览器把 HTML 当 JavaScript 解析 → Uncaught SyntaxError → **整站白屏**
 *   结果：只要发了新版本，家里没网的老人打开就是一片空白，而且不会自愈
 *   （因为每次都会走到同一分支）。
 *
 * 【还有三个隐患，一并修掉】
 *   ⑥ install 里只有 skipWaiting，从不预缓存 —— 「离线可用」实际上从没成立过：
 *      用户不先访问过一次，断网时缓存是空的。
 *   ⑦ CACHE 名是写死的 'kangban-v2'。代码更新后同名缓存不会被 activate 删除，
 *      旧资源继续被复用。
 *   ⑧ 没有排除 /api/。当前 API 跨域所以没出事，但一旦有人把 API_BASE 改成同源，
 *      接口响应会被当成静态资源缓存 → 用户读到过期的 token 和数据。
 *
 * 【修法】
 *   A. 缓存回退按**类型分流**：文档回退 index.html；脚本/样式/图片回退
 *      忽略 query 的同路径缓存；实在没有就返回一个明确的 504 响应，
 *      **绝不拿 HTML 冒充 JS**（拿不到是「某个功能不可用」，拿错是「整站崩」）。
 *   B. install 阶段主动预缓存 index.html / manifest，让离线可用真正成立。
 *   C. CACHE 名带版本号，代码更新时自动换名 + 清理旧缓存。
 *   D. 显式跳过 /api/ 与跨域请求，不进缓存。
 *   E. 只缓存基本响应（200 / 206），错误页与重定向不入缓存。
 * ========================================================== */

const VER = 'v39';
const CACHE = 'kangban-' + VER;

/* install 时预缓存：这些是「断网也必须能打开」的东西 */
const PRECACHE = ['./', './index.html', './manifest.webmanifest'];

self.addEventListener('install', function (e) {
  e.waitUntil((async function () {
    const c = await caches.open(CACHE);
    /* 逐个 add：某一个 404 不该让整个 install 失败 */
    await Promise.all(PRECACHE.map(async function (u) {
      try {
        const r = await fetch(new Request(u, { cache: 'reload' }));
        if (r && r.ok) await c.put(u, r);
      } catch (err) { /* 单个资源失败不阻塞 */ }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', function (e) {
  e.waitUntil((async function () {
    const keys = await caches.keys();
    /* 只删本应用的旧版本缓存，不碰同源下其它人（如 Chrome DevTools）的缓存 */
    await Promise.all(keys.map(function (k) {
      return (k.indexOf('kangban-') === 0 && k !== CACHE) ? caches.delete(k) : null;
    }));
    /* navigationPreload：文档请求交给浏览器预载，弱网首屏更快 */
    try {
      if (self.registration.navigationPreload) await self.registration.navigationPreload.enable();
    } catch (err) { /* 不支持就算了，逻辑不依赖它 */ }
    await self.clients.claim();
  })());
});

/** 明确的「取不到」响应。宁可少一个功能，也不要让浏览器解析错类型的内容。 */
function offlineResponse(req) {
  return new Response(
    '/* offline: 本资源未缓存 */',
    { status: 504, statusText: 'Offline', headers: { 'content-type': 'application/javascript; charset=utf-8' } }
  );
}

self.addEventListener('fetch', function (e) {
  const req = e.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (err) { return; }

  /* 跨域（含 API_BASE）一律不管：API 永远走网络，绝不能被缓存出过期数据 */
  if (url.origin !== location.origin) return;
  /* 显式排除接口路径，防止将来 API_BASE 改成同源时把响应写进缓存 */
  if (url.pathname.indexOf('/api/') === 0) return;

  /* 文档：网络优先 + 绕过 HTTP 缓存，保证打开就是最新版 */
  const accept = req.headers.get('accept') || '';
  const isDoc = req.mode === 'navigate' || accept.indexOf('text/html') >= 0;

  e.respondWith((async function () {
    /* navigationPreload 可用时与导航请求并发发出，省掉一次 RTT */
    try {
      const pre = await e.preloadResponse;
      if (pre) {
        try { const c = await caches.open(CACHE); c.put(req, pre.clone()); } catch (err) {}
        return pre;
      }
    } catch (err) { /* 不支持则忽略 */ }

    const cacheMode = isDoc ? 'reload' : 'default';
    try {
      const res = await fetch(req, { cache: cacheMode });
      /* 只缓存成功的基本响应：错误页、重定向、opaque 都不入缓存 */
      if (res && (res.status === 200 || res.status === 206) && res.type === 'basic') {
        try { const c = await caches.open(CACHE); c.put(req, res.clone()); } catch (err) {}
      }
      return res;
    } catch (err) {
      /* —— 离线：按类型分级回退 —— */
      const c = await caches.open(CACHE);

      /* 1) 原样命中（带 query 的精确键，比如已缓存过的 kb.js?v=xxx） */
      const exact = await c.match(req);
      if (exact) return exact;

      /* 2) 忽略 query / search 再找一次。
            这是修掉白屏的关键：kb.js?v=新 找不到时，退到 kb.js（任意 query），
            拿到的是真 JS，而不是 HTML。 */
      const loose = await c.match(req, { ignoreSearch: true, ignoreVary: true });
      if (loose) return loose;

      /* 3) 文档才回退到首页外壳（离线 SPA 的标准做法） */
      if (isDoc) {
        const shell = await c.match('./index.html', { ignoreSearch: true })
          || await c.match('./', { ignoreSearch: true });
        if (shell) return shell;
      }

      /* 4) 兜底：明确告诉浏览器「没有」，绝不返回 HTML 冒充 JS/CSS */
      return offlineResponse(req);
    }
  })());
});