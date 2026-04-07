import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import time
import seaborn as sns
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error, ReadoutError
from datetime import datetime, timezone

print("Hyper-Holographic v36_16more_stats_2 — 10-qubit (Locked Best Version)")
print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

service = QiskitRuntimeService(channel="ibm_quantum_platform")
backend = service.backend("ibm_kingston")
print(f"✅ Connected to: {backend.name}")

# Noise model
calib = pd.read_csv("ibm_kingston_calibrations_2026-04-04T09_16_43Z.csv")
noise_model = NoiseModel()
for _, row in calib.iterrows():
    q = int(row["Qubit"])
    t1 = max(float(row.get("T1 (us)", 100)) * 1e-6, 10e-6)
    t2 = max(min(float(row.get("T2 (us)", 100)) * 1e-6, 2*t1), 10e-6)
    r_err = float(row.get("Readout assignment error", 0.01))
    try:
        thermal = thermal_relaxation_error(t1, t2, 40e-9)
        noise_model.add_quantum_error(thermal, ['rx','ry','rz'], [q])
    except:
        noise_model.add_quantum_error(depolarizing_error(0.001, 1), ['rx','ry','rz'], [q])
    noise_model.add_readout_error(ReadoutError([[1-r_err, r_err],[r_err, 1-r_err]]), [q])

print("Noise model ready.")

# Locked v36 gauze (the proven best version)
class GauzeInTheBath(nn.Module):
    def __init__(self, dim=68, depth=5, slip_factor_base=0.09):
        super().__init__()
        self.dim = dim
        self.depth = depth
        self.slip_factor_base = slip_factor_base
        self.bath_embed = nn.Linear(7, dim)
        self.proj = nn.Linear(dim, dim)
        self.slip_gen = nn.Linear(dim, dim)
        self.holo_proj = nn.Linear(dim*2, dim*3)
        self.inv_holo = nn.Linear(dim*3, dim)
        self.norm = nn.LayerNorm(dim)

    def forward(self, x, bath_vector):
        h = x
        bath_emb = torch.relu(self.bath_embed(bath_vector))
        t_norm = bath_vector[0,0].clamp(0,1)
        vel = bath_vector[0,5]
        acc = bath_vector[0,6]

        predicted = vel + 0.51 * acc
        counter = 1.0 + 1.75 * torch.relu(-predicted)
        dynamic_slip = self.slip_factor_base * (1.0 - 0.48 * t_norm) * counter

        for _ in range(self.depth):
            slip = torch.tanh(self.slip_gen(h + bath_emb)) * dynamic_slip * 0.82
            h = torch.relu(self.proj(h + slip))
            h = self.norm(h)

            concat = torch.cat([h, bath_emb], dim=-1)
            boundary = self.holo_proj(concat)
            resolved = self.inv_holo(boundary)
            h = h + resolved * 0.46
            h = self.norm(h)
        return h


class CoherenceNet(nn.Module):
    def __init__(self, input_dim, dim=68):
        super().__init__()
        self.embed = nn.Linear(input_dim, dim)
        self.core = GauzeInTheBath()
        self.head = nn.Linear(dim, input_dim)

    def forward(self, x, bath):
        return self.head(self.core(self.embed(x), bath))


