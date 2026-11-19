"""
Pull surface / length / turns for every F1 circuit from DBpedia.

Input : data/circuits.csv   (needs the circuitId and url columns)
Output: circuit_raw_values.csv      every value DBpedia returned (for inspection)
        circuit_details_inserts.sql one INSERT per circuit
        circuits_not_found.txt      circuits with no usable DBpedia data

Run:  python fetch_circuit_details.py  
"""
import csv
import json
import re
import statistics
import time
import urllib.parse
import urllib.request

ENDPOINT = "https://dbpedia.org/sparql"
BATCH = 20

# Property names.
SURFACE_PROP = "dbp:surface"
LENGTH_PROP = "dbp:lengthKm"   
TURNS_PROP = "dbp:turns"

# DBpedia returns many values per circuit (one per layout, old and new, unpaired).
TURNS_RULE = statistics.median_low
LENGTH_RULE = statistics.median_low


def to_dbpedia_uri(wiki_url):
    title = wiki_url.rsplit("/wiki/", 1)[1]
    title = urllib.parse.unquote(title)         
    return "http://dbpedia.org/resource/" + title


def run_query(uris):
    values = " ".join(f"<{u}>" for u in uris)
    query = f"""
    PREFIX dbp: <http://dbpedia.org/property/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    SELECT ?c ?surface ?length ?turns WHERE {{
      VALUES ?c {{ {values} }}
      OPTIONAL {{ ?c dbo:wikiPageRedirects ?r }}
      BIND(COALESCE(?r, ?c) AS ?src)
      OPTIONAL {{ ?src {SURFACE_PROP} ?surface }}
      OPTIONAL {{ ?src {LENGTH_PROP} ?length }}
      OPTIONAL {{ ?src {TURNS_PROP} ?turns }}
    }}"""
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)["results"]["bindings"]


def clean_text(b):
    """Literal text, or the last part of a resource link (.../Asphalt -> Asphalt)."""
    v = b["value"]
    if b["type"] == "uri":
        v = v.rsplit("/", 1)[-1]
    return v.replace("_", " ").strip()


def to_number(b):
    try:
        return float(b["value"])
    except ValueError:
        m = re.search(r"\d+(\.\d+)?", b["value"])
        return float(m.group()) if m else None


def normalize_surface(values):
    """Collapse messy text ('Asphalt/Concrete', 'Asphalt concrete', ...) to a short label."""
    low = [v.lower() for v in values]
    if any("asphalt" in v for v in low):
        return "Asphalt"
    if any("concrete" in v for v in low):
        return "Concrete"
    return sorted(values)[0] if values else None


# Read circuits and build DBpedia URIs
circuits = {}
with open("data/circuits.csv", newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        circuits[to_dbpedia_uri(row["url"])] = int(row["circuitId"])

# Query DBpedia in batches
raw = {cid: {"surface": set(), "length": set(), "turns": set()} for cid in circuits.values()}
uris = list(circuits)
for i in range(0, len(uris), BATCH):
    batch = uris[i:i + BATCH]
    for b in run_query(batch):
        cid = circuits[b["c"]["value"]]
        if "surface" in b:
            raw[cid]["surface"].add(clean_text(b["surface"]))
        if "length" in b and to_number(b["length"]) is not None:
            raw[cid]["length"].add(to_number(b["length"]))
        if "turns" in b and to_number(b["turns"]) is not None:
            raw[cid]["turns"].add(int(to_number(b["turns"])))
    print(f"queried {min(i + BATCH, len(uris))}/{len(uris)}")
    time.sleep(1)

# Write the raw values 
uri_of = {v: k for k, v in circuits.items()}
missing = []
with open("circuit_raw_values.csv", "w", newline="", encoding="utf-8") as rf, \
     open("circuit_details_inserts.sql", "w", encoding="utf-8") as sf:
    w = csv.writer(rf)
    w.writerow(["circuitId", "attribute", "value"])
    for cid, d in sorted(raw.items()):
        for attr, vals in d.items():
            for v in sorted(vals):
                w.writerow([cid, attr, v])
        if not any(d.values()):
            missing.append(cid)
            continue
        surface = normalize_surface(d["surface"])
        length = LENGTH_RULE(d["length"]) if d["length"] else None
        turns = TURNS_RULE(d["turns"]) if d["turns"] else None
        sql = lambda x: "NULL" if x is None else (f"'{x}'" if isinstance(x, str) else str(x))
        sf.write(f"insert into circuit_details values ( {cid}, "
                 f"{sql(surface.replace(chr(39), '') if surface else None)}, "
                 f"{sql(length)}, {sql(turns)} );\n")

with open("circuits_not_found.txt", "w", encoding="utf-8") as mf:
    mf.write("\n".join(f"{cid}  {uri_of[cid]}" for cid in missing))

print(f"Done. {len(raw) - len(missing)} circuits with data, {len(missing)} not found.")