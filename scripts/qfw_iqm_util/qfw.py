"""QFw helpers used by IQM characterization scripts."""

from __future__ import annotations

from time import sleep


def reserve_iqm_qpm(system_up_timeout: int = 40):
	from api_qpm import QPMType
	from defw_app_util import defw_get_resource_mgr
	from defw_app_util import defw_reserve_service_by_name
	from defw_exception import DEFwNotReady

	resmgr = defw_get_resource_mgr(timeout=system_up_timeout)
	qpm = defw_reserve_service_by_name(
		resmgr,
		"QPM",
		svc_type=QPMType.QPM_TYPE_IQM,
	)[0]

	waited = 0
	while waited < system_up_timeout:
		try:
			qpm.is_ready()
			return qpm
		except Exception as exc:
			if isinstance(exc, DEFwNotReady):
				sleep(1)
				waited += 1
				continue
			raise

	raise TimeoutError("IQM QPM did not become ready")


def finish(rc: int = 0) -> int:
	try:
		from defw import me
		me.exit()
	except Exception:
		pass
	return rc

