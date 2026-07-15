# Metabase + driver DuckDB (motherduckdb/metabase_duckdb_driver), para ler
# output/warehouse.duckdb diretamente, sem exportar para o BigQuery.
#
# A imagem oficial metabase/metabase é Alpine (musl) e o plugin DuckDB não
# funciona nela por problemas de glibc (ver README do driver). Este Dockerfile
# é o mesmo publicado em
# https://github.com/motherduckdb/metabase_duckdb_driver/blob/main/Dockerfile,
# baseado em Debian (eclipse-temurin jammy), onde o driver funciona.

FROM eclipse-temurin:21-jre-jammy

ARG METABASE_VERSION=0.62.5
ARG METABASE_DUCKDB_DRIVER_VERSION=1.5.4.0

ENV MB_PLUGINS_DIR=/home/metabase/plugins/

RUN groupadd -r metabase && useradd -r -g metabase metabase

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/metabase/plugins /home/metabase/data && \
    chown -R metabase:metabase /home/metabase

WORKDIR /home/metabase
ADD --chown=metabase:metabase https://downloads.metabase.com/v${METABASE_VERSION}/metabase.jar /home/metabase/
ADD --chown=metabase:metabase https://github.com/motherduckdb/metabase_duckdb_driver/releases/download/${METABASE_DUCKDB_DRIVER_VERSION}/duckdb.metabase-driver.jar /home/metabase/plugins/

RUN chmod 755 /home/metabase/metabase.jar && \
    chmod 755 /home/metabase/plugins/duckdb.metabase-driver.jar

EXPOSE 3000

USER metabase

CMD ["java", "-jar", "/home/metabase/metabase.jar"]
