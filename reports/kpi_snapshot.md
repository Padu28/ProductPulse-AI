# KPI snapshot

Reporting period: 2020-11-01 to 2021-01-31  
Source: bigquery-public-data.ga4_obfuscated_sample_ecommerce (exported aggregates)  
Generated: 2026-11-11 by `scripts/build_metric_summary.py`

| Metric id | Metric | Value | Numerator | Denominator | Segment | SQL |
|---|---|---|---|---|---|---|
| `active_users` | Active users | **270,154** |  |  | All users | sql/03_event_metrics.sql Q14-Q15 |
| `user_purchase_conversion` | User purchase conversion | **1.64%** | 4,419 users with a purchase event | 270,154 active users | All users | sql/04_funnel_analysis.sql Q19 |
| `validated_orders` | Validated orders | **4,451** |  |  | All users | sql/02_data_quality.sql Q11 |
| `revenue_usd` | Revenue (USD, de-duplicated) | **$308,200.00** |  | 4,451 validated orders | All users | sql/02_data_quality.sql Q11 |
| `funnel_user_view_to_cart` | User funnel: View item to Add to cart | **20.48%** | 12,545 users with 'Add to cart' | 61,252 users with 'View item' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_cart_to_checkout` | User funnel: Add to cart to Begin checkout | **77.44%** | 9,715 users with 'Begin checkout' | 12,545 users with 'Add to cart' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_checkout_to_purchase` | User funnel: Begin checkout to Purchase | **45.49%** | 4,419 users with 'Purchase' | 9,715 users with 'Begin checkout' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_view_to_purchase` | User funnel: View item to Purchase | **7.21%** | 4,419 users with 'Purchase' | 61,252 users with 'View item' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_largest_drop_off` | User funnel: largest step drop-off | **79.52%** | 48,707 users not reaching 'Add to cart' | 61,252 users with 'View item' | View item to Add to cart | sql/04_funnel_analysis.sql Q19 |
| `funnel_session_view_to_cart` | Session funnel (sequential): View item to Add to cart | **19.69%** | 15,167 sessions reaching 'Add to cart' in order | 77,020 sessions reaching 'View item' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `funnel_session_cart_to_checkout` | Session funnel (sequential): Add to cart to Begin checkout | **35.71%** | 5,416 sessions reaching 'Begin checkout' in order | 15,167 sessions reaching 'Add to cart' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `funnel_session_checkout_to_purchase` | Session funnel (sequential): Begin checkout to Purchase | **52.33%** | 2,834 sessions reaching 'Purchase' in order | 5,416 sessions reaching 'Begin checkout' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `device_desktop_purchase_conversion` | User purchase conversion: desktop | **1.60%** | 2,518 users with a purchase | 156,905 users | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_desktop_view_to_cart` | View item to add to cart: desktop | **20.36%** | 7,268 users who added to cart | 35,697 users who viewed an item | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_desktop_cart_to_checkout` | Add to cart to begin checkout: desktop | **77.05%** | 5,600 users who began checkout | 7,268 users who added to cart | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_purchase_conversion` | User purchase conversion: mobile | **1.68%** | 1,802 users with a purchase | 107,175 users | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_view_to_cart` | View item to add to cart: mobile | **20.72%** | 5,007 users who added to cart | 24,160 users who viewed an item | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_cart_to_checkout` | Add to cart to begin checkout: mobile | **77.85%** | 3,898 users who began checkout | 5,007 users who added to cart | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_purchase_conversion` | User purchase conversion: tablet | **1.63%** | 99 users with a purchase | 6,074 users | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_view_to_cart` | View item to add to cart: tablet | **19.35%** | 270 users who added to cart | 1,395 users who viewed an item | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_cart_to_checkout` | Add to cart to begin checkout: tablet | **80.37%** | 217 users who began checkout | 270 users who added to cart | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `channel_organic_search_purchase_conversion` | User purchase conversion: Organic search | **1.53%** | 1,557 users with a purchase | 101,742 users | channel = Organic search | sql/07_segment_analysis.sql Q31 |
| `channel_direct_purchase_conversion` | User purchase conversion: Direct | **1.58%** | 1,011 users with a purchase | 64,109 users | channel = Direct | sql/07_segment_analysis.sql Q31 |
| `channel_other_purchase_conversion` | User purchase conversion: Other | **1.44%** | 680 users with a purchase | 47,101 users | channel = Other | sql/07_segment_analysis.sql Q31 |
| `channel_referral_purchase_conversion` | User purchase conversion: Referral | **1.86%** | 744 users with a purchase | 40,019 users | channel = Referral | sql/07_segment_analysis.sql Q31 |
| `channel_paid_search_purchase_conversion` | User purchase conversion: Paid search | **1.53%** | 218 users with a purchase | 14,282 users | channel = Paid search | sql/07_segment_analysis.sql Q31 |
| `channel_data_deleted_purchase_conversion` | User purchase conversion: Data deleted | **7.20%** | 209 users with a purchase | 2,901 users | channel = Data deleted | sql/07_segment_analysis.sql Q31 |
| `retention_2020-11_month_1` | Activity retention: 2020-11 cohort, month 1 | **5.86%** | 4,651 cohort users active in that month | 79,421 users in cohort | cohort = 2020-11 | sql/05_cohort_retention.sql Q23 |
| `retention_2020-11_month_2` | Activity retention: 2020-11 cohort, month 2 | **1.52%** | 1,204 cohort users active in that month | 79,421 users in cohort | cohort = 2020-11 | sql/05_cohort_retention.sql Q23 |
| `retention_2020-12_month_1` | Activity retention: 2020-12 cohort, month 1 | **2.53%** | 2,517 cohort users active in that month | 99,664 users in cohort | cohort = 2020-12 | sql/05_cohort_retention.sql Q23 |
| `single_day_users` | Users active on one day only | **89.00%** | 240,441 users with exactly one active day | 270,154 users | All users | sql/05_cohort_retention.sql Q25 |
| `product_top1_viewer_to_buyer` | Viewer-to-buyer rate: Super G Unisex Joggers | **1.50%** | 221 users who bought the item | 14,713 users who viewed the item | item = Super G Unisex Joggers (#1 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top2_viewer_to_buyer` | Viewer-to-buyer rate: Google Zip Hoodie F/C | **1.57%** | 218 users who bought the item | 13,869 users who viewed the item | item = Google Zip Hoodie F/C (#2 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top3_viewer_to_buyer` | Viewer-to-buyer rate: Google Navy Speckled Tee | **0.94%** | 129 users who bought the item | 13,696 users who viewed the item | item = Google Navy Speckled Tee (#3 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top4_viewer_to_buyer` | Viewer-to-buyer rate: YouTube Icon Tee Grey | **0.46%** | 58 users who bought the item | 12,696 users who viewed the item | item = YouTube Icon Tee Grey (#4 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top5_viewer_to_buyer` | Viewer-to-buyer rate: Google Campus Bike Eco Tee Navy | **0.36%** | 41 users who bought the item | 11,339 users who viewed the item | item = Google Campus Bike Eco Tee Navy (#5 by viewers) | sql/06_product_analysis.sql Q27 |
