import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')           # headless – no display needed
import matplotlib.pyplot as plt
import seaborn as sns

RAW_PATH       = 'ppm_dummy_data.csv'
PROCESSED_PATH = 'data/processed/cleaned_data.csv'
HEATMAP_PATH   = 'data/processed/correlation_heatmap.png'
TARGET         = 'Current_Pdc removedt (maritaview)
# Marital_S)t+ Gender added explicitly
STRONG_FEATURES = [
    'Recency', 'Never_Paid',           # Never_Paid engineered from Recency=9999
    'Current_per', 'Previous_Total_Due', 'PAttempts',
    'PSMSs', 'Xdays_per', 'PContacts', 'Account_Age', 'Deliquency',
    'Case_Age', 'Current_Due', '30days_per', 'Xdays_Due',
    'PRPCs', '90days_per', 'Previous_Payment_Perc', 'Due_90days',
    'Previous_Payment', 'Previous_Payment_Amount', 'Due_30days',
    'Due_120days', 'Existing_Account', '120days_per',
    'Marital_Status', 'Gender',        # demograph─────────────────────────────────
def load_data(path):
    df = pd.read_csv(path)
    print(f"Loaded : {df.shape[0]:,} rows × {df.shapeduplicates─────────────────────────────────
def drop_duplicates(df):
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Duplicates removed : {before - len(df):,} → {len(df):,removing deceased─────────────────────────────────────────
def remove_deceased(df):
    """Drop rows where a deceased/dead flag is set to 1 / 'Y' / True."""
    deceased_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ('deceas', 'dead', 'death'))),
        None
    )
    if deceased_col is None:
        print("Deceased column : not found — skipping")
        return df
    before = len(df)
    # Handle numeric (1) and string ('Y','yes','true') flags
    mask = df[deceased_col].astype(str).str.strip().str.lower().isin(
        {'1', '1.0', 'y', 'yes', 'true'}
    )
    df = df[~mask].reset_index(drop=True)
    print(f"Deceased removed   : {before - len(df):,} rows → {len(df):,} remainingmissing >0.70g columns ────────────────────────────────────────────────────
def drop_high_missing(df, threshold=0.70):
    missing_pct  = df.isnull().mean()
    cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
    df = df.drop(columns=cols_to_drop)
    print(f"High-missing (>{threshold:.0%}) dropdrop near constants - uselessar-constant columns ───────────────────────────────────────────────────
def drop_near_constant(df, threshold=0.95, protect=None):
    """
    Drop columns where one value (including NaN) covers ≥ threshold of rows.
    `protect` columns (e.g. target, demographic keys) are never dropped.
    """
    protect = set(protect or []) | {TARGET}
    near_const = [
        col for col in df.columns
        if col not in protect
        and df[col].value_counts(normalize=True, dropna=False).iloc[0] >= threshold
    ]
    df = df.drop(columns=near_const)
    print(f"Near-constant (≥{old:.0%}) dropped : {near_const} df


# ── 6. Leakage, EagleEye, BookKeep, DC ────────────────────────────────────────
def drop_leakage_and_useless(df):
    """
    Drop:
      • data-leakage columns
      • all-zero columns (no variance)
      • EagleEye columns  (irrelevant external score)
      • BookKeep / loan columns  (irrelevant bureau data)
      • DC column  (remoit is  feature-review)
    """
    explicit = [
        'Current_Payment_Amount',   # leakage: IS the target value
        'Current_Cure',             # all zeros
        'Previous_Cure',            # all zeros
        'DC',                       # removed per review
    ]
    eagleeye = [c for c in df.columns if 'eagle' in c.lower()]
    bookeep  = [c for c in df.columns
                if any(k in c.lower() for k in ('bookeep', 'book_keep', 'bookkeep', 'loan_'))]

    drop_cols = list(dict.fromkeys(explicit + eagleeye + bookeep))   # deduplicated, ordered
    drop_cols = [c for c in drop_cols if c in df.columns]
    df = df.drop(columissing vlues, 9999]} cols left")
    return df


# ── 7. Fix sentinel / - flag as never paid - make Nan?───────fix_missing_codes(df):
    """
    • Recency = 9999  →  flag as Never_Paid = 1, then NaN the raw value
    • Global 9999 rplacement- important_Account, Credit_Risk
    • 99 in Income_Band
    """
    # Recency 9999 = customer has *never paid* – meaningful signal
    if 'Recency' in df.columns:
        df.insert(
            df.columns.get_loc('Recency') + 1,
            'Never_Paid',
            (df['Recency'] == 9999).astype(int)
        )
        n = df['Never_Paid'].sum()
        print(f"Never_Paid flag      : {n:,} customers with Recency=9999")

    df = df.replace(9999, np.nan)

    for col in ('Existing_Account', 'Credit_Risk'):
        if col in df.columns:
            df[col] = df[col].replace(-1, np.nan)
    if 'Income_Band' in df.columns:
        df['Income_Bangender- me_Band'].replace(99,d : {df.isnull().sum().sum():,} NaNs total")
    return df


# ── 8. Gender: clean & drop NaN rows ──────────────────────────────────────────
def clean_gender(df):
    """
    After 9999→NaN replacement, drop any rows where Gender is unknown/missing.
    Keeps only rows with a valid recorded gender.
    """
    if 'Gender' not in df.columns:
        print("Gender column : not found — skipping")
        return df
    before = len(df)
    df = dffill remaining nulls w medianed   : {before - len(df):,} rows → {len(df):,} remaining")
    return df


# ── 9. Fill remaining nulls ────────────────────────────────────────────────────
def fill_missing(df):
    num_cols = df.select_dtypes(include='number').columns.difference([TARGET]).tolist()
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    remaining = df.isnuEXPLORE RECENCY- from claudeng "
          f"({'only non-numeric' if remaining else 'clean'})")
    return df


# ── 10. Explore Recency ────────────────────────────────────────────────────────
def explore_recency(df):
    """Print Recency distribution and payment-rate breakdown by bucket."""
    if 'Recency' not in df.columns:
        print("Recency exploration : column not found — skipping")
        return

    print("\n────── Recency Exploration ──────")
    print(df['Recency'].describe().rename(lambda x: f"  {x}").to_string())

    if 'Never_Paid' in df.columns:
        print(f"\n  Never-paid customers (flagged)  : {df['Never_Paid'].sum():,}")
    print(f"  Zero recency (most recent)      : {(df['Recency'] == 0).sum():,}")

    if TARGET in df.columns:
        tmp = df.copy()
        bins   = [-1, 0, 30, 60, 90, 120, float('inf')]
        labels = ['0 (same day)', '1-30', '31-60', '61-90', '91-120', '120+']
        tmp['_bucket'] = pd.cut(tmp['Recency'], bins=bins, labels=labels)
        grp = (tmp.groupby('_bucket', observed=True)[TARGET]
                  .agg(count='count', pay_rate='mean')
                  .rename(columns={'count': 'Count', 'pay_rate': 'Payment Rate'}))
 feature selectionprint(f"\n  {TARGET} by Recency bucket:\n{grp.to_string()}")
    print("─────────────────────────────────\n")


# ── 11. Feature selection ──────────────────────────────────────────────────────
def select_features(df):
    """Keep strong features + target; always retain Marital_Status and Gender."""
    cols = [c for c in STRONG_FEATURES + [TARGET] if c in df.columns]
    # Safety net: explicitly protect demographic columns if somehow excluded
    for extra in ('Marital_Status', 'Gender', 'Never_Paid'):
        if extra in df.columns and extcorrelation heatmapRGET
    df = df[cols]
    print(f"Features selected    : {len(cols) - 1} features + target → {df.shape}")
    return df


# ── 12. Correlation heatmap ────────────────────────────────────────────────────
def make_correlation_heatmap(df, save_path=HEATMAP_PATH):
    """Save a full-feature correlation heatmap, highlighting target correlations."""
    num_df = df.select_dtypes(include='number')
    corr   = num_df.corr()

    n      = len(corr)
    fig_w  = max(14, n * 0.55)
    fig_h  = max(11, n * 0.48)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    mask = np.zeros_like(corr, dtype=bool)   # show full matrix (not upper-triangle only)

    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt='.2f',
        cmap='RdYlGn',
        center=0,
        vmin=-1, vmax=1,
        linewidths=0.35,
        linecolor='#dddddd',
        annot_kws={'size': 7},
        cbar_kws={'shrink': 0.75, 'label': 'Pearson r'},
        ax=ax,
    )
    ax.set_title('Feature Correlation Heatmap', fontsize=15, fontweight='bold', pad=14)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.ytiMutual reindex- from claudedirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Heatmap saved        : {save_path}")


# ── 13. Mutual reindex ────────────────────────────────────────────────────────
def mutual_reindex(df):
    """
    Reset to a clean 0-based integePipeline summary- From CLauderies y stay in perfect alignment.
    """
    df = df.reset_index(drop=True)
    print(f"Index reset          : {len(df):,} rows, 0-based, fully aligned")
    return df


# ── Pipeline ───────────────────────────────────────────────────────────────────
def clean(path=RAW_PATH):
    print("=" * 52)
    print("  DATA CLEANING PIPELINE")
    print("=" * 52)

    df = load_data(path)                          # 1. load
    df = drop_duplicates(df)                      # 2. duplicates
    df = remove_deceased(df)                      # 3. deceased
    df = drop_high_missing(df)                    # 4. >70% missing cols
    df = drop_leakage_and_useless(df)             # 5. leakage / EagleEye / BookKeep / DC
    df = fix_missing_codes(df)                    # 6. 9999 / -1 / 99  →  NaN + Never_Paid flag
    df = clean_gender(df)                         # 7. drop NaN gender rows
    df = drop_near_constant(df,                   # 8. near-constant cols
             protect=['Marital_Status', 'Gender', 'Never_Paid'])
    df = fill_missing(df)                         # 9. median imputation
    explore_recency(df)                           # 10. explore (no mutation)
    df = select_features(df)                      # 11. feature selection
    make_correlation_heatmap(df)                  # 12. heatmap
    df = mutual_reindex(df)                       # 13. clean index alignment

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"\n✓ Cleaned data saved : {PROCESSED_PATH}")
    print(f"  Final shape        : {df.shape[0]:,} rows × {df.shape[1]} cols")
    print("=" * 52)
    return df


if __name__ == '__main__':
    df_cleaned = clean()
    print("\nSample output:")
    print(df_cleaned.head())
