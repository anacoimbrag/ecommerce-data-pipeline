select
    id as affiliate_id,
    name as affiliate_name,
    followupemail as follow_up_email,
    storehandle as store_handle,
    comission as commission_rate
from {{ source('raw', 'affiliates') }}
