"""
habit_tracking/stats.py

Statistical analyses on habit tracking data.

All public functions are pure (no side effects on tracker state) and return
plain Python types (DataFrames, dicts, lists) so they are compatible with
Streamlit's st.cache_data caching.
"""
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller

from habit_tracking import config

OUTCOME = 'Mental_Health'

# Numeric predictors that replace (or supplement) their boolean counterparts.
# Structure: boolean_col -> (numeric_col, zero_fill_value, display_label, unit)
# zero_fill_value is substituted when the boolean is False and the numeric is NaN
# (i.e., no caffeine consumed = 0 mg, no mindfulness = 0 minutes).
NUMERIC_PREDICTORS = {
    'Caffeine':    ('Caffeine_Quantity_mg', 0.0, 'Caffeine',    'mg'),
    'Mindfulness': ('Mindfulness_mins',     0.0, 'Mindfulness', 'minutes'),
}
# Minimum number of non-zero observations required to include a numeric predictor
MIN_NUMERIC_OBS = 50

SEASON_MAP = {
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall', 10: 'Fall', 11: 'Fall',
}


def get_habit_cols(df: pd.DataFrame) -> list:
    """Return habit columns present in df, in config order, excluding computed cols."""
    return [col for col in config.NA_AS_TRUE.keys() if col in df.columns]


