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
        fux__fpow = self._get_h5_type(lhs, rhs)
        if fux__fpow is not None:
            tflkn__oezk = str(fux__fpow.dtype)
            kzw__lcq = 'def _h5_read_impl(dset, index):\n'
            kzw__lcq += (
                "  arr = bodo.io.h5_api.h5_read_dummy(dset, {}, '{}', index)\n"
                .format(fux__fpow.ndim, tflkn__oezk))
            qrvyf__zgz = {}
            exec(kzw__lcq, {}, qrvyf__zgz)
            pjog__zjvlo = qrvyf__zgz['_h5_read_impl']
            tlcue__dxk = compile_to_numba_ir(pjog__zjvlo, {'bodo': bodo}
                ).blocks.popitem()[1]
            xivit__alvd = rhs.index if rhs.op == 'getitem' else rhs.index_var
            replace_arg_nodes(tlcue__dxk, [rhs.value, xivit__alvd])
            grtuu__mhq = tlcue__dxk.body[:-3]
            grtuu__mhq[-1].target = assign.target
            return grtuu__mhq
        return None

    def _get_h5_type(self, lhs, rhs):
        fux__fpow = self._get_h5_type_locals(lhs)
        if fux__fpow is not None:
            return fux__fpow
        return guard(self._infer_h5_typ, rhs)

    def _infer_h5_typ(self, rhs):
        require(rhs.op in ('getitem', 'static_getitem'))
        xivit__alvd = rhs.index if rhs.op == 'getitem' else rhs.index_var
        elqdw__snj = guard(find_const, self.func_ir, xivit__alvd)
        require(not isinstance(elqdw__snj, str))
        val_def = rhs
        obj_name_list = []
        while True:
            val_def = get_definition(self.func_ir, val_def.value)
            require(isinstance(val_def, ir.Expr))
            if val_def.op == 'call':
                return self._get_h5_type_file(val_def, obj_name_list)
            require(val_def.op in ('getitem', 'static_getitem'))
            qhn__nzkzt = (val_def.index if val_def.op == 'getitem' else
                val_def.index_var)
            ekhe__ear = get_const_value_inner(self.func_ir, qhn__nzkzt,
                arg_types=self.arg_types)
            obj_name_list.append(ekhe__ear)

    def _get_h5_type_file(self, val_def, obj_name_list):
        require(len(obj_name_list) > 0)
        require(find_callname(self.func_ir, val_def) == ('File', 'h5py'))
        require(len(val_def.args) > 0)
        gcxxe__zvis = get_const_value_inner(self.func_ir, val_def.args[0],
            arg_types=self.arg_types)
        obj_name_list.reverse()
        import h5py
        pra__kxgo = h5py.File(gcxxe__zvis, 'r')
        hhp__hip = pra__kxgo
        for ekhe__ear in obj_name_list:
            hhp__hip = hhp__hip[ekhe__ear]
        require(isinstance(hhp__hip, h5py.Dataset))
        ziep__ksb = len(hhp__hip.shape)
        dqns__agz = numba.np.numpy_support.from_dtype(hhp__hip.dtype)
        pra__kxgo.close()
        return types.Array(dqns__agz, ziep__ksb, 'C')

    def _get_h5_type_locals(self, varname):
        ezkua__ixi = self.locals.pop(varname, None)
        if ezkua__ixi is None and varname is not None:
            ezkua__ixi = self.flags.h5_types.get(varname, None)
        return ezkua__ixi
