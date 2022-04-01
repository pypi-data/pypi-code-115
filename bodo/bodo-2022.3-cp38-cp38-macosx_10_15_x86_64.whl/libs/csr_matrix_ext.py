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
        ajuuv__fxgnb = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, ajuuv__fxgnb)


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
        jnbq__xievv, rvf__qygy, ilmi__idjsv, qzxxk__qqc = args
        baxr__nyazg = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        baxr__nyazg.data = jnbq__xievv
        baxr__nyazg.indices = rvf__qygy
        baxr__nyazg.indptr = ilmi__idjsv
        baxr__nyazg.shape = qzxxk__qqc
        context.nrt.incref(builder, signature.args[0], jnbq__xievv)
        context.nrt.incref(builder, signature.args[1], rvf__qygy)
        context.nrt.incref(builder, signature.args[2], ilmi__idjsv)
        return baxr__nyazg._getvalue()
    vlmw__vzfyl = CSRMatrixType(data_t.dtype, indices_t.dtype)
    wpkp__cmaav = vlmw__vzfyl(data_t, indices_t, indptr_t, types.UniTuple(
        types.int64, 2))
    return wpkp__cmaav, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    baxr__nyazg = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    maslp__eju = c.pyapi.object_getattr_string(val, 'data')
    ndgoc__zsgsz = c.pyapi.object_getattr_string(val, 'indices')
    reief__qkpws = c.pyapi.object_getattr_string(val, 'indptr')
    ronur__meggn = c.pyapi.object_getattr_string(val, 'shape')
    baxr__nyazg.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1,
        'C'), maslp__eju).value
    baxr__nyazg.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype,
        1, 'C'), ndgoc__zsgsz).value
    baxr__nyazg.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype,
        1, 'C'), reief__qkpws).value
    baxr__nyazg.shape = c.pyapi.to_native_value(types.UniTuple(types.int64,
        2), ronur__meggn).value
    c.pyapi.decref(maslp__eju)
    c.pyapi.decref(ndgoc__zsgsz)
    c.pyapi.decref(reief__qkpws)
    c.pyapi.decref(ronur__meggn)
    ilbw__omvr = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(baxr__nyazg._getvalue(), is_error=ilbw__omvr)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    zcq__sme = c.context.insert_const_string(c.builder.module, 'scipy.sparse')
    aidw__glev = c.pyapi.import_module_noblock(zcq__sme)
    baxr__nyazg = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        baxr__nyazg.data)
    maslp__eju = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        baxr__nyazg.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        baxr__nyazg.indices)
    ndgoc__zsgsz = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), baxr__nyazg.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        baxr__nyazg.indptr)
    reief__qkpws = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), baxr__nyazg.indptr, c.env_manager)
    ronur__meggn = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        baxr__nyazg.shape, c.env_manager)
    ybm__fgbjn = c.pyapi.tuple_pack([maslp__eju, ndgoc__zsgsz, reief__qkpws])
    badw__rto = c.pyapi.call_method(aidw__glev, 'csr_matrix', (ybm__fgbjn,
        ronur__meggn))
    c.pyapi.decref(ybm__fgbjn)
    c.pyapi.decref(maslp__eju)
    c.pyapi.decref(ndgoc__zsgsz)
    c.pyapi.decref(reief__qkpws)
    c.pyapi.decref(ronur__meggn)
    c.pyapi.decref(aidw__glev)
    c.context.nrt.decref(c.builder, typ, val)
    return badw__rto


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
    iabo__aroz = A.dtype
    noc__ofhtj = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            pwg__jkxw, jggxf__urlkh = A.shape
            dzkvi__lwli = numba.cpython.unicode._normalize_slice(idx[0],
                pwg__jkxw)
            esvzi__lfdqk = numba.cpython.unicode._normalize_slice(idx[1],
                jggxf__urlkh)
            if dzkvi__lwli.step != 1 or esvzi__lfdqk.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            tpfk__fes = dzkvi__lwli.start
            zzpu__wmzp = dzkvi__lwli.stop
            yjg__zkmw = esvzi__lfdqk.start
            mvghc__hwjd = esvzi__lfdqk.stop
            nwp__qfy = A.indptr
            wnq__ctx = A.indices
            kdjgd__ety = A.data
            tbzzo__jusd = zzpu__wmzp - tpfk__fes
            xox__mckc = mvghc__hwjd - yjg__zkmw
            wqj__ikp = 0
            tiffg__qxuz = 0
            for wojx__nlmjl in range(tbzzo__jusd):
                mpl__qicxc = nwp__qfy[tpfk__fes + wojx__nlmjl]
                hfq__erh = nwp__qfy[tpfk__fes + wojx__nlmjl + 1]
                for lpx__rex in range(mpl__qicxc, hfq__erh):
                    if wnq__ctx[lpx__rex] >= yjg__zkmw and wnq__ctx[lpx__rex
                        ] < mvghc__hwjd:
                        wqj__ikp += 1
            dqlbp__xdq = np.empty(tbzzo__jusd + 1, noc__ofhtj)
            sqmnp__kux = np.empty(wqj__ikp, noc__ofhtj)
            xnk__bzi = np.empty(wqj__ikp, iabo__aroz)
            dqlbp__xdq[0] = 0
            for wojx__nlmjl in range(tbzzo__jusd):
                mpl__qicxc = nwp__qfy[tpfk__fes + wojx__nlmjl]
                hfq__erh = nwp__qfy[tpfk__fes + wojx__nlmjl + 1]
                for lpx__rex in range(mpl__qicxc, hfq__erh):
                    if wnq__ctx[lpx__rex] >= yjg__zkmw and wnq__ctx[lpx__rex
                        ] < mvghc__hwjd:
                        sqmnp__kux[tiffg__qxuz] = wnq__ctx[lpx__rex
                            ] - yjg__zkmw
                        xnk__bzi[tiffg__qxuz] = kdjgd__ety[lpx__rex]
                        tiffg__qxuz += 1
                dqlbp__xdq[wojx__nlmjl + 1] = tiffg__qxuz
            return init_csr_matrix(xnk__bzi, sqmnp__kux, dqlbp__xdq, (
                tbzzo__jusd, xox__mckc))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
