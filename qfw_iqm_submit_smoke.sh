#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
services_config="${repo_dir}/config/qfw_iqm_services.yaml"
backend="auto"
expect_backend=0

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

if [[ "${backend}" == "direct" ||
      ( "${backend}" == "auto" &&
        ( -z "${QFW_PATH:-}" || -z "${QFW_SETUP_PATH:-}" ) ) ]]; then
	exec python3 "${repo_dir}/scripts/iqm_submit_smoke.py" "$@"
fi

if [[ -z "${QFW_PATH:-}" || -z "${QFW_SETUP_PATH:-}" ]]; then
	echo "ERROR: source /path/to/QFw/setup/qfw_activate first" >&2
	exit 1
fi

cleanup() {
	echo "Running QFw teardown..."
	(cd "${QFW_PATH}" && qfw_teardown.sh) || {
		echo "WARNING: qfw_teardown.sh failed" >&2
	}
}
trap cleanup EXIT

(cd "${QFW_PATH}" && qfw_setup.sh --services-config "${services_config}")
(cd "${QFW_PATH}" && qfw_srun.sh "${repo_dir}/scripts/iqm_submit_smoke.py" "$@")
