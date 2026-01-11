# Electrical Metrics Reference

This document defines the electrical metrics used across the grid monitoring app (backend models and frontend charts).

## Core measurements (per sensor reading)

- **voltage_l1 / voltage_l2 / voltage_l3**: Phase-to-neutral voltages for lines L1, L2, L3 (volts). Typical LV nominal ≈ 230 V; HV varies by utility. Used to detect over/undervoltage and imbalance.
- **frequency**: System frequency (hertz). Nominal 50/60 Hz; small drift indicates instability or generation/load mismatch.

## Power quality metrics

- **thd_voltage**: Total harmonic distortion of voltage (%). Lower is better; many standards flag >5% as a warning.
- **thd_current**: Total harmonic distortion of current (%). High THD can indicate non-linear loads stressing the system.
- **power_factor**: Ratio of real to apparent power (unitless, -1 to 1). Closer to 1 means efficient transfer; low PF increases losses.
- **voltage_imbalance**: Percent difference between phase voltages (%). Imbalance harms motors and transformers; >2–3% is usually undesirable.
- **flicker_severity**: Short-term flicker severity (PU, often Pst). Values >1 typically indicate perceptible flicker to users.

## Fault events

- **fault_type**: Categorical description (e.g., short_circuit, ground_fault, overvoltage, undervoltage).
- **severity**: Categorical impact (critical, major, minor). Frontend uses colors to highlight severity.
- **voltage_drop**: Percent drop during the fault (%). Large drops suggest severe faults.
- **duration_ms**: Fault duration (milliseconds). Short durations may be transient; longer indicates sustained issues.
- **resolved**: Boolean flag indicating whether the fault is cleared.
- **description**: Free-text context for the event.

## Aggregated stats (dashboard)

- **active_sensors / total_sensors / offline_sensors**: Fleet health and connectivity.
- **avg_voltage**: Mean phase voltage across sensors (volts).
- **avg_power_factor**: Mean power factor across sensors (unitless).
- **total_faults_24h**: Count of faults in the last 24 hours.
- **quality_violations**: Count of readings violating quality thresholds (e.g., voltage limits or THD >5%).

## Display thresholds used in UI

- **Voltage chart nominal line**: 240 V reference line for visualization (PowerQualityChart when `dataKey="voltage"`).
- **THD warning line**: 5% reference line for visualization (PowerQualityChart when `dataKey="thd"`).

## Data model source

These fields come from backend Pydantic models in `backend/models.py` and are rendered in dashboard components (`GridStats`, `PowerQualityChart`, `FaultTimeline`, `GridTopology`).
