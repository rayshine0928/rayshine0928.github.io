/**
 * fx-core.js — 0928.love 特效共享内核（v26，移植自 LogosCaller fx-core）
 *
 * 暴露 window.LoveFx：
 *  - ticker: 全站唯一的 rAF 循环。订阅者收到 dt（秒，已封顶），
 *    返回 true 表示"还需要下一帧"；无人饥饿时循环自动停摆，
 *    wake() 可随时唤醒。
 *  - pointer: 光标实时位置 + 平滑速度（px/s，跳跃不计入速度）。
 *  - smooth()/clamp()/each()/onReady(): 共享数学与 DOM 工具。
 *  - env: 能力标记（finePointer / reduceMotion / enablePointerFx）。
 *
 * 在 _layouts/wedding.html 中最先加载。其余特效模块都以
 * window.LoveFx 作守卫——内核缺失时降级为"无特效"，而非报错。
 */
(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var finePointer = window.matchMedia('(pointer: fine)').matches;

    // --------------------------------------------------------
    // 共享 ticker —— 一个 rAF 循环喂养所有特效
    // --------------------------------------------------------
    var ticker = (function () {
        var subscribers = [];
        var rafId = null;
        var last = 0;

        function frame(now) {
            rafId = null;
            var dt = last ? Math.min((now - last) / 1000, 0.064) : 1 / 60;
            last = now;

            var hungry = false;
            for (var i = 0; i < subscribers.length; i++) {
                if (subscribers[i](dt)) {
                    hungry = true;
                }
            }

            if (hungry) {
                rafId = requestAnimationFrame(frame);
            } else {
                last = 0;
            }
        }

        return {
            add: function (fn) {
                subscribers.push(fn);
            },
            wake: function () {
                if (rafId === null) {
                    rafId = requestAnimationFrame(frame);
                }
            }
        };
    })();

    // --------------------------------------------------------
    // 指针状态（位置 + 平滑速度）
    // --------------------------------------------------------
    var pointer = { x: window.innerWidth / 2, y: window.innerHeight / 2, vx: 0, vy: 0, speed: 0 };

    (function () {
        var lastX = pointer.x;
        var lastY = pointer.y;
        var lastT = 0;
        var VEL_TAU = 0.08;

        window.addEventListener('pointermove', function (e) {
            var now = performance.now();
            var gap = lastT ? (now - lastT) / 1000 : Infinity;
            var dt = Math.min(gap, 0.1);
            lastT = now;

            // 间隔过长说明光标是"瞬移"（首次移动 / 从别的屏幕回来 /
            // 长停顿）：跳跃不是运动，不能计入速度。
            var jump = gap > 0.25;
            var ivx = jump ? 0 : (e.clientX - lastX) / dt;
            var ivy = jump ? 0 : (e.clientY - lastY) / dt;
            lastX = e.clientX;
            lastY = e.clientY;

            pointer.x = e.clientX;
            pointer.y = e.clientY;

            var k = 1 - Math.exp(-dt / VEL_TAU);
            pointer.vx += (ivx - pointer.vx) * k;
            pointer.vy += (ivy - pointer.vy) * k;
            pointer.speed = Math.sqrt(pointer.vx * pointer.vx + pointer.vy * pointer.vy);

            ticker.wake();
        }, { passive: true });

        // 指针停下后不再有 pointermove 事件，速度需要自行衰减到 0，
        // 让可停摆的订阅者看到衰减过程：每次移动后跑一小段松弛循环。
        ticker.add(function (dt) {
            if (pointer.speed < 1) {
                pointer.vx = pointer.vy = pointer.speed = 0;
                return false;
            }
            var k = 1 - Math.exp(-dt / VEL_TAU);
            pointer.vx += (0 - pointer.vx) * k;
            pointer.vy += (0 - pointer.vy) * k;
            pointer.speed = Math.sqrt(pointer.vx * pointer.vx + pointer.vy * pointer.vy);
            return true;
        });
    })();

    // --------------------------------------------------------
    // 工具
    // --------------------------------------------------------
    function smooth(current, target, tau, dt) {
        return current + (target - current) * (1 - Math.exp(-dt / tau));
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function each(list, fn) {
        Array.prototype.forEach.call(list, fn);
    }

    function onReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    window.LoveFx = {
        ticker: ticker,
        pointer: pointer,
        smooth: smooth,
        clamp: clamp,
        each: each,
        onReady: onReady,
        env: {
            reduceMotion: reduceMotion,
            finePointer: finePointer,
            enablePointerFx: finePointer && !reduceMotion
        }
    };
})();
