"""Núcleo numérico E01; no depende de Blender ni de IfcOpenShell."""

from .diffusion_1d import (
    Dirichlet, Material, Neumann, Robin, Solution, energy_per_area,
    solve, stable_timestep,
)

__all__ = [
    "Dirichlet", "Material", "Neumann", "Robin", "Solution",
    "energy_per_area", "solve", "stable_timestep",
]
