#!/usr/bin/env bash

set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${repo_dir}/qfw_iqm_common.sh"

qfw_iqm_init "$@"
qfw_iqm_run_single "scripts/iqm_timing_1q.py" "$@"
