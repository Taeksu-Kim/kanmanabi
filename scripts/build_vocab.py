#!/usr/bin/env python3
"""어휘 마스터 빌드.

2017 「국제 통용 한국어 표준 교육과정」 XLSX(레벨 백본) 와
「한국어기초사전(krdict)」 XML(일본어 뜻·한자) 을 로컬에서 1회 파싱해
`word + homonym_no (+ pos)` 기준으로 JOIN 한다.

산출:
  data/korean_vocab_master.json     정상 매칭 (일본어 뜻 보유)
  data/korean_vocab_unmatched.json  검토 필요 (미발견/다중후보/일본어 없음)

원본은 data/ 에 캐시하므로 재실행 안전. 원본 파일은 수정하지 않는다.

출처:
- 국립국어원 「국제 통용 한국어 표준 교육과정」 (공공누리 제1유형)
- 국립국어원 「한국어기초사전」 (CC BY-SA 2.0 KR) — 미러: spellcheck-ko/korean-dict-nikl-krdict
"""
import io
import json
import os
import re
import ssl
import urllib.request
from collections import Counter, defaultdict

import openpyxl
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
KRDICT_DIR = os.path.join(DATA, "krdict")

XLSX_URL = (
    "https://www.korean.go.kr/common/download.do?file_path=reportData"
    "&c_file_name=157339df-1904-443a-b1a9-d6d34578ba93.xlsx&o_file_name=list.xlsx"
)
KRDICT_BASE = "https://raw.githubusercontent.com/spellcheck-ko/korean-dict-nikl-krdict/master/"
KRDICT_FILES = [
    "5000.xml", "10000.xml", "15000.xml", "20000.xml", "25000.xml",
    "30000.xml", "35000.xml", "40000.xml", "45000.xml", "50000.xml", "51947.xml",
]

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE
_HAN = re.compile(r"[一-鿿]")


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"  download {os.path.basename(path)} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=_SSL, timeout=300) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    return path


def split_homonym(raw):
    """'가격02' -> ('가격', 2) ; '가게' -> ('가게', None). 'A/B'형은 앞쪽 사용."""
    w = str(raw).strip()
    if "/" in w:
        w = w.split("/")[0].strip()
    m = re.search(r"(\d+)$", w)
    if m:
        return w[: m.start()].strip(), int(m.group(1))
    return w, None


def norm_pos(p):
    if p is None:
        return ""
    return re.sub(r"\s+", "", str(p)).replace("∙", "·")


def feat(el, att):
    for f in el.findall("feat"):
        if f.get("att") == att:
            return f.get("val")
    return None


def parse_ja(lemma, cap=3):
    """'かかく【価格】。ねだん【値段】。…' -> ['かかく【価格】','ねだん【値段】',...] (최대 cap)."""
    if not lemma:
        return []
    parts = re.split(r"[。、]", str(lemma))
    out = [p.strip() for p in parts if p and p.strip()]
    return out[:cap]


