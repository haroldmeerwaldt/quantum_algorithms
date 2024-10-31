from dataclasses import dataclass

import matplotlib

matplotlib.use("QtAgg")
from qiskit.algorithms.optimizers import SLSQP
from qiskit.primitives import Estimator
from qiskit_nature.second_q.algorithms import VQEUCCFactory, GroundStateEigensolver
from qiskit_nature.second_q.circuit.library import UCCSD
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.formats import MoleculeInfo
from qiskit_nature.second_q.mappers import JordanWignerMapper, QubitConverter
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer


@dataclass
class AtomInfo:
    symbol: str
    coords: tuple[float, float, float]


class GroundStateEnergyCalculation:
    def __init__(self):
        # self._molecule = MoleculeInfo(["C", "H", "H", "H"], [(0.0, 0.0, 0.0), (0.1, 0.0, 0.0), (-0.1, 0.0, 0.0), (0.0, 0.1, 0.0)], charge=0, multiplicity=1)
        self._molecule = MoleculeInfo(["H"], [(0.0, 0.0, 0.0)], charge=0, multiplicity=1)

        converter = JordanWignerMapper()  # also ParityMapper, BravyiKitaevMapper
        self._qubit_converter = QubitConverter(converter, two_qubit_reduction=True)
        self._solver_factory = VQEUCCFactory(estimator=Estimator(), ansatz=UCCSD(), optimizer=SLSQP())

    def add_atom(self, atom: AtomInfo):
        self._molecule.symbols.append(atom.symbol)
        self._molecule.coords.append(atom.coords)

    def update_last_atoms_coords(self, coords: tuple[float, float, float]):
        self._molecule.coords[-1] = coords

    def __call__(self):
        print(".", end="")
        driver = PySCFDriver.from_molecule(self._molecule, basis="sto3g")
        problem = driver.run()

        n_electrons = problem.num_particles
        n_spatial_orbitals = problem.num_spatial_orbitals
        transformer = ActiveSpaceTransformer(num_electrons=n_electrons, num_spatial_orbitals=n_spatial_orbitals)
        problem_transformed = transformer.transform(problem)

        solver = self._solver_factory.get_solver(problem_transformed, self._qubit_converter)
        ground_state_eigen_solver = GroundStateEigensolver(self._qubit_converter, solver)
        ground_state = ground_state_eigen_solver.solve(problem_transformed)
        electronic_ground_state_energy = ground_state.groundenergy
        nuclear_repulsion_energy = problem.nuclear_repulsion_energy
        total_ground_state_energy = electronic_ground_state_energy + nuclear_repulsion_energy
        return total_ground_state_energy

