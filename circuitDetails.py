
import csv
import json
import re
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

# Wikipedia asks API users to identify themselves. Put your own contact here.
USER_AGENT = "F1DatabaseCourseProject/1.0 (student project; your_email@example.com)"
API = "https://en.wikipedia.org/w/api.php"

# circuitIds you already filled in by hand; the script leaves them alone.
SKIP_CIRCUIT_IDS = set()   # e.g. {7, 8}

YEARS = re.compile(r"\((\d{4})\s*[\u2013\u2014\-]\s*(\d{4}|present)\)", re.I)
ONE_YEAR = re.compile(r"\((\d{4})\)")
KM = re.compile(r"(\d+(?:\.\d+)?)\s*km", re.I)
MI = re.compile(r"(\d+(?:\.\d+)?)\s*mi\b", re.I)
LAP = re.compile(r"(\d):(\d{2})\.(\d{1,3})")
F1_TAG = re.compile(r"\bF1\b|Formula One")


def clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def fetch_html(title):
    params = urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "text",
        "redirects": 1, "format": "json", "formatversion": 2})
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)["parse"]["text"]


def new_layout(heading="", start=None, end=None):
    return {
        "heading": heading,
        "start": start,
        "end": end,
        "surface": None,
        "km": None,
        "turns": None,
        "f1_record": None,
        "any_record": False
    }


def parse_infobox(html):
    """Return a list of layout dicts found in the first infobox."""
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("table", class_="infobox")

    if box is None:
        return None

    layouts, cur = [], None
    opened = closed = None

    for tr in box.find_all("tr"):
        text = clean(tr.get_text(" ", strip=True))

        if not text:
            continue

        cells = tr.find_all(["th", "td"], recursive=False)

        # Layout heading: a single-cell row containing a year range
        if len(cells) == 1:
            m = YEARS.search(text)
            m1 = ONE_YEAR.search(text)

            if m or m1:
                if m:
                    start = int(m.group(1))
                    end = None if m.group(2).lower() == "present" else int(m.group(2))
                    name = text[:m.start()].strip()
                else:
                    start = end = int(m1.group(1))
                    name = text[:m1.start()].strip()

                cur = new_layout(name, start, end)
                layouts.append(cur)
                continue

        if re.match(r"^Opened\b", text, re.I):
            y = re.search(r"\d{4}", text)
            opened = int(y.group()) if y else None

        elif re.match(r"^Closed\b", text, re.I):
            y = re.search(r"\d{4}", text)
            closed = int(y.group()) if y else None

        elif re.match(r"^Surface\b", text, re.I):
            if cur is None:
                cur = new_layout()
                layouts.append(cur)

            if len(cells) >= 2:
                cur["surface"] = clean(cells[-1].get_text(" ", strip=True))
            else:
                cur["surface"] = clean(
                    re.sub(r"^Surface\s*:?\s*", "", text, flags=re.I)
                )

        elif re.match(r"^Length\b", text, re.I):
            if cur is None:
                cur = new_layout()
                layouts.append(cur)

            km, mi = KM.search(text), MI.search(text)

            if km:
                cur["km"] = float(km.group(1))
            elif mi:
                cur["km"] = round(float(mi.group(1)) * 1.609344, 3)

        elif re.match(r"^Turns\b", text, re.I):
            if cur is None:
                cur = new_layout()
                layouts.append(cur)

            t = re.search(r"\d+", text)
            cur["turns"] = int(t.group()) if t else None

        elif re.match(r"^Race lap record\b", text, re.I):
            if cur is None:
                cur = new_layout()
                layouts.append(cur)

            lap = LAP.search(text)

            if lap:
                cur["any_record"] = True

                if F1_TAG.search(text) and cur["f1_record"] is None:
                    cur["f1_record"] = (
                        f"{lap.group(1)}:{lap.group(2)}."
                        f"{lap.group(3).ljust(3, '0')}"
                    )

    # Single-layout circuits take their years from Opened / Closed
    if len(layouts) == 1 and layouts[0]["start"] is None:
        layouts[0]["start"] = opened
        layouts[0]["end"] = closed

    return layouts


def main():
    circuits = []

    with open("circuits.csv", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            circuits.append((int(row["circuitId"]), row["name"], row["url"]))

    attention = []

    with open("circuit_layouts_review.csv", "w", newline="", encoding="utf-8") as rf, \
         open("circuit_details_from_wiki.sql", "w", encoding="utf-8") as sf:

        review = csv.writer(rf)

        review.writerow([
            "circuitId", "circuit", "layout_heading", "yearOpen",
            "yearClosed", "surface", "km", "turns",
            "f1_lap_record", "keep", "note"
        ])

        for cid, name, url in circuits:

            if cid in SKIP_CIRCUIT_IDS:
                continue

            title = urllib.parse.unquote(
                url.split("/wiki/", 1)[1].split("#")[0]
            )

            try:
                layouts = parse_infobox(fetch_html(title))

            except Exception as e:
                attention.append(f"{cid}  {name}: fetch error ({e})")
                continue

            time.sleep(0.5)

            if not layouts:
                attention.append(f"{cid}  {name}: no infobox or no layout data")
                continue

            kept = []

            for l in layouts:
                notes = []

                complete = l["km"] is not None and l["start"] is not None

                if not complete:
                    notes.append("missing length or start year")

                is_f1 = (
                    l["f1_record"] is not None
                    or (len(layouts) == 1 and not l["any_record"])
                )

                if not is_f1:
                    notes.append("no F1 lap record (probably another series)")

                keep = complete and is_f1

                if keep:
                    kept.append(l)

                l["keep"], l["notes"] = keep, notes

            # Flag overlapping year ranges between kept layouts
            kept.sort(key=lambda l: l["start"])

            for prev, nxt in zip(kept, kept[1:]):
                if (prev["end"] if prev["end"] is not None else 9999) >= nxt["start"]:
                    nxt["notes"].append("OVERLAPS previous layout - check years")

            for l in layouts:

                review.writerow([
                    cid, name, l["heading"], l["start"], l["end"],
                    l["surface"], l["km"], l["turns"],
                    l["f1_record"], l["keep"], "; ".join(l["notes"])
                ])

                if l["keep"]:
                    turns = "NULL" if l["turns"] is None else l["turns"]
                    end = "NULL" if l["end"] is None else l["end"]
                    rec = (
                        "NULL" if l["f1_record"] is None
                        else f"'{l['f1_record']}'"
                    )
                    surface = (
                        "NULL" if l["surface"] is None
                        else "'" + l["surface"].replace("'", "''") + "'"
                    )

                    sf.write(
                        f"insert into circuit_details values ( "
                        f"{cid}, {surface}, {l['km']:.3f}, "
                        f"{turns}, {l['start']}, {end}, {rec} );\n"
                    )

            if not kept:
                attention.append(
                    f"{cid}  {name}: no layout passed the F1 filter"
                )

            print(cid, name, f"{len(kept)} kept / {len(layouts)} found")

    with open("circuits_needing_attention.txt", "w", encoding="utf-8") as af:
        af.write("\n".join(attention))

    print(f"Done. {len(attention)} circuits need attention.")


if __name__ == "__main__":
    main()
