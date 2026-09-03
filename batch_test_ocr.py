#!/usr/bin/env python3
"""批量测试 img2text.py 对退化图片的识别效果"""

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

IMG2TEXT = Path("/Users/liuchen/PycharmProjects/Pic2Word/img2text.py")
TEST_DIR = Path(__file__).parent / "output" / "ocr_test_images"
GROUND_TRUTH = TEST_DIR / "ground_truth.json"

if not IMG2TEXT.exists():
    print(f"错误: 找不到 {IMG2TEXT}")
    sys.exit(1)

with open(GROUND_TRUTH, "r", encoding="utf-8") as f:
    cases = json.load(f)

# 只测试代表性样本：4种文本 x 5种退化 = 20张
target_texts = {"Hello World 123", "低分辨率文字测试", "0123456789", "机器学习深度学习"}
target_suffixes = {"clear", "low_res", "blur_heavy", "glare_heavy", "combined"}
cases = [
    c for c in cases if c["text"] in target_texts and c["suffix"] in target_suffixes
]
print(f"过滤后测试样本: {len(cases)} 张\n")

results = []
for case in cases:
    img_path = case["file"]
    expected = case["text"]
    suffix = case["suffix"]

    cmd = ["python3", IMG2TEXT, img_path, "--strength", "heavy"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        stdout = r.stdout.strip()
        stderr = r.stderr.strip()

        # 解析 OCR 输出格式:
        #   Vision:  "OCR 识别结果 (macOS Vision):\n<text>\n已保存 Word 文件: ..."
        #   Tesseract有结果: "OCR 识别结果 (Tesseract):\n<text>\n已保存 Word 文件: ..."
        #   Tesseract无结果: "OCR 识别结果 (Tesseract):\n\n已保存 Word 文件: ..."
        recognized = ""
        if stdout:
            lines = stdout.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("OCR 识别结果"):
                    # 从下一行开始找非空行，直到遇到"已保存"
                    j = i + 1
                    while j < len(lines):
                        line = lines[j].strip()
                        if not line:
                            j += 1
                            continue
                        if line.startswith("已保存"):
                            break
                        recognized = line
                        break
                    break

        if not recognized and stderr:
            recognized = f"(stderr: {stderr[:100]})"

        match = (
            expected.lower() in recognized.lower()
            or recognized.lower() in expected.lower()
        )
        exact = expected.strip() == recognized.strip()

        # 空结果不算部分匹配
        if not recognized or not recognized.strip():
            match = False
            exact = False

        result = {
            "file": Path(img_path).name,
            "expected": expected,
            "recognized": recognized,
            "degradation": case["degradation"],
            "exact_match": exact,
            "partial_match": match,
        }
        results.append(result)
        status = "✓" if exact else ("~" if match else "✗")
        print(
            f"{status} [{suffix:12}] {case['degradation']:20} | 预期: {expected[:20]:20} | 实际: {recognized[:30]}"
        )
    except subprocess.TimeoutExpired:
        print(f"✗ [{suffix:12}] {case['degradation']:20} | 超时")
        results.append(
            {
                "file": Path(img_path).name,
                "expected": expected,
                "recognized": "(timeout)",
                "degradation": case["degradation"],
                "exact_match": False,
                "partial_match": False,
            }
        )
    except Exception as e:
        print(f"✗ [{suffix:12}] {case['degradation']:20} | 错误: {e}")
        results.append(
            {
                "file": Path(img_path).name,
                "expected": expected,
                "recognized": f"(error: {e})",
                "degradation": case["degradation"],
                "exact_match": False,
                "partial_match": False,
            }
        )

# 统计
exact_count = sum(1 for r in results if r["exact_match"])
partial_count = sum(1 for r in results if r["partial_match"])
total = len(results)
print("\n=== 统计 ===")
print(f"总计: {total}")
print(f"精确匹配: {exact_count} ({exact_count / total * 100:.1f}%)")
print(f"部分匹配: {partial_count} ({partial_count / total * 100:.1f}%)")

# 按退化类型统计
by_degradation = defaultdict(lambda: {"total": 0, "exact": 0, "partial": 0})
for r in results:
    d = r["degradation"]
    by_degradation[d]["total"] += 1
    if r["exact_match"]:
        by_degradation[d]["exact"] += 1
    if r["partial_match"]:
        by_degradation[d]["partial"] += 1

print("\n=== 按退化类型统计 ===")
for d, stats in sorted(by_degradation.items()):
    print(
        f"{d:25} | 总计: {stats['total']} | 精确: {stats['exact']} | 部分: {stats['partial']}"
    )

with open(TEST_DIR / "test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n详细结果已保存到 output/ocr_test_images/test_results.json")
