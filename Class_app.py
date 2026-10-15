from flask import Flask, jsonify, render_template_string, request
from sqlalchemy import create_engine, text
import pandas as pd
import folium
from folium.features import GeoJsonTooltip
from folium.plugins import Fullscreen
from sqlalchemy import text
import psycopg


POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "123"
POSTGRES_DB = "postgres"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"

DB_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DB_URL)

app = Flask(__name__)


# Main landing page
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NYC Dashboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            h1 {
                margin-bottom: 10px;
            }
            .button-link {
                display: inline-block;
                background-color: #1e6bd3;   
                color: white;
                padding: 10px 16px;
                margin: 6px 0;
                border-radius: 6px;
                text-decoration: none;
                font-weight: bold;
                transition: background-color 0.2s ease;
            }
            .button-link:hover {
                background-color: #1554a1;   
            }
            ul { list-style-type: none; padding-left: 0; }
            li { margin-bottom: 8px; }
        </style>
    </head>
    <body>
        <h1>NYC Collisions & Weather Dashboard</h1>
        <p>Backend is running and connected to PostgreSQL</p>

        <ul>
          <li><a class="button-link" href="/api/collisions_by_borough">API: Collisions by borough (JSON)</a></li>
          <li><a class="button-link" href="/dashboard">Dashboard view (borough collisions)</a></li>
          <li><a class="button-link" href="/dashboard_year">Dashboard: Collisions per Year</a></li>
          <li><a class="button-link" href="/heatmap_zip">Collision Heatmap</a></li>
          <li><a class="button-link" href="/dashboard_weather_effects">Dashboard: Weather effects on collisions</a></li>
        </ul>
    </body>
    </html>
    """
#<li><a href="/heatmap">Dashboard view: Collisions per Area</a></li>

# Collisions by borough
@app.route("/api/collisions_by_borough")
def collisions_by_borough():
    query = """
        SELECT borough,
               COUNT(*) AS collision_count
        FROM collisions
        WHERE borough IS NOT NULL AND borough <> ''
        GROUP BY borough
        ORDER BY collision_count DESC;
    """
    df = pd.read_sql(text(query), engine)
    return df.to_json(orient="records")


#Basic dashboard
@app.route("/dashboard")
def dashboard():
    query = """
        SELECT borough,
               COUNT(*) AS collision_count
        FROM collisions
        WHERE borough IS NOT NULL AND borough <> ''
        GROUP BY borough
        ORDER BY collision_count DESC;
    """
    df = pd.read_sql(text(query), engine)


    template = """
    <!doctype html>
    <html>
    <head>
      <title>NYC Collisions Dashboard</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
      <h1>NYC Collisions by Borough</h1>
      <canvas id="collisionsChart" width="600" height="300"></canvas>

      <h2>Data Table</h2>
      {{ table | safe }}

      <script>
        const labels = {{ labels | safe }};
        const data = {{ values | safe }};

        const ctx = document.getElementById('collisionsChart').getContext('2d');
        const chart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Collisions',
              data: data
            }]
          },
          options: {
            responsive: true,
            scales: {
              y: {
                beginAtZero: true
              }
            }
          }
        });
      </script>
    </body>
    </html>
    """

    labels = df["borough"].tolist()
    values = df["collision_count"].tolist()
    table_html = df.to_html(index=False)

    return render_template_string(
        template,
        labels=labels,
        values=values,
        table=table_html,
    )

#############################################################
@app.route("/dashboard_year")
def dashboard_year():

    #by borough
    query_borough = """
        SELECT borough,
               COUNT(*) AS collision_count
        FROM collisions
        WHERE borough IS NOT NULL AND borough <> ''
        GROUP BY borough
        ORDER BY collision_count DESC;
    """
    df_borough = pd.read_sql(text(query_borough), engine)

    #by year
    query_year = """
        SELECT EXTRACT(YEAR FROM crash_date::DATE) AS year,
               COUNT(*) AS collision_count
        FROM collisions
        WHERE crash_date IS NOT NULL
        GROUP BY year
        ORDER BY year;
    """
    df_year = pd.read_sql(text(query_year), engine)
    df_year["year"] = df_year["year"].astype(int)


    template = """
    <!doctype html>
    <html>
    <head>
      <title>NYC Collisions Dashboard</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
      <h1>NYC Collisions Dashboard</h1>

      <h2>Collisions by Borough</h2>
      <canvas id="boroughChart" width="600" height="300"></canvas>
      {{ borough_table | safe }}

      <h2>Collisions per Year</h2>
      <canvas id="yearChart" width="600" height="300"></canvas>
      {{ year_table | safe }}

      <script>
        // --- Borough Chart ---
        const boroughLabels = {{ borough_labels | safe }};
        const boroughData = {{ borough_values | safe }};
        const ctxBorough = document.getElementById('boroughChart').getContext('2d');
        new Chart(ctxBorough, {
          type: 'bar',
          data: {
            labels: boroughLabels,
            datasets: [{ label: 'Collisions', data: boroughData }]
          },
          options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        // --- Year Chart ---
        const yearLabels = {{ year_labels | safe }};
        const yearData = {{ year_values | safe }};
        const ctxYear = document.getElementById('yearChart').getContext('2d');
        new Chart(ctxYear, {
          type: 'bar',
          data: {
            labels: yearLabels,
            datasets: [{ label: 'Collisions per Year', data: yearData }]
          },
          options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });
      </script>
    </body>
    </html>
    """

    return render_template_string(
        template,
        #Borough data
        borough_labels=df_borough["borough"].tolist(),
        borough_values=df_borough["collision_count"].tolist(),
        borough_table=df_borough.to_html(index=False),
        #Year data
        year_labels=df_year["year"].tolist(),
        year_values=df_year["collision_count"].tolist(),
        year_table=df_year.to_html(index=False),
    )

@app.route("/heatmap_zip")
def heatmap_zip():
    weather_filter = request.args.get("weather", "all")

    weather_condition = ""
    if weather_filter == "clear":
        weather_condition = "AND w.precipitation_in = 0 AND w.snowfall_in = 0"
    elif weather_filter == "rain":
        weather_condition = "AND w.precipitation_in > 0 AND w.snowfall_in = 0"
    elif weather_filter == "snow":
        weather_condition = "AND w.snowfall_in > 0"

    query = f"""
        SELECT c.zip_code,
               COUNT(*) AS collision_count
        FROM collisions c
        LEFT JOIN weather w
           ON c.crash_date::date = w.date::date
        WHERE c.zip_code IS NOT NULL 
          AND c.zip_code <> ''
          {weather_condition}
        GROUP BY c.zip_code;
    """

    df = pd.read_sql(text(query), engine)
    df["zip_code"] = df["zip_code"].astype(str).str.strip()

    # Load GeoJSON
    import json
    with open("nyc-zip-code-tabulation-areas-polygons.geojson", "r") as f:
        nyc_zip_geojson = json.load(f)

    # Create map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=10, tiles="cartodbpositron")
    Fullscreen().add_to(m)

    folium.Choropleth(
        geo_data=nyc_zip_geojson,
        name="Collision count by ZIP",
        data=df,
        columns=["zip_code", "collision_count"],
        key_on="feature.properties.postalCode",
        fill_color="YlOrRd",
        fill_opacity=0.8,
        line_opacity=0.3,
        legend_name="Number of Collisions",
        highlight=True,
    ).add_to(m)

    folium.GeoJson(
        nyc_zip_geojson,
        name="zip_tooltip",
        style_function=lambda feature: {
            "weight": 0.5,
            "color": "gray",
            "opacity": 0.25,
            "fillOpacity": 0
        },
        tooltip=GeoJsonTooltip(
            fields=["postalCode"],
            aliases=["ZIP Code:"],
            sticky=True,
            permanent=False
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>NYC Collisions by ZIP</title>

      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 0;
          padding: 0;
        }

        .filter-bar {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          background: white;
          padding: 12px 20px;
          z-index: 9999; 
          border-bottom: 1px solid #ccc;
        }

        
        .map-container {
          margin-top: 70px;
        }

        select {
          padding: 8px;
          font-size: 16px;
        }

        button {
          padding: 8px 14px;
          font-size: 16px;
          margin-left: 5px;
          background-color: #1e6bd3; 
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }

        button:hover {
          opacity: 0.9;
        }
      </style>
    </head>

    <body>

      <div class="filter-bar">
        <form method="get">
          <label for="weather"><strong>Weather Filter:</strong></label>
          <select name="weather" id="weather">
            <option value="all"   {% if weather=='all' %}selected{% endif %}>All</option>
            <option value="clear" {% if weather=='clear' %}selected{% endif %}>Clear</option>
            <option value="rain"  {% if weather=='rain' %}selected{% endif %}>Rain</option>
            <option value="snow"  {% if weather=='snow' %}selected{% endif %}>Snow</option>
          </select>
          <button type="submit">Update</button>
        </form>
      </div>

      <div class="map-container">
        {{ map_html | safe }}
      </div>

      <p style="padding: 15px;">
        <a href="/">Back to Home</a>
      </p>

    </body>
    </html>
    """, map_html=m._repr_html_(), weather=weather_filter)

@app.route("/dashboard_weather_effects")
def dashboard_weather_effects():
    query = """
        WITH daily_collisions AS (
            SELECT
                crash_date::date AS day,
                borough,
                COUNT(*) AS collisions
            FROM collisions
            WHERE borough IS NOT NULL AND borough <> ''
            GROUP BY day, borough
        ),
        daily_weather AS (
            SELECT
                "date"::date AS day,
                AVG(precipitation_in) AS precipitation_in,
                AVG(snowfall_in) AS snow_in,
                AVG(max_temp_f) AS temperature_f
            FROM weather
            GROUP BY day
        )
        SELECT
            c.day,
            c.borough,
            c.collisions,
            w.precipitation_in,
            w.snow_in,
            w.temperature_f
        FROM daily_collisions c
        LEFT JOIN daily_weather w ON c.day = w.day
        WHERE c.day IS NOT NULL
        ORDER BY c.day, c.borough;
    """

    df = pd.read_sql(text(query), engine)

    #clear missing data
    df["precipitation_in"] = df["precipitation_in"].fillna(0)
    df["snow_in"] = df["snow_in"].fillna(0)
    df["temperature_f"] = df["temperature_f"].fillna(df["temperature_f"].median())


    df["weather_type"] = "Dry"
    df.loc[df["snow_in"] > 0, "weather_type"] = "Snow"
    df.loc[(df["precipitation_in"] > 0) & (df["snow_in"] == 0), "weather_type"] = "Wet (Rain)"


    weather_summary = (
        df.groupby(["borough", "weather_type"])["collisions"]
        .mean()
        .unstack(fill_value=0)
        .reset_index()
    )


    for col in ["Dry", "Wet (Rain)", "Snow"]:
        if col not in weather_summary.columns:
            weather_summary[col] = 0.0

    weather_summary = weather_summary[["borough", "Dry", "Wet (Rain)", "Snow"]]

    boroughs = weather_summary["borough"].tolist()
    dry_values = weather_summary["Dry"].round(2).tolist()
    wet_values = weather_summary["Wet (Rain)"].round(2).tolist()
    snow_values = weather_summary["Snow"].round(2).tolist()

    weather_table_html = weather_summary.round(2).to_html(index=False)


    template = """
    <!doctype html>
    <html>
    <head>
      <title>Weather Effects on NYC Collisions</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: center; }
        .chart-container { max-width: 950px; margin-bottom: 40px; }
      </style>
    </head>
    <body>

      <h1>Do Weather Conditions Affect NYC Traffic Collisions?</h1>
      <p>
        This dashboard compares <strong>average daily collisions</strong> across three
        <strong>exclusive weather categories</strong>:
        <ul>
          <li><strong>Dry</strong>: no precipitation and no snow</li>
          <li><strong>Wet (Rain)</strong>: precipitation &gt; 0 and no snow</li>
          <li><strong>Snow</strong>: snowfall &gt; 0</li>
        </ul>
      </p>

      <div class="chart-container">
        <h2>Average Daily Collisions by Borough and Weather Type</h2>
        <canvas id="weatherChart"></canvas>
      </div>

      <h3>Summary Table: Avg Daily Collisions by Borough & Weather Type</h3>
      {{ weather_table | safe }}

      <script>
        const boroughs = {{ boroughs | safe }};
        const dryValues = {{ dry_values | safe }};
        const wetValues = {{ wet_values | safe }};
        const snowValues = {{ snow_values | safe }};

        new Chart(document.getElementById('weatherChart'), {
          type: 'bar',
          data: {
            labels: boroughs,
            datasets: [
              { label: 'Dry', data: dryValues },
              { label: 'Wet (Rain)', data: wetValues },
              { label: 'Snow', data: snowValues }
            ]
          },
          options: {
            responsive: true,
            plugins: { legend: { position: 'top' }},
            scales: {
              y: { beginAtZero: true, title: { text: 'Avg Collisions per Day', display: true }},
              x: { title: { text: 'Borough', display: true }}
            }
          }
        });
      </script>

    </body>
    </html>
    """

    return render_template_string(
        template,
        boroughs=boroughs,
        dry_values=dry_values,
        wet_values=wet_values,
        snow_values=snow_values,
        weather_table=weather_table_html,
    )

if __name__ == "__main__":
    app.run(debug=True)
