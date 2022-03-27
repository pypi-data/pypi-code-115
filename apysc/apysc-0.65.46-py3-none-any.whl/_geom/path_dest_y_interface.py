"""Interface class implementation for the destination y path data.
"""

from typing import Dict

from apysc._html.debug_mode import add_debug_info_setting
from apysc._type.attr_linking_interface import AttrLinkingInterface
from apysc._type.int import Int
from apysc._type.revert_interface import RevertInterface


class PathDestYInterface(RevertInterface, AttrLinkingInterface):

    _dest_y: Int

    def _initialize_dest_y_if_not_initialized(self) -> None:
        """
        Initialize the _dest_y attribute if this instance
        does not initialize it yet.
        """
        if hasattr(self, '_dest_y'):
            return
        self._dest_y = Int(0)

        self._append_dest_y_linking_setting()

    @add_debug_info_setting(  # type: ignore[misc]
        module_name=__name__, class_name='PathDestYInterface')
    def _append_dest_y_linking_setting(self) -> None:
        """
        Append a dest_y linking setting.
        """
        self._append_applying_new_attr_val_exp(
            new_attr=self._dest_y, attr_name='dest_y')
        self._append_attr_to_linking_stack(
            attr=self._dest_y, attr_name='dest_y')

    @property  # type: ignore[misc]
    @add_debug_info_setting(  # type: ignore[misc]
        module_name=__name__, class_name='PathDestYInterface')
    def dest_y(self) -> Int:
        """
        Get a y-coordinate of the destination point.

        Returns
        -------
        dest_y : Int
            Y-coordinate of the destination point.

        Examples
        --------
        >>> import apysc as ap
        >>> bezier_2d: ap.PathBezier2D = ap.PathBezier2D(
        ...     control_x=50, control_y=0,
        ...     dest_x=100, dest_y=50)
        >>> bezier_2d.dest_y = ap.Int(75)
        >>> bezier_2d.dest_y
        Int(75)
        """
        self._initialize_dest_y_if_not_initialized()
        return self._dest_y._copy()

    @dest_y.setter
    def dest_y(self, value: Int) -> None:
        """
        Set a y-coordinate of the destination point.

        Parameters
        ----------
        value : Int
            Y-coordinate of the destination point
        """
        from apysc._html.debug_mode import DebugInfo
        with DebugInfo(
                callable_='dest_y', args=[value], kwargs={},
                module_name=__name__,
                class_name=PathDestYInterface.__name__):
            self._initialize_dest_y_if_not_initialized()
            self._dest_y.value = value

            self._append_dest_y_linking_setting()

    _dest_y_snapshots: Dict[str, int]

    def _make_snapshot(self, *, snapshot_name: str) -> None:
        """
        Make a value's snapshot.

        Parameters
        ----------
        snapshot_name : str
            Target snapshot name.
        """
        self._initialize_dest_y_if_not_initialized()
        self._set_single_snapshot_val_to_dict(
            dict_name='_dest_y_snapshots',
            value=int(self._dest_y._value), snapshot_name=snapshot_name)

    def _revert(self, *, snapshot_name: str) -> None:
        """
        Revert a value if a snapshot exists.

        Parameters
        ----------
        snapshot_name : str
            Target snapshot name.
        """
        if not self._snapshot_exists(snapshot_name=snapshot_name):
            return
        self._initialize_dest_y_if_not_initialized()
        self._dest_y._value = self._dest_y_snapshots[snapshot_name]
