#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
manifest="${1:?Uso: submit.sh manifest.json [concurrencia]}"
concurrency="${2:-2}"
[[ "$concurrency" =~ ^[1-4]$ ]] || { printf '%s\n' 'Concurrencia permitida: 1–4'; exit 2; }
E14_PYTHON="${E14_PYTHON:-$PWD/.venv_hpc/bin/python}"
count="$("$E14_PYTHON" -B -c 'import sys; from mcoc_p2.e14.workflow import load_manifest; print(len(load_manifest(sys.argv[1])["chunks"]))' "$manifest")"
mkdir -p results/e14/hpc/logs
export E14_MANIFEST="$manifest" E14_PYTHON
sbatch --parsable --array="0-$((count-1))%$concurrency" --export=ALL scripts/hpc/array.sbatch
# Cuenta/partición/módulos dependen del centro. Configurarlos con el administrador;
# no asumir una cuenta ni considerar esta impresión una evidencia de job finalizado.
