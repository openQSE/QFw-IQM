"""QFw-backed IQM workflow adapter."""

from __future__ import annotations

from qfw_iqm_util.qfw import finish, reserve_iqm_qpm
from qfw_iqm_util.qhw import QHW_IQM_DEVICE_ID_KEY, QHW_IQM_KIND_KEY
from qfw_iqm_util.qhw import normalize_iqm_payload, qhw_device_id
from qfw_iqm_util.qiskit_exec import qiskit_result_metadata


class QFwIQMBackend:
	name = "qfw"

	def __init__(self, system_up_timeout: int = 40):
		self._system_up_timeout = system_up_timeout
		self._qpm = None
		self._qiskit_backend = None
		self._qhw_device_id = qhw_device_id()

	def _qhw_tags(self, kind: str) -> dict[str, str | None]:
		return {
			QHW_IQM_KIND_KEY: kind,
			QHW_IQM_DEVICE_ID_KEY: self._qhw_device_id,
		}

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

	def qiskit_backend(self, calibration_set_id=None):
		del calibration_set_id
		if self._qiskit_backend is None:
			from qfw_qiskit import QFwBackend
			from qfw_qiskit import QFwBackendCapability
			from qfw_qiskit import QFwBackendType
			self._qiskit_backend = QFwBackend(
				betype=QFwBackendType.QFW_TYPE_IQM,
				capability=QFwBackendCapability.QFW_CAP_SUPERCONDUCTING)
		return self._qiskit_backend

	def qiskit_run_options(self, shots: int, calibration_set_id=None,
	    timeout=None, use_timeslot=False, extra_run_options=None):
		del calibration_set_id, timeout, use_timeslot
		options = {"shots": shots}
		options.update(extra_run_options or {})
		return options

	def qiskit_job_result(self, job, timeout=None):
		del timeout
		return job.result()

	def qiskit_record_extra(self, context):
		return {
			"qfw": {
				"calibration_set_id": context.get("calibration_set_id"),
				"timeout_requested": context.get("timeout"),
				"use_timeslot_requested": context.get("use_timeslot"),
			},
		}

	def extract_result_and_normalize(self, job, result, record, context):
		del job, result, context
		result_dict = record.get("result", {}).get("qiskit", {}).get("result")
		metadata = qiskit_result_metadata(result_dict or {})
		qhw_results = [
			item.get("qhw_result") for item in metadata
			if isinstance(item.get("qhw_result"), dict)
		]
		raw_payloads = [
			item.get("_raw_iqm") for item in metadata
			if isinstance(item.get("_raw_iqm"), dict)
		]
		if not qhw_results:
			raise RuntimeError(
				"QFw IQM result did not include normalized qhw_result "
				"metadata. Check that the QFw IQM service is returning "
				"qhw-normalized result payloads.")

		if len(qhw_results) == 1:
			record.setdefault("result", {})["qhw_result"] = qhw_results[0]
			if raw_payloads:
				record["_raw_iqm"] = raw_payloads[0]
			record.update(self._qhw_tags("result"))
			return record

		raw_payload = {
			"qiskit_result": result_dict,
			"qfw_metadata": metadata,
		}
		qhw_result = normalize_iqm_payload(
			"result", raw_payload, device_id=self._qhw_device_id)
		qhw_result.setdefault("extensions", {})["qfw.v1"] = {
			"per_circuit_qhw_results": qhw_results,
			"per_circuit_raw_iqm": raw_payloads,
		}
		record.setdefault("result", {})["qhw_result"] = qhw_result
		record.update(self._qhw_tags("result"))
		record["_raw_iqm"] = raw_payload
		return record

	def run_circuits(self, circuits, shots: int = 100,
		     calibration_set_id=None, timeout=None, use_timeslot=False):
		from qfw_iqm_util.backend import BackendWrapper
		return BackendWrapper(self).run_circuits(
			circuits,
			shots=shots,
			calibration_set_id=calibration_set_id,
			timeout=timeout,
			use_timeslot=use_timeslot,
		)

	def finish(self, rc: int = 0) -> int:
		return finish(rc)
