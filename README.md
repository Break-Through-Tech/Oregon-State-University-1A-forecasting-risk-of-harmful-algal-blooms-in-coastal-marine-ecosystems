# Forecasting Risk of Harmful Algal Blooms in Coastal Marine Ecosystems

This project is part of the Break Through Tech AI Studio program and was completed in partnership with the Socio-Environmental Analysis Lab at Oregon State University. Our goal is to build a reproducible machine learning workflow that estimates the risk of harmful algal bloom (HAB) events from ocean conditions while evaluating the model in a way that reflects forecasting future events.

HABs can harm marine ecosystems, human health, aquaculture, fisheries, and coastal economies. A useful forecasting system could eventually support insurance and financial risk tools for organizations that depend on coastal and marine resources. The current repository contains an in-progress research pipeline rather than a production forecasting system.

## Team Members

| Name | GitHub Handle | Contribution |
| --- | --- | --- |
| Stephanie Ng | [@syng828](https://github.com/syng828) | HAEDAT preprocessing, exploratory analysis, and biogeochemical feature exploration |
| Mayowa Esan | [@esanpelumi](https://github.com/esanpelumi) | Copernicus physics feature engineering, synthetic non-event construction, time-based validation, baseline modeling, and documentation |
| Meghana Ivaturi | [@megiva](https://github.com/megiva) | Dataset preparation, seasonal feature engineering, data splitting, and model evaluation |

## Project Highlights

- Cleaned and explored 14,101 HAEDAT records from 106 countries and corrected missing or invalid spatial and temporal values needed for Copernicus matching.
- Identified 9,700 events with usable locations and dates within the available Copernicus physics period.
- Calculated the mean, 95th percentile, and variance of surface temperature and salinity around HAB locations.
- Built a balanced 764-record model dataset containing 382 observed HAB events and 382 matched synthetic non-events.
- Corrected the original time imbalance so all five leave-future-out cross-validation folds contained both classes.
- Compared logistic regression and Random Forest models with ocean-only and ocean-plus-season feature sets.
- Found that the current features produce near-random preliminary performance, showing that additional environmental predictors and a stronger non-event definition are needed.

## Project Overview

The Harmful Algae Event Database provides records of reported HAB events, but it does not provide a comparable set of confirmed non-events. We therefore combine HAEDAT events with environmental measurements from the Copernicus Marine Service and construct synthetic non-events for model development.

The workflow has five main stages:

1. Clean and standardize HAEDAT event dates and coordinates.
2. Match each usable record with ocean conditions from Copernicus Marine.
3. Summarize the environmental data into model-ready features.
4. Pair observed HAB events with synthetic non-events matched in location and season.
5. Evaluate classification models with leave-future-out cross-validation so that each validation period occurs after its corresponding training period.

The long-term objective is a globally applicable seasonal forecasting model. The work in this repository establishes the data and evaluation pipeline and provides baseline results for future model development.

## Data Sources

### Harmful Algae Event Database

[HAEDAT](https://obis.org/dataset/62ddad25-2a19-485d-9bae-7eb3a40a71c5) contains reported harmful algae events from coastal regions around the world. The data include dates, coordinates, countries, affected organisms, detected toxins, and other event information. The repository contains standardized and processed versions of the source data under `data/`.

### Copernicus Marine Service

Ocean data are accessed through the [Copernicus Marine Service](https://data.marine.copernicus.eu/products) with the `copernicusmarine` Python package. Large global NetCDF products are queried remotely and are not stored in this repository.

The primary physics dataset is:

```text
cmems_mod_glo_phy_my_0.083deg_P1D-m
```

The current model uses:

- `thetao`: sea-water potential temperature
- `so`: sea-water salinity

The notebook also explores Copernicus biogeochemical variables, including oxygen, net primary production, pH, dissolved inorganic carbon, alkalinity, iron, nitrate, phosphate, and silicate. These exploratory variables are not included in the model comparison reported below because their available time period and matched sample are currently limited.

## Data Preparation and Exploration

The main cleaning steps include:

- Parsing event, start, and end dates into a consistent format.
- Deriving one observation date from the available temporal fields using documented midpoint and fallback rules.
- Removing records without usable latitude or longitude values.
- Flagging records without usable temporal information instead of silently treating them as valid observations.
- Correcting an obvious longitude decimal-placement error that produced values outside the valid range of -180 to 180 degrees.
- Checking duplicates, coordinate ranges, missing values, event years, geographic coverage, and reported HAB impacts.

The cleaned HAEDAT table contains 14,044 records with usable coordinates. Of these, 9,700 have usable dates within the Copernicus physics coverage period beginning in 1993. Events outside that period remain documented but cannot be matched to the same reanalysis product.

### Environmental Feature Engineering

For each selected event, the workflow extracts surface conditions from a one-degree buffer on each side of the event coordinates. It uses the nearest daily Copernicus observation and the shallowest available depth, approximately 0.494 meters.

The following six predictors are calculated over the selected ocean grid cells:

| Feature | Meaning |
| --- | --- |
| `thetao_mean` | Mean surface temperature |
| `thetao_p95` | 95th percentile of surface temperature |
| `thetao_variance` | Spatial variance of surface temperature |
| `so_mean` | Mean surface salinity |
| `so_p95` | 95th percentile of surface salinity |
| `so_variance` | Spatial variance of surface salinity |

The valid-cell counts, matched Copernicus date, date difference, buffer size, and surface depth are retained as quality-control metadata.

### Synthetic Non-Events

HAEDAT documents reported blooms but does not confirm where blooms did not occur. To create a comparison class, the project generates synthetic non-events at the same locations and in the same calendar months as observed events, using nearby years outside the defined HAEDAT spatiotemporal exclusion window.

These records are labeled `target = 0`, while observed HAEDAT events are labeled `target = 1`. They should be interpreted as **assumed non-events**, not confirmed absences. An unreported bloom may still have occurred on a synthetic date. This label uncertainty is one of the project's main limitations.

The current model-building dataset contains:

| Class | Records |
| --- | ---: |
| Observed HAB events | 382 |
| Synthetic non-events | 382 |
| **Total** | **764** |

## Model Development

### Models

The current experiments compare:

- Logistic regression as an interpretable linear baseline.
- Random Forest as a nonlinear model that can learn interactions among the predictors.
- Ocean-only features versus ocean features combined with calendar-season features.

A dummy-classifier notebook is also included as a basic reference baseline.

### Leave-Future-Out Validation

Model performance is estimated with five expanding leave-future-out folds. Each model is trained on earlier observations and evaluated on a later period. This prevents future observations from being used to predict the past and provides a more realistic estimate of forecasting performance than a random split.

The first model dataset placed many synthetic non-events in older years and observed HAB events in newer years. Several folds therefore contained only one class. The synthetic non-event procedure was revised to match the classes more closely across years and seasons. After the revision, all five folds contained both observed events and synthetic non-events.

The final unseen validation set should remain separate from model selection and tuning. Results below are cross-validation results, not final production or holdout-test performance.

## Results and Key Findings

Mean performance across the five leave-future-out folds is shown below.

| Model | Accuracy | Precision | Recall | F1 | Average Precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic regression, ocean only | 0.449 | 0.440 | 0.527 | 0.475 | 0.465 |
| Logistic regression, ocean plus season | 0.433 | 0.436 | 0.543 | 0.481 | 0.454 |
| Random Forest, ocean only | 0.456 | 0.451 | 0.460 | 0.449 | 0.483 |
| Random Forest, ocean plus season | 0.455 | 0.453 | 0.462 | 0.452 | 0.478 |

The corrected dataset produced a more trustworthy evaluation because all folds were usable and both classes appeared across the full time range. However, none of the tested configurations performed reliably above a simple chance-level benchmark on this balanced dataset.

The results suggest that:

- Temperature and salinity alone do not contain enough information to separate the current event and synthetic non-event classes.
- Adding calendar-season features did not materially improve performance.
- Random Forest did not provide a meaningful improvement over logistic regression.
- Better pseudo-absence validation and additional environmental features are more important than testing increasingly complex algorithms at this stage.

## Repository Structure

```text
.
├── Challenge-Project-Overview.md
├── Documentation.md
├── Getting-Started-for-Fellows.md
├── copernicusmarine/
│   ├── environment.yml
│   ├── example.py
│   └── instructions.md
├── data/
│   ├── raw/
│   └── processed/
├── literature/
│   └── Brenckman et al. 2025.pdf
├── notebooks/
│   ├── OSU1A.ipynb
│   ├── SeasonalFeatures.ipynb
│   ├── SplitData.ipynb
│   ├── Task3.ipynb
│   ├── dummy_classifier.ipynb
│   └── example.ipynb
├── requirements.txt
└── README.md
```

The notebooks are research notebooks and are still being consolidated. Some cells depend on processed files created by earlier steps, and Copernicus extraction cells can take a long time to complete.

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/Break-Through-Tech/Oregon-State-University-1A-forecasting-risk-of-harmful-algal-blooms-in-coastal-marine-ecosystems.git
cd Oregon-State-University-1A-forecasting-risk-of-harmful-algal-blooms-in-coastal-marine-ecosystems
```

### 2. Create a Python environment

Python 3.12 is recommended because it matches the environment used for the current notebooks.

```bash
python -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set up Copernicus Marine access

Create a free Copernicus Marine account and authenticate through the toolbox:

```python
import copernicusmarine

copernicusmarine.login()
```

Enter the credentials when prompted. Never place Copernicus credentials, GitHub tokens, or other secrets directly in a notebook or commit them to the repository.

### 4. Run the notebooks

For VS Code or Jupyter, open the repository and use the environment created above. The notebooks use paths relative to the `notebooks` directory.

For Google Colab, clone the repository and move into the notebook directory before running project cells:

```python
%cd /content/Oregon-State-University-1A-forecasting-risk-of-harmful-algal-blooms-in-coastal-marine-ecosystems/notebooks
%pip install -r ../requirements.txt
```

Start with the existing processed files when working on EDA or modeling. Do not use **Run all** unless you intend to repeat every Copernicus query. The global extraction and leave-future-out experiments can take a long time, and Colab's local storage disappears when its runtime resets.

Recommended workflow:

1. Review `notebooks/OSU1A.ipynb` for HAEDAT cleaning, EDA, and environmental feature development.
2. Use the processed files under `data/processed/` for repeatable model experiments.
3. Review `notebooks/SplitData.ipynb` and `notebooks/SeasonalFeatures.ipynb` for data-splitting and seasonal-feature work.
4. Use `notebooks/dummy_classifier.ipynb` and the model-development sections for baseline comparisons.
5. Save small processed outputs and evaluation summaries through the team's GitHub workflow rather than relying on temporary Colab storage.

## Limitations

- HAEDAT reflects reported events and may have geographic, temporal, and reporting biases.
- Synthetic non-events are assumed absences and may include unreported HAB events.
- The current 764-record model dataset is small relative to the global scope of the project.
- Temperature, salinity, and simple seasonal features do not capture all biological and physical conditions that contribute to HAB formation.
- The Copernicus biogeochemical products have a shorter usable time period than the physics reanalysis, which limits matched historical samples.
- Preliminary cross-validation performance is not strong enough for operational risk decisions.
- A final untouched validation evaluation and additional bias checks are still required.

## Next Steps

- Confirm a scientifically defensible definition of non-events with the Challenge Advisor.
- Add biologically relevant predictors such as nutrients, oxygen, pH, primary productivity, currents, and other coastal conditions where coverage permits.
- Increase the number and geographic diversity of paired observations without reintroducing time imbalance.
- Evaluate gradient-boosted trees and other models after improving the feature and label quality.
- Tune models only inside the leave-future-out training folds.
- Compare precision-recall curves and select decision thresholds based on the cost of missed HAB events and false alarms.
- Evaluate the selected pipeline once on the untouched validation dataset.
- Consolidate the exploratory notebooks into a reproducible end-to-end pipeline.

## License

An open-source license has not yet been approved for this project. Until a license is added, contact the project team and Challenge Advisor before reusing or redistributing the repository's data, code, or documentation.

## References

- [Harmful Algae Event Database on OBIS](https://obis.org/dataset/62ddad25-2a19-485d-9bae-7eb3a40a71c5)
- [Copernicus Marine Data Store](https://data.marine.copernicus.eu/products)
- [Copernicus Marine Toolbox Python interface](https://toolbox-docs.marine.copernicus.eu/en/stable/python-interface.html)
- [Brenckman et al. 2025, A Review of Harmful Algal Blooms](literature/Brenckman%20et%20al.%202025.pdf)
- [NOAA overview of the economic impact of the 2018 Florida red tide](https://coastalscience.noaa.gov/news/total-economic-impact-of-2018-red-tide-now-estimated-at-2-7b/)

## Acknowledgements

We thank Jack Buckner and the Socio-Environmental Analysis Lab at Oregon State University for their guidance as the Challenge Advisor and host organization. We also thank Hrushikesh Shetty and the Break Through Tech AI Studio team for coaching and project support. The environmental datasets used in this work are provided by the Copernicus Marine Service, and harmful algae event records are provided through HAEDAT and OBIS.
