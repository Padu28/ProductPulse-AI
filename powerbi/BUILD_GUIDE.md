# Power BI build guide

Everything you need to assemble `ProductPulse.pbix` in Power BI Desktop: the data model, the theme, the DAX measures and a page-by-page layout. A `.pbix` file can only be created inside Power BI Desktop, so this folder holds the parts and the instructions rather than the finished file.

Time needed: about 2 to 3 hours the first time.

**Before you start:** run `python scripts/export_from_bigquery.py --project YOUR_PROJECT` so that `data/exports/` contains the real CSV files. Do not build the report on `data/demo/`.

---

## Step 1. Load the data

Home > Get data > Text/CSV. Load these files from `data/exports/`:

| File | Table name | Grain | Role |
|---|---|---|---|
| `fact_user_day.csv` | `fact_user_day` | one row per user per active day | Fact |
| `dim_user.csv` | `dim_user` | one row per user | Dimension |
| `session_funnel.csv` | `session_funnel` | device x channel | Small aggregate (sequential funnel) |
| `product_performance.csv` | `product_performance` | one row per product | Small aggregate |

In Power Query (Transform data), set the types explicitly:

- `user_pseudo_id`: **Text** (it looks like a number; if Power BI makes it Decimal, ids get corrupted)
- `event_dt`, `first_seen_dt`, `last_seen_dt`, `cohort_month`: **Date**
- flags, counts: **Whole number**; `revenue_usd`, `engagement_sec`: **Decimal number**

Refresh method: re-run the export script, then Home > Refresh. Write that sentence in your README.

## Step 2. Create the date table

Modeling > New table:

```DAX
dim_date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2020, 11, 1 ), DATE ( 2021, 1, 31 ) ),
    "Month", FORMAT ( [Date], "yyyy-mm" ),
    "Month Name", FORMAT ( [Date], "mmm yyyy" ),
    "Week Start", [Date] - WEEKDAY ( [Date], 2 ) + 1,
    "Weekday", FORMAT ( [Date], "ddd" ),
    "Weekday Number", WEEKDAY ( [Date], 2 )
)
```

Table tools > Mark as date table > `Date`. Sort `Weekday` by `Weekday Number`.

## Step 3. Relationships and one calculated column

Model view. Create exactly two relationships, both **one-to-many, single direction**:

```
dim_user[user_pseudo_id]  1 ──── *  fact_user_day[user_pseudo_id]
dim_date[Date]            1 ──── *  fact_user_day[event_dt]
```

`session_funnel` and `product_performance` stay unrelated on purpose (they are pre-aggregated; see the notes on pages 2 and 4).

Add two calculated columns (needed for the cohort heatmap):

```DAX
-- on fact_user_day
Month Number =
DATEDIFF ( RELATED ( dim_user[cohort_month] ), fact_user_day[event_dt], MONTH )

-- on dim_user (a text label, so the matrix does not turn the date into a Year/Quarter hierarchy)
Cohort Label =
FORMAT ( dim_user[cohort_month], "yyyy-mm" )
```

Hide from report view: `fact_user_day[user_pseudo_id]`, `fact_user_day[event_dt]`, all raw flag columns, `dim_user[user_pseudo_id]`. Report users should pick dates from `dim_date` and attributes from `dim_user`.

## Step 4. Funnel stage table and measures

Home > Enter data. Name the table `Funnel Stage`:

| Stage | Stage Order |
|---|---|
| View item | 1 |
| Add to cart | 2 |
| Begin checkout | 3 |
| Purchase | 4 |

Select `Stage` > Sort by column > `Stage Order`. Do not relate this table to anything.

Create an empty table `_Measures` (Enter data, one blank column, Load) and add every measure from [`measures.dax`](measures.dax) with Modeling > New measure. Format rates as Percentage with 1 or 2 decimals, counts as Whole number with a thousands separator, revenue as Currency.

## Step 5. Theme and canvas

- View > Themes > Browse for themes > `powerbi/theme.json`.
- Format page > Canvas settings: 16:9 (1280 x 720).
- Use an 8-pixel rhythm: 24 px outer margin, 16 px between cards. Turn on View > Gridlines and Snap to grid.

| Element | Value |
|---|---|
| Canvas background | `#F5F7FB` |
| Header bar, titles | `#14243A` (navy) |
| Accent / selected series | `#2563EB` (blue) |
| Positive context | `#0D9488` (teal) |
| Caution | `#D97706` (amber), always with a text label |
| Device colours (fixed) | desktop blue, mobile teal, tablet amber |
| Font | Segoe UI; KPI value 28 pt, titles 12 pt semibold, labels 10 pt |

