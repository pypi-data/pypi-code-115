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
        xhp__ecx = self._get_h5_type(lhs, rhs)
        if xhp__ecx is not None:
            dnmu__ovimn = str(xhp__ecx.dtype)
            cnr__yyu = 'def _h5_read_impl(dset, index):\n'
            cnr__yyu += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(xhp__ecx.ndim, dnmu__ovimn))
            sgpc__izok = {}
            exec(cnr__yyu, {}, sgpc__izok)
            dnu__cxk = sgpc__izok['_h5_read_impl']
            vvns__svj = compile_to_numba_ir(dnu__cxk, {'bodo': bodo}
                ).blocks.popitem()[1]
            ryrdm__ahzy = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(vvns__svj, [rhs.value, ryrdm__ahzy])
            kejzv__zmld = vvns__svj.body[:-3]
            kejzv__zmld[-1].target = assign.target
            return kejzv__zmld
        return None

    def _get_h5_type(self, lhs, rhs):
        xhp__ecx = self._get_h5_type_locals(lhs)
        if xhp__ecx is not None:
            return xhp__ecx
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        ryrdm__ahzy = rhs.index if rhs.op == 'getitem' else rhs.index_var
        fzu__myhi = guard(find_const, self.func_ir, ryrdm__ahzy)
        require(not isinstance(fzu__myhi, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            qixuz__bdq = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            xqk__lxy = get_const_value_inner(self.func_ir, qixuz__bdq,
                arg_types=self.arg_types)
            obj_name_list.append(xqk__lxy)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        pzbnl__ijadn = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        itfgo__pdl = h5py.File(pzbnl__ijadn, 'r')
        qscsx__grzw = itfgo__pdl
        for xqk__lxy in obj_name_list:
            qscsx__grzw = qscsx__grzw[xqk__lxy]
        require(isinstance(qscsx__grzw, h5py.Dataset))
        zbqxa__firyh = len(qscsx__grzw.shape)
        kvlkw__gjce = numba.np.numpy_support.from_dtype(qscsx__grzw.dtype)
        itfgo__pdl.close()
        return types.Array(kvlkw__gjce, zbqxa__firyh, 'C')

    def _get_h5_type_locals(self, varname):
        vyh__mfivf = self.locals.pop(varname, None)
        if vyh__mfivf is None and varname is not None:
            vyh__mfivf = self.flags.h5_types.get(varname, None)
        return vyh__mfivf
