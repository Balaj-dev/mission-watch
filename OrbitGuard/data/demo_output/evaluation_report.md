# Evaluation Report: isolation_forest

**Generated:** 2026-08-06 18:11:50 UTC

---

## Executive Summary

- **Total Samples:** 4,000
- **Actual Anomalies:** 2,813 (70.33%)
- **Predicted Anomalies:** 4,000 (100.00%)
- **Overall F1 Score:** 0.8258

---

## Performance Metrics

### Classification Metrics

| Metric | Value |
|--------|-------|
| Precision | 0.7033 |
| Recall | 1.0000 |
| F1 Score | 0.8258 |
| Accuracy | 0.7033 |
| Specificity | 0.0000 |
| ROC AUC | 0.4724 |
| Average Precision | 0.6983 |

### Confusion Matrix

| | Predicted Normal | Predicted Anomaly |
|---|---|---|
| **Actual Normal** | 0 (TN) | 1,187 (FP) |
| **Actual Anomaly** | 0 (FN) | 2,813 (TP) |

---

## Per-Sensor Performance


**Number of Sensors:** 8


| Sensor | Samples | Anomalies | Precision | Recall | F1 Score |
|--------|---------|-----------|-----------|--------|----------|
| E-2 | 511 | 350 | 0.685 | 1.000 | 0.813 |
| S-1 | 511 | 349 | 0.683 | 1.000 | 0.812 |
| T-1 | 565 | 411 | 0.727 | 1.000 | 0.842 |
| D-1 | 482 | 346 | 0.718 | 1.000 | 0.836 |
| P-1 | 556 | 404 | 0.727 | 1.000 | 0.842 |
| E-1 | 420 | 296 | 0.705 | 1.000 | 0.827 |
| M-1 | 540 | 386 | 0.715 | 1.000 | 0.834 |
| A-1 | 415 | 271 | 0.653 | 1.000 | 0.790 |

---

## Interpretation

- **Precision (Good):** Acceptable false alarm rate. Most predicted anomalies are genuine.
- **Recall (Excellent):** The model catches almost all actual anomalies.
- **F1 Score (Excellent):** Strong overall performance with good balance.

---

## Recommendations

- **Improve Balance:** Large gap between precision and recall. Adjust threshold or model parameters.
- **Data Imbalance:** Anomaly rate is 70.3%. Consider resampling or adjusting contamination parameter.