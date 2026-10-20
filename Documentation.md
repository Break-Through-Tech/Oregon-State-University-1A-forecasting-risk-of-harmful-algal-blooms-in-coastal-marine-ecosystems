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
## Model evaluation with out-of-fold predictions

The model evaluation workflow is implemented in
[`notebooks/model_evaluation.ipynb`](notebooks/model_evaluation.ipynb). The
notebook uses the labeled environmental feature dataset,
`data/processed/hab_events_with_environmental_features.csv`, where:

- `target = 1` represents an observed harmful algal bloom (HAB) event.
- `target = 0` represents a synthetic non-event.

The notebook trains a scaled logistic-regression model using five-fold
stratified cross-validation. `StratifiedKFold` divides the data into five
folds while preserving the approximate proportion of HAB events and
non-events in each fold. For each fold, four parts are used to train the model
and the remaining part is used as unseen validation data. The process is
repeated until every row has received an out-of-fold prediction.

Before training, `StandardScaler` places the numeric features on comparable
scales. It is included in the model pipeline so that scaling is learned only
from each fold's training data. This helps prevent information from the
validation data leaking into model training. The logistic-regression model
returns a probability between 0 and 1 for each row. This probability is stored
as `y_score`.

With a classification threshold of `0.5`, scores at or above `0.5` are
converted to a positive prediction (`y_pred = 1`), representing a predicted
HAB event. Scores below `0.5` are converted to `y_pred = 0`. The threshold can
be changed depending on whether the application prioritizes finding more HAB
events or reducing false alarms.

### Evaluation metrics

The notebook calculates the following metrics for every fold:

- **Precision:** Of the rows predicted as HAB events, the proportion that
  were actually HAB events. Higher precision means fewer false alarms.
- **Recall:** Of all actual HAB events, the proportion detected by the model.
  Higher recall means fewer missed HAB events.
- **F1-score:** The harmonic mean of precision and recall. It is high only
  when both precision and recall are reasonably high.
- **PR-AUC:** The area under the Precision-Recall curve. It summarizes model
  performance over many possible probability thresholds rather than only the
  selected threshold of `0.5`. The notebook calculates this using
  `average_precision_score`.

The Precision-Recall curve plots precision on the y-axis against recall on the
x-axis at multiple thresholds. Each fold gets its own curve, allowing the
stability of the model's performance to be inspected across validation splits.

### Current evaluation results

The executed notebook produced the following mean results across the five
folds:

| Metric | Mean |
| --- | ---: |
| Precision | 0.296 |
| Recall | 0.248 |
| F1-score | 0.265 |
| PR-AUC | 0.419 |

The dataset contains 97 HAB events and 97 synthetic non-events, so the
approximate no-skill PR-AUC baseline is 0.50. The current mean PR-AUC of 0.419
indicates that this initial logistic-regression model is not yet separating
HAB events from synthetic non-events effectively. These results should be
treated as a baseline for future feature engineering and model improvements.

The notebook also saves:

- `results/hab_fold_metrics.csv` — precision, recall, F1-score, and PR-AUC for
  each fold and the mean row.
- `results/hab_oof_predictions.csv` — actual labels, predicted probabilities,
  and thresholded predictions for every row.
- `results/hab_precision_recall_curves.png` — fold-by-fold
  Precision-Recall curves.