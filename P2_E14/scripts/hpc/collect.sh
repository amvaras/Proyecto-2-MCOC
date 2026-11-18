#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
job="${1:?Indicar JobID real de sbatch}"
manifest="${2:?Indicar manifest.json}"
[[ "$job" =~ ^[0-9]+$ ]] || { printf '%s\n' 'JobID numérico'; exit 2; }
E14_PYTHON="${E14_PYTHON:-$PWD/.venv_hpc/bin/python}"
"$E14_PYTHON" -X utf8 -B scripts/collect_e14_hpc.py --job "$job" --manifest "$manifest"
