"""Genera web/euromillones.html incrustando el CSV de sorteos en la plantilla."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "data" / "euromillones_2004_2026.csv")))
data = ";".join(" ".join([r["date"]] + [r[f"n{i}"] for i in range(1, 6)] + [r["s1"], r["s2"]]) for r in rows)
tpl = (ROOT / "web" / "plantilla.html").read_text()
assert "/*DATA*/" in tpl
(ROOT / "web" / "euromillones.html").write_text(tpl.replace("/*DATA*/", data))
print(f"{len(rows)} sorteos -> web/euromillones.html")
