# QFw-IQM

QFw-IQM contains IQM-specific characterization workflows. The preferred path
runs through the Quantum Framework, where QFw owns service startup, placement,
and the reusable IQM QPM integration. The same Python workflows can also run
directly through `iqm-client` for standalone characterization without QFw.

## Requirements

For QFw-backed execution:

- A configured QFw tree with the IQM QPM service available.
- An activated QFw environment:

```bash
source /path/to/QFw/setup/qfw_activate
```

- IQM endpoint credentials exported in the shell that starts QFw:

```bash
export QFW_QC_URL="https://<iqm-endpoint>"
export QFW_API_KEY="<api-key>"
```

Optional IQM settings:

```bash
export QFW_IQM_QUANTUM_COMPUTER="<machine-name>"
export QFW_IQM_REQUEST_TIMEOUT=30
export QFW_IQM_JOB_TIMEOUT=300
```

For direct execution without QFw:

- The `iqm-client` Python package and its IQM dependencies.
- `QFW_QC_URL` and `QFW_API_KEY` exported in the shell.

## Workflows

Each workflow supports `--backend auto|qfw|direct`. The default is `auto`.
When QFw is activated, `auto` uses QFw. Otherwise, `auto` uses direct
`iqm-client` access.

In QFw mode, each wrapper starts QFw with `config/qfw_iqm_services.yaml`, runs
one Python script through `qfw_srun.sh`, and tears QFw down.

```bash
./qfw_iqm_env_check.sh --json
./qfw_iqm_discover.sh --json
./qfw_iqm_submit_smoke.sh --shots 100 --json
./qfw_iqm_timing_overhead.sh --shots-sweep 1,10,100 --batch-sweep 1,2 --json
```

To force direct mode:

```bash
./qfw_iqm_env_check.sh --backend direct --json
./qfw_iqm_discover.sh --backend direct --json
./qfw_iqm_submit_smoke.sh --backend direct --shots 100 --json
./qfw_iqm_timing_overhead.sh --backend direct --shots-sweep 1,10,100 --json
```

To run the current suite in one QFw session:

```bash
./qfw_iqm_run_all.sh
```

`qfw_iqm_run_all.sh` intentionally does not include timing campaigns. Timing
scripts submit multiple jobs and should be run explicitly with the desired
shot sweep, batch sweep, and repetition count.

Output is written under:

```text
data/raw/<YYYYMMDD>/<script-name>/<HHMMSS>/
```

The `data/` directory is intentionally ignored by git.

## QFw Execution Model

The shell wrappers assume QFw is responsible for startup, service placement,
and teardown when `--backend qfw` is selected or `--backend auto` detects an
activated QFw shell. The Python scripts run as QFw applications and use
`api_qpm` to reserve the IQM QPM service.

The default service config starts one IQM QPM on group 1:

```bash
qfw_setup.sh --services-config config/qfw_iqm_services.yaml
qfw_srun.sh scripts/iqm_submit_smoke.py
qfw_teardown.sh
```

For a heterogeneous allocation, the application runs on group 0 and the IQM
QPM service runs on the group 1 head node. For local or single-node operation,
QFw's allocation abstraction can map both groups to the same node.

## Direct Execution Model

In direct mode, the shell wrappers do not call `qfw_setup.sh`, `qfw_srun.sh`,
or `qfw_teardown.sh`. They execute the Python workflow locally and use
`iqm-client` with `QFW_QC_URL` and `QFW_API_KEY`. This mode is useful for
early machine characterization and for sharing the scripts with users who do
not have QFw installed.

## Adding Workflows

New shell wrappers should source `qfw_iqm_common.sh` rather than reimplement
backend parsing or QFw startup. A minimal wrapper looks like:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${repo_dir}/qfw_iqm_common.sh"

qfw_iqm_init "$@"
qfw_iqm_run_single "scripts/new_workflow.py" "$@"
```

The Python script should add the common backend option with
`add_backend_argument(parser)` and construct the backend with
`get_backend(args.backend, args.system_up_timeout)`.

The `_qasm.py` scripts are retained as lower-level examples that build
OpenQASM directly. Characterization workflows should prefer Qiskit-authored
circuits unless they are explicitly testing OpenQASM handling.
