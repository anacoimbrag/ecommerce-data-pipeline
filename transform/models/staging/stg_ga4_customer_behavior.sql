-- Passthrough de raw.ga4_customer_behavior, já agregado por
-- scripts/load_ga4_customer_behavior.py.
select
    user_pseudo_id,
    total_events,
    distinct_days_active,
    ga4_first_seen_at,
    ga4_last_seen_at,
    location_country,
    location_region,
    location_city,
    preferred_device_category,
    viewed_top_category,
    viewed_top_brand
from {{ source('raw', 'ga4_customer_behavior') }}
