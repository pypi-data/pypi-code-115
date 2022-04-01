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
        yhc__yewe = [('data', types.Array(fe_type.dtype, 1, 'C')), (
            'indices', types.Array(fe_type.idx_dtype, 1, 'C')), ('indptr',
            types.Array(fe_type.idx_dtype, 1, 'C')), ('shape', types.
            UniTuple(types.int64, 2))]
        models.StructModel.__init__(self, dmm, fe_type, yhc__yewe)


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
        xqjn__cln, mtp__ezcyk, hwhwt__lccxj, gmzt__bzasy = args
        edv__qtc = cgutils.create_struct_proxy(signature.return_type)(context,
            builder)
        edv__qtc.data = xqjn__cln
        edv__qtc.indices = mtp__ezcyk
        edv__qtc.indptr = hwhwt__lccxj
        edv__qtc.shape = gmzt__bzasy
        context.nrt.incref(builder, signature.args[0], xqjn__cln)
        context.nrt.incref(builder, signature.args[1], mtp__ezcyk)
        context.nrt.incref(builder, signature.args[2], hwhwt__lccxj)
        return edv__qtc._getvalue()
    mbl__mkgo = CSRMatrixType(data_t.dtype, indices_t.dtype)
    ifp__uldot = mbl__mkgo(data_t, indices_t, indptr_t, types.UniTuple(
        types.int64, 2))
    return ifp__uldot, codegen


if bodo.utils.utils.has_scipy():
    import scipy.sparse

    @typeof_impl.register(scipy.sparse.csr_matrix)
    def _typeof_csr_matrix(val, c):
        dtype = numba.from_dtype(val.dtype)
        idx_dtype = numba.from_dtype(val.indices.dtype)
        return CSRMatrixType(dtype, idx_dtype)


@unbox(CSRMatrixType)
def unbox_csr_matrix(typ, val, c):
    edv__qtc = cgutils.create_struct_proxy(typ)(c.context, c.builder)
    nxoy__cwn = c.pyapi.object_getattr_string(val, 'data')
    rka__jmc = c.pyapi.object_getattr_string(val, 'indices')
    ftbn__ontre = c.pyapi.object_getattr_string(val, 'indptr')
    ore__opp = c.pyapi.object_getattr_string(val, 'shape')
    edv__qtc.data = c.pyapi.to_native_value(types.Array(typ.dtype, 1, 'C'),
        nxoy__cwn).value
    edv__qtc.indices = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), rka__jmc).value
    edv__qtc.indptr = c.pyapi.to_native_value(types.Array(typ.idx_dtype, 1,
        'C'), ftbn__ontre).value
    edv__qtc.shape = c.pyapi.to_native_value(types.UniTuple(types.int64, 2),
        ore__opp).value
    c.pyapi.decref(nxoy__cwn)
    c.pyapi.decref(rka__jmc)
    c.pyapi.decref(ftbn__ontre)
    c.pyapi.decref(ore__opp)
    fprt__lvnu = cgutils.is_not_null(c.builder, c.pyapi.err_occurred())
    return NativeValue(edv__qtc._getvalue(), is_error=fprt__lvnu)


