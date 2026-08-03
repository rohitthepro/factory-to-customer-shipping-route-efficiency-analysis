import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME PRESERVATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Factory-to-Customer Shipping Route Efficiency Dashboard",
    page_icon="🍫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS preserving exact Chocolate Theme, Typography, Cards, and Styling
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #E4DFD9;
    }
    
    /* Hide Default UI Headers & Footers */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global Typography - Georgia Serif */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #3E2723 !important; 
        font-family: 'Georgia', serif !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #E4DFD9;
        border-right: 2px solid #3E2723;
        padding-top: 10px;
    }

    /* Multiselect Tag Styling matching Theme */
    span[data-baseweb="tag"] {
        background-color: #3E2723 !important;
        color: #D4B895 !important;
        border-radius: 4px !important;
        font-weight: bold;
    }
    span[data-baseweb="tag"] span {
        color: #D4B895 !important;
    }

    /* Metric Cards Styling - Restored to original bigger & bolder KPIs */
    div[data-testid="metric-container"] {
        text-align: left;
        padding: 5px 0px;
    }
    div[data-testid="metric-container"] label {
        color: #3E2723 !important;
        font-size: 14px !important;
        font-weight: 900 !important; 
        font-family: 'Georgia', serif;
        text-transform: uppercase;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #3E2723 !important;
        font-size: 40px !important; 
        font-weight: 900 !important; 
        font-family: 'Georgia', serif;
    }

    /* Business Insights Highlight Cards - Restored */
    .insight-card {
        background-color: #3E2723;
        color: #D4B895;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 12px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.15);
    }
    .insight-card h4 {
        color: #FFFFFF !important;
        margin-top: 0;
        margin-bottom: 4px;
        font-size: 15px !important;
        font-weight: bold;
        text-transform: uppercase;
        font-family: 'Georgia', serif;
    }
    .insight-card p {
        color: #D4B895 !important;
        margin: 0;
        font-size: 14px !important;
        font-family: 'Georgia', serif;
    }
    
    /* Table Header & Text Styling - Restored */
    .stDataFrame {
        background-color: #3E2723;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA LOADING & FEATURE ENGINEERING
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_process_data():
    print("--------------------------------------------------")
    print("DEBUGGING: PREPROCESSING STEPS")
    print("--------------------------------------------------")
    
    # Load raw dataset
    df = pd.read_csv('Nassau Candy Distributor.csv')
    print(f"Original Rows: {len(df)}")
    
    # Clean product names to ensure robust matching
    df['Product Name Clean'] = df['Product Name'].astype(str).str.replace('-', ' - ').str.replace('  ', ' ').str.strip()
    
    # 1. Fix Date Parsing using dayfirst=True
    df['Order Date Parsed'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    df['Ship Date Parsed'] = pd.to_datetime(df['Ship Date'], dayfirst=True, errors='coerce')
    print(f"After Date Conversion: {len(df)}")
    
    # Drop records with invalid dates
    df = df.dropna(subset=['Order Date Parsed', 'Ship Date Parsed'])
    print(f"After Removing Invalid Dates: {len(df)}")
    
    # Remove invalid records where Ship Date < Order Date
    df = df[df['Ship Date Parsed'] >= df['Order Date Parsed']]
    print(f"After Removing Ship Date < Order Date: {len(df)}")
    
    # Calculate Lead Time (Days)
    df['Lead Time'] = (df['Ship Date Parsed'] - df['Order Date Parsed']).dt.days
    
    # Temporal Extracts
    df['Order Month'] = df['Order Date Parsed'].dt.strftime('%B')
    df['Order Month Num'] = df['Order Date Parsed'].dt.month
    df['Order Year'] = df['Order Date Parsed'].dt.year
    
    # 2. Complete Product -> Factory Mapping
    factory_mapping_dict = {
        # Lot's O' Nuts
        "Wonka Bar - Nutty Crunch Surprise": ("Lot's O' Nuts", 32.881893, -111.768036),
        "Wonka Bar - Fudge Mallows": ("Lot's O' Nuts", 32.881893, -111.768036),
        "Wonka Bar - Scrumdiddlyumptious": ("Lot's O' Nuts", 32.881893, -111.768036),
        # Wicked Choccy's
        "Wonka Bar - Milk Chocolate": ("Wicked Choccy's", 32.076176, -81.088371),
        "Wonka Bar - Triple Dazzle Caramel": ("Wicked Choccy's", 32.076176, -81.088371),
        # Sugar Shack
        "Laffy Taffy": ("Sugar Shack", 48.119140, -96.181150),
        "SweeTARTS": ("Sugar Shack", 48.119140, -96.181150),
        "Nerds": ("Sugar Shack", 48.119140, -96.181150),
        "Fun Dip": ("Sugar Shack", 48.119140, -96.181150),
        "Fizzy Lifting Drinks": ("Sugar Shack", 48.119140, -96.181150),
        # Secret Factory
        "Everlasting Gobstopper": ("Secret Factory", 41.446333, -90.565487),
        "Lickable Wallpaper": ("Secret Factory", 41.446333, -90.565487),
        "Wonka Gum": ("Secret Factory", 41.446333, -90.565487),
        # The Other Factory
        "Hair Toffee": ("The Other Factory", 35.117500, -89.971107),
        "Kazookles": ("The Other Factory", 35.117500, -89.971107)
    }

    def assign_factory_info(product_str):
        p_str = str(product_str).lower()
        for p_key, info in factory_mapping_dict.items():
            if p_key.lower() in p_str:
                return info
        return ("Unknown Factory", 0.0, 0.0)

    factory_info = df['Product Name Clean'].apply(assign_factory_info)
    df['Factory'] = [f[0] for f in factory_info]
    df['Factory Latitude'] = [f[1] for f in factory_info]
    df['Factory Longitude'] = [f[2] for f in factory_info]
    print(f"After Factory Mapping: {len(df)}")
    
    # Filter out unmapped records if any exist
    df = df[df['Factory'] != "Unknown Factory"]
    print(f"After Filtering Unknown Factory: {len(df)}")
    print(f"Final Dataset: {len(df)}")
    
    # 3. Create Route Information
    df['State/Province'] = df['State/Province'].astype(str).str.title()
    df['Region'] = df['Region'].astype(str).str.title()
    df['Route'] = df['Factory'] + " → " + df['State/Province']
    df['Factory → Region'] = df['Factory'] + " → " + df['Region']
    
    # 4. Calculate Shipping KPIs & Flags
    global_avg_lead = df['Lead Time'].mean()
    df['Delay Flag'] = df['Lead Time'] > global_avg_lead
    
    # Efficiency Score: Min-Max inverted normalization (0-100 scale)
    min_lt = df['Lead Time'].min()
    max_lt = df['Lead Time'].max()
    if max_lt > min_lt:
        df['Route Efficiency Score'] = 100 - ((df['Lead Time'] - min_lt) / (max_lt - min_lt) * 100)
    else:
        df['Route Efficiency Score'] = 100.0

    print("--------------------------------------------------")
    print("DEBUGGING: FINAL METRICS")
    print("--------------------------------------------------")
    print(f"Total Rows: {len(df)}")
    print(f"Unique Orders: {df['Order ID'].nunique()}")
    print(f"Minimum Order Date: {df['Order Date Parsed'].min()}")
    print(f"Maximum Order Date: {df['Order Date Parsed'].max()}")
    print(f"Minimum Ship Date: {df['Ship Date Parsed'].min()}")
    print(f"Maximum Ship Date: {df['Ship Date Parsed'].max()}")
    print(f"Average Lead Time: {df['Lead Time'].mean():.2f}")
    print("--------------------------------------------------")

    return df

# Load processed dataset
df = load_and_process_data()

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTION: PLOTLY DARK CHOCOLATE CHART STYLING
# -----------------------------------------------------------------------------
def style_chart(fig, title_text, subtitle_text="", height=360):
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b><br><span style='font-size:12px; font-style:italic; color:#D4B895;'>{subtitle_text}</span>",
            x=0.5, xanchor='center', y=0.95,
            font=dict(family="Georgia, serif", size=18, color="#FFFFFF")
        ),
        plot_bgcolor='#3E2723',
        paper_bgcolor='#3E2723',
        font_color='#D4B895',
        margin=dict(t=70, b=30, l=30, r=20),
        showlegend=False
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color='#D4B895')
    fig.update_yaxes(showgrid=False, zeroline=False, color='#D4B895')
    return fig

# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & FILTERS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-weight: 900; font-size: 26px; color: #3E2723;'>CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 2px solid #3E2723; margin-top: 0px;'>", unsafe_allow_html=True)
    
    # Date Range Filter (Dynamically based on minimum and maximum order dates)
    min_date = df['Order Date Parsed'].min().date()
    max_date = df['Order Date Parsed'].max().date()
    date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    
    # Factory Filter
    all_factories = sorted(df['Factory'].unique().tolist())
    selected_factory = st.multiselect("Select Factory", options=all_factories, default=all_factories)
    
    # Region Filter
    all_regions = sorted(df['Region'].unique().tolist())
    selected_region = st.multiselect("Select Region", options=all_regions, default=all_regions)
    
    # State Filter
    all_states = sorted(df['State/Province'].unique().tolist())
    selected_state = st.multiselect("Select State", options=all_states, default=all_states)
    
    # Ship Mode Filter
    all_ship_modes = sorted(df['Ship Mode'].unique().tolist())
    selected_ship_mode = st.multiselect("Select Ship Mode", options=all_ship_modes, default=all_ship_modes)
    
    # Lead Time Slider Filter
    min_lt_val = int(df['Lead Time'].min())
    max_lt_val = int(df['Lead Time'].max())
    selected_lt_range = st.slider("Filter Lead Time (Days)", min_value=min_lt_val, max_value=max_lt_val, value=(min_lt_val, max_lt_val))

