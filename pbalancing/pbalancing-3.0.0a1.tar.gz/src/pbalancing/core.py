# The MIT License (MIT)
#
# Copyright (c) 2018 Timo Lubitz
# Copyright (c) 2022 Elad Noor, Weizmann Institute of Science
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import copy
import logging
import os
import re
import sys

import libsbml
import pkg_resources
from sbtab import SBtab, validatorSBtab

from . import balancer, kineticizer, misc


logger = logging.getLogger(__name__)


def parameter_balancing_wrapper(
    sbml,
    sbtab_data_name: str = None,
    sbtab_prior_name: str = None,
    sbtab_options_name: str = None,
    no_pseudo_values: bool = False,
    output_name: str = None,
    concat: bool = False,
):
    """
    wrapper for parameter balancing.

    Parameters
    ==========
    sbml: string (path to sbml file)
    sbtab_data_name: string (path to sbtab data file)
    sbtab_prior_name: string (path to sbtab prior file)
    sbtab_options_name: string (path to sbtab options file)
    no_pseudo_values: Boolean (disable usage of pseudo values)
    output_name: string (name for the output files)
    concat: Boolean (enable writing of concatenation input/output file)
    """
    model_name = sbml
    parameter_dict = {}

    ###########################
    # 1: open and prepare the files; then check for some rudimentary validity:
    # 1.1: SBML model
    reader = libsbml.SBMLReader()
    try:
        sbml_file = reader.readSBML(model_name)
    except Exception:
        raise ParameterBalancingError(f"The SBML file {model_name} could not be found")
    try:
        sbml_model = sbml_file.getModel()
    except Exception:
        raise ParameterBalancingError(f"The SBML file {model_name} is corrupt")
    valid_extension = misc.validate_file_extension(model_name, "sbml")
    if not valid_extension:
        raise ParameterBalancingError(
            f"The SBML file {model_name} has an incorrect xml extension"
        )

    if sbml_model.getNumReactions() > 250:
        raise ParameterBalancingError(
            "The given model has more than 250 reactions and we "
            "do not recommend employing models that large for "
            "parameter balancing."
        )

    pb = balancer.ParameterBalancing(sbml_model)

    ###########################
    # 1.2: open and prepare the optional SBtab data file
    if sbtab_data_name:
        valid_extension = misc.validate_file_extension(sbtab_data_name, "sbtab")
        if not valid_extension:
            logger.error(
                f"Incorrect extension for the SBtab data file: '{sbtab_data_name}'"
            )

        if not os.path.exists(sbtab_data_name):
            logger.error(f"Cannot find the SBtab data file: '{sbtab_data_name}'")
        with open(sbtab_data_name, "r") as f:
            f_content = f.read()

        # try:
        #     sbtab_delimiter = misc.check_delimiter(f_content)
        # except Exception:
        #     sbtab_delimiter = "\t"

        sbtab_data = SBtab.SBtabTable(f_content, sbtab_data_name)
        sbtab_data_validate = validatorSBtab.ValidateTable(sbtab_data)

        for warning in sbtab_data_validate.return_output():
            logger.warning(warning)

    ###########################
    # 1.3: open and prepare an optional SBtab prior file;
    #      if this is not provided, open the default prior file
    if sbtab_prior_name:
        # try to open and read the file
        valid_extension = misc.validate_file_extension(sbtab_prior_name, "sbtab")
        if not valid_extension:
            print(
                "The SBtab prior file %s has not the correct file"
                "extension." % (sbtab_prior_name)
            )
        try:
            f = open(sbtab_prior_name, "r")
            f_content = f.read()
        except Exception:
            print("The SBtab prior file %s cannot be found or read." % sbtab_prior_name)

        # initialise an SBtab object with the content and check its validity
        sbtab_prior = SBtab.SBtabTable(f_content, sbtab_prior_name)
        pb.get_parameter_information(sbtab_prior)
        sbtab_prior_validate = validatorSBtab.ValidateTable(sbtab_prior)

        for warning in sbtab_prior_validate.return_output():
            logger.warning("SBtab prior file: " + warning)

        for warning in misc.valid_prior(sbtab_prior):
            logger.warning("SBtab prior file: " + warning)

        # extract crucial information from prior
        (pseudos, priors, pmin, pmax) = misc.extract_pseudos_priors(sbtab_prior)
    else:
        # open default prior file
        p = pkg_resources.resource_filename("pbalancing", "data/pb_prior.tsv")
        try:
            prior_file = open(p, "r")
        except Exception as e:
            print("The prior file (pb_prior.tsv) could not be found")
            raise e
        prior = prior_file.read()
        sbtab_prior = SBtab.SBtabTable(prior, "pb_prior.tsv")
        sbtab_prior_validate = validatorSBtab.ValidateTable(sbtab_prior)

        for warning in sbtab_prior_validate.return_output():
            logger.warning("SBtab prior file: " + warning)

        for warning in misc.valid_prior(sbtab_prior):
            logger.warning("SBtab prior file: " + warning)

        # extract crucial information from prior
        (pseudos, priors, pmin, pmax) = misc.extract_pseudos_priors(sbtab_prior)

    ###########################
    # 1.4: open and prepare an optional SBtab options file;
    #      if this is not provided, open the default options file
    if sbtab_options_name:
        valid_extension = misc.validate_file_extension(sbtab_options_name, "sbtab")
        if not valid_extension:
            logger.error(
                "The SBtab options file %s has not the correct file"
                " extension." % (sbtab_options_name)
            )
        try:
            with open(sbtab_options_name, "r") as f:
                f_content = f.read()
        except Exception as e:
            logger.error(
                "The SBtab options file %s cannot be found or"
                "read." % sbtab_options_name
            )
            raise e

        sbtab_options = SBtab.SBtabTable(f_content, sbtab_options_name)
        sbtab_options_validate = validatorSBtab.ValidateTable(sbtab_options)

        warnings = sbtab_options_validate.return_output()
        for warning in sbtab_options_validate.return_output():
            logger.warning("SBtab options file: " + warning)

        parameter_dict, log = misc.readout_config(sbtab_options)
        for warning in log:
            logger.warning("SBtab options file: " + warning)
    else:
        o = pkg_resources.resource_filename("pbalancing", "data/pb_options.tsv")
        try:
            with open(o, "r") as options_file:
                f_content = options_file.read()
        except Exception as e:
            logger.error("The options file (pb_options.tsv) could not be found")
            raise e
        sbtab_options = SBtab.SBtabTable(f_content, "pb_options.tsv")
        sbtab_options_validate = validatorSBtab.ValidateTable(sbtab_options)

        warnings = sbtab_options_validate.return_output()
        for warning in sbtab_options_validate.return_output():
            logger.warning("SBtab options file: " + warning)

        parameter_dict, log = misc.readout_config(sbtab_options)
        for warning in log:
            logger.warning("SBtab options file: " + warning)

    # Make empty SBtab if required
    if sbtab_data_name:
        sbtab = pb.make_sbtab(
            sbtab_data, sbtab_data_name, "All organisms", 43, pmin, pmax, parameter_dict
        )
        for warning in misc.id_checker(sbtab, sbml_model):
            logger.warning("SBtab data file: " + warning)
    else:
        sbtab = pb.make_empty_sbtab(pmin, pmax, parameter_dict)

    # end of file read in and processing;
    # now verify that all required keys are given for the parameter_dict;
    # if not, add them
    if "temperature" not in parameter_dict.keys():
        parameter_dict["temperature"] = 300
    if "ph" not in parameter_dict.keys():
        parameter_dict["ph"] = 7
    if "standard chemical potential" not in parameter_dict.keys():
        parameter_dict["standard chemical potential"] = True
    if "catalytic rate constant geometric mean" not in parameter_dict.keys():
        parameter_dict["catalytic rate constant geometric mean"] = True
    if "Michaelis constant" not in parameter_dict.keys():
        parameter_dict["Michaelis constant"] = True
    if "activation constant" not in parameter_dict.keys():
        parameter_dict["activation constant"] = True
    if "inhibitory constant" not in parameter_dict.keys():
        parameter_dict["inhibitory constant"] = True
    if "concentration" not in parameter_dict.keys():
        parameter_dict["concentration"] = True
    if "concentration of enzyme" not in parameter_dict.keys():
        parameter_dict["concentration of enzyme"] = True
    if "equilibrium constant" not in parameter_dict.keys():
        parameter_dict["equilibrium constant"] = True
    if "substrate catalytic rate constant" not in parameter_dict.keys():
        parameter_dict["substrate catalytic rate constant"] = True
    if "product catalytic rate constant" not in parameter_dict.keys():
        parameter_dict["product catalytic rate constant"] = True
    if "forward maximal velocity" not in parameter_dict.keys():
        parameter_dict["forward maximal velocity"] = True
    if "reverse maximal velocity" not in parameter_dict.keys():
        parameter_dict["reverse maximal velocity"] = True
    if "chemical potential" not in parameter_dict.keys():
        parameter_dict["chemical potential"] = True
    if "reaction affinity" not in parameter_dict.keys():
        parameter_dict["reaction affinity"] = True
    if "use_pseudo_values" not in parameter_dict.keys():
        parameter_dict["use_pseudo_values"] = False

    logger.info("Files successfully read. Start balancing.")

    # 2: Parameter balancing
    if parameter_dict["use_pseudo_values"] == "True" and not no_pseudo_values:
        sbtab_old = copy.deepcopy(sbtab)
        sbtab_new = pb.fill_sbtab(sbtab_old, pseudos, priors)
        pseudo_flag = "pseudos"
        logger.info("Parameter balancing is using pseudo values.")

    else:
        sbtab_new = pb.fill_sbtab(sbtab)
        pseudo_flag = "no_pseudos"
        logger.info("Parameter balancing is not using pseudo values.")

    (
        sbtab_final,
        mean_vector,
        mean_vector_inc,
        c_post,
        c_post_inc,
        r_matrix,
        shannon,
        concat_file,
    ) = pb.make_balancing(sbtab_new, sbtab, pmin, pmax, parameter_dict)

    # 3: inserting parameters and kinetics into SBML model
    transfer_mode = {
        "standard chemical potential": "weg",
        "equilibrium constant": "hal",
        "catalytic rate constant": "cat",
    }

    try:
        clear_mode = parameter_dict["parametrisation"]
        mode = transfer_mode[clear_mode]
    except Exception:
        mode = "hal"
    try:
        enzyme_prefac = parameter_dict["prefac"]
    except Exception:
        enzyme_prefac = True
    try:
        def_inh = parameter_dict["default_inh"]
    except Exception:
        def_inh = "complete_inh"
    try:
        def_act = parameter_dict["default_act"]
    except Exception:
        def_act = "complete_act"
    try:
        overwrite = parameter_dict["overwrite"]
    except Exception:
        overwrite = True
    kineticizer_cs = kineticizer.KineticizerCS(
        sbml_model, sbtab_final, mode, enzyme_prefac, def_inh, def_act, True
    )

    if output_name:
        output_name = output_name
    else:
        try:
            rm = re.match(".*/(.*)", str(model_name)).group(1)[:-4]
        except Exception:
            rm = str(model_name)[:-4]
        output_name = rm + "_balanced"

    logger.info("Done... writing output files.")

    # 5b: If requested write output file with concatenated input/output files
    if concat:
        with open(output_name + "_concat.tsv", "w") as c_file:
            c_file.write(concat_file)
        logger.info(f"The concat file {output_name}_concat.tsv has been written.")

    # 6: Write SBtab and SBML model
    with open(output_name + ".tsv", "w") as sbtab_file_new:
        sbtab_file_new.write(sbtab_final.to_str())
    logger.info(f"The SBtab file {output_name}.tsv has been written.")

    sbml_code = '<?xml version="1.0" encoding="UTF-8"?>\n' + sbml_model.toSBML()
    with open(output_name + ".xml", "w") as sbml_model_new:
        sbml_model_new.write(sbml_code)
    logger.info(f"The SBML file {output_name}.xml has been written.")
    logger.info(">> Goodbye.")

    return sbml_model_new, sbtab_final
