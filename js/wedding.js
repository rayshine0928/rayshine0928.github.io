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

    window.addEventListener('scroll', () => {
        if (!raf) raf = requestAnimationFrame(() => { updateParallax(); raf = null; });
    }, { passive: true });
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
