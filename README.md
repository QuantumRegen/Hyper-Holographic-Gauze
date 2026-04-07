# Hyper-Holographic Gauze

**Environment-first quantum coherence protection on real IBM Kingston hardware.**

A small neural "gauze" layer that lives inside the bath, observes real-time environmental factors (T1/T2 drift, thermal pressure, crosstalk), and applies targeted corrections to the last layers of pulse parameters.

### Standout Results (real Kingston hardware)

- **10-qubit v37** (fixed circuit, 60 s cooldown):  
  Average Δ<Z0> = **+1.139** ± 0.009 (extremely repeatable across controlled runs).

- **20-qubit v36** (density test, 90 s cooldown):  
  Average Δ<Z0> = **+0.286** ± 0.017 (more stable, lower peak effect).

The gauze consistently lifts magnetization when the QPU is given time to breathe. Without cooldown the behaviour becomes regime-dependent and erratic — exactly as expected from real physical environment effects.

### Core Insight
Standard calibration pipelines treat the environment as noise to be brute-forced.  
This approach treats the environment as the primary signal to be observed and worked with.

### Repository Contents
- `v37_final.py` — the current best-performing version (clean, minimal, ready to run).
- `pull_results.py` — simple reusable script to fetch results from job IDs.
- Example results and plots from controlled batches.

### How to Run
1. Authenticate with IBM Quantum (`QiskitRuntimeService.save_account(...)`).
2. Run `v37_final.py` (submits raw + gauze jobs).
3. Use `pull_results.py` with the printed job IDs once complete.

No over-engineering. No claims of perfection. Just honest hardware results and the working code that produced them.

### Phase 2
This repository captures the current state. Future work will explore larger density (more qubits), stronger neighbor-watch terms, and explicit pressure/thermal modelling.

Contributions, questions, or replications are welcome.

**This is not the end — it's the first clean public snapshot.**
