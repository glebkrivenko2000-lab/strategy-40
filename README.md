# ⚡️ Crypto Execution Engine & Quantitative Pipeline

A production-ready algorithmic trading execution engine built for Bybit V5 Perpetual Futures. This project demonstrates a robust infrastructure designed to execute mid-to-high frequency systematic trading strategies while maintaining strict risk controls.

> **⚠️ Note on Proprietary Alpha:** 
> The core predictive logic, statistical features (e.g., Cross-Asset Kaufman's Efficiency Ratio routing, micro-structure wick filtering), and optimized hyper-parameters have been redacted from `src/strategy/momentum_alpha.py` to protect intellectual property. The repository contains a dummy SMA-based strategy to demonstrate the architecture's interface.

## 🏗 Core Architecture

The system is built on **SOLID principles**, isolating external I/O from business logic.

*   **`ExecutionEngine`**: Handles exchange interactions via `ccxt`. Manages tick-size/lot-size precision rounding and applies server-side Stop-Loss orders synchronously to mitigate network disconnect risks.
*   **`BaseStrategy` Interface**: Allows quantitative researchers to plug in new Alpha models without altering the execution or risk modules. Pure function processing of Pandas DataFrames.
*   **`ProgressiveRiskManager`**: The backbone of the system. Implements a multi-tier dynamic Circuit Breaker.
*   **State Persistence**: Idempotent state recovery using locked JSON/SQLite storage. If the container restarts, the bot seamlessly resumes active position tracking and cooldown enforcement.
*   **Asynchronous Telemetry**: Non-blocking background thread running a Telegram bot for real-time alerts and PnL reporting.

## 🛡 Progressive Circuit Breaker (Risk Management)

Crypto markets are prone to sudden regime shifts (e.g., liquidation cascades). To prevent the algorithm from "tilting" or overtrading during highly correlated market crashes, the `ProgressiveRiskManager` enforces strict cooling-off periods:

-   **Tier 1 (L1):** Single Stop-Loss hit -> **7-hour pause.** (Allows local volatility to settle).
-   **Tier 2 (L2):** Two consecutive Stop-Losses -> **120-hour pause.** (Signals a potential mid-term regime shift).
-   **Tier 3 (L3):** 2 out of 3 recent trades hit SL *AND* cumulative PnL drops below -5% -> **30-day hard stop.** (Total strategy invalidation; requires human review).

## 🚀 Tech Stack
*   **Language:** Python 3.10+
*   **Data Processing:** `pandas`, `numpy`
*   **Exchange API:** `ccxt`
*   **Concurrency:** `threading`
*   **Deployment:** Designed for `Docker` / `PM2` on headless Linux instances.

## ⚙️ Installation & Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crypto-execution-engine.git
   cd crypto-execution-engine
