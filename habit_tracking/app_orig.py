# app_orig.py
# Habit Tracking Application
# This is the main application file for the Habit Tracking project. 
# It initializes the HabitTracker class, loads data, and runs the application.

# TO RUN:
# streamlit run habit-tracking/habit_tracking/app_orig.py

# Load packages
from habit_tracking import config
from tracker import HabitTracker
import argparse
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import pandas as pd

st.set_page_config(layout="wide", page_title="Habit Tracking Dashboard")

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
tracker.load_and_clean()
tracker.plot_prep(start_date=selected_date_range[0], end_date=selected_date_range[1])


# --- MAIN PANEL ------------------------------------------------------
row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns(
    (0.1, 2, 0.2, 1, 0.1)
)

row0_1.title("Habit Tracking Dashboard")


with row0_2:
    add_vertical_space()

row0_2.subheader(
    "A Streamlit web app by [Katy Yut](http://www.katyyut.com)."
)

row0_2.subheader(
    "7-day Summary:"
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
    plot_col, legend_col = st.columns([4, 1])
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

with row7_1:
    st.header("**Book List Recommendation for {}**".format("Katy Yut"))
    
    st.markdown(
        "For one last bit of analysis, we scraped a few hundred book lists from famous thinkers in technology, media, and government (everyone from Barack and Michelle Obama to Keith Rabois and Naval Ravikant). We took your list of books read and tried to recommend one of their lists to book through based on information we gleaned from your list"
    )
    st.markdown(
        "You read the most books in common with **{}**, and your book list is the most similar on average to **{}**. Find their book lists [here]({}) and [here]({}) respectively.".format(
            "N/A", "N/A", "#", "#"
        )
    )


    st.markdown("***")
    st.markdown(
        "Thanks for going through this mini-analysis with me! I'd love feedback on this, so if you want to reach out you can find me on [twitter](https://twitter.com/tylerjrichards) or my [website](http://www.tylerjrichards.com/)."
    )



    
# ── MAIN PANEL ─────────────────────────────────────────────────────────────────

# st.title("Some Title Here")

# with st.expander("Instructions:"):
#     st.markdown("""
#         \n1. Insert. 
#         \n2. Something.
#         \n3. Here.""")

# render_metrics(current_df, loaded_files)

# render_data_views(
#     ordered_df[mask_failed], ordered_df[mask_acted], ordered_df[mask_passed],
#     column_config, valid_overwrite_targets, is_locked, editor_key_suffix,
# )

# render_error_summary(current_df)



# def render_metrics(current_df: pd.DataFrame, loaded_files: list[str]) -> None:
#     """Renders the summary stats row and file editing label."""
#     st.markdown("### Summary Stats")

#     num_samples = len(current_df)
#     passed      = int(current_df["qc_passed"].sum()) if "qc_passed" in current_df.columns else 0
#     failed      = num_samples - passed
#     pass_rate   = (passed / num_samples * 100) if num_samples > 0 else 0

#     m1, m2, m3, m4 = st.columns(4)
#     m1.metric("Failures",      f"{100 - pass_rate:.1f}%", delta=f"{failed} Issues",  delta_color="inverse")
#     m2.metric("Passes",        f"{pass_rate:.1f}%",       delta=f"{passed} Passed")
#     m3.metric("Total Samples", num_samples)

#     current_queue_size = len(st.session_state.queue)
#     files_completed    = list(st.session_state.status.values()).count(QCStatus.UPLOADED)
#     m4.metric("Files Completed", f"{files_completed} / {current_queue_size}")

#     st.progress(pass_rate / 100)
#     st.markdown("#### Editing:\n" + "\n".join(f"- {fn}" for fn in loaded_files))

# def render_data_views(
#     df_failed: pd.DataFrame,
#     df_acted: pd.DataFrame,
#     df_passed: pd.DataFrame,
#     column_config: dict,
#     valid_overwrite_targets: list[str],
#     is_locked: bool,
#     editor_key_suffix: str,
# ) -> None:
#     """Renders the three data editor sections: failures, pending actions, passed."""
#     # SECTION 1: FAILURES
#     st.error(f"Failures Requiring Triage ({len(df_failed)})")
#     if not df_failed.empty:
#         st.data_editor(
#             df_failed, column_config=column_config, width="stretch",
#             key=f"ed_fail_{editor_key_suffix}", disabled=is_locked,
#         )
#     else:
#         st.success("No unaddressed failures found.")

#     # SECTION 2: PENDING ACTIONS
#     st.warning(f"Pending Actions & Overwrites ({len(df_acted)})")
#     if not df_acted.empty:
#         st.markdown("The changes below will be processed upon clicking 'Validate Edits'.")
#         st.data_editor(
#             df_acted, column_config=column_config, width="stretch",
#             key=f"ed_acted_{editor_key_suffix}", disabled=is_locked,
#         )
#     else:
#         st.caption("No actions currently pending.")

#     # SECTION 3: PASSED
#     st.success(f"Passed & Verified Records ({len(df_passed)})")
#     cols_to_show      = [c for c in df_passed.columns if c not in (DataSchema.HITL_COLUMNS + DataSchema.ERROR_COLUMNS)]
#     display_passed_df = df_passed[[c for c in cols_to_show if c in df_passed.columns]]
#     pass_config       = get_column_config(display_passed_df.columns, valid_overwrite_targets)

#     with st.expander("View Passed Records", expanded=df_failed.empty):
#         st.data_editor(
#             display_passed_df, column_config=pass_config, width="stretch",
#             key=f"ed_pass_{editor_key_suffix}", disabled=True,
#         )