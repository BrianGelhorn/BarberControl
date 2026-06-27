#!/usr/bin/env python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = [
    "01Enero",
    "02Febrero",
    "03Marzo",
    "04Abril",
    "05Mayo",
    "06Junio",
    "07Julio",
    "08Agosto",
    "09Septiembre",
    "10Octubre",
    "11Noviembre",
    "12Diciembre",
]


def main():
    fechas = ROOT / "Fechas"
    fechas.mkdir(exist_ok=True)
    for month in MONTHS:
        path = fechas / month
        path.mkdir(exist_ok=True)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
