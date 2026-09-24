# 0928.love 婚礼网站 — 设计文档（v26 · 2026-09-24）

## 一、当前视觉方向

### 核心概念：「晴光极光」—— 明亮水彩极光 + 婚纱照固定底 + iOS 玻璃 + LogosCaller 式指针光交互
v26 参考 LogosCaller（logoscaller-oss.github.io）的前端特效体系整体重做，主题由"暗室光剧场"转译为**明亮**的"晴天花园光"：

- **明亮水彩极光场（`.aurora-field`）**：LogosCaller 极光团的亮色转译。五团大柔光斑（左上暖白热核——延续"光从左上来"的光源叙事——加玫瑰/香槟金/蜜桃/鼠尾草绿水彩色团）fixed 在照片与内容之间，18–26s 极慢漂移（只动 transform，走合成器）。**不用 screen 混合**（亮底上加色恒等于白，v25 的核心教训），普通混合的低透明水彩色即可显影；**不加容器 blur**（径向渐变本身够柔，省一层全屏滤镜开销）。整场由 JS 做指针视差；位于玻璃卡 backdrop-filter 采样范围内 → 极光被玻璃自动折射发虚，"光透过玻璃"零额外代码。
- **v24 滚动扫光（--lit）与 v25 体积阳光（.sun-field god rays/浮尘）已整体退役**，由极光场 + 金色光尘粒子 + 光标追光系统接管动态光影。`.site-bg` 同步提亮：撤掉曝光压暗纱（.07 暖棕），暗角减淡到轻描（.15），只留奶油轻纱保文字可读。
- **iOS 玻璃 + 香槟金发丝边（保留 v24 配方）**：150° 渐变玻璃体 + `backdrop-filter: blur(32px) saturate(188%) brightness(1.07) contrast(1.02)` + conic 香槟金环边 + 方向外影（偏右下）+ 焦散斑。集中定义在 `--glass-*` 变量。
- **文字作框**：hero 文字退到上下两端，中央留给固定背景婚纱照；日期改**流光渐变文字**（玫瑰→香槟金→暖棕，9s 循环；透明填充下 text-shadow 会从字形透出，改用 `drop-shadow` 托底）。
- **卡通保留 2D**：噜噜噜妹卡通仅用于请柬侧图 / 场地指路，滚动视差保留。

### 特效分层（z 序）
```
z0  .site-bg        fixed 婚纱照 + 奶油轻纱 + 轻暗角
z0  .aurora-field   fixed 五团水彩极光（JS 指针视差写在容器上）
z0  canvas.fx-particles  fixed 金色光尘场（JS 注入，极光之上、内容之下，被玻璃折射）
z0  .cursor-spotlight    fixed 暖阳 spotlight（JS 注入，光尘之上、内容之下）
z1  sections / footer    内容层（玻璃卡 backdrop-filter 采样以下全部光层）
z5(旧 sun-field 已删)
z1000 nav           z9999 光标胶囊
```

### 页面结构（纵向 7 节，内容与 v25 完全一致，仅增一条页脚题词）
1. HERO — 固定背景 + 上下文字框（`.hero-parallax` 视差包装层，不碰内层 reveal）+ 流光日期 + 下滑提示
2. INVITATION — 玻璃请柬卡（含倒计时天数胶囊、tilt、光标胶囊"我们的请柬"）+ 卡通请柬图（滚动视差）
3. MOMENT — 园林婚纱照三张玻璃相框（tilt + 驻停 morph 圆形照片预览；**滚动视差已让位给 tilt**，避免同元素 transform 打架）
4. VENUE — 酒店名直排 + 卡通指路（光标胶囊）+ 实景照×2（胶囊 + 预览）+ 信息卡×4（tilt）+ 地图按钮（磁性 + 胶囊）
5. SCHEDULE — 竖时间线 + 玻璃流程卡四步（迎宾 / 仪式 / 合影 / 晚宴，不参与 tilt）
6. RSVP — 玻璃卡（tilt）+ 出席登记二维码（胶囊"扫码登记出席"）
7. FOOTER — 全宽玻璃页脚 + **手电筒题词**「愿有岁月可回首 · 且以深情共白头」（新增，遮罩只在光标光斑处显影）

## 二、资产与性能

