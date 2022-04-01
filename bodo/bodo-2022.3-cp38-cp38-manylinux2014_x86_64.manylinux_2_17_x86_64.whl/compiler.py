"""
Defines Bodo's compiler pipeline.
"""
import os
import warnings
from collections import namedtuple
import numba
from numba.core import ir, ir_utils, types
from numba.core.compiler import DefaultPassBuilder
from numba.core.compiler_machinery import AnalysisPass, FunctionPass, register_pass
from numba.core.inline_closurecall import inline_closure_call
from numba.core.ir_utils import build_definitions, find_callname, get_definition, guard
from numba.core.registry import CPUDispatcher
from numba.core.typed_passes import DumpParforDiagnostics, InlineOverloads, IRLegalization, NopythonTypeInference, ParforPass, PreParforPass
from numba.core.untyped_passes import MakeFunctionToJitFunction, ReconstructSSA, WithLifting
import bodo
import bodo.hiframes.dataframe_indexing
import bodo.hiframes.datetime_datetime_ext
import bodo.hiframes.datetime_timedelta_ext
import bodo.io
import bodo.libs
import bodo.libs.array_kernels
import bodo.libs.int_arr_ext
import bodo.libs.re_ext
import bodo.libs.spark_extra
import bodo.transforms
import bodo.transforms.series_pass
import bodo.transforms.untyped_pass
import bodo.utils
import bodo.utils.typing
from bodo.transforms.series_pass import SeriesPass
from bodo.transforms.table_column_del_pass import TableColumnDelPass
from bodo.transforms.typing_pass import BodoTypeInference
from bodo.transforms.untyped_pass import UntypedPass
from bodo.utils.utils import is_assign, is_call_assign, is_expr
numba.core.config.DISABLE_PERFORMANCE_WARNINGS = 1
from numba.core.errors import NumbaExperimentalFeatureWarning, NumbaPendingDeprecationWarning
warnings.simplefilter('ignore', category=NumbaExperimentalFeatureWarning)
warnings.simplefilter('ignore', category=NumbaPendingDeprecationWarning)
inline_all_calls = False


class BodoCompiler(numba.core.compiler.CompilerBase):

    def define_pipelines(self):
        return self._create_bodo_pipeline(distributed=True,
            inline_calls_pass=inline_all_calls)

    def _create_bodo_pipeline(self, distributed=True, inline_calls_pass=
        False, udf_pipeline=False):
        amw__mdl = 'bodo' if distributed else 'bodo_seq'
        amw__mdl = amw__mdl + '_inline' if inline_calls_pass else amw__mdl
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state, amw__mdl)
        if inline_calls_pass:
            pm.add_pass_after(InlinePass, WithLifting)
        if udf_pipeline:
            pm.add_pass_after(ConvertCallsUDFPass, WithLifting)
        add_pass_before(pm, BodoUntypedPass, ReconstructSSA)
        replace_pass(pm, BodoTypeInference, NopythonTypeInference)
        remove_pass(pm, MakeFunctionToJitFunction)
        add_pass_before(pm, BodoSeriesPass, PreParforPass)
        if distributed:
            pm.add_pass_after(BodoDistributedPass, ParforPass)
        else:
            pm.add_pass_after(LowerParforSeq, ParforPass)
            pm.add_pass_after(LowerBodoIRExtSeq, LowerParforSeq)
        add_pass_before(pm, BodoTableColumnDelPass, IRLegalization)
        pm.add_pass_after(BodoDumpDistDiagnosticsPass, DumpParforDiagnostics)
        pm.finalize()
        return [pm]


