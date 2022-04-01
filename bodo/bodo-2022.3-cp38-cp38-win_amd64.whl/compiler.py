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
        lfc__reoz = 'bodo' if distributed else 'bodo_seq'
        lfc__reoz = lfc__reoz + '_inline' if inline_calls_pass else lfc__reoz
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state, lfc__reoz)
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
    for fsvp__uvvc, (tknvb__ibw, twofr__ayqf) in enumerate(pm.passes):
        if tknvb__ibw == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(fsvp__uvvc, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for fsvp__uvvc, (tknvb__ibw, twofr__ayqf) in enumerate(pm.passes):
        if tknvb__ibw == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[fsvp__uvvc] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for fsvp__uvvc, (tknvb__ibw, twofr__ayqf) in enumerate(pm.passes):
        if tknvb__ibw == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(fsvp__uvvc)
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
    ocpy__pathl = guard(get_definition, func_ir, rhs.func)
    if isinstance(ocpy__pathl, (ir.Global, ir.FreeVar, ir.Const)):
        rvfh__lbau = ocpy__pathl.value
    else:
        itj__dyvk = guard(find_callname, func_ir, rhs)
        if not (itj__dyvk and isinstance(itj__dyvk[0], str) and isinstance(
            itj__dyvk[1], str)):
            return
        func_name, func_mod = itj__dyvk
        try:
            import importlib
            yotmw__iymnc = importlib.import_module(func_mod)
            rvfh__lbau = getattr(yotmw__iymnc, func_name)
        except:
            return
    if isinstance(rvfh__lbau, CPUDispatcher) and issubclass(rvfh__lbau.
        _compiler.pipeline_class, BodoCompiler
        ) and rvfh__lbau._compiler.pipeline_class != BodoCompilerUDF:
        rvfh__lbau._compiler.pipeline_class = BodoCompilerUDF
        rvfh__lbau.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for gbiiz__ilg in block.body:
                if is_call_assign(gbiiz__ilg):
                    _convert_bodo_dispatcher_to_udf(gbiiz__ilg.value, state
                        .func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        fcui__zee = UntypedPass(state.func_ir, state.typingctx, state.args,
            state.locals, state.metadata, state.flags)
        fcui__zee.run()
        return True


def _update_definitions(func_ir, node_list):
    bez__cmp = ir.Loc('', 0)
    bfvfw__ranj = ir.Block(ir.Scope(None, bez__cmp), bez__cmp)
    bfvfw__ranj.body = node_list
    build_definitions({(0): bfvfw__ranj}, func_ir._definitions)


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
        rlby__ozzy = 'overload_series_' + rhs.attr
        czapk__asxu = getattr(bodo.hiframes.series_impl, rlby__ozzy)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        rlby__ozzy = 'overload_dataframe_' + rhs.attr
        czapk__asxu = getattr(bodo.hiframes.dataframe_impl, rlby__ozzy)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    nfi__jdkq = czapk__asxu(rhs_type)
    txyu__bwlfg = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc
        )
    bhrb__huwgu = compile_func_single_block(nfi__jdkq, (rhs.value,), stmt.
        target, txyu__bwlfg)
    _update_definitions(func_ir, bhrb__huwgu)
    new_body += bhrb__huwgu
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
        wai__ynumb = tuple(typemap[cjqnu__btnwy.name] for cjqnu__btnwy in
            rhs.args)
        uge__lghc = {lfc__reoz: typemap[cjqnu__btnwy.name] for lfc__reoz,
            cjqnu__btnwy in dict(rhs.kws).items()}
        nfi__jdkq = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*wai__ynumb, **uge__lghc)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        wai__ynumb = tuple(typemap[cjqnu__btnwy.name] for cjqnu__btnwy in
            rhs.args)
        uge__lghc = {lfc__reoz: typemap[cjqnu__btnwy.name] for lfc__reoz,
            cjqnu__btnwy in dict(rhs.kws).items()}
        nfi__jdkq = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*wai__ynumb, **uge__lghc)
    else:
        return False
    izzgh__cgud = replace_func(pass_info, nfi__jdkq, rhs.args, pysig=numba.
        core.utils.pysignature(nfi__jdkq), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    xjg__tuybo, twofr__ayqf = inline_closure_call(func_ir, izzgh__cgud.
        glbls, block, len(new_body), izzgh__cgud.func, typingctx=typingctx,
        targetctx=targetctx, arg_typs=izzgh__cgud.arg_types, typemap=
        typemap, calltypes=calltypes, work_list=work_list)
    for fwlj__more in xjg__tuybo.values():
        fwlj__more.loc = rhs.loc
        update_locs(fwlj__more.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    nsp__hqlra = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = nsp__hqlra(func_ir, typemap)
    yqqab__rwgqv = func_ir.blocks
    work_list = list((foh__zjxoo, yqqab__rwgqv[foh__zjxoo]) for foh__zjxoo in
        reversed(yqqab__rwgqv.keys()))
    while work_list:
        oxij__vryfp, block = work_list.pop()
        new_body = []
        jqji__tek = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                itj__dyvk = guard(find_callname, func_ir, rhs, typemap)
                if itj__dyvk is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = itj__dyvk
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    jqji__tek = True
                    break
            new_body.append(stmt)
        if not jqji__tek:
            yqqab__rwgqv[oxij__vryfp].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        bhohv__bjl = DistributedPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = bhohv__bjl.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        klhn__jocma = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        klhn__jocma.run()
        klhn__jocma.run()
        klhn__jocma.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        lfveg__iczzi = 0
        sgfo__btycr = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            lfveg__iczzi = int(os.environ[sgfo__btycr])
        except:
            pass
        if lfveg__iczzi > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(lfveg__iczzi,
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
        txyu__bwlfg = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, txyu__bwlfg)
        for block in state.func_ir.blocks.values():
            new_body = []
            for gbiiz__ilg in block.body:
                if type(gbiiz__ilg) in distributed_run_extensions:
                    ilg__iope = distributed_run_extensions[type(gbiiz__ilg)]
                    dnve__ngpe = ilg__iope(gbiiz__ilg, None, state.typemap,
                        state.calltypes, state.typingctx, state.targetctx)
                    new_body += dnve__ngpe
                elif is_call_assign(gbiiz__ilg):
                    rhs = gbiiz__ilg.value
                    itj__dyvk = guard(find_callname, state.func_ir, rhs)
                    if itj__dyvk == ('gatherv', 'bodo') or itj__dyvk == (
                        'allgatherv', 'bodo'):
                        tcwj__ief = state.typemap[gbiiz__ilg.target.name]
                        qwnqy__qfy = state.typemap[rhs.args[0].name]
                        if isinstance(qwnqy__qfy, types.Array) and isinstance(
                            tcwj__ief, types.Array):
                            dqgs__hctyz = qwnqy__qfy.copy(readonly=False)
                            vsfg__onth = tcwj__ief.copy(readonly=False)
                            if dqgs__hctyz == vsfg__onth:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), gbiiz__ilg.target, txyu__bwlfg)
                                continue
                        if (tcwj__ief != qwnqy__qfy and 
                            to_str_arr_if_dict_array(tcwj__ief) ==
                            to_str_arr_if_dict_array(qwnqy__qfy)):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), gbiiz__ilg.target,
                                txyu__bwlfg, extra_globals={
                                'decode_if_dict_array': decode_if_dict_array})
                            continue
                        else:
                            gbiiz__ilg.value = rhs.args[0]
                    new_body.append(gbiiz__ilg)
                else:
                    new_body.append(gbiiz__ilg)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        kedqn__uqknn = TableColumnDelPass(state.func_ir, state.typingctx,
            state.targetctx, state.typemap, state.calltypes)
        return kedqn__uqknn.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    ujcc__lycas = set()
    while work_list:
        oxij__vryfp, block = work_list.pop()
        ujcc__lycas.add(oxij__vryfp)
        for i, kqtd__deaa in enumerate(block.body):
            if isinstance(kqtd__deaa, ir.Assign):
                uar__mxcbt = kqtd__deaa.value
                if isinstance(uar__mxcbt, ir.Expr) and uar__mxcbt.op == 'call':
                    ocpy__pathl = guard(get_definition, func_ir, uar__mxcbt
                        .func)
                    if isinstance(ocpy__pathl, (ir.Global, ir.FreeVar)
                        ) and isinstance(ocpy__pathl.value, CPUDispatcher
                        ) and issubclass(ocpy__pathl.value._compiler.
                        pipeline_class, BodoCompiler):
                        obfd__pcq = ocpy__pathl.value.py_func
                        arg_types = None
                        if typingctx:
                            wdoo__brig = dict(uar__mxcbt.kws)
                            hvzm__vny = tuple(typemap[cjqnu__btnwy.name] for
                                cjqnu__btnwy in uar__mxcbt.args)
                            awqew__ova = {xxi__xjmj: typemap[cjqnu__btnwy.
                                name] for xxi__xjmj, cjqnu__btnwy in
                                wdoo__brig.items()}
                            twofr__ayqf, arg_types = (ocpy__pathl.value.
                                fold_argument_types(hvzm__vny, awqew__ova))
                        twofr__ayqf, zyv__yfg = inline_closure_call(func_ir,
                            obfd__pcq.__globals__, block, i, obfd__pcq,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((zyv__yfg[xxi__xjmj].name,
                            cjqnu__btnwy) for xxi__xjmj, cjqnu__btnwy in
                            ocpy__pathl.value.locals.items() if xxi__xjmj in
                            zyv__yfg)
                        break
    return ujcc__lycas


def udf_jit(signature_or_function=None, **options):
    dqfmg__qhd = {'comprehension': True, 'setitem': False, 'inplace_binop':
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    return numba.njit(signature_or_function, parallel=dqfmg__qhd,
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
    for fsvp__uvvc, (tknvb__ibw, twofr__ayqf) in enumerate(pm.passes):
        if tknvb__ibw == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:fsvp__uvvc + 1]
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
    xjtvm__oovkj = None
    yizpt__ufn = None
    _locals = {}
    gck__xizgz = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(gck__xizgz, arg_types,
        kw_types)
    zjkj__ntc = numba.core.compiler.Flags()
    gplv__gdptx = {'comprehension': True, 'setitem': False, 'inplace_binop':
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    hhvsx__kur = {'nopython': True, 'boundscheck': False, 'parallel':
        gplv__gdptx}
    numba.core.registry.cpu_target.options.parse_as_flags(zjkj__ntc, hhvsx__kur
        )
    ydir__wulxt = TyperCompiler(typingctx, targetctx, xjtvm__oovkj, args,
        yizpt__ufn, zjkj__ntc, _locals)
    return ydir__wulxt.compile_extra(func)
