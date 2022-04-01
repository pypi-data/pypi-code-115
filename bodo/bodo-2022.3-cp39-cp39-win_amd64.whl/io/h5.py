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
        lysci__ufy = self._get_h5_type(lhs, rhs)
        if lysci__ufy is not None:
            mxdb__ioa = str(lysci__ufy.dtype)
            fpmy__rbzmo = 'def _h5_read_impl(dset, index):\n'
            fpmy__rbzmo += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(lysci__ufy.ndim, mxdb__ioa))
            yzpuw__zcq = {}
            exec(fpmy__rbzmo, {}, yzpuw__zcq)
            iqhpp__auixr = yzpuw__zcq['_h5_read_impl']
            pmk__zgtak = compile_to_numba_ir(iqhpp__auixr, {'bodo': bodo}
                ).blocks.popitem()[1]
            rmt__zkf = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(pmk__zgtak, [rhs.value, rmt__zkf])
            nzlu__ycmc = pmk__zgtak.body[:-3]
            nzlu__ycmc[-1].target = assign.target
            return nzlu__ycmc
        return None

    def _get_h5_type(self, lhs, rhs):
        lysci__ufy = self._get_h5_type_locals(lhs)
        if lysci__ufy is not None:
            return lysci__ufy
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        rmt__zkf = rhs.index if rhs.op == 'getitem' else rhs.index_var
        safkg__eugh = guard(find_const, self.func_ir, rmt__zkf)
        require(not isinstance(safkg__eugh, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            gcbz__xwi = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            yyqki__knb = get_const_value_inner(self.func_ir, gcbz__xwi,
                arg_types=self.arg_types)
            obj_name_list.append(yyqki__knb)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        phkr__cxqt = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        ernqc__ddn = h5py.File(phkr__cxqt, 'r')
        khvvl__ija = ernqc__ddn
        for yyqki__knb in obj_name_list:
            khvvl__ija = khvvl__ija[yyqki__knb]
        require(isinstance(khvvl__ija, h5py.Dataset))
        iege__srvh = len(khvvl__ija.shape)
        amslu__hci = numba.np.numpy_support.from_dtype(khvvl__ija.dtype)
        ernqc__ddn.close()
        return types.Array(amslu__hci, iege__srvh, 'C')

    def _get_h5_type_locals(self, varname):
        eogl__askwf = self.locals.pop(varname, None)
        if eogl__askwf is None and varname is not None:
            eogl__askwf = self.flags.h5_types.get(varname, None)
        return eogl__askwf
