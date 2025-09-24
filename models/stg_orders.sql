-- Select from the seeded table (which dbt will create as LEARN_DB.PUBLIC.raw_orders)
select
  cast(order_id as number)      as order_id,
  cast(customer_id as number)   as customer_id,
  to_date(order_date)           as order_date,
  status,
  cast(amount as number(10,2))  as amount
from {{ ref('raw_orders') }}
