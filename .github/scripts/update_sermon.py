#!/usr/bin/env python3
"""유튜브 채널의 최신 주일예배 영상을 찾아 index.html의 설교 영역과 썸네일을 갱신합니다.

GitHub Actions(.github/workflows/update-sermon.yml)가 주일 오후마다 실행합니다.
영상 제목에 '주일예배' 또는 '예배'가 들어간 가장 최근 영상을 고릅니다.
설명란에 '본문: ...', '설교: ...'(또는 '설교자: ...') 줄이 있으면 함께 표시합니다.
"""
import datetime as dt
import html
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


def render(v):
    title = re.sub(r"^\s*\[[^\]]*\]\s*", "", v["title"]).strip() or v["title"]
    day = sunday_of(v["published"])
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
        f'            <img class="thumb-img" src="images/sermon-thumb.jpg?v={v["id"]}" alt="" loading="lazy" onload="this.parentNode.classList.add(\'has-img\')" onerror="this.remove()">\n'
        f'            <span class="thumb-date">{day.year}. {day.month}. {day.day} 주일예배</span>\n'
        f'            <strong>{e(title)}</strong>\n'
        + (f'            <span class="thumb-meta">{e(meta_short)}</span>\n' if meta_short else "")
        + '            <span class="play" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg></span>\n'
        '          </a>\n'
        f'          <h2 class="latest-title">{e(v["title"])}</h2>\n'
        f'          <p class="latest-meta">{e(meta_long)}</p>\n'
    )


def main():
    cid = channel_id()
    v = pick(entries(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")))
    if not v:
        print("예배 영상을 찾지 못해 그대로 둡니다.")
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


if __name__ == "__main__":
    main()
