import pandas as pd
import numpy as np

# Data Cleaning 
def clean_shipwreck_dataset(path="shipwrecks_raw.csv"):
    # Load raw CSV
    df = pd.read_csv(path)  

    # Strip whitespace from all cells
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # Replace empty strings or spaces with NaN
    df.replace(["", " ", "  ", "N/A", "na", "NA"], np.nan, inplace=True)

    # Parse DATE LOST into datetime
    df["DATE LOST"] = pd.to_datetime(df["DATE LOST"], errors="coerce")

    # Convert numeric columns
    numeric_cols = [
        "YEAR BUILT", "LENGTH", "BEAM", "DRAFT",
        "GROSS TONNAGE", "NET TONNAGE",
        "# CREW", "# PASS", "LIVES LOST"
    ]

    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.extract(r"([0-9.]+)")  
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert money fields
    money_cols = ["SHIP VALUE", "CARGO VALUE"]
    for col in money_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.extract(r"([0-9.]+)")
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Latitude & Longitude cleanup
    # Use LAT/LON, fall back to BACKUP if missing
    df["LAT"] = df["LATITUDE"].combine_first(df["LATITUDE_BACKUP"])
    df["LON"] = df["LONGITUDE"].combine_first(df["LONGITUDE_BACKUP"])

    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")

    df = df[df["DRAFT"] <= 81]

    # Drop duplicates
    df = df.drop_duplicates()

    # Final alphabetical sort (optional)
    df = df.sort_values(by="YEAR")

    return df

if __name__ == "__main__":
    cleaned = clean_shipwreck_dataset("ShipwreckDatabase.csv")
    cleaned.to_csv("shipwrecks_clean.csv", index=False)
    print("Cleaning complete! Saved as shipwrecks_clean.csv.")
