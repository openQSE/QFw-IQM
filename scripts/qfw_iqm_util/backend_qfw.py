"""QFw-backed IQM workflow adapter."""

from __future__ import annotations

from qfw_iqm_util.qfw import finish, reserve_iqm_qpm


class QFwIQMBackend:
	name = "qfw"

	def __init__(self, system_up_timeout: int = 40):
		self._system_up_timeout = system_up_timeout
		self._qpm = None

	def _service(self):
		if self._qpm is None:
			self._qpm = reserve_iqm_qpm(self._system_up_timeout)
		return self._qpm

	def get_backend_info(self):
		return self._service().get_backend_info()

	def get_dynamic_backend_info(self, calibration_set_id=None):
		return self._service().get_dynamic_backend_info(calibration_set_id)

	def get_calibration_snapshot(self, calibration_set_id=None):
		return self._service().get_calibration_snapshot(calibration_set_id)

	def get_coupling_graph(self, calibration_set_id=None):
		return self._service().get_coupling_graph(calibration_set_id)

	def sync_run(self, info):
		return self._service().sync_run(info)

	def finish(self, rc: int = 0) -> int:
		return finish(rc)
