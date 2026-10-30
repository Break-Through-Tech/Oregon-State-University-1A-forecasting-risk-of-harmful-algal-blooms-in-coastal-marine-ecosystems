# Milestone #1 
## Address missing values and outliers
Missing columns of note
- Event Date
- Start Date
- End Date
- Latitude
- Longtitude

For missing event date, start date, AND end date -> Dropped them (However, all rows have a year)\
For missing latitude and longtitude -> Dropped them 
For the outlier longtitude (was ~-800, shifted the decimal forward)

Since there are still missing event date, start date, XOR end date. Decided to add a target date column. It follows these rules: 
Rule 1: If Start Date is empty, BUT both Event Date & End Date exist -> Pick Middle of Event and End\
Rule 2: If Start Date and End Date exist -> Pick Middle of Start and End\
Rule 3: If Start Date is empty -> Fallback to Event Date\
Rule 4: If Event Date is empty -> Fallback to Start Date


# Milestone #2
## Conducting HAB 
From looking at the correlation between variables and HAB events, it appears that the sea temperature is a possible correlation. It is done with spearman and pearson correlation, where spearman appeared to show a higher correlation.

## Copernicus biogeochemistry matching

The notebook also matches Copernicus Marine biogeochemistry (BGC) values to HAB
events and synthetic non-events. Each record is matched using its
`observation_date`, `latitude`, and `longitude`. The environmental values are
predictors, while `target` is the outcome (`1` for a HAB event and `0` for a
synthetic non-event).

The BGC datasets used in the notebook provide the following variables:

- BIO: `nppv`, `o2`
- CAR: `dissic`, `ph`, `talk`
- NUT: `fe`, `no3`, `po4`, `si`

The requests use a small spatial window around each record and shallow depths
because HABs are primarily a surface or near-surface phenomenon. The notebook
uses the nearest available Copernicus grid point and saves one row per record
to `data/processed/hab_bgc_matches.csv`. It saves after each record so an
interrupted run can resume without repeating completed records.

### Date coverage limitation

The selected BGC analysis/forecast datasets cover approximately
2021-11-01 through 2026-11-08. Records outside that range cannot be matched to
these BGC variables and are saved with missing BGC values. Older records can
still be analyzed with the physics variables, which have broader historical
coverage.

### Correlation analysis

After matching, the notebook calculates Spearman and Pearson correlations
between each BGC variable and `target`. Rows missing a particular variable are
excluded from that variable's calculation. A large correlation based on only a
few non-events is exploratory and should not be treated as reliable evidence.
The BGC overlap currently contains many HAB events but few eligible
non-events, so the physics-based model should remain the primary predictive
analysis until the BGC sample is better balanced.