"""QFw-backed IQM workflow adapter."""

from __future__ import annotations

from qfw_iqm_util.qfw import finish, reserve_iqm_qpm
from qfw_iqm_util.qiskit_exec import build_qiskit_run_record
from qfw_iqm_util.qiskit_exec import ensure_circuit_list
import time


class QFwIQMBackend:
	name = "qfw"

	def __init__(self, system_up_timeout: int = 40):
		self._system_up_timeout = system_up_timeout
		self._qpm = None
		self._qiskit_backend = None

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

	def sync_run_many(self, infos):
		results = []
		for info in infos:
			results.append(self.sync_run(info))
		return {
			"cid": "qfw-sequential-batch",
			"result": {
				"batch_semantics": "sequential-qfw-sync-run",
				"results": results,
			},
			"rc": 0,
		}

	def qiskit_backend(self):
		if self._qiskit_backend is None:
			from qfw_qiskit import QFwBackend
			from qfw_qiskit import QFwBackendCapability
			from qfw_qiskit import QFwBackendType
			self._qiskit_backend = QFwBackend(
				betype=QFwBackendType.QFW_TYPE_IQM,
				capability=QFwBackendCapability.QFW_CAP_SUPERCONDUCTING)
		return self._qiskit_backend

	def run_circuits(self, circuits, shots: int = 100,
		     calibration_set_id=None, timeout=None, use_timeslot=False):
		circuit_list = ensure_circuit_list(circuits)
		run_input = circuit_list[0] if len(circuit_list) == 1 else circuit_list
		run_start = time.monotonic()
		job = self.qiskit_backend().run(run_input, shots=shots)
		result = job.result()
		return build_qiskit_run_record(
			self.name,
			circuit_list,
			shots,
			run_start,
			job,
			result,
			extra={
				"qfw": {
					"calibration_set_id": calibration_set_id,
					"timeout_requested": timeout,
					"use_timeslot_requested": use_timeslot,
				},
			},
		)

	def finish(self, rc: int = 0) -> int:
		return finish(rc)
