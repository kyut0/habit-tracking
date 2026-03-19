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


tracker = HabitTracker()
tracker.load_and_clean()
tracker.plot_prep()

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
        "Hey there! Welcome to Tyler's Goodreads Analysis App. This app scrapes (and never keeps or stores!) the books you've read and analyzes data about your book list, including estimating the gender breakdown of the authors, and looking at the distribution of the age and length of book you read. After some nice graphs, it tries to recommend a curated book list to you from a famous public reader, like Barack Obama or Bill Gates. One last tip, if you're on a mobile device, switch over to landscape for viewing ease. Give it a go!"
    )
    st.markdown(
        "**To begin, please enter the link to your [Goodreads profile](https://www.goodreads.com/) (or just use mine!).** 👇"
    )

row2_spacer1, row2_1, row2_spacer2 = st.columns((0.1, 3.2, 0.1))
with row2_1:
    default_username = st.selectbox(
        "Select one of our sample Goodreads profiles",
        (
            "89659767-tyler-richards",
            "7128368-amanda",
            "17864196-adrien-treuille",
            "133664988-jordan-pierre",
        ),
    )
    st.markdown("**or**")
    user_input = st.text_input(
        "Input your own Goodreads Link (e.g. https://www.goodreads.com/user/show/89659767-tyler-richards)"
    )
    need_help = st.expander("Need help? 👉")
    with need_help:
        st.markdown(
            "Having trouble finding your Goodreads profile? Head to the [Goodreads website](https://www.goodreads.com/) and click profile in the top right corner."
        )

    if not user_input:
        user_input = f"https://www.goodreads.com/user/show/{default_username}"


st.write("")
row3_space1, row3_1, row3_space2 = st.columns(
    (0.1, 2.1, 0.1)
)

with row3_1:
    st.subheader("Habit Totals")
    
    st.plotly_chart(tracker.plot_total_barchart(), theme="streamlit", width='stretch')
    st.markdown(
        "It looks like you've read a grand total of **{} books with {} authors,** with {} being your most read author! That's awesome. Here's what your reading habits look like since you've started using Goodreads.".format(
            4, 6, 9
        )
    )
    
st.write("")
row3_space1, row3_2, row3_space2 = st.columns(
    (0.1, 2.1, 0.1)
)
    
with row3_2:
    st.subheader("Mental Health")

    st.plotly_chart(tracker.plot_mental_health_trend(), theme="streamlit", width='stretch')

    st.markdown(
        "Looks like the average publication date is around **{}**, with your oldest book being **{}** and your youngest being **{}**.".format(
            "N/A", "N/A", "N/A"
        )
    )
    st.markdown(
        "Note that the publication date on Goodreads is the **last** publication date, so the data is altered for any book that has been republished by a publisher."
    )

add_vertical_space()
row4_space1, row4_1, row4_space2 = st.columns(
    (0.1, 2.1, 0.1)
)

with row4_1:
    st.subheader("Monthly Percentages")
    
    st.plotly_chart(tracker.plot_monthly_percentages(), theme="streamlit", width='stretch')

    if 1 > 0:
        st.markdown(
            "It looks like on average you rate books **lower** than the average Goodreads user, **by about {} points**. You differed from the crowd most on the book {} where you rated the book {} stars while the general readership rated the book {}".format(
                abs(round(2, 3)), 0, 0, 0
            )
        )
    else:
        st.markdown(
            "It looks like on average you rate books **higher** than the average Goodreads user, **by about {} points**. You differed from the crowd most on the book {} where you rated the book {} stars while the general readership rated the book {}".format(
                abs(round(7, 3)), 0, 0, 0
            )
        )

add_vertical_space()
row5_space1, row5_1, row5_space2 = st.columns(
    (0.1, 2.1, 0.1)
)

with row5_1:
    st.subheader("Medications")
    
    st.plotly_chart(tracker.plot_medications(), theme="streamlit", width='stretch')

    st.markdown(
        "Your average book length is **{} pages**, and your longest book read is **{} at {} pages!**.".format(
            0, "N/A", 0
        )
    )
    
# with row5_2:
#     st.subheader("Sleep Patterns")
    
#     sleep_fig = tracker.plot_sleep_pattern()
#     if sleep_fig is not None:
#         st.plotly_chart(sleep_fig, theme="streamlit", width='stretch')
#     else:
#         st.info("No sleep data available.")
    
#     st.markdown(
#         "On average, it takes you **{} days** between you putting on Goodreads that you're reading a title, and you getting through it! Now let's move on to a gender breakdown of your authors.".format(
#             10.0
#         )
#     )

add_vertical_space()
row6_space1, row6_1, row6_space2, row6_2, row6_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)

# with row6_1:
#     st.subheader("Cumulative Habits")
    
#     st.plotly_chart(tracker.plot_cumulative_habits(), theme="streamlit", width='stretch')
#     st.markdown(
#         "To get the gender breakdown of the books you have read, this next bit takes the first name of the authors and uses that to predict their gender. These algorithms are far from perfect, and tend to miss non-Western/non-English genders often so take this graph with a grain of salt."
#     )
#     st.markdown(
#         "Note: the package I'm using for this prediction outputs 'andy', which stands for androgenous, whenever multiple genders are nearly equally likely (at some threshold of confidence). It is not, sadly, a prediction of a new gender called andy."
#     )

with row6_2:
    st.subheader("Monthly Heatmap")
   
    st.plotly_chart(tracker.plot_monthly_heatmap(), theme="streamlit", width='stretch')
    st.markdown(
        "Here you can see the gender distribution over time to see how your reading habits may have changed."
    )
    st.markdown(
        "Want to read more books written by women? [Here](https://www.penguin.co.uk/articles/2019/mar/best-books-by-female-authors.html) is a great list from Penguin that should be a good start."
    )

add_vertical_space()
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



st.title("Some Title Here")

with st.expander("Instructions:"):
    st.markdown("""
        \n1. Insert. 
        \n2. Something.
        \n3. Here.""")

# ── SIDEBAR ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Date Selection")
    selected_date_range = st.date_input("Select a date range to view your habits over time", value=(pd.to_datetime(config.EXERCISE_START_DATE), pd.Timestamp.today()))
    
    st.header("Habit Picker")
    selected_habits = st.multiselect("Select habits to view", options=config.BOOLEAN_VARIABLES, default=["Exercised", "Caffeine", "Alcohol", "Weed"])
    
# ── MAIN PANEL ─────────────────────────────────────────────────────────────────

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