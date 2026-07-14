select distinct
    brand_id,
    brand as brand_name
from {{ ref('stg_products') }}