| 资产 | 源 | 线上 | 说明 |
|------|----|------|------|
| `couple_portrait.webp/.jpg` | 6192×8256 · 24MB | 1500×2000 · webp 88KB / jpg 384KB | 固定背景；`<link rel=preload fetchpriority=high>`；CSS `image-set()` 优先 webp |
| `garden_moment.webp/.jpg` | 6192×8256 · 30MB | 1200×1600 · webp 92KB / jpg 365KB | MOMENT 竖相框 + 胶囊预览盘；`loading=lazy` + 宽高属性防 CLS |
| `garden_stand.webp/.jpg` | 8256×6192 · 20MB | 1600×1200 · webp 106KB / jpg 340KB | MOMENT 横幅宽框（漏窗前并肩，4:3）+ 胶囊预览盘 |
| `window_kiss.webp/.jpg` | 8256×4640 · 16MB | 1600×899 · webp 36KB / jpg 158KB | MOMENT 横幅宽框（窗前轻吻，16:9）+ 胶囊预览盘 |
| 卡通 PNG ×7 | — | 各 ~240KB–1.3MB | 2D 插画，生成管线见 `data/engagement_gen/` |

- **压缩流程**：`sips -Z <长边>` 缩放 → `cwebp -m 6 -q 72~74` 出 webp → `sips -s format jpeg -s formatOptions 70~72` 出 jpg 兜底。
- **JS 三件套（无框架、无 three.js）**：
  - `js/fx-core.js` — 共享内核（移植自 LogosCaller）：全站唯一 rAF ticker（无人饥饿自动停摆）、指针位置 + 平滑速度（瞬移不计速）、能力标记 `env.enablePointerFx = finePointer && !reduceMotion`；暴露 `window.LoveFx`。
  - `js/wedding-fx.js` — 交互层：光标胶囊 / spotlight / 极光与 hero 指针视差 / 卡片 tilt + 追光 / 磁性按钮 / 导航滑囊 / 手电筒题词 / View Transitions 锚点 / 金色光尘粒子场。
  - `js/wedding.js` — 基础层：倒计时 / 卡通滚动视差 / reveal（同节错峰 .08s，`--reveal-delay`）/ 移动端抽屉 / 导航滚动态。v24 光场代码已删。
- 字体与 Font Awesome 走 CDN。请柬卡片生成约定见 `data/engagement_gen/` 与记忆库。
- **刻意不移植**：LogosCaller 的 WebGL 流体极光（会盖住婚纱照且移动端 GPU 预算紧，DOM 极光团已同语义）、烛照暗纱 light-memory（叙事是"暗室点烛"，与明亮主题相反）、音效系统（婚宴页面自动出声扰人）。

