with parsed as (
    select
        orderid as order_id,
        clientid as customer_id,
        try_cast(authorizeddate as timestamp) as purchased_at,
        cast(items as struct(
            itemId varchar, itemName varchar, brand varchar, category varchar,
            variant varchar, quantity bigint, price double
        )[]) as items
    from {{ source('raw', 'orders') }}
)
select
    customer_id,
    order_id,
    purchased_at,
    i.itemId as item_id,
    i.itemName as item_name,
    i.brand,
    i.category,
    i.variant,
    i.quantity,
    i.price
from parsed
cross join unnest(items) as t(i)
