-- Achata a árvore de categorias (3 níveis: raiz -> grupo -> folha) em um
-- registro por nó, em qualquer nível.
with roots as (
    select
        id as root_id,
        name as root_name,
        cast(children as struct(
            id integer, name varchar, "hasChildren" boolean,
            children struct(id integer, name varchar, "hasChildren" boolean)[]
        )[]) as mids
    from {{ source('raw', 'categories') }}
),

flattened as (
    select root_id as category_id, root_name as category_name, cast(null as integer) as parent_category_id, 1 as level
    from roots

    union all

    select m.id as category_id, m.name as category_name, root_id as parent_category_id, 2 as level
    from roots
    cross join unnest(mids) as t(m)

    union all

    select l.id as category_id, l.name as category_name, m.id as parent_category_id, 3 as level
    from roots
    cross join unnest(mids) as t(m)
    cross join unnest(m.children) as t2(l)
)

select
    category_id,
    category_name,
    parent_category_id,
    level
from flattened
