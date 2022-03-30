from typing import Dict

import torchio as tio
from medical_shape.subject import ShapeSupportSubject
from medical_shape.transforms import TransformShapeValidationMixin

from medical_shape_building.utils import get_largest_cc


class SplitStructuresTransform(TransformShapeValidationMixin):
    def __init__(
        self,
        structures: Dict[str, int],
        include_other_keys: bool = False,
        not_only_largest_component: bool = False,
        **kwargs,
    ):
        self.structures = structures
        self.include_other_keys = include_other_keys
        self.not_only_largest_component = not_only_largest_component
        super().__init__(**kwargs)

    def apply_transform(self, subject: tio.data.Subject):
        new_sub = {}
        kwargs = {"intensity_only": False}

        if isinstance(subject, ShapeSupportSubject):
            kwargs["include_shapes"] = False
        for k, v in subject.items():
            if isinstance(v, tio.data.LabelMap):
                for _k, _v in self.structures.items():
                    new_sub[k + "/" + _k] = tio.LabelMap(
                        tensor=v[tio.constants.DATA] == _v, affine=v.affine
                    )

                    if not self.not_only_largest_component:
                        new_sub[k + "/" + _k].set_data(
                            get_largest_cc(new_sub[k + "/" + _k].tensor)
                        )
            elif self.include_other_keys:
                new_sub[k] = v

        return type(subject)(new_sub)
