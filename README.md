# NYC Traffic Collisions & Weather Dashboard

A data engineering and visualization project exploring **New York City motor vehicle collisions from 2021 through 2024** and their relationship with daily weather conditions. The project builds a local data pipeline using **MongoDB and PostgreSQL**, then serves interactive collision summaries and maps through a **Flask** web application.

## Project Overview

This project combines two public data sources to explore questions such as:

- How do reported collisions vary by NYC borough and year?
- Where are collisions concentrated across NYC ZIP Code Tabulation Areas (ZCTAs)?
- How do average daily collision counts compare across dry, rainy, and snowy days?

The dashboards provide **descriptive comparisons**, not causal estimates of the effect of weather on accidents.

## Data Sources

| Dataset | Source | Usage |
| --- | --- | --- |
| Motor Vehicle Collisions — Crashes | [NYC Open Data](https://data.cityofnewyork.us/resource/h9gi-nx95.json) | Collision dates, boroughs, ZIP codes, and other crash attributes; extracted for January 1, 2021–December 31, 2024 |
| Daily weather observations | [NOAA Climate Data Online API](https://www.ncei.noaa.gov/cdo-web/webservices/v2) | Daily precipitation, snowfall, and temperature observations (station `GHCND:USW00094728`) for 2021–2024 |
| NYC ZIP Code Tabulation Area polygons | Supplied GeoJSON file | Geographic boundaries used for the collision choropleth map |

## Architecture

```text
NYC Open Data API ──────┐
                        ├──> MongoDB (apan5400)
NOAA CDO API ───────────┘      ├── collisions
                               └── weather
                                      │
                               Python / pandas
                         select and organize fields
                                      │
                                      ▼
                              PostgreSQL database
                             ├── collisions table
                             └── weather table
                                      │
                             Flask + SQLAlchemy
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
          Chart.js charts      Folium ZIP map         JSON API endpoint
                              + local GeoJSON
```

## Features

| Route | Description |
| --- | --- |
| `/` | Home page with links to project views |
| `/api/collisions_by_borough` | JSON records containing collision counts grouped by borough |
| `/dashboard` | Borough collision counts as a bar chart and table |
| `/dashboard_year` | Borough and annual collision counts as charts and tables |
| `/heatmap_zip` | Folium choropleth of collision counts by ZIP/ZCTA, with a weather-condition filter |
| `/dashboard_weather_effects` | Grouped bar chart and table of average daily collisions by borough and weather type |

### Weather Filters

The ZIP map supports the query parameter `weather`:

- `all`: all eligible collisions
- `clear`: precipitation = 0 and snowfall = 0
- `rain`: precipitation > 0 and snowfall = 0
- `snow`: snowfall > 0

For example, visit `http://127.0.0.1:5000/heatmap_zip?weather=snow` to view the map for snowy days.

The weather-comparison dashboard uses three mutually exclusive groups: **Dry**, **Wet (Rain)**, and **Snow**, based on those same precipitation/snowfall rules. It aggregates collisions by date and borough and then averages daily counts within each weather group.

## Technology Stack

- **Languages:** Python, SQL, HTML, CSS, JavaScript
- **Data extraction:** `requests`, NYC Open Data API, NOAA CDO API
- **Staging database:** MongoDB (`pymongo`)
- **Processing:** pandas, Jupyter Notebook
- **Analytical database:** PostgreSQL, SQLAlchemy, `psycopg2-binary`
- **Web application:** Flask
- **Visualizations:** Chart.js, Folium, GeoJSON

## Project Files

```text
.
├── Class_app (1).py
├── Data Engineering group project (302).ipynb
├── nyc-zip-code-tabulation-areas-polygons.geojson
└── README.md
```

- **`Data Engineering group project (302).ipynb`** retrieves data, stores it in MongoDB, organizes collision and weather records, exports intermediate JSON files, and loads PostgreSQL tables.
- **`Class_app (1).py`** is the Flask application containing the SQL queries, dashboard routes, visualizations, and map.
- **`nyc-zip-code-tabulation-areas-polygons.geojson`** provides ZIP/ZCTA shapes and the `postalCode` field used to join polygon features to collision counts on the map.

The notebook can also generate `collisions_raw.json` and `weather_raw.json`; these are output artifacts, not files required for rendering dashboards once PostgreSQL is populated.

## Local Setup

### 1. Prerequisites

Install Python 3, MongoDB, and PostgreSQL. Make sure both database services are running locally (the supplied code uses MongoDB port **27017** and PostgreSQL port **5432**).

### 2. Install Python packages

From the project folder, create an environment and install the dependencies used across the notebook and Flask app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask sqlalchemy pandas folium pymongo requests psycopg2-binary notebook
```

On Windows, activate the environment using `.venv\Scripts\activate` instead.

### 3. Configure databases and API access

The supplied notebook and application currently use **hardcoded local PostgreSQL connection settings**, and the notebook contains a **hardcoded NOAA API token**. Before sharing or deploying this code:

1. Replace the embedded NOAA token and move it to an environment variable or another secure local configuration mechanism. Obtain an API token through [NOAA CDO](https://www.ncdc.noaa.gov/cdo-web/token).
2. Replace the embedded database password, and configure the PostgreSQL connection in **both** the notebook and Flask file for your local database.
3. Ensure MongoDB is available at `localhost:27017` or update the notebook connection.
4. Keep secrets out of Git history; rotate any credentials or tokens previously committed or shared.

> **Important:** The uploaded code does **not yet** read credentials from environment variables. Simply setting environment variables without updating the code will not change its connection settings.

### 4. Run the data pipeline

Launch the notebook:

```bash
jupyter notebook "Data Engineering group project (302).ipynb"
```

Run the notebook's data-processing cells in sequence. The pipeline:

1. Clears the existing `collisions` and `weather` collections in the local MongoDB database named `apan5400`.
2. Retrieves collision records for 2021–2024 from NYC Open Data in paginated batches.
3. Downloads NOAA observations month by month, including retry handling for certain HTTP errors.
4. Reshapes daily weather measurements into one record per date and converts selected weather values to Fahrenheit or inches.
5. Builds pandas DataFrames, selects collision columns, and writes intermediate JSON outputs.
6. Writes the DataFrames to PostgreSQL tables named `collisions` and `weather` using `if_exists="replace"`.

**Caution:** Running this notebook can **delete existing MongoDB collection data and replace PostgreSQL tables** with the same names. Use a dedicated project database or back up your data first. API extraction may also take time and depend on rate limits or source availability.

### 5. Start the Flask application

Keep the GeoJSON file in the working directory alongside the Python app, since the map route opens it using a relative file path. Then start the server:

```bash
python3 "Class_app (1).py"
```

Open **http://127.0.0.1:5000/** in a browser. Use the landing-page links to explore the dashboards.

The Flask app runs with `debug=True` in the uploaded code, which is intended for **local development only**, not production deployment.

## Data Processing Notes

- Collision records are filtered to the dates **2021-01-01 through 2024-12-31** during API extraction.
- The notebook selects crash date/time, borough, ZIP code, geographic coordinates, street, and injury/fatality count fields if available.
- The weather extraction requests NOAA's `GHCND` dataset for a single configured station and reorganizes observations by date.
- The ZIP-code map joins collisions to weather on the crash date and then uses `feature.properties.postalCode` to associate collision counts with GeoJSON polygons.
- The weather dashboard joins daily borough collision counts to daily weather observations by date. Missing precipitation/snowfall values are filled with zero, and missing temperature values are filled with the median, before weather categories are assigned.

## Limitations

- **Descriptive analysis:** Differences between collision counts on dry, wet, and snowy days do not prove that weather caused those differences.
- **Counts vs. rates:** Visualizations show raw collision counts or average counts per observed day, not measures adjusted for traffic volume or driving exposure.
- **Geography:** The map requires valid collision ZIP codes matching the GeoJSON's `postalCode` identifiers; missing and unmatched ZIP codes are not represented by shaded regions.
- **Weather coverage:** Weather measurements come from one NOAA station and may not capture conditions uniformly across all boroughs.
- **Missing weather observations:** Filling missing precipitation or snowfall with zero can classify unavailable weather data as dry.
- **Local configuration:** The current implementation expects local databases, pre-populated tables, and the GeoJSON file in the working directory.

## Potential Enhancements

- Move settings and secrets to environment variables and provide an `.env.example`.
- Add a pinned `requirements.txt` and database initialization scripts.
- Improve API pagination and logging, and add incremental loading rather than replacing whole tables.
- Add automated data validation, including ZIP-code matching and weather completeness checks.
- Normalize collision counts by traffic exposure where reliable data is available.
- Deploy the app with a production-ready server and external database configuration.

## Data Attribution

Collision data: **NYC Open Data — Motor Vehicle Collisions: Crashes**. Weather data: **NOAA National Centers for Environmental Information (NCEI)**. Geographic boundaries: supplied **NYC ZIP Code Tabulation Areas GeoJSON**.
