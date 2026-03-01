// ===== ヘッダー スクロール =====
const header = document.getElementById('header');
window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', window.scrollY > 20);
});

// ===== ハンバーガーメニュー =====
const hamburger = document.getElementById('hamburger');
const navList = document.getElementById('nav-list');

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navList.classList.toggle('open');
});

// ナビリンクをクリックしたらメニューを閉じる
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navList.classList.remove('open');
  });
});

// ===== スクロールアニメーション =====
const fadeEls = document.querySelectorAll(
  '.work-card, .tool-card, .about-grid, .section-header, .about-bio, .skills-section, .contact-form'
);

fadeEls.forEach(el => el.classList.add('fade-in'));

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.classList.add('visible');
      }, i * 80);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

fadeEls.forEach(el => observer.observe(el));

// ===== スキルバー アニメーション =====
const skillFills = document.querySelectorAll('.skill-fill');
const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const target = entry.target;
      const width = target.style.width;
      target.style.width = '0';
      requestAnimationFrame(() => {
        setTimeout(() => { target.style.width = width; }, 100);
      });
      skillObserver.unobserve(target);
    }
  });
}, { threshold: 0.5 });

skillFills.forEach(el => skillObserver.observe(el));

// ===== お問い合わせフォーム バリデーション =====
const form = document.getElementById('contact-form');
const formSuccess = document.getElementById('form-success');

function showError(fieldId, msg) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(fieldId + '-error');
  if (field) field.classList.add('error');
  if (error) error.textContent = msg;
}

function clearError(fieldId) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(fieldId + '-error');
  if (field) field.classList.remove('error');
  if (error) error.textContent = '';
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// リアルタイムバリデーション
['name', 'email', 'message'].forEach(id => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener('input', () => {
      if (el.value.trim()) clearError(id);
    });
  }
});

form.addEventListener('submit', (e) => {
  e.preventDefault();
  let valid = true;

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const message = document.getElementById('message').value.trim();

  clearError('name'); clearError('email'); clearError('message');

  if (!name) { showError('name', 'お名前を入力してください'); valid = false; }
  if (!email) {
    showError('email', 'メールアドレスを入力してください'); valid = false;
  } else if (!validateEmail(email)) {
    showError('email', '正しいメールアドレスを入力してください'); valid = false;
  }
  if (!message) { showError('message', 'メッセージを入力してください'); valid = false; }

  if (valid) {
    const btn = form.querySelector('button[type="submit"]');
    btn.textContent = '送信中...';
    btn.disabled = true;

    setTimeout(() => {
      form.reset();
      formSuccess.classList.add('show');
      btn.textContent = '送信する';
      btn.disabled = false;
      setTimeout(() => formSuccess.classList.remove('show'), 5000);
    }, 1200);
  }
});

// ===== アクティブナビリンク =====
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-link:not(.contact-btn)');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    const top = section.offsetTop - 100;
    if (window.scrollY >= top) current = section.getAttribute('id');
  });
  navLinks.forEach(link => {
    link.style.color = '';
    if (link.getAttribute('href') === '#' + current) {
      link.style.color = 'var(--green)';
    }
  });
});
