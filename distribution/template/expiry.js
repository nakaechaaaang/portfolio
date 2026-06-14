/* =========================================================
   公開期限の自動管理（3週間で自動的に「期限切れ」へ）
   ---------------------------------------------------------
   ✏️ 編集: 下の PUBLISH_DATE を「公開した日」に設定してください。
            この日から VALID_DAYS（既定21日 = 3週間）が過ぎると、
            自動的にページの内容を削除し「期限切れ」画面に切り替えます。
   ========================================================= */
const PUBLISH_DATE = '2026-06-14'; // 公開日（YYYY-MM-DD）
const VALID_DAYS   = 21;           // 公開期間（日数）。3週間 = 21

(function () {
  // 公開日が未設定・不正なら何もしない
  const start = new Date(PUBLISH_DATE + 'T00:00:00');
  if (isNaN(start.getTime())) return;

  const expiry = new Date(start.getTime() + VALID_DAYS * 24 * 60 * 60 * 1000);
  if (new Date() < expiry) return; // 期限内なら通常表示

  // ---- ここから先は「期限切れ」処理 ----
  document.documentElement.classList.add('expired');

  // 1) ブラウザに保存されたデータを自動削除
  function wipeData() {
    try { localStorage.clear(); } catch (e) {}
    try { sessionStorage.clear(); } catch (e) {}
    // Cookie をすべて失効させる
    try {
      document.cookie.split(';').forEach(function (c) {
        const name = c.split('=')[0].trim();
        if (name) document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
      });
    } catch (e) {}
    // キャッシュストレージを削除
    try {
      if (window.caches && caches.keys) {
        caches.keys().then(function (keys) { keys.forEach(function (k) { caches.delete(k); }); });
      }
    } catch (e) {}
    // IndexedDB を削除
    try {
      if (window.indexedDB && indexedDB.databases) {
        indexedDB.databases().then(function (dbs) {
          dbs.forEach(function (db) { if (db.name) indexedDB.deleteDatabase(db.name); });
        });
      }
    } catch (e) {}
  }

  // 2) ページ上のコンテンツ（個人情報を含む）をDOMから削除して期限切れ画面に差し替え
  function showExpired() {
    wipeData();
    document.title = '公開期限切れ';
    document.body.className = 'expired';
    document.body.innerHTML =
      '<div class="expiry-overlay">' +
        '<div class="expiry-icon">🔒</div>' +
        '<h1>このページの<span class="expiry-accent">公開は終了</span>しました</h1>' +
        '<p>公開期間（3週間）が過ぎたため、コンテンツは自動的に削除されました。' +
        'ご覧いただきありがとうございました。</p>' +
      '</div>';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showExpired);
  } else {
    showExpired();
  }
})();
