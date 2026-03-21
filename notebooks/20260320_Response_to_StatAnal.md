# Habit Tracking — Statistical Analysis
**Katy Yut** **March 20, 2026**

## Goals
Investigate correlations and potential causal relationships between daily habits and mental health (rated 1–10).

**Key questions:**
1. Does exercise make me feel better?
2. Do I make my bed more often when I was sober the day before?
3. Does dancing make me happier?
4. Do drugs (alcohol/weed) have a negative impact on mental health?

## Statistical Approach
| Test | When used |
|---|---|
| Point-biserial correlation | Boolean habit vs continuous Mental_Health |
| Mann-Whitney U | Compare Mental_Health distributions (habit done vs not done) |
| OLS multiple regression | All habits simultaneously predicting Mental_Health |
| Lagged correlation | Yesterday's habit vs today's outcome |
| Logistic regression | Boolean outcome (e.g. Made_Bed) predicted by prior-day habits |
| Pearson correlation | Habit-habit associations (treating booleans as 0/1) |

## Assumptions & Caveats
- **Observational data only**: correlation ≠ causation. Lagged effects strengthen causal arguments but cannot prove them.
- **Analysis restricted to active tracking period** (`HT_START_DATE = 2022-06-17`) to avoid bias from sparse early data.
- **Mental_Health is ordinal** (1–10 integer) but treated as continuous here. 
- **Multiple comparisons**: Bonferroni-corrected threshold is noted to avoid false positives.
- **Missing data**: Rows with missing outcomes are dropped per-analysis, not imputed.

---

# 0. Setup

```python
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from habit_tracking.tracker import HabitTracker
from habit_tracking import config

# Consistent visual style
plt.rcParams.update({
    'figure.dpi': 120,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.size': 11,
})
PALETTE = sns.color_palette('muted')

tracker = HabitTracker()
tracker.load_and_clean()

print(f'Full dataset: {len(tracker.df):,} rows')
```

---

# 1. Data Preparation

```python
tracker.plot_prep(start_date=config.HT_START_DATE)

# Only keep days where a form was actually submitted that day
df = tracker.df[tracker.df['Tracked_Habits'] == True].copy()
df = df.reset_index(drop=True)

HABIT_COLS = [col for col in config.NA_AS_TRUE.keys() if col in df.columns]
OUTCOME = 'Mental_Health'

# Cast booleans to int (0/1)
df_int = df[HABIT_COLS + [OUTCOME, 'Date']].copy()
df_int['Date'] = pd.to_datetime(df_int['Date'])
for col in HABIT_COLS:
    df_int[col] = df_int[col].astype(int)
df_int[OUTCOME] = pd.to_numeric(df_int[OUTCOME], errors='coerce')

# Seasonal Mapping
df_int['Month'] = df_int['Date'].dt.month
df_int['Season'] = df_int['Month'].map({
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall',   10: 'Fall',  11: 'Fall',
})
```

---

# 2. Descriptive Overview

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
mh = df_int[OUTCOME].dropna()

# Histogram
axes[0].hist(mh, bins=range(1, 12), align='left', color=PALETTE[0], rwidth=0.8)
axes[0].set_title('Mental Health Distribution')

# Rolling 30-day average
ts = df_int[['Date', OUTCOME]].dropna().set_index('Date').sort_index()
rolling = ts[OUTCOME].rolling(30, min_periods=7).mean()
axes[1].plot(ts.index, ts[OUTCOME], alpha=0.25, color=PALETTE[0])
axes[1].plot(rolling.index, rolling, color=PALETTE[0], linewidth=2, label='30-day avg')
axes[1].set_title('Mental Health Over Time')
plt.show()
```

---

# 3. Habit → Mental Health Correlations

```python
results = []
analysis_df = df_int.dropna(subset=[OUTCOME])

for habit in HABIT_COLS:
    done = analysis_df.loc[analysis_df[habit] == 1, OUTCOME]
    not_done = analysis_df.loc[analysis_df[habit] == 0, OUTCOME]

    if len(done) < 10 or len(not_done) < 10: continue

    r, p_r = stats.pointbiserialr(analysis_df[habit], analysis_df[OUTCOME])
    u_stat, p_mw = stats.mannwhitneyu(done, not_done, alternative='two-sided')

    results.append({
        'Habit': habit,
        'MH_diff': done.mean() - not_done.mean(),
        'p_mannwhitney': p_mw,
    })

