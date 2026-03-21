# app_orig.py
# Habit Tracking Application
# TO RUN: streamlit run habit_tracking/app_orig.py

import warnings
warnings.filterwarnings('ignore')

import config
from tracker import HabitTracker
from stats import run_all
import stats_plots as sp

import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import pandas as pd
from google.oauth2 import service_account

st.set_page_config(layout="wide", page_title="Habit Tracking Dashboard")

# ── CREDENTIALS ────────────────────────────────────────────────────────────────
creds_dict = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(creds_dict)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for _key, _default in {
    "queue": {},
    "removed_files": set(),
    "last_s3_sync_time": None,
    "last_reviewer": "",
    "selected_filenames": [],
}.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Date Selection")
    selected_date_range = st.date_input(
        "Select a date range to view your habits over time",
        value=(pd.to_datetime(config.HT_START_DATE), pd.Timestamp.today())
    )

    st.header("Habit Picker")
    selected_habits = st.multiselect(
        "Select habits to view",
        options=config.BOOLEAN_VARIABLES,
        default=["Exercised", "Caffeine", "Alcohol", "Weed"]
    )

# ── DATA LOADING ───────────────────────────────────────────────────────────────
tracker = HabitTracker()
tracker.load_and_clean(service_account_file=credentials,
                       sleep_file=None,
                       weight_file=None)

# Capture full DataFrame BEFORE plot_prep() mutates it (plot_prep filters dates)
full_df = tracker.df.copy()


@st.cache_data
def _cached_stats(df: pd.DataFrame) -> dict:
    """Run all statistical analyses. Cached so rerenders from widget interactions
    don't recompute the models."""
    return run_all(df)


stats = _cached_stats(full_df)
df_int = stats['df_int']
habit_cols = stats['habit_cols']

# Now filter tracker for the dashboard tab
tracker.plot_prep(start_date=selected_date_range[0], end_date=selected_date_range[1])