# ---------- 1) 백본 로드 ----------
def load_backbone(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = []
    for r in wb["어휘"].iter_rows(min_row=2, values_only=True):
        grade, raw_word, pos, guide = r[2], r[3], r[4], r[5]
        if not raw_word:
            continue
        word, hnum = split_homonym(raw_word)
        level = int(str(grade).replace("급", "")) if grade else None
        rows.append({
            "level": level,
            "word": word,
            "homonym_no": hnum,
            "pos": (str(pos).strip() if pos else ""),
            "guide": (str(guide).strip() if guide else ""),
        })
    return rows


# ---------- 2) krdict 인덱스 ----------
def build_krdict_index(paths):
    by_wh = {}                     # (word, hnum) -> {ja, hanja, pos}
    by_w = defaultdict(list)       # word -> [entry,...]
    for p in paths:
        # recover=True: 사전 원본에 이스케이프 안 된 토큰이 섞여 있어 관용 파싱
        for _, el in etree.iterparse(p, events=("end",), tag="LexicalEntry",
                                     recover=True, huge_tree=True, resolve_entities=False):
            lem = el.find("Lemma")
            wf = feat(lem, "writtenForm") if lem is not None else None
            word = wf.strip() if wf else None
            if not word:
                el.clear()
                continue
            hnum = feat(el, "homonym_number")
            hnum = int(hnum) if (hnum and hnum.isdigit()) else None
            pos = norm_pos(feat(el, "partOfSpeech"))
            origin = feat(el, "origin")
            hanja = origin if (origin and _HAN.search(origin)) else None
            ja = []
            for s in el.findall("Sense"):
                for eq in s.findall("Equivalent"):
                    if feat(eq, "language") == "일본어":
                        ja = parse_ja(feat(eq, "lemma"))
                        break
                if ja:
                    break
            entry = {"ja": ja, "hanja": hanja, "pos": pos}
            by_wh[(word, hnum)] = entry
            by_w[word].append(entry)
            el.clear()
            parent = el.getparent()
            while parent is not None and el.getprevious() is not None:
                del parent[0]
    return by_wh, by_w


# ---------- 3) JOIN ----------
def match(rows, by_wh, by_w):
    master, unmatched = [], []
    stats = Counter()
    by_level = Counter()
    for v in rows:
        w, h, pos = v["word"], v["homonym_no"], norm_pos(v["pos"])
        entry, reason = None, None
        if h is not None and (w, h) in by_wh:
            entry = by_wh[(w, h)]                              # 1차: word+homonym
        else:
            cands = by_w.get(w, [])
            if len(cands) == 1:
                entry = cands[0]                               # 유일 후보
            elif len(cands) > 1:
                pos_hit = [c for c in cands if c["pos"] == pos]
                if len(pos_hit) == 1:
                    entry = pos_hit[0]                         # 2차: word+pos
                else:
                    reason = "multiple_dictionary_candidates"
            else:
                reason = "not_found_in_dictionary"

        if entry and entry["ja"]:
            master.append({**v, "ja": entry["ja"], "hanja": entry["hanja"]})
            stats["matched"] += 1
            by_level[v["level"]] += 1
        else:
            if entry and not entry["ja"]:
                reason = "no_japanese"
            unmatched.append({**v, "reason": reason or "no_japanese"})
            stats[reason or "no_japanese"] += 1
    return master, unmatched, stats, by_level


def main():
    os.makedirs(DATA, exist_ok=True)
    print("[1/4] 원본 확보")
    xlsx = download(XLSX_URL, os.path.join(DATA, "korean_standard_vocab_grammar.xlsx"))
    krdict_paths = [download(KRDICT_BASE + fn, os.path.join(KRDICT_DIR, fn)) for fn in KRDICT_FILES]

    print("[2/4] 백본(교육과정) 로드")
    rows = load_backbone(xlsx)

    print("[3/4] krdict 인덱스 구축")
    by_wh, by_w = build_krdict_index(krdict_paths)

    print("[4/4] JOIN")
    master, unmatched, stats, by_level = match(rows, by_wh, by_w)

    with open(os.path.join(DATA, "korean_vocab_master.json"), "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DATA, "korean_vocab_unmatched.json"), "w", encoding="utf-8") as f:
        json.dump(unmatched, f, ensure_ascii=False, indent=1)

    total = len(rows)
    print("\n===== 검증 통계 =====")
    print(f"교육과정 전체 어휘 수: {total}")
    print(f"정상 매칭(일본어 보유): {stats['matched']} ({stats['matched']*100//total}%)")
    print(f"미발견:              {stats['not_found_in_dictionary']}")
    print(f"다중 후보:            {stats['multiple_dictionary_candidates']}")
    print(f"일본어 대역 없음:      {stats['no_japanese']}")
    print(f"한자 보유(master 중):  {sum(1 for m in master if m['hanja'])}")
    print("등급별 매칭:", {f"{k}급": by_level[k] for k in sorted(by_level)})
    print(f"\n산출: data/korean_vocab_master.json ({len(master)}), "
          f"data/korean_vocab_unmatched.json ({len(unmatched)})")


if __name__ == "__main__":
    main()