results_df = pd.DataFrame(results)
_, p_bh, _, _ = multipletests(results_df['p_mannwhitney'], method='fdr_bh')
results_df['p_BH'] = p_bh
results_df['sig_BH'] = results_df['p_BH'] < 0.05
```

---

# 4. Lagged Effects — Yesterday's Habits Today

```python
lag_df = df_int.sort_values('Date').copy()
for col in HABIT_COLS:
    lag_df[f'{col}_lag1'] = lag_df[col].shift(1)

# Ensure consecutive days
lag_df['Gap'] = (lag_df['Date'] - lag_df['Date'].shift(1)).dt.days
lag_df = lag_df[lag_df['Gap'] == 1].copy()

# Q2: Does being sober yesterday predict making your bed today?
lag_df['Sober_lag1'] = ((lag_df['Alcohol_lag1'] == 0) & (lag_df['Weed_lag1'] == 0)).astype(float)
contingency = pd.crosstab(lag_df['Sober_lag1'], lag_df['Made_Bed'])
chi2, p_chi, _, _ = stats.chi2_contingency(contingency)
print(f'Sobriety → Bed Chi-sq p-value: {p_chi:.4f}')
```

---

# 5. Multiple Regression

```python
reg_df = df_int.dropna(subset=[OUTCOME]).copy()
sufficient_habits = [h for h in HABIT_COLS if reg_df[h].sum() >= 20]

X = sm.add_constant(reg_df[sufficient_habits])
y = reg_df[OUTCOME]
model = sm.OLS(y, X).fit()
print(model.summary())
```

---

# Expert Review & Theoretical Adjustments

You have built a remarkably robust analysis. Using **Benjamini-Hochberg corrections** and **Mann-Whitney U** tests shows a level of statistical rigor that goes far beyond a typical "hobbyist" project. 

However, compared to the "Econometrics Refresher" plan, there are specific **structural adjustments** needed to move from correlation to a more defensible causal model.

### 1. Comparison & Corrections: The "Delta"

| Statistical Concept | What You Did | The "Econ" Adjustment Needed |
| :--- | :--- | :--- |
| **Autocorrelation** | Checked lagged habits ($X_{t-1} \rightarrow Y_t$) | **Add a Lagged Dependent Variable ($Y_{t-1}$)** to your OLS. In mood data, $Y_t$ is highly dependent on $Y_{t-1}$. Without this, your habit coefficients are likely overestimating the "lift." |
| **Stationarity** | Visualized rolling averages. | **Run an Augmented Dickey-Fuller (ADF) Test.** If $p > 0.05$, your $R^2$ is likely inflated by shared trends (spurious correlation). |
| **Exogeneity** | Used Lagged Correlations. | **Check for Simultaneity.** Does "Low Mood $\rightarrow$ Drinking"? If so, Alcohol is endogenous. Consider a 2SLS approach if you have an instrument (e.g., "Day of the week"). |
| **Error Structure** | Used OLS with standard errors. | **Use Newey-West Standard Errors.** Since this is time-series, your errors are likely heteroscedastic and autocorrelated (HAC). |

---

### 2. Updating Your Assumptions Checklist

1.  **Assumption of Weak Exogeneity:** You are assuming your habits today aren't a *reaction* to your mood earlier this morning.
2.  **Assumption of Stationarity:** You assume your mental health scale (1–10) has a constant mean and variance over the years.
3.  **No Structural Breaks:** You assume no major life events (job change, move, etc.) shifted the *entire* relationship between habits and mood.
4.  **Linearity of Dosage:** You assume the effect of a habit is linear (e.g., the 1st cup of coffee has the same marginal effect as the 5th).

---

### 3. Recommended Code Adjustments

To get that "econometrics-grade" $R^2$ and coefficient list, modify your Section 5 as follows:

```python
# 1. Create the Lagged Dependent Variable
reg_df['MH_lag1'] = reg_df['Mental_Health'].shift(1)

# 2. Re-run OLS with the lag included
sufficient_habits_with_lag = sufficient_habits + ['MH_lag1']
clean_df = reg_df.dropna(subset=['MH_lag1'])
X = sm.add_constant(clean_df[sufficient_habits_with_lag])
y = clean_df['Mental_Health']

# 3. Use HAC (Newey-West) standard errors
model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 1})
print(model.summary())
```



**Next Step Recommendation:** Check the **Durbin-Watson** stat in your current OLS summary. If it's far from 2.0 (e.g., < 1.5), you definitely have autocorrelation that needs to be addressed with the `MH_lag1` variable above.