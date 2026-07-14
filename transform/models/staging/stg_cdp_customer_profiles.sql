with parsed as (
    select
        identity_cdpid as customer_id,
        identity_userpseudoid as user_pseudo_id,
        identity_documentid as document_id,
        identity_documenttype as document_type,
        identity_firstname as first_name,
        identity_lastname as last_name,
        descriptive_gender as gender,
        try_cast(descriptive_birthdate as date) as birth_date,
        descriptive_languagepreference as language_preference,
        descriptive_communicationpreferences_emailoptin as email_opt_in,
        descriptive_communicationpreferences_smsoptin as sms_opt_in,
        descriptive_communicationpreferences_pushoptin as push_opt_in,
        descriptive_communicationpreferences_whatsappoptin as whatsapp_opt_in,
        cast(identity_emails as struct(address varchar, isPrimary boolean, verified boolean)[]) as emails,
        cast(identity_phones as struct(number varchar, type varchar, verified boolean)[]) as phones
    from {{ source('raw', 'cdp_customer_profiles') }}
)
select
    customer_id,
    user_pseudo_id,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    document_id,
    document_type,
    gender,
    birth_date,
    date_diff('year', birth_date, current_date) as age,
    language_preference,
    email_opt_in,
    sms_opt_in,
    push_opt_in,
    whatsapp_opt_in,
    coalesce(
        list_filter(emails, x -> x.isPrimary)[1].address,
        emails[1].address
    ) as primary_email,
    coalesce(
        list_filter(emails, x -> x.isPrimary)[1].verified,
        emails[1].verified,
        false
    ) as email_verified,
    len(list_filter(phones, x -> x.verified)) > 0 as has_verified_phone
from parsed