# Apply Sidebar Filters to Data
filtered_df = df.copy()

# Date filter evaluation (ensuring safe tuple unpacking)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[(filtered_df['Order Date Parsed'].dt.date >= start_d) & (filtered_df['Order Date Parsed'].dt.date <= end_d)]
elif isinstance(date_range, tuple) and len(date_range) == 1:
    start_d = date_range[0]
    filtered_df = filtered_df[filtered_df['Order Date Parsed'].dt.date >= start_d]
elif not isinstance(date_range, tuple):
    filtered_df = filtered_df[filtered_df['Order Date Parsed'].dt.date == date_range]

if selected_factory:
    filtered_df = filtered_df[filtered_df['Factory'].isin(selected_factory)]
if selected_region:
    filtered_df = filtered_df[filtered_df['Region'].isin(selected_region)]
if selected_state:
    filtered_df = filtered_df[filtered_df['State/Province'].isin(selected_state)]
if selected_ship_mode:
    filtered_df = filtered_df[filtered_df['Ship Mode'].isin(selected_ship_mode)]

filtered_df = filtered_df[
    (filtered_df['Lead Time'] >= selected_lt_range[0]) & 
    (filtered_df['Lead Time'] <= selected_lt_range[1])
]

# Ensure dashboard doesn't break on empty filter selection
if filtered_df.empty:
    st.warning("No records match the selected sidebar filters. Please broaden your selection.")
    st.stop()

# -----------------------------------------------------------------------------
# 5. MAIN DASHBOARD LAYOUT (ONE PAGE DESIGN)
# -----------------------------------------------------------------------------

