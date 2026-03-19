# app_orig.py
# Habit Tracking Application
# This is the main application file for the Habit Tracking project. 
# It initializes the HabitTracker class, loads data, and runs the application.

# TO RUN:
# streamlit run habit-tracking/habit_tracking/app_orig.py

# Load packages
import config
from tracker import HabitTracker
import argparse
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import pandas as pd
from google.oauth2 import service_account

st.set_page_config(layout="wide", page_title="Habit Tracking Dashboard")

# Load credentials from Streamlit Secrets
creds_dict = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(creds_dict)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for _key, _default in {
    "queue":                  {},
    "removed_files":          set(),
    "last_s3_sync_time":      None,
    "last_reviewer":          "",
    "selected_filenames":     [],
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── SIDEBAR ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Date Selection")
    selected_date_range = st.date_input("Select a date range to view your habits over time", value=(pd.to_datetime(config.HT_START_DATE), pd.Timestamp.today()))
    
    st.header("Habit Picker")
    selected_habits = st.multiselect("Select habits to view", options=config.BOOLEAN_VARIABLES, default=["Exercised", "Caffeine", "Alcohol", "Weed"])

# --- PROCESSING -----------------------------------------------------
tracker = HabitTracker()
tracker.load_and_clean(service_account_file=credentials,
                       sleep_file=None,
                       weight_file=None)
tracker.plot_prep(start_date=selected_date_range[0], end_date=selected_date_range[1])


# --- MAIN PANEL ------------------------------------------------------
row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns(
    (0.1, 2, 0.2, 1, 0.1)
)

row0_1.title("Habit Tracking Dashboard")


with row0_2:
    add_vertical_space()

# row0_2.subheader(
#     "A Streamlit web app by [Katy Yut](http://www.katyyut.com)."
# )

past_week = tracker.df_long[tracker.df_long['Date'] >= (pd.Timestamp.today().date() - pd.Timedelta(days=7))].groupby('Habit')['Value'].sum().reset_index()
past_week_filtered = past_week[past_week['Habit'].isin(selected_habits)]
past_week_lines = "\n".join(
        f"- {row['Habit']}: {row['Value']} days"
        for _, row in past_week_filtered.iterrows()
    )

row0_2.subheader(
    "7-day Summary:  \n"
    f"{past_week_lines}"
)

row1_spacer1, row1_1, row1_spacer2 = st.columns((0.1, 3.2, 0.1))

with row0_1:
    st.markdown(
        "Hello and welcome to Katy's spectacular habit tracking app."
    )
    st.markdown(
        ""
    )

row2_spacer1, row2_1, row2_spacer2 = st.columns((0.1, 3.2, 0.1))
with row2_1:
    
    st.markdown(
        ""
    )


st.write("")
row3_space1, row3_1, row3_space2 = st.columns(
    (0.1, 2.1, 0.1)
)

with row3_1:
    st.subheader("Monthly Percentages")

    fig, legend_fig = tracker.plot_monthly_percentages(selected_habits=selected_habits)
    plot_col, legend_col = st.columns([6, 1])
    with plot_col:
        st.pyplot(fig, use_container_width=True)
    with legend_col:
        if legend_fig:
            st.pyplot(legend_fig, use_container_width=True)

    if 1 > 0:
        st.markdown(
            ""
        )
    else:
        st.markdown(
            ""
        )
    
st.write("")
row3_space1, row3_2, row3_space2 = st.columns(
    (0.1, 2.1, 0.1)
)

with row3_2:
    st.subheader("Habit Totals")

    fig, _ = tracker.plot_total_barchart()
    st.pyplot(fig, use_container_width=True)
    st.markdown(
        ""
    )

add_vertical_space()
row4_space1, row4_1, row4_space2 = st.columns(
    (0.1, 2.1, 0.1)
)
    
with row4_1:
    st.subheader("Mental Health")

    fig, _ = tracker.plot_mental_health_trend()
    st.pyplot(fig, use_container_width=True)

    st.markdown(
        f"All time average mental health: {tracker.df['Mental_Health'].mean():.2f} out of 10"
    )
    
add_vertical_space()
row5_space1, row5_1, row5_space2, row5_2, row5_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)

with row5_1:
    st.subheader("Monthly Heatmap")
   
    fig, _ = tracker.plot_monthly_heatmap()
    st.pyplot(fig, use_container_width=True)
    st.markdown(
        ""
    )
    st.markdown(
        ""
    )
    
with row5_2:
    st.subheader("Monthly Goal Achievement")
   
    fig, _ = tracker.plot_monthly_goal_achievement()
    st.pyplot(fig, use_container_width=True)
    st.markdown(
        ""
    )
    st.markdown(
        ""
    )

add_vertical_space()
row6_space1, row6_1, row6_space2, row6_2, row6_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)


with row6_1:
    st.subheader("Diary")
    
    diary = tracker.df[['Date', 'Other_notes']].dropna().sort_values('Date', ascending=False)
    st.dataframe(diary, hide_index=True)
    
    st.markdown(
        ""
    )
    st.markdown(
        ""
    )

add_vertical_space()

with row6_2:
    st.subheader("Medications")
    
    fig, legend_fig = tracker.plot_medications()
    if fig is not None:
        plot_col, legend_col = st.columns([4, 1])
        with plot_col:
            st.pyplot(fig, use_container_width=True)
        with legend_col:
            if legend_fig:
                st.pyplot(legend_fig, use_container_width=True)

    curr_meds = tracker.meds_data[tracker.meds_data['End_Date'] == pd.Timestamp.today().date()]

    med_lines = "\n".join(
        f"- {row['Medication_Generic']} (aka {row['Medication_Brand']}) — {row['Dose (mg)']} mg"
        for _, row in curr_meds.iterrows()
    )
    st.markdown(f"You are currently taking:\n{med_lines}")
    
row7_spacer1, row7_1, row7_spacer2 = st.columns((0.1, 3.2, 0.1))

# with row7_1:
#     st.header("**Book List Recommendation for {}**".format("Katy Yut"))
    
#     st.markdown(
#         "For one last bit of analysis, we scraped a few hundred book lists from famous thinkers in technology, media, and government (everyone from Barack and Michelle Obama to Keith Rabois and Naval Ravikant). We took your list of books read and tried to recommend one of their lists to book through based on information we gleaned from your list"
#     )
#     st.markdown(
#         "You read the most books in common with **{}**, and your book list is the most similar on average to **{}**. Find their book lists [here]({}) and [here]({}) respectively.".format(
#             "N/A", "N/A", "#", "#"
#         )
#     )


#     st.markdown("***")
#     st.markdown(
#         "Thanks for going through this mini-analysis with me! I'd love feedback on this, so if you want to reach out you can find me on [twitter](https://twitter.com/tylerjrichards) or my [website](http://www.tylerjrichards.com/)."
#     )
