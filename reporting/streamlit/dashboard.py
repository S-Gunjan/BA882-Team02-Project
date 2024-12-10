import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import base64
from streamlit_lottie import st_lottie
import json
from google.cloud import secretmanager

# Secret manager and database connection setup
project_id = 'group2-ba882'
region_id = "us-east-1"
secret_id = 'project_key'
version_id = 'latest'
db = 'city_services_boston'
schema = "stage"
db_schema = f"{db}.{schema}"

# Secret manager setup
sm = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
response = sm.access_secret_version(request={"name": name})
db_token = response.payload.data.decode("UTF-8")
conn = duckdb.connect(f'md:?token={db_token}')

# Load Lottie animation
# def load_lottiefile(filepath: str):
#     with open(filepath, "r") as f:
#         return json.load(f)

# Background image loading
# def load_background_image(image_file):
#     with open(image_file, "rb") as f:
#         data = base64.b64encode(f.read()).decode()
#     return data

# Fetch service request types from DuckDB
def get_request_types():
    query = "SELECT DISTINCT type FROM city_services_boston.stage.case_duration"
    types_df = conn.execute(query).df()
    return types_df['type'].tolist()

# Set page config
#st.set_page_config(page_title="Boston 311 Analytics Dashboard", layout="wide")

# Load and encode background image
#background_image = load_background_image("boston_skyline.jpg")

# Apply Boston styling
st.markdown(f"""
<style>
.stApp {{
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}
body {{
    color: white;
}}
.stSelectbox {{
    color: white;
}}
.stButton>button {{
    color: white;
    background-color: #CC0000;
    border-color: #CC0000;
}}
.stButton>button:hover {{
    color: white;
    background-color: #990000;
    border-color: #990000;
}}
.css-1d391kg {{
    background-color: rgba(0, 0, 0, 0.05);
}}
[data-testid="stDataFrame"] {{
    width: 80% !important;
    margin: auto;
}}
.block-container {{
    max-width: 1200px;
    padding-top: 1rem;
    padding-bottom: 1rem;
    margin: auto;
}}
</style>
""", unsafe_allow_html=True)

# Boston logo and title
#st.image("https://www.boston.gov/sites/default/files/img/b/boston-black.svg", width=100)
st.write("""<h1 style="color:white;">Boston 311 Analytics Dashboard</h1>""", unsafe_allow_html=True)

# Load Lottie animation
# Replace animation with text
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h2 style='text-align: center;'>Welcome to Boston City Services</h2>", unsafe_allow_html=True)

# Create dashboard tabs
tab1, tab2, tab3 = st.tabs(["Service Request Types 📊", "Response Time Analysis ⏱️", "Neighborhood Insights 🏙️"])

with tab1:
    st.header('Top Service Request Types')
    
    # Date range filter
    date_range = st.date_input("Select Date Range", [pd.to_datetime('2024-01-01'), pd.to_datetime('2024-12-31')])
    
    # Query for top service request types
    query = f"""
    SELECT type, COUNT(*) as count
    FROM city_services_boston.stage.requests
    WHERE open_dt BETWEEN '{date_range[0]}' AND '{date_range[1]}'
    GROUP BY type
    ORDER BY count DESC
    LIMIT 10
    """
    top_types = conn.execute(query).df()
    
    # Create bar chart
    fig = px.bar(top_types, x='count', y='type', orientation='h',
                 title='Top 10 Service Request Types',
                 labels={'count': 'Number of Requests', 'type': 'Request Type'},
                 color_discrete_sequence=['#CC0000'])
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig)

with tab2:
    st.header('Response Time Analysis')
    
    # Service type filter
    service_types = get_request_types()
    selected_type = st.selectbox("Select Service Type", service_types)
    
    # Query for response times
    query = f"""
    SELECT 
        DATE_TRUNC('month', open_dt) as month,
        AVG(DATEDIFF('hour', open_dt, closed_dt)) as avg_response_time
    FROM city_services_boston.stage.response_time
    WHERE type = '{selected_type}'
    GROUP BY month
    ORDER BY month
    """
    response_times = conn.execute(query).df()
    
    # Create line chart
    fig = px.line(response_times, x='month', y='avg_response_time',
                  title=f'Average Response Time for {selected_type}',
                  labels={'month': 'Month', 'avg_response_time': 'Average Response Time (hours)'},
                  color_discrete_sequence=['#CC0000'])
    st.plotly_chart(fig)

with tab3:
    st.header('Neighborhood Insights')
    
    # Query for neighborhood data
    query = """
    SELECT neighborhood, COUNT(*) as count
    FROM city_services_boston.stage.loctions
    GROUP BY neighborhood
    ORDER BY count DESC
    """
    neighborhood_data = conn.execute(query).df()
    
    # Create choropleth map
    fig = px.choropleth(neighborhood_data,
                        geojson="https://raw.githubusercontent.com/codeforboston/boston-neighborhoods/main/boston_neighborhoods.geojson",
                        locations='neighborhood',
                        color='count',
                        featureidkey="properties.Name",
                        color_continuous_scale="Reds",
                        title='Service Requests by Neighborhood')
    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig)

    # Top 5 neighborhoods table
    st.subheader("Top 5 Neighborhoods by Service Requests")
    st.table(neighborhood_data.head())