def add_pass_before(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for iuzgs__eveaf, (ellh__ulci, sifrv__frcw) in enumerate(pm.passes):
        if ellh__ulci == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(iuzgs__eveaf, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for iuzgs__eveaf, (ellh__ulci, sifrv__frcw) in enumerate(pm.passes):
        if ellh__ulci == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[iuzgs__eveaf] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for iuzgs__eveaf, (ellh__ulci, sifrv__frcw) in enumerate(pm.passes):
        if ellh__ulci == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(iuzgs__eveaf)
    pm._finalized = False


@register_pass(mutates_CFG=True, analysis_only=False)
class InlinePass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        inline_calls(state.func_ir, state.locals)
        state.func_ir.blocks = ir_utils.simplify_CFG(state.func_ir.blocks)
        return True


def _convert_bodo_dispatcher_to_udf(rhs, func_ir):
    vegrg__bpvnd = guard(get_definition, func_ir, rhs.func)
    if isinstance(vegrg__bpvnd, (ir.Global, ir.FreeVar, ir.Const)):
        okex__vpykx = vegrg__bpvnd.value
    else:
        zoavk__zdox = guard(find_callname, func_ir, rhs)
        if not (zoavk__zdox and isinstance(zoavk__zdox[0], str) and
            isinstance(zoavk__zdox[1], str)):
            return
        func_name, func_mod = zoavk__zdox
        try:
            import importlib
            ciqsv__yxu = importlib.import_module(func_mod)
            okex__vpykx = getattr(ciqsv__yxu, func_name)
        except:
            return
    if isinstance(okex__vpykx, CPUDispatcher) and issubclass(okex__vpykx.
        _compiler.pipeline_class, BodoCompiler
        ) and okex__vpykx._compiler.pipeline_class != BodoCompilerUDF:
        okex__vpykx._compiler.pipeline_class = BodoCompilerUDF
        okex__vpykx.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for iahhn__wihsc in block.body:
                if is_call_assign(iahhn__wihsc):
                    _convert_bodo_dispatcher_to_udf(iahhn__wihsc.value,
                        state.func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        rbwm__nhfvm = UntypedPass(state.func_ir, state.typingctx, state.
            args, state.locals, state.metadata, state.flags)
        rbwm__nhfvm.run()
        return True


def _update_definitions(func_ir, node_list):
    xwjdz__spv = ir.Loc('', 0)
    ionv__birzn = ir.Block(ir.Scope(None, xwjdz__spv), xwjdz__spv)
    ionv__birzn.body = node_list
    build_definitions({(0): ionv__birzn}, func_ir._definitions)


_series_inline_attrs = {'values', 'shape', 'size', 'empty', 'name', 'index',
    'dtype'}
_series_no_inline_methods = {'to_list', 'tolist', 'rolling', 'to_csv',
    'count', 'fillna', 'to_dict', 'map', 'apply', 'pipe', 'combine',
    'bfill', 'ffill', 'pad', 'backfill', 'mask', 'where'}
_series_method_alias = {'isnull': 'isna', 'product': 'prod', 'kurtosis':
    'kurt', 'is_monotonic': 'is_monotonic_increasing', 'notnull': 'notna'}
_dataframe_no_inline_methods = {'apply', 'itertuples', 'pipe', 'to_parquet',
    'to_sql', 'to_csv', 'to_json', 'assign', 'to_string', 'query',
    'rolling', 'mask', 'where'}
TypingInfo = namedtuple('TypingInfo', ['typingctx', 'targetctx', 'typemap',
    'calltypes', 'curr_loc'])


def _inline_bodo_getattr(stmt, rhs, rhs_type, new_body, func_ir, typingctx,
    targetctx, typemap, calltypes):
    from bodo.hiframes.pd_dataframe_ext import DataFrameType
    from bodo.hiframes.pd_series_ext import SeriesType
    from bodo.utils.transform import compile_func_single_block
    if isinstance(rhs_type, SeriesType) and rhs.attr in _series_inline_attrs:
        itt__wsk = 'overload_series_' + rhs.attr
        eag__qamvr = getattr(bodo.hiframes.series_impl, itt__wsk)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        itt__wsk = 'overload_dataframe_' + rhs.attr
        eag__qamvr = getattr(bodo.hiframes.dataframe_impl, itt__wsk)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    dezd__ehusu = eag__qamvr(rhs_type)
    crhos__wkt = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc)
    rud__wls = compile_func_single_block(dezd__ehusu, (rhs.value,), stmt.
        target, crhos__wkt)
    _update_definitions(func_ir, rud__wls)
    new_body += rud__wls
    return True


def _inline_bodo_call(rhs, i, func_mod, func_name, pass_info, new_body,
    block, typingctx, targetctx, calltypes, work_list):
    from bodo.hiframes.pd_dataframe_ext import DataFrameType
    from bodo.hiframes.pd_series_ext import SeriesType
    from bodo.utils.transform import replace_func, update_locs
    func_ir = pass_info.func_ir
    typemap = pass_info.typemap
    if isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        SeriesType) and func_name not in _series_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        if (func_name in bodo.hiframes.series_impl.explicit_binop_funcs or 
            func_name.startswith('r') and func_name[1:] in bodo.hiframes.
            series_impl.explicit_binop_funcs):
            return False
        rhs.args.insert(0, func_mod)
        tfng__hdnx = tuple(typemap[tlc__tcu.name] for tlc__tcu in rhs.args)
        lcpi__fovht = {amw__mdl: typemap[tlc__tcu.name] for amw__mdl,
            tlc__tcu in dict(rhs.kws).items()}
        dezd__ehusu = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*tfng__hdnx, **lcpi__fovht)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        tfng__hdnx = tuple(typemap[tlc__tcu.name] for tlc__tcu in rhs.args)
        lcpi__fovht = {amw__mdl: typemap[tlc__tcu.name] for amw__mdl,
            tlc__tcu in dict(rhs.kws).items()}
        dezd__ehusu = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*tfng__hdnx, **lcpi__fovht)
    else:
        return False
    pfrb__cjus = replace_func(pass_info, dezd__ehusu, rhs.args, pysig=numba
        .core.utils.pysignature(dezd__ehusu), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    ctk__yik, sifrv__frcw = inline_closure_call(func_ir, pfrb__cjus.glbls,
        block, len(new_body), pfrb__cjus.func, typingctx=typingctx,
        targetctx=targetctx, arg_typs=pfrb__cjus.arg_types, typemap=typemap,
        calltypes=calltypes, work_list=work_list)
    for crq__iqwf in ctk__yik.values():
        crq__iqwf.loc = rhs.loc
        update_locs(crq__iqwf.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    xtp__ppwk = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = xtp__ppwk(func_ir, typemap)
    abjbn__plgmw = func_ir.blocks
    work_list = list((sazis__fdy, abjbn__plgmw[sazis__fdy]) for sazis__fdy in
        reversed(abjbn__plgmw.keys()))
    while work_list:
        qcfrj__iyffa, block = work_list.pop()
        new_body = []
        lhwiz__glkli = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                zoavk__zdox = guard(find_callname, func_ir, rhs, typemap)
                if zoavk__zdox is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = zoavk__zdox
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    lhwiz__glkli = True
                    break
            new_body.append(stmt)
        if not lhwiz__glkli:
            abjbn__plgmw[qcfrj__iyffa].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        qeynt__znr = DistributedPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = qeynt__znr.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        rkm__gvdhu = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        rkm__gvdhu.run()
        rkm__gvdhu.run()
        rkm__gvdhu.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        yayzu__esnr = 0
        fjnl__iqsmu = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            yayzu__esnr = int(os.environ[fjnl__iqsmu])
        except:
            pass
        if yayzu__esnr > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(yayzu__esnr,
                state.metadata)
        return True


class BodoCompilerSeq(BodoCompiler):

    def define_pipelines(self):
        return self._create_bodo_pipeline(distributed=False,
            inline_calls_pass=inline_all_calls)


class BodoCompilerUDF(BodoCompiler):

    def define_pipelines(self):
        return self._create_bodo_pipeline(distributed=False, udf_pipeline=True)


@register_pass(mutates_CFG=False, analysis_only=True)
class LowerParforSeq(FunctionPass):
    _name = 'bodo_lower_parfor_seq_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        bodo.transforms.distributed_pass.lower_parfor_sequential(state.
            typingctx, state.func_ir, state.typemap, state.calltypes, state
            .metadata)
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class LowerBodoIRExtSeq(FunctionPass):
    _name = 'bodo_lower_ir_ext_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        from bodo.transforms.distributed_pass import distributed_run_extensions
        from bodo.transforms.table_column_del_pass import remove_dead_table_columns
        from bodo.utils.transform import compile_func_single_block
        from bodo.utils.typing import decode_if_dict_array, to_str_arr_if_dict_array
        state.func_ir._definitions = build_definitions(state.func_ir.blocks)
        crhos__wkt = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, crhos__wkt)
        for block in state.func_ir.blocks.values():
            new_body = []
            for iahhn__wihsc in block.body:
                if type(iahhn__wihsc) in distributed_run_extensions:
                    opkm__yink = distributed_run_extensions[type(iahhn__wihsc)]
                    mpjyw__qvuc = opkm__yink(iahhn__wihsc, None, state.
                        typemap, state.calltypes, state.typingctx, state.
                        targetctx)
                    new_body += mpjyw__qvuc
                elif is_call_assign(iahhn__wihsc):
                    rhs = iahhn__wihsc.value
                    zoavk__zdox = guard(find_callname, state.func_ir, rhs)
                    if zoavk__zdox == ('gatherv', 'bodo') or zoavk__zdox == (
                        'allgatherv', 'bodo'):
                        fda__qwonp = state.typemap[iahhn__wihsc.target.name]
                        rcy__sajsw = state.typemap[rhs.args[0].name]
                        if isinstance(rcy__sajsw, types.Array) and isinstance(
                            fda__qwonp, types.Array):
                            vpyu__nog = rcy__sajsw.copy(readonly=False)
                            qkot__oqg = fda__qwonp.copy(readonly=False)
                            if vpyu__nog == qkot__oqg:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), iahhn__wihsc.target, crhos__wkt)
                                continue
                        if (fda__qwonp != rcy__sajsw and 
                            to_str_arr_if_dict_array(fda__qwonp) ==
                            to_str_arr_if_dict_array(rcy__sajsw)):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), iahhn__wihsc.target,
                                crhos__wkt, extra_globals={
                                'decode_if_dict_array': decode_if_dict_array})
                            continue
                        else:
                            iahhn__wihsc.value = rhs.args[0]
                    new_body.append(iahhn__wihsc)
                else:
                    new_body.append(iahhn__wihsc)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        sdgpv__dlw = TableColumnDelPass(state.func_ir, state.typingctx,
            state.targetctx, state.typemap, state.calltypes)
        return sdgpv__dlw.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    uavz__lpgq = set()
    while work_list:
        qcfrj__iyffa, block = work_list.pop()
        uavz__lpgq.add(qcfrj__iyffa)
        for i, ylmcm__stpf in enumerate(block.body):
            if isinstance(ylmcm__stpf, ir.Assign):
                oad__pmbp = ylmcm__stpf.value
                if isinstance(oad__pmbp, ir.Expr) and oad__pmbp.op == 'call':
                    vegrg__bpvnd = guard(get_definition, func_ir, oad__pmbp
                        .func)
                    if isinstance(vegrg__bpvnd, (ir.Global, ir.FreeVar)
                        ) and isinstance(vegrg__bpvnd.value, CPUDispatcher
                        ) and issubclass(vegrg__bpvnd.value._compiler.
                        pipeline_class, BodoCompiler):
                        fjd__lifvt = vegrg__bpvnd.value.py_func
                        arg_types = None
                        if typingctx:
                            jyd__cldg = dict(oad__pmbp.kws)
                            eoi__rqxm = tuple(typemap[tlc__tcu.name] for
                                tlc__tcu in oad__pmbp.args)
                            cmeke__ppi = {fejyz__nwb: typemap[tlc__tcu.name
                                ] for fejyz__nwb, tlc__tcu in jyd__cldg.items()
                                }
                            sifrv__frcw, arg_types = (vegrg__bpvnd.value.
                                fold_argument_types(eoi__rqxm, cmeke__ppi))
                        sifrv__frcw, phh__gbgm = inline_closure_call(func_ir,
                            fjd__lifvt.__globals__, block, i, fjd__lifvt,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((phh__gbgm[fejyz__nwb].name,
                            tlc__tcu) for fejyz__nwb, tlc__tcu in
                            vegrg__bpvnd.value.locals.items() if fejyz__nwb in
                            phh__gbgm)
                        break
    return uavz__lpgq


def udf_jit(signature_or_function=None, **options):
    faa__ovahk = {'comprehension': True, 'setitem': False, 'inplace_binop':
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    return numba.njit(signature_or_function, parallel=faa__ovahk,
        pipeline_class=bodo.compiler.BodoCompilerUDF, **options)


def is_udf_call(func_type):
    return isinstance(func_type, numba.core.types.Dispatcher
        ) and func_type.dispatcher._compiler.pipeline_class == BodoCompilerUDF


def is_user_dispatcher(func_type):
    return isinstance(func_type, numba.core.types.functions.ObjModeDispatcher
        ) or isinstance(func_type, numba.core.types.Dispatcher) and issubclass(
        func_type.dispatcher._compiler.pipeline_class, BodoCompiler)


@register_pass(mutates_CFG=False, analysis_only=True)
class DummyCR(FunctionPass):
    _name = 'bodo_dummy_cr'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        state.cr = (state.func_ir, state.typemap, state.calltypes, state.
            return_type)
        return True


def remove_passes_after(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for iuzgs__eveaf, (ellh__ulci, sifrv__frcw) in enumerate(pm.passes):
        if ellh__ulci == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:iuzgs__eveaf + 1]
    pm._finalized = False


class TyperCompiler(BodoCompiler):

    def define_pipelines(self):
        [pm] = self._create_bodo_pipeline()
        remove_passes_after(pm, InlineOverloads)
        pm.add_pass_after(DummyCR, InlineOverloads)
        pm.finalize()
        return [pm]


def get_func_type_info(func, arg_types, kw_types):
    typingctx = numba.core.registry.cpu_target.typing_context
    targetctx = numba.core.registry.cpu_target.target_context
    ptk__lpzlg = None
    lfhqi__lmgi = None
    _locals = {}
    sssrr__aqx = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(sssrr__aqx, arg_types,
        kw_types)
    ifob__eqeh = numba.core.compiler.Flags()
    tivb__ytw = {'comprehension': True, 'setitem': False, 'inplace_binop': 
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    fccaz__uvw = {'nopython': True, 'boundscheck': False, 'parallel': tivb__ytw
        }
    numba.core.registry.cpu_target.options.parse_as_flags(ifob__eqeh,
        fccaz__uvw)
    hsajy__bdd = TyperCompiler(typingctx, targetctx, ptk__lpzlg, args,
        lfhqi__lmgi, ifob__eqeh, _locals)
    return hsajy__bdd.compile_extra(func)
