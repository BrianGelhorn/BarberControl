CREATE TABLE "Cortes"(
    "id" INTEGER NOT NULL,
    "id_barbero" INTEGER NOT NULL,
    "id_jornada" INTEGER NOT NULL,
    "hora" TIME(0) WITHOUT TIME ZONE NULL,
    "importe" DECIMAL(8, 2) NOT NULL,
    "propina" DECIMAL(8, 2) NULL,
    "mercadoPago" BOOLEAN NOT NULL,
    "fila_origen" INTEGER NOT NULL,
    "columna_origen" TEXT NOT NULL
);
ALTER TABLE
    "Cortes" ADD PRIMARY KEY("id");
CREATE TABLE "Barberos"(
    "id" INTEGER NOT NULL,
    "nombre" TEXT NOT NULL
);
ALTER TABLE
    "Barberos" ADD PRIMARY KEY("id");
CREATE TABLE "SalidasCaja"(
    "id" INTEGER NOT NULL,
    "id_jornada" INTEGER NOT NULL,
    "motivo" TEXT NULL,
    "importe" DECIMAL(8, 2) NOT NULL,
    "mercadoPago" BOOLEAN NOT NULL,
    "fila_origen" INTEGER NOT NULL
);
ALTER TABLE
    "SalidasCaja" ADD PRIMARY KEY("id");
CREATE TABLE "Ventas"(
    "id" INTEGER NOT NULL,
    "id_jornada" INTEGER NOT NULL,
    "producto" TEXT NOT NULL,
    "importe" DECIMAL(8, 2) NOT NULL,
    "mercadoPago" BOOLEAN NOT NULL,
    "fila_origen" INTEGER NOT NULL
);
ALTER TABLE
    "Ventas" ADD PRIMARY KEY("id");
CREATE TABLE "Adelantos"(
    "id" INTEGER NOT NULL,
    "id_barbero" INTEGER NOT NULL,
    "id_jornada" INTEGER NOT NULL,
    "importe" DECIMAL(8, 2) NULL,
    "mercadoPago" BOOLEAN NOT NULL,
    "fila_origen" INTEGER NOT NULL
);
ALTER TABLE
    "Adelantos" ADD PRIMARY KEY("id");
CREATE TABLE "Jornadas"(
    "id" INTEGER NOT NULL,
    "id_archivo" INTEGER NOT NULL,
    "fecha" DATE NOT NULL,
    "caja_inicial" DECIMAL(8, 2) NOT NULL,
    "comision_barberos" DECIMAL(8, 2) NOT NULL,
    "retiro" INTEGER NULL,
    "archivo_origen" TEXT NOT NULL
);
ALTER TABLE
    "Jornadas" ADD PRIMARY KEY("id");
ALTER TABLE
    "Jornadas" ADD CONSTRAINT "jornadas_fecha_unique" UNIQUE("fecha");
ALTER TABLE
    "Jornadas" ADD CONSTRAINT "jornadas_archivo_origen_unique" UNIQUE("archivo_origen");
CREATE TABLE "ArchivosImportados"(
    "id" INTEGER NOT NULL,
    "nombre" TEXT NOT NULL,
    "hash" TEXT NOT NULL,
    "fecha_importacion" DATE NOT NULL,
    "fecha_actualizacion" DATE NOT NULL
);
ALTER TABLE
    "ArchivosImportados" ADD PRIMARY KEY("id");
ALTER TABLE
    "ArchivosImportados" ADD CONSTRAINT "archivosimportados_hash_unique" UNIQUE("hash");
ALTER TABLE
    "Ventas" ADD CONSTRAINT "ventas_id_jornada_foreign" FOREIGN KEY("id_jornada") REFERENCES "Jornadas"("id");
ALTER TABLE
    "Adelantos" ADD CONSTRAINT "adelantos_id_jornada_foreign" FOREIGN KEY("id_jornada") REFERENCES "Jornadas"("id");
ALTER TABLE
    "Adelantos" ADD CONSTRAINT "adelantos_id_barbero_foreign" FOREIGN KEY("id_barbero") REFERENCES "Barberos"("id");
ALTER TABLE
    "SalidasCaja" ADD CONSTRAINT "salidascaja_id_jornada_foreign" FOREIGN KEY("id_jornada") REFERENCES "Jornadas"("id");
ALTER TABLE
    "Cortes" ADD CONSTRAINT "cortes_id_jornada_foreign" FOREIGN KEY("id_jornada") REFERENCES "Jornadas"("id");
ALTER TABLE
    "Jornadas" ADD CONSTRAINT "jornadas_id_archivo_foreign" FOREIGN KEY("id_archivo") REFERENCES "ArchivosImportados"("id");
ALTER TABLE
    "Cortes" ADD CONSTRAINT "cortes_id_barbero_foreign" FOREIGN KEY("id_barbero") REFERENCES "Barberos"("id");
