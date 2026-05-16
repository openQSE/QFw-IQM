#!/usr/bin/env bash

qfw_iqm_parse_backend() {
	local backend="auto"
	local expect_backend=0
	local arg

	for arg in "$@"; do
		if [[ "${expect_backend}" -eq 1 ]]; then
			backend="${arg}"
			expect_backend=0
			continue
		fi
		case "${arg}" in
			--backend)
				expect_backend=1
				;;
			--backend=*)
				backend="${arg#--backend=}"
				;;
		esac
	done

	printf '%s\n' "${backend}"
}

qfw_iqm_parse_run_id() {
	local run_id=""
	local expect_run_id=0
	local arg

	for arg in "$@"; do
		if [[ "${expect_run_id}" -eq 1 ]]; then
			run_id="${arg}"
			expect_run_id=0
			continue
		fi
		case "${arg}" in
			--run-id)
				expect_run_id=1
				;;
			--run-id=*)
				run_id="${arg#--run-id=}"
				;;
		esac
	done

	if [[ "${expect_run_id}" -eq 1 ]]; then
		echo "ERROR: --run-id requires a value" >&2
		exit 1
	fi

	printf '%s\n' "${run_id}"
}

qfw_iqm_args_have_run_id() {
	local expect_run_id=0
	local arg

	for arg in "$@"; do
		if [[ "${expect_run_id}" -eq 1 ]]; then
			return 0
		fi
		case "${arg}" in
			--run-id)
				expect_run_id=1
				;;
			--run-id=*)
				return 0
				;;
		esac
	done

	return 1
}

qfw_iqm_init() {
	QFW_IQM_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
	QFW_IQM_SERVICES_CONFIG="${QFW_IQM_REPO_DIR}/config/qfw_iqm_services.yaml"
	QFW_IQM_BACKEND="$(qfw_iqm_parse_backend "$@")"
	QFW_IQM_RUN_ID="$(qfw_iqm_parse_run_id "$@")"
	if [[ -z "${QFW_IQM_RUN_ID}" ]]; then
		QFW_IQM_RUN_ID="$(date -u +%H%M%S)"
	fi

	QFW_IQM_BACKEND_ARGS=()
	if [[ "${QFW_IQM_BACKEND}" != "auto" ]]; then
		QFW_IQM_BACKEND_ARGS=(--backend "${QFW_IQM_BACKEND}")
	fi
}

qfw_iqm_use_direct_backend() {
	[[ "${QFW_IQM_BACKEND}" == "direct" ]] && return 0
	[[ "${QFW_IQM_BACKEND}" == "auto" &&
	   ( -z "${QFW_PATH:-}" || -z "${QFW_SETUP_PATH:-}" ) ]]
}

qfw_iqm_require_qfw() {
	if [[ -z "${QFW_PATH:-}" || -z "${QFW_SETUP_PATH:-}" ]]; then
		echo "ERROR: source /path/to/QFw/setup/qfw_activate first" >&2
		exit 1
	fi
}

qfw_iqm_teardown() {
	echo "Running QFw teardown..."
	(cd "${QFW_PATH}" && qfw_teardown.sh) || {
		echo "WARNING: qfw_teardown.sh failed" >&2
	}
}

qfw_iqm_start_qfw() {
	qfw_iqm_require_qfw
	trap qfw_iqm_teardown EXIT
	(cd "${QFW_PATH}" && qfw_setup.sh \
		--services-config "${QFW_IQM_SERVICES_CONFIG}")
}

qfw_iqm_run_single() {
	local script="$1"
	shift
	local run_id_args=()

	if ! qfw_iqm_args_have_run_id "$@"; then
		run_id_args=(--run-id "${QFW_IQM_RUN_ID}")
	fi

	if qfw_iqm_use_direct_backend; then
		exec python3 "${QFW_IQM_REPO_DIR}/${script}" \
			"${run_id_args[@]}" "$@"
	fi

	qfw_iqm_start_qfw
	(cd "${QFW_PATH}" && qfw_srun.sh \
		"${QFW_IQM_REPO_DIR}/${script}" \
		"${run_id_args[@]}" "$@")
}

qfw_iqm_run_python_json() {
	local script="$1"
	shift
	local run_id_args=()

	if ! qfw_iqm_args_have_run_id "$@"; then
		run_id_args=(--run-id "${QFW_IQM_RUN_ID}")
	fi

	python3 "${QFW_IQM_REPO_DIR}/${script}" \
		"${QFW_IQM_BACKEND_ARGS[@]}" "${run_id_args[@]}" "$@" --json
}

qfw_iqm_run_qfw_json() {
	local script="$1"
	shift
	local run_id_args=()

	if ! qfw_iqm_args_have_run_id "$@"; then
		run_id_args=(--run-id "${QFW_IQM_RUN_ID}")
	fi

	(cd "${QFW_PATH}" && qfw_srun.sh \
		"${QFW_IQM_REPO_DIR}/${script}" \
		"${QFW_IQM_BACKEND_ARGS[@]}" "${run_id_args[@]}" "$@" --json)
}

qfw_iqm_run_suite_json() {
	local script

	if qfw_iqm_use_direct_backend; then
		for script in "$@"; do
			qfw_iqm_run_python_json "${script}"
		done
		return 0
	fi

	qfw_iqm_start_qfw
	for script in "$@"; do
		qfw_iqm_run_qfw_json "${script}"
	done
}
