#!/usr/bin/env python
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FECHAS_DIR = ROOT / "Fechas"
IMPORT_YEAR = int(os.getenv("IMPORT_YEAR", "2026"))
DB_USER = os.getenv("POSTGRES_USER", "barberia")
DB_NAME = os.getenv("POSTGRES_DB", "barberia_prod")

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
BLOCKS = [(1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16),
          (17, 18, 19, 20), (21, 22, 23, 24), (25, 26, 27, 28),
          (29, 30, 31, 32), (33, 34, 35, 36)]
CORTE_ROWS = range(4, 35)


def clean(value):
    return "" if value is None else str(value).strip()


def col_number(cell_ref):
    n = 0
    for ch in re.match(r"[A-Z]+", cell_ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n


def money(value):
    value = clean(value).replace("$", "").replace(".", "").replace(",", ".")
    return value if re.match(r"^\d+(\.\d+)?$", value) else ""


def is_mp(value):
    return "true" if clean(value).lower() == "x" else "false"


def parse_time(value):
    value = clean(value).replace(".", " ").replace(":", " ")
    m = re.match(r"^(\d{1,2})\s+(\d{1,2})$", value)
    if not m and re.match(r"^\d{3,4}$", value):
        m = re.match(r"^(\d{1,2})(\d{2})$", value)
    if not m:
        numbers = re.findall(r"\d{1,2}", value)
        if len(numbers) >= 2:
            m = re.match(r"^(\d{1,2})\s+(\d{1,2})$", " ".join(numbers[:2]))
    if not m:
        return ""
    hour, minute = map(int, m.groups())
    return f"{hour:02d}:{minute:02d}:00" if 0 <= hour <= 23 and 0 <= minute <= 59 else ""


def date_from_filename(path):
    m = re.search(r"(\d{2})-(\d{2})", path.name)
    if not m:
        raise ValueError(f"no pude inferir fecha desde {path}")
    day, month = map(int, m.groups())
    return dt.date(IMPORT_YEAR, month, day).isoformat()


def excel_date(serial, path):
    try:
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(float(serial)))).isoformat()
    except (TypeError, ValueError):
        fallback = date_from_filename(path)
        print(f"aviso: {path.relative_to(ROOT)} sin fecha Excel valida, uso {fallback}")
        return fallback


def parse_retiro(rows):
    for row in rows.values():
        for col, value in row.items():
            if clean(value).lower() == "retiro:":
                return money(row.get(col + 1)) or None
    return None


def read_sheet(z, sheet_name, shared):
    root = ET.fromstring(z.read(sheet_name))
    rows = {}
    for row in root.findall(".//a:row", NS):
        row_num = int(row.attrib["r"])
        rows[row_num] = {}
        for cell in row.findall("a:c", NS):
            value_node = cell.find("a:v", NS)
            value = "" if value_node is None else value_node.text
            if cell.attrib.get("t") == "s" and value != "":
                value = shared[int(value)]
            rows[row_num][col_number(cell.attrib["r"])] = clean(value)
    return rows


