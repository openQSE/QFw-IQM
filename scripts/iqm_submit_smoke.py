#!/usr/bin/env python3
"""Submit a one-qubit smoke circuit through the selected IQM backend."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qfw_iqm_util.backend import add_backend_argument, get_backend
from qfw_iqm_util.output import create_run_paths, to_jsonable, write_json
from qfw_iqm_util.timing import build_timing_summary


def build_smoke_qasm(flip: bool) -> str:
	gate = "x q[0];\n" if flip else ""
	return (
		"OPENQASM 2.0;\n"
		"include \"qelib1.inc\";\n"
		"qreg q[1];\n"
		"creg c[1];\n"
		f"{gate}"
		"measure q[0] -> c[0];\n"
	)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Run a minimal IQM circuit.",
	)
	parser.add_argument("--output-dir", type=Path, default=None)
	parser.add_argument("--run-id", default=None)
	parser.add_argument("--system-up-timeout", type=int, default=40)
	parser.add_argument("--shots", type=int, default=100)
	parser.add_argument("--qubit", default=None)
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

	qasm = build_smoke_qasm(args.flip)
	info = {
		"qasm": qasm,
		"num_qubits": 1,
		"num_shots": args.shots,
		"compiler": "iqm-native",
		"timeout": args.timeout,
		"use_timeslot": args.use_timeslot,
	}
	if args.qubit:
		info["iqm_qubit_mapping"] = {0: args.qubit}
	if args.calibration_set_id:
		info["calibration_set_id"] = args.calibration_set_id

	qasm_file = paths.circuits / "smoke.qasm"
	input_file = paths.root / "input.json"
	result_file = paths.results / "result.json"
	timing_file = paths.results / "timing_summary.json"

	qasm_file.write_text(qasm)
	write_json(input_file, info)

	result = to_jsonable(backend.sync_run(info))
	write_json(result_file, result)

	payload = result.get("result", {})
	iqm_payload = payload.get("iqm", {}) if isinstance(payload, dict) else {}
	timing_summary = (
		iqm_payload.get("timing_summary")
		or build_timing_summary(iqm_payload.get("metadata", {}))
	)
	write_json(timing_file, timing_summary)

	summary = {
		"ok": result.get("rc") == 0,
		"run_id": paths.run_id,
		"date_id": paths.date_id,
		"backend_mode": backend.name,
		"output_dir": str(paths.root),
		"job_id": iqm_payload.get("job_id"),
		"status": iqm_payload.get("status"),
		"counts": payload.get("counts") if isinstance(payload, dict) else None,
		"files": {
			"input": str(input_file),
			"qasm": str(qasm_file),
			"result": str(result_file),
			"timing_summary": str(timing_file),
		},
	}

	if args.json:
		print(json.dumps(summary, indent=2, sort_keys=True))
	else:
		print(f"run id: {summary['run_id']}")
		print(f"output dir: {summary['output_dir']}")
		print(f"job id: {summary['job_id']}")
		print(f"status: {summary['status']}")
		print(f"counts: {summary['counts']}")
		for name, path in summary["files"].items():
			print(f"{name}: {path}")

	return backend.finish(0 if summary["ok"] else 2)


if __name__ == "__main__":
	raise SystemExit(main())
