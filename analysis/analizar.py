"""Análisis estadístico del histórico de EuroMillones.

Lee data/euromillones_2004_2026.csv y escribe analysis/resumen.json con:
- frecuencias de números y estrellas (histórico y recientes)
- distribuciones de forma (suma, pares/impares, bajos/altos, consecutivos, decenas)
- pruebas chi-cuadrado de uniformidad
- backtest walk-forward: ¿los números "calientes" aciertan más que el azar?

Solo usa la biblioteca estándar.
"""
import csv
import json
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "euromillones_2004_2026.csv"
OUT = ROOT / "analysis" / "resumen.json"

# Desde el 27/09/2016 hay 12 estrellas; el análisis de estrellas usa solo esa era.
ERA_12_ESTRELLAS = "2016-09-27"
RECIENTES = 200


def cargar():
    with open(CSV) as f:
        filas = list(csv.DictReader(f))
    return [
        {
            "fecha": r["date"],
            "n": sorted(int(r[f"n{i}"]) for i in range(1, 6)),
            "s": sorted((int(r["s1"]), int(r["s2"]))),
        }
        for r in filas
    ]


def chi2_sf(x, k):
    """P(X >= x) para chi-cuadrado con k grados de libertad (gamma incompleta regularizada)."""
    a, x2 = k / 2.0, x / 2.0
    if x2 < a + 1:  # serie
        term = total = 1.0 / a
        n = a
        while abs(term) > 1e-15 * abs(total):
            n += 1
            term *= x2 / n
            total += term
        p = total * math.exp(-x2 + a * math.log(x2) - math.lgamma(a))
        return 1 - p
    # fracción continua
    b = x2 + 1 - a
    c = 1 / 1e-300
    d = 1 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d
        h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return math.exp(-x2 + a * math.log(x2) - math.lgamma(a)) * h


def chi2_uniforme(conteos, categorias):
    total = sum(conteos.get(c, 0) for c in categorias)
    esperado = total / len(categorias)
    x = sum((conteos.get(c, 0) - esperado) ** 2 / esperado for c in categorias)
    return {"chi2": round(x, 2), "gl": len(categorias) - 1, "p": round(chi2_sf(x, len(categorias) - 1), 4)}


