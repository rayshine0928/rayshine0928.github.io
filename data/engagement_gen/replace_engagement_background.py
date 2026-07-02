"""订婚宴背景替换：用人像 + 现场背景参考图，生成自然融合的成片（富士单反 / 胶片模拟质感）。

参考 generate_engagement_photos.py：多张图以 `image[]` 提交到同一 `/images/edits` 请求。

图片顺序（固定，勿改）：
- 第 1 张：templates/人像.jpg — 仅保留人物、服装、道具与姿态，作为「主体」来源。
- 第 2 张：templates/背景.jpg — 订婚宴场景，作为「环境 / 背景」与光线氛围参考。
"""

import argparse
import asyncio
import base64
import json
import os

import aiohttp
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api.env")
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("IMAGE_OPENAI_API_KEY")
BASE_URL = os.getenv("IMAGE_OPENAI_BASE_URL")
MODEL = os.getenv("IMAGE_OPENAI_MODEL", "gpt-image-2")
EDITS_ENDPOINT = f"{BASE_URL.rstrip('/')}/images/edits"

DEFAULT_PORTRAIT = os.path.join(current_dir, "templates", "人像.jpg")
DEFAULT_BACKGROUND = os.path.join(current_dir, "templates", "背景.jpg")


COMPOSITE_PROMPT = """
你将收到 2 张参考图，请严格按以下方式合成一张**竖构图订婚宴纪实照片**：

**第 1 张（人像图，主体来源）**
- 画面中的两位新人、他们的面部五官与身份特征、体型比例、服装（礼服 / 西装 / 领等）、手持物（如花束）、发型与妆造必须**原样保留**，禁止换脸、禁止「明星化 / 网红脸」、不要把五官比例改成模板脸。
- 人物在最终图中的**相对姿势、站位与亲密感**应与第 1 张一致；若第 1 张为半身 / 腰以上取景，请**自然扩画**为更接近订婚全景的取景（可补足合理的下身与脚部），使人物能稳稳站在第 2 张的地面 / 舞台上，**不要凭空多出与第 1 张矛盾的重大姿势改变**。
- 第 1 张中原有的**纯色棚拍背景必须完全移除**，不要保留任何浅色 / 灰色摄影棚底色。

**第 2 张（背景图，环境与氛围）**
- 将第 2 张中的订婚宴现场（红色主视觉、囍字元素、气球、桌面陈设、地面透视等）作为**最终成片的背景与环境**。
- 透视、地平线、地面纹理应与第 2 张协调；人物必须**脚踏实地**，站在可信的地面上，比例与景深合理。

**融合与真实感（必须做到）**
- 用**柔和过渡的边缘**把人像抠入场景，避免生硬的「剪贴画」白边或彩虹边；头发丝、花束边缘尽量自然。
- **重新匹配光线**：主光方向与明暗应与第 2 张现场一致，在人物面部与服装上形成统一的高光 / 阴影；在人物脚下绘制**轻微接触阴影**，让人物「落」在场地里。
- **色彩统一**：人物肤色与服装色调与现场红色、暖环境光协调，避免人物偏冷而背景偏暖的割裂感。

**整体质感：富士 X 系列单反 + 胶片模拟（如 Classic Chrome / Astia 方向）**
- 有机的色彩科学，**通透自然的肤色**，高光柔和滚落、不死白，中间调层次丰富，阴影略抬起但仍有密度。
- 细腻的**胶片颗粒**（极轻微、像高 ISO 富士出片），微观反差与织物纹理清晰，**禁止塑料 HDR、禁止过度锐化、禁止蜡像磨皮**。
- 背景可有**克制、自然的浅景深虚化**，人物的眼睛与面部保持锐利；整体像专业婚礼 / 订婚跟拍的单张成片。

**禁止事项**
- 画面中不要新增莫名其妙的文字、水印、Logo；若现场装饰上已有礼仪性汉字（如囍），可与第 2 张保持一致，不要乱改语义。
- 不要插画、3D 渲染、AI 通用美图风；必须是**写实摄影**。

输出一张竖构图、喜庆克制、**自然订婚宴现场**中的双人合影，质感高级、耐看。
""".strip()


