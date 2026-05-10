"""Output and serialization helpers for QFw-IQM scripts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID
import json


@dataclass(frozen=True)
class RunPaths:
	root: Path
	circuits: Path
	results: Path
	date_id: str
	run_id: str
	timestamp_utc: str


def to_jsonable(value: Any) -> Any:
	if value is None or isinstance(value, (str, int, float, bool)):
		return value
	if isinstance(value, UUID):
		return str(value)
	if isinstance(value, dict):
		return {str(key): to_jsonable(item) for key, item in value.items()}
	if isinstance(value, (list, tuple, set, frozenset)):
		return [to_jsonable(item) for item in value]
	if is_dataclass(value):
		return to_jsonable(asdict(value))
	if hasattr(value, "model_dump"):
		return to_jsonable(value.model_dump(mode="json"))
	if hasattr(value, "dict"):
		return to_jsonable(value.dict())
	return str(value)


def write_json(path: Path, data: Any) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(to_jsonable(data), indent=2, sort_keys=True))


def create_run_paths(script_file: str,
		     output_dir: Path | None = None,
		     run_id: str | None = None) -> RunPaths:
	now = datetime.now(timezone.utc)
	date_id = now.strftime("%Y%m%d")
	run_id = run_id or now.strftime("%H%M%S")
	script_name = Path(script_file).stem

	if output_dir is None:
		repo_dir = Path(script_file).resolve().parents[1]
		root = repo_dir / "data" / "raw" / date_id / script_name / run_id
	else:
		root = output_dir

	circuits = root / "circuits"
	results = root / "results"
	circuits.mkdir(parents=True, exist_ok=True)
	results.mkdir(parents=True, exist_ok=True)

	return RunPaths(
		root=root,
		circuits=circuits,
		results=results,
		date_id=date_id,
		run_id=run_id,
		timestamp_utc=now.isoformat(),
	)

