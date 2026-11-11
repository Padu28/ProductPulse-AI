# Data dictionary

Two parts: the source fields used from the GA4 export, and the tables this project derives from them.

The "Observed" columns hold values measured on the live dataset on 2026-11-11 (export run `scripts/export_from_bigquery.py`, tables in `data/exports/`). Where this document says "expected", it describes the standard GA4 export schema.

Size of the sample: 4,295,584 event rows, 270,154 users, 360,129 sessions, 17 distinct event names, 92 days with data.

Reporting period: 2020-11-01 to 2021-01-31. Source: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`.

## Part 1. Source fields

### Core event fields

| Field | Type (expected) | Meaning | Handling in this project | Observed (query) |
|---|---|---|---|---|
| `event_date` | STRING `YYYYMMDD` | Date the event was logged, in the property's reporting time zone | Parsed to DATE as `event_dt` with `PARSE_DATE('%Y%m%d', ...)` | 2020-11-01 / 2021-01-31 / 92 days, none missing (Q01) |
| `event_timestamp` | INT64, microseconds since epoch, UTC | Time the event was logged | Used for ordering events; `event_ts` = `TIMESTAMP_MICROS(...)` | Null count: 0; rows where the UTC date differs from `event_date`: 0 (Q10) |
| `event_name` | STRING | Name of the event | Mapped to funnel stages (table below) | 17 distinct names (Q02) |
| `user_pseudo_id` | STRING | Pseudonymous id for a browser / app instance. Not a person | Rows with NULL are excluded from every user and session metric. Suitable for distinct-user analysis with the caveat that one person can have several ids | Null rows: 0 of 4,295,584 (Q07) |

In a standard GA4 export `event_date` is in the property's time zone and `event_timestamp` is UTC, so some events near midnight would fall on different dates. In this sample the check found 0 such rows: the two fields agree for every event. This project uses `event_date` for all daily grouping and `event_timestamp` only for ordering.

### Funnel stage mapping

| `event_name` | Stage | Flag column | Caution |
|---|---|---|---|
| `session_start` | (session began) | n/a | Do not count events to count sessions; use user + `ga_session_id` |
| `page_view` | (browsing) | n/a | One user generates many |
| `view_item` | 1. View item | `viewed_item` | Item details are in the `items` array |
| `add_to_cart` | 2. Add to cart | `added_cart` | Users, sessions and events are three different counts |
| `begin_checkout` | 3. Begin checkout | `began_checkout` | A user may trigger it more than once |
| `purchase` | 4. Purchase | `purchased` | An order is a distinct valid `transaction_id`, not a purchase event |

Event rows and users per event (Q02, all 17 events):

| event_name | event_rows | users |
|---|---|---|
| `page_view` | 1,350,428 | 269,792 |
| `user_engagement` | 1,058,721 | 213,004 |
| `scroll` | 493,072 | 138,098 |
| `view_item` | 386,068 | 61,252 |
| `session_start` | 354,970 | 267,116 |
| `first_visit` | 257,462 | 257,314 |
| `view_promotion` | 190,104 | 102,443 |
| `add_to_cart` | 58,543 | 12,545 |
| `begin_checkout` | 38,757 | 9,715 |
| `select_item` | 31,007 | 13,180 |
| `view_search_results` | 26,172 | 14,449 |
| `add_shipping_info` | 19,722 | 9,714 |
| `add_payment_info` | 13,899 | 5,751 |
| `select_promotion` | 9,450 | 8,164 |
| `purchase` | 5,692 | 4,419 |
| `click` | 1,446 | 1,010 |
| `view_item_list` | 71 | 44 |

Notes: `session_start` has 354,970 rows but there are 360,129 sessions, which is why sessions are counted from user + `ga_session_id` and not from this event. `add_shipping_info` and `add_payment_info` exist as intermediate checkout steps; they are not used as funnel stages in this project.

### `event_params` (repeated key / value)

Each event carries an array of parameters. A value sits in exactly one of `string_value`, `int_value`, `float_value`, `double_value`.

| Key used | Value type (expected) | Extracted as | Why |
|---|---|---|---|
| `ga_session_id` | `int_value` | `ga_session_id` | Session key, together with `user_pseudo_id` |
| `ga_session_number` | `int_value` | `ga_session_number` | 1 = first session for that id |
| `engagement_time_msec` | `int_value` | `engagement_time_msec` | Engagement time |
| `page_location` | `string_value` | `page_location` | Page URL |
| `page_title` | `string_value` | `page_title` | Page title |

Extraction rule: a scalar sub-query, one per key, for example
`(SELECT ep.value.int_value FROM UNNEST(event_params) ep WHERE ep.key = 'ga_session_id')`.
This returns one value per event and cannot multiply rows. A `CROSS JOIN UNNEST(event_params)` returns one row per parameter and is used only in Q03 to list the keys.

Observed (Q03): 34 distinct keys. The five keys used here have the expected types on every occurrence:

| Key | Occurrences | Value type observed |
|---|---|---|
| `ga_session_id` | 4,295,584 (every event) | `int_value` only |
| `ga_session_number` | 4,295,584 (every event) | `int_value` only |
| `page_location` | 4,295,584 (every event) | `string_value` only |
| `page_title` | 4,276,104 | `string_value` (1,468 with no value) |
| `engagement_time_msec` | 2,431,818 | `int_value` only; absent on the other events, treated as 0 |

Keys with mixed or awkward types, not used by this project but worth knowing: `session_engaged` (3,682,921 string and 313,391 integer values), `transaction_id` (4,786 string, 456 integer), `value` and `tax` (integer on some events, double on others). The keys `source`, `medium` and `campaign` are present on about 1.43 million events, so session-level traffic source could be built from them in future work.

### `device`, `geo`, `traffic_source`

| Field | Derived column | Values (expected) | Handling | Observed (Q05) |
|---|---|---|---|---|
| `device.category` | `device_category` | `desktop`, `mobile`, `tablet` | NULL shown as `(not set)`. Per user: the device of the first observed event | Users: desktop 156,905; mobile 107,175; tablet 6,074. No NULL rows. 4,182 users (1.55%) were seen on more than one device category |
| `geo.country` | `country` | Country names, `(not set)` | Empty or NULL shown as `(not set)`. Per user: first observed country | Top: United States 118,493 users; India 25,367; Canada 20,268; United Kingdom 8,527. `(not set)`: 2,168 users (0.80%), 32,208 event rows |
| `traffic_source.source` | `first_user_source` | e.g. `google`, `(direct)`, `<Other>`, `(data deleted)` | Kept as is | Users: `google` 107,324; `<Other>` 81,109; `(direct)` 64,109; `shop.googlemerchandisestore.com` 14,763; `(data deleted)` 2,849 |
| `traffic_source.medium` | `first_user_medium` | e.g. `organic`, `(none)`, `referral`, `cpc`, `<Other>` | Kept as is | Users: `organic` 101,742; `(none)` 64,109; `<Other>` 47,101; `referral` 40,020; `cpc` 14,282; `(data deleted)` 2,900 |

**Attribution caveat.** `traffic_source` in the GA4 export is the source that *first acquired the user*. It is a user-level, first-touch field and stays the same on every later event. It is not the source of each session. All channel comparisons in this project are therefore first-touch comparisons.

`channel_group` is derived in `events_base`:

| Rule (first match wins) | `channel_group` |
|---|---|
| source or medium = `(data deleted)` | Data deleted |
| source = `(direct)` and medium in `(none)`, `(not set)` | Direct |
| medium = `organic` | Organic search |
| medium in `cpc`, `ppc`, `paid` | Paid search |
| medium = `referral` | Referral |
| source and medium both NULL | Unknown |
| anything else (including `<Other>`) | Other |

"Other" and "Data deleted" are artefacts of the dataset's obfuscation, not real channels. Their share is reported wherever channels are compared.

Observed users per `channel_group`: Organic search 101,742 (37.7%); Direct 64,109 (23.7%); Other 47,101 (17.4%); Referral 40,019 (14.8%); Paid search 14,282 (5.3%); Data deleted 2,901 (1.1%). Unknown: 0.

### `items` (repeated ecommerce structure)

| Field | Use | Caution |
|---|---|---|
| `items.item_name`, `item_id`, `item_category` | Product and category analysis | `(not set)` and NULL names are excluded from product tables |
| `items.quantity` | Units purchased (purchase events only) | NULL on non-purchase events |
| `items.price_in_usd`, `item_revenue_in_usd` | Item revenue (purchase events only) | Approximate if an order has repeated purchase events |

**Row multiplication.** `UNNEST(items)` turns one event into one row per item. It is isolated in the `items_base` view. User counts there use `COUNT(DISTINCT user_pseudo_id)` and order counts use `COUNT(DISTINCT transaction_id)`. Headline revenue never comes from the item level. Fan-out per event type: run Q12 in the BigQuery console and record the average items per event here.

### Purchase revenue

| Aspect | Decision | Observed (Q11) |
|---|---|---|
| Source field | `ecommerce.purchase_revenue_in_usd` on `purchase` events | 5,692 purchase events from 4,419 users |
| Currency | USD | Median order $48.00, mean $69.24, largest $1,530.00 |
| Validated order | DISTINCT `ecommerce.transaction_id`, not NULL and not `(not set)` | Validated orders: 4,451 |
| Excluded purchases | NULL or `(not set)` transaction id | 906 of 5,692 purchase events (15.9%) |
| Aggregation | `MAX(purchase_revenue_in_usd)` per transaction, then SUM. Counts each order once | 326 orders (7.3%) had more than one purchase event; 15 had conflicting revenue values; 15 were shared by more than one user id |
| Null revenue | Treated as 0 | 0 purchase events with NULL revenue; 0 validated orders with zero revenue |
| Check | Summed over every event vs de-duplicated | $362,165 vs $308,200. The $53,965 difference is repeated events plus purchases without a usable transaction id |

## Part 2. Derived tables

### View `events_base` (one row per event)

`event_dt`, `event_timestamp`, `event_ts`, `event_name`, `user_pseudo_id`, `ga_session_id`, `ga_session_number`, `engagement_time_msec`, `page_location`, `page_title`, `device_category`, `operating_system`, `browser`, `country`, `first_user_source`, `first_user_medium`, `first_user_campaign`, `channel_group`, `transaction_id`, `purchase_revenue_usd`, `total_item_quantity`.

### View `sessions_base` (one row per user + session)

Session key = `user_pseudo_id` + `ga_session_id`. `ga_session_id` alone is not unique across users.

### View `items_base` (one row per event x item)

Funnel events only. Item-level grain: re-aggregate before counting users, orders or revenue.

### Export `dim_user` (one row per user)

| Column | Type | Definition |
|---|---|---|
| `user_pseudo_id` | text | Primary key |
| `first_seen_dt` | date | First event date in the sample. Not necessarily the first-ever visit |
| `last_seen_dt` | date | Last event date in the sample |
| `cohort_month` | date | First day of the month of `first_seen_dt` |
| `device_category` | text | Device of the first observed event |
| `country` | text | Country of the first observed event |
| `first_user_source`, `first_user_medium` | text | GA4 user-level first-touch source and medium |
| `channel_group` | text | Derived grouping (rules above) |
| `n_devices` | integer | Distinct device categories seen for this id |

### Export `fact_user_day` (one row per user per active day)

| Column | Type | Definition |
|---|---|---|
| `user_pseudo_id` | text | Foreign key to `dim_user` |
| `event_dt` | date | Activity date |
| `events` | integer | Event rows that day |
| `sessions` | integer | Distinct `ga_session_id` that day. A session crossing midnight counts on both days |
| `page_views` | integer | `page_view` events |
| `engagement_sec` | decimal | Sum of `engagement_time_msec` / 1000 |
| `viewed_item`, `added_cart`, `began_checkout`, `purchased` | 0 / 1 | 1 if the event occurred at least once that day |
| `transactions` | integer | Validated orders whose first purchase event was on that day |
| `revenue_usd` | decimal | Revenue of those orders, each counted once |

Why this grain: distinct users can be recounted correctly under any filter (date, device, country, channel), which a pre-aggregated daily table cannot do.

### Other exports

| Table | Columns |
|---|---|
| `daily_metrics` | `event_dt`, `total_events`, `active_users`, `sessions`, `purchasers`, `transactions`, `revenue_usd` |
| `user_funnel_by_device` | `device_category`, `users`, `users_viewed`, `users_added_cart`, `users_began_checkout`, `users_purchased` |
| `session_funnel` | `device_category`, `channel_group`, `sessions`, `seq_view`, `seq_cart`, `seq_checkout`, `seq_purchase`, `any_purchase` |
| `cohort_retention_monthly` | `cohort_month`, `month_number`, `active_users`, `cohort_users`, `retention_rate` |
| `product_performance` | `item_name`, `item_category`, `users_viewed`, `users_added_cart`, `users_purchased`, `orders`, `units_purchased`, `item_revenue_usd` |
| `transactions` | `transaction_id`, `purchase_dt`, `device_category`, `purchase_events`, `distinct_users`, `revenue_usd`, `min_revenue_usd`, `total_item_quantity` |
| `data_quality` | `check_name`, `value`, `note` |

## Part 3. Data quality decisions

| Issue | Decision | Effect | Observed count (notebook 02) |
|---|---|---|---|
| NULL `user_pseudo_id` | Exclude from user and session metrics | Consistent distinct-user denominators | 0 rows |
| NULL `ga_session_id` | Exclude from session metrics only | Session funnel covers slightly fewer events | 0 rows |
| Same-microsecond duplicate events | Keep; report the count | No effect on DISTINCT user / session metrics | 0 extra copies |
| Purchase without a usable transaction id | Not a validated order | Orders and revenue slightly conservative | 906 of 5,692 purchase events |
| Repeated purchase events for one order | Order and revenue counted once | No double-counted revenue | 326 of 4,451 orders |
| Users with several devices or countries | First observed value | Splits are per user, not per event | 4,182 users with more than one device (1.55%) |
| `<Other>` / `(data deleted)` sources | Kept as their own groups | Obfuscated share is always visible | 50,002 users (18.5%) in Other or Data deleted |
| Extreme order values and user-days | Kept; medians shown beside means | Averages may be pulled by a few rows | Largest order $1,530 against a $48 median; user-day outliers: see notebook 02, section 6 |
