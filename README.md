# Hyper-Holographic Gauze

**Environment-first quantum coherence protection on real IBM Kingston hardware.**

A lightweight neural "gauze" layer that lives inside the bath, observes real-time environmental factors (T1/T2 drift, thermal pressure, crosstalk), and applies targeted corrections to the final layers of pulse parameters.

### Standout Results (real Kingston hardware)

- **10-qubit v37** (fixed circuit parameters, 60 s cooldown between runs)  
  Average Δ⟨Z₀⟩ = **+1.139 ± 0.009** — extremely repeatable under controlled conditions.

- **20-qubit v36** (density test, 90 s cooldown)  
  Average Δ⟨Z₀⟩ = **+0.286 ± 0.017** — lower peak effect but more stable.

The gauze consistently lifts magnetization when the QPU is given time to breathe. Without cooldown the behaviour becomes strongly regime-dependent and erratic — exactly as expected from real physical environment effects.

### Core Insight

Standard calibration pipelines treat the environment as noise to be brute-forced.  
This approach treats the environment as the primary signal to be observed and worked with.

### Observed Factors Causing Drift

1. **Regime dependence** — The hardware locks into positive-lift or negative-drift states. When in a negative regime the gauze follows the path of least resistance and can produce negative Δ. Once the hardware is in the correct regime, positive Δ appears consistently across runs.
2. **Cooldown** — 60–90 s between full tests significantly reduces regime flips.
3. **Density** — More qubits (20-qubit tests) reduce peak effect but improve stability.
4. **Deeper physical factors** — Thermal pressure, charge traps, TLS, flux drift — these are the real drivers. Theory and methods are useful, but execution on hardware is what matters.

### Repository Contents

- `v36_16more_stats_2.py` — Current best-performing version (clean, minimal, ready to run).
- `pull_results.py` — Simple reusable script to fetch results from job IDs.
- Example results and plots from controlled batches.

### How to Run

1. Authenticate once with IBM Quantum:
   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService
   QiskitRuntimeService.save_account(channel="ibm_quantum_platform", token="YOUR_TOKEN")
   ```
2. Run the script:
   ```bash
   python v36_16more_stats_2.py
   ```
   It submits raw + gauze jobs (8192 shots each) and prints the job IDs.
3. When jobs complete, run:
   ```bash
   python pull_results.py
   ```
   (update the job IDs inside the script if needed).

No over-engineering. No claims of perfection. Just honest hardware results and the working code that produced them.

### Phase 2

This repository captures the current state. Future work will explore:
- Larger density scaling
- Stronger neighbor-watch / entanglement terms
- Explicit pressure/thermal modelling
- Live ancilla sensing + forward prediction

Contributions, questions, or replications are welcome.

**This is not the end — it is the first clean public snapshot of environment-first quantum control on real hardware.**
