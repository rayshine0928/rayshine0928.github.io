/**
 * wedding-fx.js — v26「晴光极光」交互层
 * 移植自 LogosCaller premium-interactions.js + ambient.js，按明亮主题转译：
 *
 *  - 情境光标胶囊（antigravity.google 风格）：速度挤压拉伸、
 *    残影彗尾、驻停morph成圆形照片预览、按压反馈、区域跳转换词
 *  - 暖阳 Spotlight：跟随光标的暖金光斑 + 极光场/hero 指针视差
 *  - 玻璃卡 3D tilt + 追光 glare + 1px 边缘流光（--glare-x/y 驱动）
 *  - 磁性按钮（地图 CTA）
 *  - 导航滑行胶囊（nav glide）
 *  - 页脚手电筒题词（遮罩只在光标落处显影）
 *  - View Transitions 圆形揭示锚点跳转（无支持时平滑滚动兜底）
 *  - 金色光尘粒子场：环形位移 + 涡旋 + 弹簧回位 + 深度视差，
 *    光标掠过的金尘"染上玫瑰色"，快速甩动抛出金色流星
 *
 * 明亮主题的关键教训（承接 v25）：亮底上加色混合（lighter/screen）
 * 恒等于白——粒子与光斑一律 source-over 用"有颜色的暖金/玫瑰"上色。
 *
 * 降级矩阵：
 *  - 无 JS / 内核缺失：什么都不加，页面按纯 CSS 静态呈现；
 *  - 触屏设备：不启用任何指针特效（reveal 由 wedding.js 负责）；
 *  - prefers-reduced-motion：同上，静止但完整。
 */
