# 0928.love 婚礼网站 — 设计文档（v22 · 2026-09-08）

## 一、当前视觉方向

### 核心概念：真实婚纱照作底，玻璃卡片叙事
- **固定背景**：`img/couple_portrait.webp`（卡其色端庄婚纱照）由 `.site-bg` fixed 层铺满全页、**不随内容滚动**；上层叠一条奶油色轻纱渐变（`linear-gradient` 同层 background-image），压高光、托卡片。
- **iOS 玻璃 + 香槟金发丝边**：所有卡片/导航/页脚统一配方 —— 半透明白 + `backdrop-filter: blur(28px) saturate(180%) brightness(1.08)` + 135° 金白渐变发丝边（双层 background：padding 层玻璃底色、border 层 `--glass-edge`）+ 上下内高光 + 深投影。集中定义在 `css/wedding.css` 的 `--glass-*` 变量，改配方只改变量；发丝边统一加在 `.invitation-card / .moment-frame / .rsvp-card / .venue-info-card / .sched-content / .btn-map`。
- **文字作框**：hero 文字退到上下两端（eyebrow / 日期），中央完全留给背景照片；上下各一条奶油色渐隐纱保证可读。
- **卡通保留 2D**：噜噜噜妹卡通插画仅用于请柬侧图 / 场地指路；**3D 模型已于 v19 退役**（36MB glb + three.js CDN 加载过慢）。

### 页面结构（纵向 7 节）
1. HERO — 固定背景 + 上下文字框 + 下滑提示
2. INVITATION — 玻璃请柬卡（含倒计时天数胶囊）+ 卡通请柬图
3. MOMENT — 园林婚纱照三张，玻璃相框（v19 新增竖框；v22 加漏窗并肩、窗前轻吻两横幅宽框，`#moment`）
4. VENUE — 酒店名直排于背景（不衬卡片、无 logo，v20）+ 卡通指路 + 实景照 + 信息卡 + 地图按钮
5. SCHEDULE — 竖时间线 + 玻璃流程卡（仪式 / 晚宴）
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
- 导航：滚动 60px 后变玻璃态；移动端抽屉同样玻璃。
- `prefers-reduced-motion` 下停用装饰动画。

## 四、版本沿革
- v16 玻璃简化（单倒计时、QR 回执）→ v17 hero 画框化 → v18 3D 加载指示器 + 移动端居中修复
- v19：退役 3D（删 `wedding-three.js`、两个 glb、hippo_wedding.glb，共 ~92MB）；真实婚纱照固定背景 + 全站 iOS 玻璃；新增 MOMENT 园林照 section；两张婚纱照压缩为 webp/jpg 双格式。
- v20：移除「我们的故事」四格卡通；场地酒店名去卡片化直排；玻璃升级为香槟金发丝边 + 深 blur + 金线题饰（section-title 下金线、subtitle 金色斜体），向百万级婚礼质感靠拢。
- v21：Liquid Glass 三层配方 —— 低透明 158° 渐变玻璃体 + 斜向高光带 + conic 香槟金环边流光（含双角高光）；blur 调为 28px/saturate 180%/brightness 1.08；阴影改贴地 + 弥散双影 + 四侧内壁受光；无 backdrop-filter 时 `@supports` 降级不透明白底。
- **v22（当前）**：MOMENT 新增两横幅玻璃宽框（园林漏窗前并肩 4:3、窗前轻吻 16:9）；`.moment-wide` 宽框 max-width 760px、比例随原图不裁切；20MB/16MB 原片压为 webp 106KB/36KB。
- 更早的「七章视差画卷」方案与 AI 图片清单已过期，见 git 历史中的旧版 DESIGN_DOC。
