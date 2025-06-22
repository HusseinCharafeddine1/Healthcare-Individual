# streamlit_app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

# Load data
df = pd.read_excel(r"cleaned_data.xlsx")
df['PServdate'] = pd.to_datetime(df['PServdate'], errors='coerce')

# --- Utility Functions ---
def get_season(date):
    if pd.isnull(date): return None
    month = date.month
    if month in [12, 1, 2]: return 'Winter'
    elif month in [3, 4, 5]: return 'Spring'
    elif month in [6, 7, 8]: return 'Summer'
    elif month in [9, 10, 11]: return 'Fall'

def plot_service_by_sex():
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.countplot(data=df, y='ServName', hue='patsex', order=df['ServName'].value_counts().index, ax=ax)
    ax.set_title('Service Name Counts by Sex')
    st.pyplot(fig)

def plot_avg_age_per_service():
    avg_age = df.groupby('ServName')['PatAge'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=avg_age.values, y=avg_age.index, palette='viridis', ax=ax)
    ax.set_title('Average Age per Medical Service')
    st.pyplot(fig)

def plot_age_dist_by_service_nationality():
    service = st.selectbox("Select Service", df['ServName'].dropna().unique())
    nationality = st.selectbox("Select Nationality", df['nationality'].dropna().unique())
    filtered = df[(df['ServName'] == service) & (df['nationality'] == nationality)]
    if filtered.empty:
        st.warning("No data for this selection.")
    else:
        fig, ax = plt.subplots()
        sns.histplot(filtered['PatAge'], kde=True, bins=15, color='skyblue', ax=ax)
        ax.set_title(f"Age Distribution for {service} ({nationality})")
        st.pyplot(fig)

def plot_south_lebanon_top_services():
    coords = {
        'Dar De Ghaya': (33.2267, 35.3317),
        'Ankoun': (33.3648, 35.3033),
        'Tyre': (33.2730, 35.1939)
    }
    south_df = df[df['cntname'].isin(coords.keys())].copy()
    top5_services = (
        south_df.groupby('cntname')['ServName']
        .value_counts().groupby(level=0, group_keys=False)
        .nlargest(5).reset_index(name='Count').rename(columns={'cntname': 'city'})
    )
    m = folium.Map(location=[33.3, 35.3], zoom_start=10)
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in top5_services.iterrows():
        city = row['city']
        lat, lon = coords[city]
        offset = 0.005 * top5_services[top5_services['city'] == city].index.get_loc(_)
        folium.Marker(
            location=(lat + offset, lon),
            popup=f"{city}<br>{row['ServName']}: {row['Count']}",
            icon=folium.Icon(color='blue')
        ).add_to(marker_cluster)
    folium_static(m)

def plot_family_service_bar():
    family_num = st.slider("Select Family Number", min_value=0, max_value=10, step=1)
    filtered = df[df['FamilyNbr'] == family_num]
    if filtered.empty:
        st.warning("No data for selected family.")
    else:
        top_services = filtered['ServName'].value_counts().head(5).reset_index()
        top_services.columns = ['ServName', 'Count']
        fig, ax = plt.subplots()
        sns.barplot(data=top_services, x='ServName', y='Count', palette='Set2', ax=ax)
        ax.set_title(f"Top 5 Services for Family {family_num}")
        st.pyplot(fig)

def plot_services_by_season():
    df['Season'] = df['PServdate'].apply(get_season)
    top_services = df.groupby(['Season', 'ServName']).size().reset_index(name='Count')
    top5 = top_services.sort_values(['Season', 'Count'], ascending=[True, False]).groupby('Season').head(5)
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.barplot(data=top5, x='ServName', y='Count', hue='Season', ax=ax)
    ax.set_title("Top 5 Medical Services per Season")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title("Healthcare Data Visualizations")

visual_options = {
    "1. Service Name Count by Sex": plot_service_by_sex,
    "2. Average Age per Service": plot_avg_age_per_service,
    "3. Age Distribution (Service vs Nationality)": plot_age_dist_by_service_nationality,
    "4. Top 5 Services in South Lebanon (Map)": plot_south_lebanon_top_services,
    "5. Top Services by Family Number": plot_family_service_bar,
    "6. Top 5 Services per Season": plot_services_by_season
}

selected_visual = st.sidebar.selectbox("Choose a Visualization", list(visual_options.keys()))
visual_options[selected_visual]()