# ── TABS ───────────────────────────────────────────────────────────────────────
tab_dash, tab_compare, tab_stat = st.tabs(["📊 Dashboard", "📅 Comparison", "🔬 Analysis"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD (existing content, unchanged)
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns(
        (0.1, 2, 0.2, 1, 0.1)
    )
    row0_1.title("Habit Tracking Dashboard")

    with row0_2:
        add_vertical_space()

    past_week = (tracker.df_long[
        tracker.df_long['Date'] >= (pd.Timestamp.today().date() - pd.Timedelta(days=7))
    ].groupby('Habit')['Value'].sum().reset_index())
    past_week_filtered = past_week[past_week['Habit'].isin(selected_habits)]
    past_week_lines = "\n".join(
        f"- {row['Habit']}: {row['Value']} days"
        for _, row in past_week_filtered.iterrows()
    )
    row0_2.subheader("7-day Summary:  \n" + past_week_lines)

    row1_spacer1, row1_1, row1_spacer2 = st.columns((0.1, 3.2, 0.1))

    with row0_1:
        st.markdown("Hello and welcome to Katy's spectacular habit tracking app.")
        st.markdown("")

    row2_spacer1, row2_1, row2_spacer2 = st.columns((0.1, 3.2, 0.1))
    with row2_1:
        st.markdown("")

    st.write("")
    row3_space1, row3_1, row3_space2 = st.columns((0.1, 2.1, 0.1))

    with row3_1:
        st.subheader("Monthly Percentages")
        fig, legend_fig = tracker.plot_monthly_percentages(selected_habits=selected_habits)
        plot_col, legend_col = st.columns([6, 1])
        with plot_col:
            st.pyplot(fig, use_container_width=True)
        with legend_col:
            if legend_fig:
                st.pyplot(legend_fig, use_container_width=True)
        st.markdown("")

    st.write("")
    row3_space1, row3_2, row3_space2 = st.columns((0.1, 2.1, 0.1))

    with row3_2:
        st.subheader("Habit Totals")
        fig, _ = tracker.plot_total_barchart()
        st.pyplot(fig, use_container_width=True)
        st.markdown("")

    add_vertical_space()
    row4_space1, row4_1, row4_space2 = st.columns((0.1, 2.1, 0.1))

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
        st.markdown("")

    with row5_2:
        st.subheader("Monthly Goal Achievement")
        fig, _ = tracker.plot_monthly_goal_achievement()
        st.pyplot(fig, use_container_width=True)
        st.markdown("")

    add_vertical_space()
    row6_space1, row6_1, row6_space2, row6_2, row6_space3 = st.columns(
        (0.1, 1, 0.1, 1, 0.1)
    )

    with row6_1:
        st.subheader("Diary")
        diary = (tracker.df[['Date', 'Other_notes']]
                 .dropna().sort_values('Date', ascending=False))
        st.dataframe(diary, hide_index=True)
        st.markdown("")

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

        curr_meds = tracker.meds_data[
            tracker.meds_data['End_Date'] == pd.Timestamp.today().date()
        ]
        med_lines = "\n".join(
            f"- {row['Medication_Generic']} (aka {row['Medication_Brand']}) — {row['Dose (mg)']} mg"
            for _, row in curr_meds.iterrows()
        )
        st.markdown(f"You are currently taking:\n{med_lines}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPARISON (year-over-year + seasonal)
# ══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.title("Comparison & Trends")
    st.markdown(
        "Explore how your habits and mental health have changed year over year "
        "and whether seasonal patterns emerge. All data from the active tracking "
        f"period ({config.HT_START_DATE} onward, submitted days only)."
    )

    # ── Year-over-Year Mental Health ──────────────────────────────────────────
    st.subheader("Mental Health — Year over Year")

    years = sorted(df_int['Year'].unique())
    annual_mh = df_int.groupby('Year')['Mental_Health'].mean()
    best_year = int(annual_mh.idxmax())
    worst_year = int(annual_mh.idxmin())
    trend_dir = "improving" if annual_mh.iloc[-1] > annual_mh.iloc[0] else "declining"
    trend_delta = annual_mh.iloc[-1] - annual_mh.iloc[0]

    st.markdown(
        f"Your data spans **{len(years)} years** ({years[0]}–{years[-1]}). "
        f"Your best year for mental health was **{best_year}** "
        f"(avg {annual_mh[best_year]:.2f}/10) and your lowest was **{worst_year}** "
        f"(avg {annual_mh[worst_year]:.2f}/10). "
        f"Overall trend from first to last year: **{trend_dir}** "
        f"({trend_delta:+.2f} points)."
    )

    col_yoy1, col_yoy2 = st.columns([3, 1])
    with col_yoy1:
        st.pyplot(sp.plot_yoy_mental_health(df_int), use_container_width=True)
    with col_yoy2:
        st.pyplot(sp.plot_annual_mh_trend(df_int), use_container_width=True)

    # ── Year-over-Year Habits ─────────────────────────────────────────────────
    st.subheader("Habit Completion — Year over Year")

    yoy_habits = df_int.groupby('Year')[habit_cols].mean() * 100
    most_improved = None
    most_declined = None
    if len(years) >= 2:
        delta = yoy_habits.iloc[-1] - yoy_habits.iloc[0]
        delta_clean = delta.dropna()
        if len(delta_clean) > 0:
            most_improved = delta_clean.idxmax()
            most_declined = delta_clean.idxmin()
            st.markdown(
                f"From **{years[0]}** to **{years[-1]}**: "
                f"your most-improved habit is **{most_improved}** "
                f"({delta_clean[most_improved]:+.0f} pp), "
                f"and the most-declined is **{most_declined}** "
                f"({delta_clean[most_declined]:+.0f} pp)."
            )

    st.pyplot(sp.plot_yoy_habits(df_int, habit_cols), use_container_width=True)

    # ── Seasonal Patterns ─────────────────────────────────────────────────────
    st.subheader("Seasonal Patterns")

    seasonal_mh = df_int.groupby('Season')['Mental_Health'].mean()
    best_season = seasonal_mh.idxmax() if len(seasonal_mh) > 0 else "N/A"
    worst_season = seasonal_mh.idxmin() if len(seasonal_mh) > 0 else "N/A"
    seasonal_range = seasonal_mh.max() - seasonal_mh.min() if len(seasonal_mh) > 1 else 0

    if seasonal_range > 0.3:
        season_note = (
            f"Your mental health varies meaningfully by season "
            f"(range: {seasonal_range:.2f} points). "
            f"You tend to feel best in **{best_season}** "
            f"(avg {seasonal_mh[best_season]:.2f}) "
            f"and lowest in **{worst_season}** "
            f"(avg {seasonal_mh[worst_season]:.2f})."
        )
        if worst_season == 'Winter':
            season_note += " This is consistent with seasonal affective patterns."
        elif worst_season == 'Fall':
            season_note += " A fall dip can precede seasonal affective patterns — worth watching."
    else:
        season_note = (
            f"Your mental health is relatively stable across seasons "
            f"(range: {seasonal_range:.2f} points), "
            f"suggesting you don't experience strong seasonal mood swings."
        )
    st.markdown(season_note)

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        st.pyplot(sp.plot_seasonal_mh(df_int), use_container_width=True)
    with col_s2:
        st.pyplot(sp.plot_seasonal_habits(df_int, habit_cols), use_container_width=True)

    # ── Monthly Heatmap ───────────────────────────────────────────────────────
    st.subheader("Monthly Habit Heatmap")
    st.markdown(
        "Aggregated across all years — shows which habits cluster in which months."
    )
    st.pyplot(sp.plot_monthly_habit_heatmap(df_int, habit_cols), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STATISTICAL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_stat:
    st.title("Statistical Analysis")
    st.markdown(
        "Rigorous analysis of which habits are associated with your mental health. "
        "All p-values use Benjamini-Hochberg correction for multiple comparisons. "
        "Regression uses HAC (Newey-West) standard errors appropriate for daily time-series."
    )

    corr = stats['correlations']
    reg = stats['regression']
    sob = stats['sobriety_bed']
    lag = stats['lagged_mh']
    adf = stats['stationarity']
    endo = stats['endogeneity']

    # ── Key Findings banner ───────────────────────────────────────────────────
    st.subheader("Key Findings")

    if len(corr) > 0:
        sig_corr = corr[corr['sig_BH']]
        n_sig = len(sig_corr)
        n_total = len(corr)
        top_pos = sig_corr[sig_corr['MH_diff'] > 0]
        top_neg = sig_corr[sig_corr['MH_diff'] < 0]

        if n_sig > 0:
            best = corr.iloc[0]  # already sorted by MH_diff desc
            worst = corr.iloc[-1]
            sig_pos_list = ", ".join(f"**{h}**" for h in top_pos['Habit'].tolist())
            sig_neg_list = ", ".join(f"**{h}**" for h in top_neg['Habit'].tolist())

            findings_md = f"""
**{n_sig} of {n_total} habits** showed a statistically significant association with your mental health
(Mann-Whitney U, BH-corrected α = 0.05):

- **Positive habits** (doing them = better mood): {sig_pos_list if sig_pos_list else '_none significant_'}
- **Negative habits** (doing them = lower mood): {sig_neg_list if sig_neg_list else '_none significant_'}

Your single highest-impact habit is **{best['Habit']}** — on days you did it,
your mental health averaged **{best['MH_diff']:+.2f} points** {'higher' if best['MH_diff'] > 0 else 'lower'}
than on days you didn't (done on {best['N_done']} days, not done on {best['N_not_done']} days).
"""
        else:
            findings_md = (
                f"After multiple-comparison correction, **none of your {n_total} habits** "
                "showed a statistically significant same-day association with mental health. "
                "This can happen when effect sizes are small relative to variance in mood — "
                "check the lagged effects section for next-day associations."
            )
        st.info(findings_md)
    else:
        st.warning("Not enough data to run correlation analysis.")

    # ── Section 1: Correlations ───────────────────────────────────────────────
    st.markdown("---")
    st.subheader("1. Habit → Mental Health Correlations (Same Day)")
    st.markdown(
        "**Method:** Mann-Whitney U test (non-parametric — no normality assumption). "
        "Δ = mean Mental_Health on days you did the habit minus days you didn't. "
        "★ = significant after Benjamini-Hochberg correction."
    )

    if len(corr) > 0:
        col_p1, col_p2 = st.columns([1.2, 1])
        with col_p1:
            st.pyplot(sp.plot_correlation_forest(corr), use_container_width=True)

        with col_p2:
            # Interactive habit explorer
            st.markdown("**Explore a specific habit:**")
            chosen = st.selectbox(
                "Select habit", options=corr['Habit'].tolist(),
                key='corr_habit_selector'
            )
            row = corr[corr['Habit'] == chosen].iloc[0]
            st.pyplot(sp.plot_habit_mh_boxplot(df_int, chosen), use_container_width=True)

            sig_text = (
                f"✓ Significant (BH p = {row['p_BH']:.4f})"
                if row['sig_BH']
                else f"Not significant (BH p = {row['p_BH']:.4f})"
            )
            st.markdown(
                f"**{chosen}**: done on **{row['N_done']} days** ({row['N_done']/(row['N_done']+row['N_not_done'])*100:.0f}% of tracked days).  \n"
                f"Mental health when done: **{row['MH_done_mean']:.2f}** vs not done: **{row['MH_not_done_mean']:.2f}** (Δ = {row['MH_diff']:+.2f}).  \n"
                f"{sig_text}"
            )

        # Summary table
        with st.expander("Full correlation table"):
            display = corr[['Habit', 'N_done', 'MH_done_mean', 'MH_not_done_mean',
                            'MH_diff', 'r', 'p_mannwhitney', 'p_BH', 'sig_BH']].copy()
            display.columns = ['Habit', 'N (done)', 'MH done', 'MH not done',
                               'Δ MH', 'r', 'p (MW)', 'p (BH)', 'Sig*']
            st.dataframe(display.style.format({
                'MH done': '{:.2f}', 'MH not done': '{:.2f}',
                'Δ MH': '{:+.2f}', 'r': '{:.3f}',
                'p (MW)': '{:.4f}', 'p (BH)': '{:.4f}',
            }), hide_index=True, use_container_width=True)

    # ── Section 2: Regression ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("2. Multiple Regression — Controlling for Yesterday's Mood")
    st.markdown(
        "**Upgrade over simple correlation:** holds all habits constant simultaneously "
        "and adds a lagged dependent variable (`MH_lag1`) to absorb day-to-day mood persistence. "
        "Uses HAC (Newey-West) standard errors robust to autocorrelation and heteroscedasticity."
    )

    if reg.get('sufficient_data'):
        coef_df = reg['coef_df']
        sig_habits = coef_df[coef_df['sig']]
        n_sig_reg = len(sig_habits)
        mh_lag = reg['mh_lag_coef']
        mh_lag_p = reg['mh_lag_p']
        r2 = reg['r_squared']
        dw = reg['dw_stat']

        # Adaptive interpretation
        lag_sig_text = (
            f"Yesterday's mood is a **strong predictor** of today's mood "
            f"(β = {mh_lag:.2f}, p = {mh_lag_p:.4f}) — "
            "this is normal for daily mood data and is why including it is essential."
            if mh_lag_p < 0.05
            else f"Surprisingly, yesterday's mood does not significantly predict today's (β = {mh_lag:.2f}, p = {mh_lag_p:.4f}). "
                 "Your mood changes may be relatively independent day-to-day."
        )

        if n_sig_reg > 0:
            pos_reg = sig_habits[sig_habits['Coef'] > 0]
            neg_reg = sig_habits[sig_habits['Coef'] < 0]
            pos_str = ", ".join(f"**{h}** (+{c:.2f})" for h, c in zip(pos_reg['Habit'], pos_reg['Coef']))
            neg_str = ", ".join(f"**{h}** ({c:+.2f})" for h, c in zip(neg_reg['Habit'], neg_reg['Coef']))
            reg_narrative = (
                f"After controlling for yesterday's mood, **{n_sig_reg} habit(s)** "
                f"remained independently significant (HAC p < 0.05).  \n"
                + (f"Positive: {pos_str}  \n" if pos_str else "")
                + (f"Negative: {neg_str}" if neg_str else "")
            )
        else:
            reg_narrative = (
                "After controlling for yesterday's mood, **no individual habit** "
                "independently predicted mental health at p < 0.05. "
                "The habits may influence mood collectively or through correlated behavior "
                "rather than any single habit driving the effect."
            )

        dw_text = (
            "Residual autocorrelation is low (near 2.0 — good)."
            if 1.5 <= dw <= 2.5
            else f"Residual autocorrelation detected (DW = {dw:.2f}). "
                 "Consider adding `MH_lag2` if you want to push further."
        )

        st.markdown(lag_sig_text)
        st.markdown(reg_narrative)
        st.caption(
            f"Model R² = {r2:.3f} ({r2*100:.1f}% of variance explained) | "
            f"Adjusted R² = {reg['r_squared_adj']:.3f} | "
            f"N = {reg['n_obs']} obs | Durbin-Watson = {dw:.3f} — {dw_text}"
        )

        st.pyplot(
            sp.plot_regression_coefficients(coef_df, r2, mh_lag, mh_lag_p),
            use_container_width=True
        )

        with st.expander("Full regression table"):
            pt = reg['params_table'].copy()
            pt.columns = ['Predictor', 'β', 'CI low', 'CI high', 'p', 'Sig*']
            st.dataframe(pt.style.format({
                'β': '{:+.3f}', 'CI low': '{:.3f}',
                'CI high': '{:.3f}', 'p': '{:.4f}',
            }), hide_index=True, use_container_width=True)
    else:
        st.warning("Not enough data to run regression analysis.")

    # ── Section 3: Lagged Effects ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("3. Lagged Effects — Does Yesterday's Habit Predict Today's Mood?")
    st.markdown(
        "Same-day correlations can't distinguish cause from effect "
        "(does exercise improve mood, or does good mood motivate exercise?). "
        "Lagged analysis is stronger: yesterday's habit cannot be caused by today's mood."
    )

    if len(lag) > 0:
        sig_lag = lag[lag['sig_BH']]
        n_sig_lag = len(sig_lag)

        if n_sig_lag > 0:
            lag_pos = sig_lag[sig_lag['MH_diff'] > 0]['Habit'].tolist()
            lag_neg = sig_lag[sig_lag['MH_diff'] < 0]['Habit'].tolist()
            lag_text = (
                f"**{n_sig_lag} habit(s)** showed a significant *next-day* effect on mood "
                f"(BH-corrected):  \n"
                + (f"- **Positive carry-over**: {', '.join(lag_pos)}  \n" if lag_pos else "")
                + (f"- **Negative carry-over**: {', '.join(lag_neg)}" if lag_neg else "")
            )
        else:
            lag_text = (
                "No habits showed a significant *next-day* effect on mental health "
                "after correction. Habit effects on mood appear to be primarily same-day."
            )
        st.markdown(lag_text)

    # ── Section 4: Your Questions Answered ───────────────────────────────────
    st.markdown("---")
    st.subheader("4. Your Questions Answered")

    q_col1, q_col2 = st.columns(2)

    # Q1: Exercise
    with q_col1:
        st.markdown("**Q1: Does exercise make you feel better?**")
        if len(corr) > 0 and 'Exercised' in corr['Habit'].values:
            ex_row = corr[corr['Habit'] == 'Exercised'].iloc[0]
            ex_dir = "higher" if ex_row['MH_diff'] > 0 else "lower"
            ex_sig = "statistically significant" if ex_row['sig_BH'] else "not statistically significant"
            ex_lag_row = lag[lag['Habit'] == 'Exercised'].iloc[0] if (len(lag) > 0 and 'Exercised' in lag['Habit'].values) else None

            ex_text = (
                f"On exercise days your mental health averaged **{ex_row['MH_done_mean']:.2f}** "
                f"vs **{ex_row['MH_not_done_mean']:.2f}** on rest days — "
                f"**{abs(ex_row['MH_diff']):.2f} points {ex_dir}**. "
                f"This difference is **{ex_sig}** (BH p = {ex_row['p_BH']:.3f})."
            )
            if ex_lag_row is not None:
                lag_dir = "higher" if ex_lag_row['MH_diff'] > 0 else "lower"
                lag_sig = "also significant" if ex_lag_row.get('sig_BH') else "not significant"
                ex_text += (
                    f" The *next-day* effect is {lag_sig}: "
                    f"after exercising, the following day's mood averaged "
                    f"**{ex_lag_row['MH_diff']:+.2f} points {lag_dir}**."
                )
            st.markdown(ex_text)
        else:
            st.markdown("_Insufficient data for Exercise analysis._")

    # Q3: Dancing
    with q_col2:
        st.markdown("**Q3: Does dancing make you happier?**")
        if len(corr) > 0 and 'Danced' in corr['Habit'].values:
            d_row = corr[corr['Habit'] == 'Danced'].iloc[0]
            d_dir = "higher" if d_row['MH_diff'] > 0 else "lower"
            d_sig = "Yes — statistically significant" if d_row['sig_BH'] else "No significant difference detected"
            st.markdown(
                f"On dancing days your mental health was **{d_row['MH_diff']:+.2f} points {d_dir}** "
                f"than on non-dancing days ({d_row['MH_done_mean']:.2f} vs {d_row['MH_not_done_mean']:.2f}).  \n"
                f"**{d_sig}** (BH p = {d_row['p_BH']:.3f}, n = {d_row['N_done']} dancing days)."
            )
        else:
            st.markdown("_Insufficient dancing data._")

    q_col3, q_col4 = st.columns(2)

    # Q2: Sobriety → Made Bed
    with q_col3:
        st.markdown("**Q2: Do you make your bed more when you were sober the day before?**")
        if sob.get('sufficient_data'):
            diff_pct = sob['sober_rate'] - sob['substance_rate']
            sig_text = "Yes — statistically significant" if sob['significant'] else "Not statistically significant"
            direction = "more" if diff_pct > 0 else "less"
            st.markdown(
                f"After a sober day you made your bed **{sob['sober_rate']*100:.0f}%** of the time "
                f"({sob['sober_n']} sober days).  \n"
                f"After using alcohol or weed: **{sob['substance_rate']*100:.0f}%** "
                f"({sob['substance_n']} days).  \n"
                f"You make your bed **{abs(diff_pct)*100:.0f}pp {direction}** after sober days.  \n"
                f"**{sig_text}** (χ² = {sob['chi2']:.2f}, p = {sob['p']:.4f})."
            )
        else:
            st.markdown("_Not enough consecutive sober/substance days to test._")

    # Q4: Drugs and mental health
    with q_col4:
        st.markdown("**Q4: Do drugs have a negative impact on your mental health?**")
        if len(corr) > 0:
            for substance in ['Alcohol', 'Weed']:
                if substance in corr['Habit'].values:
                    s_row = corr[corr['Habit'] == substance].iloc[0]
                    s_dir = "higher" if s_row['MH_diff'] > 0 else "lower"
                    s_sig = "significant" if s_row['sig_BH'] else "not significant"
                    st.markdown(
                        f"**{substance}**: on use days, mental health was **{s_row['MH_diff']:+.2f} {s_dir}** "
                        f"({s_row['MH_done_mean']:.2f} vs {s_row['MH_not_done_mean']:.2f}) — "
                        f"**{s_sig}** (BH p = {s_row['p_BH']:.3f})."
                    )

            # Add endogeneity context
            endo_subs = {r['substance']: r for r in endo if r.get('sufficient_data')}
            for substance, er in endo_subs.items():
                if er['reverse_causal']:
                    st.caption(
                        f"⚠ Reverse causality detected for {substance}: "
                        f"lower mood yesterday predicts more use today (p = {er['p']:.3f}). "
                        "The causal arrow likely runs both ways."
                    )
                elif er['recreational']:
                    st.caption(
                        f"↑ {substance} use appears recreational: "
                        f"higher mood yesterday predicts more use today (p = {er['p']:.3f})."
                    )
        else:
            st.markdown("_Insufficient data._")

    # ── Section 5: Technical Notes (collapsible) ──────────────────────────────
    st.markdown("---")
    with st.expander("🔬 Technical Notes — Econometric Validity Checks"):
        st.markdown("### Stationarity (Augmented Dickey-Fuller Test)")
        st.markdown(
            "OLS regression on time-series data can produce spuriously high R² if the "
            "outcome drifts over time (unit root). The ADF test checks for this."
        )

        if adf.get('sufficient_data'):
            if adf['stationary']:
                st.success(
                    f"✓ **Stationary** (ADF p = {adf['p']:.4f}). "
                    "The Mental_Health series has no unit root — "
                    "regression results are not inflated by a shared long-run trend."
                )
            else:
                st.warning(
                    f"⚠ **Possible unit root** (ADF p = {adf['p']:.4f}). "
                    "Consider first-differencing the outcome before drawing strong conclusions "
                    "from R² values."
                )
            st.caption(
                f"ADF statistic: {adf['stat']:.4f} | Lags: {adf['lags']} | "
                + " | ".join(f"{k}: {v:.3f}" for k, v in adf['crit'].items())
            )
            st.pyplot(sp.plot_stationarity_visual(df_int), use_container_width=True)
        else:
            st.warning("Not enough data for stationarity test.")

        st.markdown("### Reverse Causality / Endogeneity Check")
        st.markdown(
            "Does *low mood yesterday* predict *more substance use today*? "
            "If yes, causality runs both ways and OLS coefficients for that substance "
            "likely overstate the negative causal effect."
        )

        endo_sufficient = [r for r in endo if r.get('sufficient_data')]
        if endo_sufficient:
            endo_fig = sp.plot_endogeneity(endo, df_int)
            if endo_fig:
                st.pyplot(endo_fig, use_container_width=True)

            for r in endo_sufficient:
                sub = r['substance']
                if r['reverse_causal']:
                    st.warning(
                        f"**{sub}**: lower mood yesterday → more use today "
                        f"(Δ = {r['diff']:+.2f}, p = {r['p']:.4f}). "
                        "Endogeneity is empirically relevant — treat the OLS coefficient "
                        "as an upper bound on the causal effect."
                    )
                elif r['recreational']:
                    st.info(
                        f"**{sub}**: higher mood yesterday → more use today "
                        f"(Δ = {r['diff']:+.2f}, p = {r['p']:.4f}). "
                        "Consistent with recreational use rather than mood coping."
                    )
                else:
                    st.success(
                        f"**{sub}**: no significant reverse causality "
                        f"(p = {r['p']:.4f}). "
                        "The OLS coefficient is less likely to be endogeneity-biased."
                    )
        else:
            st.info("Insufficient data for endogeneity check.")

        st.markdown("### Model Assumptions")
        st.markdown("""
| Assumption | How addressed |
|---|---|
| **Weak exogeneity** | Habits coded as *end-of-day* self-report; morning mood may still influence daily habits |
| **Stationarity** | ADF test above — see result |
| **Autocorrelation** | `MH_lag1` absorbs first-order autocorrelation; HAC SEs correct for residual |
| **No structural breaks** | Year-over-year plot in Comparison tab provides visual check |
| **Linearity of dosage** | All habit variables are binary — caffeine quantity available but not modeled here |
""")
