#!/usr/bin/env python3
"""生成 OCR 测试图片：低分辨率、反光、模糊等退化场景"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import string

output_dir = Path(__file__).parent / "output" / "ocr_test_images"
output_dir.mkdir(parents=True, exist_ok=True)

# 使用系统字体
try:
    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
except:
    font = ImageFont.load_default()

# 测试文本（中英文混合，有标准答案）
test_texts = [
    "Hello World 123",
    "Python 3.14",
    "低分辨率文字测试",
    "模糊与反光识别",
    "The quick brown fox jumps over the lazy dog",
    "0123456789",
    "ABCDabcd1234",
    "机器学习深度学习",
]

def add_glare(img, intensity=0.4):
    """添加反光效果"""
    width, height = img.size
    # 创建一个半透明白色渐变作为反光
    glare = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glare)
    # 随机位置的反光区域
    x1 = random.randint(0, width // 2)
    y1 = random.randint(0, height // 2)
    x2 = x1 + random.randint(width // 4, width // 2)
    y2 = y1 + random.randint(height // 4, height // 2)
    draw.ellipse([x1, y1, x2, y2], fill=(255, 255, 255, int(255 * intensity)))
    # 转换为 RGB 并混合
    glare_rgb = glare.convert('RGB')
    return Image.blend(img, glare_rgb, alpha=intensity * 0.5)

def add_noise(img, intensity=20):
    """添加噪声"""
    pixels = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            if random.random() < 0.1:
                noise = random.randint(-intensity, intensity)
                pixels[i, j] = tuple(max(0, min(255, c + noise)) for c in pixels[i, j])
    return img

# 生成不同退化等级的测试图
configs = [
    ("clear", "清晰原图", lambda img: img),
    ("low_res", "低分辨率(50x50)", lambda img: img.resize((50, 50), Image.LANCZOS).resize((400, 100), Image.LANCZOS)),
    ("blur_light", "轻度模糊", lambda img: img.filter(ImageFilter.GaussianBlur(radius=1))),
    ("blur_heavy", "重度模糊", lambda img: img.filter(ImageFilter.GaussianBlur(radius=4))),
    ("glare_light", "轻度反光", lambda img: add_glare(img, 0.3)),
    ("glare_heavy", "重度反光", lambda img: add_glare(img, 0.7)),
    ("noise", "噪声干扰", lambda img: add_noise(img, 40)),
    ("combined", "综合退化(低分+模糊+反光)", lambda img: add_glare(
        img.filter(ImageFilter.GaussianBlur(radius=2)).resize((60, 30), Image.LANCZOS).resize((400, 100), Image.LANCZOS),
        0.5
    )),
]

generated = []
for text in test_texts:
    # 创建基础图像
    img = Image.new('RGB', (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 25), text, fill=(0, 0, 0), font=font)
    
    for suffix, desc, transform in configs:
        transformed = transform(img.copy())
        fname = f"{text[:10]}_{suffix}.png"
        fpath = output_dir / fname
        transformed.save(fpath)
        generated.append({
            "file": str(fpath),
            "text": text,
            "degradation": desc,
            "suffix": suffix,
        })
        print(f"生成: {fname} ({desc})")

# 保存标准答案
import json
with open(output_dir / "ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(generated, f, ensure_ascii=False, indent=2)

print(f"\n共生成 {len(generated)} 张测试图片，保存在 {output_dir}")
print("标准答案已保存到 ground_truth.json")
