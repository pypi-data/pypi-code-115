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
        oonpk__uzhax = 'bodo' if distributed else 'bodo_seq'
        oonpk__uzhax = (oonpk__uzhax + '_inline' if inline_calls_pass else
            oonpk__uzhax)
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state,
            oonpk__uzhax)
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
    for bgl__mwyjp, (wvcqs__mzhie, oanj__mdg) in enumerate(pm.passes):
        if wvcqs__mzhie == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(bgl__mwyjp, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for bgl__mwyjp, (wvcqs__mzhie, oanj__mdg) in enumerate(pm.passes):
        if wvcqs__mzhie == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[bgl__mwyjp] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for bgl__mwyjp, (wvcqs__mzhie, oanj__mdg) in enumerate(pm.passes):
        if wvcqs__mzhie == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(bgl__mwyjp)
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
    hmaxd__fei = guard(get_definition, func_ir, rhs.func)
    if isinstance(hmaxd__fei, (ir.Global, ir.FreeVar, ir.Const)):
        iudp__kcoda = hmaxd__fei.value
    else:
        eng__fjq = guard(find_callname, func_ir, rhs)
        if not (eng__fjq and isinstance(eng__fjq[0], str) and isinstance(
            eng__fjq[1], str)):
            return
        func_name, func_mod = eng__fjq
        try:
            import importlib
            tmm__vhc = importlib.import_module(func_mod)
            iudp__kcoda = getattr(tmm__vhc, func_name)
        except:
            return
    if isinstance(iudp__kcoda, CPUDispatcher) and issubclass(iudp__kcoda.
        _compiler.pipeline_class, BodoCompiler
        ) and iudp__kcoda._compiler.pipeline_class != BodoCompilerUDF:
        iudp__kcoda._compiler.pipeline_class = BodoCompilerUDF
        iudp__kcoda.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for xlx__czbhm in block.body:
                if is_call_assign(xlx__czbhm):
                    _convert_bodo_dispatcher_to_udf(xlx__czbhm.value, state
                        .func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        nogc__dnjm = UntypedPass(state.func_ir, state.typingctx, state.args,
            state.locals, state.metadata, state.flags)
        nogc__dnjm.run()
        return True


def _update_definitions(func_ir, node_list):
    qwhme__ybk = ir.Loc('', 0)
    eem__jyk = ir.Block(ir.Scope(None, qwhme__ybk), qwhme__ybk)
    eem__jyk.body = node_list
    build_definitions({(0): eem__jyk}, func_ir._definitions)


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
        rkw__ojyi = 'overload_series_' + rhs.attr
        wuf__fbu = getattr(bodo.hiframes.series_impl, rkw__ojyi)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        rkw__ojyi = 'overload_dataframe_' + rhs.attr
        wuf__fbu = getattr(bodo.hiframes.dataframe_impl, rkw__ojyi)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    bpyc__bgeal = wuf__fbu(rhs_type)
    may__vcq = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc)
    ogoj__gqa = compile_func_single_block(bpyc__bgeal, (rhs.value,), stmt.
        target, may__vcq)
    _update_definitions(func_ir, ogoj__gqa)
    new_body += ogoj__gqa
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
        ujnm__topd = tuple(typemap[gxcjt__iox.name] for gxcjt__iox in rhs.args)
        kcqfk__feke = {oonpk__uzhax: typemap[gxcjt__iox.name] for 
            oonpk__uzhax, gxcjt__iox in dict(rhs.kws).items()}
        bpyc__bgeal = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*ujnm__topd, **kcqfk__feke)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        ujnm__topd = tuple(typemap[gxcjt__iox.name] for gxcjt__iox in rhs.args)
        kcqfk__feke = {oonpk__uzhax: typemap[gxcjt__iox.name] for 
            oonpk__uzhax, gxcjt__iox in dict(rhs.kws).items()}
        bpyc__bgeal = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*ujnm__topd, **kcqfk__feke)
    else:
        return False
    emnx__jndx = replace_func(pass_info, bpyc__bgeal, rhs.args, pysig=numba
        .core.utils.pysignature(bpyc__bgeal), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    czfmy__cxo, oanj__mdg = inline_closure_call(func_ir, emnx__jndx.glbls,
        block, len(new_body), emnx__jndx.func, typingctx=typingctx,
        targetctx=targetctx, arg_typs=emnx__jndx.arg_types, typemap=typemap,
        calltypes=calltypes, work_list=work_list)
    for mqbdp__zbodo in czfmy__cxo.values():
        mqbdp__zbodo.loc = rhs.loc
        update_locs(mqbdp__zbodo.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    peoc__helwv = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = peoc__helwv(func_ir, typemap)
    yvck__jvmvg = func_ir.blocks
    work_list = list((itr__alutp, yvck__jvmvg[itr__alutp]) for itr__alutp in
        reversed(yvck__jvmvg.keys()))
    while work_list:
        oket__ndag, block = work_list.pop()
        new_body = []
        vez__umk = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                eng__fjq = guard(find_callname, func_ir, rhs, typemap)
                if eng__fjq is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = eng__fjq
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    vez__umk = True
                    break
            new_body.append(stmt)
        if not vez__umk:
            yvck__jvmvg[oket__ndag].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        yje__bwyyq = DistributedPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = yje__bwyyq.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        inqm__ocnt = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        inqm__ocnt.run()
        inqm__ocnt.run()
        inqm__ocnt.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        oziq__hba = 0
        vzocm__klogn = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            oziq__hba = int(os.environ[vzocm__klogn])
        except:
            pass
        if oziq__hba > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(oziq__hba, state
                .metadata)
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
        may__vcq = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, may__vcq)
        for block in state.func_ir.blocks.values():
            new_body = []
            for xlx__czbhm in block.body:
                if type(xlx__czbhm) in distributed_run_extensions:
                    fmn__anfzz = distributed_run_extensions[type(xlx__czbhm)]
                    mft__juq = fmn__anfzz(xlx__czbhm, None, state.typemap,
                        state.calltypes, state.typingctx, state.targetctx)
                    new_body += mft__juq
                elif is_call_assign(xlx__czbhm):
                    rhs = xlx__czbhm.value
                    eng__fjq = guard(find_callname, state.func_ir, rhs)
                    if eng__fjq == ('gatherv', 'bodo') or eng__fjq == (
                        'allgatherv', 'bodo'):
                        tlbkk__mzoe = state.typemap[xlx__czbhm.target.name]
                        qxo__dib = state.typemap[rhs.args[0].name]
                        if isinstance(qxo__dib, types.Array) and isinstance(
                            tlbkk__mzoe, types.Array):
                            mjnmv__gjvq = qxo__dib.copy(readonly=False)
                            cpag__uxzk = tlbkk__mzoe.copy(readonly=False)
                            if mjnmv__gjvq == cpag__uxzk:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), xlx__czbhm.target, may__vcq)
                                continue
                        if (tlbkk__mzoe != qxo__dib and 
                            to_str_arr_if_dict_array(tlbkk__mzoe) ==
                            to_str_arr_if_dict_array(qxo__dib)):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), xlx__czbhm.target, may__vcq,
                                extra_globals={'decode_if_dict_array':
                                decode_if_dict_array})
                            continue
                        else:
                            xlx__czbhm.value = rhs.args[0]
                    new_body.append(xlx__czbhm)
                else:
                    new_body.append(xlx__czbhm)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        fcecw__gwg = TableColumnDelPass(state.func_ir, state.typingctx,
            state.targetctx, state.typemap, state.calltypes)
        return fcecw__gwg.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    qpb__vsvz = set()
    while work_list:
        oket__ndag, block = work_list.pop()
        qpb__vsvz.add(oket__ndag)
        for i, tfvaa__jhmqv in enumerate(block.body):
            if isinstance(tfvaa__jhmqv, ir.Assign):
                fho__rqf = tfvaa__jhmqv.value
                if isinstance(fho__rqf, ir.Expr) and fho__rqf.op == 'call':
                    hmaxd__fei = guard(get_definition, func_ir, fho__rqf.func)
                    if isinstance(hmaxd__fei, (ir.Global, ir.FreeVar)
                        ) and isinstance(hmaxd__fei.value, CPUDispatcher
                        ) and issubclass(hmaxd__fei.value._compiler.
                        pipeline_class, BodoCompiler):
                        szf__eoka = hmaxd__fei.value.py_func
                        arg_types = None
                        if typingctx:
                            bjzcf__hvo = dict(fho__rqf.kws)
                            oen__hlu = tuple(typemap[gxcjt__iox.name] for
                                gxcjt__iox in fho__rqf.args)
                            ybtlv__uqa = {itm__yzeuh: typemap[gxcjt__iox.
                                name] for itm__yzeuh, gxcjt__iox in
                                bjzcf__hvo.items()}
                            oanj__mdg, arg_types = (hmaxd__fei.value.
                                fold_argument_types(oen__hlu, ybtlv__uqa))
                        oanj__mdg, wrvy__lqmf = inline_closure_call(func_ir,
                            szf__eoka.__globals__, block, i, szf__eoka,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((wrvy__lqmf[itm__yzeuh].name,
                            gxcjt__iox) for itm__yzeuh, gxcjt__iox in
                            hmaxd__fei.value.locals.items() if itm__yzeuh in
                            wrvy__lqmf)
                        break
    return qpb__vsvz


def udf_jit(signature_or_function=None, **options):
    oeyc__zyu = {'comprehension': True, 'setitem': False, 'inplace_binop': 
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    return numba.njit(signature_or_function, parallel=oeyc__zyu,
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
    for bgl__mwyjp, (wvcqs__mzhie, oanj__mdg) in enumerate(pm.passes):
        if wvcqs__mzhie == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:bgl__mwyjp + 1]
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
    ice__sabk = None
    rjcew__tnbon = None
    _locals = {}
    gvbqd__jkcpq = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(gvbqd__jkcpq, arg_types,
        kw_types)
    yuzvx__dniae = numba.core.compiler.Flags()
    fuh__vdf = {'comprehension': True, 'setitem': False, 'inplace_binop': 
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    gbpl__tmzzk = {'nopython': True, 'boundscheck': False, 'parallel': fuh__vdf
        }
    numba.core.registry.cpu_target.options.parse_as_flags(yuzvx__dniae,
        gbpl__tmzzk)
    xihe__vzo = TyperCompiler(typingctx, targetctx, ice__sabk, args,
        rjcew__tnbon, yuzvx__dniae, _locals)
    return xihe__vzo.compile_extra(func)
