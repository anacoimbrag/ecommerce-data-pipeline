select
    o.customer_id,
    o.order_id,
    -- coupon é a referência de promoção do pedido (dim_promotions.promotion_id).
    o.coupon as promotion_id,
    o.purchased_at,
    cast(o.purchased_at as date) as order_date,
    o.revenue,
    o.shipping_value,
    o.tax_value,
    o.payment_type as payment_method_id,
    o.order_status_id,
    o.channel_id,
    o.affiliate_id
from {{ ref('stg_customer_orders') }} o
