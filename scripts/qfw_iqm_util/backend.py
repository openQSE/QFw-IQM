"""Backend selection for IQM workflows."""

from __future__ import annotations

import os

BACKEND_CHOICES = ("auto", "qfw", "direct")


def add_backend_argument(parser):
	parser.add_argument(
		"--backend",
		choices=BACKEND_CHOICES,
		default="auto",
		help=(
			"IQM execution backend. Default: auto, which uses QFw when "
			"available and falls back to direct iqm-client access."
		),
	)


def qfw_available() -> bool:
	if not os.environ.get("QFW_PATH") or not os.environ.get("QFW_SETUP_PATH"):
		return False
	try:
		import api_qpm  # noqa: F401
		import defw_app_util  # noqa: F401
	except Exception:
		return False
	return True


def get_backend(mode: str = "auto", system_up_timeout: int = 40):
	if mode not in BACKEND_CHOICES:
		raise ValueError(f"invalid backend mode {mode!r}")

	if mode == "qfw":
		if not qfw_available():
			raise RuntimeError(
				"QFw backend was requested, but QFw is not available. "
				"Source qfw_activate and run through qfw_srun.sh.")
		from qfw_iqm_util.backend_qfw import QFwIQMBackend
		return QFwIQMBackend(system_up_timeout=system_up_timeout)

	if mode == "auto" and qfw_available():
		from qfw_iqm_util.backend_qfw import QFwIQMBackend
		return QFwIQMBackend(system_up_timeout=system_up_timeout)

	if mode == "auto" or mode == "direct":
		from qfw_iqm_util.backend_direct import DirectIQMBackend
		return DirectIQMBackend()

	raise RuntimeError(f"unsupported backend mode {mode!r}")
