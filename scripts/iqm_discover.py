#!/usr/bin/env python3
"""Collect IQM discovery data through the QFw IQM QPM service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qfw_iqm_util.output import create_run_paths, to_jsonable, write_json
from qfw_iqm_util.qfw import finish, reserve_iqm_qpm


def summarize_native_gates(dynamic_info: dict[str, Any]) -> list[dict[str, Any]]:
	dynamic = dynamic_info.get("dynamic_architecture", {})
	gates = dynamic.get("gates", {})
	if not isinstance(gates, dict):
		return []

	summary = []
	for name, gate_info in sorted(gates.items()):
		implementations = []
		if isinstance(gate_info, dict):
			impls = gate_info.get("implementations", {})
			if isinstance(impls, dict):
				implementations = sorted(str(key) for key in impls.keys())
		summary.append({
			"name": str(name),
			"implementations": implementations,
		})
	return summary


def build_qschedsim_skeleton(device_snapshot: dict[str, Any],
			     coupling_graph: dict[str, Any],
			     calibration_snapshot: dict[str, Any]) -> dict[str, Any]:
	backend_info = device_snapshot.get("backend_info", {})
	static_arch = backend_info.get("static_architecture", {})
	dynamic_info = device_snapshot.get("dynamic_backend_info", {})
	return {
		"schema": "qschedsim-device-skeleton-v1",
		"name": static_arch.get("dut_label") or static_arch.get("name")
		or "iqm-device",
		"source": {
			"tool": "QFw-IQM/scripts/iqm_discover.py",
			"calibration_set_id": coupling_graph.get("calibration_set_id"),
		},
		"hardware": {
			"vendor": "IQM",
			"technology": "superconducting",
			"qubit_count": len(coupling_graph.get("qubits", [])),
			"qubits": coupling_graph.get("qubits", []),
			"coupling_graph": coupling_graph.get("couplers", []),
			"native_gates": summarize_native_gates(dynamic_info),
		},
		"admission_model": {
			"status": "unmeasured",
		},
		"timing_model": {
			"status": "unmeasured",
		},
		"noise_model": {
			"status": "raw-calibration-recorded",
			"calibration_snapshot": calibration_snapshot,
		},
	}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Discover IQM architecture and calibration through QFw.",
	)
	parser.add_argument("--output-dir", type=Path, default=None)
	parser.add_argument("--run-id", default=None)
	parser.add_argument("--system-up-timeout", type=int, default=40)
	parser.add_argument("--calibration-set-id", default=None)
	parser.add_argument("--json", action="store_true")
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	paths = create_run_paths(__file__, args.output_dir, args.run_id)
	qpm = reserve_iqm_qpm(args.system_up_timeout)

	device_snapshot = {
		"backend_info": to_jsonable(qpm.get_backend_info()),
		"dynamic_backend_info": to_jsonable(
			qpm.get_dynamic_backend_info(args.calibration_set_id)),
	}
	calibration_snapshot = to_jsonable(
		qpm.get_calibration_snapshot(args.calibration_set_id))
	coupling_graph = to_jsonable(
		qpm.get_coupling_graph(args.calibration_set_id))
	qschedsim_skeleton = build_qschedsim_skeleton(
		device_snapshot,
		coupling_graph,
		calibration_snapshot,
	)

	files = {
		"device_snapshot": paths.root / "device_snapshot.json",
		"calibration_snapshot": paths.root / "calibration_snapshot.json",
		"coupling_graph": paths.root / "coupling_graph.json",
		"qschedsim_device_skeleton": (
			paths.root / "qschedsim_device_skeleton.json"),
	}
	write_json(files["device_snapshot"], device_snapshot)
	write_json(files["calibration_snapshot"], calibration_snapshot)
	write_json(files["coupling_graph"], coupling_graph)
	write_json(files["qschedsim_device_skeleton"], qschedsim_skeleton)

	summary = {
		"ok": True,
		"run_id": paths.run_id,
		"date_id": paths.date_id,
		"output_dir": str(paths.root),
		"files": {name: str(path) for name, path in files.items()},
		"qubits": len(coupling_graph.get("qubits", [])),
		"couplers": len(coupling_graph.get("couplers", [])),
		"calibration_set_id": coupling_graph.get("calibration_set_id"),
	}

	if args.json:
		print(json.dumps(summary, indent=2, sort_keys=True))
	else:
		print(f"run id: {summary['run_id']}")
		print(f"output dir: {summary['output_dir']}")
		print(f"qubits: {summary['qubits']}")
		print(f"couplers: {summary['couplers']}")
		print(f"calibration set: {summary['calibration_set_id']}")
		for name, path in summary["files"].items():
			print(f"{name}: {path}")

	return finish(0)


if __name__ == "__main__":
	raise SystemExit(main())
