# -------------------------------------------------------
def plot_feature_importance(model, feature_names, name, top_n=15):
    """
    Bar chart of which features (columns) the model found most useful.

    Only works for Decision Tree, Random Forest, and XGBoost.
    Logistic Regression doesn't have feature_importances_ so we skip it.

    Parameters:
        model         - trained model
        feature_names - list of column names from the dataframe
        name          - model name string (used in the plot title)
        top_n (int)   - how many top features to display, default is 15
    """

    # logistic regression doesnt have this so skip it quietly
    if not hasattr(model, 'feature_importances_'):
        print(f"  Skipping feature importance for {name} — not a tree-based model")
        return

    # pair up each feature name with its importance score, then sort highest first
    importances = pd.Series(model.feature_importances_, index=feature_names)
    top = importances.sort_values(ascending=False).head(top_n)

    top.plot(kind='bar', figsize=(12, 5), color='steelblue', edgecolor='white')
    plt.title(f'Top {top_n} Feature Importances — {name}')
    plt.ylabel('Importance')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}importance_{name.lower().replace(' ', '_')}.png")
    plt.show()


# -------------------------------------------------------
def get_models(y_train):
    """
    Defines all 4 models with their settings and returns them as a dict.

    I picked these 4 because they range from simple → complex:
        1. Logistic Regression  (simple linear baseline)
        2. Decision Tree        (easy to interpret)
        3. Random Forest        (lots of trees, more stable)
        4. XGBoost              (usually best performance but harder to tune)

    All of them are set up to handle class imbalance since we have a lot
    more 'Not Paid' rows than 'Paid' rows.

    Parameters:
        y_train - training labels, needed to calculate the imbalance ratio

    Returns:
        dict of {model_name: model_object}
    """

    # work out how imbalanced the classes are
    # e.g. 900 not paid vs 100 paid → ratio = 9.0
    # this number gets passed to XGBoost below
    imbalance_ratio = len(y_train[y_train == 0]) / len(y_train[y_train == 1])
    print(f"\n  Class imbalance ratio (0s / 1s): {imbalance_ratio:.2f}")  # just to check

    return {

        # --- simple starting model, good baseline to beat ---
        'Logistic Regression': LogisticRegression(
            max_iter=1000,           # default 100 sometimes isnt enough, causes warning
            random_state=42,         # makes results repeatable
            class_weight='balanced'  # auto adjusts for imbalance
        ),

        # --- single tree, simple but can overfit if not limited ---
        'Decision Tree': DecisionTreeClassifier(
            max_depth=5,             # stops tree going too deep and memorising training data
            random_state=42,
            class_weight='balanced'
        ),

        # --- 100 trees averaged together, more reliable than one tree ---
        'Random Forest': RandomForestClassifier(
            n_estimators=100,        # number of trees to build
            max_depth=5,             # cap each tree at depth 5
            random_state=42,
            class_weight='balanced',
            n_jobs=-1                # use all cpu cores so it trains faster
        ),

        # gradient boosting, builds trees one at a time fixing previous mistakes 
        # TODO: try tuning learning_rate and n_estimators more later
        'XGBoost': XGBClassifier(
            n_estimators=100,              # how many boosting rounds
            max_depth=4,                   # slightly shallower since its boosted already
            learning_rate=0.1,             # how much each new tree contributes (0.1 = safe default)
            random_state=42,
            eval_metric='logloss',         # loss function for binary classification
            scale_pos_weight=imbalance_ratio  # handling class imbalance
        )
    }