**Shared layout on every page**

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ProductPulse AI   [Overview] [Funnel] [Retention] [Products]    [Reset]  │  navy header, 56 px
├──────────────────────────────────────────────────────────────────────────┤
│ Date ▾        Device ▾        Country ▾        Channel ▾                 │  slicer row, 56 px
├──────────────────────────────────────────────────────────────────────────┤
│                              page content                                │
└──────────────────────────────────────────────────────────────────────────┘
```

Slicers: `dim_date[Date]` (Between), `dim_user[device_category]`, `dim_user[country]`, `dim_user[channel_group]` (all Dropdown). Build them once on page 1, then View > Sync slicers and tick all four pages.

## Step 6. The four pages

### Page 1: Executive overview

```
┌ Active Users ┐┌ Validated Orders ┐┌ User Purchase Conv. ┐┌ Revenue USD ┐   4 cards
├──────────────────────────────────┬──────────────────────────────────────┤
│ Daily active users (line)        │ Daily user purchase conversion (line)│
├──────────────────────────────────┼──────────────────────────────────────┤
│ Active users by device (bar)     │ Conversion by channel (bar)          │
├──────────────────────────────────┴──────────────────────────────────────┤
│ Insight strip: [Largest Drop-off Label]            [See funnel →]       │
└─────────────────────────────────────────────────────────────────────────┘
```

| Visual | Fields |
|---|---|
| 4 cards | `[Active Users]`, `[Validated Orders]`, `[User Purchase Conversion]`, `[Revenue USD]` |
| Line chart 1 | X `dim_date[Date]`, Y `[Active Users]` |
| Line chart 2 | X `dim_date[Date]`, Y `[User Purchase Conversion]` |
| Bar chart 1 | Y `dim_user[device_category]`, X `[Active Users]` |
| Bar chart 2 | Y `dim_user[channel_group]`, X `[User Purchase Conversion]` |
| Insight strip | Card with `[Largest Drop-off Label]`, plus a button with Action > Page navigation > Funnel |

Two line charts are used instead of one dual-axis chart: users and a percentage on two y-scales invite false comparisons. Put the reporting period in the header with a card showing `[Reporting Period]`.

### Page 2: Conversion funnel

| Visual | Fields |
|---|---|
| Clustered bar "Users reaching each stage" | Y `'Funnel Stage'[Stage]`, X `[Funnel Users]`, data labels on |
| Table "Stage detail" | `Stage`, `[Funnel Users]`, `[Funnel Share of First Stage]`, `[Funnel Step Conversion]`, `[Funnel Drop-off Users]` |
| Matrix "By device" | Rows `dim_user[device_category]`; values `[Users Viewed Item]`, `[View to Cart Rate]`, `[Cart to Checkout Rate]`, `[Checkout to Purchase Rate]` |
| Matrix "By channel" | Same, rows `dim_user[channel_group]` |
| Card row "Sequential session funnel" | `[Seq View to Cart Rate]`, `[Seq Cart to Checkout Rate]`, `[Seq Checkout to Purchase Rate]` |
| Text box (definition) | "Top visuals: user-level stage presence (each event at least once, any order). Bottom cards: sequential funnel inside one session, whole period." |

A plain bar chart is used rather than the funnel visual so the bar lengths are honest and the step rates sit in the table next to it.

The sequential cards read the unrelated `session_funnel` table, so they cover the whole period and do **not** respond to the slicers. Say so in the text box. If you want a device or channel view of them, add `session_funnel[device_category]` or `session_funnel[channel_group]` as a visual-level filter on those cards.

### Page 3: Retention and cohorts

| Visual | Fields |
|---|---|
| Matrix "Cohort heatmap" | Rows `dim_user[Cohort Label]`; Columns `fact_user_day[Month Number]` (drag it into Columns); Values `[Retention Rate]` |
| Table "Cohort size" (next to it) | `dim_user[Cohort Label]`, `[Cohort Users]` |
| Line chart "Returning share" | X `dim_date[Week Start]`, Y `[Single-day User Share]` |
| Bar chart "Segment comparison" | Y `dim_user[device_category]`, X `[Avg Active Days per User]` |
| Text box | "Cohort = month of first OBSERVED activity, not first-ever visit. Blank cells were not observed (sample ends 31 Jan 2021)." |

Heatmap formatting: select the matrix > Cell elements > Background colour > Format style: Gradient, based on `[Retention Rate]`, minimum `#EFF4FF`, maximum `#1E3A8A`, and set "If value is blank" to **Don't format**. Turn off row and column subtotals. Month 0 is always 100%; that is correct. Expected values: 2020-11 → 100%, 5.9%, 1.5%; 2020-12 → 100%, 2.5%; 2021-01 → 100%.

