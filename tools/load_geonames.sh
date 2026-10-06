#!/usr/bin/env bash
# Загрузка полной выгрузки GeoNames по России (CC BY 4.0) в БД jyotisha (схема geo).
# Источник: https://download.geonames.org/export/dump/  (RU.zip + admin1CodesASCII.txt + admin2Codes.txt)
# Данные в git НЕ хранятся (объём). Запуск однократно/при обновлении.
#   DB_CONTAINER=jyotisha_db bash calc_engine/tools/load_geonames.sh
set -euo pipefail
DB="${DB_CONTAINER:-jyotisha_db}"
U="${POSTGRES_USER:-jyotisha}"; D="${POSTGRES_DB:-jyotisha}"
TMP=$(mktemp -d); cd "$TMP"
DL="https://download.geonames.org/export/dump"
for f in RU.zip admin1CodesASCII.txt admin2Codes.txt; do
  curl -fsSL "$DL/$f" -o "$f"
done
unzip -o RU.zip >/dev/null

docker exec "$DB" psql -U "$U" -d "$D" -c "CREATE SCHEMA IF NOT EXISTS geo;" \
  -c "DROP TABLE IF EXISTS geo.geonames_raw,geo.admin1_raw,geo.admin2_raw CASCADE;" \
  -c "CREATE TABLE geo.geonames_raw(geonameid text,name text,asciiname text,alternatenames text,lat text,lon text,fclass text,fcode text,country text,cc2 text,admin1 text,admin2 text,admin3 text,admin4 text,population text,elevation text,dem text,timezone text,moddate text);" \
  -c "CREATE TABLE geo.admin1_raw(code text,name text,ascii text,gid text);" \
  -c "CREATE TABLE geo.admin2_raw(code text,name text,ascii text,gid text);"
docker exec -i "$DB" psql -U "$U" -d "$D" -c "\copy geo.geonames_raw FROM STDIN WITH (FORMAT text,DELIMITER E'\t',NULL '')" < RU.txt
docker exec -i "$DB" psql -U "$U" -d "$D" -c "\copy geo.admin1_raw FROM STDIN WITH (FORMAT text,DELIMITER E'\t',NULL '')" < admin1CodesASCII.txt
docker exec -i "$DB" psql -U "$U" -d "$D" -c "\copy geo.admin2_raw FROM STDIN WITH (FORMAT text,DELIMITER E'\t',NULL '')" < admin2Codes.txt

# типизированные места (РФ, населённые пункты) + индекс имён
docker exec "$DB" psql -U "$U" -d "$D" -c "
DROP TABLE IF EXISTS geo.places CASCADE;
CREATE TABLE geo.places AS
SELECT g.geonameid::bigint id,g.name,g.asciiname,g.alternatenames,
  g.lat::double precision lat,g.lon::double precision lon,g.fcode,
  NULLIF(g.population,'')::bigint population,g.timezone tz,a1.name region,a2.name district
FROM geo.geonames_raw g
LEFT JOIN geo.admin1_raw a1 ON a1.code='RU.'||g.admin1
LEFT JOIN geo.admin2_raw a2 ON a2.code='RU.'||g.admin1||'.'||g.admin2
WHERE g.country='RU' AND g.fclass='P';
ALTER TABLE geo.places ADD PRIMARY KEY(id);
CREATE TABLE geo.place_names AS
SELECT id, lower(trim(nm)) name_lower FROM geo.places,
  LATERAL unnest(string_to_array(name||','||coalesce(asciiname,'')||','||coalesce(alternatenames,''),',')) nm
WHERE trim(nm)<>'';
CREATE INDEX idx_place_names_lower ON geo.place_names(name_lower);
CREATE INDEX idx_places_pop ON geo.places(population DESC NULLS LAST);"
# русские названия регионов — из отдельного файла проекта
docker exec -i "$DB" psql -U "$U" -d "$D" < "$(dirname "$0")/regions_ru.sql"
echo "GeoNames RU загружен."
rm -rf "$TMP"
