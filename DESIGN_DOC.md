# 0928.love 婚礼网站 — 设计文档（v25 · 2026-09-11）

## 一、当前视觉方向

### 核心概念：真实婚纱照作底，玻璃卡片叙事，全站单一光源
- **光源系统（v24 定向 + v25 体积阳光）**：全站光源统一设定在**页面左上角，向右下照射**。v25 按动画/阳光摄影语言重做为**前后两层体积光**：
  - **背景层**（`.site-bg`）：左上过曝热核 + 大暖晕（screen 加色于照片）；`::after` 宽软 conic 扇形光柱（blur 14px、screen），经卡片 backdrop-filter 折射发虚 = 深层光；底叠**曝光压暗纱**（全页暖棕 .07）+ **暗角**（四角 .30）——高调奶白底不压暗则光柱无法显影（摄影曝光逻辑）。
  - **前景层**（`.sun-field`，fixed z-index 5 压内容之上）：从光源点扇形射出的**窄楔形 god rays**（亮核 .50 + 暖金边、blur 5px、13s 极慢摇摆且 transform-origin 钉在光源）+ 沿光路三枚镜头光晕 + 逆光**浮尘微粒**（12 枚 radial 点，漂移 + 明灭双动画）。**关键教训：页面是高调亮底，screen/加色混合在亮底上恒等于白（不可见），前景光柱必须用"有颜色的暖金" source-over 上色**；screen 只留给背景层对照片加光。
  - **卡片层**（v24）：`::after` specular 扫光带随滚动左上扫右下、`::before` 右下折射暖斑；所有投影/焦散偏右下。
  - 三层叠加 = 层次感：背景光虚、前景光锐、卡片扫光随视口动；背景光在卡片 backdrop-filter 采样范围内被自动折射——"光透过玻璃"零额外代码。
- **固定背景**：`img/couple_portrait.webp`（卡其色端庄婚纱照）由 `.site-bg` fixed 层铺满全页、**不随内容滚动**；上层叠一条奶油色轻纱渐变（`linear-gradient` 同层 background-image），压高光、托卡片。
- **iOS 玻璃 + 香槟金发丝边（v24 通透折射配方）**：所有卡片/导航/页脚统一配方 —— 150° 渐变玻璃体（左上受光 .44 → 中段最透 .05 让背景充分透出 → 右下暖金回升 .20）+ `backdrop-filter: blur(32px) saturate(188%) brightness(1.07) contrast(1.02)` + 环边流光（左上纯白锐亮受光边、右下暖金折射角、conic 香槟金绕边）+ 方向外影（贴地小影 + 弥散大影偏右下 + 右下暖色焦散斑 `rgba(212,165,116,.38)`）+ inset 左上 1.5px 锐亮边与右下内壁暖金折射。集中定义在 `css/wedding.css` 的 `--glass-*` 变量，改配方只改变量；发丝边统一加在 `.invitation-card / .moment-frame / .rsvp-card / .venue-info-card / .sched-content / .btn-map`。
- **文字作框**：hero 文字退到上下两端（eyebrow / 日期），中央完全留给背景照片；上下各一条奶油色渐隐纱保证可读。
- **卡通保留 2D**：噜噜噜妹卡通插画仅用于请柬侧图 / 场地指路；**3D 模型已于 v19 退役**（36MB glb + three.js CDN 加载过慢）。

### 页面结构（纵向 7 节）
1. HERO — 固定背景 + 上下文字框 + 下滑提示
2. INVITATION — 玻璃请柬卡（含倒计时天数胶囊）+ 卡通请柬图
3. MOMENT — 园林婚纱照三张，玻璃相框（v19 新增竖框；v22 加漏窗并肩、窗前轻吻两横幅宽框，`#moment`）
4. VENUE — 酒店名直排于背景（不衬卡片、无 logo，v20）+ 卡通指路 + 实景照 + 信息卡 + 地图按钮
5. SCHEDULE — 竖时间线 + 玻璃流程卡（迎宾 / 仪式 / 合影 / 晚宴四步，v23）
6. RSVP — 玻璃卡 + 出席登记二维码
7. FOOTER — 全宽玻璃页脚

（「我们的故事」四格卡通连环画于 v20 移除；卡通仅保留请柬侧图与场地指路两处。）

## 二、资产与性能

| 资产 | 源 | 线上 | 说明 |
|------|----|------|------|
| `couple_portrait.webp/.jpg` | 6192×8256 · 24MB | 1500×2000 · webp 88KB / jpg 384KB | 固定背景；`<link rel=preload fetchpriority=high>`；CSS `image-set()` 优先 webp |
| `garden_moment.webp/.jpg` | 6192×8256 · 30MB | 1200×1600 · webp 92KB / jpg 365KB | MOMENT 竖相框；`loading=lazy` + 宽高属性防 CLS |
| `garden_stand.webp/.jpg` | 8256×6192 · 20MB | 1600×1200 · webp 106KB / jpg 340KB | MOMENT 横幅宽框（漏窗前并肩，4:3）；`loading=lazy` + 宽高属性防 CLS |
| `window_kiss.webp/.jpg` | 8256×4640 · 16MB | 1600×899 · webp 36KB / jpg 158KB | MOMENT 横幅宽框（窗前轻吻，16:9）；`loading=lazy` + 宽高属性防 CLS |
| 卡通 PNG ×7 | — | 各 ~240KB–1.3MB | 2D 插画，生成管线见 `data/engagement_gen/` |

