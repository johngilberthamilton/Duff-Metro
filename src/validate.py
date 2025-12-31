"""
Data validation module for Excel uploads.

Validates uploaded Excel files against the schema contract defined in
context_dd_core.md, providing human-readable error messages.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
import re


# Required columns as per context_dd_core.md
REQUIRED_COLUMNS = ["SYSTEM_ID", "CITY", "COUNTRY"]

# Column name mappings from various formats to normalized names
# Maps variations to standardized column names
COLUMN_MAPPINGS = {
    "CITY": ["CITY", "City"],
    "COUNTRY": ["COUNTRY", "Country"],
    "SYSTEM_ID": ["SYSTEM_ID", "Sequence"],
    "SYSTEM_NAME": ["SYSTEM_NAME", "Name"],
    "OPENED_YEAR": ["OPENED_YEAR"],
    "NUMBER_OF_LINES": ["NUMBER_OF_LINES", "Lines"],
    "TOTAL_MILES": ["TOTAL_MILES", "System length   miles"],
    "ANNUAL_RIDERSHIP": ["ANNUAL_RIDERSHIP", "Annual Ridership"],
    "CITY_POPULATION": ["CITY_POPULATION"],
    "VISITED": ["VISITED", "Ridden?"],
    "LAST_MAJOR_UPDATE": ["LAST_MAJOR_UPDATE", "Year of last expansion"],
    "STATIONS": ["Stations"],
    "LATITUDE": ["LATITUDE"],
    "LONGITUDE": ["LONGITUDE"],
}

# Columns to ignore during validation
IGNORE_COLUMNS = [
    "City",  # Use CITY instead
    "Year when First Ridden",
    "Continent",
    "Year opened (General Format)",
    "Year opened     (date order)",
    "System length  km",  # Prefer miles
    "Year of ridership data ",
    "Visited but subway not ridden",
    "Logo",
    "Pre-1985?",
]


class ValidationError(Exception):
    """Custom exception for validation errors with user-friendly messages."""
    pass


def normalize_column_name(col_name: str) -> str:
    """
    Normalize column names to ALL_CAPS_WITH_UNDERSCORES format.
    
    Args:
        col_name: Original column name
        
    Returns:
        Normalized column name
    """
    if pd.isna(col_name):
        return str(col_name).upper()
    
    # Convert to string and strip whitespace
    normalized = str(col_name).strip()
    
    # Replace spaces with underscores
    normalized = normalized.replace(" ", "_")
    
    # Replace special characters (keep only alphanumeric and underscore)
    normalized = "".join(c if c.isalnum() or c == "_" else "_" for c in normalized)
    
    # Convert to uppercase
    normalized = normalized.upper()
    
    # Remove multiple consecutive underscores
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    
    # Remove leading/trailing underscores
    normalized = normalized.strip("_")
    
    return normalized


def map_columns_to_normalized(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map various column name formats to normalized names.
    
    First tries to find exact matches in COLUMN_MAPPINGS, then normalizes
    any remaining columns.
    
    Args:
        df: DataFrame with original column names
        
    Returns:
        DataFrame with normalized column names
    """
    df_copy = df.copy()
    column_mapping = {}
    
    # Build mapping from original to normalized names
    for normalized_name, variants in COLUMN_MAPPINGS.items():
        for variant in variants:
            if variant in df_copy.columns:
                column_mapping[variant] = normalized_name
                break
    
    # For any unmapped columns, normalize them
    for col in df_copy.columns:
        if col not in column_mapping:
            normalized = normalize_column_name(col)
            # Only map if the normalized name is different and not already taken
            if normalized != col and normalized not in column_mapping.values():
                # Check if this is an ignored column
                if col not in IGNORE_COLUMNS:
                    column_mapping[col] = normalized
    
    # Rename columns
    df_copy = df_copy.rename(columns=column_mapping)
    
    return df_copy


def validate_required_columns(df: pd.DataFrame) -> List[str]:
    """
    Check for missing required columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        List of missing required column names (empty if all present)
    """
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    return missing


