# agentic-cdp

Pipeline ELT (Meltano + dbt) que extrai dados do CDP e os transforma em um
data warehouse local em DuckDB, usado para BI e agentes.

O fluxo é: **Meltano** extrai da API `ecomm-data` e do GA4 e carrega no schema
`raw` do DuckDB; **dbt** transforma `raw` em modelos `staging` (limpeza) e
`marts` (as tabelas consultadas por dashboards e agentes).

## Estrutura

- `meltano.yml` — configuração dos plugins e do job de extração/carga (EL).
- `docker-compose.yml` — quatro serviços: `meltano` (EL), `ga4-loader`
  (carga do comportamento de clientes do GA4), `dbt` (transformação) e
  `bq-export` (publica `marts.*` no BigQuery para o Looker Studio).
- `scripts/load_ga4_customer_behavior.py` — lê os arquivos de export do GA4
  (`../ga4_bigquery_export/events/*.json.gz`), filtra pelos clientes
  conhecidos, agrega por cliente e grava em `raw.ga4_customer_behavior`.
- `scripts/export_marts_to_bigquery.py` — copia cada tabela de `marts.*` do
  DuckDB para o BigQuery (load com `WRITE_TRUNCATE`, sem reprocessar SQL).
- `transform/` — projeto dbt (`dbt-duckdb`): modelos `staging` alimentam os
  modelos `marts`.
- `output/warehouse.duckdb` — arquivo DuckDB de destino (ignorado pelo git).

## Fontes → `raw` → marts

| Fonte (ecomm-data / GA4)            | Tabela `raw`             | Modelos staging                                                           | Modelos marts |
|-------------------------------------|--------------------------|---------------------------------------------------------------------------|---------------|
| `GET /categories`                   | `raw.categories`         | `stg_categories`                                                          | `dim_categories` |
| `GET /promotions`                   | `raw.promotions`         | `stg_promotions`                                                          | `dim_promotions` |
| `GET /affiliates`                   | `raw.affiliates`         | `stg_affiliates`                                                          | `dim_affiliates` |
| `GET /products?page=N`              | `raw.products`           | `stg_products`                                                            | `dim_products`, `dim_brands` |
| `GET /profiles?page=N`              | `raw.cdp_customer_profiles` | `stg_cdp_customer_profiles`                                            | `dim_customers` |
| `GET /orders?page=N`                | `raw.orders`             | `stg_customer_orders`, `stg_customer_order_items`, `stg_customer_refunds` | `fct_customer_orders`, `fct_order_line`, `dim_order_status`, `dim_channel`, `dim_payment_methods`, `dim_date` |
| GA4 (arquivos locais, agregado)     | `raw.ga4_customer_behavior` | `stg_ga4_customer_behavior`                                            | alimenta campos de GA4 em `dim_customers` |

## Setup

```bash
# uma vez: rede compartilhada para o container alcançar o ecomm-data
docker network create cdp-shared-net

cp .env.example .env          # ajuste ECOMM_DATA_API_URL etc.
docker compose run --rm meltano lock --update --all   # fixa as definições em plugins/
docker compose run --rm meltano install
```

Suba também o `ecomm-data` na mesma rede (ver README do projeto):

```bash
(cd ../ecomm-data && docker compose up --build -d)
```

## Executar o pipeline

```bash
docker compose run --rm meltano run el_ecomm_data   # ecomm-data -> raw
docker compose run --rm ga4-loader                  # GA4 -> raw.ga4_customer_behavior
docker compose run --rm dbt                          # dbt build: staging + marts + testes
```

`docker compose run --rm dbt` executa `dbt build` (comando padrão). Outros
subcomandos também funcionam, por exemplo gerar a documentação:

```bash
docker compose run --rm dbt docs generate
python3 -m http.server --directory transform/target 8080   # abrir http://localhost:8080
```

## Inspecionar o resultado

```bash
docker compose run --rm dbt show --inline "select * from marts.dim_customers limit 5"
```

(ou abra `output/warehouse.duckdb` em qualquer cliente DuckDB.)

## Exportar marts para o Looker Studio (BigQuery)

O warehouse é um arquivo DuckDB local, que o Looker Studio não lê
diretamente. `bq-export` publica as tabelas já materializadas em `marts.*`
(sem reprocessar SQL) num dataset do BigQuery, que o Looker Studio consome
pelo conector nativo do BigQuery.

Setup (uma vez):

1. Crie (ou reaproveite) um projeto no GCP e um dataset no BigQuery — o
   dataset é criado automaticamente pelo script se não existir.
2. Crie uma service account com os papéis **BigQuery Data Editor** e
   **BigQuery Job User**, gere uma chave JSON e salve em
   `./secrets/service-account.json` (pasta ignorada pelo git).
3. Em `.env`, defina `GCP_PROJECT` (e opcionalmente `BQ_DATASET`, padrão
   `agentic_cdp`).

Rodar depois de todo `dbt build`:

```bash
docker compose run --rm bq-export
```

No Looker Studio: **Criar fonte de dados → BigQuery → escolha o projeto,
dataset e tabela** (uma fonte por tabela de `marts`, ou combine via *blend*).
Para manter os dashboards atualizados, agende `dbt build` seguido de
`bq-export` (ex.: cron ou orquestrador).

## Adicionar um endpoint do ecomm-data

Adicione uma entrada em `extractors.tap-rest-api-msdk.config.streams` no
`meltano.yml`: `name` (nome do stream/tabela), `path` (concatenado à
`api_url`), `records_path` (JSONPath para o array de registros) e,
opcionalmente, `primary_keys`.

## Adicionar um modelo

- **Staging**: crie um `.sql` em `transform/models/staging/` fazendo
  `select` de `{{ source('raw', '<tabela>') }}` (declarada em
  `sources.yml`). Mantém-se `ephemeral` por padrão.
- **Marts**: crie um `.sql` em `transform/models/marts/` a partir de
  `{{ ref('stg_...') }}` e adicione descrição e testes no `schema.yml` da
  pasta — todo modelo deve ter ao menos `not_null` + `unique` na chave
  primária.

## Licença

Distribuído sob a licença [MIT](LICENSE).
