"""
using ASE as interface

run relaxation track:
    need a commit_func that take low dimensional collective variable and return basin id
run normal md
    need a colvar_func that return collective variables
"""

import numpy as np

from pyfile_utils import load_callable, instantiate
from os.path import isfile

from ase import units
from ase.io import read
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.md.langevin import Langevin

from .engine import Engine


class ASE(Engine):

    # 'constraints': 'list of atom indices to fix during MD simulation'})
    # 'dt': 'MD time step in [fs]',
    # 'temperature': 'MD target temperature in [K]',
    # 'n_steps': 'Number of MD steps to equilibrate system: '
    #                  'set to 0 for no run: default: '
    #                  '2000 (= 1ps at default time step)',
    # 'friction': 'langevin with this friction term',

    def __init__(
        self,
        atoms=None,
        calculator=None,
        calculator_name="",
        calculator_params={},
        read_params: dict = {},
        constraints=[],
        **kwargs,
    ):

        Engine.__init__(self, **kwargs)

        self.atoms = read(filename=self.x0, **read_params) if atoms is None else atoms
        self.read_params = read_params
        self.langevin_fix_com = langevin_fix_com
        self.constraints = constraints

        if calculator is None:
            if calculator_name != "CP2K":
                calculator_class = load_callable("ase.calculators." + calculator_name)
            else:
                from .cp2k import CP2K

                calculator_class = CP2K
            self.calculator = calculator_class(calculator_params)
            self.calculator_name = calculator_name
        else:
            self.calculator = calculator
            self.calculator_name = self.calculator.name

        if self.calculator_name in ["cp2k"]:
            self.log_freq = 1

        self.md_params = dict(steps=self.md_n_steps)
        self.committor_params = dict(steps=self.md_n_steps)

        self.atoms.set_calculator(self.calculator)

    def get_structure(self, config):
        x0 = config["x0"]
        read_params = config.get("ASE_read_params", config.get("read_params", {}))
        atoms = read(filename=x0, **read_params) if isinstance(x0, str) else x0
        return atoms

    def check_instance(self):

        Engine.check_instance(self)

        if not isfile(self.x0):
            raise RuntimeError(f"{self.x0} file does not exist")

        if self.colvar_func is None:
            self.colvar_func = dummy_colvar

        if self.commit_func is None:
            self.commit_func = dummy_commit

    def single_run(
        self, params, start_config, root, run_name, commit_run: bool = False
    ):

        logger = self.logger

        assert isinstance(start_config, dict), (
            f"starting config has to be a dict," f"but it is a {type(start_config)}"
        )

        subroot = (
            self.output_kwargs["root"]
            + "/"
            + self.output_kwargs["run_name"]
            + "/"
            + root
        )

        output = self.get_replica_log(subroot, run_name)
        logger = output.open_logfile("pysampling_engine.log")

        atoms = self.atoms

        x = start_config["x"]
        atoms.set_positions(x, apply_constraint=False)
        if start_config.get("v", None) is None:
            self.initialize_v()
        else:
            atoms.set_velocities(start_config.get("v", None))

        self.sync_thermostat(params=params)

        langevin = instantiate(
            builder=Langevin,
            prefix="langevin",
            positional_args=dict(atoms=atoms),
            all_args=params,
        )
        params["prefix"] = run_name
        params["run_name"] = run_name

        # frame 0
        trj = {k: [v] for k, v in (self.get_state(atoms)).items()}

        not_commit = True
        basin = -1
        i = 0
        steps = params["steps"]
        while not_commit and i < steps:

            langevin.run(steps=1)
            i += 1

            if (i % self.save_freq == 0) or (i % self.log_freq == 0):

                state = self.get_state(atoms)
                if i % self.save_freq == 0:
                    for k, v in trj.items():
                        v.append(state[k])

                if i % self.log_freq == 0:
                    T = state["T"][-1]
                    ke = state["ke"][-1]
                    pe = state["pe"][-1]
                    colvar = state["intc"][-1]
                    logger.info(f"{i:8d} {T:8.3f} {ke:8.3f} {pe:8.3f} {colvar}")

                    if commit_run:
                        basin = self.commit_func(colvar)
                        if basin != -1:
                            not_commit = False
                            logger.info(f"! commit {basin}")

        logger.debug(f"end with {basin}")

        for entry in self.entries:
            if entry in ["x", "v", "f", "intc"]:
                trj[entry] = np.vstack(trj[entry])
            elif entry in ["pe", "T", "etotal"]:
                trj[entry] = np.hstack(trj[entry])

        return trj

    def sync_thermostat(self, params: dict):

        # copy some keys in
        for key in ["temperature", "friction", "fixcm", "dump_freq"]:
            if key in params:
                self.logger.debug(f"general key: {key} " f"will be override")
            params[key] = getattr(self, key)
        params["timestep"] = self.dt * units.fs
        return params

    def get_state(self, atoms):
        state = {"x": atoms.get_positions()}
        if "v" in self.entries:
            state["v"] = atoms.get_velocities()
        if "f" in self.entries:
            state["f"] = atoms.get_forces()
        state["pe"] = [atoms.get_potential_energy()]
        state["T"] = [atoms.get_temperature()]
        ke = np.sum(0.5 * atoms.get_masses() * np.linalg.norm(state["v"], axis=1) ** 2)
        state["etotal"] = [ke + state["pe"][0]]
        state["intc"] = self.colvar_func(atoms=atoms)
        return state

    def single_md_run(self, config, root: str, run_name: str):

        return self.single_run(
            "md_run",
            commit_run=False,
        )

    def single_commitor_run(self, config, root: str, run_name: str):

        return self.single_run(
            "md_run",
            commit_run=True,
        )

    def obtain_config(self, trj, iconfig):
        return {"x": trj["x"][iconfig], "v": trj["v"][iconfig]}

    def initialize_v(self):
        MaxwellBoltzmannDistribution(
            atoms=self.atoms, temp=self.temperature * units.kB, rng=self.np_random_state
        )
        v = self.atoms.get_velocities().reshape([-1])
        return v


def dummy_colvar(x=None, **kwargs):
    if x is None:
        return 1.0
    return np.average(x)


def dummy_commit(x=None, **kwargs):
    return -1
