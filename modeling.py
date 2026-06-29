
# Run after preprocessing.py. Trains 4 models, evaluates and compares them,
# plots ROC curves and feature importances, saves all models to models/

# import
import pandas as pd
import numpy as np
import pickle
import os
import matplotlib.pyplot as plt

from sklearn.linear_model      import LogisticRegression
from sklearn.tree               import DecisionTreeClassifier
from sklearn.ensemble           import RandomForestClassifier
from xgboost                    import XGBClassifier

#comparison metrics
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    ConfusionMatrixDisplay
)

#configuration
PROCESSED_PATH = 'data/processed/preprocessed_data.pkl'
MODELS_DIR     = 'models/'

#load data using pickle
def load_data():
    with open(PROCESSED_PATH, 'rb') as f:
        data = pickle.load(f)
    print(f"✅ Loaded data — Train: {data['X_train'].shape} | Test: {data['X_test'].shape}")
    return data

#evaluate a single model
def evaluate_model(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    print(f"  Accuracy : {acc:.4f}")
    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Not Paid','Paid'])}")

    # Confusion matrix
    fig, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_test, y_pred,
        display_labels=['Not Paid', 'Paid'],
        ax=ax, colorbar=False
    )
    ax.set_title(f'Confusion Matrix — {name}')
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}confusion_{name.lower().replace(' ', '_')}.png")
    plt.show()

    return {'name': name, 'accuracy': acc, 'roc_auc': auc, 'y_prob': y_prob}

# Plot ROC curves for all models 
def plot_roc_curves(results, y_test):
    plt.figure(figsize=(10, 6))
    colors = ['steelblue', 'salmon', 'green', 'purple']

    for r, color in zip(results, colors):
        fpr, tpr, _ = roc_curve(y_test, r['y_prob'])
        plt.plot(fpr, tpr, color=color,
                 label=f"{r['name']} (AUC = {r['roc_auc']:.3f})")

    plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve — All Models')
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}roc_curves.png")
    plt.show()
    print(f"✅ Saved → {MODELS_DIR}roc_curves.png")

#Plot feature importance (tree-based models only) 
def plot_feature_importance(model, feature_names, name, top_n=15):
    if not hasattr(model, 'feature_importances_'):
        return  # logistic regression skipped here

    importances = pd.Series(model.feature_importances_, index=feature_names)
    top = importances.sort_values(ascending=False).head(top_n)

    top.plot(kind='bar', figsize=(12, 5), color='steelblue', edgecolor='white')
    plt.title(f'Top {top_n} Feature Importances — {name}')
    plt.ylabel('Importance')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}importance_{name.lower().replace(' ', '_')}.png")
    plt.show()

#Define all models
def get_models(y_train):
    # class_weight='balanced' handles class imbalance automatically
    imbalance_ratio = len(y_train[y_train == 0]) / len(y_train[y_train == 1])

    return {
        'Logistic Regression': LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced'
        ),
        'Decision Tree': DecisionTreeClassifier(
            max_depth=5,
            random_state=42,
            class_weight='balanced'
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        ),
        'XGBoost': XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss',
            scale_pos_weight=imbalance_ratio   # handles class imbalance for XGBoost
        )
    }

# train all models & compare
def train_models():
    data     = load_data()
    X_train  = data['X_train']
    X_test   = data['X_test']
    y_train  = data['y_train']
    y_test   = data['y_test']
    features = data['feature_names']

    os.makedirs(MODELS_DIR, exist_ok=True)
    models  = get_models(y_train)
    results = []

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        # Evaluate
        result = evaluate_model(name, model, X_test, y_test)
        results.append(result)

        # Feature importance plot
        plot_feature_importance(model, features, name)

        # Save model
        save_path = f"{MODELS_DIR}{name.lower().replace(' ', '_')}.pkl"
        with open(save_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"  Saved → {save_path}")

    # final comparison table
    print("\n\n" + "="*55)
    print("  MODEL COMPARISON")
    print("="*55)
    comparison = pd.DataFrame([{
        'Model'   : r['name'],
        'Accuracy': round(r['accuracy'], 4),
        'ROC-AUC' : round(r['roc_auc'],  4)
    } for r in results]).sort_values('ROC-AUC', ascending=False)

    print(comparison.to_string(index=False))

    # roc
    plot_roc_curves(results, y_test)

    return results, comparison

#run
if __name__ == '__main__':
    results, comparison = train_models()