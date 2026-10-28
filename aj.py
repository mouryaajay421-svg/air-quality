import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Indian Air Quality Trend Analysis",
    page_icon="🌍",
    layout="wide"
)

# ---------------- LOAD CSV ----------------

@st.cache_data
def load_data():
    return pd.read_csv("ajayen.csv")

try:
    df = load_data()
except FileNotFoundError:
    st.error("ajayen.csv file ko aj.py ke same folder mein rakho.")
    st.stop()
except Exception as e:
    st.error(f"CSV load nahi hui: {e}")
    st.stop()

# Clean column names
df.columns = [
    str(col).strip().lower().replace(" ", "_")
    for col in df.columns
]

# Required columns
required = [
    "country", "state", "city", "station",
    "last_update", "latitude", "longitude",
    "pollutant_id", "pollutant_min",
    "pollutant_max", "pollutant_avg"
]

missing = [col for col in required if col not in df.columns]

if missing:
    st.error(f"CSV mein ye columns nahi mile: {missing}")
    st.write("Available columns:", list(df.columns))
    st.stop()

# Convert numeric columns
for col in [
    "latitude", "longitude", "pollutant_min",
    "pollutant_max", "pollutant_avg"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1220, #111827, #172033);
}
.block-container {
    padding-top: 1.5rem;
}
[data-testid="stMetric"] {
    background: #172033;
    border: 1px solid #334155;
    padding: 15px;
    border-radius: 12px;
}
[data-testid="stMetricValue"] {
    color: white;
}
</style>
""", unsafe_allow_html=True)


def show_chart(fig, height=450):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        title_x=0.03
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🌍 India Air Quality")
    st.caption("Monitor • Analyze • Explore")

    page = st.radio(
        "MAIN MENU",
        [
            "🏠Home",
            "📝Dataset",
            "📊Visualization",
            "🧐Search City / Station",
            "💡Insights",
            "💭About"
        ]
    )

    st.divider()
    st.caption("Data Source: ajayen.csv")


# ---------------- SUMMARY ----------------

total_records = len(df)
total_cities = df["city"].nunique()
total_states = df["state"].nunique()
total_stations = df["station"].nunique()

pollutants = sorted(
    df["pollutant_id"].dropna().astype(str).unique()
)

# ---------------- HOME ----------------

if page ==  "🏠Home":

    st.title("🇮🇳 Indian Air Quality Trend Analysis")

    st.markdown(
        "### Monitor pollution • Analyze data • Explore cities"
    )

    st.info(
        "This dashboard analyzes the pollutant readings provided in " 
        "the csv.The pollutant averages are not to be considered as direct AQI"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📄 Total Records", f"{total_records:,}")
    c2.metric("🏙️ Unique Cities", f"{total_cities:,}")
    c3.metric("🗺️ States / UTs", f"{total_states:,}")
    c4.metric("📡 Monitoring Stations", f"{total_stations:,}")

    c1, c2, c3 = st.columns(3)

    c1.metric("🧪 Pollutant Types", len(pollutants))
    c2.metric(
        "Available Readings",
        f"{df['pollutant_avg'].notna().sum():,}"
    )
    c3.metric(
        "Missing Readings",
        f"{df['pollutant_avg'].isna().sum():,}"
    )

    st.subheader("📊 Pollutant-wise Average")

    summary = (
        df.dropna(subset=["pollutant_avg"])
        .groupby("pollutant_id", as_index=False)["pollutant_avg"]
        .mean()
        .sort_values("pollutant_avg", ascending=False)
    )

    if not summary.empty:
        fig = px.bar(
            summary,
            x="pollutant_id",
            y="pollutant_avg",
            color="pollutant_avg",
            text_auto=".1f",
            title="Average Reading by Pollutant",
            color_continuous_scale="Oranges"
        )
        fig.update_layout(coloraxis_showscale=False)
        show_chart(fig)

    st.subheader("📂 Complete Dataset")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    st.download_button(
        "⬇️ Download Complete Dataset",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="complete_air_quality_data.csv",
        mime="text/csv"
    )


# ---------------- DATASET ----------------

elif page == "📝Dataset":

    st.title("📂 Complete Dataset Explorer")

    st.write(f"Total Records: **{total_records:,}**")

    search = st.text_input(
        "Search City, State, Station or Pollutant"
    )

    filtered = df.copy()

    if search.strip():
        mask = pd.Series(False, index=filtered.index)

        for col in ["city", "state", "station", "pollutant_id"]:
            mask |= filtered[col].astype(str).str.contains(
                search,
                case=False,
                na=False
            )

        filtered = filtered[mask]

    st.write(f"Matching Records: **{len(filtered):,}**")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        height=550
    )

    st.download_button(
        "⬇️ Download Displayed Records",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_air_quality_data.csv",
        mime="text/csv"
    )

    st.subheader("Missing Values")

    missing_data = pd.DataFrame({
        "Column": df.columns,
        "Missing Values": df.isna().sum().values,
        "Data Type": df.dtypes.astype(str).values
    })

    st.dataframe(
        missing_data,
        use_container_width=True,
        hide_index=True
    )


# ---------------- VISUALIZATION ----------------

elif page == "📊Visualization":

    st.title("📊 Air Quality Visualizations")

    tab1, tab2, tab3 = st.tabs([
        "Pollutant Ranking",
        "City Analysis",
        "State Analysis"
    ])

    with tab1:

        st.subheader("🏆 Highest Pollutant Readings")

        selected = st.selectbox(
            "Select Pollutant",
            pollutants
        )

        limit = st.selectbox(
            "Records to Display",
            ["Top 10", "Top 20", "Top 50", "All Records"]
        )

        ranked = df[
            (df["pollutant_id"] == selected)
            & df["pollutant_avg"].notna()
        ].sort_values("pollutant_avg", ascending=False)

        if limit != "All Records":
            ranked = ranked.head(int(limit.split()[1]))

        st.write(f"Records Shown: **{len(ranked):,}**")

        if not ranked.empty:

            fig = px.bar(
                ranked.sort_values("pollutant_avg"),
                x="pollutant_avg",
                y="station",
                orientation="h",
                color="pollutant_avg",
                hover_data=["city", "state", "pollutant_id"],
                title=f"{selected} Reading Ranking",
                color_continuous_scale="Reds"
            )

            fig.update_layout(coloraxis_showscale=False)

            show_chart(
                fig,
                max(450, min(1000, len(ranked) * 25))
            )

            st.dataframe(
                ranked,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.warning("Is pollutant ki numeric readings available nahi hain.")

    with tab2:

        st.subheader("🏙️ City-wise Pollutant Comparison")

        selected = st.selectbox(
            "Select Pollutant",
            pollutants,
            key="city_pollutant"
        )

        city_data = (
            df[
                (df["pollutant_id"] == selected)
                & df["pollutant_avg"].notna()
            ]
            .groupby("city", as_index=False)["pollutant_avg"]
            .mean()
            .sort_values("pollutant_avg", ascending=False)
        )

        if not city_data.empty:

            count = st.selectbox(
                "Cities to Display",
                ["Top 10", "Top 20", "All Cities"]
            )

            if count != "All Cities":
                city_data = city_data.head(int(count.split()[1]))

            fig = px.bar(
                city_data.sort_values("pollutant_avg"),
                x="pollutant_avg",
                y="city",
                orientation="h",
                color="pollutant_avg",
                title=f"{selected} Average by City",
                color_continuous_scale="Oranges"
            )

            fig.update_layout(coloraxis_showscale=False)

            show_chart(
                fig,
                max(450, min(1000, len(city_data) * 25))
            )

            st.dataframe(
                city_data,
                use_container_width=True,
                hide_index=True
            )

    with tab3:

        st.subheader("🗺️ State-wise Analysis")

        selected = st.selectbox(
            "Select Pollutant",
            pollutants,
            key="state_pollutant"
        )

        state_data = (
            df[
                (df["pollutant_id"] == selected)
                & df["pollutant_avg"].notna()
            ]
            .groupby("state", as_index=False)["pollutant_avg"]
            .mean()
            .sort_values("pollutant_avg", ascending=False)
        )

        if not state_data.empty:

            fig = px.bar(
                state_data,
                x="state",
                y="pollutant_avg",
                color="pollutant_avg",
                text_auto=".1f",
                title=f"{selected} Average by State",
                color_continuous_scale="Oranges"
            )

            fig.update_layout(
                xaxis_tickangle=-45,
                coloraxis_showscale=False
            )

            show_chart(fig, 500)

            st.dataframe(
                state_data,
                use_container_width=True,
                hide_index=True
            )


# ---------------- SEARCH ----------------

elif page == "🧐Search City / Station":

    st.title("🔎 Search Air Quality Data")

    search_type = st.radio(
        "Search By",
        ["City", "State", "Pollutant", "Station"],
        horizontal=True
    )

    if search_type == "City":

        value = st.selectbox(
            "Select City",
            sorted(df["city"].dropna().unique())
        )
        result = df[df["city"] == value]

    elif search_type == "State":

        value = st.selectbox(
            "Select State",
            sorted(df["state"].dropna().unique())
        )
        result = df[df["state"] == value]

    elif search_type == "Pollutant":

        value = st.selectbox(
            "Select Pollutant",
            pollutants
        )
        result = df[df["pollutant_id"] == value]

    else:

        value = st.selectbox(
            "Select Station",
            sorted(df["station"].dropna().unique())
        )
        result = df[df["station"] == value]

    st.write(f"Records Found: **{len(result):,}**")

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Search Results",
        data=result.to_csv(index=False).encode("utf-8"),
        file_name="air_quality_search_results.csv",
        mime="text/csv"
    )


# ---------------- INSIGHTS ----------------

elif page == "💡Insights":

    st.title("💡 Dataset Insights")

    st.info(
        "These insights are based on the pollution readings in our csv file"
        " and do not represent direct AQI scores or live air quality status."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Records", f"{total_records:,}")
    c2.metric("Unique Cities", f"{total_cities:,}")
    c3.metric("Monitoring Stations", f"{total_stations:,}")

    st.subheader("Highest Reading by Pollutant")

    valid = df.dropna(subset=["pollutant_avg"])

    if not valid.empty:

        highest = valid.loc[
            valid.groupby("pollutant_id")["pollutant_avg"].idxmax(),
            [
                "pollutant_id",
                "city",
                "state",
                "station",
                "pollutant_avg"
            ]
        ]

        st.dataframe(
            highest.sort_values("pollutant_id"),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("📊 Records by Pollutant")

    counts = (
        df["pollutant_id"]
        .value_counts()
        .rename_axis("Pollutant")
        .reset_index(name="Records")
    )

    fig = px.pie(
        counts,
        names="Pollutant",
        values="Records",
        title="Dataset Records by Pollutant"
    )

    show_chart(fig, 400)


# ---------------- ABOUT ----------------

elif page == "💭About":

    st.title("ℹ️ About This Project")

    st.markdown("""
    ## Indian Air Quality Trend Analysis

    This project analyzes air-pollution monitoring data from a CSV file.

    ### Features
    - Complete dataset viewing
    - City and state analysis
    - Pollutant-wise visualizations
    - Station and pollutant search
    - Missing-value summary
    - CSV download
    - Data-based insights

    ### Technologies
    - Python
    - Streamlit
    - Pandas
    - Plotly
    - CSV Dataset

    **Important:** This CSV does not provide a direct AQI column or
    lockdown-period readings. The dashboard therefore analyzes
    pollutant measurements rather than claiming to calculate AQI.
    """)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Records", f"{total_records:,}")
    c2.metric("Cities", f"{total_cities:,}")
    c3.metric("States", f"{total_states:,}")
    c4.metric("Stations", f"{total_stations:,}")


st.divider()
st.caption(
    "🌍 Indian Air Quality Trend Analysis | Educational Data Analysis Project"
)