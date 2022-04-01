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
        nbg__qeo = self._get_h5_type(lhs, rhs)
        if nbg__qeo is not None:
            dylro__kdv = str(nbg__qeo.dtype)
            xzwrw__nmwx = 'def _h5_read_impl(dset, index):\n'
            xzwrw__nmwx += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(nbg__qeo.ndim, dylro__kdv))
            jvvv__aly = {}
            exec(xzwrw__nmwx, {}, jvvv__aly)
            qxpe__okeo = jvvv__aly['_h5_read_impl']
            ythyo__ytxo = compile_to_numba_ir(qxpe__okeo, {'bodo': bodo}
                ).blocks.popitem()[1]
            odxg__hjuc = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(ythyo__ytxo, [rhs.value, odxg__hjuc])
            xvx__gaa = ythyo__ytxo.body[:-3]
            xvx__gaa[-1].target = assign.target
            return xvx__gaa
        return None

    def _get_h5_type(self, lhs, rhs):
        nbg__qeo = self._get_h5_type_locals(lhs)
        if nbg__qeo is not None:
            return nbg__qeo
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        odxg__hjuc = rhs.index if rhs.op == 'getitem' else rhs.index_var
        zmqqu__rqwy = guard(find_const, self.func_ir, odxg__hjuc)
        require(not isinstance(zmqqu__rqwy, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            etz__vig = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            hzb__lumey = get_const_value_inner(self.func_ir, etz__vig,
                arg_types=self.arg_types)
            obj_name_list.append(hzb__lumey)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        wsqlq__htzmi = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        rakrs__sumwn = h5py.File(wsqlq__htzmi, 'r')
        fnh__mstgc = rakrs__sumwn
        for hzb__lumey in obj_name_list:
            fnh__mstgc = fnh__mstgc[hzb__lumey]
        require(isinstance(fnh__mstgc, h5py.Dataset))
        bshhw__mdfnz = len(fnh__mstgc.shape)
        onjo__wpuxq = numba.np.numpy_support.from_dtype(fnh__mstgc.dtype)
        rakrs__sumwn.close()
        return types.Array(onjo__wpuxq, bshhw__mdfnz, 'C')

    def _get_h5_type_locals(self, varname):
        fnsfx__wyxl = self.locals.pop(varname, None)
        if fnsfx__wyxl is None and varname is not None:
            fnsfx__wyxl = self.flags.h5_types.get(varname, None)
        return fnsfx__wyxl
