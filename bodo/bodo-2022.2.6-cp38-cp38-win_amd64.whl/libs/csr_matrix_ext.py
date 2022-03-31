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
        zpngn__jxa = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, zpngn__jxa)


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
        lxbw__iklx, znxn__evr, mplry__ybj, elyt__sym = args
        ruxy__jbhcf = cgutils.create_struct_proxy(signature.return_type)(
            context, builder)
        ruxy__jbhcf.data = lxbw__iklx
        ruxy__jbhcf.indices = znxn__evr
        ruxy__jbhcf.indptr = mplry__ybj
        ruxy__jbhcf.shape = elyt__sym
        context.nrt.incref(builder, signature.args[0], lxbw__iklx)
        context.nrt.incref(builder, signature.args[1], znxn__evr)
        context.nrt.incref(builder, signature.args[2], mplry__ybj)
        return ruxy__jbhcf._getvalue()
    ueepk__pte = CSRMatrixType(data_t.dtype, indices_t.dtype)
    wkdk__tomp = ueepk__pte(data_t, indices_t, indptr_t, types.UniTuple(
        types.int64, 2))
    return wkdk__tomp, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    ruxy__jbhcf = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    cbte__nhk = c.pyapi.object_getattr_string(val, 'data')
    rix__aveak = c.pyapi.object_getattr_string(val, 'indices')
    rngk__wfe = c.pyapi.object_getattr_string(val, 'indptr')
    xefq__xoxu = c.pyapi.object_getattr_string(val, 'shape')
    ruxy__jbhcf.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1,
        'C'), cbte__nhk).value
    ruxy__jbhcf.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype,
        1, 'C'), rix__aveak).value
    ruxy__jbhcf.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype,
        1, 'C'), rngk__wfe).value
    ruxy__jbhcf.shape = c.pyapi.to_native_value(types.UniTuple(types.int64,
        2), xefq__xoxu).value
    c.pyapi.decref(cbte__nhk)
    c.pyapi.decref(rix__aveak)
    c.pyapi.decref(rngk__wfe)
    c.pyapi.decref(xefq__xoxu)
    jvr__fvi = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(ruxy__jbhcf._getvalue(), is_error=jvr__fvi)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    jysu__herxn = c.context.insert_const_string(c.builder.module,
        'scipy.sparse')
    xbhxm__tnrj = c.pyapi.import_module_noblock(jysu__herxn)
    ruxy__jbhcf = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        ruxy__jbhcf.data)
    cbte__nhk = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        ruxy__jbhcf.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        ruxy__jbhcf.indices)
    rix__aveak = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), ruxy__jbhcf.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        ruxy__jbhcf.indptr)
    rngk__wfe = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1, 'C'
        ), ruxy__jbhcf.indptr, c.env_manager)
    xefq__xoxu = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        ruxy__jbhcf.shape, c.env_manager)
    myh__kzkf = c.pyapi.tuple_pack([cbte__nhk, rix__aveak, rngk__wfe])
    xbbzo__hneu = c.pyapi.call_method(xbhxm__tnrj, 'csr_matrix', (myh__kzkf,
        xefq__xoxu))
    c.pyapi.decref(myh__kzkf)
    c.pyapi.decref(cbte__nhk)
    c.pyapi.decref(rix__aveak)
    c.pyapi.decref(rngk__wfe)
    c.pyapi.decref(xefq__xoxu)
    c.pyapi.decref(xbhxm__tnrj)
    c.context.nrt.decref(c.builder, typ, val)
    return xbbzo__hneu


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
    ykg__clc = A.dtype
    qnozf__qgviq = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            zlb__xoml, bhw__ygm = A.shape
            mtin__zism = numba.cpython.unicode._normalize_slice(idx[0],
                zlb__xoml)
            jvgc__kgqw = numba.cpython.unicode._normalize_slice(idx[1],
                bhw__ygm)
            if mtin__zism.step != 1 or jvgc__kgqw.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            eoal__stq = mtin__zism.start
            ssp__xemr = mtin__zism.stop
            njass__kbej = jvgc__kgqw.start
            mvq__ybgww = jvgc__kgqw.stop
            fovjm__xgrzt = A.indptr
            rahj__rulq = A.indices
            wfoav__djlr = A.data
            ikmo__tvuzy = ssp__xemr - eoal__stq
            lbt__ojeib = mvq__ybgww - njass__kbej
            ewddx__oza = 0
            xdac__hhbx = 0
            for yflbr__klhsv in range(ikmo__tvuzy):
                ylu__gghz = fovjm__xgrzt[eoal__stq + yflbr__klhsv]
                tdth__woyfo = fovjm__xgrzt[eoal__stq + yflbr__klhsv + 1]
                for qlf__xhxh in range(ylu__gghz, tdth__woyfo):
                    if rahj__rulq[qlf__xhxh] >= njass__kbej and rahj__rulq[
                        qlf__xhxh] < mvq__ybgww:
                        ewddx__oza += 1
            diwwe__flq = np.empty(ikmo__tvuzy + 1, qnozf__qgviq)
            xjarh__kjihd = np.empty(ewddx__oza, qnozf__qgviq)
            znb__fuk = np.empty(ewddx__oza, ykg__clc)
            diwwe__flq[0] = 0
            for yflbr__klhsv in range(ikmo__tvuzy):
                ylu__gghz = fovjm__xgrzt[eoal__stq + yflbr__klhsv]
                tdth__woyfo = fovjm__xgrzt[eoal__stq + yflbr__klhsv + 1]
                for qlf__xhxh in range(ylu__gghz, tdth__woyfo):
                    if rahj__rulq[qlf__xhxh] >= njass__kbej and rahj__rulq[
                        qlf__xhxh] < mvq__ybgww:
                        xjarh__kjihd[xdac__hhbx] = rahj__rulq[qlf__xhxh
                            ] - njass__kbej
                        znb__fuk[xdac__hhbx] = wfoav__djlr[qlf__xhxh]
                        xdac__hhbx += 1
                diwwe__flq[yflbr__klhsv + 1] = xdac__hhbx
            return init_csr_matrix(znb__fuk, xjarh__kjihd, diwwe__flq, (
                ikmo__tvuzy, lbt__ojeib))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
