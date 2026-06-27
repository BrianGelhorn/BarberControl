#!/usr/bin/env python
import shutil
import sys
from datetime import date

from create_fechas_dirs import MONTHS, ROOT


def parse_date():
    if len(sys.argv) == 1:
        return date.today()
    if len(sys.argv) == 2:
        return date.fromisoformat(sys.argv[1])
    raise SystemExit("Uso: python scripts/create_today_file.py [YYYY-MM-DD]")


def template_path():
    for path in (ROOT / "templates" / "Dia-Mes-template.xlsx", ROOT / "Dia-Mes-template.xlsx"):
        if path.exists():
            return path
    raise SystemExit("No encontre templates/Dia-Mes-template.xlsx ni Dia-Mes-template.xlsx")


def main():
    today = parse_date()
    month_dir = ROOT / "Fechas" / MONTHS[today.month - 1]
    month_dir.mkdir(parents=True, exist_ok=True)

    target = month_dir / f"{today.day:02d}-{today.month:02d}.xlsx"
    if target.exists():
        print(f"Ya existe: {target.relative_to(ROOT)}")
        return

    shutil.copy2(template_path(), target)
    print(f"Creado: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
