select
    sku ->> 'itemId' as sku_id,
    sku ->> 'nameComplete' as sku_name,
    sku ->> 'ean' as ean,
    p.product_id,
    p.product_name,
    p.product_reference,
    p.description,
    p.brand,
    p.brand_id,
    p.link,
    p.category_id,
    p.list_price_low,
    p.list_price_high,
    p.selling_price_low,
    p.selling_price_high,
    p.category_paths_json,
    p.category_ids_json,
    p.product_clusters_json,
    p.properties_json
from {{ ref('stg_products') }} p
cross join unnest(json_extract(p.bundle_items_json, '$[*]')) as t(sku)
