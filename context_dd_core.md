# Data Dictionary Core Schema Contract

This document defines the expected schema for the subway systems Excel file.

## Required Columns

- `SYSTEM_ID`: Unique identifier for each subway system (string). If absent, will be generated deterministically.
- `CITY`: City name where the subway system is located (string).
- `COUNTRY`: Country name where the subway system is located (string).

## Optional Columns

- `LATITUDE`: Latitude coordinate (numeric). If absent, will be inferred via geocoding.
- `LONGITUDE`: Longitude coordinate (numeric). If absent, will be inferred via geocoding.
- `SYSTEM_NAME`: Name of the subway system (string).
- `OPENED_YEAR`: Year the system opened (integer).
- `NUMBER_OF_LINES`: Number of lines in the system (integer).
- `TOTAL_MILES`: Total track length in miles (numeric).
- `ANNUAL_RIDERSHIP`: Annual ridership count (integer).
- `CITY_POPULATION`: City population (integer).
- `VISITED`: Whether the system has been visited (boolean or string: "yes"/"no"/"true"/"false").
- `LAST_MAJOR_UPDATE`: Year of last major update (integer or date string).
- `Sequence`: ID
- `City`: IGNORE
- `Ridden?`: y/n whether or not i've ridden on it
- `Year when First Ridden`: IGNORE
- `City links`: USE for inference of location
- `Country`: USE for inference of location
- `Continent`: IGNORE
- `Name`: name of the subway	
- `Year opened (General Format)`: year the subway was opened
- `Year opened     (date order)`: IGNORE
- `Year of last expansion`: year of last expansion
- `Stations`: the number of stations in the subway system
- `Lines`: number of lines in the subway system
- `System length  km`: IGNORE
- `System length   miles`: total track length of the subway system
- `Annual Ridership`: number of riders, unit of million trips
- `Year of ridership data `: IGNORE
- `Currently accessible?`: y/n whether or not you can access the subway system
- `Visited but subway not ridden`: IGNORE
- `Logo`: IGNORE
- `Pre-1985?`: IGNORE



## Column Name Normalization

All column names will be normalized to:
- ALL CAPS
- Spaces replaced with underscores
- Special characters handled appropriately


