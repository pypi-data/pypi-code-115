"""
Analysis and transformation for HDF5 support.
"""
import types as pytypes
import numba
from numba.core import ir, types
from numba.core.ir_utils import compile_to_numba_ir, find_callname, find_const, get_definition, guard, replace_arg_nodes, require
import bodo
import bodo.io
from bodo.utils.transform import get_const_value_inner


class H5_IO:

    def __init__(self, func_ir, _locals, flags, arg_types):
        self.func_ir = func_ir
        self.locals = _locals
        self.flags = flags
        self.arg_types = arg_types

    def handle_possible_h5_read(self, assign, lhs, rhs):
        zln__lvbug = self._get_h5_type(lhs, rhs)
        if zln__lvbug is not None:
            ydic__aba = str(zln__lvbug.dtype)
            cxmpg__ycxa = 'def _h5_read_impl(dset, index):\n'
            cxmpg__ycxa += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(zln__lvbug.ndim, ydic__aba))
            iwle__vipn = {}
            exec(cxmpg__ycxa, {}, iwle__vipn)
            lpyop__kosmx = iwle__vipn['_h5_read_impl']
            hdja__gfz = compile_to_numba_ir(lpyop__kosmx, {'bodo': bodo}
                ).blocks.popitem()[1]
            dcn__zmfv = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(hdja__gfz, [rhs.value, dcn__zmfv])
            nwvv__cxiz = hdja__gfz.body[:-3]
            nwvv__cxiz[-1].target = assign.target
            return nwvv__cxiz
        return None

    def _get_h5_type(self, lhs, rhs):
        zln__lvbug = self._get_h5_type_locals(lhs)
        if zln__lvbug is not None:
            return zln__lvbug
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        dcn__zmfv = rhs.index if rhs.op == 'getitem' else rhs.index_var
        fofv__mpvp = guard(find_const, self.func_ir, dcn__zmfv)
        require(not isinstance(fofv__mpvp, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            txm__ndd = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            ojehc__ttol = get_const_value_inner(self.func_ir, txm__ndd,
                arg_types=self.arg_types)
            obj_name_list.append(ojehc__ttol)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        wklbc__bwn = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        vpfb__fivuo = h5py.File(wklbc__bwn, 'r')
        bdpbz__woq = vpfb__fivuo
        for ojehc__ttol in obj_name_list:
            bdpbz__woq = bdpbz__woq[ojehc__ttol]
        require(isinstance(bdpbz__woq, h5py.Dataset))
        wtcj__rba = len(bdpbz__woq.shape)
        jwg__xnjyg = numba.np.numpy_support.from_dtype(bdpbz__woq.dtype)
        vpfb__fivuo.close()
        return types.Array(jwg__xnjyg, wtcj__rba, 'C')

    def _get_h5_type_locals(self, varname):
        pjxcf__nsusi = self.locals.pop(varname, None)
        if pjxcf__nsusi is None and varname is not None:
            pjxcf__nsusi = self.flags.h5_types.get(varname, None)
        return pjxcf__nsusi
