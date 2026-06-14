/* =========================================================
   パスワードゲート（任意・初期OFF）
   ---------------------------------------------------------
   ✏️ 使い方: 既定では無効（誰でもそのまま閲覧可）です。
            ロックをかけたい場合だけ、下の SITE_PASSWORD に
            好きなパスワードを設定してください（空ならロックなし）。
   ⚠️ 注意: これは静的サイト向けの「簡易ロック」です。画面は隠せますが、
            ページのソースを見れば中身は取得可能なため、完全な機密保護には
            なりません（限定共有など軽い用途向け）。
   ========================================================= */
const SITE_PASSWORD = ''; // ← パスワードを入れるとロックが有効に（空＝ロックなし）

(function () {
  // パスワード未設定（空）ならロックをかけない＝誰でもそのまま閲覧できる
  if (!SITE_PASSWORD) return;

  const KEY = 'site_unlocked';
  // 同じタブのセッション中、一度ログインすれば再入力不要
  if (sessionStorage.getItem(KEY) === '1') return;

  function showGate() {
    document.body.classList.add('locked');
    const overlay = document.createElement('div');
    overlay.className = 'auth-overlay';
    overlay.innerHTML =
      '<form class="auth-card" autocomplete="off">' +
        '<div class="auth-icon">🔒</div>' +
        '<h1>このサイトは非公開です</h1>' +
        '<p>閲覧にはパスワードが必要です。</p>' +
        '<input type="password" class="auth-input" placeholder="パスワード" aria-label="パスワード" autofocus />' +
        '<button type="submit">ログイン</button>' +
        '<p class="auth-error"></p>' +
      '</form>';
    document.body.appendChild(overlay);

    const form = overlay.querySelector('form');
    const input = overlay.querySelector('.auth-input');
    const error = overlay.querySelector('.auth-error');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (input.value === SITE_PASSWORD) {
        sessionStorage.setItem(KEY, '1');
        overlay.remove();
        document.body.classList.remove('locked');
      } else {
        error.textContent = 'パスワードが違います';
        input.value = '';
        input.focus();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showGate);
  } else {
    showGate();
  }
})();