def generate_system_id_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate deterministic SYSTEM_ID if missing.
    
    Uses CITY + COUNTRY to create a deterministic ID.
    
    Args:
        df: DataFrame that may be missing SYSTEM_ID
        
    Returns:
        DataFrame with SYSTEM_ID column (generated if needed)
    """
    df_copy = df.copy()
    
    if "SYSTEM_ID" not in df_copy.columns or df_copy["SYSTEM_ID"].isna().all():
        # Generate deterministic ID from CITY and COUNTRY
        df_copy["SYSTEM_ID"] = (
            df_copy.get("CITY", "").astype(str).str.strip() + "_" +
            df_copy.get("COUNTRY", "").astype(str).str.strip()
        ).str.upper().str.replace(" ", "_")
    
    return df_copy


def convert_numeric_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convert numeric-like text columns to numeric with error reporting.
    
    Robustly handles:
    - Commas and thousand separators
    - Units (miles, km, million, billion, etc.)
    - Parenthetical notes
    - Text annotations
    
    Args:
        df: DataFrame to process
        
    Returns:
        Tuple of (DataFrame with converted columns, list of conversion errors)
    """
    
    df_copy = df.copy()
    errors = []
    
    numeric_columns = [
        "OPENED_YEAR", "NUMBER_OF_LINES", "TOTAL_MILES", 
        "ANNUAL_RIDERSHIP", "CITY_POPULATION", "STATIONS",
        "LAST_MAJOR_UPDATE", "LATITUDE", "LONGITUDE"
    ]
    
    def robust_to_numeric(series, column_name):
        """
        Convert a series to numeric, handling various formats.
        
        Returns:
            Tuple of (converted series, list of failed values)
        """
        original_series = series.copy()
        converted = series.astype(str)
        
        # Handle NaN/None
        mask = converted.isin(['nan', 'None', '', 'None', 'NaT', '<NA>'])
        converted[mask] = None
        
        # Extract numeric patterns for different column types
        for idx in converted.index:
            if pd.isna(converted.loc[idx]) or converted.loc[idx] in ['nan', 'None', '']:
                continue
                
            val = str(converted.loc[idx]).strip()
            
            # Handle special cases by column type
            if column_name == "ANNUAL_RIDERSHIP":
                # Handle "X million" or "X billion" formats
                billion_match = re.search(r'([\d,]+\.?\d*)\s*billion', val, re.IGNORECASE)
                if billion_match:
                    num = float(billion_match.group(1).replace(',', '')) * 1_000_000_000
                    converted.loc[idx] = str(int(num))
                    continue
                
                million_match = re.search(r'([\d,]+\.?\d*)\s*million', val, re.IGNORECASE)
                if million_match:
                    num = float(million_match.group(1).replace(',', '')) * 1_000_000
                    converted.loc[idx] = str(int(num))
                    continue
                
                # Remove common text annotations in parentheses for ANNUAL_RIDERSHIP
                val = re.sub(r'\([^)]*\)', '', val).strip()
                
                # Try to extract numeric value (handles comma-separated numbers)
                numeric_match = re.search(r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)', val)
                if numeric_match:
                    # Remove commas and convert
                    num_str = numeric_match.group(1).replace(',', '')
                    converted.loc[idx] = num_str
                    continue
                else:
                    # No numeric value found - convert to NaN
                    converted.loc[idx] = None
                    continue
            
            elif column_name in ["TOTAL_MILES", "LATITUDE", "LONGITUDE"]:
                # Replace non-breaking spaces with regular spaces
                val = val.replace('\xa0', ' ').replace('\u00A0', ' ')
                # Extract numeric value first, even if wrapped in parentheses (handles "(250 mi)" format)
                # This regex looks for a number, optionally inside parentheses
                numeric_match = re.search(r'\(?\s*([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:mi|miles?|km|kilometers?)?\s*\)?', val, re.IGNORECASE)
                if numeric_match:
                    # Extract just the number part
                    num_str = numeric_match.group(1).replace(',', '')
                    converted.loc[idx] = num_str
                    continue
                else:
                    # Fallback: try to extract any number from the string
                    numeric_match = re.search(r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)', val)
                    if numeric_match:
                        num_str = numeric_match.group(1).replace(',', '')
                        converted.loc[idx] = num_str
                        continue
                    else:
                        converted.loc[idx] = None
                        continue
            
            elif column_name == "LAST_MAJOR_UPDATE":
                # Extract year from dates or year strings (4-digit year pattern)
                year_match = re.search(r'(\d{4})', val)
                if year_match:
                    converted.loc[idx] = year_match.group(1)
                    continue
                else:
                    # No year pattern found - convert to NaN
                    converted.loc[idx] = None
                    continue
            
            # For other columns, remove common text annotations in parentheses
            val = re.sub(r'\([^)]*\)', '', val)
            
            # Extract first numeric value (handles cases like "245.5 (approx)")
            numeric_match = re.search(r'([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)', val)
            if numeric_match:
                # Remove commas and convert
                num_str = numeric_match.group(1).replace(',', '')
                converted.loc[idx] = num_str
            else:
                # No numeric pattern found
                converted.loc[idx] = None
        
        # Now convert to numeric
        result = pd.to_numeric(converted, errors='coerce')
        
        # Find failures
        failed_mask = pd.isna(result) & ~original_series.isna()
        failed_values = original_series[failed_mask].unique()[:3].tolist() if failed_mask.any() else []
        
        return result, failed_values
    
    for col in numeric_columns:
        if col in df_copy.columns:
            original_values = df_copy[col].copy()
            converted_series, failed_values = robust_to_numeric(df_copy[col], col)
            
            # For ANNUAL_RIDERSHIP and LAST_MAJOR_UPDATE, explicitly set failed conversions to NaN
            # and suppress error reporting (these columns are expected to have some non-numeric values)
            if col in ["ANNUAL_RIDERSHIP", "LAST_MAJOR_UPDATE"]:
                # Ensure any values that couldn't be converted are explicitly NaN
                # Force any remaining non-numeric values to NaN as a final safety check
                df_copy[col] = converted_series
                # Additional explicit conversion to ensure all non-numeric are NaN
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                # Don't report errors for these columns - non-numeric values are expected and converted to NaN
            else:
                df_copy[col] = converted_series
                # Report errors if any (for other columns)
                if failed_values:
                    errors.append(
                        f"Column '{col}': Could not convert values to numeric. "
                        f"Example failing values: {failed_values}"
                    )
    
    return df_copy, errors