def forma(n):
    pares = sum(v % 2 == 0 for v in n)
    bajos = sum(v <= 25 for v in n)
    consec = sum(1 for a, b in zip(n, n[1:]) if b - a == 1)
    decenas = len({(v - 1) // 10 for v in n})
    return {"suma": sum(n), "pares": pares, "bajos": bajos, "consec": consec, "decenas": decenas}


def backtest(sorteos, inicio=500):
    """Para cada sorteo desde `inicio`, elige los 5 números más frecuentes hasta ese momento
    (y los 5 más recientes-calientes, y los 5 más fríos) y cuenta aciertos.
    Esperanza por azar: 5 * 5/50 = 0.5 aciertos por sorteo."""
    acum = Counter()
    ventana = []
    res = {"calientes_historico": 0, "calientes_ultimos50": 0, "frios_historico": 0, "azar": 0}
    rng = random.Random(42)
    n = 0
    for i, d in enumerate(sorteos):
        if i >= inicio:
            real = set(d["n"])
            top = [x for x, _ in sorted(acum.items(), key=lambda t: (-t[1], t[0]))[:5]]
            frio = [x for x, _ in sorted(((k, acum[k]) for k in range(1, 51)), key=lambda t: (t[1], t[0]))[:5]]
            rec = Counter(v for w in ventana[-50:] for v in w)
            top_rec = [x for x, _ in sorted(((k, rec[k]) for k in range(1, 51)), key=lambda t: (-t[1], t[0]))[:5]]
            res["calientes_historico"] += len(real & set(top))
            res["frios_historico"] += len(real & set(frio))
            res["calientes_ultimos50"] += len(real & set(top_rec))
            res["azar"] += len(real & set(rng.sample(range(1, 51), 5)))
            n += 1
        acum.update(d["n"])
        ventana.append(d["n"])
    return {"sorteos_probados": n, "esperado_por_azar": 0.5,
            **{k: round(v / n, 4) for k, v in res.items()}}


def main():
    s = cargar()
    era12 = [d for d in s if d["fecha"] >= ERA_12_ESTRELLAS]
    rec = s[-RECIENTES:]

    fn = Counter(v for d in s for v in d["n"])
    fn_rec = Counter(v for d in rec for v in d["n"])
    fs = Counter(v for d in era12 for v in d["s"])
    fs_rec = Counter(v for d in rec for v in d["s"])
    pares_est = Counter(tuple(d["s"]) for d in era12)

    # Último sorteo en el que salió cada número (retraso en sorteos)
    retraso_n = {k: len(s) for k in range(1, 51)}
    retraso_s = {k: len(era12) for k in range(1, 13)}
    for i, d in enumerate(s):
        for v in d["n"]:
            retraso_n[v] = len(s) - 1 - i
    for i, d in enumerate(era12):
        for v in d["s"]:
            retraso_s[v] = len(era12) - 1 - i

    formas = [forma(d["n"]) for d in s]
    dist = {k: Counter(f[k] for f in formas) for k in ("pares", "bajos", "consec", "decenas")}
    sumas = sorted(f["suma"] for f in formas)

    repetidas = Counter(tuple(d["n"]) for d in s)
    repetidas_completas = Counter(tuple(d["n"] + d["s"]) for d in s)

    resumen = {
        "fuente": "Histórico completo de sorteos EuroMillones (13/02/2004 – " + s[-1]["fecha"] + ")",
        "sorteos": len(s),
        "sorteos_era_12_estrellas": len(era12),
        "primer_sorteo": s[0]["fecha"],
        "ultimo_sorteo": s[-1]["fecha"],
        "ultimos_5": s[-5:],
        "combinaciones_posibles": math.comb(50, 5) * math.comb(12, 2),
        "freq_numeros": {k: fn[k] for k in range(1, 51)},
        "freq_numeros_recientes": {k: fn_rec[k] for k in range(1, 51)},
        "freq_estrellas_era12": {k: fs[k] for k in range(1, 13)},
        "freq_estrellas_recientes": {k: fs_rec[k] for k in range(1, 13)},
        "retraso_numeros": retraso_n,
        "retraso_estrellas": retraso_s,
        "top_pares_estrellas": [[list(p), c] for p, c in pares_est.most_common(10)],
        "chi2_numeros": chi2_uniforme(fn, range(1, 51)),
        "chi2_estrellas_era12": chi2_uniforme(fs, range(1, 13)),
        "suma": {"media": round(sum(sumas) / len(sumas), 1), "p10": sumas[len(sumas) // 10],
                 "p90": sumas[9 * len(sumas) // 10], "min": sumas[0], "max": sumas[-1]},
        "dist_pares": dict(sorted(dist["pares"].items())),
        "dist_bajos": dict(sorted(dist["bajos"].items())),
        "dist_consecutivos": dict(sorted(dist["consec"].items())),
        "dist_decenas": dict(sorted(dist["decenas"].items())),
        "cinco_numeros_repetidos": sum(1 for c in repetidas.values() if c > 1),
        "combinacion_completa_repetida": sum(1 for c in repetidas_completas.values() if c > 1),
        "backtest": backtest(s),
    }
    OUT.write_text(json.dumps(resumen, ensure_ascii=False, indent=1))
    print(json.dumps({k: resumen[k] for k in ("sorteos", "chi2_numeros", "chi2_estrellas_era12", "suma",
                                               "dist_pares", "dist_bajos", "dist_consecutivos", "dist_decenas",
                                               "cinco_numeros_repetidos", "combinacion_completa_repetida",
                                               "backtest", "top_pares_estrellas")}, ensure_ascii=False))
    print("top numeros", fn.most_common(10))
    print("top estrellas", fs.most_common(12))


if __name__ == "__main__":
    main()
