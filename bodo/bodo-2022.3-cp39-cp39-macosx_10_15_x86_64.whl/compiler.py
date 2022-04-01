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
        qiq__emn = 'bodo' if distributed else 'bodo_seq'
        qiq__emn = qiq__emn + '_inline' if inline_calls_pass else qiq__emn
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state, qiq__emn)
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
    for rrimt__ekhv, (bhx__bmlsz, ppvxb__yih) in enumerate(pm.passes):
        if bhx__bmlsz == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(rrimt__ekhv, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for rrimt__ekhv, (bhx__bmlsz, ppvxb__yih) in enumerate(pm.passes):
        if bhx__bmlsz == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[rrimt__ekhv] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for rrimt__ekhv, (bhx__bmlsz, ppvxb__yih) in enumerate(pm.passes):
        if bhx__bmlsz == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(rrimt__ekhv)
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
    bqqqr__mfpu = guard(get_definition, func_ir, rhs.func)
    if isinstance(bqqqr__mfpu, (ir.Global, ir.FreeVar, ir.Const)):
        jqgrr__gdcim = bqqqr__mfpu.value
    else:
        jgkn__mwp = guard(find_callname, func_ir, rhs)
        if not (jgkn__mwp and isinstance(jgkn__mwp[0], str) and isinstance(
            jgkn__mwp[1], str)):
            return
        func_name, func_mod = jgkn__mwp
        try:
            import importlib
            bosd__lgyav = importlib.import_module(func_mod)
            jqgrr__gdcim = getattr(bosd__lgyav, func_name)
        except:
            return
    if isinstance(jqgrr__gdcim, CPUDispatcher) and issubclass(jqgrr__gdcim.
        _compiler.pipeline_class, BodoCompiler
        ) and jqgrr__gdcim._compiler.pipeline_class != BodoCompilerUDF:
        jqgrr__gdcim._compiler.pipeline_class = BodoCompilerUDF
        jqgrr__gdcim.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for nuzb__wfjow in block.body:
                if is_call_assign(nuzb__wfjow):
                    _convert_bodo_dispatcher_to_udf(nuzb__wfjow.value,
                        state.func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        wxki__wtv = UntypedPass(state.func_ir, state.typingctx, state.args,
            state.locals, state.metadata, state.flags)
        wxki__wtv.run()
        return True


def _update_definitions(func_ir, node_list):
    ynuuz__yktsu = ir.Loc('', 0)
    nkrl__ybz = ir.Block(ir.Scope(None, ynuuz__yktsu), ynuuz__yktsu)
    nkrl__ybz.body = node_list
    build_definitions({(0): nkrl__ybz}, func_ir._definitions)


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
        bhst__qle = 'overload_series_' + rhs.attr
        rrxo__heeox = getattr(bodo.hiframes.series_impl, bhst__qle)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        bhst__qle = 'overload_dataframe_' + rhs.attr
        rrxo__heeox = getattr(bodo.hiframes.dataframe_impl, bhst__qle)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    wlvn__fonk = rrxo__heeox(rhs_type)
    inl__vazp = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc)
    tpcll__qlioy = compile_func_single_block(wlvn__fonk, (rhs.value,), stmt
        .target, inl__vazp)
    _update_definitions(func_ir, tpcll__qlioy)
    new_body += tpcll__qlioy
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
        cokcj__iken = tuple(typemap[gbw__ebs.name] for gbw__ebs in rhs.args)
        jhzjn__bsgm = {qiq__emn: typemap[gbw__ebs.name] for qiq__emn,
            gbw__ebs in dict(rhs.kws).items()}
        wlvn__fonk = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*cokcj__iken, **jhzjn__bsgm)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        cokcj__iken = tuple(typemap[gbw__ebs.name] for gbw__ebs in rhs.args)
        jhzjn__bsgm = {qiq__emn: typemap[gbw__ebs.name] for qiq__emn,
            gbw__ebs in dict(rhs.kws).items()}
        wlvn__fonk = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*cokcj__iken, **jhzjn__bsgm)
    else:
        return False
    epi__pvg = replace_func(pass_info, wlvn__fonk, rhs.args, pysig=numba.
        core.utils.pysignature(wlvn__fonk), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    ozjke__kde, ppvxb__yih = inline_closure_call(func_ir, epi__pvg.glbls,
        block, len(new_body), epi__pvg.func, typingctx=typingctx, targetctx
        =targetctx, arg_typs=epi__pvg.arg_types, typemap=typemap, calltypes
        =calltypes, work_list=work_list)
    for qibc__igcs in ozjke__kde.values():
        qibc__igcs.loc = rhs.loc
        update_locs(qibc__igcs.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    bscpo__caj = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = bscpo__caj(func_ir, typemap)
    wcs__ery = func_ir.blocks
    work_list = list((fqeez__eyon, wcs__ery[fqeez__eyon]) for fqeez__eyon in
        reversed(wcs__ery.keys()))
    while work_list:
        mlacp__pnwfl, block = work_list.pop()
        new_body = []
        dcz__mucjt = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                jgkn__mwp = guard(find_callname, func_ir, rhs, typemap)
                if jgkn__mwp is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = jgkn__mwp
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    dcz__mucjt = True
                    break
            new_body.append(stmt)
        if not dcz__mucjt:
            wcs__ery[mlacp__pnwfl].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        pom__xrz = DistributedPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = pom__xrz.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        lktaa__gfpn = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        lktaa__gfpn.run()
        lktaa__gfpn.run()
        lktaa__gfpn.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        ajoxr__uiok = 0
        achto__ihj = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            ajoxr__uiok = int(os.environ[achto__ihj])
        except:
            pass
        if ajoxr__uiok > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(ajoxr__uiok,
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
        inl__vazp = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, inl__vazp)
        for block in state.func_ir.blocks.values():
            new_body = []
            for nuzb__wfjow in block.body:
                if type(nuzb__wfjow) in distributed_run_extensions:
                    mwx__rch = distributed_run_extensions[type(nuzb__wfjow)]
                    cos__vjar = mwx__rch(nuzb__wfjow, None, state.typemap,
                        state.calltypes, state.typingctx, state.targetctx)
                    new_body += cos__vjar
                elif is_call_assign(nuzb__wfjow):
                    rhs = nuzb__wfjow.value
                    jgkn__mwp = guard(find_callname, state.func_ir, rhs)
                    if jgkn__mwp == ('gatherv', 'bodo') or jgkn__mwp == (
                        'allgatherv', 'bodo'):
                        nlts__sruok = state.typemap[nuzb__wfjow.target.name]
                        hvjjk__knfb = state.typemap[rhs.args[0].name]
                        if isinstance(hvjjk__knfb, types.Array) and isinstance(
                            nlts__sruok, types.Array):
                            jwwx__age = hvjjk__knfb.copy(readonly=False)
                            swur__hqi = nlts__sruok.copy(readonly=False)
                            if jwwx__age == swur__hqi:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), nuzb__wfjow.target, inl__vazp)
                                continue
                        if (nlts__sruok != hvjjk__knfb and 
                            to_str_arr_if_dict_array(nlts__sruok) ==
                            to_str_arr_if_dict_array(hvjjk__knfb)):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), nuzb__wfjow.target,
                                inl__vazp, extra_globals={
                                'decode_if_dict_array': decode_if_dict_array})
                            continue
                        else:
                            nuzb__wfjow.value = rhs.args[0]
                    new_body.append(nuzb__wfjow)
                else:
                    new_body.append(nuzb__wfjow)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        eou__rpquh = TableColumnDelPass(state.func_ir, state.typingctx,
            state.targetctx, state.typemap, state.calltypes)
        return eou__rpquh.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    jvqa__xyei = set()
    while work_list:
        mlacp__pnwfl, block = work_list.pop()
        jvqa__xyei.add(mlacp__pnwfl)
        for i, pwtz__pln in enumerate(block.body):
            if isinstance(pwtz__pln, ir.Assign):
                fpsm__ieghz = pwtz__pln.value
                if isinstance(fpsm__ieghz, ir.Expr
                    ) and fpsm__ieghz.op == 'call':
                    bqqqr__mfpu = guard(get_definition, func_ir,
                        fpsm__ieghz.func)
                    if isinstance(bqqqr__mfpu, (ir.Global, ir.FreeVar)
                        ) and isinstance(bqqqr__mfpu.value, CPUDispatcher
                        ) and issubclass(bqqqr__mfpu.value._compiler.
                        pipeline_class, BodoCompiler):
                        skz__uzrj = bqqqr__mfpu.value.py_func
                        arg_types = None
                        if typingctx:
                            wual__kyzai = dict(fpsm__ieghz.kws)
                            gqka__udz = tuple(typemap[gbw__ebs.name] for
                                gbw__ebs in fpsm__ieghz.args)
                            cumo__lldie = {amnt__njwj: typemap[gbw__ebs.
                                name] for amnt__njwj, gbw__ebs in
                                wual__kyzai.items()}
                            ppvxb__yih, arg_types = (bqqqr__mfpu.value.
                                fold_argument_types(gqka__udz, cumo__lldie))
                        ppvxb__yih, lcq__fgv = inline_closure_call(func_ir,
                            skz__uzrj.__globals__, block, i, skz__uzrj,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((lcq__fgv[amnt__njwj].name, gbw__ebs
                            ) for amnt__njwj, gbw__ebs in bqqqr__mfpu.value
                            .locals.items() if amnt__njwj in lcq__fgv)
                        break
    return jvqa__xyei


def udf_jit(signature_or_function=None, **options):
    gfzgf__fqwky = {'comprehension': True, 'setitem': False,
        'inplace_binop': False, 'reduction': True, 'numpy': True, 'stencil':
        False, 'fusion': True}
    return numba.njit(signature_or_function, parallel=gfzgf__fqwky,
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
    for rrimt__ekhv, (bhx__bmlsz, ppvxb__yih) in enumerate(pm.passes):
        if bhx__bmlsz == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:rrimt__ekhv + 1]
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
    wmknx__srao = None
    gqwn__wlqlp = None
    _locals = {}
    kylo__xbt = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(kylo__xbt, arg_types,
        kw_types)
    uwd__yxbnt = numba.core.compiler.Flags()
    yplq__jcuee = {'comprehension': True, 'setitem': False, 'inplace_binop':
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    vtvs__eqgn = {'nopython': True, 'boundscheck': False, 'parallel':
        yplq__jcuee}
    numba.core.registry.cpu_target.options.parse_as_flags(uwd__yxbnt,
        vtvs__eqgn)
    zkxe__jppt = TyperCompiler(typingctx, targetctx, wmknx__srao, args,
        gqwn__wlqlp, uwd__yxbnt, _locals)
    return zkxe__jppt.compile_extra(func)
