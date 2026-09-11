/* ============================================================
   0928.love — Wedding Site JS
   Countdown + Parallax + Nav + Reveal
   ============================================================ */
(function() {
    'use strict';

    /* ========================================================
       COUNTDOWN — Target: 2026-09-28 15:00 CST（迎宾开始）
       只保留"剩余天数"，作为请柬卡内的一行小胶囊
       ======================================================== */
    const WEDDING = new Date('2026-09-28T15:00:00+08:00');
    const cdPill = document.getElementById('countdownPill');

    function tick() {
        if (!cdPill) return;
        const diff = WEDDING - Date.now();
        if (diff <= 0) {
            cdPill.innerHTML = '<i class="fas fa-champagne-glasses"></i> 婚礼进行中，感谢见证 ❤';
            clearInterval(cdTimer);
            return;
        }
        const days = Math.floor(diff / 864e5);
        if (days === 0) {
            cdPill.innerHTML = '<i class="fas fa-champagne-glasses"></i> 婚礼就在今天！';
            clearInterval(cdTimer);
            return;
        }
        const num = cdPill.querySelector('.cd-days-num');
        if (num && num.textContent !== String(days)) {
            num.textContent = days;
            num.style.transform = 'scale(1.15)';
            num.style.transition = 'transform .12s ease';
            requestAnimationFrame(() => num.style.transform = 'scale(1)');
        }
    }

    const cdTimer = setInterval(tick, 60000);
    tick();

    /* ========================================================
       PARALLAX SCROLLING
       ======================================================== */
    const parallaxEls = document.querySelectorAll('[data-parallax]');
    let raf;

    function updateParallax() {
        const sy = window.pageYOffset;
        const vh = window.innerHeight;
        parallaxEls.forEach(el => {
            const rate = parseFloat(el.getAttribute('data-parallax'));
            const parent = el.closest('section') || el.parentElement;
            const rect = parent.getBoundingClientRect();
            if (rect.bottom > -vh && rect.top < vh * 2) {
                const offset = (sy - (rect.top + sy)) * (1 - rate);
                el.style.transform = `translate3d(0, ${offset * 0.3}px, 0)`;
            }
        });
    }

    /* ========================================================
       V24 LIGHT FIELD — 滚动驱动光影（光源在左上，向右下照射）
       --scroll-p → .site-bg 本元素（全局进度，驱动光晕/光束漂移；
                    不写 :root，样式失效范围收缩到两个伪元素）
       --lit      → 各玻璃卡（0=顶边抵视口底，1=底边出视口顶，
                    驱动 ::after 扫光带与 ::before 折射暖斑）
       量化步长（.005 / .025）+ 仅视口内更新，CSS 端 .3s linear
       transition 把台阶抹成连续滑动（跑在合成器上）
       ======================================================== */
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const siteBg = document.querySelector('.site-bg');
    const litCards = document.querySelectorAll(
        '.invitation-card, .moment-frame, .rsvp-card, .venue-info-card, .sched-content');
    let lastP = -1;

    function updateLightField() {
        if (reduceMotion.matches) return;  /* 减弱动效：停更，CSS 兜底值 = 静态但完整的光照 */
        const sy = window.pageYOffset, vh = window.innerHeight;

        /* 全局进度（量化 0.005） */
        const max = document.documentElement.scrollHeight - vh;
        const p = max > 0 ? Math.min(1, Math.max(0, sy / max)) : 0;
        const pq = Math.round(p * 200) / 200;
        if (siteBg && pq !== lastP) {
            siteBg.style.setProperty('--scroll-p', pq);
            lastP = pq;
        }

        /* 逐卡光位：帧内读写分离 —— 先集中读 rect（本帧唯一一次强制布局，
           不缓存 offsetTop：懒加载图片/字体 swap/reveal/parallax 都会让缓存漂移），
           再集中写变量（写自定义属性不弄脏布局） */
        const visible = [];
        litCards.forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.bottom > 0 && r.top < vh) visible.push([el, r]);
        });
        visible.forEach(([el, r]) => {
            const lit = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
            const lq = Math.round(lit * 40) / 40;  /* 量化 0.025 */
            if (el._lit !== lq) {
                el.style.setProperty('--lit', lq);
                el._lit = lq;
            }
        });
    }

    /* 减弱动效偏好中途切换：清除内联变量回落静态光照 / 恢复滚动驱动 */
    reduceMotion.addEventListener('change', () => {
        if (reduceMotion.matches) {
            if (siteBg) siteBg.style.removeProperty('--scroll-p');
            litCards.forEach(el => { el.style.removeProperty('--lit'); el._lit = undefined; });
        } else { lastP = -1; updateLightField(); }
    });

    window.addEventListener('scroll', () => {
        if (!raf) raf = requestAnimationFrame(() => { updateLightField(); updateParallax(); raf = null; });
    }, { passive: true });
    updateLightField();
    updateParallax();

    /* ========================================================
       SCROLL REVEAL (Intersection Observer)
       ======================================================== */
    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal').forEach(el => obs.observe(el));

    /* ========================================================
       MOBILE NAV
       ======================================================== */
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.querySelector('.nav-links');
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const s = navToggle.querySelectorAll('span');
            if (navLinks.classList.contains('active')) {
                s[0].style.transform = 'rotate(45deg) translate(5px,5px)';
                s[1].style.opacity = '0';
                s[2].style.transform = 'rotate(-45deg) translate(5px,-5px)';
            } else {
                s[0].style.transform = s[1].style.opacity = s[2].style.transform = '';
            }
        });
        navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
            navLinks.classList.remove('active');
            navToggle.querySelectorAll('span').forEach(s => s.style.transform = s.style.opacity = '');
        }));
    }

    /* ========================================================
       NAV SCROLL STATE
       ======================================================== */
    const nav = document.getElementById('nav');
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.pageYOffset > 60);
    }, { passive: true });

    /* ========================================================
       SMOOTH ANCHOR SCROLL
       ======================================================== */
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            const t = document.querySelector(this.getAttribute('href'));
            if (t) {
                e.preventDefault();
                window.scrollTo({ top: t.getBoundingClientRect().top + window.pageYOffset - 70, behavior: 'smooth' });
            }
        });
    });

})();
