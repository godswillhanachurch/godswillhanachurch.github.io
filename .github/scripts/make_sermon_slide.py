#!/usr/bin/env python3
"""주일 설교 카드 그림(images/sermon-slide-YYYYMMDD.jpg)을 기존 설교 슬라이드 첫 화면 모양 그대로 만듭니다.

남색 바탕 · 왼쪽 금색 세로줄 · 날짜(금색) · 제목(흰색, 길면 두 줄) · 본문(옅은 회청색) · 말씀선포 줄(청록).
드라이브의 PPT를 쓰지 않고, 제목·본문·설교자·날짜만 바꿔서 만듭니다. (2026-11-23)

사용법:
  python3 .github/scripts/make_sermon_slide.py --date 2026-11-22 --title "그리스도의 향기" \
      --passage "고린도후서 2장 12~16절" --preacher "이관영 선교사"
  (--line "..." 를 주면 맨 아래 줄을 '말씀선포 · 설교자' 대신 그 문구로)
필요: pillow, Noto Sans CJK 글꼴(우분투: apt-get install fonts-noto-cjk)
"""
import argparse
import datetime as dt
import glob
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 1280, 720
BG = (16, 36, 61)
GOLD = (219, 179, 94)
WHITE = (255, 255, 255)
GRAY = (196, 210, 228)
TEAL = (110, 189, 188)
X = 120           # 글 왼쪽 시작
TITLE_MAX = 470   # 제목 한 줄 최대 폭(넘으면 두 줄)


def font(weight, size):
    for pat in (f"/usr/share/fonts/**/NotoSansCJK-{weight}.ttc", f"/usr/share/fonts/**/NotoSansCJKkr-{weight}.otf",
                f"/usr/share/fonts/**/NotoSansKR-{weight}.*"):
        for path in glob.glob(pat, recursive=True):
            if path.endswith(".ttc"):
                for i in range(10):
                    f = ImageFont.truetype(path, size, index=i)
                    if f.getname()[0] == "Noto Sans CJK KR":
                        return f
            return ImageFont.truetype(path, size)
    raise SystemExit("Noto Sans CJK 글꼴이 없습니다 (apt-get install fonts-noto-cjk)")


def nice_passage(p):
    """'고린도후서 2장  12절 ~ 16절' → '고린도후서  2 장  12–16 절' (슬라이드 표기)."""
    p = re.sub(r"\s+", " ", p.strip())
    m = re.match(r"^(.+?)\s*(\d+)\s*장\s*(\d+)\s*절?\s*(?:[~\-–]\s*(\d+)\s*절?)?\s*$", p)
    if not m:
        return p
    book, ch, v1, v2 = m.groups()
    return f"{book}  {ch} 장  {v1}{'–' + v2 if v2 else ''} 절"


def wrap(draw, text, f):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and draw.textlength(t, font=f) > TITLE_MAX:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines[:3]


def make(day, title, passage="", preacher="", line=None, out=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([79, 106, 85, 575], fill=GOLD)
    d.text((X, 139), f"{day.year} 년  {day.month} 월  {day.day} 일 주일예배 설교", font=font("Bold", 20), fill=GOLD, anchor="ls")
    ft = font("Bold", 56)
    lines = wrap(d, title, ft)
    pitch = 69
    first = 274 if len(lines) >= 2 else 308   # 한 줄이면 두 줄 자리의 가운데
    for i, ln in enumerate(lines):
        d.text((X, first + i * pitch), ln, font=ft, fill=WHITE, anchor="ls")
    if passage:
        d.text((X + 4, 456), nice_passage(passage), font=font("Regular", 26), fill=GRAY, anchor="ls")
    bottom = line if line is not None else (f"말씀선포  ·  {preacher}" if preacher else "")
    if bottom:
        d.text((X + 4, 542), bottom, font=font("Bold", 25), fill=TEAL, anchor="ls")
    out = out or os.path.join(ROOT, "images", f"sermon-slide-{day:%Y%m%d}.jpg")
    im.save(out, "JPEG", quality=86, optimize=True)
    return out


def prune(keep=2):
    """images/sermon-slide-*.jpg는 최근 것 keep개만 남기고 지웁니다. 지운 파일 목록을 돌려줌."""
    files = sorted(glob.glob(os.path.join(ROOT, "images", "sermon-slide-*.jpg")))
    gone = files[:-keep] if len(files) > keep else []
    for f in gone:
        os.remove(f)
    return gone


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--passage", default="")
    ap.add_argument("--preacher", default="")
    ap.add_argument("--line", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-prune", action="store_true")
    a = ap.parse_args()
    print("만듦:", make(dt.date.fromisoformat(a.date), a.title, a.passage, a.preacher, a.line, a.out))
    if not a.no_prune:
        for f in prune():
            print("지움:", f)