def build_analysis_df(tracker_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare an analysis-ready DataFrame from tracker.df.

    Filters to:
        - Active tracking window (HT_START_DATE onward)
        - Days with a form submission that matches the date (Tracked_Habits == True)

    Returns df_int with:
        - Boolean habit columns cast to int (0/1)
        - Mental_Health as float
        - Date as pd.Timestamp (so .dt accessor works downstream)
        - Year, Month, Season columns
    """
    df = tracker_df.copy()
    df = df[pd.to_datetime(df['Date']) >= pd.to_datetime(config.HT_START_DATE)]
    df = df[df['Tracked_Habits'] == True].reset_index(drop=True)

    habit_cols = get_habit_cols(df)

    df_int = df[habit_cols + [OUTCOME, 'Date']].copy()
    df_int['Date'] = pd.to_datetime(df_int['Date'])
    for col in habit_cols:
        df_int[col] = df_int[col].astype(int)
    df_int[OUTCOME] = pd.to_numeric(df_int[OUTCOME], errors='coerce')
    df_int['Year'] = df_int['Date'].dt.year
    df_int['Month'] = df_int['Date'].dt.month
    df_int['Season'] = df_int['Month'].map(SEASON_MAP)

    # ── Numeric predictors ────────────────────────────────────────────────────
    # For each boolean habit that has a numeric quantity column, add it to df_int
    # with 0 substituted on non-use days (so "no caffeine" = 0 mg, not NaN).
    for bool_col, (num_col, fill_val, _, _) in NUMERIC_PREDICTORS.items():
        if num_col not in df.columns or bool_col not in df.columns:
            continue
        vals = pd.to_numeric(df[num_col], errors='coerce')
        # Where boolean is False and quantity is NaN → substitute fill_val (0)
        is_non_use = (df[bool_col].astype(int) == 0) & vals.isna()
        vals = vals.copy()
        vals.loc[is_non_use] = fill_val
        df_int[num_col] = vals.values

    return df_int


def build_lag_df(df_int: pd.DataFrame) -> pd.DataFrame:
    """
    Build a lagged dataset — consecutive tracked days only.

    For each habit column, adds a {habit}_lag1 column (yesterday's value).
    Rows where the prior day was NOT tracked (gap > 1) are dropped entirely
    to avoid carrying lags across breaks in the series.
    """
    habit_cols = get_habit_cols(df_int)
    lag = df_int.sort_values('Date').copy()

    for col in habit_cols:
        lag[f'{col}_lag1'] = lag[col].shift(1)

    # Also lag the outcome so endogeneity checks can reuse this df
    lag[f'{OUTCOME}_lag1'] = lag[OUTCOME].shift(1)

    gap = (lag['Date'] - lag['Date'].shift(1)).dt.days
    lag = lag[gap == 1].copy()
    return lag


def run_habit_mh_correlations(df_int: pd.DataFrame) -> pd.DataFrame:
    """
    For each habit, compute:
        - Point-biserial correlation vs Mental_Health (same day)
        - Mann-Whitney U test (habit done vs not done)
        - BH-corrected p-values

    Returns DataFrame sorted by MH_diff descending.
    Habits with fewer than 10 observations in either group are excluded.
    """
    habit_cols = get_habit_cols(df_int)
    analysis = df_int.dropna(subset=[OUTCOME])
    rows = []

    for habit in habit_cols:
        done = analysis.loc[analysis[habit] == 1, OUTCOME]
        not_done = analysis.loc[analysis[habit] == 0, OUTCOME]
        if len(done) < 10 or len(not_done) < 10:
            continue

        r, _ = scipy_stats.pointbiserialr(analysis[habit], analysis[OUTCOME])
        _, p_mw = scipy_stats.mannwhitneyu(done, not_done, alternative='two-sided')

        rows.append({
            'Habit': habit,
            'N_done': len(done),
            'N_not_done': len(not_done),
            'MH_done_mean': round(done.mean(), 3),
            'MH_not_done_mean': round(not_done.mean(), 3),
            'MH_diff': done.mean() - not_done.mean(),
            'r': r,
            'p_mannwhitney': p_mw,
        })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    _, p_bh, _, _ = multipletests(out['p_mannwhitney'], method='fdr_bh')
    out['p_BH'] = p_bh
    out['sig_BH'] = out['p_BH'] < 0.05
    return out.sort_values('MH_diff', ascending=False).reset_index(drop=True)


def run_lagged_mh(lag_df: pd.DataFrame) -> pd.DataFrame:
    """
    Test whether yesterday's habit predicts today's Mental_Health.
    Mirrors run_habit_mh_correlations but uses _lag1 columns as predictors.
    Returns DataFrame sorted by MH_diff descending.
    """
    habit_cols = get_habit_cols(lag_df)
    analysis = lag_df.dropna(subset=[OUTCOME])
    rows = []

    for habit in habit_cols:
        lag_col = f'{habit}_lag1'
        if lag_col not in analysis.columns:
            continue
        sub = analysis.dropna(subset=[lag_col])
        done = sub.loc[sub[lag_col] == 1, OUTCOME]
        not_done = sub.loc[sub[lag_col] == 0, OUTCOME]
        if len(done) < 10 or len(not_done) < 10:
            continue

        _, p_mw = scipy_stats.mannwhitneyu(done, not_done, alternative='two-sided')
        rows.append({
            'Habit': habit,
            'MH_next_done': done.mean(),
            'MH_next_not_done': not_done.mean(),
            'MH_diff': done.mean() - not_done.mean(),
            'p_mannwhitney': p_mw,
        })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    _, p_bh, _, _ = multipletests(out['p_mannwhitney'], method='fdr_bh')
    out['p_BH'] = p_bh
    out['sig_BH'] = out['p_BH'] < 0.05
    return out.sort_values('MH_diff', ascending=False).reset_index(drop=True)


def run_sobriety_bed_test(lag_df: pd.DataFrame) -> dict:
    """
    Q2: Does being sober yesterday predict making your bed today?
    'Sober' = no Alcohol AND no Weed the prior day.

    Returns a dict with rates, chi-squared stat, and significance flag.
    Returns {'sufficient_data': False} if n < 20 in either group.
    """
    ld = lag_df.copy()
    if 'Alcohol_lag1' not in ld.columns or 'Weed_lag1' not in ld.columns:
        return {'sufficient_data': False}

    mask = ld['Alcohol_lag1'].notna() & ld['Weed_lag1'].notna()
    ld.loc[mask, 'Sober_lag1'] = (
        (ld.loc[mask, 'Alcohol_lag1'] == 0) & (ld.loc[mask, 'Weed_lag1'] == 0)
    ).astype(float)

    sub = ld.dropna(subset=['Sober_lag1', 'Made_Bed'])
    if len(sub) < 20:
        return {'sufficient_data': False}

    sober_rate = sub.loc[sub['Sober_lag1'] == 1, 'Made_Bed'].mean()
    substance_rate = sub.loc[sub['Sober_lag1'] == 0, 'Made_Bed'].mean()
    sober_n = int((sub['Sober_lag1'] == 1).sum())
    substance_n = int((sub['Sober_lag1'] == 0).sum())

    contingency = pd.crosstab(sub['Sober_lag1'], sub['Made_Bed'])
    chi2, p_chi, _, _ = scipy_stats.chi2_contingency(contingency)

    return {
        'sufficient_data': True,
        'sober_rate': float(sober_rate),
        'substance_rate': float(substance_rate),
        'sober_n': sober_n,
        'substance_n': substance_n,
        'chi2': float(chi2),
        'p': float(p_chi),
        'significant': p_chi < 0.05,
        'diff_pct': float((sober_rate - substance_rate) * 100),
    }


def run_numeric_correlations(df_int: pd.DataFrame) -> pd.DataFrame:
    """
    Spearman correlation between numeric predictors and Mental_Health.

    Spearman is used because:
        - Mental_Health is ordinal (1–10 integers)
        - Caffeine_Quantity_mg and Mindfulness_mins are right-skewed
          (many zeros, with a long tail of higher values)

    For each numeric predictor we also compute:
        - Linear slope (MH change per unit, e.g. per mg or per minute)
        - % of days with non-zero value (to flag sparse predictors)

    Returns an empty DataFrame if no numeric predictors have sufficient data.
    """
    analysis = df_int.dropna(subset=[OUTCOME])
    rows = []

    for bool_col, (num_col, _, label, unit) in NUMERIC_PREDICTORS.items():
        if num_col not in analysis.columns:
            continue
        sub = analysis[[num_col, OUTCOME]].dropna()
        n_nonzero = int((sub[num_col] > 0).sum())
        if n_nonzero < MIN_NUMERIC_OBS:
            continue

        r_sp, p_sp = scipy_stats.spearmanr(sub[num_col], sub[OUTCOME])
        # Linear slope gives an interpretable "per-unit" effect size
        slope, intercept, r_lin, p_lin, _ = scipy_stats.linregress(
            sub[num_col], sub[OUTCOME]
        )

        rows.append({
            'Variable':      num_col,
            'Label':         label,
            'Unit':          unit,
            'Bool_col':      bool_col,
            'N_total':       len(sub),
            'N_nonzero':     n_nonzero,
            'Pct_nonzero':   round(100 * n_nonzero / len(sub), 1),
            'Spearman_r':    round(r_sp, 4),
            'p_spearman':    float(p_sp),
            'slope':         float(slope),       # MH points per unit
            'p_linear':      float(p_lin),
            'significant':   p_sp < 0.05,
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def run_regression(df_int: pd.DataFrame) -> dict:
    """
    OLS with:
        - Lagged dependent variable (MH_lag1) to absorb autocorrelation
        - HAC (Newey-West) standard errors for heteroscedastic, autocorrelated residuals
        - Durbin-Watson check on residuals
        - Numeric versions of Caffeine / Mindfulness used instead of booleans
          to capture dose-response effects (e.g. 300mg caffeine ≠ 50mg)

    Habits with fewer than 20 observed days (or non-zero rows for numeric) excluded.
    Lags that cross a tracking gap are nulled out.

    Returns a dict of plain types (no statsmodels objects) safe for caching.
    """
    habit_cols = get_habit_cols(df_int)
    reg_df = df_int.dropna(subset=[OUTCOME]).copy().sort_values('Date')

    # Start with boolean habits that meet the observation threshold
    sufficient = [h for h in habit_cols if reg_df[h].sum() >= 20]

    # Swap boolean predictors for their numeric counterparts where available.
    # The numeric column is already 0-filled for non-use days in build_analysis_df,
    # so it directly replaces the boolean without losing information.
    # Track replacements for the 'numeric_swaps' annotation in results.
    numeric_swaps = {}
    final_predictors = []
    for h in sufficient:
        if h in NUMERIC_PREDICTORS:
            num_col, _, label, unit = NUMERIC_PREDICTORS[h]
            if num_col in reg_df.columns:
                n_nonzero = int((reg_df[num_col] > 0).sum())
                if n_nonzero >= MIN_NUMERIC_OBS:
                    final_predictors.append(num_col)
                    numeric_swaps[h] = {
                        'numeric_col': num_col,
                        'label': label,
                        'unit': unit,
                    }
                    continue
        final_predictors.append(h)

    reg_df['MH_lag1'] = reg_df[OUTCOME].shift(1)
    gap = (reg_df['Date'] - reg_df['Date'].shift(1)).dt.days
    reg_df.loc[gap != 1, 'MH_lag1'] = np.nan

    predictors = final_predictors + ['MH_lag1']
    clean = reg_df.dropna(subset=predictors + [OUTCOME])

    if len(clean) < 30:
        return {'sufficient_data': False}

    X = sm.add_constant(clean[predictors])
    y = clean[OUTCOME]
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 1})

    # Extract habit-only coefficients (exclude const and MH_lag1)
    drop_keys = [k for k in ['const', 'MH_lag1'] if k in model.params.index]
    coef = model.params.drop(drop_keys)
    conf = model.conf_int().drop(drop_keys)
    pv = model.pvalues.drop(drop_keys)

    coef_df = pd.DataFrame({
        'Habit': coef.index,
        'Coef': coef.values,
        'CI_low': conf[0].values,
        'CI_high': conf[1].values,
        'p': pv.values,
    }).sort_values('Coef').reset_index(drop=True)
    coef_df['sig'] = coef_df['p'] < 0.05

    dw = float(sm.stats.durbin_watson(model.resid))

    # Full params table (including MH_lag1) for display
    full_conf = model.conf_int()
    params_table = pd.DataFrame({
        'Predictor': model.params.index,
        'Coef': model.params.values,
        'CI_low': full_conf[0].values,
        'CI_high': full_conf[1].values,
        'p': model.pvalues.values,
    })
    params_table['sig'] = params_table['p'] < 0.05

    return {
        'sufficient_data': True,
        'coef_df': coef_df,
        'params_table': params_table,
        'r_squared': float(model.rsquared),
        'r_squared_adj': float(model.rsquared_adj),
        'aic': float(model.aic),
        'n_obs': int(model.nobs),
        'dw_stat': dw,
        'mh_lag_coef': float(model.params.get('MH_lag1', np.nan)),
        'mh_lag_p': float(model.pvalues.get('MH_lag1', np.nan)),
        # Which boolean habits were replaced by their numeric counterparts
        'numeric_swaps': numeric_swaps,
    }


def run_stationarity(df_int: pd.DataFrame) -> dict:
    """
    Augmented Dickey-Fuller test on the Mental_Health time series.

    H0: series has a unit root (non-stationary — OLS R² may be inflated).
    H1: series is stationary (mean-reverting — OLS is appropriate).

    Returns dict with test results and a boolean 'stationary' flag.
    """
    series = (
        df_int[['Date', OUTCOME]]
        .dropna()
        .sort_values('Date')
        .set_index('Date')[OUTCOME]
    )
    if len(series) < 20:
        return {'sufficient_data': False}

    try:
        adf_stat, adf_p, lags, _, crit, _ = adfuller(series, autolag='AIC')
    except Exception:
        return {'sufficient_data': False}

    return {
        'sufficient_data': True,
        'stat': float(adf_stat),
        'p': float(adf_p),
        'lags': int(lags),
        'crit': {k: float(v) for k, v in crit.items()},
        'stationary': adf_p < 0.05,
    }


def run_endogeneity_check(df_int: pd.DataFrame) -> list:
    """
    Reverse causality check for substance habits (Alcohol, Weed):
    Does yesterday's Mental_Health predict today's substance use?

    If lower mood predicts more use tomorrow → substance is endogenous
    (both cause and effect of mood), and OLS coefficients are biased upward.

    Returns a list of dicts, one per substance.
    """
    habit_cols = get_habit_cols(df_int)
    substances = [s for s in ['Alcohol', 'Weed'] if s in habit_cols]

    endo = df_int.sort_values('Date').copy()
    endo['MH_lag1'] = endo[OUTCOME].shift(1)
    gap = (endo['Date'] - endo['Date'].shift(1)).dt.days
    endo.loc[gap != 1, 'MH_lag1'] = np.nan
    endo = endo.dropna(subset=['MH_lag1'])

    results = []
    for substance in substances:
        sub = endo.dropna(subset=[substance, 'MH_lag1'])
        used = sub.loc[sub[substance] == 1, 'MH_lag1']
        not_used = sub.loc[sub[substance] == 0, 'MH_lag1']

        if len(used) < 10:
            results.append({'substance': substance, 'sufficient_data': False})
            continue

        _, p_mw = scipy_stats.mannwhitneyu(used, not_used, alternative='two-sided')
        diff = float(used.mean() - not_used.mean())

        results.append({
            'substance': substance,
            'sufficient_data': True,
            'mh_yesterday_used': float(used.mean()),
            'mh_yesterday_not_used': float(not_used.mean()),
            'diff': diff,
            'p': float(p_mw),
            'significant': p_mw < 0.05,
            # Lower mood yesterday → more use today = reverse causality
            'reverse_causal': p_mw < 0.05 and diff < 0,
            # Higher mood yesterday → more use today = recreational pattern
            'recreational': p_mw < 0.05 and diff > 0,
            'n_used': int(len(used)),
            'n_not_used': int(len(not_used)),
        })

    return results


def run_all(tracker_df: pd.DataFrame) -> dict:
    """
    Run all statistical analyses on tracker.df and return a nested dict.

    Intended to be called once and cached (e.g. with st.cache_data).
    All values in the returned dict are plain Python types (DataFrames, dicts,
    lists, scalars) — no statsmodels or scipy objects.
    """
    df_int = build_analysis_df(tracker_df)
    lag_df = build_lag_df(df_int)

    return {
        'df_int': df_int,
        'lag_df': lag_df,
        'habit_cols': get_habit_cols(df_int),
        'correlations': run_habit_mh_correlations(df_int),
        'numeric_correlations': run_numeric_correlations(df_int),
        'lagged_mh': run_lagged_mh(lag_df),
        'sobriety_bed': run_sobriety_bed_test(lag_df),
        'regression': run_regression(df_int),
        'stationarity': run_stationarity(df_int),
        'endogeneity': run_endogeneity_check(df_int),
    }
