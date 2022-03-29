try:
    from lammps import PyLammps, LAMMPS_INT, LMP_STYLE_GLOBAL, LMP_TYPE_SCALAR
    import ctypes
    from ctypes import c_double
except:
    Warning("Lammps python package is not installed")

import numpy as np

from copy import deepcopy
from os import getcwd, chdir
from os.path import isfile
from string import Formatter

from .engine import Engine

# TO DO: should enable either file storage or memory storage


class LAMMPS(Engine):
    def __init__(
        self,
        templates={},
        md_params={},
        committor_params={},
        lammps_init_params=dict(
            units="metal",
            atom_style="atomic",
            boundary="p p p",
            newton="off",
        ),
        velocity_group_name: str = "all",
        rc_command: str = None,
        continuous_mode: bool = True,
        **kwargs,
    ):
        """
        Args:
        """

        Engine.__init__(self, **kwargs)
        self.lammps_init_params = lammps_init_params
        self.velocity_group_name = velocity_group_name
        self.rc_command = rc_command
        self.continuous_mode = continuous_mode

        new_templates = {}
        for sim_type, template in templates.items():
            new_templates[sim_type] = {}
            for file_name, file_str in template.items():
                if isfile(file_str):
                    with open(file_str) as fin:
                        file_str = fin.read()
                new_templates[sim_type][file_name] = file_str
        templates = new_templates

        self.md_templates = templates.get("md", None)
        self.committor_templates = templates.get("committor", None)
        self.md_params = md_params
        self.md_params["steps"] = self.md_n_steps
        self.committor_params = committor_params
        self.committor_params["steps"] = self.committor_n_steps

        self.seed_index = 10000 if self.seed is None else self.seed

        self.lmp = None

    def init_lmp(self, init_params):
        args = "-screen none"
        lmp = PyLammps(cmdargs=args.split())
        for k, v in init_params.items():
            if k == "atom_modify":
                v_list = v.split()
                if "map" in v_list:
                    idx = v_list.index("map")
                    if v_list[idx + 1] != "yes":
                        self.logger.debug(
                            f"atom_modify map {v_list[idx+1]} will be overrode"
                        )
            getattr(lmp, k)(v)
            self.logger.debug(f"lmp: {k} {v}")
        lmp.atom_modify("map yes")
        return lmp

    def __del__(self):
        self.lmp.finalize()
        self.lmp.close()

    def check_instance(self):
        pass

    def sync_thermostat(self, templates: dict, params: dict):

        # copy some keys in
        key_list = ["temperature", "friction", "dt", "dump_freq"]
        for key in key_list:
            if key in params:
                Warning(f"general key: {key} " f"will be override")
            params[key] = getattr(self, key)

        template_list = ["prefix", "seed"]
        f = Formatter()
        format_keys = []
        for script in templates.values():
            format_keys += [i[1] for i in f.parse(script) if i[1] is not None]
        if len(format_keys) > 0:
            for key in template_list + key_list:
                assert key in format_keys, f"{key} is not in template"
        for key in format_keys:
            if key not in template_list:
                assert key in params, f"{key} is not in feed list"

    def write_scripts(self, scripts, para):
        """
        write the script with templates and parameters

        Args:
            scripts (dict): dict of formated string with variables to be fed
            para (dict): dictionary of parameters that includes \
                         "filename":filenames_list
        """

        para["seed"] = self.seed_index
        self.seed_index += 10

        return {filename: script.format(**para) for filename, script in scripts.items()}

    def single_run(self, params, start_config, root, run_name):
        """
        run multiple simulations given the

        Args:
            params (dict): dict of parameters to plug into the template
            template (list): list of formated string
            start_config (list): list of starting configuration,
                                 which are dicts with x and v np arrays
            workdir (str): string for workdir

        Return:
            trajectories (list): list of lammpstrj files that \
                    store the trajectory

        Each item is a dictionary that stores 'x' and 'v'
        """

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

        para = deepcopy(params)

        para["prefix"] = run_name
        para["run_name"] = run_name
        lmp = self.lmp

        output = self.get_replica_log(subroot, run_name)
        logger = output.open_logfile("pysampling_engine.log")

        x = start_config["x"]
        lmp.lmp.scatter_atoms("x", 1, 3, ctypes.c_void_p(x.ctypes.data))
        logger.debug(f"change atom positions")

        v = lmp.lmp.gather_atoms("v", 1, 3)
        if np.max(np.abs(v)) == 0 and start_config.get("v", None) is None:
            v = None
            lmp.velocity(
                f"{self.velocity_group_name} create {self.temperature}"
                f" {self.seed_index} rot yes mom yes dist gaussian"
            )
            logger.debug(
                f"lmp: velocity {self.velocity_group_name} create {self.temperature}"
                f" {self.seed_index} rot yes mom yes dist gaussian"
            )
            self.seed_index += 10
        else:
            lmp.lmp.scatter_atoms(
                "v", 1, 3, ctypes.c_void_p(start_config["v"].ctypes.data)
            )
            logger.debug(f"change atom velocities")

        lmp.log(f"{run_name}.log")
        if self.rc_command is not None:
            lmp.fix(f"{run_name}_rc " + self.rc_command.format(**para))
            logger.debug(f"lmp: fix {run_name} " + self.rc_command.format(**para))
        lmp.compute(f"{run_name}temp {self.velocity_group_name} temp")

        lmp.command("run 0 pre yes post no")
        logger.debug("lmp: run 0 pre yes post no")

        step = 0  # -1
        trj = {k: [v] for k, v in (self.get_state(lmp, run_name)).items()}
        _T = trj["T"][-1]
        _pe = trj["pe"][-1]
        _ke = trj["ke"][-1]
        logger.debug(f"{step:8d} {_T:10.4f} {_pe:10.4f} {_ke:10.4f} {_ke+_pe:10.4f}")

        init_lammps_steps = lmp.lmp.get_thermo("step")

        lmp.thermo(self.dump_freq)

        steps = para["steps"]
        stop = False
        while step < steps and not stop:

            _step = np.min((steps - step, self.dump_freq))
            lmp.command(f"run {_step} pre no post no")
            # lmp.run(_step, "pre yes post yes") somehow it doesn't work
            step += _step

            lammps_steps = lmp.lmp.get_thermo("step") - init_lammps_steps
            if lammps_steps < step:
                stop = True
                self.logger.debug("Early stop for unknown reason")

            if not stop:
                state = self.get_state(lmp)
                _T = trj["T"][-1]
                _pe = trj["pe"][-1]
                _ke = trj["ke"][-1]
                logger.debug(
                    f"{step:8d} {_T:10.4f} {_pe:10.4f} {_ke:10.4f} {_ke+_pe:10.4f}"
                )

        lmp.command("run 0 pre no post yes")
        logger.debug("lmp: run 0 pre no post yes")

        if self.rc_command is not None:
            lmp.command(f"unfix {run_name}_rc")
            logger.debug(f"lmp: unfix {run_name}_rc")
        lmp.command(f"uncompute {run_name}temp")

        for entry in self.entries:
            if entry in ["x", "v", "f"]:
                trj[entry] = np.vstack(trj[entry])
            elif entry in ["pe", "T", "etotal"]:
                trj[entry] = np.hstack(trj[entry])

        trj.update(self.read_intc(run_name))
        n_frames = len(trj["x"])
        if "n" in trj:
            trj["n"] = np.ones(n_frames, dtype=int) * trj["n"]
        if "intc" in trj:
            nframes = trj["intc"].shape[0]
            if nframes != trj["x"].shape[0]:
                raise RuntimeError("hello")

        return trj

    def get_state(self, lmp, run_name):
        state = {}
        for entry in self.entries:
            if entry in ["x", "v", "f"]:
                state[entry] = np.copy(lmp.lmp.gather_atoms("x", 1, 3))

        _pe = lmp.lmp.get_thermo("pe")
        _ke = lmp.lmp.get_thermo("ke")
        # _T = lmp.lmp.get_thermo("temp")
        _T = lmp.lmp.extract_compute(
            f"{run_name}temp", LMP_STYLE_GLOBAL, LMP_TYPE_SCALAR
        )
        state["pe"] = _pe
        state["ke"] = _ke
        state["etotal"] = _ke + _pe
        state["T"] = _T
        return state

    def single_md_run(self, config, root: str, run_name: str):
        return self.single_run(self.md_params, config, root, run_name)

    def single_committor_run(self, config, root, run_name):
        return self.single_run(self.committor_params, config, root, run_name)

    def md_run(self, start_config=[], suffix="md", force_restart: bool = True):
        return self.run(
            params=self.md_params,
            templates=self.md_templates,
            single_run=LAMMPS.single_md_run,
            start_config=start_config,
            suffix=suffix,
            md=True,
            force_restart=force_restart,
        )

    def committor_run(
        self, start_config=[], suffix="committor", force_restart: bool = True
    ):
        return self.run(
            params=self.committor_params,
            templates=self.committor_templates,
            single_run=LAMMPS.single_committor_run,
            start_config=start_config,
            suffix=suffix,
            md=False,
            force_restart=force_restart,
        )

    def run(
        self,
        params,
        templates,
        start_config,
        suffix,
        single_run,
        md: bool = True,
        force_restart: bool = True,
    ):

        self.sync_thermostat(templates=templates, params=params)

        first_run = False
        if self.lmp is None or force_restart:
            first_run = True
            self.lmp = self.init_lmp(init_params=self.lammps_init_params)
            lmp = self.lmp
            lmp.read_data(self.x0)
            self.logger.debug(f"read_data {self.x0}")

        subroot = self.output_kwargs["root"] + "/" + self.output_kwargs["run_name"]
        scripts = self.write_scripts(templates, params)

        # move onto the working folder
        cwd = getcwd()
        chdir(f"{subroot}")
        self.logger.debug(f"chdir to {subroot}")

        for filename, script in scripts.items():
            if ".in" in filename and (force_restart or first_run):
                lines = script.splitlines()
                for line in lines:
                    self.logger.debug(f"lmp: {line}")
                    self.lmp.lmp.command(line)
            elif ".in" not in filename:
                with open(f"{suffix}_{filename}", "w+") as fout:
                    print(script, file=fout)

        trjs = self.multiple_runs(
            run_function=single_run,
            start_config=start_config,
            suffix=suffix,
        )

        if force_restart:
            lmp.clear()
            self.logger.debug("lmp: clear")
        chdir(cwd)
        self.logger.debug(f"chdir to {cwd}")

        return trjs

    def obtain_config(self, trj, iconfig):
        return {"x": np.copy(trj["x"][iconfig]), "v": np.copy(trj["v"][iconfig])}

    def get_structure(self, config):
        x0 = config["x0"]
        if isinstance(x0, str):
            temp_lmp = self.init_lmp(self.lammps_init_params)
            temp_lmp.read_data(x0)
            x = np.copy(temp_lmp.lmp.gather_atoms("x", 1, 3))
            v = np.copy(temp_lmp.lmp.gather_atoms("v", 1, 3))
            if np.max(np.abs(v)) == 0:
                v = None
            del temp_lmp
        return {"x": x, "v": v}

    def read_intc(self, run_name):
        """
        read intc files and return the xyz, vxyz info
        """

        trj = {}

        filename = f"{run_name}_intc.dat"
        if isfile(filename):
            data = np.loadtxt(filename)
            if len(data.shape) == 1:
                data = data.reshape([1, -1])
            trj["intc"] = data[:, 1:]

        filename = f"{run_name}_basin"
        if isfile(filename):
            try:
                n = np.loadtxt(filename).reshape([-1])
                n = n[-1] - 1
            except Exception as e:
                n = -1
                intc = trj["intc"][-1]
                self.logger.debug(f"no basin: {e} {intc}")
            trj["n"] = int(n)

        return trj
