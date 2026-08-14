# SupportSense Dataset Profile

## Dataset

Sprint 1 uses the BANKING77 dataset for customer-support intent
classification.

The dataset contains two supplied splits:

| Split | Records | Intents |
|---|---:|---:|
| Train | 10,003 | 77 |
| Test | 3,080 | 77 |

The test set contains exactly 40 examples for each of the 77 intents.

## Data Quality

The current validation results are:

- Train null text: 0
- Train null category: 0
- Test null text: 0
- Test null category: 0
- Train duplicate rows: 0
- Test duplicate rows: 0
- Train duplicate texts: 0
- Test duplicate texts: 0
- Cross-split text overlap: 0
- Intent vocabulary mismatch between train and test: none

## Text Characteristics

### Training set

| Statistic | Value |
|---|---:|
| Minimum characters | 13 |
| Maximum characters | 433 |
| Mean characters | 59.47 |
| Median characters | 47 |
| Minimum words | 2 |
| Maximum words | 79 |
| Mean words | 11.95 |
| Median words | 10 |

### Test set

| Statistic | Value |
|---|---:|
| Minimum characters | 13 |
| Maximum characters | 368 |
| Mean characters | 54.23 |
| Median characters | 45 |
| Minimum words | 2 |
| Maximum words | 69 |
| Mean words | 10.95 |
| Median words | 9 |

The test queries are slightly shorter on average than the training
queries. This difference is observed descriptively and is not by itself
treated as evidence of significant distribution shift.

## Intent Distribution

The training-set intent counts range from 35 to 187 examples.

| Statistic | Value |
|---|---:|
| Minimum class count | 35 |
| Maximum class count | 187 |
| Mean class count | 129.91 |
| Median class count | 127 |
| Imbalance ratio | approximately 5.34 |

The training set contains:

- 2 intents with fewer than 50 examples.
- 11 intents with fewer than 100 examples.
- 66 intents with at least 100 examples.

The smallest training classes are:

- `contactless_not_working`: 35
- `virtual_card_not_working`: 41
- `card_acceptance`: 59
- `card_swallowed`: 61
- `lost_or_stolen_card`: 82

The largest training classes are:

- `card_payment_fee_charged`: 187
- `direct_debit_payment_not_recognised`: 182
- `balance_not_updated_after_cheque_or_cash_deposit`: 181
- `wrong_amount_of_cash_received`: 180
- `cash_withdrawal_charge`: 177

## Initial ML Implications

The training distribution is not perfectly balanced, although most intents
have a substantial number of examples.

The imbalance ratio is approximately 5.34. Therefore, model evaluation
should not rely exclusively on accuracy.

Macro-F1, per-class metrics, and confusion matrices will be considered
important evaluation tools.

No oversampling or class-weighting strategy is applied at this stage.
Potential imbalance mitigation will be evaluated experimentally after a
baseline model has been established.

The intent vocabulary also contains several semantically related groups,
such as card-payment, transfer, and top-up intents. Confusion between
closely related intents will therefore be an important area of later model
analysis.
