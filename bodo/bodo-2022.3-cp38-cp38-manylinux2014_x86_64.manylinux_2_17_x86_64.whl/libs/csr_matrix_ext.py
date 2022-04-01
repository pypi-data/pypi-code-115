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
        eykem__herht = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, eykem__herht)


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
        lpv__ourm, nzpb__ijj, flwz__bshw, rah__ieox = args
        tbvr__wlq = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        tbvr__wlq.data = lpv__ourm
        tbvr__wlq.indices = nzpb__ijj
        tbvr__wlq.indptr = flwz__bshw
        tbvr__wlq.shape = rah__ieox
        context.nrt.incref(builder, signature.args[0], lpv__ourm)
        context.nrt.incref(builder, signature.args[1], nzpb__ijj)
        context.nrt.incref(builder, signature.args[2], flwz__bshw)
        return tbvr__wlq._getvalue()
    yitb__jeoud = CSRMatrixType(data_t.dtype, indices_t.dtype)
    uvxu__qfv = yitb__jeoud(data_t, indices_t, indptr_t, types.UniTuple(
        types.int64, 2))
    return uvxu__qfv, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    tbvr__wlq = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    adpvt__mhh = c.pyapi.object_getattr_string(val, 'data')
    smbc__kud = c.pyapi.object_getattr_string(val, 'indices')
    wscse__ybuqi = c.pyapi.object_getattr_string(val, 'indptr')
    ziyeo__ycvsc = c.pyapi.object_getattr_string(val, 'shape')
    tbvr__wlq.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1, 'C'),
        adpvt__mhh).value
    tbvr__wlq.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 
        1, 'C'), smbc__kud).value
    tbvr__wlq.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), wscse__ybuqi).value
    tbvr__wlq.shape = c.pyapi.to_native_value(types.UniTuple(types.int64, 2
        ), ziyeo__ycvsc).value
    c.pyapi.decref(adpvt__mhh)
    c.pyapi.decref(smbc__kud)
    c.pyapi.decref(wscse__ybuqi)
    c.pyapi.decref(ziyeo__ycvsc)
    yktb__rfcou = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(tbvr__wlq._getvalue(), is_error=yktb__rfcou)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    rhrp__pfeds = c.context.insert_const_string(c.builder.module,
        'scipy.sparse')
    xfe__fhoj = c.pyapi.import_module_noblock(rhrp__pfeds)
    tbvr__wlq = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        tbvr__wlq.data)
    adpvt__mhh = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        tbvr__wlq.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        tbvr__wlq.indices)
    smbc__kud = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1, 'C'
        ), tbvr__wlq.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        tbvr__wlq.indptr)
    wscse__ybuqi = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), tbvr__wlq.indptr, c.env_manager)
    ziyeo__ycvsc = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        tbvr__wlq.shape, c.env_manager)
    qzij__xoawd = c.pyapi.tuple_pack([adpvt__mhh, smbc__kud, wscse__ybuqi])
    yquua__gab = c.pyapi.call_method(xfe__fhoj, 'csr_matrix', (qzij__xoawd,
        ziyeo__ycvsc))
    c.pyapi.decref(qzij__xoawd)
    c.pyapi.decref(adpvt__mhh)
    c.pyapi.decref(smbc__kud)
    c.pyapi.decref(wscse__ybuqi)
    c.pyapi.decref(ziyeo__ycvsc)
    c.pyapi.decref(xfe__fhoj)
    c.context.nrt.decref(c.builder, typ, val)
    return yquua__gab


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
    tbdmw__yoysw = A.dtype
    qyjai__pqj = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            tau__zknl, smqvt__cig = A.shape
            ybb__kwoiw = numba.cpython.unicode._normalize_slice(idx[0],
                tau__zknl)
            uksmc__fpo = numba.cpython.unicode._normalize_slice(idx[1],
                smqvt__cig)
            if ybb__kwoiw.step != 1 or uksmc__fpo.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            bee__jyql = ybb__kwoiw.start
            jyjx__iogh = ybb__kwoiw.stop
            vpvk__zyk = uksmc__fpo.start
            onuae__csx = uksmc__fpo.stop
            msx__uuxmk = A.indptr
            kkkvh__act = A.indices
            rik__inri = A.data
            pzvo__twkh = jyjx__iogh - bee__jyql
            szn__owf = onuae__csx - vpvk__zyk
            fniea__pzna = 0
            tpgo__zfx = 0
            for ofil__zvg in range(pzvo__twkh):
                hbl__uzu = msx__uuxmk[bee__jyql + ofil__zvg]
                esj__cqgbr = msx__uuxmk[bee__jyql + ofil__zvg + 1]
                for nne__pmnqi in range(hbl__uzu, esj__cqgbr):
                    if kkkvh__act[nne__pmnqi] >= vpvk__zyk and kkkvh__act[
                        nne__pmnqi] < onuae__csx:
                        fniea__pzna += 1
            cbptu__afc = np.empty(pzvo__twkh + 1, qyjai__pqj)
            ofxd__zcwj = np.empty(fniea__pzna, qyjai__pqj)
            vuu__wzj = np.empty(fniea__pzna, tbdmw__yoysw)
            cbptu__afc[0] = 0
            for ofil__zvg in range(pzvo__twkh):
                hbl__uzu = msx__uuxmk[bee__jyql + ofil__zvg]
                esj__cqgbr = msx__uuxmk[bee__jyql + ofil__zvg + 1]
                for nne__pmnqi in range(hbl__uzu, esj__cqgbr):
                    if kkkvh__act[nne__pmnqi] >= vpvk__zyk and kkkvh__act[
                        nne__pmnqi] < onuae__csx:
                        ofxd__zcwj[tpgo__zfx] = kkkvh__act[nne__pmnqi
                            ] - vpvk__zyk
                        vuu__wzj[tpgo__zfx] = rik__inri[nne__pmnqi]
                        tpgo__zfx += 1
                cbptu__afc[ofil__zvg + 1] = tpgo__zfx
            return init_csr_matrix(vuu__wzj, ofxd__zcwj, cbptu__afc, (
                pzvo__twkh, szn__owf))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
