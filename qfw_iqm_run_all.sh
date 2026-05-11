#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${repo_dir}/qfw_iqm_common.sh"

qfw_iqm_init "$@"

qfw_iqm_run_all_1q_args=(
	--qubits "${QFW_IQM_RUN_ALL_1Q_QUBITS:-QB1}"
	--gates "${QFW_IQM_RUN_ALL_1Q_GATES:-rx}"
	--depths "${QFW_IQM_RUN_ALL_1Q_DEPTHS:-1,2}"
	--shots "${QFW_IQM_RUN_ALL_1Q_SHOTS:-100}"
	--repetitions "${QFW_IQM_RUN_ALL_1Q_REPETITIONS:-1}"
)

if qfw_iqm_use_direct_backend; then
	qfw_iqm_run_python_json "scripts/iqm_env_check.py"
	qfw_iqm_run_python_json "scripts/iqm_discover.py"
	qfw_iqm_run_python_json "scripts/iqm_submit_smoke.py"
	qfw_iqm_run_python_json \
		"scripts/iqm_timing_1q.py" "${qfw_iqm_run_all_1q_args[@]}"
	exit 0
fi

qfw_iqm_start_qfw
qfw_iqm_run_qfw_json "scripts/iqm_env_check.py"
qfw_iqm_run_qfw_json "scripts/iqm_discover.py"
qfw_iqm_run_qfw_json "scripts/iqm_submit_smoke.py"
qfw_iqm_run_qfw_json \
	"scripts/iqm_timing_1q.py" "${qfw_iqm_run_all_1q_args[@]}"