`[Retention Rate]` ignores the date slicer by design, so cohorts are never cut in half. Mention it in the text box.

### Page 4: Product and acquisition insights

| Visual | Fields |
|---|---|
| Bar "Top 10 products by viewers" | Y `product_performance[item_name]`, X `[Product Viewers]`, Top N filter = 10 by `[Product Viewers]` |
| Bar "Top 10 products by item revenue" | Y `item_name`, X `[Product Item Revenue USD]`, Top N = 10 |
| Table "Product detail" | `item_name`, `item_category`, `users_viewed`, `users_added_cart`, `users_purchased`, `units_purchased`, `item_revenue_usd`, `[Viewer to Buyer Rate]` |
| Matrix "Acquisition" | Rows `dim_user[channel_group]`; values `[Active Users]`, `[Purchasers]`, `[User Purchase Conversion]`, `[Revenue USD]`, `[Revenue per User]` |
| Text box (coverage) | "Product tables cover the whole period and all users; slicers do not apply. Channel = first-touch source; 'Other' and 'Data deleted' are obfuscation artefacts." |

## Step 7. Interactions

| Interaction | How to build it |
|---|---|
| Slicers | Built in step 5 and synced to all pages |
| Cross-filtering | On by default. On page 1, select the device bar chart > Format > Edit interactions and set it to **Filter** (not Highlight) the line charts |
| Drill-through | New page "Segment detail" (hidden). Drag `dim_user[device_category]` and `dim_user[channel_group]` into the Drill through well. Add the four KPI cards, the funnel bar chart and the daily line chart. A back button is added automatically. Right-click any device or channel bar > Drill through |
| Report-page tooltip | New page "Tooltip - definitions" (hidden): Page information > Allow use as tooltip; Canvas settings > Tooltip. Add cards for `[Purchasers]`, `[Active Users]`, `[User Purchase Conversion]` and a text box with the definition. On each conversion visual: Format > General > Tooltips > Report page > select it |
| Bookmarks | View > Bookmarks. Clear all slicers > Add > rename to **Default view**. Then expand the detail tables you want > Add > **Detailed view** |
| Reset filters | Insert > Buttons > Blank, text "Reset", Action > Bookmark > Default view. Put it in the header of every page |
| Navigation | Insert > Buttons > Navigator > Page navigator. Format the selected state with the blue accent so the active page is obvious |
| Accessibility | Give every visual a descriptive title and Alt text (Format > General > Alt text). Turn data labels on for the main bars. Set tab order in View > Selection |

## Step 8. Reconcile with SQL before you take screenshots

With **all slicers cleared**, the cards must equal these SQL results exactly:

| Power BI measure | Must equal | SQL |
|---|---|---|
| `[Active Users]` | `identified_users` | `01_schema_exploration.sql` Q01 |
| `[Users Viewed Item]`, `[Users Added to Cart]`, `[Users Began Checkout]`, `[Purchasers]` | the four stage counts | `04_funnel_analysis.sql` Q19 |
| `[Validated Orders]`, `[Revenue USD]` | `validated_orders`, `revenue_deduplicated` | `02_data_quality.sql` Q11 |
| `[Retention Rate]` per cell | `retention_rate` | `05_cohort_retention.sql` Q23 |
| `[Seq Sessions Purchase]` | `seq_purchase` | `04_funnel_analysis.sql` Q21 |

Then select **Device = mobile** and check the funnel counts against the mobile row of Q20. Record both checks in `docs/qa_checklist.md`. The same numbers are printed by `scripts/build_metric_summary.py` in `reports/kpi_snapshot.md`, which is the quickest thing to compare against.

## Step 9. Save and capture

1. File > Save as > `powerbi/ProductPulse.pbix`.
2. Export one PNG per page (File > Export > PDF, or the Snipping Tool at 100% zoom) into `powerbi/screenshots/` as `01_overview.png`, `02_funnel.png`, `03_retention.png`, `04_products.png`.
3. Add the screenshots near the top of `README.md` (the image links are already there).

`fact_user_day` and `dim_user` contain the obfuscated `user_pseudo_id`. The dataset is public, but before pushing the `.pbix` to GitHub check its size (GitHub rejects files over 100 MB) and that you are comfortable publishing it.