- **压缩流程**：`sips -Z <长边>` 缩放 → `cwebp -m 6 -q 72~74` 出 webp → `sips -s format jpeg -s formatOptions 70~72` 出 jpg 兜底。
- **JS**：仅 `js/wedding.js`（倒计时 / 视差 / reveal / 导航）；无 three.js、无框架。字体与 Font Awesome 走 CDN。
- 请柬卡片生成（国学风成片、二维码像素级贴码）约定见 `data/engagement_gen/` 脚本与记忆库。

## 三、交互
- 滚动 reveal：IntersectionObserver 加 `.visible`。
- 视差：`[data-parallax]` 元素按速率 translate3d（RAF 节流）。
- **滚动光影（v24）**：`updateLightField()` 挂在同一 RAF scroll 循环，写两个 CSS 变量——
  - `--scroll-p`（0~1 页面进度，量化 .005）同写 **`.site-bg` 与 `.sun-field` 两个光层元素（而非 `:root`）**，样式失效范围各自收缩到本元素伪元素，驱动光晕/光柱 `translate` 漂移；
  - `--lit`（0~1 卡片穿越视口进度，量化 .025）写在每张玻璃卡上，仅更新视口内卡片；驱动 `::after` 扫光带 `translate3d` + 抛物线 opacity 包络 `lit*(1-lit)*3.4`（两端淡出不穿帮）与 `::before` 折射暖斑 opacity。
  - 性能约定：伪元素只动 **transform/opacity**（合成器属性），CSS 端 `.3s linear` transition 抹平量化台阶；不主动加 `will-change`（13 卡×2 伪元素会撑 iOS 层内存）；帧内读写分离（先集中读 rect 再集中写变量）。
  - 未用 CSS scroll-driven animations（`animation-timeline: view()` 需 Safari 26+，宾客以 iOS 17/18 为主）；消费端 CSS 已按变量协议写好，未来可删 JS 平替。
  - `.btn-map` 不参与扫光（胶囊太小且 hover 有玫瑰金底整体替换）；卡片 `overflow: hidden` 已逐项审计（moment 照片在内层自带裁剪、时间轴金线/圆点是兄弟节点、hover 外影不被自身裁剪）。
- 导航：滚动 60px 后变玻璃态；移动端抽屉同样玻璃。
- `prefers-reduced-motion`：JS 停更变量并清除内联值（中途切换有 change 监听），CSS 关呼吸/扫光过渡——回落到 `--lit: .42` / `--scroll-p: 0` 兜底值，呈**静态但完整的光照**；无 JS 同理。无 backdrop-filter 浏览器走 `@supports` 更实暖白底，扫光/折射是纯渐变照常工作。

## 四、版本沿革
- v16 玻璃简化（单倒计时、QR 回执）→ v17 hero 画框化 → v18 3D 加载指示器 + 移动端居中修复
- v19：退役 3D（删 `wedding-three.js`、两个 glb、hippo_wedding.glb，共 ~92MB）；真实婚纱照固定背景 + 全站 iOS 玻璃；新增 MOMENT 园林照 section；两张婚纱照压缩为 webp/jpg 双格式。
- v20：移除「我们的故事」四格卡通；场地酒店名去卡片化直排；玻璃升级为香槟金发丝边 + 深 blur + 金线题饰（section-title 下金线、subtitle 金色斜体），向百万级婚礼质感靠拢。
- v21：Liquid Glass 三层配方 —— 低透明 158° 渐变玻璃体 + 斜向高光带 + conic 香槟金环边流光（含双角高光）；blur 调为 28px/saturate 180%/brightness 1.08；阴影改贴地 + 弥散双影 + 四侧内壁受光；无 backdrop-filter 时 `@supports` 降级不透明白底。
- v22：MOMENT 新增两横幅玻璃宽框（园林漏窗前并肩 4:3、窗前轻吻 16:9）；`.moment-wide` 宽框 max-width 760px、比例随原图不裁切；20MB/16MB 原片压为 webp 106KB/36KB。
- v23：婚礼流程时间线重排为四步 run-of-show（迎宾 / 仪式 / 合影 / 晚宴），倒计时目标同步为 15:00 迎宾开始。
- v24：滚动动态光影 + 通透折射玻璃 —— 全站光源定于左上角向右下照射；卡片 specular 扫光带与右下折射暖斑随 `--lit` 动；玻璃配方改通透折射（中段 .05 更透、左上 1.5px 锐亮边、右下暖金 inset、外影偏右下含暖焦散斑、blur 32px + contrast 1.02）；hover/nav/footer/抽屉/@supports 五处同步同一光源语言；补齐 `prefers-reduced-motion` 实现。
- **v25（当前）**：体积阳光层 —— 用户反馈 v24 光"不明显、无质感层次"，按动画/阳光摄影重做：新增前景 `.sun-field` 固定层（窄楔形 god rays 扇形光柱 + 镜头光晕 + 逆光浮尘，普通混合暖金上色）；背景层改过曝热核 + 宽软 screen 光柱；`.site-bg` 加曝光压暗纱与暗角让光显影；卡片扫光带提亮（峰 .32）；`--scroll-p` 同写两光层；reduced-motion 覆盖新层。
- 更早的「七章视差画卷」方案与 AI 图片清单已过期，见 git 历史中的旧版 DESIGN_DOC。
