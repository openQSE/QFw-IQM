#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${repo_dir}/qfw_iqm_common.sh"

qfw_iqm_run_all_manifest="${repo_dir}/config/qfw_iqm_tests.yaml"
qfw_iqm_run_all_resolver="${repo_dir}/scripts/qfw_iqm_util/run_manifest.py"

qfw_iqm_run_all_usage() {
	cat <<'EOF'
Usage: qfw_iqm_run_all.sh [--level <level>] [--backend auto|qfw|direct]
       qfw_iqm_run_all.sh [<level>] [--backend auto|qfw|direct]

Levels are ordered in config/qfw_iqm_tests.yaml. Higher levels include all
tests from lower levels.

Set QFW_IQM_RUN_ALL_LEVEL to override the manifest default.
EOF
	if [[ -f "${qfw_iqm_run_all_manifest}" ]]; then
		echo
		echo "Configured levels:"
		python3 "${qfw_iqm_run_all_resolver}" \
			--manifest "${qfw_iqm_run_all_manifest}" levels \
			2>/dev/null | while IFS=$'\t' read -r name description; do
				printf '  %-8s %s\n' "${name}" "${description}"
			done || true
	fi
}

qfw_iqm_run_all_parse_level() {
	local expect_level=0
	local skip_value=0
	local arg

	for arg in "$@"; do
		if [[ "${expect_level}" -eq 1 ]]; then
			qfw_iqm_run_all_level="${arg}"
			expect_level=0
			continue
		fi
		if [[ "${skip_value}" -eq 1 ]]; then
			skip_value=0
			continue
		fi

		case "${arg}" in
			-h|--help)
				qfw_iqm_run_all_usage
				exit 0
				;;
			--level)
				expect_level=1
				;;
			--level=*)
				qfw_iqm_run_all_level="${arg#--level=}"
				;;
			--backend|--run-id)
				skip_value=1
				;;
			--backend=*|--run-id=*)
				;;
			--*)
				echo "ERROR: unsupported qfw_iqm_run_all.sh option: ${arg}" >&2
				qfw_iqm_run_all_usage >&2
				exit 1
				;;
			*)
				if [[ -n "${qfw_iqm_run_all_positional_level}" ]]; then
					echo "ERROR: only one positional level is supported" >&2
					exit 1
				fi
				qfw_iqm_run_all_level="${arg}"
				qfw_iqm_run_all_positional_level="${arg}"
				;;
		esac
	done

	if [[ "${expect_level}" -eq 1 ]]; then
		echo "ERROR: --level requires a configured level" >&2
		exit 1
	fi
}

qfw_iqm_run_all_validate_plan() {
	python3 "${qfw_iqm_run_all_resolver}" \
		--manifest "${qfw_iqm_run_all_manifest}" \
		plan --level "${qfw_iqm_run_all_level}" >/dev/null
}

qfw_iqm_run_all_run() {
	local run_cmd="$1"
	local plan_file
	local fields
	local script
	local test_args

	plan_file="$(mktemp)"
	trap 'rm -f "${plan_file}"' RETURN
	python3 "${qfw_iqm_run_all_resolver}" \
		--manifest "${qfw_iqm_run_all_manifest}" \
		plan --level "${qfw_iqm_run_all_level}" >"${plan_file}"

	while IFS=$'\t' read -r -a fields; do
		[[ "${#fields[@]}" -gt 0 ]] || continue
		script="${fields[0]}"
		test_args=("${fields[@]:1}")
		"${run_cmd}" "${script}" "${test_args[@]}"
	done <"${plan_file}"

	rm -f "${plan_file}"
	trap - RETURN
}

qfw_iqm_run_all_positional_level=""
qfw_iqm_run_all_level="${QFW_IQM_RUN_ALL_LEVEL:-}"
if [[ -z "${qfw_iqm_run_all_level}" ]]; then
	qfw_iqm_run_all_level="$(python3 "${qfw_iqm_run_all_resolver}" \
		--manifest "${qfw_iqm_run_all_manifest}" default-level)"
fi
qfw_iqm_run_all_parse_level "$@"
qfw_iqm_run_all_validate_plan
qfw_iqm_init "$@"

if qfw_iqm_use_direct_backend; then
	qfw_iqm_run_all_run qfw_iqm_run_python_json
	exit 0
fi

qfw_iqm_start_qfw
qfw_iqm_run_all_run qfw_iqm_run_qfw_json
