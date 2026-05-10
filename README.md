# QFw-IQM

QFw-IQM contains IQM-specific characterization workflows that run through the
Quantum Framework. The QFw repository owns the reusable integration layer, such
as `svc_iqm_qpm` and `api_qpm`. This repository owns the IQM workflows, shell
entrypoints, output layout, and analysis artifacts.

## Requirements

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

## Workflows

Each wrapper starts QFw with `config/qfw_iqm_services.yaml`, runs one Python
script through `qfw_srun.sh`, and tears QFw down.

```bash
./qfw_iqm_env_check.sh --json
./qfw_iqm_discover.sh --json
./qfw_iqm_submit_smoke.sh --shots 100 --json
```

To run the current suite in one QFw session:

```bash
./qfw_iqm_run_all.sh
```

Output is written under:

```text
data/raw/<YYYYMMDD>/<script-name>/<HHMMSS>/
```

The `data/` directory is intentionally ignored by git.

## QFw Execution Model

The shell wrappers assume QFw is responsible for startup, service placement,
and teardown. The Python scripts run as QFw applications and use `api_qpm` to
reserve the IQM QPM service. They do not contact the IQM machine directly.

The default service config starts one IQM QPM on group 1:

```bash
qfw_setup.sh --services-config config/qfw_iqm_services.yaml
qfw_srun.sh scripts/iqm_submit_smoke.py
qfw_teardown.sh
```

For a heterogeneous allocation, the application runs on group 0 and the IQM
QPM service runs on the group 1 head node. For local or single-node operation,
QFw's allocation abstraction can map both groups to the same node.

