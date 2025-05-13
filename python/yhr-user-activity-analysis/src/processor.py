import pandas as pd
from typing import Dict, Any

def enrich_dataframe(df: pd.DataFrame, geolocation_data: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Enrich DataFrame with geolocation data."""
    for field in ['city', 'region', 'country', 'postal', 'org']:
        df[field] = df['SOURCE_ADDRESS'].map(lambda ip: geolocation_data.get(ip, {}).get(field, 'unknown'))
    return df

def save_dataframe(df: pd.DataFrame, output_path: str) -> None:
    """Save DataFrame to CSV."""
    df.to_csv(output_path, index=False)
