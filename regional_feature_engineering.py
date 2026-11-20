import argparse
from pathlib import Path

import pandas as pd


OCEAN_VARIABLES = (
    "thetao_mean",
    "thetao_p95",
    "thetao_variance",
    "so_mean",
    "so_p95",
    "so_variance",
)


def classify_ocean_basin(latitude: float, longitude: float) -> str:
    if pd.isna(latitude) or pd.isna(longitude):
        return "UNKNOWN"
    if latitude >= 66:
        return "ARCTIC"
    if 30 <= latitude <= 46 and -6 <= longitude <= 36:
        return "MEDITERRANEAN"
    if longitude >= -70 and longitude <= 20 and latitude < 0:
        return "SOUTH_ATLANTIC"
    if longitude >= -80 and longitude <= 20 and latitude >= 0:
        return "NORTH_ATLANTIC"
    if longitude >= 20 and longitude <= 120:
        if latitude >= 0:
            return "NORTH_INDIAN"
        return "INDIAN_OCEAN"
    if longitude >= 120 or longitude <= -70:
        if latitude >= 0:
            return "NORTH_PACIFIC"
        return "SOUTH_PACIFIC"
    return "OTHER"


def add_regional_features(
    frame: pd.DataFrame,
    region_column: str = "region",
) -> pd.DataFrame:
    result = frame.copy()

    country = result["country"].fillna("UNKNOWN").astype(str).str.strip()
    country = country.mask(country.eq("") | country.str.lower().eq("nan"), "UNKNOWN")
    result["country_region"] = country

    if {"latitude", "longitude"}.issubset(result.columns):
        result["ocean_basin"] = [
            classify_ocean_basin(latitude, longitude)
            for latitude, longitude in zip(result["latitude"], result["longitude"])
        ]
    else:
        result["ocean_basin"] = "UNKNOWN"

    if region_column not in result.columns:
        result[region_column] = "UNKNOWN"
    region = result[region_column].fillna("UNKNOWN").astype(str).str.strip()
    region = region.mask(region.eq("") | region.str.lower().eq("nan"), "UNKNOWN")
    result[region_column] = region

    interaction_columns = {}
    for region_type in ("country_region", "ocean_basin", region_column):
        categories = sorted(result[region_type].unique())
        for variable in OCEAN_VARIABLES:
            if variable not in result.columns:
                continue
            for category in categories:
                safe_category = (
                    str(category)
                    .upper()
                    .replace(" ", "_")
                    .replace("-", "_")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(":", "")
                )
                column = f"{variable}__x__{region_type}__{safe_category}"
                interaction_columns[column] = (
                    result[variable] * result[region_type].eq(category)
                )

    if interaction_columns:
        result = pd.concat([result, pd.DataFrame(interaction_columns)], axis=1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add country, ocean-basin, and ocean-variable interaction features."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    frame = add_regional_features(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