def workbook_sheets(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//a:t", NS)) for si in root.findall("a:si", NS)]
        return [read_sheet(z, name, shared) for name in z.namelist() if name.startswith("xl/worksheets/sheet")]


def parse_file(path):
    cortes_sheet = None
    extras_sheet = None
    for sheet in workbook_sheets(path):
        if clean(sheet.get(2, {}).get(1)).lower() == "hora":
            cortes_sheet = sheet
        if clean(sheet.get(1, {}).get(1)).lower() == "salida de caja":
            extras_sheet = sheet

    if not cortes_sheet:
        raise ValueError(f"{path}: no encontre hoja de cortes")

    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    invalidos = 0
    jornada = {
        "fecha": excel_date(cortes_sheet.get(1, {}).get(6, ""), path),
        "caja_inicial": money(cortes_sheet.get(1, {}).get(9)) or "0",
        "comision_barberos": money(cortes_sheet.get(1, {}).get(13)) or "0",
        "retiro": parse_retiro(cortes_sheet),
        "archivo_origen": rel,
    }

    cortes = []
    for block_index, (hora_col, importe_col, propina_col, mp_col) in enumerate(BLOCKS, 1):
        barbero = clean(cortes_sheet.get(3, {}).get(importe_col))
        if not barbero or barbero.lower().startswith("barbero"):
            continue
        for row_num in CORTE_ROWS:
            row = cortes_sheet[row_num]
            importe = money(row.get(importe_col))
            if not importe:
                continue
            hora = parse_time(row.get(hora_col))
            if not hora:
                hora = None
                invalidos += 1
            cortes.append({
                "barbero": barbero,
                "hora": hora,
                "importe": importe,
                "propina": money(row.get(propina_col)) or None,
                "mercadoPago": is_mp(row.get(mp_col)),
                "fila_origen": row_num,
                "columna_origen": str(importe_col),
            })

    salidas, ventas, adelantos = [], [], []
    if extras_sheet:
        for row_num, row in sorted(extras_sheet.items()):
            salida_importe = money(row.get(2))
            if 3 <= row_num < 19 and salida_importe:
                salidas.append({
                    "motivo": clean(row.get(1)) or None,
                    "importe": salida_importe,
                    "mercadoPago": is_mp(row.get(3)),
                    "fila_origen": row_num,
                })
            venta_importe = money(row.get(7))
            if row_num >= 3 and venta_importe and clean(row.get(6)).lower() not in ("", "total"):
                ventas.append({
                    "producto": clean(row.get(6)),
                    "importe": venta_importe,
                    "mercadoPago": is_mp(row.get(8)),
                    "fila_origen": row_num,
                })
            adelanto_importe = money(row.get(2))
            if 21 <= row_num <= 35 and clean(row.get(1)) and clean(row.get(2)):
                if not adelanto_importe:
                    invalidos += 1
                adelantos.append({
                    "barbero": clean(row.get(1)),
                    "importe": adelanto_importe or None,
                    "mercadoPago": is_mp(row.get(3)),
                    "fila_origen": row_num,
                })

    return jornada, cortes, salidas, ventas, adelantos, invalidos


def sql_text(value):
    if value in (None, ""):
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def values(rows, fields):
    if not rows:
        return ""
    return "INSERT INTO tmp_" + fields[0] + " VALUES\n" + ",\n".join(
        "(" + ", ".join(sql_text(row.get(field)) for field in fields[1:]) + ")" for row in rows
    ) + ";\n"


def run_psql(sql):
    cmd = ["docker", "compose", "exec", "-T", "postgres", "psql", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-U", DB_USER, "-d", DB_NAME]
    result = subprocess.run(cmd, cwd=ROOT, input=sql, text=True, encoding="utf-8", check=True, stdout=subprocess.PIPE)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def import_file(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    jornada, cortes, salidas, ventas, adelantos, invalidos = parse_file(path)
    today = dt.date.today().isoformat()

    barberos = [{"nombre": row["barbero"]} for row in cortes + adelantos]
    sql = f"""
BEGIN;
LOCK TABLE "ArchivosImportados", "Jornadas", "Barberos", "Cortes", "SalidasCaja", "Ventas", "Adelantos" IN EXCLUSIVE MODE;
CREATE TEMP TABLE tmp_barberos(nombre text);
CREATE TEMP TABLE tmp_cortes(barbero text, hora time, importe numeric, propina numeric, "mercadoPago" boolean, fila_origen integer, columna_origen text);
CREATE TEMP TABLE tmp_salidas(motivo text, importe numeric, "mercadoPago" boolean, fila_origen integer);
CREATE TEMP TABLE tmp_ventas(producto text, importe numeric, "mercadoPago" boolean, fila_origen integer);
CREATE TEMP TABLE tmp_adelantos(barbero text, importe numeric, "mercadoPago" boolean, fila_origen integer);
{values(barberos, ["barberos", "nombre"])}
{values(cortes, ["cortes", "barbero", "hora", "importe", "propina", "mercadoPago", "fila_origen", "columna_origen"])}
{values(salidas, ["salidas", "motivo", "importe", "mercadoPago", "fila_origen"])}
{values(ventas, ["ventas", "producto", "importe", "mercadoPago", "fila_origen"])}
{values(adelantos, ["adelantos", "barbero", "importe", "mercadoPago", "fila_origen"])}
WITH nuevos AS (
  SELECT DISTINCT nombre FROM tmp_barberos t
  WHERE nombre IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM "Barberos" b WHERE lower(b."nombre") = lower(t.nombre))
), base AS (
  SELECT COALESCE(max("id"), 0) AS id FROM "Barberos"
)
INSERT INTO "Barberos"("id", "nombre")
SELECT base.id + row_number() OVER (ORDER BY nuevos.nombre), nuevos.nombre
FROM nuevos, base;

CREATE TEMP TABLE tmp_existing AS
SELECT j."id" AS id_jornada, a."id" AS id_archivo, a."hash"
FROM "Jornadas" j
JOIN "ArchivosImportados" a ON a."id" = j."id_archivo"
WHERE j."archivo_origen" = {sql_text(rel)};

CREATE TEMP TABLE tmp_target(id_jornada integer);

DELETE FROM "Cortes" WHERE "id_jornada" IN (SELECT id_jornada FROM tmp_existing WHERE "hash" <> {sql_text(digest)});
DELETE FROM "SalidasCaja" WHERE "id_jornada" IN (SELECT id_jornada FROM tmp_existing WHERE "hash" <> {sql_text(digest)});
DELETE FROM "Ventas" WHERE "id_jornada" IN (SELECT id_jornada FROM tmp_existing WHERE "hash" <> {sql_text(digest)});
DELETE FROM "Adelantos" WHERE "id_jornada" IN (SELECT id_jornada FROM tmp_existing WHERE "hash" <> {sql_text(digest)});

UPDATE "Jornadas" j
SET "fecha" = {sql_text(jornada["fecha"])},
    "caja_inicial" = {jornada["caja_inicial"]},
    "comision_barberos" = {jornada["comision_barberos"]},
    "retiro" = {jornada["retiro"] or "NULL"}
FROM tmp_existing e
WHERE j."id" = e.id_jornada
  AND e."hash" <> {sql_text(digest)};

UPDATE "ArchivosImportados" a
SET "nombre" = {sql_text(rel)},
    "hash" = {sql_text(digest)},
    "fecha_actualizacion" = {sql_text(today)}
FROM tmp_existing e
WHERE a."id" = e.id_archivo
  AND e."hash" <> {sql_text(digest)};

INSERT INTO tmp_target(id_jornada)
SELECT id_jornada FROM tmp_existing WHERE "hash" <> {sql_text(digest)};

WITH archivo AS (
  INSERT INTO "ArchivosImportados"("id", "nombre", "hash", "fecha_importacion", "fecha_actualizacion")
  SELECT COALESCE((SELECT max("id") FROM "ArchivosImportados"), 0) + 1,
         {sql_text(rel)}, {sql_text(digest)}, {sql_text(today)}, {sql_text(today)}
  WHERE NOT EXISTS (SELECT 1 FROM tmp_existing)
  ON CONFLICT ("hash") DO NOTHING
  RETURNING "id"
), jornada AS (
  INSERT INTO "Jornadas"("id", "id_archivo", "fecha", "caja_inicial", "comision_barberos", "retiro", "archivo_origen")
  SELECT COALESCE((SELECT max("id") FROM "Jornadas"), 0) + 1,
         archivo."id", {sql_text(jornada["fecha"])}, {jornada["caja_inicial"]}, {jornada["comision_barberos"]}, {jornada["retiro"] or "NULL"}, {sql_text(rel)}
  FROM archivo
  ON CONFLICT DO NOTHING
  RETURNING "id"
)
INSERT INTO tmp_target(id_jornada)
SELECT "id" FROM jornada;

WITH cortes_base AS (
  SELECT COALESCE(max("id"), 0) AS id FROM "Cortes"
), salidas_base AS (
  SELECT COALESCE(max("id"), 0) AS id FROM "SalidasCaja"
), ventas_base AS (
  SELECT COALESCE(max("id"), 0) AS id FROM "Ventas"
), adelantos_base AS (
  SELECT COALESCE(max("id"), 0) AS id FROM "Adelantos"
), ins_cortes AS (
  INSERT INTO "Cortes"("id", "id_barbero", "id_jornada", "hora", "importe", "propina", "mercadoPago", "fila_origen", "columna_origen")
  SELECT cortes_base.id + row_number() OVER (ORDER BY t.fila_origen, t.columna_origen),
         b."id", tmp_target.id_jornada, t.hora, t.importe, t.propina, t."mercadoPago", t.fila_origen, t.columna_origen
  FROM tmp_cortes t
  JOIN (SELECT lower("nombre") AS nombre, min("id") AS "id" FROM "Barberos" GROUP BY lower("nombre")) b ON b.nombre = lower(t.barbero)
  CROSS JOIN tmp_target
  CROSS JOIN cortes_base
), ins_salidas AS (
  INSERT INTO "SalidasCaja"("id", "id_jornada", "motivo", "importe", "mercadoPago", "fila_origen")
  SELECT salidas_base.id + row_number() OVER (ORDER BY t.fila_origen),
         tmp_target.id_jornada, t.motivo, t.importe, t."mercadoPago", t.fila_origen
  FROM tmp_salidas t
  CROSS JOIN tmp_target
  CROSS JOIN salidas_base
), ins_ventas AS (
  INSERT INTO "Ventas"("id", "id_jornada", "producto", "importe", "mercadoPago", "fila_origen")
  SELECT ventas_base.id + row_number() OVER (ORDER BY t.fila_origen),
         tmp_target.id_jornada, t.producto, t.importe, t."mercadoPago", t.fila_origen
  FROM tmp_ventas t
  CROSS JOIN tmp_target
  CROSS JOIN ventas_base
)
INSERT INTO "Adelantos"("id", "id_barbero", "id_jornada", "importe", "mercadoPago", "fila_origen")
SELECT adelantos_base.id + row_number() OVER (ORDER BY t.fila_origen),
       b."id", tmp_target.id_jornada, t.importe, t."mercadoPago", t.fila_origen
FROM tmp_adelantos t
JOIN (SELECT lower("nombre") AS nombre, min("id") AS "id" FROM "Barberos" GROUP BY lower("nombre")) b ON b.nombre = lower(t.barbero)
CROSS JOIN tmp_target
CROSS JOIN adelantos_base;
COMMIT;
SELECT {sql_text(rel)} || '|' || CASE
  WHEN NOT EXISTS (SELECT 1 FROM tmp_existing) THEN 'importado'
  WHEN EXISTS (SELECT 1 FROM tmp_existing WHERE "hash" <> {sql_text(digest)}) THEN 'actualizado'
  ELSE 'sin cambios'
END;
DROP TABLE tmp_barberos, tmp_cortes, tmp_salidas, tmp_ventas, tmp_adelantos, tmp_existing, tmp_target;
"""
    return sql, len(cortes), len(salidas), len(ventas), len(adelantos), invalidos


def main():
    if not FECHAS_DIR.exists():
        sys.exit("No existe la carpeta Fechas/")
    files = sorted(path for path in FECHAS_DIR.glob("*/*.xlsx") if not path.name.startswith("~$"))
    if not files:
        sys.exit("No encontre archivos .xlsx en Fechas/")

    totals = [0, 0, 0, 0, 0]
    scripts = []
    pending = []
    for path in files:
        sql, *counts = import_file(path)
        scripts.append(sql)
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        pending.append((rel, counts))
        totals = [a + b for a, b in zip(totals, counts)]

    statuses = {}
    for line in run_psql("\n".join(scripts)):
        if "|" in line:
            rel, status = line.split("|", 1)
            statuses[rel] = status

    for rel, counts in pending:
        status = statuses.get(rel, "sin estado")
        print(f"{status}: {rel} cortes={counts[0]} salidas={counts[1]} ventas={counts[2]} adelantos={counts[3]} invalidos={counts[4]}")
    print(f"Listo. Leidos cortes={totals[0]} salidas={totals[1]} ventas={totals[2]} adelantos={totals[3]} invalidos={totals[4]}.")


if __name__ == "__main__":
    main()
