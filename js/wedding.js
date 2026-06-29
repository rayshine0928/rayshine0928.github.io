/* ============================================================
   0928.love — Wedding Site JavaScript
   ============================================================ */

(function() {
    'use strict';

    /* ========================================================
       COUNTDOWN TIMER
       Target: 2026-09-28 18:28:00 (CST, UTC+8)
       ======================================================== */
    const WEDDING_DATE = new Date('2026-09-28T17:00:00+08:00');

    function updateCountdown() {
        const now = new Date();
        const diff = WEDDING_DATE - now;

        if (diff <= 0) {
            // Wedding day! Show zeros or celebration
            setAllNumbers(0, 0, 0, 0);
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const mins = Math.floor((diff / (1000 * 60)) % 60);
        const secs = Math.floor((diff / 1000) % 60);

        setAllNumbers(days, hours, mins, secs);
    }

    function setAllNumbers(d, h, m, s) {
        // Hero countdown
        setEl('cd-days', d);
        setEl('cd-hours', pad(h));
        setEl('cd-mins', pad(m));
        setEl('cd-secs', pad(s));

        // Main countdown section
        setEl('mcd-days', d);
        setEl('mcd-hours', pad(h));
        setEl('mcd-mins', pad(m));
        setEl('mcd-secs', pad(s));
    }

    function setEl(id, val) {
        const el = document.getElementById(id);
        if (el && el.textContent !== String(val)) {
            el.textContent = val;
            // Quick pulse animation
            el.style.transform = 'scale(1.15)';
            el.style.transition = 'transform 0.15s ease';
            requestAnimationFrame(() => {
                el.style.transform = 'scale(1)';
            });
        }
    }

    function pad(n) { return String(n).padStart(2, '0'); }

    updateCountdown();
    setInterval(updateCountdown, 1000);

    /* ========================================================
       PARALLAX SCROLLING
       ======================================================== */
    const parallaxEls = document.querySelectorAll('[data-parallax]');
    let parallaxRAF;

    function updateParallax() {
        const scrollY = window.pageYOffset;
        const vh = window.innerHeight;

        parallaxEls.forEach(el => {
            const rate = parseFloat(el.getAttribute('data-parallax'));
            const rect = el.parentElement.getBoundingClientRect();
            const parentTop = rect.top + scrollY;

            // Only update if element is in viewport
            if (rect.bottom > -vh && rect.top < vh * 2) {
                const offset = (scrollY - parentTop) * rate;
                el.style.transform = `translate3d(0, ${offset}px, 0)`;
            }
        });
    }

    function onParallaxScroll() {
        if (!parallaxRAF) {
            parallaxRAF = requestAnimationFrame(() => {
                updateParallax();
                parallaxRAF = null;
            });
        }
    }

    window.addEventListener('scroll', onParallaxScroll, { passive: true });
    updateParallax();

    /* ========================================================
       SCROLL REVEAL (Intersection Observer)
       ======================================================== */
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.reveal').forEach(el => {
        revealObserver.observe(el);
    });

    /* ========================================================
       PARTICLES (Hero Section)
       ======================================================== */
    const canvas = document.getElementById('particles');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let animId;

        function resizeCanvas() {
            canvas.width = canvas.parentElement.offsetWidth;
            canvas.height = canvas.parentElement.offsetHeight;
        }

        function createParticles() {
            const count = Math.min(Math.floor(window.innerWidth * 0.15), 80);
            particles = [];

            for (let i = 0; i < count; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: Math.random() * 2.5 + 0.5,
                    speedX: (Math.random() - 0.5) * 0.3,
                    speedY: -(Math.random() * 0.5 + 0.1),
                    opacity: Math.random() * 0.6 + 0.1,
                    pulse: Math.random() * Math.PI * 2,
                    pulseSpeed: Math.random() * 0.02 + 0.005,
                });
            }
        }

        function drawParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach(p => {
                p.x += p.speedX;
                p.y += p.speedY;
                p.pulse += p.pulseSpeed;

                // Wrap around edges
                if (p.y < -10) { p.y = canvas.height + 10; p.x = Math.random() * canvas.width; }
                if (p.x < -10) p.x = canvas.width + 10;
                if (p.x > canvas.width + 10) p.x = -10;

                const alpha = p.opacity + Math.sin(p.pulse) * 0.2;

                // Glow effect
                const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
                gradient.addColorStop(0, `rgba(232, 213, 183, ${alpha})`);
                gradient.addColorStop(0.5, `rgba(232, 213, 183, ${alpha * 0.4})`);
                gradient.addColorStop(1, 'rgba(232, 213, 183, 0)');

                ctx.beginPath();
                ctx.fillStyle = gradient;
                ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
                ctx.fill();

                // Core
                ctx.beginPath();
                ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
            });

            animId = requestAnimationFrame(drawParticles);
        }

        resizeCanvas();
        createParticles();
        drawParticles();

        window.addEventListener('resize', () => {
            resizeCanvas();
            createParticles();
        });
    }

    /* ========================================================
       MOBILE NAVIGATION
       ======================================================== */
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.querySelector('.nav-links');
    const nav = document.getElementById('nav');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            const spans = navToggle.querySelectorAll('span');
            if (navLinks.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });

        // Close nav on link click (mobile)
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                const spans = navToggle.querySelectorAll('span');
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            });
        });
    }

    /* ========================================================
       NAV SCROLL STATE
       ======================================================== */
    let lastScrollY = 0;

    function updateNavState() {
        const scrollY = window.pageYOffset;

        if (scrollY > 60) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }

        lastScrollY = scrollY;
    }

    window.addEventListener('scroll', updateNavState, { passive: true });
    updateNavState();

    /* ========================================================
       THREE.JS FADE ON SCROLL
       ======================================================== */
    const threeBg = document.getElementById('threeBg');
    if (threeBg) {
        window.addEventListener('scroll', () => {
            const scrollY = window.pageYOffset;
            const vh = window.innerHeight;
            if (scrollY > vh * 0.5) {
                threeBg.classList.add('faded');
            } else {
                threeBg.classList.remove('faded');
            }
        }, { passive: true });
    }

    /* ========================================================
       SMOOTH SCROLL (for older browsers)
       ======================================================== */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                const navHeight = 70;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

})();
