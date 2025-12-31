"""
Geocoding module for inferring latitude and longitude from city and country.

Uses geopy with Nominatim to geocode locations and caches results in session state.
"""

import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Tuple, Optional, List
import time
import ssl
import certifi


def get_geocoder() -> Nominatim:
    """
    Get a Nominatim geocoder instance with SSL context configured.
    
    Returns:
        Nominatim geocoder instance
    """
    # Try to use certifi's certificate bundle for SSL verification
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        return Nominatim(
            user_agent="duff_metro_app",
            scheme="https",
            ssl_context=ssl_context
        )
    except Exception:
        # Fallback: create geocoder without strict SSL verification
        # This is acceptable for local development
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return Nominatim(
            user_agent="duff_metro_app",
            scheme="https",
            ssl_context=ssl_context
        )


def geocode_location(city: str, country: str, cache: dict) -> Optional[Tuple[float, float]]:
    """
    Geocode a city and country to get latitude and longitude.
    
    Uses caching to avoid repeated API calls. Constructs query as "{CITY}, {COUNTRY}".
    
    Args:
        city: City name
        country: Country name
        cache: Dictionary to cache geocoding results (key: query string, value: (lat, lon))
        
    Returns:
        Tuple of (latitude, longitude) if successful, None otherwise
    """
    # Construct query
    query = f"{city}, {country}"
    
    # Check cache first
    if query in cache:
        return cache[query]
    
    # Geocode
    try:
        geolocator = get_geocoder()
        location = geolocator.geocode(query, timeout=10)
        
        if location:
            result = (location.latitude, location.longitude)
            cache[query] = result
            # Small delay to respect rate limits
            time.sleep(0.5)
            return result
        else:
            cache[query] = None
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.warning(f"Geocoding error for {query}: {str(e)}")
        cache[query] = None
        return None
    except Exception as e:
        st.warning(f"Unexpected error geocoding {query}: {str(e)}")
        cache[query] = None
        return None


def add_coordinates_to_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Add latitude and longitude columns to dataframe using geocoding.
    
    Uses CITY and COUNTRY columns. Caches results in session state.
    If coordinates already exist, uses them. If geocoding fails, excludes
    that row from having coordinates (but doesn't remove it from the dataframe).
    
    Args:
        df: DataFrame with CITY and COUNTRY columns
        
    Returns:
        Tuple of (DataFrame with LATITUDE and LONGITUDE columns, list of unresolved cities)
    """
    df_copy = df.copy()
    unresolved = []
    
    # Initialize geocoding cache in session state if not exists
    if "geocoding_cache" not in st.session_state:
        st.session_state.geocoding_cache = {}
    
    cache = st.session_state.geocoding_cache
    
    # Initialize columns if they don't exist
    if "LATITUDE" not in df_copy.columns:
        df_copy["LATITUDE"] = None
    if "LONGITUDE" not in df_copy.columns:
        df_copy["LONGITUDE"] = None
    
    # Geocode rows that don't have coordinates
    for idx, row in df_copy.iterrows():
        # Skip if already has coordinates
        if pd.notna(row.get("LATITUDE")) and pd.notna(row.get("LONGITUDE")):
            continue
        
        city = str(row.get("CITY", "")).strip()
        country = str(row.get("COUNTRY", "")).strip()
        
        if not city or not country:
            unresolved.append(f"{city}, {country}")
            continue
        
        coords = geocode_location(city, country, cache)
        
        if coords:
            df_copy.at[idx, "LATITUDE"] = coords[0]
            df_copy.at[idx, "LONGITUDE"] = coords[1]
        else:
            unresolved.append(f"{city}, {country}")
    
    return df_copy, unresolved

