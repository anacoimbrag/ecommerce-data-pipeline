-- Calendário limitado ao intervalo de datas de pedidos observado nos dados.
with bounds as (
    select
        cast(min(purchased_at) as date) as min_date,
        cast(max(purchased_at) as date) as max_date
    from {{ ref('stg_customer_orders') }}
)
select
    cast(date_day as date) as order_date,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    monthname(date_day) as month_name,
    extract(day from date_day) as day_of_month,
    isodow(date_day) as day_of_week,
    dayname(date_day) as day_name,
    extract(week from date_day) as week_of_year,
    isodow(date_day) in (6, 7) as is_weekend
from bounds, generate_series(bounds.min_date, bounds.max_date, interval 1 day) as t(date_day)
