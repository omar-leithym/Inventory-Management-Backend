# Discount Tier Recommendation Model Documentation

## 1. Problem definition and objective

The objective of this system is to recommend an operationally safe discount level for time-sensitive inventory such that expected sell-through improves while unnecessary margin loss is avoided. The recommendation is formulated as a multi-class classification problem, where each class corresponds to a discrete discount tier in increments of 5 percentage points from 0% to 40% (inclusive). This discretization reflects how discounts are typically executed in operations, and it ensures that recommendations remain within policy bounds and remain interpretable by staff.

The system receives a snapshot of the current state of an item (stock remaining, expected baseline demand over a remaining time window, and context identifiers such as item and store). It outputs a single discount tier intended to improve alignment between expected demand and inventory remaining before the selling window ends.

## 2. Output space and tier encoding

The model produces a discount tier \( y \in \{0, 5, 10, 15, 20, 25, 30, 35, 40\} \). Internally, this set can be represented as class indices \(\{0,\dots,8\}\) for training and inference convenience, but the API returns the tier in percentage units.

This constrained output space is important for deployment because it prevents invalid recommendations and supports straightforward operational execution.

## 3. System overview

The deployed inference logic is organized as a decision pipeline with two complementary components:

1. **A learned multi-class classifier** that estimates which discount tier is most appropriate given the current state of inventory pressure and expected demand.
2. **A rule-based elasticity component** that provides a stable inductive bias when data coverage is sparse, and that serves as a controlled fallback when requests appear out-of-distribution or when the model signal is weak.

A user-facing parameter called **aggressiveness** modulates the trade-off between these two components and tunes how strongly the system prioritizes sell-through over margin protection.

## 4. API inputs and feature definitions

### 4.1 Required inputs

**amount_left (number).**  
This feature represents the current stock remaining for the item. It is the central operational constraint because the discount decision is intended to control how quickly inventory is depleted. Larger values indicate a higher risk of leftover stock if remaining time is limited.

**expected_demand_for_remaining (number).**  
This feature represents the expected baseline demand in the remaining time window if no additional discount were applied. It can be produced by a separate demand forecasting module or by historical averages. This feature is essential because discounting should be applied primarily when baseline demand is insufficient to clear inventory.

**item_id (integer).**  
This identifier provides item-level context that captures persistent differences in popularity, seasonality, and price sensitivity across products. Items are heterogeneous, and a single global mapping from inventory pressure to discount is rarely optimal without item identity.

### 4.2 Optional inputs

**num_items_targeted (integer, default: 1).**  
This feature indicates how many items are being targeted by the same promotion decision. It matters because a promotion applied to multiple items can interact with substitution effects and can change the effective demand allocation across items.

**now_ts_unix (integer, default: server time in seconds).**  
This timestamp anchors the request in time. Time is relevant because demand patterns vary by hour and day, and because the meaning of “remaining window” is time-dependent. Using server time as a default reduces client complexity while keeping the system consistent.

**window_end_ts_unix (integer).**  
This value defines the end of the selling window as an absolute timestamp. If provided, it overrides window_hours and enables precise remaining-time computation, which is important when the decision horizon is anchored to a fixed operational cutoff (for example, store closing time).

**window_hours (number, default: 3.0).**  
This value defines the remaining horizon in hours when an explicit end timestamp is not provided. Remaining time affects discount urgency because less time implies less opportunity for demand to materialize at baseline.

**pct_grid (array[number]).**  
This is the candidate set of discount rates expressed as decimals (for example, 0.0 to 0.4). In inference, the system may evaluate multiple candidate discounts and select the best tier under the scoring policy. A grid mechanism supports scenario evaluation and makes the system robust to business constraints that restrict certain tiers.

**baseline_pct (number, default: 0.0).**  
This feature represents the existing discount baseline. It is useful when a promotion is already active and the system is asked to revise it. In that setting, the relevant decision is an adjustment rather than a new discount from scratch.

**place_id (integer).**  
This identifier provides store-level context. Stores differ in foot traffic, customer mix, and local habits. Store identity therefore improves generalization and reduces the risk of transferring one store’s discount behavior to a different store with different demand characteristics.

