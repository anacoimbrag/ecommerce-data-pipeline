with profiles as (
    select * from {{ ref('stg_cdp_customer_profiles') }}
),

order_agg as (
    select
        customer_id,
        count(*) as total_orders,
        sum(revenue) as total_revenue,
        avg(revenue) as avg_order_value,
        min(purchased_at) as first_purchase_at,
        max(purchased_at) as last_purchase_at
    from {{ ref('stg_customer_orders') }}
    group by 1
),

refund_agg as (
    select
        customer_id,
        count(*) as total_refunds,
        sum(refund_value) as total_refund_value
    from {{ ref('stg_customer_refunds') }}
    group by 1
),

category_totals as (
    select customer_id, category, sum(quantity) as qty
    from {{ ref('stg_customer_order_items') }}
    group by 1, 2
),
favorite_category as (
    select customer_id, category as favorite_category
    from (
        select customer_id, category,
               row_number() over (partition by customer_id order by qty desc, category) as rn
        from category_totals
    )
    where rn = 1
),

brand_totals as (
    select customer_id, brand, sum(quantity) as qty
    from {{ ref('stg_customer_order_items') }}
    group by 1, 2
),
favorite_brand as (
    select customer_id, brand as favorite_brand
    from (
        select customer_id, brand,
               row_number() over (partition by customer_id order by qty desc, brand) as rn
        from brand_totals
    )
    where rn = 1
),

-- Comportamento e localização do GA4, unidos por user_pseudo_id.
behavior as (
    select * from {{ ref('stg_ga4_customer_behavior') }}
)

select
    p.customer_id,
    p.user_pseudo_id,
    p.first_name,
    p.last_name,
    p.full_name,
    p.document_id,
    p.document_type,
    p.gender,
    p.birth_date,
    p.age,
    p.language_preference,
    p.email_opt_in,
    p.sms_opt_in,
    p.push_opt_in,
    p.whatsapp_opt_in,
    p.primary_email,
    p.email_verified,
    p.has_verified_phone,
    b.location_country,
    b.location_region,
    b.location_city,
    b.preferred_device_category,
    b.viewed_top_category,
    b.viewed_top_brand,
    b.total_events as ga4_total_events,
    b.distinct_days_active as ga4_distinct_days_active,
    b.ga4_first_seen_at,
    b.ga4_last_seen_at,
    coalesce(oa.total_orders, 0) as total_orders,
    coalesce(oa.total_revenue, 0) as total_revenue,
    oa.avg_order_value,
    oa.first_purchase_at,
    oa.last_purchase_at,
    date_diff('day', oa.last_purchase_at, current_timestamp) as recency_days,
    coalesce(ra.total_refunds, 0) as total_refunds,
    coalesce(ra.total_refund_value, 0) as total_refund_value,
    coalesce(oa.total_revenue, 0) - coalesce(ra.total_refund_value, 0) as net_revenue,
    fc.favorite_category,
    fb.favorite_brand
from profiles p
left join behavior b on p.user_pseudo_id = b.user_pseudo_id
left join order_agg oa on p.customer_id = oa.customer_id
left join refund_agg ra on p.customer_id = ra.customer_id
left join favorite_category fc on p.customer_id = fc.customer_id
left join favorite_brand fb on p.customer_id = fb.customer_id
