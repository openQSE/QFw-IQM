#!/usr/bin/env python3
"""Validate access to an IQM backend."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qfw_iqm_util.backend import add_backend_argument, get_backend
from qfw_iqm_util.output import create_run_paths
from qfw_iqm_util.output import render_json_output
from qfw_iqm_util.output import render_text_output
from qfw_iqm_util.output import script_output_path
from qfw_iqm_util.output import to_jsonable
from qfw_iqm_util.output import write_json
from qfw_iqm_util.output import write_script_output


def summarize_backend(info: dict[str, Any]) -> dict[str, Any]:
	static_arch = info.get("static_architecture", {})
	return {
		"backend": info.get("backend"),
		"metadata_supported": info.get("metadata_supported"),
		"name": static_arch.get("name") or static_arch.get("dut_label"),
		"active_qubits": info.get("active_qubits", []),
		"calibration_set_id": info.get("calibration_set_id"),
	}


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Check that QFw-IQM can reach an IQM backend.",
	)
	parser.add_argument("--output-dir", type=Path, default=None)
	parser.add_argument("--run-id", default=None)
	parser.add_argument("--system-up-timeout", type=int, default=40)
	parser.add_argument("--calibration-set-id", default=None)
	add_backend_argument(parser)
	parser.add_argument("--json", action="store_true")
	return parser.parse_args()


def main() -> int:
	args = parse_args()
	paths = create_run_paths(__file__, args.output_dir, args.run_id)
	backend = get_backend(args.backend, args.system_up_timeout)

	result = {
		"ok": True,
		"backend_mode": backend.name,
		"backend_info": to_jsonable(backend.get_backend_info()),
		"dynamic_backend_info": to_jsonable(
			backend.get_dynamic_backend_info(args.calibration_set_id)),
	}
	result["summary"] = summarize_backend(result["backend_info"])

	output_file = paths.root / "env_check.json"
	write_json(output_file, result)
	result["output_file"] = str(output_file)
	result["script_output_file"] = str(script_output_path(paths, args.json))

	if args.json:
		output = render_json_output(result)
	else:
		summary = result["summary"]
		output = render_text_output([
			f"backend: {summary['backend']}",
			f"machine: {summary['name']}",
			f"active qubits: {len(summary['active_qubits'])}",
			f"calibration set: {summary['calibration_set_id']}",
			f"output: {output_file}",
		])
	write_script_output(paths, output, args.json)

	return backend.finish(0)


if __name__ == "__main__":
	raise SystemExit(main())
