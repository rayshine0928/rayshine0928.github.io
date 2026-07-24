/* ============================================================
   0928.love — 噜噜和噜妹 3D Wedding Scene
   Scroll-driven 3D model showcase with Three.js
   Silky smooth rotation following page scroll position
   ============================================================ */

(function() {
    'use strict';

    function initWhenReady() {
        if (typeof THREE === 'undefined' || typeof THREE.GLTFLoader === 'undefined') {
            setTimeout(initWhenReady, 200);
            return;
        }
        startScene();
    }

    function startScene() {
        const container = document.getElementById('threeBg');
        if (!container) return;

        // Use container's actual rendered size (accounts for scrollbar, etc.)
        const rect = container.getBoundingClientRect();
        const W = rect.width || window.innerWidth;
        const H = rect.height || window.innerHeight;

        const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent)
            || W < 768;

        // --- Scene ---
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xfdf8f2);
        scene.fog = new THREE.Fog(0xfdf8f2, 8, 50);

        const camera = new THREE.PerspectiveCamera(50, W / Math.max(H, 1), 0.1, 100);
        camera.position.set(0, 1.5, 12);
        camera.lookAt(0, 0.5, 0);

        const renderer = new THREE.WebGLRenderer({ alpha: false, antialias: !isMobile });
        renderer.setSize(W, H);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = !isMobile;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;
        renderer.domElement.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;';
        container.appendChild(renderer.domElement);
        container.setAttribute('data-three', 'active');

        // ============================================================
        // LIGHTING — Warm golden wedding glow
        // ============================================================
        const ambient = new THREE.AmbientLight(0xfff5eb, 0.9);
        scene.add(ambient);

        const hemisphere = new THREE.HemisphereLight(0xffffff, 0x8d7c6b, 0.5);
        scene.add(hemisphere);

        const sunLight = new THREE.DirectionalLight(0xffeedd, 3.0);
        sunLight.position.set(8, 12, 8);
        sunLight.castShadow = !isMobile;
        if (!isMobile) {
            sunLight.shadow.mapSize.width = 1024;
            sunLight.shadow.mapSize.height = 1024;
            sunLight.shadow.camera.near = 0.5;
            sunLight.shadow.camera.far = 60;
            sunLight.shadow.camera.left = -20;
            sunLight.shadow.camera.right = 20;
            sunLight.shadow.camera.top = 20;
            sunLight.shadow.camera.bottom = -20;
            sunLight.shadow.bias = -0.0001;
            sunLight.shadow.normalBias = 0.02;
        }
        scene.add(sunLight);

        const fillLight = new THREE.DirectionalLight(0xffccaa, 0.8);
        fillLight.position.set(-4, 3, -2);
        scene.add(fillLight);

        const rimLight = new THREE.PointLight(0xffffff, 1.8, 25);
        rimLight.position.set(2, 6, -4);
        scene.add(rimLight);

        // ============================================================
        // SOFT GROUND SHADOW
        // ============================================================
        const shadowPlane = new THREE.Mesh(
            new THREE.PlaneGeometry(30, 25),
            new THREE.MeshBasicMaterial({
                color: 0x000000,
                transparent: true,
                opacity: 0.05,
                side: THREE.DoubleSide,
                depthWrite: false,
            })
        );
        shadowPlane.rotation.x = -Math.PI * 0.48;
        shadowPlane.position.set(0, -6, -4);
        shadowPlane.receiveShadow = true;
        scene.add(shadowPlane);

        // ============================================================
        // SILK RIBBONS — decorative flowing ribbons
        // ============================================================
        const ribbonColors = [
            '#E8A0B4',
            '#F0C8A0',
            '#F5E0B0',
            '#C8D8A0',
            '#A0C8D8',
            '#C0B0D8',
        ];

        const ribbons = [];
        const ribbonGroup = new THREE.Group();
        scene.add(ribbonGroup);

        function createSilkMaterial(hexColor) {
            return new THREE.MeshPhysicalMaterial({
                color: new THREE.Color(hexColor),
                metalness: 0.05,
                roughness: 0.25,
                clearcoat: 0.3,
                clearcoatRoughness: 0.25,
                sheen: 0.8,
                sheenRoughness: 0.3,
                sheenColor: new THREE.Color(0xffffff),
                specularIntensity: 0.4,
                specularColor: new THREE.Color(0xffffff),
                transparent: true,
                opacity: 0.5,
                side: THREE.DoubleSide,
                envMapIntensity: 0.5,
            });
        }

        function createRibbon(hexColor, index) {
            const total = ribbonColors.length;
            const segments = 80;
            const tubularSegments = 180;
            const radius = 0.12 + Math.random() * 0.15;

            const baseY = -8 + index * 5;
            const points = [];
            const numCP = 10;
            for (let i = 0; i < numCP; i++) {
                const t = i / (numCP - 1);
                const x = Math.sin(t * Math.PI * 2.5 + index * 1.2) * (7 + index * 0.4);
                const y = baseY + t * 16;
                const z = Math.cos(t * Math.PI * 1.8 + index * 0.7) * (5 + Math.sin(index) * 2) - 4;
                points.push(new THREE.Vector3(x, y, z));
            }

            const curve = new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.5);
            const tubeGeom = new THREE.TubeGeometry(curve, tubularSegments, radius, segments, false);
            const material = createSilkMaterial(hexColor);
            const mesh = new THREE.Mesh(tubeGeom, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;

            mesh.userData = {
                basePoints: points.map(p => p.clone()),
                index: index,
                phase: index * 0.8 + Math.random() * 0.5,
                speed: 0.3 + Math.random() * 0.5,
                amplitude: 1.5 + Math.random() * 2.5,
                curve: curve,
            };

            return mesh;
        }

        ribbonColors.forEach((color, i) => {
            const ribbon = createRibbon(color, i);
            ribbons.push(ribbon);
            ribbonGroup.add(ribbon);
        });

        // ============================================================
        // SPARKLE PARTICLES
        // ============================================================
        const sparkleCount = isMobile ? 200 : 400;
        const sPositions = new Float32Array(sparkleCount * 3);
        const sColors = new Float32Array(sparkleCount * 3);
        const sSizes = new Float32Array(sparkleCount);

        const sparklePalette = [
            [1, 0.95, 0.8],
            [1, 0.85, 0.7],
            [0.95, 0.75, 0.8],
            [0.8, 0.9, 1],
            [0.85, 1, 0.85],
        ];

        for (let i = 0; i < sparkleCount; i++) {
            sPositions[i * 3] = (Math.random() - 0.5) * 30;
            sPositions[i * 3 + 1] = (Math.random() - 0.5) * 22;
            sPositions[i * 3 + 2] = (Math.random() - 0.5) * 15;
            sSizes[i] = 0.02 + Math.random() * 0.10;

            const c = sparklePalette[Math.floor(Math.random() * sparklePalette.length)];
            sColors[i * 3] = c[0];
            sColors[i * 3 + 1] = c[1];
            sColors[i * 3 + 2] = c[2];
        }

        const sparkleGeom = new THREE.BufferGeometry();
        sparkleGeom.setAttribute('position', new THREE.BufferAttribute(sPositions, 3));
        sparkleGeom.setAttribute('color', new THREE.BufferAttribute(sColors, 3));
        sparkleGeom.setAttribute('size', new THREE.BufferAttribute(sSizes, 1));

        const sparkleCanvas = document.createElement('canvas');
        sparkleCanvas.width = 32;
        sparkleCanvas.height = 32;
        const sctx = sparkleCanvas.getContext('2d');
        const sgrad = sctx.createRadialGradient(16, 16, 0, 16, 16, 16);
        sgrad.addColorStop(0, 'rgba(255,255,255,1)');
        sgrad.addColorStop(0.02, 'rgba(255,255,240,0.95)');
        sgrad.addColorStop(0.15, 'rgba(255,220,180,0.6)');
        sgrad.addColorStop(0.5, 'rgba(200,180,160,0.1)');
        sgrad.addColorStop(1, 'rgba(0,0,0,0)');
        sctx.fillStyle = sgrad;
        sctx.fillRect(0, 0, 32, 32);

        const sparkleTex = new THREE.CanvasTexture(sparkleCanvas);
        const sparkleMat = new THREE.PointsMaterial({
            size: 0.22,
            map: sparkleTex,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            depthTest: true,
            vertexColors: true,
            transparent: true,
            opacity: 0.6,
        });

        const sparkles = new THREE.Points(sparkleGeom, sparkleMat);
        scene.add(sparkles);

        // ============================================================
        // 3D WEDDING MODEL — 噜噜和噜妹的结婚婚纱照
        // ============================================================
        let weddingModel = null;
        let weddingMixer = null;
        const modelGroup = new THREE.Group();
        scene.add(modelGroup);

        // Target values for smooth interpolation (scroll-driven)
        const modelTarget = {
            rotY: 0,
            rotX: 0,
            posY: 0,
            scale: 1,
        };
        const modelCurrent = {
            rotY: 0,
            rotX: 0,
            posY: 0,
            scale: 1,
        };

        // Scroll tracking
        let scrollY = 0;
        let targetScrollY = 0;
        let pageHeight = 1;
        let scrollProgress = 0;

        const gltfLoader = new THREE.GLTFLoader();
        const modelPath = '/img/%E5%99%9C%E5%99%9C%E5%92%8C%E5%99%9C%E5%A6%B9%E7%9A%84%E7%BB%93%E5%A9%9A%E5%A9%9A%E7%BA%B1%E7%85%A7_compressed.glb';

        gltfLoader.load(
            modelPath,
            (gltf) => {
                weddingModel = gltf.scene;

                // Auto-scale: fit model nicely in view
                const box = new THREE.Box3().setFromObject(weddingModel);
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const targetSize = isMobile ? 5 : 7;
                const scale = targetSize / maxDim;
                weddingModel.scale.setScalar(scale);

                // Center the model
                const center = box.getCenter(new THREE.Vector3());
                weddingModel.position.set(
                    -center.x * scale,
                    -center.y * scale,
                    -center.z * scale
                );

                // Enable shadows
                weddingModel.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });

                // Handle animations
                if (gltf.animations && gltf.animations.length > 0) {
                    weddingMixer = new THREE.AnimationMixer(weddingModel);
                    gltf.animations.forEach((clip) => {
                        const action = weddingMixer.clipAction(clip);
                        action.play();
                    });
                }

                modelGroup.add(weddingModel);

                // Fade in
                weddingModel.traverse((child) => {
                    if (child.isMesh && child.material) {
                        child.material.transparent = true;
                        child.material.opacity = 0;
                    }
                });

                console.log('💒 Wedding model loaded!',
                    'animations:', gltf.animations ? gltf.animations.length : 0,
                    'size:', size.toArray().map(v => v.toFixed(2)));
            },
            (progress) => {
                if (progress.total > 0) {
                    const pct = Math.round((progress.loaded / progress.total) * 100);
                    console.log('💒 Loading wedding model...', pct + '%');
                }
            },
            (error) => {
                console.warn('⚠️ Wedding model failed to load:', error);
            }
        );

        // ============================================================
        // SCROLL-DRIVEN ANIMATION LOGIC
        // ============================================================

        function updateScrollState() {
            targetScrollY = window.pageYOffset;
            pageHeight = Math.max(
                document.body.scrollHeight - window.innerHeight,
                1
            );
            scrollProgress = targetScrollY / pageHeight;

            // --- Model rotation driven by scroll ---
            // Full 360° rotation over the entire page scroll
            // Start at a flattering 3/4 angle, spin 360° through the page
            const baseAngle = Math.PI * 0.2 - Math.PI / 4; // clockwise 45° from default
            modelTarget.rotY = baseAngle + scrollProgress * Math.PI * 2;

            // Gentle X tilt: model tilts back slightly in middle, forward at top/bottom
            modelTarget.rotX = Math.sin(scrollProgress * Math.PI) * 0.25;

            // Subtle vertical float based on scroll
            modelTarget.posY = Math.sin(scrollProgress * Math.PI * 2) * 0.8;

            // Subtle scale pulse at key moments (hero section: slightly larger)
            if (scrollProgress < 0.15) {
                modelTarget.scale = 1 + (0.15 - scrollProgress) / 0.15 * 0.08;
            } else {
                modelTarget.scale = 1;
            }
        }

        // ============================================================
        // MOUSE INPUT — subtle parallax overlay
        // ============================================================
        const mouse = { x: 0, y: 0, tx: 0, ty: 0 };
        document.addEventListener('mousemove', e => {
            mouse.tx = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.ty = -(e.clientY / window.innerHeight) * 2 + 1;
        });
        document.addEventListener('touchmove', e => {
            const t = e.touches[0];
            mouse.tx = (t.clientX / window.innerWidth) * 2 - 1;
            mouse.ty = -(t.clientY / window.innerHeight) * 2 + 1;
        }, { passive: true });

        // ============================================================
        // SECTION DETECTION — for dynamic environment
        // ============================================================
        const sections = ['hero', 'invitation', 'countdown', 'story', 'schedule', 'venue', 'rsvp'];
        let currentSection = 'hero';

        function detectSection() {
            const sy = window.pageYOffset;
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
        // MAIN ANIMATION LOOP
        // ============================================================
        const clock = new THREE.Clock();

        function animate() {
            requestAnimationFrame(animate);
            const dt = Math.min(clock.getDelta(), 0.1);
            const time = performance.now() * 0.001;

            // --- Update scroll state ---
            updateScrollState();
            detectSection();

            // Smooth scroll following (lerp for silky motion)
            scrollY += (targetScrollY - scrollY) * 0.08;

            // --- Mouse smoothing ---
            mouse.x += (mouse.tx - mouse.x) * 0.04;
            mouse.y += (mouse.ty - mouse.y) * 0.04;

            // --- Smooth model transform interpolation ---
            const lerpSpeed = 0.06; // lower = smoother/silkier
            modelCurrent.rotY += (modelTarget.rotY - modelCurrent.rotY) * lerpSpeed;
            modelCurrent.rotX += (modelTarget.rotX - modelCurrent.rotX) * lerpSpeed;
            modelCurrent.posY += (modelTarget.posY - modelCurrent.posY) * lerpSpeed;
            modelCurrent.scale += (modelTarget.scale - modelCurrent.scale) * lerpSpeed;

            // --- Apply transforms to model group ---
            modelGroup.rotation.y = modelCurrent.rotY;
            modelGroup.rotation.x = modelCurrent.rotX;
            modelGroup.position.y = modelCurrent.posY;
            modelGroup.scale.setScalar(modelCurrent.scale);

            // --- Mouse parallax on top of scroll rotation ---
            modelGroup.rotation.y += mouse.x * 0.3;
            modelGroup.rotation.x += mouse.y * 0.15;

            // --- Camera subtle response to scroll ---
            const camBaseZ = 12;
            const camBaseY = 1.5;
            const camZ = camBaseZ + Math.sin(scrollProgress * Math.PI) * 1.5;
            const camY = camBaseY + scrollProgress * 0.8;
            camera.position.z += (camZ - camera.position.z) * 0.03;
            camera.position.y += (camY - camera.position.y) * 0.03;
            camera.position.x += (mouse.x * 1.5 - camera.position.x) * 0.03;
            camera.lookAt(0, modelCurrent.posY, 0);

            // --- Section-driven environment ---
            let ribbonOpacityTarget = 0.5;
            let sparkleOpacityTarget = 0.6;
            let sunIntensityTarget = 3.0;

            switch (currentSection) {
                case 'hero':
                    ribbonOpacityTarget = 0.6; sparkleOpacityTarget = 0.75;
                    sunIntensityTarget = 3.5;
                    break;
                case 'countdown':
                    ribbonOpacityTarget = 0.5; sparkleOpacityTarget = 0.85;
                    sunIntensityTarget = 2.5;
                    break;
                case 'venue':
                    ribbonOpacityTarget = 0.35; sparkleOpacityTarget = 0.45;
                    sunIntensityTarget = 2.0;
                    break;
                default:
                    ribbonOpacityTarget = 0.3; sparkleOpacityTarget = 0.35;
                    sunIntensityTarget = 1.8;
            }

            sunLight.intensity += (sunIntensityTarget - sunLight.intensity) * 0.025;

            // --- Animate silk ribbons ---
            ribbons.forEach((ribbon, idx) => {
                const ud = ribbon.userData;
                const bp = ud.basePoints;

                const newPoints = bp.map((p, i) => {
                    const t = i / (bp.length - 1);
                    const waveX = Math.sin(time * ud.speed * 1.3 + t * 3 + ud.phase) * ud.amplitude;
                    const waveY = Math.cos(time * ud.speed * 0.7 + t * 2.5 + ud.phase) * ud.amplitude * 0.6;
                    const waveZ = Math.sin(time * ud.speed * 0.9 + t * 2 + ud.phase + 1.5) * ud.amplitude * 0.8;
                    const driftX = Math.sin(time * 0.2 + ud.phase) * 1.5;
                    const driftZ = Math.cos(time * 0.25 + ud.phase) * 1.2;

                    return new THREE.Vector3(
                        p.x + waveX + driftX,
                        p.y + waveY,
                        p.z + waveZ + driftZ
                    );
                });

                const curve = new THREE.CatmullRomCurve3(newPoints, false, 'catmullrom', 0.5);
                const tubularSegments = 180;
                const segments = 80;
                const radius = 0.12 + idx * 0.03;
                const newGeom = new THREE.TubeGeometry(curve, tubularSegments, radius, segments, false);

                ribbon.geometry.dispose();
                ribbon.geometry = newGeom;
                ribbon.userData.curve = curve;

                ribbon.material.opacity += (ribbonOpacityTarget - ribbon.material.opacity) * 0.03;
            });

            // --- Sparkle animation ---
            sparkleMat.opacity += (sparkleOpacityTarget - sparkleMat.opacity) * 0.03;
            sparkles.rotation.y += dt * 0.04;
            sparkles.rotation.x += dt * 0.02;

            const sparklePosArr = sparkles.geometry.attributes.position.array;
            for (let i = 0; i < Math.min(sparkleCount, sparklePosArr.length / 3); i++) {
                sparklePosArr[i * 3 + 1] += dt * (0.04 + Math.sin(i) * 0.03);
                if (sparklePosArr[i * 3 + 1] > 13) sparklePosArr[i * 3 + 1] = -13;
            }
            sparkles.geometry.attributes.position.needsUpdate = true;

            // --- Sunlight gentle orbit ---
            const sunAngle = time * 0.08;
            sunLight.position.x = 8 + Math.sin(sunAngle) * 3;
            sunLight.position.z = 8 + Math.cos(sunAngle) * 3;
            rimLight.intensity = 1.2 + Math.sin(time * 0.5) * 0.6;

            // --- Ribbon group slow rotation ---
            ribbonGroup.rotation.y += dt * 0.02;

            // --- Wedding model animation ---
            if (weddingModel) {
                // Fade in
                weddingModel.traverse((child) => {
                    if (child.isMesh && child.material && child.material.opacity < 1) {
                        child.material.opacity = Math.min(1, child.material.opacity + dt * 0.6);
                    }
                });

                // Update animation mixer
                if (weddingMixer) {
                    weddingMixer.update(dt);
                }
            }

            renderer.render(scene, camera);
        }

        // ============================================================
        // RESIZE
        // ============================================================
        window.addEventListener('resize', () => {
            const rect = container.getBoundingClientRect();
            const w = rect.width || window.innerWidth;
            const h = rect.height || window.innerHeight;
            if (w <= 0 || h <= 0) return;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        // ============================================================
        // KICK OFF
        // ============================================================
        updateScrollState();
        animate();
        console.log('💒 Wedding 3D scene live — scroll to spin the model! ✨');
    }

    // Delay init by one frame to ensure layout is fully settled
    requestAnimationFrame(() => { initWhenReady(); });
})();