# --- HEADER & KPIs MOVED TO THE TOP ---
st.markdown("<h1 style='text-align: center; font-weight: 900; font-size: 42px; color: #3E2723; line-height: 1.1; margin-bottom: 25px;'>SUPPLY CHAIN DIAGNOSTICS:ROUTE OPTIMIZATION DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<hr style='border-top: 2px solid #3E2723; margin: 0px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# 5. REPLACED CURRENT KPIs (Focused on Shipping Efficiency)
total_orders = len(filtered_df)
total_sales = filtered_df['Sales'].sum()
total_profit = filtered_df['Gross Profit'].sum()
avg_lead_time = filtered_df['Lead Time'].mean()
delay_pct = (filtered_df['Delay Flag'].mean()) * 100
avg_eff_score = filtered_df['Route Efficiency Score'].mean()

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1: st.metric("TOTAL ORDERS", f"{total_orders:,}")
with kpi2: st.metric("TOTAL SALES", f"${total_sales:,.0f}")
with kpi3: st.metric("TOTAL PROFIT", f"${total_profit:,.0f}")
with kpi4: st.metric("AVERAGE LEAD TIME", f"{avg_lead_time:.1f} Days")
with kpi5: st.metric("DELAY %", f"{delay_pct:.1f}%")
with kpi6: st.metric("AVG ROUTE EFFICIENCY SCORE", f"{avg_eff_score:.1f} / 100")

st.markdown("<hr style='border-top: 2px solid #3E2723; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# --- SPLIT LAYOUT: CHARTS/LEADERBOARD (LEFT) AND INSIGHTS (RIGHT) ---
charts_col, insights_col = st.columns([3.2, 1], gap="large")

with charts_col:
    # ROW 1: Geographic Map & Bottleneck Analysis
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        # 7. REPLACED GEOGRAPHIC MAP: Average Lead Time by State (USA Choropleth)
        state_geo = filtered_df.groupby('State/Province').agg(
            Avg_Lead_Time=('Lead Time', 'mean'),
            Order_Count=('Order ID', 'count')
        ).reset_index()
        
        fig_map = px.choropleth(
            state_geo,
            locations='State/Province',
            locationmode="USA-states",
            color='Avg_Lead_Time',
            scope="usa",
            color_continuous_scale=['#3E2723', '#D4B895', '#F5E6D3'],
            hover_data={'State/Province': True, 'Avg_Lead_Time': ':.1f', 'Order_Count': True}
        )
        fig_map = style_chart(fig_map, "Geographic Lead Time Map", "Average shipping lead time (days) by customer state")
        fig_map.update_layout(geo=dict(bgcolor='#3E2723', lakecolor='#3E2723'))
        fig_map.update_traces(hovertemplate="<b>%{location}</b><br>Avg Lead Time: %{z:.1f} Days<br>Orders: %{customdata[1]}<extra></extra>")
        st.plotly_chart(fig_map, use_container_width=True)

    with row1_col2:
        # 10. BOTTLENECK ANALYSIS: Top 10 States with Highest Avg Lead Time
        top_bottlenecks = state_geo.sort_values('Avg_Lead_Time', ascending=True).tail(10)
        fig_bottle = px.bar(
            top_bottlenecks,
            x='Avg_Lead_Time',
            y='State/Province',
            orientation='h',
            text_auto='.1f',
            color_discrete_sequence=['#D4B895']
        )
        fig_bottle = style_chart(fig_bottle, "Top 10 State Bottlenecks", "Destination states experiencing highest average transit delays")
        fig_bottle.update_traces(
            textfont=dict(color='#FFFFFF', size=11),
            textposition='outside',
            hovertemplate="<b>State: %{y}</b><br>Avg Lead Time: %{x:.1f} Days<extra></extra>"
        )
        fig_bottle.update_xaxes(title_text="Avg Lead Time (Days)")
        fig_bottle.update_yaxes(title_text="")
        st.plotly_chart(fig_bottle, use_container_width=True)

    # ROW 2: Route Analysis & Ship Mode Analysis
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        # 11. ROUTE ANALYSIS: Horizontal Bar Chart (Factory -> State Avg Lead Time)
        route_lead = filtered_df.groupby('Route').agg(
            Avg_Lead_Time=('Lead Time', 'mean'),
            Shipments=('Order ID', 'count')
        ).reset_index().sort_values('Avg_Lead_Time', ascending=True).tail(10)
        
        fig_route = px.bar(
            route_lead,
            x='Avg_Lead_Time',
            y='Route',
            orientation='h',
            text_auto='.1f',
            color_discrete_sequence=['#F5E6D3']
        )
        fig_route = style_chart(fig_route, "Slowest Shipping Routes", "Top 10 Factory → State routes with longest average lead times")
        fig_route.update_traces(
            textfont=dict(color='#FFFFFF', size=11),
            textposition='outside',
            hovertemplate="<b>Route: %{y}</b><br>Avg Lead Time: %{x:.1f} Days<extra></extra>"
        )
        fig_route.update_xaxes(title_text="Avg Lead Time (Days)")
        fig_route.update_yaxes(title_text="")
        st.plotly_chart(fig_route, use_container_width=True)

    with row2_col2:
        # 9. SHIP MODE ANALYSIS: Comparison Chart (Avg Lead Time & Shipment Count)
        ship_mode_df = filtered_df.groupby('Ship Mode').agg(
            Avg_Lead_Time=('Lead Time', 'mean'),
            Avg_Sales=('Sales', 'mean'),
            Avg_Profit=('Gross Profit', 'mean'),
            Shipment_Count=('Order ID', 'count')
        ).reset_index()
        
        fig_ship = px.bar(
            ship_mode_df,
            x='Ship Mode',
            y='Avg_Lead_Time',
            text_auto='.1f',
            color_discrete_sequence=['#D4B895']
        )
        fig_ship = style_chart(fig_ship, "Ship Mode Performance", "Comparing average lead time across shipping carriers/modes")
        fig_ship.update_traces(
            textfont=dict(color='#FFFFFF', size=11),
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>Avg Lead Time: %{y:.1f} Days<extra></extra>"
        )
        fig_ship.update_xaxes(title_text="")
        fig_ship.update_yaxes(title_text="Avg Lead Time (Days)")
        st.plotly_chart(fig_ship, use_container_width=True)

    # ROW 3: Factory Analysis, Delay Distribution, Monthly Analysis
    row3_col1, row3_col2, row3_col3 = st.columns([1, 1, 1])
    
    with row3_col1:
        # 12. IMPROVED FACTORY ANALYSIS: Orders, Avg Lead Time, Avg Profit
        fac_df = filtered_df.groupby('Factory').agg(
            Orders=('Order ID', 'count'),
            Avg_Lead_Time=('Lead Time', 'mean'),
            Avg_Profit=('Gross Profit', 'mean')
        ).reset_index()
        
        fig_fac = px.bar(
            fac_df,
            x='Factory',
            y='Orders',
            text_auto=True,
            color_discrete_sequence=['#D4B895']
        )
        fig_fac = style_chart(fig_fac, "Factory Dispatch Volume", "Order volume and performance per manufacturing location")
        fig_fac.update_traces(
            textfont=dict(color='#FFFFFF', size=11),
            textposition='outside',
            hovertemplate="<b>Factory: %{x}</b><br>Orders: %{y}<extra></extra>"
        )
        fig_fac.update_xaxes(title_text="", tickangle=-20)
        fig_fac.update_yaxes(title_text="Total Orders")
        st.plotly_chart(fig_fac, use_container_width=True)

    with row3_col2:
        # 13. DELAY DISTRIBUTION: Histogram of Lead Time
        fig_hist = px.histogram(
            filtered_df,
            x='Lead Time',
            nbins=30,
            color_discrete_sequence=['#F5E6D3']
        )
        fig_hist = style_chart(fig_hist, "Lead Time Distribution", "Frequency distribution of order fulfillment lead times")
        fig_hist.update_traces(
            hovertemplate="<b>Lead Time Interval: %{x} Days</b><br>Order Count: %{y}<extra></extra>"
        )
        fig_hist.update_xaxes(title_text="Lead Time (Days)")
        fig_hist.update_yaxes(title_text="Frequency")
        st.plotly_chart(fig_hist, use_container_width=True)

    with row3_col3:
        # 14. MONTHLY ANALYSIS: Monthly Revenue & Avg Monthly Lead Time
        monthly_df = filtered_df.groupby(['Order Month Num', 'Order Month']).agg(
            Sales=('Sales', 'sum'),
            Avg_Lead_Time=('Lead Time', 'mean')
        ).reset_index().sort_values('Order Month Num')
        
        fig_month = px.line(
            monthly_df,
            x='Order Month',
            y='Avg_Lead_Time',
            markers=True,
            color_discrete_sequence=['#D4B895']
        )
        fig_month = style_chart(fig_month, "Monthly Lead Time Trend", "Average transit lead time across order months")
        fig_month.update_traces(
            marker=dict(size=7, color='#F5E6D3'),
            line=dict(width=2.5),
            hovertemplate="<b>%{x}</b><br>Avg Lead Time: %{y:.1f} Days<extra></extra>"
        )
        fig_month.update_xaxes(title_text="", tickangle=-30)
        fig_month.update_yaxes(title_text="Avg Days")
        st.plotly_chart(fig_month, use_container_width=True)

    # -----------------------------------------------------------------------------
    # ROUTE LEADERBOARD SECTION (INSIDE LEFT COLUMN)
    # -----------------------------------------------------------------------------
    st.markdown("<h3 style='font-weight: 900; font-size: 22px; color: #3E2723; margin-top: 15px;'>ROUTE EFFICIENCY LEADERBOARD</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 2px solid #3E2723; margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    route_leaderboard = filtered_df.groupby('Route').agg(
        Avg_Lead_Time=('Lead Time', 'mean'),
        Shipment_Count=('Order ID', 'count'),
        Efficiency_Score=('Route Efficiency Score', 'mean')
    ).reset_index()

    lead_col1, lead_col2 = st.columns(2)

    with lead_col1:
        st.markdown("<h4 style='font-weight: bold; font-size: 16px; color: #2E7D32;'>⚡ Top 10 Fastest Shipping Routes</h4>", unsafe_allow_html=True)
        top_fastest = route_leaderboard.sort_values('Avg_Lead_Time', ascending=True).head(10)
        top_fastest['Avg_Lead_Time'] = top_fastest['Avg_Lead_Time'].round(1)
        top_fastest['Efficiency_Score'] = top_fastest['Efficiency_Score'].round(1)
        st.dataframe(
            top_fastest.rename(columns={
                'Route': 'Route (Factory → State)',
                'Avg_Lead_Time': 'Avg Lead Time (Days)',
                'Shipment_Count': 'Shipment Count',
                'Efficiency_Score': 'Efficiency Score (0-100)'
            }),
            hide_index=True,
            use_container_width=True
        )

    with lead_col2:
        st.markdown("<h4 style='font-weight: bold; font-size: 16px; color: #C62828;'>🐢 Bottom 10 Slowest Shipping Routes</h4>", unsafe_allow_html=True)
        top_slowest = route_leaderboard.sort_values('Avg_Lead_Time', ascending=False).head(10)
        top_slowest['Avg_Lead_Time'] = top_slowest['Avg_Lead_Time'].round(1)
        top_slowest['Efficiency_Score'] = top_slowest['Efficiency_Score'].round(1)
        st.dataframe(
            top_slowest.rename(columns={
                'Route': 'Route (Factory → State)',
                'Avg_Lead_Time': 'Avg Lead Time (Days)',
                'Shipment_Count': 'Shipment Count',
                'Efficiency_Score': 'Efficiency Score (0-100)'
            }),
            hide_index=True,
            use_container_width=True
        )

# -----------------------------------------------------------------------------
# BUSINESS INSIGHTS & EXECUTIVE SUMMARY SECTION (RIGHT COLUMN)
# -----------------------------------------------------------------------------
with insights_col:
    st.markdown("<h3 style='font-weight: 900; font-size: 22px; color: #3E2723; margin-top: 15px;'>EXECUTIVE INSIGHTS</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='border-top: 2px solid #3E2723; margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    # Calculating summary metrics dynamically from filtered dataset
    factory_perf = filtered_df.groupby('Factory')['Lead Time'].mean()
    top_factory = factory_perf.idxmin() if not factory_perf.empty else "N/A"
    worst_factory = factory_perf.idxmax() if not factory_perf.empty else "N/A"

    route_perf = filtered_df.groupby('Route')['Lead Time'].mean()
    fastest_route_str = route_perf.idxmin() if not route_perf.empty else "N/A"
    slowest_route_str = route_perf.idxmax() if not route_perf.empty else "N/A"

    ship_perf = filtered_df.groupby('Ship Mode')['Lead Time'].mean()
    best_ship_mode = ship_perf.idxmin() if not ship_perf.empty else "N/A"
    worst_ship_mode = ship_perf.idxmax() if not ship_perf.empty else "N/A"

    state_perf = filtered_df.groupby('State/Province')['Lead Time'].mean()
    state_highest_delay = state_perf.idxmax() if not state_perf.empty else "N/A"
    state_lowest_delay = state_perf.idxmin() if not state_perf.empty else "N/A"

    st.markdown(f"""
        <div class='insight-card'>
            <h4>🏭 Top Performing Factory</h4>
            <p><b>{top_factory}</b> (Lowest average transit lead time across network dispatches).</p>
        </div>
        <div class='insight-card'>
            <h4>🏚️ Worst Performing Factory</h4>
            <p><b>{worst_factory}</b> (Highest average lead time requiring loading dock optimization).</p>
        </div>
        <div class='insight-card'>
            <h4>🚀 Fastest Route</h4>
            <p><b>{fastest_route_str}</b> (Optimal logistical flow with lowest recorded transit delay).</p>
        </div>
        <div class='insight-card'>
            <h4>🐢 Slowest Route</h4>
            <p><b>{slowest_route_str}</b> (Major bottleneck requiring regional hub rerouting).</p>
        </div>
        <div class='insight-card'>
            <h4>🚢 Best Ship Mode</h4>
            <p><b>{best_ship_mode}</b> (Delivers highest fulfillment efficiency and lowest lead time).</p>
        </div>
        <div class='insight-card'>
            <h4>⚓ Worst Ship Mode</h4>
            <p><b>{worst_ship_mode}</b> (Exhibits fulfillment lag relative to carrier SLAs).</p>
        </div>
        <div class='insight-card'>
            <h4>⚠️ State with Highest Delay</h4>
            <p><b>{state_highest_delay}</b> (Primary geographic bottleneck for customer order fulfillment).</p>
        </div>
        <div class='insight-card'>
            <h4>✅ State with Lowest Delay</h4>
            <p><b>{state_lowest_delay}</b> (Most efficient destination state for outbound shipments).</p>
        </div>
        <div class='insight-card'>
            <h4>💡 Best Recommendation</h4>
            <p>Consolidate cross-country shipments into regional cross-dock hubs and renegotiate carrier SLAs.</p>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAGIC RUN BLOCK FOR DIRECT VS CODE PLAY BUTTON EXECUTION
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import subprocess
    import sys
    if not st.runtime.exists():
        subprocess.run(["streamlit", "run", sys.argv[0]])