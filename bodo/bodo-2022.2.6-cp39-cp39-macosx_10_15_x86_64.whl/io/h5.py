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
        nqaor__pinw = self._get_h5_type(lhs, rhs)
        if nqaor__pinw is not None:
            uht__irf = str(nqaor__pinw.dtype)
            jqzq__lug = 'def _h5_read_impl(dset, index):\n'
            jqzq__lug += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(nqaor__pinw.ndim, uht__irf))
            zgj__zcuz = {}
            exec(jqzq__lug, {}, zgj__zcuz)
            bni__askvt = zgj__zcuz['_h5_read_impl']
            elkrs__hlihi = compile_to_numba_ir(bni__askvt, {'bodo': bodo}
                ).blocks.popitem()[1]
            vcgi__qqfqn = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(elkrs__hlihi, [rhs.value, vcgi__qqfqn])
            qopf__unql = elkrs__hlihi.body[:-3]
            qopf__unql[-1].target = assign.target
            return qopf__unql
        return None

    def _get_h5_type(self, lhs, rhs):
        nqaor__pinw = self._get_h5_type_locals(lhs)
        if nqaor__pinw is not None:
            return nqaor__pinw
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        vcgi__qqfqn = rhs.index if rhs.op == 'getitem' else rhs.index_var
        xsvxk__sgvzp = guard(find_const, self.func_ir, vcgi__qqfqn)
        require(not isinstance(xsvxk__sgvzp, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            iiha__dkmk = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            xjfcu__gps = get_const_value_inner(self.func_ir, iiha__dkmk,
                arg_types=self.arg_types)
            obj_name_list.append(xjfcu__gps)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        cml__pdxlq = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        ubh__xsko = h5py.File(cml__pdxlq, 'r')
        ebnmq__zxau = ubh__xsko
        for xjfcu__gps in obj_name_list:
            ebnmq__zxau = ebnmq__zxau[xjfcu__gps]
        require(isinstance(ebnmq__zxau, h5py.Dataset))
        hawn__pacd = len(ebnmq__zxau.shape)
        ugefa__yfzx = numba.np.numpy_support.from_dtype(ebnmq__zxau.dtype)
        ubh__xsko.close()
        return types.Array(ugefa__yfzx, hawn__pacd, 'C')

    def _get_h5_type_locals(self, varname):
        khid__gjzu = self.locals.pop(varname, None)
        if khid__gjzu is None and varname is not None:
            khid__gjzu = self.flags.h5_types.get(varname, None)
        return khid__gjzu