## 三、交互（LogosCaller 语汇 → 婚礼明亮转译）
- **情境光标胶囊**（antigravity.google 风格）：`[data-cursor-pill]` 区域内隐藏系统光标，白瓷胶囊（玫瑰图标 + 暖影）缓动跟随；沿速度矢量挤压拉伸、快速移动拖两道暖金残影彗尾、驻停 450ms morph 成**圆形照片预览盘**（拍立得圆窗，moment 相框 / 酒店实景）、按压下潜、区域直接跳转换词、滚动出界收起。全站 9 个区域：请柬卡、三张 moment 相框、卡通指路、酒店实景×2、地图按钮、RSVP 二维码。
- **暖阳 spotlight**：560px 暖金径向光斑跟随光标（明亮版禁用 screen，低透明暖色 source-over），点击时 saturate 增强；绘制在内容之下 → 被玻璃卡折射。
- **金色光尘粒子场**：canvas 版"阳光下的金粉"，LogosCaller 星尘的亮色转译 —— 四芒闪点 + 衍射短刺 + 横向柔光条纹，暖金/玫瑰/香槟四色 source-over 上色（**亮底禁用 lighter**）；光标是"戒指"：环内金尘被推开 + 切向涡旋 + 接过光标动量，弹簧欠阻尼回位；被掠过的金尘**染上玫瑰色**（lit 通道，2.2s 指数消退）；快速甩动抛出至多两枚金色流星；深度视差（近尘躲得更远）；数量 `clamp(W*H/16000, 36, 110)`，DPR 封顶 1.5，`document.hidden` 停摆。
- **玻璃卡 3D tilt + 追光**：`.tilt-card`（请柬 / 相框 / 信息卡 / RSVP 卡，`data-tilt-max` 4–8°）—— `::after` 420px 暖白 glare 追着光标在玻璃面游走，`::before` 1px 环内玫瑰金边缘流光（mask-composite 挖心），tilt 时抬起 8px、影更大更偏右下、焦散更暖（同一光源语言）。**sched-content 不参与**（时间线行内倾斜破坏对齐）。
- **磁性按钮**：`.btn-map` 被光标吸过去（.35 强度 / 12px 封顶），松手 .35s 弹回。
- **导航滑行胶囊**：`.nav-glide` 玫瑰金光晕胶囊在链接间滑动（垂直按实测高度对中），**取代旧下划线**；移动端抽屉内隐藏。
- **流光渐变文字**：hero 日期玫瑰→金→暖棕 250% 背景位移动画。
- **手电筒题词**：页脚誓词平时藏在遮罩外（`--ly: -160px`），光标进入 footer 后 210px 径向光斑内显影；面具只挂 `body.fx-live`（指针特效上岗才戴），**无 JS / 触屏 / 减弱动效整行常显，内容永不丢失**。
- **View Transitions 圆形揭示**：锚点跳转从点击处 `clip-path: circle()` 展开（0.55s），带 -70px 导航偏移 + pushState；无支持退回平滑滚动（reduced-motion 时 behavior auto）。
- **滚动 reveal + 错峰**：IntersectionObserver 加 `.visible`；同节内第 n 个延迟 n×.08s。**reveal 隐藏态由 `html.js` 门控**（head 内联一行加 class）——无 JS 内容完整可见，不玩捉迷藏。
- **指针视差**：极光场容器 ±26px、hero 上下文字组 ∓12/18.4px（`.hero-parallax` 包装层承载，与内层 reveal transform 解耦），时间常数按 60Hz 手感标定（120Hz+ 一致）。

### 降级矩阵
| 环境 | 得到什么 |
|------|----------|
| 桌面 + JS | 全部特效 |
| 触屏（iOS 宾客主力） | 极光漂移 + 玻璃 + reveal 错峰 + 平滑滚动锚点（指针特效整体不启用，`enablePointerFx=false`） |
| prefers-reduced-motion | 静止但完整：极光/流光/粒子/胶囊 CSS 全关，JS 不启用指针特效，题词常显 |
| 无 JS | 内容完整可见（html.js 门控），极光纯 CSS 照常漂移，题词常显 |
| 无 backdrop-filter | `@supports` 更实暖白底；glare/边缘流光是纯渐变照常工作 |

## 四、版本沿革
- v16 玻璃简化 → v17 hero 画框化 → v18 3D 加载指示器 → v19 退役 3D（-92MB）、真实婚纱照固定背景 + iOS 玻璃、MOMENT 园林照
- v20：移除四格卡通连环画；场地酒店名去卡片化；香槟金发丝边 + 深 blur + 金线题饰
- v21：Liquid Glass 三层配方（渐变玻璃体 + 斜向高光带 + conic 环边流光）
- v22：MOMENT 两横幅宽框（4:3 / 16:9），原片压 webp
- v23：婚礼流程重排为四步 run-of-show，倒计时目标 15:00 迎宾
- v24：滚动光影 + 通透折射玻璃（--lit 扫光带 / --scroll-p 光场漂移 / 左上光源语言 / reduced-motion 补齐）
- v25：体积阳光层（.sun-field god rays + 镜头光晕 + 逆光浮尘；亮底上 screen 不可见 → 前景光柱改暖金 source-over 的关键教训）
- **v26（当前）：「晴光极光」整体改版** —— 参考 LogosCaller 前端特效体系、按明亮主题转译：极光水彩场取代 v24 扫光与 v25 体积阳光；新增 fx-core/wedding-fx 双脚本（共享 ticker + 指针内核）；光标胶囊（含驻停圆形照片预览）、暖阳 spotlight、金色光尘粒子场（环形位移 + 金尘"脸红"）、玻璃卡 tilt + 追光 + 边缘流光、磁性地图按钮、导航滑行胶囊、流光日期、页脚手电筒题词、View Transitions 圆形揭示、reveal 错峰 + html.js 无 JS 门控；照片/请柬/流程/回执等全部内容保持不变，仅新增题词一行。
- 更早的「七章视差画卷」方案与 AI 图片清单已过期，见 git 历史中的旧版 DESIGN_DOC。
