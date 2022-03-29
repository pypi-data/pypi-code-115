import numpy as np

from scipy.spatial.transform import Rotation as R

from guide_bot.base_elements import guide_elements
from guide_bot.parameters import instrument_parameters as ipars
from guide_bot.base_elements.guide_elements import PositionAndRotation

class Kink(guide_elements.GuideElement):
    """
    Kink GuideElement that inserts an empty space and kink into a guide

    A Kink still has start and end dimensions as it is supposed to fit with the
    surrounding elements, as if it was a guide element. In this way, it can
    for example be used to set a Kink for a chopper, and force the adjacent
    Elements to narrow to the required width / height for the chopper. A kink
    changes the position and direction of a guide element after.
    """

    def __init__(self, name, length=None, start_point=None,
                 start_width=None, start_height=None,
                 end_width=None, end_height=None, angle=None,
                 h_displacement=None, v_displacement=None,
                 displacement=None, kink_dir="horizontal",
                 **kwargs):
        """
        Kink GuideElement that inserts an empty space into a guide

        A Kink still has start and end dimensions as it is supposed to fit with
        the surrounding elements, as if it was a guide element. In this way,
        it can for example be used to set a Kink for a chopper, and force the
        adjacent Elements to narrow to the required width / height for the
        chopper. If end_width / end_height is specified, they will override
        the following modules start_width / start_height settings. A kink
        changes the position and direction of a guide element after, the
        direction is controlled with kink_dir, and a small displacement is
        included unless disabled with for example displacement=0.

        Parameters
        ----------
        name : str
            Name of the element

        length : (float, None, InstrumentParameter)
            Length of guide element, optimized parameter

        start_point : (float, None, InstrumentParameter)
            Distance from source to start of the Kink element

        start_width : (float, None, InstrumentParameter)
            Width of the start of the Kink

        start_height : (float, None, InstrumentParameter)
            Height of the start of the Kink

        end_width : (float, None, InstrumentParameter)
            Width of the end of the Kink

        end_height : (float, None, InstrumentParameter)
            Height of the end of the Kink

        kink_dir : str
            Allowed: 'horizontal', 'vertical', 'left', 'right', 'up', 'down'

        h_displacement : float
            Horizontal displacement of next element [m]

        v_displacement : float
            Vertical displacement of next element [m]

        displacement : float
            Sets both horizontal and vertical displacement simultaneously
        """

        if displacement is not None:
            h_displacement = displacement
            v_displacement = displacement

        # Internalize stuff relevant for this Element

        super().__init__(name, length=length, start_point=start_point,
                         start_width=start_width, start_height=start_height,
                         end_width=end_width, end_height=end_height, **kwargs)

        if kink_dir == "left":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", 1)
            min_angle = 0
            max_angle = 3
        elif kink_dir == "right":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", 1)
            min_angle = -3
            max_angle = 0
        elif kink_dir == "horizontal":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", 1)
            min_angle = -3
            max_angle = 3
        elif kink_dir == "up":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", -1)
            min_angle = 0
            max_angle = 3
        elif kink_dir == "down":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", -1)
            min_angle = -3
            max_angle = 0
        elif kink_dir == "vertical":
            self.horizontal_kink_par = ipars.FixedInstrumentParameter(self.name + "_horizontal", -1)
            min_angle = -3
            max_angle = 3

        self.kink_angle = guide_elements.handle_input_parameter(name + "_kink_angle", angle,
                                                                default_min=min_angle, default_max=max_angle)
        self.h_displacement = guide_elements.handle_input_parameter(name + "_h_displacement", h_displacement,
                                                                    default_min=-0.03, default_max=0.03)
        self.v_displacement = guide_elements.handle_input_parameter(name + "_v_displacement", v_displacement,
                                                                    default_min=-0.03, default_max=0.03)

    def add_to_instr(self):
        """
        Adds code describing the Kink element to the current McStas instrument

        This methods uses McStasScript to add components and code to a McStas
        instrument object. The McStas instrument object is an attribute of the
        class called current_instrument. New instrument parameters can also be
        created and added to the optimization by using the current_parameters
        attribute.

        Since the add_to_instr method of all the Elements are called in order
        from the sample to the source, it is important the components are
        added after the Origin component to ensure the correct order.
        """

        self.current_parameters.add_parameter(self.kink_angle)
        self.current_parameters.add_parameter(self.h_displacement)
        self.current_parameters.add_parameter(self.v_displacement)
        self.current_parameters.add_parameter(self.horizontal_kink_par)

        Kink = self.current_instrument.add_component(self.end_component_name, "Arm")
        position = [self.h_displacement.name, self.v_displacement.name, self.get_length_name()]
        Kink.set_AT(position, RELATIVE=self.reference_component_name)

        if self.horizontal_kink_par.get_value() == 1:
            Kink.set_ROTATED([0, self.kink_angle.name, 0], RELATIVE=self.reference_component_name)
        elif self.horizontal_kink_par.get_value() == -1:
            Kink.set_ROTATED([self.kink_angle.name, 0, 0], RELATIVE=self.reference_component_name)
        else:
            raise ValueError("horizontal_kink_par had illegal value.")

    def write_to_log(self, file):
        self.write_to_log_base(file)
        if self.horizontal_kink_par.get_value() == 1:
            direction = "horizontal"
        elif self.horizontal_kink_par.get_value() == -1:
            direction = "vertical"
        else:
            raise RunTimeError("horizontal_kink_par should have a value of either +1 or -1.")

        self.write_parameter(file, "kink_angle", self.kink_angle, direction)
        self.write_parameter(file, "horizontal_kink", self.horizontal_kink_par, direction)
        self.write_parameter(file, "h_displacement", self.h_displacement, "horizontal")
        self.write_parameter(file, "v_displacement", self.v_displacement, "vertical")


def guide_width(par_dict, distance_unit_less):
    start_width = par_dict["start_width"]
    end_width = par_dict["end_width"]

    return start_width + (end_width - start_width) * distance_unit_less

def guide_height(par_dict, distance_unit_less):
    start_height = par_dict["start_height"]
    end_height = par_dict["end_height"]

    return start_height + (end_height - start_height)*distance_unit_less

def center_line(start_pr, par_dict, distance_unit_less):

    kink_angle = par_dict["kink_angle"]
    horizontal_kink = par_dict["horizontal_kink"]
    h_displacement = par_dict["h_displacement"]
    v_displacement = par_dict["v_displacement"]

    start = par_dict["start_point"]
    end = par_dict["next_start_point"]
    start_height = par_dict["start_height"]
    end_height = par_dict["end_height"]

    length = end - start

    displacement_x = h_displacement*distance_unit_less
    displacement_y = v_displacement*distance_unit_less
    displacement_z = length*distance_unit_less

    x_vector = np.array([1, 0, 0])
    y_vector = np.array([0, 1, 0])
    z_vector = np.array([0, 0, 1])

    start_direction = start_pr.rotation

    x_vector = start_direction.apply(x_vector)
    y_vector = start_direction.apply(y_vector)
    z_vector = start_direction.apply(z_vector)

    updated_position = start_pr.position + displacement_x*x_vector + displacement_y*y_vector + displacement_z*z_vector

    if horizontal_kink == 1:
        updated_rotation = start_pr.rotation * R.from_euler("y", kink_angle, degrees=True)
    elif horizontal_kink == -1:
        updated_rotation = start_pr.rotation * R.from_euler("x", kink_angle, degrees=True)

    return PositionAndRotation(updated_position, updated_rotation)