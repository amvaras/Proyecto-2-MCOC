#!/usr/bin/env bash
#SBATCH --job-name=mcoc-e14
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=results/e14/hpc/logs/%A_%a.out
#SBATCH --error=results/e14/hpc/logs/%A_%a.err
set -euo pipefail
# Slurm copia el script al spool: su ubicación ya no es la del proyecto.
if [[ -n "${SLURM_SUBMIT_DIR:-}" ]]; then
  cd -- "$SLURM_SUBMIT_DIR"
else
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
fi
[[ -f pyproject.toml && -d src/mcoc_p2/e14 ]] || { printf '%s\n' 'Enviar desde la raíz P2_E14'; exit 2; }
: "${E14_MANIFEST:?Indicar manifest preparado}"
: "${SLURM_ARRAY_TASK_ID:?Se requiere índice de array}"
E14_PYTHON="${E14_PYTHON:-$PWD/.venv_hpc/bin/python}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
args=(--manifest "$E14_MANIFEST")
if [[ "${E14_LOCAL_EMULATION:-0}" == 1 ]]; then args+=(--local-emulation); fi
"$E14_PYTHON" -X utf8 -B examples/e14_hpc_worker.py "${args[@]}"