def parse_date_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse date columns robustly.
    
    Args:
        df: DataFrame to process
        
    Returns:
        Tuple of (DataFrame with parsed dates, list of parsing errors)
    """
    df_copy = df.copy()
    errors = []
    
    # For now, date parsing is handled by numeric conversion for year columns
    # This can be extended for actual date columns if needed
    
    return df_copy, errors


def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate and clean a dataframe according to the schema contract.
    
    This function:
    1. Filters rows with non-numeric Sequence values (before any data cleaning)
    2. Normalizes column names
    3. Validates required columns
    4. Generates SYSTEM_ID if missing
    5. Converts numeric columns
    6. Parses date columns
    
    Args:
        df: Raw dataframe from Excel upload
        
    Returns:
        Tuple of (cleaned DataFrame, list of validation errors/warnings)
        
    Raises:
        ValidationError: If critical validation fails (e.g., missing required columns)
    """
    errors = []
    warnings = []
    
    # Step 0: Filter out rows where "Sequence" is not numeric (before any data cleaning)
    df_copy = df.copy()
    if "Sequence" in df_copy.columns:
        # Convert Sequence to numeric, coercing errors to NaN
        sequence_numeric = pd.to_numeric(df_copy["Sequence"], errors='coerce')
        # Keep only rows where Sequence is numeric (not NaN after conversion)
        valid_mask = sequence_numeric.notna()
        rows_filtered = (~valid_mask).sum()
        if rows_filtered > 0:
            df_copy = df_copy[valid_mask].copy()
            warnings.append(f"Filtered out {rows_filtered} row(s) with non-numeric 'Sequence' values.")
    
    # Step 1: Map and normalize column names
    df_cleaned = map_columns_to_normalized(df_copy)
    
    # Step 2: Check for required columns (before generating SYSTEM_ID)
    missing_required = validate_required_columns(df_cleaned)
    if missing_required:
        # CITY and COUNTRY are truly required
        if "CITY" in missing_required or "COUNTRY" in missing_required:
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_required)}. "
                f"CITY and COUNTRY are required for geocoding."
            )
    
    # Step 3: Generate SYSTEM_ID if missing
    df_cleaned = generate_system_id_if_missing(df_cleaned)
    
    # Step 4: Convert numeric columns
    df_cleaned, numeric_errors = convert_numeric_columns(df_cleaned)
    errors.extend(numeric_errors)
    
    # Step 5: Parse date columns
    df_cleaned, date_errors = parse_date_columns(df_cleaned)
    errors.extend(date_errors)
    
    # Combine errors and warnings
    all_issues = errors + warnings
    
    return df_cleaned, all_issues