**aggressiveness (number, default: 5.0, range 0..10).**  
This parameter tunes the decision policy. Lower aggressiveness places greater weight on margin protection and typically yields smaller discounts, while higher aggressiveness places greater weight on sell-through and typically yields larger discounts. In implementation terms, aggressiveness can influence the weighting between learned predictions and rule-based estimates and can shift the internal coverage target for clearing inventory.

**return_debug (boolean, default: false).**  
When enabled, the system returns a structured explanation of how each candidate discount in the grid was evaluated. This option supports monitoring, validation, and stakeholder trust without changing the core decision.

**debug_limit (integer, default: 200).**  
This parameter caps the number of debug rows to avoid oversized responses, particularly if pct_grid is large or if multiple items are evaluated.

**reload (boolean, default: false).**  
This option forces artifact reload from disk for debugging or administrative use. In production it should be disabled and protected, because it can increase latency and can interact with deployment safety practices.

## 5. Why these features are appropriate for this problem

The decision problem can be summarized as a constrained trade-off: discounts increase expected demand (and therefore sell-through) but reduce revenue per unit. The system therefore requires features that quantify:

1. **Inventory pressure**, captured primarily by amount_left.
2. **Baseline demand**, captured by expected_demand_for_remaining.
3. **Time remaining**, captured by window_end_ts_unix or window_hours (with now_ts_unix as an anchor).
4. **Heterogeneity across items and venues**, captured by item_id and place_id.
5. **Operational and policy controls**, captured by baseline_pct, pct_grid, num_items_targeted, and aggressiveness.

This set is intentionally compact because it is feasible to compute reliably in real time and because it aligns directly with the causal structure of the decision.

## 6. Inference-time decision policy

At inference time, the system constructs the remaining-time representation using either window_end_ts_unix (if provided) or window_hours (otherwise). It then considers candidate tiers defined by pct_grid, mapped onto the tier set \{0,5,…,40\}.

For each candidate tier, the system assigns a score that reflects expected sell-through benefit and discount cost. The learned classifier provides probability mass across tiers, while the rule-based component provides a smooth uplift estimate as a function of discount level. The final score is computed as a weighted combination of these signals. The aggressiveness parameter adjusts the weighting and the acceptance thresholds, thereby changing the preference for higher tiers when inventory pressure is high.

The final output is the tier with the best score under this policy, subject to hard bounds of the tier set.

## 7. Learning formulation

The learned component is trained as a multi-class classifier over the discount tiers. Each training example corresponds to a historical decision or an engineered target label that represents a preferred tier under the training objective. The input representation matches the inference-time feature set so that training and deployment are consistent.

Tier classification is appropriate because it matches the action space used in deployment, supports calibrated probabilities, and reduces sensitivity to noise in historical logs. In discount systems, near-by tiers (for example, 15% versus 20%) often have similar operational effect, and classification tends to be more robust than unconstrained regression when labels are discretized by policy.

## 8. Practical constraints and robustness considerations

Promotion and sales logs often contain missing fields, inconsistent timestamps, and business-rule exceptions. For this reason, the deployed API focuses on high-signal fields that can be computed consistently and includes explicit controls for time-window computation and tier grids.

The inclusion of a rule-based fallback improves stability under distribution shift, such as newly introduced items with limited history or stores with atypical traffic patterns. Debug outputs are available to support monitoring and to enable rapid diagnosis of failures or surprising recommendations.

## 9. Interpretability and debugging

When return_debug is enabled, the response includes a candidate-level table that reports the evaluation of each candidate discount tier. This table is intended to show intermediate quantities used for ranking, such as learned preference or probability, rule-based uplift estimates, and the final composite score. This design supports transparency and provides actionable information to operators and developers without exposing sensitive model internals.

## 10. Summary

This system recommends a discrete discount tier from 0% to 40% in steps of 5%. It uses stock remaining and expected baseline demand as the primary decision drivers, incorporates time remaining to capture urgency, and uses item and store identifiers to account for heterogeneity. A combined learned-and-rule decision policy, controlled by an aggressiveness parameter, enables the system to trade off sell-through and margin in a manner that is tunable and operationally robust.
