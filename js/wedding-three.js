/* ============================================================
   0928.love — Dramatic Three.js Wedding Scene v4
   Giant rings, galaxy swirl, heart bursts, fireflies, crystals
   ============================================================ */

(function() {
    'use strict';

    function initWhenReady() {
        if (typeof THREE === 'undefined') { setTimeout(initWhenReady, 200); return; }
        startScene();
    }

    function startScene() {
        const container = document.getElementById('threeBg');
        if (!container) return;

        const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent)
            || window.innerWidth < 768;

        const W = window.innerWidth;
        const H = window.innerHeight;

        // --- Scene ---
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0305);
        scene.fog = new THREE.FogExp2(0x0a0305, 0.00008);

        const camera = new THREE.PerspectiveCamera(60, W / H, 0.1, 120);
        camera.position.set(0, 2, 24);
        camera.lookAt(0, 0, -2);

        const renderer = new THREE.WebGLRenderer({ alpha: false, antialias: !isMobile });
        renderer.setSize(W, H);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.domElement.style.cssText = 'position:absolute;top:0;left:0;';
        container.appendChild(renderer.domElement);
        container.setAttribute('data-three', 'active');

        // --- Lighting ---
        scene.add(new THREE.AmbientLight(0x2a1015, 0.5));
        const key = new THREE.PointLight(0xffc080, 3, 40, 1.5);
        key.position.set(8, 5, 10); scene.add(key);
        const fill = new THREE.PointLight(0xff7090, 2, 30, 1.5);
        fill.position.set(-6, -3, 6); scene.add(fill);
        const rim = new THREE.PointLight(0xffffff, 1.5, 25, 2);
        rim.position.set(0, 6, -8); scene.add(rim);

        // ============================================================
        // 1. GIANT WEDDING RINGS — dramatic, crossing
        // ============================================================
        const ringPivot = new THREE.Group();
        scene.add(ringPivot);

        const ringGroup = new THREE.Group();
        ringPivot.add(ringGroup);
        ringGroup.position.set(0, 0, 0);

        const ring1 = new THREE.Mesh(
            new THREE.TorusGeometry(7, 0.18, 48, 160),
            new THREE.MeshStandardMaterial({
                color: 0xd4a574, emissive: 0xd4a574, emissiveIntensity: 1.5,
                metalness: 0.95, roughness: 0.12, transparent: true, opacity: 0.8,
            })
        );
        ring1.rotation.set(Math.PI * 0.5, 0, 0);
        ringGroup.add(ring1);

        const ring2 = new THREE.Mesh(
            new THREE.TorusGeometry(6.5, 0.18, 48, 160),
            new THREE.MeshStandardMaterial({
                color: 0xb76e79, emissive: 0xb76e79, emissiveIntensity: 1.3,
                metalness: 0.95, roughness: 0.12, transparent: true, opacity: 0.8,
            })
        );
        ring2.rotation.set(Math.PI * 0.3, Math.PI * 0.15, 0);
        ringGroup.add(ring2);

        // Diamond cluster at ring center
        const diamondGroup = new THREE.Group();
        ringGroup.add(diamondGroup);

        const mainDiamond = new THREE.Mesh(
            new THREE.OctahedronGeometry(0.4, 0),
            new THREE.MeshStandardMaterial({
                color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2.5,
                roughness: 0, metalness: 0.1,
            })
        );
        diamondGroup.add(mainDiamond);

        // Orbiting crystals around diamond
        const crystals = [];
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            const cGeom = new THREE.OctahedronGeometry(0.08, 0);
            const cMat = new THREE.MeshStandardMaterial({
                color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 1.5,
                roughness: 0,
            });
            const crystal = new THREE.Mesh(cGeom, cMat);
            crystal.userData = { angle, radius: 0.8 + Math.random() * 0.3, speed: 0.5 + Math.random(), yOff: (Math.random() - 0.5) * 0.6 };
            crystal.position.set(
                Math.cos(angle) * crystal.userData.radius,
                crystal.userData.yOff,
                Math.sin(angle) * crystal.userData.radius
            );
            diamondGroup.add(crystal);
            crystals.push(crystal);
        }

        ringPivot.position.set(0, 1, -4);

        // ============================================================
        // 2. GALAXY SPIRAL PARTICLES
        // ============================================================
        const galaxyCount = isMobile ? 400 : 800;
        const gPositions = new Float32Array(galaxyCount * 3);
        const gColors = new Float32Array(galaxyCount * 3);
        const gSizes = new Float32Array(galaxyCount);

        for (let i = 0; i < galaxyCount; i++) {
            // Logarithmic spiral
            const t = (i / galaxyCount) * Math.PI * 6;
            const radius = 2 + t * 0.8;
            const spread = 0.3 + Math.random() * 1.5;
            const theta = t + (Math.random() - 0.5) * 1.2;

            gPositions[i * 3] = Math.cos(theta) * (radius + (Math.random() - 0.5) * spread * 4);
            gPositions[i * 3 + 1] = (Math.random() - 0.5) * spread * 3;
            gPositions[i * 3 + 2] = Math.sin(theta) * (radius + (Math.random() - 0.5) * spread * 4);

            gSizes[i] = 0.06 + (1 - i / galaxyCount) * 0.25;

            const mix = i / galaxyCount;
            const c = new THREE.Color();
            c.setHSL(0.1 + mix * 0.08, 0.6, 0.5 + mix * 0.5);
            gColors[i * 3] = c.r;
            gColors[i * 3 + 1] = c.g;
            gColors[i * 3 + 2] = c.b;
        }

        const galaxyGeom = new THREE.BufferGeometry();
        galaxyGeom.setAttribute('position', new THREE.BufferAttribute(gPositions, 3));
        galaxyGeom.setAttribute('color', new THREE.BufferAttribute(gColors, 3));
        galaxyGeom.setAttribute('size', new THREE.BufferAttribute(gSizes, 1));

        const galaxyMat = new THREE.PointsMaterial({
            size: 0.35,
            map: createGlowTexture(),
            blending: THREE.AdditiveBlending,
            depthWrite: false, depthTest: true,
            vertexColors: true, transparent: true, opacity: 0.8,
        });

        const galaxy = new THREE.Points(galaxyGeom, galaxyMat);
        galaxy.rotation.x = Math.PI * 0.25;
        scene.add(galaxy);

        // ============================================================
        // 3. FIREFLY SWARMS — organic clusters
        // ============================================================
        const swarmCount = isMobile ? 6 : 12;
        const firefliesPerSwarm = isMobile ? 15 : 30;
        const swarms = [];

        for (let s = 0; s < swarmCount; s++) {
            const ffCount = firefliesPerSwarm;
            const ffPositions = new Float32Array(ffCount * 3);
            const ffColors = new Float32Array(ffCount * 3);
            const ffSizes = new Float32Array(ffCount);

            const center = {
                x: (Math.random() - 0.5) * 30,
                y: (Math.random() - 0.5) * 20,
                z: (Math.random() - 0.5) * 15,
            };

            for (let i = 0; i < ffCount; i++) {
                ffPositions[i * 3] = center.x + (Math.random() - 0.5) * 4;
                ffPositions[i * 3 + 1] = center.y + (Math.random() - 0.5) * 3;
                ffPositions[i * 3 + 2] = center.z + (Math.random() - 0.5) * 4;
                ffSizes[i] = 0.04 + Math.random() * 0.15;
                const c = new THREE.Color().setHSL(0.12 + Math.random() * 0.05, 0.5, 0.7 + Math.random() * 0.3);
                ffColors[i * 3] = c.r;
                ffColors[i * 3 + 1] = c.g;
                ffColors[i * 3 + 2] = c.b;
            }

            const ffGeom = new THREE.BufferGeometry();
            ffGeom.setAttribute('position', new THREE.BufferAttribute(ffPositions, 3));
            ffGeom.setAttribute('color', new THREE.BufferAttribute(ffColors, 3));
            ffGeom.setAttribute('size', new THREE.BufferAttribute(ffSizes, 1));

            const ffMat = new THREE.PointsMaterial({
                size: 0.25,
                map: createGlowTexture(),
                blending: THREE.AdditiveBlending,
                depthWrite: false, depthTest: true,
                vertexColors: true, transparent: true, opacity: 0.9,
            });

            const ffMesh = new THREE.Points(ffGeom, ffMat);
            ffMesh.userData = {
                center,
                phase: Math.random() * Math.PI * 2,
                speed: 0.2 + Math.random() * 0.6,
                amplitude: 2 + Math.random() * 4,
            };
            scene.add(ffMesh);
            swarms.push(ffMesh);
        }

        // ============================================================
        // 4. HEART CONSTELLATION — particles that form a heart
        // ============================================================
        const heartCount = 200;
        const heartPositions = new Float32Array(heartCount * 3);
        const heartRandom = new Float32Array(heartCount * 3);
        const heartColors = new Float32Array(heartCount * 3);
        const heartSizes = new Float32Array(heartCount);

        // Precompute heart shape
        for (let i = 0; i < heartCount; i++) {
            const t = (i / heartCount) * Math.PI * 2;
            const x = 16 * Math.pow(Math.sin(t), 3);
            const y = 13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t);
            heartPositions[i * 3] = x * 0.35;
            heartPositions[i * 3 + 1] = y * 0.35;
            heartPositions[i * 3 + 2] = (Math.random() - 0.5) * 2;

            // Random scattered positions
            heartRandom[i * 3] = (Math.random() - 0.5) * 25;
            heartRandom[i * 3 + 1] = (Math.random() - 0.5) * 20;
            heartRandom[i * 3 + 2] = (Math.random() - 0.5) * 12;

            heartSizes[i] = 0.05 + Math.random() * 0.2;

            const c = new THREE.Color().setHSL(0.93 + Math.random() * 0.07, 0.6, 0.6 + Math.random() * 0.4);
            heartColors[i * 3] = c.r;
            heartColors[i * 3 + 1] = c.g;
            heartColors[i * 3 + 2] = c.b;
        }

        const heartGeom = new THREE.BufferGeometry();
        heartGeom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(heartCount * 3), 3));
        heartGeom.setAttribute('color', new THREE.BufferAttribute(heartColors, 3));
        heartGeom.setAttribute('size', new THREE.BufferAttribute(heartSizes, 1));

        const heartMat = new THREE.PointsMaterial({
            size: 0.3,
            map: createGlowTexture('#ff8899'),
            blending: THREE.AdditiveBlending,
            depthWrite: false, depthTest: true,
            vertexColors: true, transparent: true, opacity: 0,
        });

        const heartMesh = new THREE.Points(heartGeom, heartMat);
        heartMesh.position.set(0, 2, -6);
        scene.add(heartMesh);

        // ============================================================
        // 5. FLOATING "09.28" — box geometry forming numbers
        // ============================================================
        const dateGroup = new THREE.Group();
        dateGroup.position.set(0, -6, -10);
        scene.add(dateGroup);

        // Create "0928" with small cubes in a pixel-art style
        function createDigit(digit, offsetX) {
            const patterns = {
                '0': ['111','101','101','101','111'],
                '2': ['111','001','111','100','111'],
                '8': ['111','101','111','101','111'],
                '9': ['111','101','111','001','111'],
                '·': ['000','000','010','000','000'],
            };
            const pattern = patterns[digit] || patterns['0'];
            const group = new THREE.Group();
            const size = 0.22;
            const gap = 0.26;

            for (let row = 0; row < 5; row++) {
                for (let col = 0; col < 3; col++) {
                    if (pattern[row][col] === '1') {
                        const box = new THREE.Mesh(
                            new THREE.BoxGeometry(size, size, size * 0.5),
                            new THREE.MeshStandardMaterial({
                                color: 0xd4a574, emissive: 0xd4a574, emissiveIntensity: 0.8,
                                metalness: 0.3, roughness: 0.4, transparent: true, opacity: 0.7,
                            })
                        );
                        box.position.set(col * gap, (4 - row) * gap, 0);
                        group.add(box);
                    }
                }
            }
            group.position.x = offsetX;
            return group;
        }

        dateGroup.add(createDigit('0', -4.5));
        dateGroup.add(createDigit('9', -2.8));
        dateGroup.add(createDigit('·', -1.2));
        dateGroup.add(createDigit('2', 0.0));
        dateGroup.add(createDigit('8', 1.7));

        // ============================================================
        // UTILITY: Glow texture
        // ============================================================
        function createGlowTexture(tint) {
            const cvs = document.createElement('canvas'); cvs.width = 64; cvs.height = 64;
            const ctx = cvs.getContext('2d');
            const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
            grad.addColorStop(0, 'rgba(255,255,255,1)');
            grad.addColorStop(0.06, 'rgba(255,240,220,0.95)');
            grad.addColorStop(0.3, tint ? 'rgba(255,150,160,0.4)' : 'rgba(220,180,140,0.4)');
            grad.addColorStop(0.7, 'rgba(100,40,50,0.04)');
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad; ctx.fillRect(0, 0, 64, 64);
            return new THREE.CanvasTexture(cvs);
        }

        // ============================================================
        // SECTION DETECTION
        // ============================================================
        const sections = ['hero', 'invitation', 'countdown', 'story', 'schedule', 'venue', 'gallery', 'rsvp'];
        let currentSection = 'hero';

        function detectSection() {
            const scrollY = window.pageYOffset;
            const vh = window.innerHeight;
            let best = 'hero', bestDist = Infinity;
            sections.forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                const rect = el.getBoundingClientRect();
                const dist = Math.abs(rect.top + rect.height * 0.4 - vh * 0.4);
                if (dist < bestDist) { bestDist = dist; best = id; }
            });
            if (best !== currentSection) {
                currentSection = best;
                container.setAttribute('data-section', currentSection);
            }
            return currentSection;
        }

        // ============================================================
        // ANIMATION LOOP
        // ============================================================
        const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
        document.addEventListener('mousemove', e => {
            mouse.tx = (e.clientX / W) * 2 - 1;
            mouse.ty = -(e.clientY / H) * 2 + 1;
        });
        document.addEventListener('touchmove', e => {
            const t = e.touches[0];
            mouse.tx = (t.clientX / W) * 2 - 1;
            mouse.ty = -(t.clientY / H) * 2 + 1;
        }, { passive: true });

        const clock = new THREE.Clock();
        let heartFormTimer = 0;
        let heartVisible = false;

        function animate() {
            requestAnimationFrame(animate);
            const dt = Math.min(clock.getDelta(), 0.1);
            const time = performance.now() * 0.001;

            detectSection();
            mouse.x += (mouse.tx - mouse.x) * 0.03;
            mouse.y += (mouse.ty - mouse.y) * 0.03;

            // Dramatic camera orbit
            const camRadius = 24;
            const camAngle = time * 0.08 + mouse.x * 0.5;
            camera.position.x += (Math.sin(camAngle) * camRadius * 0.3 - camera.position.x) * 0.015;
            camera.position.y += (2 + mouse.y * 4 - camera.position.y) * 0.02;
            camera.position.z += (camRadius - camera.position.z) * 0.015;
            camera.lookAt(0, 0, -2);

            // --- Section-driven parameters ---
            let ringOpacityTarget = 0.8, galaxyOpacityTarget = 0.8;
            let heartOpacityTarget = 0, dateOpacityTarget = 0.6;

            switch (currentSection) {
                case 'hero':
                    ringOpacityTarget = 0.85; galaxyOpacityTarget = 0.85;
                    heartOpacityTarget = 0.9; dateOpacityTarget = 0.7;
                    break;
                case 'countdown':
                    ringOpacityTarget = 1.0; galaxyOpacityTarget = 0.9;
                    heartOpacityTarget = 0.3; dateOpacityTarget = 0.9;
                    break;
                case 'venue':
                    ringOpacityTarget = 0.6; galaxyOpacityTarget = 0.6;
                    heartOpacityTarget = 0; dateOpacityTarget = 0.4;
                    break;
                default:
                    ringOpacityTarget = 0.4; galaxyOpacityTarget = 0.5;
                    heartOpacityTarget = 0; dateOpacityTarget = 0.3;
            }

            // Smooth transitions
            ring1.material.opacity += (ringOpacityTarget - ring1.material.opacity) * 0.03;
            ring2.material.opacity += (ringOpacityTarget - ring2.material.opacity) * 0.03;
            galaxyMat.opacity += (galaxyOpacityTarget - galaxyMat.opacity) * 0.03;
            heartMat.opacity += (heartOpacityTarget - heartMat.opacity) * 0.03;

            dateGroup.children.forEach(g => {
                g.children.forEach(b => {
                    b.material.opacity += (dateOpacityTarget - b.material.opacity) * 0.03;
                });
            });

            // --- Ring animation ---
            ring1.rotation.z += dt * 0.25;
            ring1.rotation.x += dt * 0.12;
            ring2.rotation.z -= dt * 0.2;
            ring2.rotation.y += dt * 0.15;
            ringGroup.rotation.y += dt * 0.08;
            ringGroup.position.y = Math.sin(time * 0.35) * 1.2;
            ringGroup.rotation.x = Math.sin(time * 0.25) * 0.2;

            // --- Diamond pulse ---
            const pulse = 1 + Math.sin(time * 4) * 0.5 + Math.sin(time * 9) * 0.35;
            mainDiamond.scale.setScalar(pulse);
            mainDiamond.rotation.y += dt * 2;
            mainDiamond.rotation.x += dt;

            // Orbiting crystals
            crystals.forEach(c => {
                c.userData.angle += dt * c.userData.speed;
                const a = c.userData.angle;
                c.position.x = Math.cos(a) * c.userData.radius;
                c.position.z = Math.sin(a) * c.userData.radius;
                c.position.y = c.userData.yOff + Math.sin(time * 2 + a) * 0.3;
                c.scale.setScalar(0.6 + Math.sin(time * 5 + a) * 0.4);
            });

            // --- Galaxy rotation ---
            galaxy.rotation.y += dt * 0.04;
            galaxy.rotation.z += dt * 0.02;

            // --- Firefly swarms — organic motion ---
            swarms.forEach(swarm => {
                const ud = swarm.userData;
                ud.center.x += Math.sin(time * ud.speed + ud.phase) * dt * ud.amplitude * 0.5;
                ud.center.y += Math.cos(time * ud.speed * 0.7 + ud.phase) * dt * ud.amplitude * 0.3;
                ud.center.z += Math.cos(time * ud.speed * 0.5 + ud.phase + 1) * dt * ud.amplitude * 0.4;

                const pos = swarm.geometry.attributes.position.array;
                for (let i = 0; i < pos.length / 3; i++) {
                    pos[i * 3] += (ud.center.x + (Math.sin(time * 3 + i) * 2) - pos[i * 3]) * 0.02;
                    pos[i * 3 + 1] += (ud.center.y + (Math.cos(time * 2.5 + i) * 1.5) - pos[i * 3 + 1]) * 0.02;
                    pos[i * 3 + 2] += (ud.center.z + (Math.cos(time * 3.3 + i) * 2) - pos[i * 3 + 2]) * 0.02;
                }
                swarm.geometry.attributes.position.needsUpdate = true;

                // Swarm opacity follows ring opacity
                swarm.material.opacity += (ringOpacityTarget * 0.7 - swarm.material.opacity) * 0.03;
            });

            // --- Heart constellation — form every 8 seconds ---
            heartFormTimer += dt;
            const heartCycle = 8;
            const heartFormDuration = 2;
            const heartHoldDuration = 2.5;
            const phaseInCycle = heartFormTimer % heartCycle;

            let heartMix = 0; // 0 = scattered, 1 = heart shape
            if (phaseInCycle < heartFormDuration) {
                heartMix = phaseInCycle / heartFormDuration; // forming
                if (!heartVisible) { heartVisible = true; }
            } else if (phaseInCycle < heartFormDuration + heartHoldDuration) {
                heartMix = 1; // holding
            } else if (phaseInCycle < heartFormDuration * 2 + heartHoldDuration) {
                heartMix = 1 - (phaseInCycle - heartFormDuration - heartHoldDuration) / heartFormDuration; // dispersing
            } else {
                heartMix = 0;
                heartVisible = false;
            }

            // Apply heart morph
            const hPos = heartMesh.geometry.attributes.position.array;
            for (let i = 0; i < heartCount; i++) {
                hPos[i * 3] = heartRandom[i * 3] + (heartPositions[i * 3] - heartRandom[i * 3]) * heartMix;
                hPos[i * 3 + 1] = heartRandom[i * 3 + 1] + (heartPositions[i * 3 + 1] - heartRandom[i * 3 + 1]) * heartMix;
                hPos[i * 3 + 2] = heartRandom[i * 3 + 2] + (heartPositions[i * 3 + 2] - heartRandom[i * 3 + 2]) * heartMix;
            }
            heartMesh.geometry.attributes.position.needsUpdate = true;

            // --- Date group float ---
            dateGroup.position.y += (-6 + Math.sin(time * 0.5) * 1.5 - dateGroup.position.y) * 0.02;
            dateGroup.rotation.y += dt * 0.1;

            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            const w = window.innerWidth, h = window.innerHeight;
            camera.aspect = w / h; camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        animate();
        console.log('💒 Three.js dramatic scene v4 live');
    }

    initWhenReady();
})();
