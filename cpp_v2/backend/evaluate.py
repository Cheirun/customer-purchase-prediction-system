# evaluate.py
# -------------------------------------------------
# calculates metrics and draws evaluation charts
# using 5 metrics because accuracy alone is misleading
# especially when classes are a bit imbalanced
# -------------------------------------------------

import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
    ConfusionMatrixDisplay, roc_curve
)

sns.set_theme(style='whitegrid')
CHART_DIR = 'static/charts'


def _save(fig, name):
    os.makedirs(CHART_DIR, exist_ok=True)
    fig.savefig(f'{CHART_DIR}/{name}.png', bbox_inches='tight')
    plt.close(fig)
    print(f'  [eval] saved → {name}.png')


def get_metrics(name, model, X_test, y_test):
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None

    return {
        'Model'    : name,
        'Accuracy' : round(accuracy_score(y_test, preds), 4),
        'Precision': round(precision_score(y_test, preds, zero_division=0), 4),
        'Recall'   : round(recall_score(y_test, preds, zero_division=0), 4),
        'F1'       : round(f1_score(y_test, preds, zero_division=0), 4),
        'ROC_AUC'  : round(roc_auc_score(y_test, probs), 4) if probs is not None else None,
    }


def evaluate_all(trained_models, X_test, y_test):
    print('[eval] computing metrics...')
    rows = []
    for name, model in trained_models.items():
        m = get_metrics(name, model, X_test, y_test)
        rows.append(m)
        print(f'  {name:<22}  acc={m["Accuracy"]}  f1={m["F1"]}  auc={m["ROC_AUC"]}')

    df = pd.DataFrame(rows).set_index('Model')
    best = df['F1'].idxmax()
    print(f'\n[eval] best model by F1: {best} ({df.loc[best,"F1"]})\n')
    return df


def draw_confusion_matrices(trained_models, X_test, y_test):
    n   = len(trained_models)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    fig.suptitle('Confusion Matrices — Test Set', fontweight='bold')

    for ax, (name, mdl) in zip(axes, trained_models.items()):
        cm = confusion_matrix(y_test, mdl.predict(X_test))
        ConfusionMatrixDisplay(cm, display_labels=["No Buy", "Buy"]).plot(
            ax=ax, colorbar=False, cmap='Blues'
        )
        ax.set_title(name, fontsize=9)

    fig.tight_layout()
    _save(fig, '06_confusion_matrices')


def draw_roc_curves(trained_models, X_test, y_test):
    fig, ax = plt.subplots(figsize=(7, 5))
    palette = ['#3dba8c', '#e05c5c', '#5b8dee', '#f59e0b']

    for (name, mdl), color in zip(trained_models.items(), palette):
        if hasattr(mdl, 'predict_proba'):
            probs = mdl.predict_proba(X_test)[:, 1]
            fpr, tpr, _ = roc_curve(y_test, probs)
            auc = roc_auc_score(y_test, probs)
            ax.plot(fpr, tpr, label=f'{name}  (AUC={auc:.3f})', color=color, lw=2)

    ax.plot([0,1],[0,1], 'k--', lw=1, alpha=0.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curves', fontweight='bold')
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, '07_roc_curves')


def draw_metrics_bar(summary_df):
    cols = ['Accuracy', 'Precision', 'Recall', 'F1', 'ROC_AUC']
    plot_df = summary_df[cols].astype(float)

    fig, ax = plt.subplots(figsize=(11, 5))
    plot_df.plot(kind='bar', ax=ax, edgecolor='white', width=0.72)
    ax.set_title('Model Comparison — All Metrics', fontweight='bold')
    ax.set_ylabel('Score')
    ax.set_ylim(0, 1.12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    _save(fig, '08_metric_comparison')


def draw_feature_importance(rf_model, feature_names):
    imp = pd.Series(rf_model.feature_importances_, index=feature_names).sort_values()

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(imp.index, imp.values, color='#5b8dee', edgecolor='white')
    ax.set_xlabel('Importance')
    ax.set_title('Random Forest — Feature Importance', fontweight='bold')
    for bar, val in zip(bars, imp.values):
        ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=8)
    fig.tight_layout()
    _save(fig, '09_feature_importance')


def run_evaluation(trained_models, X_test, y_test, feature_names):
    summary = evaluate_all(trained_models, X_test, y_test)
    draw_confusion_matrices(trained_models, X_test, y_test)
    draw_roc_curves(trained_models, X_test, y_test)
    draw_metrics_bar(summary)
    draw_feature_importance(trained_models['Random Forest'], feature_names)

    # save as json for the API
    records = summary.reset_index().to_dict(orient='records')
    with open('model_scores.json', 'w') as fh:
        json.dump(records, fh)
    print('[eval] scores saved to model_scores.json')

    return summary


if __name__ == '__main__':
    from data_loader   import load_data
    from preprocessing import preprocess
    from train_models  import train

    df  = load_data()
    Xtr, Xte, ytr, yte, sc, feats = preprocess(df)
    models = train(Xtr, ytr)
    run_evaluation(models, Xte, yte, feats)
