# 주보 PDF → 홈페이지용 JPG (bulletin-NNN-1.jpg, -2.jpg)
# 홈페이지에 올릴 때 지울 이름(HIDE)을 글자째 지우고(앞뒤 쉼표 포함) 변환합니다. (사용자 요청 2026-11-21)
# 사용: python3 bulletin_to_jpg.py 주보.pdf NNN 저장폴더
# 필요: pip install pymupdf pillow
import sys, io
import pymupdf
from PIL import Image

HIDE = ['(이름)']   # 교회 청소 안내 등 어디에 있든 홈페이지에서는 뺌


def chars_of(page):
    out = []
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                for c in s['chars']:
                    out.append((c['c'], pymupdf.Rect(c['bbox'])))
    return out


def redact(page):
    ch = chars_of(page)
    text = ''.join(c for c, _ in ch)
    found = 0
    for name in HIDE:
        start = 0
        while True:
            i = text.find(name, start)
            if i < 0:
                break
            j = i + len(name)
            idx = list(range(i, j))
            # 바로 앞(공백 건너뜀)의 쉼표를 함께 지움. 앞에 없고 뒤에 있으면 뒤 쉼표를 지움
            k = i - 1
            while k >= 0 and text[k].isspace():
                k -= 1
            if k >= 0 and text[k] in ',，':
                idx.append(k)
            else:
                k = j
                while k < len(text) and text[k].isspace():
                    k += 1
                if k < len(text) and text[k] in ',，':
                    idx.append(k)
            for n in idx:
                r = ch[n][1]
                # 글자 상자가 윗줄·아랫줄과 겹치면 옆 글자까지 지워지므로 가운데 부분만 표시
                cy, hh = (r.y0 + r.y1) / 2, 0.4  # 줄 간격이 글자 상자보다 좁아 아주 얇게
                page.add_redact_annot(pymupdf.Rect(r.x0 + 0.3, cy - hh, r.x1 - 0.3, cy + hh), fill=False)
            found += 1
            start = j
    if found:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    return found


def main(pdf, num, outdir='.'):
    doc = pymupdf.open(pdf)
    total = 0
    for pno in range(min(2, len(doc))):
        page = doc[pno]
        total += redact(page)
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
        h = round(img.height * 1518 / img.width)
        img = img.resize((1518, h), Image.LANCZOS)
        path = f'{outdir}/bulletin-{num}-{pno + 1}.jpg'
        img.save(path, quality=85)
        print(path, img.size)
    print('지운 이름 수:', total)


if __name__ == '__main__':
    main(*sys.argv[1:])