def _content_type_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


async def replace_background(
    portrait_path: str,
    background_path: str,
    *,
    prompt: str,
    size: str = "2048x3072",
) -> tuple[str, object]:
    """调用 /images/edits，image[] 顺序：人像 → 背景。返回 ("bytes", bytes) | ("url", str) | ("error", str)。"""
    if not API_KEY or not BASE_URL:
        return "error", "请在 api.env 中配置 IMAGE_OPENAI_API_KEY 与 IMAGE_OPENAI_BASE_URL"

    paths = [portrait_path, background_path]
    for p in paths:
        if not os.path.isfile(p):
            return "error", f"文件不存在: {p}"

    try:
        form = aiohttp.FormData()
        form.add_field("model", MODEL)
        form.add_field("prompt", prompt)
        form.add_field("size", size)
        form.add_field("n", "1")

        for p in paths:
            with open(p, "rb") as f:
                data = f.read()
            form.add_field(
                "image[]",
                data,
                filename=os.path.basename(p),
                content_type=_content_type_for(p),
            )

        headers = {"Authorization": f"Bearer {API_KEY}"}
        timeout = aiohttp.ClientTimeout(total=600)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(EDITS_ENDPOINT, headers=headers, data=form) as resp:
                text = await resp.text()
                if resp.status != 200:
                    return "error", f"HTTP {resp.status}: {text[:800]}"
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    return "error", f"非 JSON 响应: {text[:800]}"

        data_list = payload.get("data") or []
        if data_list and data_list[0].get("b64_json"):
            return "bytes", base64.b64decode(data_list[0]["b64_json"])
        if data_list and data_list[0].get("url"):
            return "url", data_list[0]["url"]

        return "error", str(payload)[:800]

    except Exception as e:
        return "error", str(e)


async def download_image(url: str, filename: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                response.raise_for_status()
                content = await response.read()
        with open(filename, "wb") as f:
            f.write(content)
        return True
    except Exception:
        return False


async def run(args: argparse.Namespace) -> int:
    portrait = args.portrait
    background = args.background
    out_path = args.output

    if not out_path:
        output_dir = os.path.join(current_dir, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "engagement_composite_fuji.png")

    if args.prompt_file is None:
        prompt = COMPOSITE_PROMPT
    else:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()
    if args.extra_prompt:
        prompt = prompt + "\n\n" + args.extra_prompt.strip()

    print(f"模型: {MODEL}")
    print(f"人像（第 1 张）: {portrait}")
    print(f"背景（第 2 张）: {background}")
    print(f"输出: {out_path}")

    kind, payload = await replace_background(
        portrait,
        background,
        prompt=prompt,
        size=args.size,
    )

    if kind == "bytes":
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(payload)
        print(f"✅ 已保存: {out_path}")
        return 0

    if kind == "url":
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        if await download_image(payload, out_path):
            print(f"✅ 已从 URL 保存: {out_path}")
            return 0
        print(f"❌ 下载失败: {payload}")
        return 1

    print(f"❌ 生成失败: {payload}")
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="用人像 + 订婚宴背景参考图合成自然成片（富士胶片模拟质感），API 与 generate_engagement_photos 一致。",
    )
    parser.add_argument(
        "--portrait",
        default=DEFAULT_PORTRAIT,
        help=f"人像图路径（默认: {DEFAULT_PORTRAIT}）",
    )
    parser.add_argument(
        "--background",
        default=DEFAULT_BACKGROUND,
        help=f"背景场景图路径（默认: {DEFAULT_BACKGROUND}）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="输出路径（默认: outputs/engagement_composite_fuji.png）",
    )
    parser.add_argument(
        "--size",
        default="2048x3072",
        help="输出尺寸（默认 2048x3072，约为原 1024x1536 的两倍，竖图超清）",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="从文件读取完整 prompt（覆盖内置 COMPOSITE_PROMPT）",
    )
    parser.add_argument(
        "--extra-prompt",
        default="",
        help="附加在内置 prompt 后的补充说明",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