class KernelGauzeWrapper:
    def __init__(self):
        self.model = None
        self.input_dim = None

    def apply_gauze(self, params_last, bath_vector):
        flat_size = params_last.size
        if self.model is None or self.input_dim != flat_size:
            print(f"  Applying v36 gauze for size {flat_size}")
            self.model = CoherenceNet(input_dim=flat_size)
            self.input_dim = flat_size
            self.model.eval()
        flat = torch.from_numpy(params_last.reshape(-1).astype(np.float32)).unsqueeze(0)
        bath_t = torch.tensor(bath_vector, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            filtered = self.model(flat, bath_t)
        return filtered.numpy().reshape(params_last.shape)


kernel = KernelGauzeWrapper()

def build_10qubit_nv_chain(params, add_measure=True):
    n = 10
    qc = QuantumCircuit(n, n)
    for q in range(n):
        qc.h(q)
        qc.rx(np.pi, q)

    cx_pairs = [(1,0),(2,1),(3,2),(4,3),(4,5),(6,5),(6,7),(7,8),(8,9)]
    for ctrl, tgt in cx_pairs:
        qc.cx(ctrl, tgt)

    n_layers = params.shape[2]
    for L in range(n_layers):
        for i in range(n):
            qc.rx(params[i,0,L], i)
            qc.ry(params[i,1,L], i)
            qc.rz(params[i,2,L], i)

    if add_measure:
        qc.measure_all()
    return qc

T2_TARGET = 130e-6
def get_bath_vector(t=1e-3, prev_z0=0.0, prev_vel=0.0):
    deco = 1.0 / T2_TARGET
    norm_t = np.clip(t / 1e-3, 0, 1)
    phase = np.sin(2*np.pi*t/5e-5)*0.80
    vel = -prev_z0
    acc = vel - prev_vel
    return np.array([norm_t, deco, 120e-6, T2_TARGET, phase, vel, acc], dtype=np.float32)

def calculate_z0(counts):
    total = sum(counts.values())
    if total == 0: return 0.0
    z0 = sum(c for bs, c in counts.items() if bs[0] == '0')
    return (2 * z0 / total) - 1

# ====================== 16-RUN BATCH ======================
shots = 8192
num_runs = 16
cooldown_seconds = 60

fixed_params = 2 * np.pi * np.random.rand(10, 3, 8)   # fixed for the whole batch

results = []

print(f"\nStarting 16-run sequential batch with {cooldown_seconds}s cooldown...\n")

for i in range(num_runs):
    print(f"--- Run {i+1}/{num_runs} (fixed params) ---")

    qc_raw = build_10qubit_nv_chain(fixed_params)
    qc_raw_t = transpile(qc_raw, backend=backend, optimization_level=3)

    params_last = fixed_params[:,:,-6:].copy()
    gauze_last = kernel.apply_gauze(params_last, get_bath_vector())
    params_g = fixed_params.copy()
    params_g[:,:,-6:] = gauze_last

    qc_g = build_10qubit_nv_chain(params_g)
    qc_g_t = transpile(qc_g, backend=backend, optimization_level=3)

    sampler = Sampler(mode=backend)
    job_raw = sampler.run([qc_raw_t], shots=shots)
    job_g   = sampler.run([qc_g_t],   shots=shots)

    print(f"Raw job:   {job_raw.job_id()}")
    print(f"Gauze job: {job_g.job_id()}")

    print("Waiting for jobs to complete...")
    while job_raw.status() != "DONE" or job_g.status() != "DONE":
        time.sleep(10)

    result_raw = job_raw.result()
    result_g   = job_g.result()

    counts_raw = result_raw[0].data.meas.get_counts()
    counts_g   = result_g[0].data.meas.get_counts()

    z0_raw = calculate_z0(counts_raw)
    z0_g   = calculate_z0(counts_g)
    delta  = z0_g - z0_raw

    results.append({"run": i+1, "raw_z0": z0_raw, "gauze_z0": z0_g, "delta": delta})

    print(f"Δ = {delta:.5f}")

    time.sleep(cooldown_seconds)

# ====================== SAVE & PLOT ======================
df = pd.DataFrame(results)
df.to_csv("v36_16more_stats_2_results.csv", index=False)
print("\nResults saved to v36_16more_stats_2_results.csv")

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.histplot(df["delta"], kde=True, color="purple")
plt.title("Distribution of Δ (16 runs)")
plt.xlabel("Δ <Z0>")

plt.subplot(1, 2, 2)
sns.lineplot(x=df["run"], y=df["delta"], marker="o", color="teal")
plt.axhline(0, color="red", linestyle="--")
plt.title("Δ over Runs")
plt.xlabel("Run")
plt.ylabel("Δ")

plt.tight_layout()
plt.savefig("v36_16more_stats_2_delta_plots.png", dpi=300)
plt.show()

print("Plots saved to v36_16more_stats_2_delta_plots.png")
print(f"\nFinal average Δ: {df['delta'].mean():.5f} ± {df['delta'].std():.5f}")
