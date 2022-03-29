import copy

from guide_bot.parameters import instrument_parameters as ipars

class Guide:
    """
    Guide with elements and constraints, can be added to McStas instrument

    The main class for describing a neutron guide, internally keeping a list
    of the added guide modules and user defined constraints. In the main logic
    section of guide_bot, the methods of the Guide object are called to
    prepare for optimization. Since elements define their opening dimensions,
    the end dimensions provided by the user are shifted back to the next
    opening dimensions by the transfer_end_specifications method. The Guide
    can add code to a McStasScript instrument object using the
    add_to_instrument method, this is done from target (backend) to source, and
    the previous start dimensions are transferred to the next module in each step.
    """

    def __init__(self, name=None):
        """
        Provides a Guide object that describes a guide with given constraints

        Initially the guide object is empty, and guide elements should be
        added using the add_guide_element method. The collection of guide
        elements can then be added to a McStasScript instrument and optimized
        together. Constraints on user defined parameters can be added directly
        to this Guide object, these will be in addition to the constraints
        defined through the options of the individual modules. Can have a
        current_owner attribute set which sets that owner to Elements added to
        this guide.

        ----------
        Parameters

        name : str
            Optional name of the guide
        """
        self.guide_elements = []

        self.name = name
        self.auto_name = None
        self.generate_name()

        self.original_guide_elements = None

        self.constraints = []

        self.current_owner = None
        self.required_components = set()

    def save_original(self):
        """
        Saves the original guide configuration
        """
        self.original_guide_elements = copy.deepcopy(self.guide_elements)

    def restore_original(self):
        """
        Restores to original guide configuration
        """
        self.guide_elements = self.original_guide_elements

    def generate_name(self):
        """
        Generates a name for this guide using first letter of each element
        """

        if self.auto_name is None:
            self.auto_name = self.name is None

        if self.auto_name:
            self.name = "Guide_"
            for element in self.guide_elements:
                first_letter = type(element).__name__[0]
                self.name += first_letter

    def make_name_unique(self, all_names):
        """
        Ensures the name of the guide is unique

        Parameters
        ----------

        all_names : list
            List of all guide names used to ensure this name is unique
        """
        suggested_name = self.name
        index = 0
        while suggested_name in all_names:
            suggested_name = self.name + "_Alt" + str(index)
            index += 1

        self.name = suggested_name
        return self.name

    def set_current_owner(self, owner):
        """
        Sets the current owner, added Elements will have this owner specified

        Parameters
        ----------

        owner : str
            Specifies the owner of this Element
        """
        self.current_owner = owner

    def add_guide_element(self, guide_element):
        """
        Adds a GuideElement to the Guide object

        This is the main method for adding GuideElements to the guide, this
        is appended to the current list of GuideElements.

        Parameters
        ----------

        guide_element : GuideElement
            New element added to the end of the guide
        """

        # todo: check element name not already in use

        if self.current_owner is not None:
            guide_element.set_owner(self.current_owner)

        self.guide_elements.append(guide_element)
        self.generate_name()

    def __iadd__(self, guide_element):
        """
        Adds a GuideElement to the Guide object with += syntax

        This is the main method for adding GuideElements to the guide, this
        is appended to the current list of GuideElements.

        Parameters
        ----------

        guide_element : GuideElement
            New element added to the end of the guide
        """
        self.add_guide_element(guide_element)

        return self

    def add_guide_element_at_start(self, guide_element):
        """
        Adds a GuideElement to the start of the Guide

        Allows adding a GuideElement to the start of the guide instead of the
        end.

        Parameters
        ----------

        guide_element : GuideElement
            New element added at the start of the guide
        """
        if self.current_owner is not None:
            guide_element.set_owner(self.current_owner)

        # todo: check element name not already in use
        self.guide_elements = [guide_element] + self.guide_elements

    def add_constraint(self, constraint):
        """
        Adds constraint between user defined parameters

        Constraints can be added that uses parameters derived from the
        InstrumentParameter class. These constraints are in addition to those
        defined in the options of the individual guide modules.

        Parameters
        ----------

        constraint : Constraint
            Adds the constraint, will be exported to the optimizer
        """
        self.constraints.append(constraint)

    def export_constraints(self, instrument_parameters):
        """
        Exports the contained constraints to object used by the optimizer

        The modules adds their constraints to instrument_parameters which is
        an instance of InstrumentParameterContainer, and the user defined
        can be exported to this format using this method. In this way the
        optimizer will get both types of constraints in the same system.

        Parameters

        instrument_parameters : InstrumentParameterContainer
            Container to which the Guide constraints are added
        """
        for constraint in self.constraints:
            instrument_parameters.add_constraint(constraint)

    def transfer_end_specifications(self):
        """
        Transfer specified end dimensions to next module as start dimensions

        If end dimensions are specified by the user, they will overwrite the
        start dimensions set at the next module that may or may not have been
        specified by the user.
        """

        for this_guide, next_guide in zip(self.guide_elements[0:-1], self.guide_elements[1:]):
            if this_guide.end_width is not None:
                next_guide.start_width = this_guide.end_width

            if this_guide.end_height is not None:
                next_guide.start_height = this_guide.end_height

    def add_full_instrument(self, instrument, instrument_parameters, moderator, target):
        """
        Adds McStasScript objects describing this guide to a instrument

        Takes a McStasScript instrument objects and adds the guide modules
        contained in this Guide object to the instrument. This is done from
        the target to the source, and the start dimensions from each module
        is carried to the next to ensure the guide is closed. The target and
        moderator is added as well. The wavelength range is contained in the
        target description, but needed by the moderator, this transfer is
        also performed in this method.

        Parameters
        ----------

        instrument : McStasScript instr object
            Instrument object to which the guide should be added

        instrument_parameters : InstrumentParameterContainer
            The InstrumentParameterContainer with parameters and constraints

        moderator : Object derived from BaseSource
            Description of the source, will be added to the instrument

        target : Object derived from Beam
            Descrption of sample / figure of merit, will be added to instrument
        """
        target.add_to_instrument(instrument, instrument_parameters)
        target.add_wavelength_parameters(instrument_parameters)

        target_width = ipars.FixedInstrumentParameter("target_width", target["width"])
        target_height = ipars.FixedInstrumentParameter("target_height", target["height"])

        previous_start_dimensions = [target_width, target_height]

        for guide in reversed(self.guide_elements):
            guide.setup_instrument_and_parameters(instrument, instrument_parameters)
            guide.set_end_dimensions(previous_start_dimensions[0], previous_start_dimensions[1])
            guide.add_to_instr()

            previous_start_dimensions = [guide.start_width, guide.start_height]

        # Moderator gets the first guide module to set up focusing
        moderator.add_to_instrument(instrument, instrument_parameters, guide)

    def set_instrument_and_instr_parameters(self, instrument, instrument_parameters):
        """
        Sets McStasScript instrument and instrument parameter container

        All elements are informed of the current instrument object and
        instrument parameter container.

        instrument : McStasScript instr object
            Instrument object to which the guide should be added

        instrument_parameters : InstrumentParameterContainer
            The InstrumentParameterContainer with parameters and constraints
        """

        for element in self.guide_elements:
            element.setup_instrument_and_parameters(instrument, instrument_parameters)

    def add_to_instrument(self, target_dimensions):
        """
        Adds McStasScript objects describing this guide to a instrument

        Takes a McStasScript instrument objects and adds the guide modules
        contained in this Guide object to the instrument. This is done from
        the target to the source, and the start dimensions from each module
        is carried to the next to ensure the guide is closed. The target and
        moderator is added as well. The wavelength range is contained in the
        target description, but needed by the moderator, this transfer is
        also performed in this method.

        Parameters
        ----------

        target_dimensions : list of length 2
            The width and height parameter for target dimensions in a list
        """

        reference = "ABSOLUTE"
        for element, next_element in zip(self.guide_elements[:-1], self.guide_elements[1:]):
            element.reference_component_name = reference
            reference = element.end_component_name
            element.set_end_dimensions(next_element.start_width, next_element.start_height)
            element.add_to_instr()

        last_element = self.guide_elements[-1]
        last_element.reference_component_name = reference
        last_element.set_end_dimensions(target_dimensions[0], target_dimensions[1])
        last_element.add_to_instr()

    def write_log_file(self, filename):
        # Start file
        with open(filename, "w") as file:
            file.write("Guide log file from python guide_bot\n")

            for element in self.guide_elements:
                element.write_to_log(file)

    def copy_components(self, destination):
        """
        Copies necessary components to destination
        """
        for element in self.guide_elements:
            required_components = element.copy_components(destination)
            for required_component in required_components:
                self.required_components.add(required_component)

    def __repr__(self):
        """
        Provides a string describing the Guide object
        """
        string = "Guide object: "
        if self.name is not None:
            string += self.name
        string += "\n"
        for element in self.guide_elements:
            string += element.__repr__() + "\n"

        for constraint in self.constraints:
            string += constraint.__repr__() + "\n"

        return string
