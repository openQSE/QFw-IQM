#!/usr/bin/env python3
"""Submit a one-qubit Qiskit smoke circuit through the selected backend."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qfw_iqm_util.backend import add_backend_argument, get_backend
from qfw_iqm_util.output import create_run_paths
from qfw_iqm_util.output import render_json_output
from qfw_iqm_util.output import render_text_output
from qfw_iqm_util.output import script_output_path
from qfw_iqm_util.output import to_jsonable
from qfw_iqm_util.output import write_json
from qfw_iqm_util.output import write_script_output
from qfw_iqm_util.qiskit_exec import write_qasm2_artifact


def build_smoke_circuit(flip: bool):
	try:
		from qiskit import QuantumCircuit
	except Exception as exc:
		raise RuntimeError(
			"qiskit is required for iqm_submit_smoke.py") from exc
	circuit = QuantumCircuit(1, 1, name="iqm_submit_smoke")
	if flip:
		circuit.x(0)
	circuit.measure(0, 0)
	return circuit


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Run a minimal IQM circuit authored with Qiskit.",
	)
	parser.add_argument("--output-dir", type=Path, default=None)
	parser.add_argument("--run-id", default=None)
	parser.add_argument("--system-up-timeout", type=int, default=40)
	parser.add_argument("--shots", type=int, default=100)
	parser.add_argument("--calibration-set-id", default=None)
	parser.add_argument("--timeout", type=float, default=300.0)
	parser.add_argument("--use-timeslot", action="store_true")
	parser.add_argument("--flip", action="store_true")
	add_backend_argument(parser)
	parser.add_argument("--json", action="store_true")
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	paths = create_run_paths(__file__, args.output_dir, args.run_id)
	backend = get_backend(args.backend, args.system_up_timeout)

	circuit = build_smoke_circuit(args.flip)
	qasm_file = paths.circuits / "smoke.qasm"
	input_file = paths.root / "input.json"
	result_file = paths.results / "result.json"
	timing_file = paths.results / "timing_summary.json"

	write_qasm2_artifact(circuit, qasm_file)
	write_json(input_file, {
		"source": "qiskit",
		"shots": args.shots,
		"flip": args.flip,
		"calibration_set_id": args.calibration_set_id,
		"use_timeslot": args.use_timeslot,
		"qasm_artifact": str(qasm_file),
	})

	result = to_jsonable(backend.run_circuits(
		[circuit],
		shots=args.shots,
		calibration_set_id=args.calibration_set_id,
		timeout=args.timeout,
		use_timeslot=args.use_timeslot))
	write_json(result_file, result)

	payload = result.get("result", {})
	timing_summary = (
		payload.get("timing_summary")
		if isinstance(payload, dict) else {})
	write_json(timing_file, timing_summary or {})

	qiskit_payload = payload.get("qiskit", {}) if isinstance(
		payload, dict) else {}
	iqm_payload = payload.get("iqm", {}) if isinstance(payload, dict) else {}
	summary = {
		"ok": result.get("rc") == 0,
		"run_id": paths.run_id,
		"date_id": paths.date_id,
		"backend_mode": backend.name,
		"output_dir": str(paths.root),
		"job_id": (
			iqm_payload.get("job_id")
			or qiskit_payload.get("job_id")
			or result.get("cid")),
		"counts": payload.get("counts") if isinstance(payload, dict) else None,
		"files": {
			"input": str(input_file),
			"qasm": str(qasm_file),
			"result": str(result_file),
			"timing_summary": str(timing_file),
		},
	}
	summary["files"]["script_output"] = str(
		script_output_path(paths, args.json))

	if args.json:
		output = render_json_output(summary)
	else:
		lines = [
			f"run id: {summary['run_id']}",
			f"output dir: {summary['output_dir']}",
			f"job id: {summary['job_id']}",
			f"counts: {summary['counts']}",
		]
		for name, path in summary["files"].items():
			lines.append(f"{name}: {path}")
		output = render_text_output(lines)
	write_script_output(paths, output, args.json)

	return backend.finish(0 if summary["ok"] else 2)


if __name__ == "__main__":
	raise SystemExit(main())
