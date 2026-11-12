#!/usr/bin/env python3
"""유튜브 채널의 최신 주일예배 영상을 찾아 index.html의 설교 영역과 썸네일을 갱신합니다.

GitHub Actions(.github/workflows/update-sermon.yml)가 주일 오후마다 실행합니다.
영상 제목에 '주일예배' 또는 '예배'가 들어간 가장 최근 영상을 고릅니다.
설명란에 '본문: ...', '설교: ...'(또는 '설교자: ...') 줄이 있으면 함께 표시합니다.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

HANDLE = "Godwillhanachurch"
CHANNEL_ID = os.environ.get("YT_CHANNEL_ID", "").strip()  # 비어 있으면 핸들로 찾음
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "index.html")
THUMB = os.path.join(ROOT, "images", "sermon-thumb.jpg")
KST = dt.timezone(dt.timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (church-site-updater)", "Accept-Language": "ko-KR,ko;q=0.9",
      "Cookie": "CONSENT=YES+1; SOCS=CAI"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def channel_id():
    if CHANNEL_ID:
        return CHANNEL_ID
    page = get(f"https://www.youtube.com/@{HANDLE}")
    for pat in (r'"externalId":"(UC[\w-]{22})"', r'"channelId":"(UC[\w-]{22})"',
                r'youtube\.com/channel/(UC[\w-]{22})'):
        m = re.search(pat, page)
        if m:
            return m.group(1)
    sys.exit("채널 ID를 찾지 못했습니다.")


def entries(feed_xml):
    root = ET.fromstring(feed_xml)
    for e in root.findall("a:entry", NS):
        yield {
            "id": e.findtext("yt:videoId", "", NS),
            "title": (e.findtext("a:title", "", NS) or "").strip(),
            "published": e.findtext("a:published", "", NS),
            "desc": e.findtext("media:group/media:description", "", NS) or "",
        }


def pick(items):
    items = [i for i in items if i["id"]]
    for key in ("주일예배", "예배"):
        hits = [i for i in items if key in i["title"]]
        if hits:
            return max(hits, key=lambda i: i["published"])
    return None


def from_pages():
    """RSS가 안 될 때: 채널의 실시간(streams)·동영상 목록 화면에서 직접 찾습니다."""
    for tab in ("streams", "videos"):
        try:
            page = get(f"https://www.youtube.com/@{HANDLE}/{tab}")
        except Exception as ex:
            print(f"{tab} 화면을 읽지 못함:", ex)
            continue
        found = []
        for m in re.finditer(r'"videoId":"([\w-]{11})"', page):
            vid = m.group(1)
            if vid in [x[0] for x in found]:
                continue
            near = page[m.start():m.start() + 8000]
            t = (re.search(r'"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"', near)
                 or re.search(r'"title":\{"content":"((?:[^"\\]|\\.)*)"', near)
                 or re.search(r'"accessibilityText":"((?:[^"\\]|\\.)*)"', near))
            if not t:
                continue
            found.append((vid, json.loads('"' + t.group(1) + '"'), "upcomingEventData" in near[:3000] or "UPCOMING" in near[:3000]))
        print(f"{tab}: 화면 {len(page)}자, 영상 {len(found)}개 —", [x[1][:20] for x in found[:5]])
        for vid, title, upcoming in found:
            if upcoming or "예배" not in title:
                continue
            watch = get(f"https://www.youtube.com/watch?v={vid}")
            d = re.search(r'"(?:publishDate|uploadDate)":"([^"]+)"', watch) or \
                re.search(r'itemprop="(?:datePublished|uploadDate)" content="([^"]+)"', watch)
            desc = re.search(r'"shortDescription":"((?:[^"\\]|\\.)*)"', watch)
            pub = d.group(1) if d else dt.datetime.now(KST).isoformat()
            if len(pub) == 10:
                pub += "T12:00:00+09:00"
            return {"id": vid, "title": title, "published": pub,
                    "desc": json.loads('"' + desc.group(1) + '"') if desc else ""}
    return None


def sunday_of(published):
    d = dt.datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(KST).date()
    back = (d.weekday() + 1) % 7  # 일요일까지 거슬러 간 날 수 (일=0)
    return d - dt.timedelta(days=back) if back <= 3 else d + dt.timedelta(days=7 - back)


def field(desc, *labels):
    for lb in labels:
        m = re.search(rf"{lb}\s*[:：]\s*(.+)", desc)
        if m:
            return m.group(1).strip()
    return ""


def thumb_src(day, vid):
    """설교 슬라이드 첫 화면(images/sermon-slide-YYYYMMDD.jpg)이 있으면 그것을, 없으면 유튜브 썸네일을 씁니다."""
    slide = f"images/sermon-slide-{day:%Y%m%d}.jpg"
    if os.path.exists(os.path.join(ROOT, slide)):
        return slide
    return f"images/sermon-thumb.jpg?v={vid}"


def render(v):
    dm = re.search(r"(\d{2,4})\.\s*(\d{1,2})\.\s*(\d{1,2})", v["title"])
    if dm:  # 제목의 '26. 11. 01.' 같은 날짜를 우선 사용
        yy = int(dm.group(1))
        day = dt.date(yy + 2000 if yy < 100 else yy, int(dm.group(2)), int(dm.group(3)))
    else:
        day = sunday_of(v["published"])
    title = field(v["desc"], "설교 제목", "제목")
    if not title:  # 설명란에 제목이 없으면 영상 제목에서 날짜·꾸밈을 뺀 나머지
        rest = re.sub(r"^\s*\[[^\]]*\]\s*", "", v["title"])
        rest = re.sub(r"\d{2,4}\.\s*\d{1,2}\.\s*\d{1,2}\.?", "", rest).strip(" |·-")
        title = rest if rest and re.sub(r"\s", "", rest) not in ("주일예배", "예배") else "주일예배 말씀"
    head = f"[주일예배] {title}" if title != "주일예배 말씀" else f"[주일예배] {day.year}년 {day.month}월 {day.day}일"
    passage = field(v["desc"], "본문", "말씀")
    preacher = field(v["desc"], "설교자", "설교")
    e = html.escape
    meta_short = " · ".join(x for x in (passage, preacher) if x)
    meta_long = " / ".join(x for x in (f"{day.year}년 {day.month}월 {day.day}일 주일예배",
                                         f"본문: {passage}" if passage else "",
                                         f"설교자: {preacher}" if preacher else "") if x)
    url = f"https://www.youtube.com/watch?v={v['id']}"
    return (
        f'          <a class="thumb" href="{url}" target="_blank" rel="noopener" aria-label="{day.month}월 {day.day}일 주일예배 영상 보기 (유튜브)">\n'
        f'            <img class="thumb-img" src="{thumb_src(day, v["id"])}" alt="" loading="lazy" onload="this.parentNode.classList.add(\'has-img\')" onerror="this.remove()">\n'
        f'            <span class="thumb-date">{day.year}. {day.month}. {day.day} 주일예배</span>\n'
        f'            <strong>{e(title)}</strong>\n'
        + (f'            <span class="thumb-meta">{e(meta_short)}</span>\n' if meta_short else "")
        + '            <span class="play" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span>\n'
        '          </a>\n'
        f'          <h2 class="latest-title">{e(head)}</h2>\n'
        f'          <p class="latest-meta">{e(meta_long)}</p>\n'
    )


def main():
    v = None
    try:
        cid = channel_id()
        print("채널 ID:", cid)
        for q in (f"channel_id={cid}", f"playlist_id=UU{cid[2:]}"):
            try:
                v = pick(entries(get(f"https://www.youtube.com/feeds/videos.xml?{q}")))
                if v:
                    break
            except Exception as ex:
                print("RSS 실패:", q, ex)
    except BaseException as ex:  # RSS 장애(404 등) 시 목록 화면으로 대체
        print("RSS를 읽지 못함:", ex)
    if not v:
        v = from_pages()
    if not v:
        print("예배 영상을 찾지 못해 그대로 둡니다.")
        return
    if os.environ.get("PREVIEW"):
        print("미리보기 설명란:\n" + v["desc"][:600])
        print("미리보기 결과:\n" + render(v))
        return
    page = open(INDEX, encoding="utf-8").read()
    m = re.search(r"(<!-- sermon:start[^>]*-->\n)(.*?)(<!-- sermon:end -->)", page, re.S)
    if not m:
        sys.exit("index.html에서 sermon 표시를 찾지 못했습니다.")
    if f"watch?v={v['id']}\"" in m.group(2):
        print("이미 최신 영상입니다:", v["title"])
        return
    page = page[:m.start(2)] + render(v) + page[m.end(2):]
    open(INDEX, "w", encoding="utf-8").write(page)
    for size in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            img = get(f"https://i.ytimg.com/vi/{v['id']}/{size}.jpg", binary=True)
            if len(img) > 5000:
                open(THUMB, "wb").write(img)
                break
        except Exception:
            continue
    print("새 영상으로 갱신:", v["title"])


SHORTS_THUMB = os.path.join(ROOT, "images", "shorts-thumb.jpg")


def latest_short():
    """가장 최근 숏츠 영상(id, 제목)을 찾습니다. RSS의 /shorts/ 링크 → 채널 숏츠 화면 순서로 봅니다."""
    try:
        cid = channel_id()
        root = ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
        best = None
        for e in root.findall("a:entry", NS):
            link = e.find("a:link", NS)
            href = link.get("href", "") if link is not None else ""
            if "/shorts/" in href:
                item = {"id": e.findtext("yt:videoId", "", NS), "title": (e.findtext("a:title", "", NS) or "").strip(),
                        "published": e.findtext("a:published", "", NS)}
                if not best or item["published"] > best["published"]:
                    best = item
        if best:
            return best
    except BaseException as ex:
        print("숏츠 RSS 실패:", ex)
    try:
        page = get(f"https://www.youtube.com/@{HANDLE}/shorts")
        m = re.search(r'/shorts/([\w-]{11})', page) or re.search(r'"videoId":"([\w-]{11})"', page)
        if m:
            near = page[m.start():m.start() + 6000]
            t = (re.search(r'"primaryText":\{"content":"((?:[^"\\]|\\.)*)"', near)
                 or re.search(r'"accessibilityText":"((?:[^"\\]|\\.)*)"', near))
            title = json.loads('"' + t.group(1) + '"') if t else ""
            return {"id": m.group(1), "title": title, "published": ""}
    except Exception as ex:
        print("숏츠 화면을 읽지 못함:", ex)
    return None


def render_short(v):
    e = html.escape
    title = re.sub(r"\s*#\S+", "", v["title"]).strip() or "이번 주 설교 숏츠"
    url = f"https://www.youtube.com/shorts/{v['id']}"
    return (
        f'          <a class="thumb thumb-short" href="{url}" target="_blank" rel="noopener" aria-label="설교 숏츠 보기 (유튜브)">\n'
        f'            <img class="thumb-img" src="images/shorts-thumb.jpg?v={v["id"]}" alt="" loading="lazy" onload="this.parentNode.classList.add(\'has-img\')" onerror="this.remove()">\n'
        '            <span class="thumb-date">설교 숏츠</span>\n'
        f'            <strong>{e(title)}</strong>\n'
        '            <span class="play" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span>\n'
        '          </a>\n'
        f'          <h2 class="latest-title">[숏츠] {e(title)}</h2>\n'
    )


def update_shorts():
    v = latest_short()
    if not v:
        print("숏츠를 찾지 못해 그대로 둡니다.")
        return
    print("최신 숏츠:", v["id"], v["title"])
    if os.environ.get("PREVIEW"):
        print("숏츠 미리보기:\n" + render_short(v))
        return
    page = open(INDEX, encoding="utf-8").read()
    m = re.search(r"(<!-- shorts:start[^>]*-->\n)(.*?)(<!-- shorts:end -->)", page, re.S)
    if not m:
        print("index.html에 shorts 표시가 없어 숏츠는 건너뜁니다.")
        return
    if f"/shorts/{v['id']}\"" in m.group(2):
        print("이미 최신 숏츠입니다.")
        return
    for size in ("oar2", "oardefault", "hq720", "hqdefault"):
        try:
            img = get(f"https://i.ytimg.com/vi/{v['id']}/{size}.jpg", binary=True)
            if len(img) > 5000:
                open(SHORTS_THUMB, "wb").write(img)
                print("숏츠 썸네일:", size)
                break
        except Exception:
            continue
    page = page[:m.start(2)] + render_short(v) + page[m.end(2):]
    open(INDEX, "w", encoding="utf-8").write(page)
    print("숏츠 갱신:", v["title"])


if __name__ == "__main__":
    main()
    update_shorts()
