import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Layout Config
st.set_page_config(page_title="Fremont Ultimate Mobility Framework", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    h1 { color: #0F2C59; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 800; }
    h2, h3 { color: #1E2022; font-family: 'Helvetica Neue', Arial, sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #0284C7; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("FREMONT BRIDGE ACTIVE MOBILITY ANALYTICS")
st.markdown("### Executive Planning & Data-Driven Infrastructure Control Deck")
st.markdown("---")

@st.cache_data
def load_dashboard_data():
    df = pd.read_csv("fremont_cleaned.csv")
    df['Date'] = pd.to_datetime(df['Date'])

    if 'Rush_Hour_Flag' not in df.columns:
        df['Rush_Hour_Flag'] = np.where(
            (df['Is_Weekend'] == 'Weekday') & 
            (((df['Hour'] >= 7) & (df['Hour'] <= 9)) | 
             ((df['Hour'] >= 16) & (df['Hour'] <= 18))),
            'Rush Hour', 'Off-Peak'
        )
    if 'Time_of_Day_Bucket' not in df.columns:
        def assign_time_bucket(hour):
            if 5 <= hour <= 11: return 'Morning'
            elif 12 <= hour <= 16: return 'Afternoon'
            elif 17 <= hour <= 21: return 'Evening'
            else: return 'Night'
        df['Time_of_Day_Bucket'] = df['Hour'].apply(assign_time_bucket)
    return df

try:
    df_cleaned = load_dashboard_data()

    # Sidebar Filters
    st.sidebar.header("🕹️ Controls & Filters")
    min_date = df_cleaned['Date'].min().date()
    max_date = df_cleaned['Date'].max().date()

    selected_dates = st.sidebar.date_input(
        "Date Constraints Range", 
        [min_date, max_date],
        format="DD/MM/YYYY"
    )

    traffic_profile = st.sidebar.selectbox(
        "Traffic Profiler Filter Profile", 
        ["Show All Traffic Volume", "Weekday Commuters Only", "Weekend Leisure Only"]
    )

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = df_cleaned[(df_cleaned['Date'].dt.date >= start_date) & (df_cleaned['Date'].dt.date <= end_date)]
        start_str = start_date.strftime('%d/%m/%Y')
        end_str = end_date.strftime('%d/%m/%Y')
        st.info(f"📅 Active Analysis Window Filtered From: **{start_str}** to **{end_str}**")
    else:
        filtered_df = df_cleaned.copy()
        st.info(f"📅 Active Analysis Window Filtered From: **{min_date.strftime('%d/%m/%Y')}** to **{max_date.strftime('%d/%m/%Y')}**")

    if traffic_profile == "Weekday Commuters Only":
        filtered_df = filtered_df[filtered_df['Is_Weekend'] == 'Weekday']
    elif traffic_profile == "Weekend Leisure Only":
        filtered_df = filtered_df[filtered_df['Is_Weekend'] == 'Weekend']

    # KPI Summary Cards
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Total Documented Crossings", f"{int(filtered_df['Total_Count'].sum()):,}")
    with kpi2:
        st.metric("Average Hourly Passing Rate", f"{round(filtered_df['Total_Count'].mean(), 1)} riders/hr")
    with kpi3:
        st.metric("Busiest Recorded Peak Hour Volume", f"{int(filtered_df['Total_Count'].max()):,} riders")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section A: Baseline Visualizations
    st.markdown("## Core Dataset Baseline Performance Metrics")

    # 1. Timeline Chart
    st.subheader("1. Long-Term Cycling Growth Trends")
    daily_trends = filtered_df.set_index('Date').resample('D')[['Total_Count']].sum().reset_index()
    fig_macro = px.line(daily_trends, x='Date', y='Total_Count', color_discrete_sequence=['#1E3A8A'])
    fig_macro.update_layout(
        template='plotly_white', 
        height=420, 
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(rangeslider=dict(visible=True), type="date")
    )
    st.plotly_chart(fig_macro, use_container_width=True)

    # 2 & 3. Hourly & Heatmap Charts
    col_orig1, col_orig2 = st.columns(2)
    with col_orig1:
        st.subheader("2. Busiest Hours: Weekdays vs. Weekends")
        hourly_trends = filtered_df.groupby(['Hour', 'Is_Weekend'])['Total_Count'].mean().reset_index()
        fig_hourly = px.line(hourly_trends, x='Hour', y='Total_Count', color='Is_Weekend', markers=True,
                             color_discrete_sequence=['#10B981', '#F59E0B'])
        fig_hourly.update_layout(template='plotly_white', xaxis=dict(tickmode='linear', dtick=2), height=360)
        st.plotly_chart(fig_hourly, use_container_width=True)

    with col_orig2:
        st.subheader("3. Traffic Intensity Heatmap")
        day_map = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        heatmap_data = filtered_df.groupby(['Day_of_Week', 'Hour'])['Total_Count'].mean().reset_index()
        heatmap_data['Day_Name'] = heatmap_data['Day_of_Week'].map(day_map)
        heatmap_pivot = heatmap_data.pivot(index='Day_Name', columns='Hour', values='Total_Count').reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
        fig_heat = px.imshow(heatmap_pivot, color_continuous_scale='Viridis')
        fig_heat.update_layout(xaxis=dict(tickmode='linear', dtick=2), height=360)
        st.plotly_chart(fig_heat, use_container_width=True)

    # Section B: Targeted Urban Planning Visualizations
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown("## Infrastructure & Policy Planning Analytics")

    # Directional Commute Split & Seasonal Box Plot
    col_plan1, col_plan2 = st.columns(2)

    with col_plan1:
        st.subheader("4. Directional Commute Split (Asymmetric Hourly Usage)")
        dir_trends = filtered_df.groupby('Hour')[['West_Sidewalk_SB', 'East_Sidewalk_NB']].mean().reset_index()
        fig_dir = go.Figure()
        fig_dir.add_trace(go.Scatter(x=dir_trends['Hour'], y=dir_trends['West_Sidewalk_SB'], mode='lines+markers', name='Southbound (West)', line=dict(color='#2563EB')))
        fig_dir.add_trace(go.Scatter(x=dir_trends['Hour'], y=dir_trends['East_Sidewalk_NB'], mode='lines+markers', name='Northbound (East)', line=dict(color='#D97706')))
        fig_dir.update_layout(
            template='plotly_white',
            height=360,
            xaxis=dict(tickmode='linear', dtick=2, title='Hour of Day'),
            yaxis=dict(title='Avg Hourly Cyclist Volume'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_dir, use_container_width=True)


    with col_plan2:
        st.subheader("5. Seasonal Traffic Distribution (Weather Drop-offs)")
        fig_box = px.box(
            filtered_df, 
            x='Season', 
            y='Total_Count', 
            color='Season',
            category_orders={'Season': ['Spring', 'Summer', 'Autumn', 'Winter']},
            color_discrete_map={'Spring': '#10B981', 'Summer': '#F59E0B', 'Autumn': '#D97706', 'Winter': '#3B82F6'}
        )
        fig_box.update_layout(
            template='plotly_white',
            height=360,
            showlegend=False,
            yaxis=dict(title='Hourly Rider Count')
        )
        st.plotly_chart(fig_box, use_container_width=True)


    # Year-over-Year Growth & Rush Hour Donut
    st.markdown("<br>", unsafe_allow_html=True)
    col_plan3, col_plan4 = st.columns(2)

    with col_plan3:
        st.subheader("6. Year-over-Year Overall Traffic Growth")
        yoy_df = filtered_df.copy()
        yoy_df['Year'] = yoy_df['Date'].dt.year
        yearly_summary = yoy_df.groupby('Year')['Total_Count'].sum().reset_index()

        fig_yoy_growth = px.bar(
            yearly_summary, 
            x='Year', 
            y='Total_Count',
            text_auto='.2s',
            color_discrete_sequence=['#0EA5E9']
        )
        fig_yoy_growth.update_layout(
            template='plotly_white',
            height=360,
            xaxis=dict(tickmode='linear', dtick=1),
            yaxis=dict(title='Total Annual Cyclist Volume')
        )
        st.plotly_chart(fig_yoy_growth, use_container_width=True)


    with col_plan4:
        st.subheader("7. Rush Hour vs. Off-Peak Proportion")
        rush_data = filtered_df.groupby('Rush_Hour_Flag')['Total_Count'].sum().reset_index()
        fig_donut = px.pie(
            rush_data, 
            values='Total_Count', 
            names='Rush_Hour_Flag', 
            hole=0.5,
            color_discrete_sequence=['#0284C7', '#CBD5E1']
        )
        fig_donut.update_layout(height=360, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)


    # Section C: Engineered Volatility & Project Effort Features
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.markdown("## Engineered Volatility & Project Operations")

    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        st.subheader("8. Daily Traffic Volatility Index (Standard Deviation)")
        vol_data = filtered_df.groupby('Day_Name')['Total_Count'].std().reset_index().rename(columns={'Total_Count': 'Volatility_SD'})
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        vol_data['Day_Name'] = pd.Categorical(vol_data['Day_Name'], categories=day_order, ordered=True)
        vol_data = vol_data.sort_values('Day_Name')
        fig_vol = px.line(vol_data, x='Day_Name', y='Volatility_SD', markers=True, color_discrete_sequence=['#EF4444'])
        fig_vol.update_layout(height=350, template='plotly_white', yaxis_title="Standard Deviation (Sigma)")
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_adv2:
        st.subheader("9. Project Management Effort Allocation Matrix")
        effort_df = pd.DataFrame({
            'Task Phase Area': ['Data Wrangling', 'Feature Extraction', 'Dashboard Formulation', 'Technical Report Writeup'],
            'Hours Accounted Log': [6, 4, 12, 8]
        })
        fig_effort = px.bar(effort_df, x='Task Phase Area', y='Hours Accounted Log', color='Task Phase Area',
                            color_discrete_sequence=['#1E3A8A', '#0D9488', '#B45309', '#6B21A8'], text='Hours Accounted Log')
        fig_effort.update_layout(template='plotly_white', showlegend=False, height=350)
        st.plotly_chart(fig_effort, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard application components: {e}")
