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

## Why `OrderExecuted` Can Be Safely Treated as Market Flow

NASDAQ ITCH does not explicitly encode whether an execution was initiated by a market order or by an aggressive limit order crossing the spread.  
An `OrderExecuted` message only reports that a resting order on the book was partially or fully filled, without identifying the precise order type of the incoming aggressor.

At first glance, this ambiguity raises a concern: reconstructing executions as market orders may appear to conflate distinct order types.

However, this distinction is not material at the point of execution.

In continuous limit order markets, any aggressive order that crosses the spread—whether a true market order or a limit order priced above the best ask (for buys) or below the best bid (for sells)—is immediately matched against the best available resting liquidity. The matching process, price–time priority, and queue consumption behavior are identical in both cases. The only difference is that an aggressive limit order carries a price cap, whereas a market order does not.

Crucially, this price constraint does not alter execution behavior when the order is immediately executable. At the moment of matching, both order types represent intentional liquidity-taking actions and function equivalently from the perspective of the order book.

As a result, even though ITCH does not distinguish between market orders and aggressive limit orders in `OrderExecuted` messages, treating executions as synthetic market orders preserves the correct microstructural interpretation: an active aggressor consuming resting liquidity.

Therefore, reconstructing market orders from `OrderExecuted` messages is not a distortion of historical behavior, but a structurally faithful representation of aggressive order flow. This approach ensures that all executions pass through the same matching logic, respect queue dynamics, and generate realistic market impact within the agent-based simulator.

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
