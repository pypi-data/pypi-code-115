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
        mrrxe__hlhto = 'bodo' if distributed else 'bodo_seq'
        mrrxe__hlhto = (mrrxe__hlhto + '_inline' if inline_calls_pass else
            mrrxe__hlhto)
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state,
            mrrxe__hlhto)
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
    for nkwc__kxrx, (uaes__pda, ghx__guuo) in enumerate(pm.passes):
        if uaes__pda == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(nkwc__kxrx, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for nkwc__kxrx, (uaes__pda, ghx__guuo) in enumerate(pm.passes):
        if uaes__pda == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[nkwc__kxrx] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for nkwc__kxrx, (uaes__pda, ghx__guuo) in enumerate(pm.passes):
        if uaes__pda == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(nkwc__kxrx)
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
    ofd__ltrc = guard(get_definition, func_ir, rhs.func)
    if isinstance(ofd__ltrc, (ir.Global, ir.FreeVar, ir.Const)):
        kws__dxvy = ofd__ltrc.value
    else:
        zzoq__dii = guard(find_callname, func_ir, rhs)
        if not (zzoq__dii and isinstance(zzoq__dii[0], str) and isinstance(
            zzoq__dii[1], str)):
            return
        func_name, func_mod = zzoq__dii
        try:
            import importlib
            vtd__dimfv = importlib.import_module(func_mod)
            kws__dxvy = getattr(vtd__dimfv, func_name)
        except:
            return
    if isinstance(kws__dxvy, CPUDispatcher) and issubclass(kws__dxvy.
        _compiler.pipeline_class, BodoCompiler
        ) and kws__dxvy._compiler.pipeline_class != BodoCompilerUDF:
        kws__dxvy._compiler.pipeline_class = BodoCompilerUDF
        kws__dxvy.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for nnyye__wgh in block.body:
                if is_call_assign(nnyye__wgh):
                    _convert_bodo_dispatcher_to_udf(nnyye__wgh.value, state
                        .func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        giw__tqwcn = UntypedPass(state.func_ir, state.typingctx, state.args,
            state.locals, state.metadata, state.flags)
        giw__tqwcn.run()
        return True


def _update_definitions(func_ir, node_list):
    xxji__yjuyv = ir.Loc('', 0)
    cnhh__myl = ir.Block(ir.Scope(None, xxji__yjuyv), xxji__yjuyv)
    cnhh__myl.body = node_list
    build_definitions({(0): cnhh__myl}, func_ir._definitions)


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
        rgz__lcgxs = 'overload_series_' + rhs.attr
        hve__fzjlv = getattr(bodo.hiframes.series_impl, rgz__lcgxs)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        rgz__lcgxs = 'overload_dataframe_' + rhs.attr
        hve__fzjlv = getattr(bodo.hiframes.dataframe_impl, rgz__lcgxs)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    wxzi__pzoyc = hve__fzjlv(rhs_type)
    jdlt__kdhnq = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc
        )
    iadzn__qko = compile_func_single_block(wxzi__pzoyc, (rhs.value,), stmt.
        target, jdlt__kdhnq)
    _update_definitions(func_ir, iadzn__qko)
    new_body += iadzn__qko
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
        zmuq__cgfn = tuple(typemap[bdql__eqig.name] for bdql__eqig in rhs.args)
        kavjw__iur = {mrrxe__hlhto: typemap[bdql__eqig.name] for 
            mrrxe__hlhto, bdql__eqig in dict(rhs.kws).items()}
        wxzi__pzoyc = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*zmuq__cgfn, **kavjw__iur)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        zmuq__cgfn = tuple(typemap[bdql__eqig.name] for bdql__eqig in rhs.args)
        kavjw__iur = {mrrxe__hlhto: typemap[bdql__eqig.name] for 
            mrrxe__hlhto, bdql__eqig in dict(rhs.kws).items()}
        wxzi__pzoyc = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*zmuq__cgfn, **kavjw__iur)
    else:
        return False
    lrs__tsq = replace_func(pass_info, wxzi__pzoyc, rhs.args, pysig=numba.
        core.utils.pysignature(wxzi__pzoyc), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    ubdd__mwwy, ghx__guuo = inline_closure_call(func_ir, lrs__tsq.glbls,
        block, len(new_body), lrs__tsq.func, typingctx=typingctx, targetctx
        =targetctx, arg_typs=lrs__tsq.arg_types, typemap=typemap, calltypes
        =calltypes, work_list=work_list)
    for fwl__mnnv in ubdd__mwwy.values():
        fwl__mnnv.loc = rhs.loc
        update_locs(fwl__mnnv.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    nytr__wab = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = nytr__wab(func_ir, typemap)
    bzlq__xlzv = func_ir.blocks
    work_list = list((bzjio__ora, bzlq__xlzv[bzjio__ora]) for bzjio__ora in
        reversed(bzlq__xlzv.keys()))
    while work_list:
        iec__ggxnb, block = work_list.pop()
        new_body = []
        syvy__ttvp = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                zzoq__dii = guard(find_callname, func_ir, rhs, typemap)
                if zzoq__dii is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = zzoq__dii
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    syvy__ttvp = True
                    break
            new_body.append(stmt)
        if not syvy__ttvp:
            bzlq__xlzv[iec__ggxnb].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        xeyi__xlk = DistributedPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = xeyi__xlk.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        vyg__wdmj = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        vyg__wdmj.run()
        vyg__wdmj.run()
        vyg__wdmj.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        bur__cfli = 0
        jcbbn__kqb = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            bur__cfli = int(os.environ[jcbbn__kqb])
        except:
            pass
        if bur__cfli > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(bur__cfli, state
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
        jdlt__kdhnq = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, jdlt__kdhnq)
        for block in state.func_ir.blocks.values():
            new_body = []
            for nnyye__wgh in block.body:
                if type(nnyye__wgh) in distributed_run_extensions:
                    gvmvy__nkb = distributed_run_extensions[type(nnyye__wgh)]
                    fhhfh__kopf = gvmvy__nkb(nnyye__wgh, None, state.
                        typemap, state.calltypes, state.typingctx, state.
                        targetctx)
                    new_body += fhhfh__kopf
                elif is_call_assign(nnyye__wgh):
                    rhs = nnyye__wgh.value
                    zzoq__dii = guard(find_callname, state.func_ir, rhs)
                    if zzoq__dii == ('gatherv', 'bodo') or zzoq__dii == (
                        'allgatherv', 'bodo'):
                        pifo__vtbd = state.typemap[nnyye__wgh.target.name]
                        epjwk__ugtw = state.typemap[rhs.args[0].name]
                        if isinstance(epjwk__ugtw, types.Array) and isinstance(
                            pifo__vtbd, types.Array):
                            cang__lrvs = epjwk__ugtw.copy(readonly=False)
                            mvwf__cqqqm = pifo__vtbd.copy(readonly=False)
                            if cang__lrvs == mvwf__cqqqm:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), nnyye__wgh.target, jdlt__kdhnq)
                                continue
                        if (pifo__vtbd != epjwk__ugtw and 
                            to_str_arr_if_dict_array(pifo__vtbd) ==
                            to_str_arr_if_dict_array(epjwk__ugtw)):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), nnyye__wgh.target,
                                jdlt__kdhnq, extra_globals={
                                'decode_if_dict_array': decode_if_dict_array})
                            continue
                        else:
                            nnyye__wgh.value = rhs.args[0]
                    new_body.append(nnyye__wgh)
                else:
                    new_body.append(nnyye__wgh)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        vdek__vop = TableColumnDelPass(state.func_ir, state.typingctx,
            state.targetctx, state.typemap, state.calltypes)
        return vdek__vop.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    yyg__qivf = set()
    while work_list:
        iec__ggxnb, block = work_list.pop()
        yyg__qivf.add(iec__ggxnb)
        for i, iptrj__dtj in enumerate(block.body):
            if isinstance(iptrj__dtj, ir.Assign):
                yitlm__lrzox = iptrj__dtj.value
                if isinstance(yitlm__lrzox, ir.Expr
                    ) and yitlm__lrzox.op == 'call':
                    ofd__ltrc = guard(get_definition, func_ir, yitlm__lrzox
                        .func)
                    if isinstance(ofd__ltrc, (ir.Global, ir.FreeVar)
                        ) and isinstance(ofd__ltrc.value, CPUDispatcher
                        ) and issubclass(ofd__ltrc.value._compiler.
                        pipeline_class, BodoCompiler):
                        ouv__yhxpv = ofd__ltrc.value.py_func
                        arg_types = None
                        if typingctx:
                            xxrai__tqd = dict(yitlm__lrzox.kws)
                            hxyr__hweee = tuple(typemap[bdql__eqig.name] for
                                bdql__eqig in yitlm__lrzox.args)
                            wrd__plb = {lecu__sxq: typemap[bdql__eqig.name] for
                                lecu__sxq, bdql__eqig in xxrai__tqd.items()}
                            ghx__guuo, arg_types = (ofd__ltrc.value.
                                fold_argument_types(hxyr__hweee, wrd__plb))
                        ghx__guuo, dkd__vfj = inline_closure_call(func_ir,
                            ouv__yhxpv.__globals__, block, i, ouv__yhxpv,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((dkd__vfj[lecu__sxq].name,
                            bdql__eqig) for lecu__sxq, bdql__eqig in
                            ofd__ltrc.value.locals.items() if lecu__sxq in
                            dkd__vfj)
                        break
    return yyg__qivf


def udf_jit(signature_or_function=None, **options):
    ovv__ced = {'comprehension': True, 'setitem': False, 'inplace_binop': 
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    return numba.njit(signature_or_function, parallel=ovv__ced,
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
    for nkwc__kxrx, (uaes__pda, ghx__guuo) in enumerate(pm.passes):
        if uaes__pda == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:nkwc__kxrx + 1]
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
    ntwoa__nva = None
    fimdh__ixm = None
    _locals = {}
    cktk__pgv = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(cktk__pgv, arg_types,
        kw_types)
    xof__teh = numba.core.compiler.Flags()
    mmkfm__skrht = {'comprehension': True, 'setitem': False,
        'inplace_binop': False, 'reduction': True, 'numpy': True, 'stencil':
        False, 'fusion': True}
    bhhlq__qokg = {'nopython': True, 'boundscheck': False, 'parallel':
        mmkfm__skrht}
    numba.core.registry.cpu_target.options.parse_as_flags(xof__teh, bhhlq__qokg
        )
    ncg__brxmx = TyperCompiler(typingctx, targetctx, ntwoa__nva, args,
        fimdh__ixm, xof__teh, _locals)
    return ncg__brxmx.compile_extra(func)
