# PostGIS with init script baked in (avoids bind-mount issues on Docker Desktop / Windows WSL)
FROM postgis/postgis:16-3.4
COPY docker/init.sql /docker-entrypoint-initdb.d/init.sql
