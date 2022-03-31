"""CSR Matrix data type implementation for scipy.sparse.csr_matrix
"""
import operator
import numba
import numpy as np
from numba.core import cgutils, types
from numba.extending import NativeValue, box, intrinsic, make_attribute_wrapper, models, overload, overload_attribute, overload_method, register_model, typeof_impl, unbox
import bodo
from bodo.utils.typing import BodoError


class CSRMatrixType(types.ArrayCompatible):
    ndim = 2

    def __init__(self, dtype, idx_dtype):
        self.dtype = dtype
        self.idx_dtype = idx_dtype
        super(CSRMatrixType, self).__init__(name=
            f'CSRMatrixType({dtype}, {idx_dtype})')

    @property
    def as_array(self):
        return types.Array(types.undefined, 2, 'C')

    def copy(self):
        return CSRMatrixType(self.dtype, self.idx_dtype)


@register_model(CSRMatrixType)
class CSRMatrixModel(models.StructModel):

    def __init__(self, dmm, fe_type):
        wnnr__pfift = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, wnnr__pfift)


make_attribute_wrapper(CSRMatrixType, 'data', 'data')
make_attribute_wrapper(CSRMatrixType, 'indices', 'indices')
make_attribute_wrapper(CSRMatrixType, 'indptr', 'indptr')
make_attribute_wrapper(CSRMatrixType, 'shape', 'shape')


@intrinsic
def init_csr_matrix(typingctx, data_t, indices_t, indptr_t, shape_t=None):
    assert isinstance(data_t, types.Array)
    assert isinstance(indices_t, types.Array) and isinstance(indices_t.
        dtype, types.Integer)
    assert indices_t == indptr_t

    def codegen(context, builder, signature, args):
        tjut__ecjym, xdlrr__swhao, bcox__brnb, obxxg__syx = args
        arg__kcz = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        arg__kcz.data = tjut__ecjym
        arg__kcz.indices = xdlrr__swhao
        arg__kcz.indptr = bcox__brnb
        arg__kcz.shape = obxxg__syx
        context.nrt.incref(builder, signature.args[0], tjut__ecjym)
        context.nrt.incref(builder, signature.args[1], xdlrr__swhao)
        context.nrt.incref(builder, signature.args[2], bcox__brnb)
        return arg__kcz._getvalue()
    pcd__lukmg = CSRMatrixType(data_t.dtype, indices_t.dtype)
    dlu__wyx = pcd__lukmg(data_t, indices_t, indptr_t, types.UniTuple(types
        .int64, 2))
    return dlu__wyx, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    arg__kcz = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    wyta__omu = c.pyapi.object_getattr_string(val, 'data')
    jjvl__cjkki = c.pyapi.object_getattr_string(val, 'indices')
    pggy__bkf = c.pyapi.object_getattr_string(val, 'indptr')
    lbhj__zaaj = c.pyapi.object_getattr_string(val, 'shape')
    arg__kcz.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1, 'C'),
        wyta__omu).value
    arg__kcz.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), jjvl__cjkki).value
    arg__kcz.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), pggy__bkf).value
    arg__kcz.shape = c.pyapi.to_native_value(types.UniTuple(types.int64, 2),
        lbhj__zaaj).value
    c.pyapi.decref(wyta__omu)
    c.pyapi.decref(jjvl__cjkki)
    c.pyapi.decref(pggy__bkf)
    c.pyapi.decref(lbhj__zaaj)
    eff__jmd = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(arg__kcz._getvalue(), is_error=eff__jmd)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    ydth__kslr = c.context.insert_const_string(c.builder.module, 'scipy.sparse'
        )
    cluqn__edxd = c.pyapi.import_module_noblock(ydth__kslr)
    arg__kcz = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        arg__kcz.data)
    wyta__omu = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        arg__kcz.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        arg__kcz.indices)
    jjvl__cjkki = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), arg__kcz.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        arg__kcz.indptr)
    pggy__bkf = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1, 'C'
        ), arg__kcz.indptr, c.env_manager)
    lbhj__zaaj = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        arg__kcz.shape, c.env_manager)
    pdevf__ilqqs = c.pyapi.tuple_pack([wyta__omu, jjvl__cjkki, pggy__bkf])
    vbnh__biw = c.pyapi.call_method(cluqn__edxd, 'csr_matrix', (
        pdevf__ilqqs, lbhj__zaaj))
    c.pyapi.decref(pdevf__ilqqs)
    c.pyapi.decref(wyta__omu)
    c.pyapi.decref(jjvl__cjkki)
    c.pyapi.decref(pggy__bkf)
    c.pyapi.decref(lbhj__zaaj)
    c.pyapi.decref(cluqn__edxd)
    c.context.nrt.decref(c.builder, typ, val)
    return vbnh__biw


