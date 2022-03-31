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
        jxmd__nhzgf = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, jxmd__nhzgf)


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
        lpql__rih, pxs__wmuck, kauh__ogiql, opmz__jdgoo = args
        hfv__bic = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        hfv__bic.data = lpql__rih
        hfv__bic.indices = pxs__wmuck
        hfv__bic.indptr = kauh__ogiql
        hfv__bic.shape = opmz__jdgoo
        context.nrt.incref(builder, signature.args[0], lpql__rih)
        context.nrt.incref(builder, signature.args[1], pxs__wmuck)
        context.nrt.incref(builder, signature.args[2], kauh__ogiql)
        return hfv__bic._getvalue()
    znkdh__rglf = CSRMatrixType(data_t.dtype, indices_t.dtype)
    icsn__rnrg = znkdh__rglf(data_t, indices_t, indptr_t, types.UniTuple(
        types.int64, 2))
    return icsn__rnrg, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    hfv__bic = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    owy__pciv = c.pyapi.object_getattr_string(val, 'data')
    ibt__rqypd = c.pyapi.object_getattr_string(val, 'indices')
    jqq__hvc = c.pyapi.object_getattr_string(val, 'indptr')
    pzych__eiti = c.pyapi.object_getattr_string(val, 'shape')
    hfv__bic.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1, 'C'),
        owy__pciv).value
    hfv__bic.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), ibt__rqypd).value
    hfv__bic.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), jqq__hvc).value
    hfv__bic.shape = c.pyapi.to_native_value(types.UniTuple(types.int64, 2),
        pzych__eiti).value
    c.pyapi.decref(owy__pciv)
    c.pyapi.decref(ibt__rqypd)
    c.pyapi.decref(jqq__hvc)
    c.pyapi.decref(pzych__eiti)
    jzv__pqgtj = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(hfv__bic._getvalue(), is_error=jzv__pqgtj)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    ccx__vnso = c.context.insert_const_string(c.builder.module, 'scipy.sparse')
    kiinv__rtuy = c.pyapi.import_module_noblock(ccx__vnso)
    hfv__bic = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        hfv__bic.data)
    owy__pciv = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        hfv__bic.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        hfv__bic.indices)
    ibt__rqypd = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), hfv__bic.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        hfv__bic.indptr)
    jqq__hvc = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1, 'C'),
        hfv__bic.indptr, c.env_manager)
    pzych__eiti = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        hfv__bic.shape, c.env_manager)
    zqded__uubuh = c.pyapi.tuple_pack([owy__pciv, ibt__rqypd, jqq__hvc])
    hfb__lpegf = c.pyapi.call_method(kiinv__rtuy, 'csr_matrix', (
        zqded__uubuh, pzych__eiti))
    c.pyapi.decref(zqded__uubuh)
    c.pyapi.decref(owy__pciv)
    c.pyapi.decref(ibt__rqypd)
    c.pyapi.decref(jqq__hvc)
    c.pyapi.decref(pzych__eiti)
    c.pyapi.decref(kiinv__rtuy)
    c.context.nrt.decref(c.builder, typ, val)
    return hfb__lpegf


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
    tmrbl__wkwl = A.dtype
    yftd__hwg = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            agcf__pkfh, dyciq__ukv = A.shape
            teb__fdpy = numba.cpython.unicode._normalize_slice(idx[0],
                agcf__pkfh)
            xlkpd__qsw = numba.cpython.unicode._normalize_slice(idx[1],
                dyciq__ukv)
            if teb__fdpy.step != 1 or xlkpd__qsw.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            omwq__orr = teb__fdpy.start
            uljv__jze = teb__fdpy.stop
            bec__hsghr = xlkpd__qsw.start
            ycq__rnps = xlkpd__qsw.stop
            dhzj__dsd = A.indptr
            kue__jmdij = A.indices
            qtw__gjx = A.data
            hmri__rrzyo = uljv__jze - omwq__orr
            vsrj__jgm = ycq__rnps - bec__hsghr
            hhnld__ccc = 0
            ykx__znumo = 0
            for fdkll__xnegg in range(hmri__rrzyo):
                lclcl__mth = dhzj__dsd[omwq__orr + fdkll__xnegg]
                wybjd__lab = dhzj__dsd[omwq__orr + fdkll__xnegg + 1]
                for ivsbd__atnz in range(lclcl__mth, wybjd__lab):
                    if kue__jmdij[ivsbd__atnz] >= bec__hsghr and kue__jmdij[
                        ivsbd__atnz] < ycq__rnps:
                        hhnld__ccc += 1
            yavx__zpc = np.empty(hmri__rrzyo + 1, yftd__hwg)
            aoqrf__kyw = np.empty(hhnld__ccc, yftd__hwg)
            xme__bnhvd = np.empty(hhnld__ccc, tmrbl__wkwl)
            yavx__zpc[0] = 0
            for fdkll__xnegg in range(hmri__rrzyo):
                lclcl__mth = dhzj__dsd[omwq__orr + fdkll__xnegg]
                wybjd__lab = dhzj__dsd[omwq__orr + fdkll__xnegg + 1]
                for ivsbd__atnz in range(lclcl__mth, wybjd__lab):
                    if kue__jmdij[ivsbd__atnz] >= bec__hsghr and kue__jmdij[
                        ivsbd__atnz] < ycq__rnps:
                        aoqrf__kyw[ykx__znumo] = kue__jmdij[ivsbd__atnz
                            ] - bec__hsghr
                        xme__bnhvd[ykx__znumo] = qtw__gjx[ivsbd__atnz]
                        ykx__znumo += 1
                yavx__zpc[fdkll__xnegg + 1] = ykx__znumo
            return init_csr_matrix(xme__bnhvd, aoqrf__kyw, yavx__zpc, (
                hmri__rrzyo, vsrj__jgm))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
