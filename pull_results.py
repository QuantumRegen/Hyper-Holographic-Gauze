from qiskit_ibm_runtime import QiskitRuntimeService

RAW_ID = "PASTE_RAW_JOB_ID_HERE"
GAUZE_ID = "PASTE_GAUZE_JOB_ID_HERE"

service = QiskitRuntimeService(channel="ibm_quantum_platform")

job_raw = service.job(RAW_ID)
job_g   = service.job(GAUZE_ID)

result_raw = job_raw.result()
result_g   = job_g.result()

counts_raw = result_raw[0].data.meas.get_counts()
counts_g   = result_g[0].data.meas.get_counts()

def calculate_z0(counts):
    total = sum(counts.values())
    if total == 0: return 0.0
    z0 = sum(c for bs, c in counts.items() if bs[0] == '0')
    return (2 * z0 / total) - 1

print(f"Raw   <Z0>: {calculate_z0(counts_raw):.5f}")
print(f"Gauze <Z0>: {calculate_z0(counts_g):.5f}")
print(f"Δ     : {calculate_z0(counts_g) - calculate_z0(counts_raw):.5f}")