@overload(len, no_unliteral=True)
def overload_csr_matrix_len(A):
    if isinstance(A, CSRMatrixType):
        return lambda A: A.shape[0]


@overload_attribute(CSRMatrixType, 'ndim')
def overload_csr_matrix_ndim(A):
    return lambda A: 2


@overload_method(CSRMatrixType, 'copy', no_unliteral=True)
def overload_csr_matrix_copy(A):

    def copy_impl(A):
        return init_csr_matrix(A.data.copy(), A.indices.copy(), A.indptr.
            copy(), A.shape)
    return copy_impl


@overload(operator.getitem, no_unliteral=True)
def csr_matrix_getitem(A, idx):
    if not isinstance(A, CSRMatrixType):
        return
    xlh__psfg = A.dtype
    yvdd__egv = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            txs__cdmqx, ntnns__dtmuf = A.shape
            nkhau__pps = numba.cpython.unicode._normalize_slice(idx[0],
                txs__cdmqx)
            ynlii__ugiwh = numba.cpython.unicode._normalize_slice(idx[1],
                ntnns__dtmuf)
            if nkhau__pps.step != 1 or ynlii__ugiwh.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            irc__wafcm = nkhau__pps.start
            lvzsh__pdrhp = nkhau__pps.stop
            zpjym__mhs = ynlii__ugiwh.start
            lkqv__ulwrl = ynlii__ugiwh.stop
            qllkd__hbg = A.indptr
            otmvq__jan = A.indices
            cfo__woa = A.data
            cfhaz__zxya = lvzsh__pdrhp - irc__wafcm
            swox__sugy = lkqv__ulwrl - zpjym__mhs
            cyfj__fgs = 0
            fkpt__kgco = 0
            for mmm__hbtdm in range(cfhaz__zxya):
                tbmr__jqozv = qllkd__hbg[irc__wafcm + mmm__hbtdm]
                athk__ull = qllkd__hbg[irc__wafcm + mmm__hbtdm + 1]
                for trrd__mgjca in range(tbmr__jqozv, athk__ull):
                    if otmvq__jan[trrd__mgjca] >= zpjym__mhs and otmvq__jan[
                        trrd__mgjca] < lkqv__ulwrl:
                        cyfj__fgs += 1
            wjk__ydx = np.empty(cfhaz__zxya + 1, yvdd__egv)
            tcnac__fcsqe = np.empty(cyfj__fgs, yvdd__egv)
            dwknq__wmzu = np.empty(cyfj__fgs, xlh__psfg)
            wjk__ydx[0] = 0
            for mmm__hbtdm in range(cfhaz__zxya):
                tbmr__jqozv = qllkd__hbg[irc__wafcm + mmm__hbtdm]
                athk__ull = qllkd__hbg[irc__wafcm + mmm__hbtdm + 1]
                for trrd__mgjca in range(tbmr__jqozv, athk__ull):
                    if otmvq__jan[trrd__mgjca] >= zpjym__mhs and otmvq__jan[
                        trrd__mgjca] < lkqv__ulwrl:
                        tcnac__fcsqe[fkpt__kgco] = otmvq__jan[trrd__mgjca
                            ] - zpjym__mhs
                        dwknq__wmzu[fkpt__kgco] = cfo__woa[trrd__mgjca]
                        fkpt__kgco += 1
                wjk__ydx[mmm__hbtdm + 1] = fkpt__kgco
            return init_csr_matrix(dwknq__wmzu, tcnac__fcsqe, wjk__ydx, (
                cfhaz__zxya, swox__sugy))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