(function () {
    'use strict';

    var Fx = window.LoveFx;
    if (!Fx) {
        return;
    }

    var ticker = Fx.ticker;
    var pointer = Fx.pointer;
    var smooth = Fx.smooth;
    var clamp = Fx.clamp;
    var each = Fx.each;
    var enablePointerFx = Fx.env.enablePointerFx;
    var reduceMotion = Fx.env.reduceMotion;

    // --------------------------------------------------------
    // 情境光标胶囊 —— 跟随 ≈ quickTo(0.35, power2.out)，
    // 弹入 ≈ back.out(1.7)（CSS 过冲贝塞尔），弹出 ≈ power2.in。
    // 扩展：沿速度矢量的挤压拉伸、两道残影、驻停 morph 圆形预览。
    // --------------------------------------------------------
    function initCursorPill() {
        if (!enablePointerFx) {
            return;
        }

        var ZONE = '[data-cursor-pill]';
        if (!document.querySelector(ZONE)) {
            return;
        }

        var pill = document.createElement('div');
        pill.className = 'cursor-pill';
        pill.setAttribute('aria-hidden', 'true');
        pill.innerHTML =
            '<div class="cursor-pill-stretch">' +
            '<div class="cursor-pill-inner">' +
            '<i class="cursor-pill-icon"></i>' +
            '<span class="cursor-pill-label"></span>' +
            '</div>' +
            // 预览盘是 inner 的兄弟而非子元素：morph 会把 inner 缩没，
            // 预览盘必须活下来。
            '<img class="cursor-pill-preview" alt="">' +
            '</div>';
        document.body.appendChild(pill);

        var stretchEl = pill.querySelector('.cursor-pill-stretch');
        var iconEl = pill.querySelector('.cursor-pill-icon');
        var labelEl = pill.querySelector('.cursor-pill-label');
        var previewEl = pill.querySelector('.cursor-pill-preview');

        // 残影彗尾 —— 快速移动时拖在胶囊身后的两团暖金模糊光。
        var trails = [0.18, 0.3].map(function (tau, i) {
            var el = document.createElement('div');
            el.className = 'cursor-trail cursor-trail-' + (i + 1);
            el.setAttribute('aria-hidden', 'true');
            document.body.appendChild(el);
            return { el: el, tau: tau, x: 0, y: 0 };
        });

        // 只有胶囊真正上岗后才隐藏区域内的系统光标。
        document.body.classList.add('cursor-pill-live');

        var FOLLOW_TAU = 0.09;
        var STRETCH_TAU = 0.06;
        var DWELL_MS = 450;

        var targetX = 0;
        var targetY = 0;
        var pillX = 0;
        var pillY = 0;
        var prevX = 0;
        var prevY = 0;
        var stretch = 1;
        var angle = 0;
        var activeZone = null;
        var dwellTimer = null;

        ticker.add(function (dt) {
            var moving = pointer.speed > 1 || activeZone;
            if (!moving && stretch === 1) {
                // 停摆前残影也要归位。
                var trailBusy = false;
                each(trails, function (t) {
                    t.x = smooth(t.x, pointer.x, t.tau, dt);
                    t.y = smooth(t.y, pointer.y, t.tau, dt);
                    t.el.style.transform = 'translate3d(' + t.x.toFixed(1) + 'px,' + t.y.toFixed(1) + 'px,0)';
                    if (Math.abs(pointer.x - t.x) > 1 || Math.abs(pointer.y - t.y) > 1) {
                        trailBusy = true;
                    }
                });
                var fade = parseFloat(trails[0].el.style.opacity || '0');
                if (fade > 0.01) {
                    each(trails, function (t) {
                        t.el.style.opacity = '0';
                    });
                    trailBusy = true;
                }
                return trailBusy;
            }

            // --- 胶囊跟随 ---
            if (activeZone) {
                pillX = smooth(pillX, targetX, FOLLOW_TAU, dt);
                pillY = smooth(pillY, targetY, FOLLOW_TAU, dt);
                if (Math.abs(targetX - pillX) < 0.1 && Math.abs(targetY - pillY) < 0.1) {
                    pillX = targetX;
                    pillY = targetY;
                }
                pill.style.transform =
                    'translate3d(' + pillX.toFixed(2) + 'px,' + pillY.toFixed(2) + 'px,0)';
            }

            // --- 沿自身速度矢量的挤压拉伸 ---
            var vx = (pillX - prevX) / dt;
            var vy = (pillY - prevY) / dt;
            prevX = pillX;
            prevY = pillY;
            var speed = Math.sqrt(vx * vx + vy * vy);
            var wantStretch = 1 + clamp(speed / 6000, 0, 0.16);
            stretch = smooth(stretch, wantStretch, STRETCH_TAU, dt);
            if (speed > 40) {
                angle = Math.atan2(vy, vx);
            }
            var sy = 1 / Math.pow(stretch, 0.85);
            stretchEl.style.transform =
                'rotate(' + angle.toFixed(3) + 'rad) scale(' +
                stretch.toFixed(3) + ',' + sy.toFixed(3) + ')';

            // --- 残影：光标移动够快时显形 ---
            var trailAlpha = clamp((pointer.speed - 250) / 2500, 0, 1);
            each(trails, function (t, i) {
                t.x = smooth(t.x, pointer.x, t.tau, dt);
                t.y = smooth(t.y, pointer.y, t.tau, dt);
                t.el.style.transform = 'translate3d(' + t.x.toFixed(1) + 'px,' + t.y.toFixed(1) + 'px,0)';
                t.el.style.opacity = (trailAlpha * (i === 0 ? 0.35 : 0.18)).toFixed(3);
            });

            var settled =
                (!activeZone || (Math.abs(targetX - pillX) < 0.1 && Math.abs(targetY - pillY) < 0.1)) &&
                Math.abs(stretch - 1) < 0.004 &&
                pointer.speed < 1;
            return !settled;
        });

        function setZoneContent(zone) {
            var icon = zone.getAttribute('data-cursor-icon') || '';
            iconEl.className = 'cursor-pill-icon' + (icon ? ' ' + icon : '');
            iconEl.style.display = icon ? '' : 'none';
            labelEl.textContent = zone.getAttribute('data-cursor-label') || '';
        }

        function cancelDwell() {
            if (dwellTimer) {
                clearTimeout(dwellTimer);
                dwellTimer = null;
            }
            pill.classList.remove('is-preview');
        }

        function startDwell(zone) {
            cancelDwell();
            var src = zone.getAttribute('data-cursor-preview');
            if (!src) {
                return;
            }
            dwellTimer = setTimeout(function () {
                dwellTimer = null;
                if (activeZone === zone) {
                    previewEl.src = src;
                    pill.classList.add('is-preview');
                }
            }, DWELL_MS);
        }

        function deactivate() {
            activeZone = null;
            cancelDwell();
            pill.classList.remove('is-active', 'is-press');
        }

        document.addEventListener('pointerover', function (e) {
            var zone = e.target && e.target.closest ? e.target.closest(ZONE) : null;
            if (!zone || zone === activeZone) {
                return;
            }
            if (activeZone) {
                // 区域直接跳区域：换词，保持显形。
                activeZone = zone;
                cancelDwell();
                setZoneContent(zone);
                startDwell(zone);
                return;
            }
            activeZone = zone;
            setZoneContent(zone);
            // 跳到指针处，而不是从陈旧位置飞过来。
            targetX = pillX = prevX = e.clientX;
            targetY = pillY = prevY = e.clientY;
            pill.style.transform = 'translate3d(' + pillX + 'px,' + pillY + 'px,0)';
            pill.classList.add('is-active');
            startDwell(zone);
            ticker.wake();
        });

        document.addEventListener('pointerout', function (e) {
            if (!activeZone) {
                return;
            }
            var to = e.relatedTarget;
            // 仍在某个胶囊区域内（同一个，或跳向另一个——由
            // pointerover 接管换词）。relatedTarget === null 说明
            // 指针离开了窗口。
            if (to && to.closest && to.closest(ZONE)) {
                return;
            }
            deactivate();
        });

        window.addEventListener('pointermove', function (e) {
            targetX = e.clientX;
            targetY = e.clientY;
            ticker.wake();
        }, { passive: true });

        // 按压反馈 —— 点击时胶囊微微下潜。
        window.addEventListener('pointerdown', function () {
            if (activeZone) {
                pill.classList.add('is-press');
            }
        }, { passive: true });

        window.addEventListener('pointerup', function () {
            pill.classList.remove('is-press');
        }, { passive: true });

        // 页面滚动把活跃区域从静止指针底下挪走时，收起胶囊。
        window.addEventListener('scroll', function () {
            if (!activeZone) {
                return;
            }
            var r = activeZone.getBoundingClientRect();
            var inside =
                targetX >= r.left && targetX <= r.right &&
                targetY >= r.top && targetY <= r.bottom;
            if (!inside) {
                deactivate();
            }
        }, { passive: true });

        document.documentElement.addEventListener('pointerleave', deactivate, { passive: true });
    }

    // --------------------------------------------------------
    // 指针光场：暖阳 spotlight + 极光场 / hero 视差
    // --------------------------------------------------------
    function initPointerField() {
        if (!enablePointerFx) {
            return;
        }

        var spotlight = document.createElement('div');
        spotlight.className = 'cursor-spotlight';
        spotlight.setAttribute('aria-hidden', 'true');
        document.body.appendChild(spotlight);

        var aurora = document.querySelector('.aurora-field');
        var heroLayers = document.querySelectorAll('.hero-parallax');

        // 时间常数按 60Hz 下的手感标定（spotlight 0.11 / 极光 0.32 /
        // hero 0.20），在 120Hz+ 屏幕上表现一致。
        var SPOT_TAU = 0.11;
        var BG_TAU = 0.32;
        var HERO_TAU = 0.20;

        var targetX = window.innerWidth / 2;
        var targetY = window.innerHeight / 2;
        var spotX = targetX;
        var spotY = targetY;
        var bgX = 0;
        var bgY = 0;
        var heroX = 0;
        var heroY = 0;
        var engaged = false;

        ticker.add(function (dt) {
            var nx = targetX / window.innerWidth - 0.5;  // -0.5 .. 0.5
            var ny = targetY / window.innerHeight - 0.5;

            spotX = smooth(spotX, targetX, SPOT_TAU, dt);
            spotY = smooth(spotY, targetY, SPOT_TAU, dt);
            spotlight.style.transform =
                'translate3d(' + spotX.toFixed(1) + 'px,' + spotY.toFixed(1) + 'px,0)';

            var bgTargetX = nx * 26;
            var bgTargetY = ny * 26;
            var heroTargetX = nx * -16;
            var heroTargetY = ny * -16;

            if (aurora) {
                bgX = smooth(bgX, bgTargetX, BG_TAU, dt);
                bgY = smooth(bgY, bgTargetY, BG_TAU, dt);
                aurora.style.transform =
                    'translate3d(' + bgX.toFixed(2) + 'px,' + bgY.toFixed(2) + 'px,0)';
            }

            if (heroLayers.length) {
                heroX = smooth(heroX, heroTargetX, HERO_TAU, dt);
                heroY = smooth(heroY, heroTargetY, HERO_TAU, dt);
                each(heroLayers, function (el) {
                    var f = parseFloat(el.getAttribute('data-px-factor')) || 1;
                    el.style.transform =
                        'translate3d(' + (heroX * f).toFixed(2) + 'px,' +
                        (heroY * f).toFixed(2) + 'px,0)';
                });
            }

            var settled =
                Math.abs(targetX - spotX) < 0.5 &&
                Math.abs(targetY - spotY) < 0.5 &&
                (!aurora || (Math.abs(bgTargetX - bgX) < 0.05 && Math.abs(bgTargetY - bgY) < 0.05)) &&
                (!heroLayers.length || (Math.abs(heroTargetX - heroX) < 0.05 && Math.abs(heroTargetY - heroY) < 0.05));

            return !settled;
        });

        window.addEventListener('pointermove', function (e) {
            targetX = e.clientX;
            targetY = e.clientY;
            if (!engaged) {
                engaged = true;
                // 首次移动直接跳到指针处，不要飞进来。
                spotX = targetX;
                spotY = targetY;
                document.body.classList.add('spotlight-on');
            }
            ticker.wake();
        }, { passive: true });

        window.addEventListener('pointerdown', function () {
            document.body.classList.add('spotlight-boost');
        }, { passive: true });

        window.addEventListener('pointerup', function () {
            document.body.classList.remove('spotlight-boost');
        }, { passive: true });

        document.documentElement.addEventListener('pointerleave', function () {
            engaged = false;
            document.body.classList.remove('spotlight-on', 'spotlight-boost');
        }, { passive: true });
    }

    // --------------------------------------------------------
    // 玻璃卡 3D tilt + 追光 glare（边缘流光是纯 CSS，
    // 由同一组 --glare-x/--glare-y 变量驱动）
    // --------------------------------------------------------
    function initCardTilt() {
        if (!enablePointerFx) {
            return;
        }

        each(document.querySelectorAll('.tilt-card'), function (card) {
            var maxDeg = parseFloat(card.getAttribute('data-tilt-max')) || 6;

            card.addEventListener('pointermove', function (e) {
                var rect = card.getBoundingClientRect();
                if (!rect.width || !rect.height) {
                    return;
                }
                var px = (e.clientX - rect.left) / rect.width;   // 0 .. 1
                var py = (e.clientY - rect.top) / rect.height;   // 0 .. 1

                if (!card.classList.contains('tilt')) {
                    card.classList.add('tilt');
                }
                card.style.setProperty('--tilt-y', ((px - 0.5) * 2 * maxDeg).toFixed(2) + 'deg');
                card.style.setProperty('--tilt-x', ((0.5 - py) * 2 * maxDeg).toFixed(2) + 'deg');
                card.style.setProperty('--glare-x', (px * 100).toFixed(1) + '%');
                card.style.setProperty('--glare-y', (py * 100).toFixed(1) + '%');
            }, { passive: true });

            card.addEventListener('pointerleave', function () {
                card.classList.remove('tilt');
                card.style.setProperty('--tilt-x', '0deg');
                card.style.setProperty('--tilt-y', '0deg');
            }, { passive: true });
        });
    }

    // --------------------------------------------------------
    // 磁性按钮 —— 被光标吸过去，松手弹回
    // --------------------------------------------------------
    function initMagneticButtons() {
        if (!enablePointerFx) {
            return;
        }

        var STRENGTH = 0.35;
        var MAX_OFFSET_PX = 12;

        each(document.querySelectorAll('.btn-map'), function (btn) {
            btn.addEventListener('pointermove', function (e) {
                var rect = btn.getBoundingClientRect();
                if (!rect.width || !rect.height) {
                    return;
                }
                var dx = e.clientX - (rect.left + rect.width / 2);
                var dy = e.clientY - (rect.top + rect.height / 2);
                var mx = clamp(dx * STRENGTH, -MAX_OFFSET_PX, MAX_OFFSET_PX);
                var my = clamp(dy * (STRENGTH + 0.1), -MAX_OFFSET_PX, MAX_OFFSET_PX) - 2;

                btn.classList.add('magnetic');
                btn.style.transform =
                    'translate3d(' + mx.toFixed(1) + 'px,' + my.toFixed(1) + 'px,0)';
            }, { passive: true });

            btn.addEventListener('pointerleave', function () {
                // 先摘掉快跟踪 class，让基础 .35s 过渡去演"弹回"。
                btn.classList.remove('magnetic');
                btn.style.transform = '';
            }, { passive: true });
        });
    }

    // --------------------------------------------------------
    // 导航滑行胶囊 —— 一枚玫瑰金光晕胶囊在链接间滑动
    // --------------------------------------------------------
    function initNavGlide() {
        if (!enablePointerFx) {
            return;
        }

        var list = document.querySelector('.nav-links');
        if (!list) {
            return;
        }

        var glide = document.createElement('span');
        glide.className = 'nav-glide';
        glide.setAttribute('aria-hidden', 'true');
        list.appendChild(glide);

        function moveTo(link) {
            var lr = link.getBoundingClientRect();
            var ur = list.getBoundingClientRect();
            var gh = glide.offsetHeight || 32;
            glide.style.width = lr.width + 14 + 'px';
            // 垂直按实测高度对中，不写死偏移
            glide.style.transform =
                'translate3d(' + (lr.left - ur.left - 7).toFixed(1) + 'px,' +
                (lr.top - ur.top + (lr.height - gh) / 2).toFixed(1) + 'px,0)';
        }

        each(list.querySelectorAll('li a'), function (link) {
            link.addEventListener('pointerenter', function () {
                moveTo(link);
                glide.classList.add('is-on');
            });
            link.addEventListener('focus', function () {
                moveTo(link);
                glide.classList.add('is-on');
            });
        });

        list.addEventListener('pointerleave', function () {
            glide.classList.remove('is-on');
        });
        list.addEventListener('focusout', function () {
            glide.classList.remove('is-on');
        });

        window.addEventListener('resize', function () {
            glide.classList.remove('is-on');
        }, { passive: true });
    }

    // --------------------------------------------------------
    // 手电筒题词 —— 只存在于光标光斑里的一行誓词。
    // 无 JS / 触屏 / 减弱动效时不戴面具，整行常显（内容不丢）。
    // --------------------------------------------------------
    function initInscription() {
        if (!enablePointerFx) {
            return;
        }

        var line = document.querySelector('.inscription');
        if (!line || !line.closest('footer')) {
            return;
        }

        line.closest('footer').addEventListener('pointermove', function (e) {
            var r = line.getBoundingClientRect();
            line.style.setProperty('--lx', (e.clientX - r.left).toFixed(1) + 'px');
            line.style.setProperty('--ly', (e.clientY - r.top).toFixed(1) + 'px');
        }, { passive: true });

        line.closest('footer').addEventListener('pointerleave', function () {
            // 光离开了：题词沉回纸面之下。
            line.style.setProperty('--ly', '-160px');
        }, { passive: true });
    }

    // --------------------------------------------------------
    // 锚点跳转 —— View Transitions 圆形揭示（从点击处展开），
    // 无支持时退回平滑滚动；两者都带 -70px 导航偏移。
    // --------------------------------------------------------
    function initAnchors() {
        var supportsVT = enablePointerFx && !!document.startViewTransition;

        document.addEventListener('click', function (e) {
            if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) {
                return;
            }
            var link = e.target.closest ? e.target.closest('a[href^="#"]') : null;
            if (!link) {
                return;
            }
            var id = link.getAttribute('href');
            var targetEl = id && id.length > 1 ? document.querySelector(id) : null;
            if (!targetEl) {
                return;
            }

            e.preventDefault();

            function jump() {
                var y = targetEl.getBoundingClientRect().top + window.pageYOffset - 70;
                window.scrollTo(0, Math.max(0, y));
                if (history.pushState) {
                    history.pushState(null, '', id);
                }
            }

            if (supportsVT) {
                document.documentElement.style.setProperty('--vt-x', e.clientX + 'px');
                document.documentElement.style.setProperty('--vt-y', e.clientY + 'px');
                document.startViewTransition(jump);
            } else {
                var y = targetEl.getBoundingClientRect().top + window.pageYOffset - 70;
                window.scrollTo({
                    top: Math.max(0, y),
                    behavior: reduceMotion ? 'auto' : 'smooth'
                });
                if (history.pushState) {
                    history.pushState(null, '', id);
                }
            }
        });
    }

    // --------------------------------------------------------
    // 金色光尘 —— 阳光下的金粉场（明亮转译版星尘）：
    // 四芒闪点 + 衍射短刺，source-over 暖金/玫瑰上色（亮底上
    // 加色混合不可见）；光标是一枚"戒指"，环内的金尘被推开、
    // 被涡旋卷动、接过光标的动量，事后被弹簧轻轻拉回原位；
    // 被光标掠过的金尘染上玫瑰色（lit 通道）；快速甩动抛出
    // 至多两枚金色流星。
    // --------------------------------------------------------
    function initParticles() {
        if (!enablePointerFx) {
            return;
        }

        var canvas = document.createElement('canvas');
        canvas.className = 'fx-particles';
        canvas.setAttribute('aria-hidden', 'true');
        var aurora = document.querySelector('.aurora-field');
        if (aurora && aurora.parentNode) {
            aurora.parentNode.insertBefore(canvas, aurora.nextSibling);
        } else {
            document.body.insertBefore(canvas, document.body.firstChild);
        }

        var ctx = canvas.getContext('2d');
        if (!ctx) {
            return;
        }

        var DPR = Math.min(window.devicePixelRatio || 1, 1.5);
        var W = 0;
        var H = 0;
        var stars = [];
        var shots = [];              // 快速甩动抛出的金色流星

        // 暖金系尘色 —— 以及金尘被光标掠过后"脸红"的玫瑰色。
        // 存成 [r,g,b] 便于点燃时混色。
        var COLORS = [[212, 165, 116], [183, 110, 121], [174, 131, 82], [196, 154, 110]];
        var WARM = [183, 110, 121];

        function mixc(a, b, t) {
            return ((a[0] + (b[0] - a[0]) * t) | 0) + ',' +
                ((a[1] + (b[1] - a[1]) * t) | 0) + ',' +
                ((a[2] + (b[2] - a[2]) * t) | 0);
        }

        // 环形交互（antigravity.google 主粒子场范式）：光标是一枚
        // 圆环，推开环内金尘并施加切向涡旋；弹簧事后把它们拉回家。
        var RING_R = 150;
        var RING_PUSH = 260;
        var RING_SWIRL = 110;
        var SPRING_K = 26;
        var SPRING_C = 6.5;
        var WAKE = 1.6;              // 快速光标交给金尘的动量
        var PARALLAX = 0.02;         // 深度：近尘比远尘躲得更远
        var FLICK_SPEED = 2600;

        var t = 0;
        var shotCool = 0;
        var fastFor = 0;

        function makeStar() {
            var z = 0.25 + Math.random() * 0.75;   // 深度：0 远，1 近
            return {
                hx: Math.random() * W,
                hy: Math.random() * H,
                z: z,
                s: (0.7 + z * 1.9) * (0.7 + Math.random() * 0.6),
                phase: Math.random() * 6.2832,
                tws: 0.6 + Math.random() * 1.4,    // 明灭速度
                rot: Math.random() * 6.2832,
                c: COLORS[(Math.random() * COLORS.length) | 0],
                dx: 0, dy: 0, vx: 0, vy: 0,        // 位移弹簧
                lit: 0                             // 玫瑰点燃度 0..1
            };
        }

        function resize() {
            W = window.innerWidth;
            H = window.innerHeight;
            canvas.width = Math.round(W * DPR);
            canvas.height = Math.round(H * DPR);
            canvas.style.width = W + 'px';
            canvas.style.height = H + 'px';
            ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

            var want = clamp(Math.round(W * H / 16000), 36, 110);
            while (stars.length < want) {
                stars.push(makeStar());
            }
            stars.length = want;
        }

        resize();
        window.addEventListener('resize', resize, { passive: true });

        // 四芒闪点：尖端落在轴上，腰部收在轴间。
        function sparkle(x, y, s, rot, alpha, rgb) {
            var w = s * 0.3;
            ctx.beginPath();
            for (var k = 0; k < 4; k++) {
                var a = rot + k * 1.5708;
                var b = a + 0.7854;
                var tx = x + Math.cos(a) * s;
                var ty = y + Math.sin(a) * s;
                if (k === 0) {
                    ctx.moveTo(tx, ty);
                } else {
                    ctx.lineTo(tx, ty);
                }
                ctx.lineTo(x + Math.cos(b) * w, y + Math.sin(b) * w);
            }
            ctx.closePath();
            ctx.fillStyle = 'rgba(' + rgb + ',' + alpha.toFixed(3) + ')';
            ctx.fill();
        }

        // 一根两端渐隐的光刺 —— 点光源经衍射的真实画法。
        // 圆晕读作散景球，刺与条纹才读作闪光。
        function spike(x, y, len, wid, ang, alpha, rgb) {
            if (alpha <= 0.004 || len <= 0.5) {
                return;
            }
            var dx = Math.cos(ang) * len;
            var dy = Math.sin(ang) * len;
            var g = ctx.createLinearGradient(x - dx, y - dy, x + dx, y + dy);
            g.addColorStop(0, 'rgba(' + rgb + ',0)');
            g.addColorStop(0.5, 'rgba(' + rgb + ',' + Math.min(1, alpha).toFixed(3) + ')');
            g.addColorStop(1, 'rgba(' + rgb + ',0)');
            ctx.strokeStyle = g;
            ctx.lineWidth = wid;
            ctx.beginPath();
            ctx.moveTo(x - dx, y - dy);
            ctx.lineTo(x + dx, y + dy);
            ctx.stroke();
        }

        ticker.add(function (dt) {
            if (document.hidden) {
                return false;
            }
            t += dt;

            ctx.clearRect(0, 0, W, H);
            // 明亮主题：source-over。亮底上 'lighter' 会把金尘洗成白。

            var px = pointer.x;
            var py = pointer.y;
            var pvx = pointer.vx;
            var pvy = pointer.vy;

            // 快速甩动抛出一枚流星（同屏至多两枚）。速度必须保持
            // 两三帧，单次尖峰伪造不了"甩"。
            fastFor = pointer.speed > FLICK_SPEED ? fastFor + dt : 0;
            shotCool -= dt;
            if (fastFor > 0.045 && shotCool <= 0 && shots.length < 2) {
                fastFor = 0;
                shotCool = 2.5;
                var sl = Math.sqrt(pvx * pvx + pvy * pvy) || 1;
                shots.push({
                    x: px,
                    y: py,
                    vx: (pvx / sl) * (900 + Math.random() * 400),
                    vy: (pvy / sl) * (900 + Math.random() * 400),
                    life: 0.9
                });
            }

            var i, st;
            for (i = 0; i < stars.length; i++) {
                st = stars[i];

                // 深度视差：近尘比远尘更躲着光标走。
                var parx = (px - W / 2) * -PARALLAX * st.z;
                var pary = (py - H / 2) * -PARALLAX * st.z;
                var sx = st.hx + st.dx + parx;
                var sy = st.hy + st.dy + pary;

                // 环形位移 + 涡旋 + 光标尾流。
                var rx = sx - px;
                var ry = sy - py;
                var d = Math.sqrt(rx * rx + ry * ry);
                if (d < RING_R && d > 0.001) {
                    var push = 1 - d / RING_R;
                    var f = push * push * RING_PUSH * dt;
                    st.vx += (rx / d) * f;
                    st.vy += (ry / d) * f;
                    var sw = push * RING_SWIRL * dt;
                    st.vx += (-ry / d) * sw;
                    st.vy += (rx / d) * sw;
                    st.vx += pvx * push * WAKE * dt;
                    st.vy += pvy * push * WAKE * dt;
                    // 被光标掠过的金尘会"脸红"。
                    if (d < RING_R * 0.8) {
                        st.lit = Math.min(1, st.lit + dt * 3);
                    }
                }
                st.lit *= Math.exp(-dt / 2.2);

                // 弹簧回家，轻微欠阻尼。
                st.vx += (-SPRING_K * st.dx - SPRING_C * st.vx) * dt;
                st.vy += (-SPRING_K * st.dy - SPRING_C * st.vy) * dt;
                st.dx += st.vx * dt;
                st.dy += st.vy * dt;

                // 明灭，其上再叠一层快速闪烁。
                var tw = 0.55 + 0.45 * Math.sin(st.phase + t * st.tws);
                tw *= 0.86 + 0.14 * Math.sin(t * 7.3 + st.phase * 3.1);
                var lit = st.lit;
                // 亮底上的可见度靠"更实的暖色"，alpha 收敛着调。
                var alpha = Math.min(1,
                    (0.2 + 0.38 * tw) * (0.35 + 0.65 * st.z) + lit * 0.4);
                var size = st.s * (0.8 + 0.35 * tw + lit * 0.8);
                var col = lit > 0.02 ? mixc(st.c, WARM, lit) : st.c.join(',');
                var rot = st.rot + lit * 0.7;

                // 衍射十字：点燃时刺变长、颜色转暖 —— 是闪光不是圆球。
                var len = size * (2.1 + 1.7 * tw + lit * 3.2);
                spike(sx, sy, len, Math.max(0.7, size * 0.16), rot, alpha * 0.5, col);
                spike(sx, sy, len * 0.8, Math.max(0.7, size * 0.14), rot + 1.5708, alpha * 0.38, col);
                // 横向拉宽的柔光条纹：玻璃把光摊开的样子。
                spike(sx, sy, len * 1.9, size * 0.5, 0, alpha * (0.08 + lit * 0.14), col);

                //  tiny 暖核 —— 唯一的圆部分，几个像素，读作"实"而非散景。
                var cr = size * 1.7;
                var g = ctx.createRadialGradient(sx, sy, 0, sx, sy, cr);
                g.addColorStop(0, 'rgba(255,252,244,' + (alpha * 0.55).toFixed(3) + ')');
                g.addColorStop(0.4, 'rgba(' + col + ',' + (alpha * 0.3).toFixed(3) + ')');
                g.addColorStop(1, 'rgba(' + col + ',0)');
                ctx.fillStyle = g;
                ctx.beginPath();
                ctx.arc(sx, sy, cr, 0, 6.2832);
                ctx.fill();

                sparkle(sx, sy, size, rot, alpha, col);
                ctx.fillStyle = 'rgba(' + col + ',' + (alpha * 0.9).toFixed(3) + ')';
                ctx.beginPath();
                ctx.arc(sx, sy, Math.max(0.4, size * 0.28), 0, 6.2832);
                ctx.fill();
            }

            // 金色流星：亮头拖着渐隐的暖金尾。
            for (i = shots.length - 1; i >= 0; i--) {
                var sh = shots[i];
                sh.life -= dt;
                if (sh.life <= 0) {
                    shots.splice(i, 1);
                    continue;
                }
                sh.x += sh.vx * dt;
                sh.y += sh.vy * dt;
                var a2 = Math.min(1, sh.life / 0.9);
                var tx2 = sh.x - sh.vx * 0.14;
                var ty2 = sh.y - sh.vy * 0.14;
                var lg = ctx.createLinearGradient(sh.x, sh.y, tx2, ty2);
                lg.addColorStop(0, 'rgba(196,154,110,' + (a2 * 0.85).toFixed(3) + ')');
                lg.addColorStop(1, 'rgba(212,165,116,0)');
                ctx.strokeStyle = lg;
                ctx.lineWidth = 1.6;
                ctx.beginPath();
                ctx.moveTo(sh.x, sh.y);
                ctx.lineTo(tx2, ty2);
                ctx.stroke();
                sparkle(sh.x, sh.y, 3.2, t * 4, a2 * 0.9, '183,110,121');
            }

            return true; // 环境层：页面可见就一直呼吸
        });

        document.addEventListener('visibilitychange', function () {
            if (!document.hidden) {
                ticker.wake();
            }
        });
    }

    Fx.onReady(function () {
        // 指针特效上岗，才给 <body> 挂 fx-live：
        // CSS 用它作"手电筒题词戴面具 / 隐藏区域系统光标"的开关，
        // 触屏与减弱动效用户永远看到完整常显的页面。
        if (enablePointerFx) {
            document.body.classList.add('fx-live');
        }

        initCursorPill();
        initPointerField();
        initCardTilt();
        initMagneticButtons();
        initNavGlide();
        initInscription();
        initAnchors();
        initParticles();

        // 粒子与光尘生来饥饿：即使指针从未移动也让循环转起来。
        if (enablePointerFx) {
            ticker.wake();
        }
    });
})();
