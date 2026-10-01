# Proyecto EuroMillones

Histórico completo de sorteos de EuroMillones (13/02/2004 – 29/09/2026, 1.978 sorteos), análisis estadístico y un selector interactivo que ordena combinaciones según criterios ajustables.

## Contenido

| Ruta | Qué es |
|---|---|
| `data/euromillones_2004_2026.csv` | Un sorteo por fila: `date,n1..n5,s1,s2` |
| `analysis/analizar.py` | Frecuencias, retrasos, distribución de formas, χ² de uniformidad y backtest. Escribe `analysis/resumen.json` |
| `web/plantilla.html` | Selector interactivo (boleto, pesos, top 100/200/500, gráficos) |
| `web/build.py` | Incrusta el CSV en la plantilla y genera `web/euromillones.html` |

```bash
python3 analysis/analizar.py   # regenera resumen.json
python3 web/build.py           # regenera web/euromillones.html
```

## Origen de los datos

La web oficial (euro-millions.com) no era accesible desde el entorno de trabajo, así que los datos proceden del archivo público [daowa89/lottery-archive](https://github.com/daowa89/lottery-archive) (`eu/euromillions/results.csv`). Comprobaciones hechas:

- Todos los sorteos tienen 5 números distintos entre 1 y 50 y 2 estrellas distintas.
- La estrella 11 aparece por primera vez en 2011 y la 12 el 27/09/2016, que coinciden con los cambios de reglas.
- Se eliminó una fila duplicada (06/08/2017, copia del 04/08/2017).
- Quedan pendientes de verificar contra la fuente oficial: 4 filas con fecha fuera de martes/viernes (26/03/2009, 04/07/2010, 12/09/2012, 16/12/2012) y unas 9 fechas de sorteo sin fila. Su efecto en las estadísticas es despreciable.

## Conclusiones del análisis

- Cada combinación tiene una probabilidad de 1 entre 139.838.160.
- Frecuencias de los 50 números: χ² = 59,6 (49 gl), p = 0,14. Estrellas (desde 2016): p = 0,15. Ambas son compatibles con un sorteo perfectamente aleatorio. El estadístico lleva la corrección por extracción sin reemplazo, factor (N−n)/(N−1); sin ella los p-valores salen inflados (0,27 y 0,22).
- Backtest sobre 1.478 sorteos: elegir los 5 números más frecuentes antes de cada sorteo da 0,499 aciertos de media; los «calientes» de los últimos 50, 0,478; los fríos, 0,474. El valor esperado por azar es exactamente 0,5 (hipergeométrica), con IC 95 % de ±0,033: ninguna estrategia se distingue del azar.
- Ninguna combinación ganadora completa se ha repetido.

El selector ordena por parecido con el histórico, no por probabilidad real. El criterio que sí mejora el premio esperado es evitar combinaciones populares (fechas, series, terminaciones repetidas), porque reduce la probabilidad de compartir el bote.