@box(CSRMatrixType)
def box_csr_matrix(typ, val, c):
    ducy__dybxb = c.context.insert_const_string(c.builder.module,
        'scipy.sparse')
    faj__aofw = c.pyapi.import_module_noblock(ducy__dybxb)
    edv__qtc = cgutils.create_struct_proxy(typ)(c.context, c.builder, val)
    c.context.nrt.incref(c.builder, types.Array(typ.dtype, 1, 'C'),
        edv__qtc.data)
    nxoy__cwn = c.pyapi.from_native_value(types.Array(typ.dtype, 1, 'C'),
        edv__qtc.data, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        edv__qtc.indices)
    rka__jmc = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1, 'C'),
        edv__qtc.indices, c.env_manager)
    c.context.nrt.incref(c.builder, types.Array(typ.idx_dtype, 1, 'C'),
        edv__qtc.indptr)
    ftbn__ontre = c.pyapi.from_native_value(types.Array(typ.idx_dtype, 1,
        'C'), edv__qtc.indptr, c.env_manager)
    ore__opp = c.pyapi.from_native_value(types.UniTuple(types.int64, 2),
        edv__qtc.shape, c.env_manager)
    crbfs__uprdw = c.pyapi.tuple_pack([nxoy__cwn, rka__jmc, ftbn__ontre])
    yzd__eaf = c.pyapi.call_method(faj__aofw, 'csr_matrix', (crbfs__uprdw,
        ore__opp))
    c.pyapi.decref(crbfs__uprdw)
    c.pyapi.decref(nxoy__cwn)
    c.pyapi.decref(rka__jmc)
    c.pyapi.decref(ftbn__ontre)
    c.pyapi.decref(ore__opp)
    c.pyapi.decref(faj__aofw)
    c.context.nrt.decref(c.builder, typ, val)
    return yzd__eaf


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
    qurw__faqsa = A.dtype
    mqfn__kyy = A.idx_dtype
    if isinstance(idx, types.BaseTuple) and len(idx) == 2 and isinstance(idx
        [0], types.SliceType) and isinstance(idx[1], types.SliceType):

        def impl(A, idx):
            edpcd__idn, mdlr__ckcqi = A.shape
            ltu__ecl = numba.cpython.unicode._normalize_slice(idx[0],
                edpcd__idn)
            vpxcg__ilfep = numba.cpython.unicode._normalize_slice(idx[1],
                mdlr__ckcqi)
            if ltu__ecl.step != 1 or vpxcg__ilfep.step != 1:
                raise ValueError(
                    'CSR matrix slice getitem only supports step=1 currently')
            ryq__ukmwj = ltu__ecl.start
            iuq__onex = ltu__ecl.stop
            udoo__sjmfq = vpxcg__ilfep.start
            jrmmp__tpxi = vpxcg__ilfep.stop
            kfaf__jmuxw = A.indptr
            sqq__xyl = A.indices
            aap__qkvw = A.data
            ltxka__ybx = iuq__onex - ryq__ukmwj
            gnkx__lqjnb = jrmmp__tpxi - udoo__sjmfq
            ook__iiey = 0
            puzne__woza = 0
            for biq__fexx in range(ltxka__ybx):
                aftb__avid = kfaf__jmuxw[ryq__ukmwj + biq__fexx]
                oukr__cnfi = kfaf__jmuxw[ryq__ukmwj + biq__fexx + 1]
                for dsld__anw in range(aftb__avid, oukr__cnfi):
                    if sqq__xyl[dsld__anw] >= udoo__sjmfq and sqq__xyl[
                        dsld__anw] < jrmmp__tpxi:
                        ook__iiey += 1
            bxm__asth = np.empty(ltxka__ybx + 1, mqfn__kyy)
            jwsnl__sxlcq = np.empty(ook__iiey, mqfn__kyy)
            tyc__spcm = np.empty(ook__iiey, qurw__faqsa)
            bxm__asth[0] = 0
            for biq__fexx in range(ltxka__ybx):
                aftb__avid = kfaf__jmuxw[ryq__ukmwj + biq__fexx]
                oukr__cnfi = kfaf__jmuxw[ryq__ukmwj + biq__fexx + 1]
                for dsld__anw in range(aftb__avid, oukr__cnfi):
                    if sqq__xyl[dsld__anw] >= udoo__sjmfq and sqq__xyl[
                        dsld__anw] < jrmmp__tpxi:
                        jwsnl__sxlcq[puzne__woza] = sqq__xyl[dsld__anw
                            ] - udoo__sjmfq
                        tyc__spcm[puzne__woza] = aap__qkvw[dsld__anw]
                        puzne__woza += 1
                bxm__asth[biq__fexx + 1] = puzne__woza
            return init_csr_matrix(tyc__spcm, jwsnl__sxlcq, bxm__asth, (
                ltxka__ybx, gnkx__lqjnb))
        return impl
    raise BodoError(
        f'getitem for CSR matrix with index type {idx} not supported yet.')
