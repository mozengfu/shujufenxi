"""生成 macOS 应用图标 .icns"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFilter

ICONSET = '/tmp/数据分析系统.iconset'
OUTPUT = os.path.join(os.path.dirname(__file__), 'icon.icns')

SIZES = [
    ('icon_16x16.png', 16),
    ('icon_16x16@2x.png', 32),
    ('icon_32x32.png', 32),
    ('icon_32x32@2x.png', 64),
    ('icon_128x128.png', 128),
    ('icon_128x128@2x.png', 256),
    ('icon_256x256.png', 256),
    ('icon_256x256@2x.png', 512),
    ('icon_512x512.png', 512),
    ('icon_512x512@2x.png', 1024),
]

BG_TOP = (44, 62, 80)       # #2c3e50
BG_BOTTOM = (41, 128, 185)  # #2980b9
GREEN = (39, 174, 96)       # #27ae60
PURPLE = (142, 68, 173)     # #8e44ad
WHITE = (255, 255, 255)
LGRAY = (200, 200, 200)
DGRAY = (100, 100, 100)     # 阴影色


def make_icon(size: int) -> Image.Image:
    """在 RGB 画布上画图标，最后统一做圆角蒙版裁切 + 阴影"""
    S = size
    # 画在 RGB 上，避免 alpha 干扰
    img = Image.new('RGB', (S, S), BG_TOP)
    draw = ImageDraw.Draw(img)

    # ── 渐变背景（简化：对角渐变用分条近似） ──
    for y in range(S):
        t = y / S
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (S, y)], fill=(r, g, b))

    # ── 柱状图（3 根，比例居中） ──
    cx, cy = S // 2, S // 2
    bw = S * 0.08           # 柱宽
    gap = S * 0.07          # 柱间距
    base_y = int(S * 0.78)  # 柱底 Y

    bars = [
        (cx - gap - bw,     base_y - S * 0.25,  cx - gap,           base_y),
        (cx - bw / 2,       base_y - S * 0.45,  cx + bw / 2,        base_y),
        (cx + gap,          base_y - S * 0.35,  cx + gap + bw,      base_y),
    ]

    for i, (x1, y1, x2, y2) in enumerate(bars):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        radius = max(int(bw * 0.25), 2)
        color = GREEN if i == 1 else WHITE
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=color)

    # ── 折线 + 圆点 ──
    pts = [
        (int(cx - gap - bw / 2), int(base_y - S * 0.22)),
        (int(cx),                int(base_y - S * 0.48)),
        (int(cx + gap + bw / 2), int(base_y - S * 0.38)),
    ]
    draw.line(pts, fill=PURPLE, width=max(int(S * 0.01), 2), joint='curve')
    for px, py in pts:
        r2 = max(int(S * 0.018), 2)
        draw.ellipse((px - r2, py - r2, px + r2, py + r2), fill=PURPLE)

    # ── 表格网格（右下方） ──
    table_l = int(S * 0.58)
    table_r = int(S * 0.92)
    table_t = int(S * 0.48)
    table_b = int(S * 0.78)
    tw, th = table_r - table_l, table_b - table_t

    # 半透明表头背景
    header_h = th // 4
    draw.rectangle((table_l, table_t, table_r, table_t + header_h), fill=(255, 255, 255, 30))

    # 网格虚线（用短线段模拟）
    for c in range(4):
        x = table_l + int(tw * c / 3)
        draw.line([(x, table_t), (x, table_b)], fill=LGRAY, width=1)
    for r in range(5):
        y = table_t + int(th * r / 4)
        draw.line([(table_l, y), (table_r, y)], fill=LGRAY, width=1)

    # 数据点（小圆点）
    dots = [(1, 0), (1, 1), (0, 2), (2, 0), (2, 2), (0, 1)]
    dot_r = max(int(S * 0.012), 1)
    for dr, dc in dots:
        dx = int(table_l + (dc + 0.5) * tw / 3)
        dy = int(table_t + header_h + (dr + 0.5) * th / 4 * 3 + th / 4)
        draw.ellipse((dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r), fill=GREEN)

    # ── 生成圆角蒙版 + 阴影 ──
    # 阴影
    shadow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = max(int(S * 0.02), 2)
    sd.rounded_rectangle(
        (pad, pad, S - pad, S - pad),
        radius=int(S * 0.16), fill=(0, 0, 0, 100)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(int(S * 0.025), 2)))

    # 圆角蒙版裁切主图
    mask = Image.new('L', (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, S, S), radius=int(S * 0.16), fill=255)
    masked = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    masked.paste(img, (0, 0), mask)

    # 合成：阴影在下，主图在上
    result = Image.alpha_composite(shadow, masked)
    return result.convert('RGBA')


def main():
    if os.path.exists(ICONSET):
        subprocess.run(['rm', '-rf', ICONSET], check=True)
    os.makedirs(ICONSET, exist_ok=True)

    # 先生成 1024 基础图，再缩放
    master = make_icon(1024)

    for name, sz in SIZES:
        if sz == 1024:
            resized = master
        else:
            resized = master.resize((sz, sz), Image.LANCZOS)
        resized.save(os.path.join(ICONSET, name), 'PNG')
        print(f'  {name}  {sz}x{sz}')

    subprocess.run([
        'iconutil', '--convert', 'icns', '--output', OUTPUT, ICONSET
    ], check=True)
    print(f'\n✅ {OUTPUT}  ({os.path.getsize(OUTPUT) / 1024:.0f} KB)')
    subprocess.run(['rm', '-rf', ICONSET])


if __name__ == '__main__':
    main()
