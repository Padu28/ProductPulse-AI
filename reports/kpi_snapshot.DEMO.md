# KPI snapshot (SYNTHETIC DEMO DATA - not findings)

Reporting period: 2020-11-01 to 2021-01-31  
Source: SYNTHETIC DEMO DATA - not findings  
Generated: 2026-11-11 by `scripts/build_metric_summary.py`

| Metric id | Metric | Value | Numerator | Denominator | Segment | SQL |
|---|---|---|---|---|---|---|
| `active_users` | Active users | **12,000** |  |  | All users | sql/03_event_metrics.sql Q14-Q15 |
| `user_purchase_conversion` | User purchase conversion | **2.07%** | 248 users with a purchase event | 12,000 active users | All users | sql/04_funnel_analysis.sql Q19 |
| `validated_orders` | Validated orders | **245** |  |  | All users | sql/02_data_quality.sql Q11 |
| `revenue_usd` | Revenue (USD, de-duplicated) | **$13,301.00** |  | 245 validated orders | All users | sql/02_data_quality.sql Q11 |
| `funnel_user_view_to_cart` | User funnel: View item to Add to cart | **25.18%** | 1,135 users with 'Add to cart' | 4,508 users with 'View item' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_cart_to_checkout` | User funnel: Add to cart to Begin checkout | **47.67%** | 541 users with 'Begin checkout' | 1,135 users with 'Add to cart' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_checkout_to_purchase` | User funnel: Begin checkout to Purchase | **45.84%** | 248 users with 'Purchase' | 541 users with 'Begin checkout' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_view_to_purchase` | User funnel: View item to Purchase | **5.50%** | 248 users with 'Purchase' | 4,508 users with 'View item' | All users | sql/04_funnel_analysis.sql Q19 |
| `funnel_user_largest_drop_off` | User funnel: largest step drop-off | **74.82%** | 3,373 users not reaching 'Add to cart' | 4,508 users with 'View item' | View item to Add to cart | sql/04_funnel_analysis.sql Q19 |
| `funnel_session_view_to_cart` | Session funnel (sequential): View item to Add to cart | **22.18%** | 1,187 sessions reaching 'Add to cart' in order | 5,352 sessions reaching 'View item' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `funnel_session_cart_to_checkout` | Session funnel (sequential): Add to cart to Begin checkout | **46.67%** | 554 sessions reaching 'Begin checkout' in order | 1,187 sessions reaching 'Add to cart' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `funnel_session_checkout_to_purchase` | Session funnel (sequential): Begin checkout to Purchase | **45.13%** | 250 sessions reaching 'Purchase' in order | 554 sessions reaching 'Begin checkout' in order | All sessions | sql/04_funnel_analysis.sql Q21 |
| `device_desktop_purchase_conversion` | User purchase conversion: desktop | **2.31%** | 160 users with a purchase | 6,914 users | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_desktop_view_to_cart` | View item to add to cart: desktop | **25.24%** | 696 users who added to cart | 2,758 users who viewed an item | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_desktop_cart_to_checkout` | Add to cart to begin checkout: desktop | **51.44%** | 358 users who began checkout | 696 users who added to cart | device = desktop | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_purchase_conversion` | User purchase conversion: mobile | **1.75%** | 85 users with a purchase | 4,864 users | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_view_to_cart` | View item to add to cart: mobile | **24.85%** | 417 users who added to cart | 1,678 users who viewed an item | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_mobile_cart_to_checkout` | Add to cart to begin checkout: mobile | **42.21%** | 176 users who began checkout | 417 users who added to cart | device = mobile | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_purchase_conversion` | User purchase conversion: tablet | **1.35%** | 3 users with a purchase | 222 users | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_view_to_cart` | View item to add to cart: tablet | **30.56%** | 22 users who added to cart | 72 users who viewed an item | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `device_tablet_cart_to_checkout` | Add to cart to begin checkout: tablet | **31.82%** | 7 users who began checkout | 22 users who added to cart | device = tablet | sql/04_funnel_analysis.sql Q20 |
| `channel_organic_search_purchase_conversion` | User purchase conversion: Organic search | **2.22%** | 90 users with a purchase | 4,057 users | channel = Organic search | sql/07_segment_analysis.sql Q31 |
| `channel_direct_purchase_conversion` | User purchase conversion: Direct | **2.10%** | 57 users with a purchase | 2,720 users | channel = Direct | sql/07_segment_analysis.sql Q31 |
| `channel_other_purchase_conversion` | User purchase conversion: Other | **2.00%** | 41 users with a purchase | 2,045 users | channel = Other | sql/07_segment_analysis.sql Q31 |
| `channel_referral_purchase_conversion` | User purchase conversion: Referral | **2.30%** | 35 users with a purchase | 1,520 users | channel = Referral | sql/07_segment_analysis.sql Q31 |
| `channel_data_deleted_purchase_conversion` | User purchase conversion: Data deleted | **1.78%** | 17 users with a purchase | 956 users | channel = Data deleted | sql/07_segment_analysis.sql Q31 |
| `channel_paid_search_purchase_conversion` | User purchase conversion: Paid search | **1.14%** | 8 users with a purchase | 702 users | channel = Paid search | sql/07_segment_analysis.sql Q31 |
| `retention_2020-11_month_1` | Activity retention: 2020-11 cohort, month 1 | **11.22%** | 440 cohort users active in that month | 3,923 users in cohort | cohort = 2020-11 | sql/05_cohort_retention.sql Q23 |
| `retention_2020-11_month_2` | Activity retention: 2020-11 cohort, month 2 | **0.94%** | 37 cohort users active in that month | 3,923 users in cohort | cohort = 2020-11 | sql/05_cohort_retention.sql Q23 |
| `retention_2020-12_month_1` | Activity retention: 2020-12 cohort, month 1 | **10.80%** | 434 cohort users active in that month | 4,017 users in cohort | cohort = 2020-12 | sql/05_cohort_retention.sql Q23 |
| `single_day_users` | Users active on one day only | **75.41%** | 9,049 users with exactly one active day | 12,000 users | All users | sql/05_cohort_retention.sql Q25 |
| `product_top1_viewer_to_buyer` | Viewer-to-buyer rate: Demo Item 01 | **4.34%** | 36 users who bought the item | 829 users who viewed the item | item = Demo Item 01 (#1 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top2_viewer_to_buyer` | Viewer-to-buyer rate: Demo Item 02 | **4.92%** | 25 users who bought the item | 508 users who viewed the item | item = Demo Item 02 (#2 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top3_viewer_to_buyer` | Viewer-to-buyer rate: Demo Item 03 | **5.05%** | 22 users who bought the item | 436 users who viewed the item | item = Demo Item 03 (#3 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top4_viewer_to_buyer` | Viewer-to-buyer rate: Demo Item 04 | **7.05%** | 26 users who bought the item | 369 users who viewed the item | item = Demo Item 04 (#4 by viewers) | sql/06_product_analysis.sql Q27 |
| `product_top5_viewer_to_buyer` | Viewer-to-buyer rate: Demo Item 05 | **5.33%** | 16 users who bought the item | 300 users who viewed the item | item = Demo Item 05 (#5 by viewers) | sql/06_product_analysis.sql Q27 |
