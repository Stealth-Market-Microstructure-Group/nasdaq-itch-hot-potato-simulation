# Market Order Handling in ITCH-Based Agent Simulation

## Background

NASDAQ ITCH data does not contain explicit market order messages.  
Instead, executions are reported via `OrderExecuted` messages that indicate an order on the book was partially or fully filled.

This structural property of ITCH creates a fundamental challenge when building an agent-based market simulator that aims to model realistic execution, queue dynamics, and market impact.

---

## Problem Statement

### Initial (Incorrect) Assumption

Early versions of the simulator implicitly assumed that:

- Market orders exist in the historical ITCH stream, **or**
- `OrderExecuted` messages could be treated as simple book updates without reconstructing the initiating order

As a result:

- Agent limit orders could not be filled by historical market flow
- Executions were handled as passive quantity removals rather than active matching events
- Queue position, aggressor behavior, and matching logic were effectively bypassed

---

## Consequences for Agent-Based Modeling

These assumptions led to critical failures in the simulation:

- Agent limit orders could not execute naturally
- Core matching logic (e.g. `add_match_market_order`) was rarely used
- Queue priority and price–time ordering were ignored
- Agent actions had negligible impact on market evolution

As a result, the simulator did not represent genuine agent-based market dynamics.

---

## Rejected Interim Workaround

To demonstrate effects such as the *hot potato effect*, an auxiliary agent was introduced to:

- Submit market orders that intentionally hit another agent’s limit orders
- Hedge positions using additional limit orders
- Artificially enforce execution paths

While this enabled demonstrations, it was:

- Artificial
- Fragile
- Non-scalable
- Conceptually inconsistent with true agent-based modeling

This approach was therefore rejected.

---

## Key Design Insight

Although ITCH does not expose market orders explicitly,  
**each `OrderExecuted` message implicitly represents an aggressive order.**

Therefore, executions must be modeled as **active matching events**, not passive book updates.

---

## Final Design Solution

### Synthetic Market Order Reconstruction

For each `OrderExecuted` message:

1. Extract:
   - Executed quantity
   - Side (inferred from the resting order)
2. Construct a synthetic market order with:
   - Side
   - Quantity
   - Temporary order ID
3. Route this order through the standard matching pipeline:
   - `add_match_market_order`

This ensures all executions pass through the same matching logic as agent-generated orders.

---

## Resulting Properties

After implementing this design:

- Agent limit orders can be filled by historical market flow
- Queue position and price–time priority are respected
- Both market and limit orders generate realistic market impact
- Agent actions alter the future state of the order book

If an agent does not interact, the market follows historical evolution.  
If an agent interacts, the market trajectory diverges accordingly.

---

## Summary

By reconstructing synthetic market orders from ITCH `OrderExecuted` messages and routing them through the matching engine, the simulator achieves:

- Structural consistency
- Realistic execution dynamics
- Meaningful agent–market interaction
- Research-valid outcomes

This design removes the need for artificial counterparty agents and establishes a clean foundation for future experimentation.
