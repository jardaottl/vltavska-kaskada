#!/usr/bin/env python3
"""Fetch hourly filled storage volumes of the Vltava Cascade from PVL."""
from __future__ import annotations

import csv
import html
import re
import ssl
import urllib.request
import certifi
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

URL = "https://www.pvl.cz/portal/Nadrze/cz/pc/Objemy.aspx?data=1"
TZ = ZoneInfo("Europe/Prague")
EXPECTED = [
    "VD Lipno 1", "VD Lipno 2", "VD Hněvkovice", "VD Kořensko",
    "VD Orlík", "VD Kamýk", "VD Slapy", "VD Štěchovice", "VD Vrané",
]
OUT = Path("docs")
CSV = OUT / "data.csv"
ISSUER_CERT = Path("alpiro-intermediate.crt")


def norm(s: str) -> str:
    s = html.unescape(s).replace("\xa0", " ").strip()
    return " ".join(s.split())


class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "tr":
            self.row = []
        elif tag.lower() in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(norm("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
            self.cell = None


def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (compatible; VltavaCascadeMonitor/1.0)",
        "Accept-Language": "cs-CZ,cs;q=0.9",
    })

    if not ISSUER_CERT.is_file():
        raise FileNotFoundError(
            f"PVL issuer certificate not found: {ISSUER_CERT}"
        )

    # Použije běžné certifikáty certifi i certifikát stažený workflow.
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cafile=str(ISSUER_CERT))

    with urllib.request.urlopen(req, timeout=30, context=context) as response:
        page = response.read().decode(
            response.headers.get_content_charset() or "utf-8",
            "replace",
        )

    parser = Rows()
    parser.feed(page)

    found = {}
    expected = {
        re.sub(r"\s+", " ", name).casefold(): name
        for name in EXPECTED
    }

    # PVL může používat také římské číslice u názvů Lipna.
    aliases = {
        "vd lipno i": "vd lipno 1",
        "vd lipno ii": "vd lipno 2",
    }

    for row in parser.rows:
        if len(row) < 4:
            continue

        name = norm(row[0]).casefold()
        name = aliases.get(name, name)
        canonical = expected.get(name)

        if not canonical or norm(row[1]).casefold() != "vltava":
            continue

        # PVL přidalo sloupec „Účel“ před datum.
        # Objem může být ve starém sloupci 4 (index 3)
        # nebo v novém sloupci 5 (index 4). Datum přeskočíme,
        # protože přijímáme pouze číselnou hodnotu.
        volume = None

        for cell in row[3:5]:
            candidate = norm(cell).replace(" ", "").replace(",", ".")

            if re.fullmatch(r"\d+(?:\.\d+)?", candidate):
                volume = float(candidate)
                break

        if volume is None:
            continue

        found[canonical] = volume

    missing = [name for name in EXPECTED if name not in found]

    if missing:
        raise RuntimeError(
            "PVL page did not provide filled-storage values for: "
            + ", ".join(missing)
        )

    return found


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    values = fetch()
    now = datetime.now(TZ).isoformat(timespec="seconds")
    total = round(sum(values.values()), 3)

    new_file = not CSV.exists() or CSV.stat().st_size == 0

    with CSV.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")

        if new_file:
            writer.writerow(
                ["čas"]
                + [name.removeprefix("VD ") for name in EXPECTED]
                + ["součet"]
            )

        writer.writerow(
            [now]
            + [values[name] for name in EXPECTED]
            + [total]
        )

    print(f"{now}: saved {total:.3f} million m³")


if __name__ == "__main__":
    main()
