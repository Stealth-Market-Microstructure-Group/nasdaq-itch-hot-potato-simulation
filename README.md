# NASDAQ-ITCH Market Microstructure Simulation: Hot Potato Effect

This repository is part of an ongoing research effort by **Stealth Market Microstructure Group (SMMG Research)** focused on studying event-level dynamics in electronic limit order markets.

The project is experimental in nature and serves as a foundation for larger-scale research involving high-frequency market data, agent-based simulation, and market microstructure phenomena such as the *hot potato effect*.

This repository is **not intended for trading or strategy deployment**. Its sole purpose is research, experimentation, and methodological exploration.

---

## Research Context

Market microstructure models necessarily rely on simplifying assumptions. This project explores how certain empirically observed behaviors — particularly rapid inventory turnover and inter-agent trade propagation (commonly referred to as the *hot potato effect*) — manifest within a limit order book setting.

While similar effects have been studied extensively in FX markets, their behavior and structure within equity limit order markets remain comparatively underexplored. This research focuses on *what is observed* at the event level rather than attempting to explain *why agents behave this way*. Behavioral explanations are part of ongoing and future research outputs.

The research direction has received informal academic feedback and encouragement from researchers in market microstructure and finance, reinforcing the relevance and complexity of the problem space.

---

## System Scope

The system is designed as a modular research simulator capable of:

- Processing **event-by-event ITCH market data**
- Reconstructing limit order book state transitions
- Simulating agent interaction with the book
- Supporting order placement, cancellation, update, and execution flows
- Enabling controlled experimentation with agent inventories and interaction dynamics

A custom matching engine is implemented to ensure deterministic and reproducible replay of historical market events.

---

## Data & Infrastructure

This project is built with scalability as a primary design constraint and is intended to integrate with:

- High-performance computing (HPC) environments
- Terabyte-scale historical market datasets
- Object storage systems (e.g., S3-compatible storage)
- Streaming and pipeline architectures (e.g., Kafka-based ingestion)

**Data is not included in this repository.**  
The system is compatible with publicly available ITCH-format datasets as well as institutional-grade market data accessed through research collaboration.

---

## Methodological Notes

- The simulator prioritizes structural correctness over optimization
- The goal is to preserve causal event ordering and microstructure integrity
- Agent logic is intentionally abstracted and not exposed in this repository
- The focus is on observability and experimental control, not performance benchmarking

Visual artifacts, handwritten derivations, and internal research notes are intentionally excluded from this public repository.

---

## Minimal Execution Path (Research Evaluation Only)

This repository is **not designed as a plug-and-play tool**.  
However, a minimal execution path is provided for architectural and behavioral inspection.

### Entry Point

The primary simulation entry point is:
`hot_potato_sim/new_main_sim_real_match_V7.py`

To run the simulator:

1. Clone the repository  
2. Place compatible ITCH-style event data in the designated placeholder paths  
3. Execute the entry-point script  

No data is bundled with this repository.

---

## Runtime Output

During execution, the simulator continuously rewrites a log file:
`best_bid_ask_live.log`

This file reflects the current best bid and ask levels and is updated on each simulation step, providing a lightweight, real-time view of market state evolution that mimics a live feed.

Full detailed system logs and event message appear in terminal window.

---

## Project Status

This repository represents an **active research experiment**.

Ongoing and planned work includes:

- Large-scale agent-based experimentation
- Analysis of trade propagation chains and inventory dynamics
- Integration with terabyte-scale historical market data
- Expansion into distributed compute and storage environments

The system is designed to scale as additional data access and research collaboration becomes available.

---

## Access & Usage

This repository is intended for:
- Research collaborators
- Academic exploration
- Technical evaluation of system architecture

It is not intended for:
- Trading
- Strategy development
- Production deployment

---

## Contributors

- **David M.**  
  Strategic Advisor  
  Key guidance and advice; expertise from 20+ years in proprietary trading firms

- **Pankaj J.**  
  Tech Lead & Research Architect  
  System design, simulator code & architecture, and agent interaction logic

- **Bhavik P.**  
  Data Engineering Contributor  
  ITCH parsing, data pipelines, and streaming code & infrastructure

---

## Disclaimer

This project is for research purposes only.  
No financial advice, trading recommendation, or investment guidance is provided or implied.

---

For collaboration or inquiries, please contact:  
[spcmer@gmail.com](mailto:spcmer@gmail.com) or [p737917355@gmail.com](mailto:p737917355@gmail.com)

