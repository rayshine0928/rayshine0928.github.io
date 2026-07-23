/* ============================================================
   0928.love — Rainbow Silk Ribbons + Sunlight Scene
   Flowing silk scarves drifting through 3D space
   Warm golden sunlight, soft shadows, premium elegance
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

        const isMobile = /Android|iPhone|iPad|iPod|webOS/i.test(navigator.userAgent)
            || window.innerWidth < 768;

        const W = window.innerWidth;
        const H = window.innerHeight;

        // --- Scene ---
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xfdf8f2); // warm cream
        scene.fog = new THREE.Fog(0xfdf8f2, 15, 60);

        const camera = new THREE.PerspectiveCamera(55, W / H, 0.1, 100);
        camera.position.set(0, 1, 28);
        camera.lookAt(0, 1, 0);

        const renderer = new THREE.WebGLRenderer({ alpha: false, antialias: !isMobile });
        renderer.setSize(W, H);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = !isMobile;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
        renderer.domElement.style.cssText = 'position:absolute;top:0;left:0;';
        container.appendChild(renderer.domElement);
        container.setAttribute('data-three', 'active');

        // ============================================================
        // LIGHTING — Golden sunlight simulation
        // ============================================================
        const ambient = new THREE.AmbientLight(0xfff5eb, 0.8);
        scene.add(ambient);

        const hemisphere = new THREE.HemisphereLight(0xffffff, 0x8d7c6b, 0.4);
        scene.add(hemisphere);

        // Main "sun" directional light — warm golden
        const sunLight = new THREE.DirectionalLight(0xffeedd, 2.5);
        sunLight.position.set(12, 18, 8);
        sunLight.castShadow = !isMobile;
        if (!isMobile) {
            sunLight.shadow.mapSize.width = 1024;
            sunLight.shadow.mapSize.height = 1024;
            sunLight.shadow.camera.near = 0.5;
            sunLight.shadow.camera.far = 80;
            sunLight.shadow.camera.left = -25;
            sunLight.shadow.camera.right = 25;
            sunLight.shadow.camera.top = 25;
            sunLight.shadow.camera.bottom = -25;
            sunLight.shadow.bias = -0.0001;
            sunLight.shadow.normalBias = 0.02;
        }
        scene.add(sunLight);

        // Warm fill light
        const fillLight = new THREE.DirectionalLight(0xffccaa, 0.6);
        fillLight.position.set(-5, 3, -3);
        scene.add(fillLight);

        // Subtle rim light for silk sheen
        const rimLight = new THREE.PointLight(0xffffff, 1.5, 30);
        rimLight.position.set(3, 8, -5);
        scene.add(rimLight);

        // ============================================================
        // RAINBOW SILK RIBBONS
        // ============================================================
        const ribbonColors = [
            '#E8A0B4', // soft rose
            '#F0C8A0', // warm peach
            '#F5E0B0', // pale gold
            '#C8D8A0', // sage green
            '#A0C8D8', // sky blue
            '#C0B0D8', // soft lavender
        ];

        const ribbons = [];
        const ribbonGroup = new THREE.Group();
        scene.add(ribbonGroup);

        // Silk material template
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
                opacity: 0.65,
                side: THREE.DoubleSide,
                envMapIntensity: 0.5,
            });
        }

        // Each ribbon is a TubeGeometry along an animated CatmullRom curve
        function createRibbon(hexColor, index) {
            const total = ribbonColors.length;
            const segments = 80;
            const tubularSegments = 200;
            const radius = 0.15 + Math.random() * 0.2;

            // Initial control points — gentle wave
            const baseY = -6 + index * 4;
            const points = [];
            const numCP = 12;
            for (let i = 0; i < numCP; i++) {
                const t = i / (numCP - 1);
                const x = Math.sin(t * Math.PI * 2.5 + index * 1.2) * (6 + index * 0.5);
                const y = baseY + t * 14;
                const z = Math.cos(t * Math.PI * 1.8 + index * 0.7) * (4 + Math.sin(index) * 2) - 3;
                points.push(new THREE.Vector3(x, y, z));
            }

            const curve = new THREE.CatmullRomCurve3(points, false, 'catmullrom', 0.5);
            const tubeGeom = new THREE.TubeGeometry(curve, tubularSegments, radius, segments, false);
            const material = createSilkMaterial(hexColor);
            const mesh = new THREE.Mesh(tubeGeom, material);
            mesh.castShadow = true;
            mesh.receiveShadow = true;

            // Store animation data
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
        // SPARKLE PARTICLES — catch the sunlight
        // ============================================================
        const sparkleCount = isMobile ? 200 : 500;
        const sPositions = new Float32Array(sparkleCount * 3);
        const sColors = new Float32Array(sparkleCount * 3);
        const sSizes = new Float32Array(sparkleCount);

        const sparklePalette = [
            [1, 0.95, 0.8],   // warm white
            [1, 0.85, 0.7],   // gold
            [0.95, 0.75, 0.8], // rose
            [0.8, 0.9, 1],    // soft blue
            [0.85, 1, 0.85],  // soft green
        ];

        for (let i = 0; i < sparkleCount; i++) {
            sPositions[i * 3] = (Math.random() - 0.5) * 35;
            sPositions[i * 3 + 1] = (Math.random() - 0.5) * 25;
            sPositions[i * 3 + 2] = (Math.random() - 0.5) * 18;
            sSizes[i] = 0.02 + Math.random() * 0.12;

            const c = sparklePalette[Math.floor(Math.random() * sparklePalette.length)];
            sColors[i * 3] = c[0];
            sColors[i * 3 + 1] = c[1];
            sColors[i * 3 + 2] = c[2];
        }

        const sparkleGeom = new THREE.BufferGeometry();
        sparkleGeom.setAttribute('position', new THREE.BufferAttribute(sPositions, 3));
        sparkleGeom.setAttribute('color', new THREE.BufferAttribute(sColors, 3));
        sparkleGeom.setAttribute('size', new THREE.BufferAttribute(sSizes, 1));

        // Sparkle texture — star-like glow
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
            size: 0.25,
            map: sparkleTex,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            depthTest: true,
            vertexColors: true,
            transparent: true,
            opacity: 0.7,
        });

        const sparkles = new THREE.Points(sparkleGeom, sparkleMat);
        scene.add(sparkles);

        // ============================================================
        // SOFT GROUND SHADOW — semi-transparent plane
        // ============================================================
        const shadowPlane = new THREE.Mesh(
            new THREE.PlaneGeometry(40, 30),
            new THREE.MeshBasicMaterial({
                color: 0x000000,
                transparent: true,
                opacity: 0.04,
                side: THREE.DoubleSide,
                depthWrite: false,
            })
        );
        shadowPlane.rotation.x = -Math.PI * 0.48;
        shadowPlane.position.set(0, -10, -5);
        shadowPlane.receiveShadow = true;
        scene.add(shadowPlane);

        // ============================================================
        // 3D MODEL — Golden Hour Hippo Wedding
        // ============================================================
        let hippoModel = null;
        let hippoMixer = null;
        const hippoGroup = new THREE.Group();
        scene.add(hippoGroup);

        const gltfLoader = new THREE.GLTFLoader();
        gltfLoader.load(
            '/img/hippo_wedding.glb',
            (gltf) => {
                hippoModel = gltf.scene;

                // Auto-scale: fit model to ~5 units tall
                const box = new THREE.Box3().setFromObject(hippoModel);
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const targetSize = 6;
                const scale = targetSize / maxDim;
                hippoModel.scale.setScalar(scale);

                // Center the model
                const center = box.getCenter(new THREE.Vector3());
                hippoModel.position.set(
                    -center.x * scale,
                    -center.y * scale + 2.5,  // float above center
                    -center.z * scale - 6       // behind content
                );

                // Enable shadows on all meshes
                hippoModel.traverse((child) => {
                    if (child.isMesh) {
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });

                // Handle animations
                if (gltf.animations && gltf.animations.length > 0) {
                    hippoMixer = new THREE.AnimationMixer(hippoModel);
                    gltf.animations.forEach((clip) => {
                        hippoMixer.clipAction(clip).play();
                    });
                }

                hippoGroup.add(hippoModel);

                // Fade in
                hippoModel.traverse((child) => {
                    if (child.isMesh && child.material) {
                        child.material.transparent = true;
                        child.material.opacity = 0;
                    }
                });

                console.log('🦛 Hippo model loaded!',
                    'animations:', gltf.animations ? gltf.animations.length : 0,
                    'size:', size.toArray().map(v => v.toFixed(2)));
            },
            (progress) => {
                if (progress.total > 0) {
                    const pct = Math.round((progress.loaded / progress.total) * 100);
                    console.log('🦛 Loading hippo...', pct + '%');
                }
            },
            (error) => {
                console.warn('⚠️ Hippo model failed to load:', error);
            }
        );

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
        // ANIMATION
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

        function animate() {
            requestAnimationFrame(animate);
            const dt = Math.min(clock.getDelta(), 0.1);
            const time = performance.now() * 0.001;

            detectSection();
            mouse.x += (mouse.tx - mouse.x) * 0.03;
            mouse.y += (mouse.ty - mouse.y) * 0.03;

            // Camera gentle sway
            camera.position.x += (mouse.x * 3 - camera.position.x) * 0.015;
            camera.position.y += (1 + mouse.y * 2 - camera.position.y) * 0.015;
            camera.lookAt(0, 1, -2);

            // --- Section-driven visual parameters ---
            let ribbonOpacityTarget = 0.65;
            let sparkleOpacityTarget = 0.7;
            let sunIntensityTarget = 2.5;
            let cameraFovTarget = 55;

            switch (currentSection) {
                case 'hero':
                    ribbonOpacityTarget = 0.7; sparkleOpacityTarget = 0.8;
                    sunIntensityTarget = 3.0; cameraFovTarget = 52;
                    break;
                case 'countdown':
                    ribbonOpacityTarget = 0.55; sparkleOpacityTarget = 0.9;
                    sunIntensityTarget = 2.0; cameraFovTarget = 58;
                    break;
                case 'venue':
                    ribbonOpacityTarget = 0.45; sparkleOpacityTarget = 0.5;
                    sunIntensityTarget = 1.8; cameraFovTarget = 60;
                    break;
                default:
                    ribbonOpacityTarget = 0.35; sparkleOpacityTarget = 0.4;
                    sunIntensityTarget = 1.5; cameraFovTarget = 62;
            }

            // Smooth light transition
            sunLight.intensity += (sunIntensityTarget - sunLight.intensity) * 0.02;
            camera.fov += (cameraFovTarget - camera.fov) * 0.02;
            camera.updateProjectionMatrix();

            // --- Animate silk ribbons ---
            ribbons.forEach((ribbon, idx) => {
                const ud = ribbon.userData;
                const bp = ud.basePoints;

                // Build new control points — each shifts on layered sine waves
                const newPoints = bp.map((p, i) => {
                    const t = i / (bp.length - 1);
                    const waveX = Math.sin(time * ud.speed * 1.3 + t * 3 + ud.phase) * ud.amplitude;
                    const waveY = Math.cos(time * ud.speed * 0.7 + t * 2.5 + ud.phase) * ud.amplitude * 0.6;
                    const waveZ = Math.sin(time * ud.speed * 0.9 + t * 2 + ud.phase + 1.5) * ud.amplitude * 0.8;
                    // Additional slow drift
                    const driftX = Math.sin(time * 0.2 + ud.phase) * 1.5;
                    const driftZ = Math.cos(time * 0.25 + ud.phase) * 1.2;

                    return new THREE.Vector3(
                        p.x + waveX + driftX,
                        p.y + waveY,
                        p.z + waveZ + driftZ
                    );
                });

                // Rebuild curve and geometry
                const curve = new THREE.CatmullRomCurve3(newPoints, false, 'catmullrom', 0.5);
                const tubularSegments = 200;
                const segments = 80;
                const radius = 0.15 + idx * 0.03;
                const newGeom = new THREE.TubeGeometry(curve, tubularSegments, radius, segments, false);

                ribbon.geometry.dispose();
                ribbon.geometry = newGeom;
                ribbon.userData.curve = curve;

                // Opacity transition
                ribbon.material.opacity += (ribbonOpacityTarget - ribbon.material.opacity) * 0.03;
            });

            // --- Sparkle animation ---
            sparkleMat.opacity += (sparkleOpacityTarget - sparkleMat.opacity) * 0.03;
            sparkles.rotation.y += dt * 0.03;
            sparkles.rotation.x += dt * 0.015;

            // Sparkles twinkle — each particle pulses independently via the position array
            const sparklePosArr = sparkles.geometry.attributes.position.array;
            for (let i = 0; i < Math.min(sparkleCount, sparklePosArr.length / 3); i++) {
                // Gentle upward drift
                sparklePosArr[i * 3 + 1] += dt * (0.05 + Math.sin(i) * 0.03);
                // Wrap
                if (sparklePosArr[i * 3 + 1] > 14) sparklePosArr[i * 3 + 1] = -14;
            }
            sparkles.geometry.attributes.position.needsUpdate = true;

            // --- Sunlight position slowly orbits ---
            const sunAngle = time * 0.08;
            sunLight.position.x = 12 + Math.sin(sunAngle) * 4;
            sunLight.position.z = 8 + Math.cos(sunAngle) * 4;
            rimLight.intensity = 1.0 + Math.sin(time * 0.5) * 0.5;

            // --- Ribbon group subtle rotation ---
            ribbonGroup.rotation.y += dt * 0.02;

            // --- Hippo model animation ---
            if (hippoModel) {
                // Gentle float + slow rotation
                hippoGroup.rotation.y += dt * 0.15;
                hippoGroup.position.y = Math.sin(time * 0.6) * 0.5;

                // Fade in model
                hippoModel.traverse((child) => {
                    if (child.isMesh && child.material && child.material.opacity < 1) {
                        child.material.opacity = Math.min(1, child.material.opacity + dt * 0.5);
                    }
                });

                // Update animation mixer
                if (hippoMixer) {
                    hippoMixer.update(dt);
                }
            }

            renderer.render(scene, camera);
        }

        // --- Resize ---
        window.addEventListener('resize', () => {
            const w = window.innerWidth, h = window.innerHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        animate();
        console.log('🌈 Rainbow silk ribbons scene live —', ribbonColors.length, 'ribbons,', sparkleCount, 'sparkles');
    }

    initWhenReady();
})();
