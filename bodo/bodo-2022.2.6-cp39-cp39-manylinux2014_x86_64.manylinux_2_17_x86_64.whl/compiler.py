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
        vrgyi__qhulj = 'bodo' if distributed else 'bodo_seq'
        vrgyi__qhulj = (vrgyi__qhulj + '_inline' if inline_calls_pass else
            vrgyi__qhulj)
        pm = DefaultPassBuilder.define_nopython_pipeline(self.state,
            vrgyi__qhulj)
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
    for xyp__bla, (twv__wnj, kty__wlll) in enumerate(pm.passes):
        if twv__wnj == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.insert(xyp__bla, (pass_cls, str(pass_cls)))
    pm._finalized = False


def replace_pass(pm, pass_cls, location):
    assert pm.passes
    pm._validate_pass(pass_cls)
    pm._validate_pass(location)
    for xyp__bla, (twv__wnj, kty__wlll) in enumerate(pm.passes):
        if twv__wnj == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes[xyp__bla] = pass_cls, str(pass_cls)
    pm._finalized = False


def remove_pass(pm, location):
    assert pm.passes
    pm._validate_pass(location)
    for xyp__bla, (twv__wnj, kty__wlll) in enumerate(pm.passes):
        if twv__wnj == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes.pop(xyp__bla)
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
    dgtgq__pqc = guard(get_definition, func_ir, rhs.func)
    if isinstance(dgtgq__pqc, (ir.Global, ir.FreeVar, ir.Const)):
        ospry__wtmd = dgtgq__pqc.value
    else:
        omgd__ehhmo = guard(find_callname, func_ir, rhs)
        if not (omgd__ehhmo and isinstance(omgd__ehhmo[0], str) and
            isinstance(omgd__ehhmo[1], str)):
            return
        func_name, func_mod = omgd__ehhmo
        try:
            import importlib
            hck__rohs = importlib.import_module(func_mod)
            ospry__wtmd = getattr(hck__rohs, func_name)
        except:
            return
    if isinstance(ospry__wtmd, CPUDispatcher) and issubclass(ospry__wtmd.
        _compiler.pipeline_class, BodoCompiler
        ) and ospry__wtmd._compiler.pipeline_class != BodoCompilerUDF:
        ospry__wtmd._compiler.pipeline_class = BodoCompilerUDF
        ospry__wtmd.recompile()


@register_pass(mutates_CFG=True, analysis_only=False)
class ConvertCallsUDFPass(FunctionPass):
    _name = 'inline_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        for block in state.func_ir.blocks.values():
            for icb__ucz in block.body:
                if is_call_assign(icb__ucz):
                    _convert_bodo_dispatcher_to_udf(icb__ucz.value, state.
                        func_ir)
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoUntypedPass(FunctionPass):
    _name = 'bodo_untyped_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        uwu__vqfph = UntypedPass(state.func_ir, state.typingctx, state.args,
            state.locals, state.metadata, state.flags)
        uwu__vqfph.run()
        return True


def _update_definitions(func_ir, node_list):
    rookc__zbfk = ir.Loc('', 0)
    wqtj__jdh = ir.Block(ir.Scope(None, rookc__zbfk), rookc__zbfk)
    wqtj__jdh.body = node_list
    build_definitions({(0): wqtj__jdh}, func_ir._definitions)


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
        ymuy__ebwy = 'overload_series_' + rhs.attr
        wud__zqn = getattr(bodo.hiframes.series_impl, ymuy__ebwy)
    if isinstance(rhs_type, DataFrameType) and rhs.attr in ('index', 'columns'
        ):
        ymuy__ebwy = 'overload_dataframe_' + rhs.attr
        wud__zqn = getattr(bodo.hiframes.dataframe_impl, ymuy__ebwy)
    else:
        return False
    func_ir._definitions[stmt.target.name].remove(rhs)
    oyz__juqx = wud__zqn(rhs_type)
    xkd__logd = TypingInfo(typingctx, targetctx, typemap, calltypes, stmt.loc)
    rxiwg__atdh = compile_func_single_block(oyz__juqx, (rhs.value,), stmt.
        target, xkd__logd)
    _update_definitions(func_ir, rxiwg__atdh)
    new_body += rxiwg__atdh
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
        fvwpe__emz = tuple(typemap[myrbn__miz.name] for myrbn__miz in rhs.args)
        xmzts__avw = {vrgyi__qhulj: typemap[myrbn__miz.name] for 
            vrgyi__qhulj, myrbn__miz in dict(rhs.kws).items()}
        oyz__juqx = getattr(bodo.hiframes.series_impl, 'overload_series_' +
            func_name)(*fvwpe__emz, **xmzts__avw)
    elif isinstance(func_mod, ir.Var) and isinstance(typemap[func_mod.name],
        DataFrameType) and func_name not in _dataframe_no_inline_methods:
        if func_name in _series_method_alias:
            func_name = _series_method_alias[func_name]
        rhs.args.insert(0, func_mod)
        fvwpe__emz = tuple(typemap[myrbn__miz.name] for myrbn__miz in rhs.args)
        xmzts__avw = {vrgyi__qhulj: typemap[myrbn__miz.name] for 
            vrgyi__qhulj, myrbn__miz in dict(rhs.kws).items()}
        oyz__juqx = getattr(bodo.hiframes.dataframe_impl, 
            'overload_dataframe_' + func_name)(*fvwpe__emz, **xmzts__avw)
    else:
        return False
    jbd__awwcm = replace_func(pass_info, oyz__juqx, rhs.args, pysig=numba.
        core.utils.pysignature(oyz__juqx), kws=dict(rhs.kws))
    block.body = new_body + block.body[i:]
    lox__vwobc, kty__wlll = inline_closure_call(func_ir, jbd__awwcm.glbls,
        block, len(new_body), jbd__awwcm.func, typingctx=typingctx,
        targetctx=targetctx, arg_typs=jbd__awwcm.arg_types, typemap=typemap,
        calltypes=calltypes, work_list=work_list)
    for bjgwb__oiz in lox__vwobc.values():
        bjgwb__oiz.loc = rhs.loc
        update_locs(bjgwb__oiz.body, rhs.loc)
    return True


def bodo_overload_inline_pass(func_ir, typingctx, targetctx, typemap, calltypes
    ):
    bwuj__lqqw = namedtuple('PassInfo', ['func_ir', 'typemap'])
    pass_info = bwuj__lqqw(func_ir, typemap)
    jbiua__nkl = func_ir.blocks
    work_list = list((vqqvp__idye, jbiua__nkl[vqqvp__idye]) for vqqvp__idye in
        reversed(jbiua__nkl.keys()))
    while work_list:
        tfw__olzm, block = work_list.pop()
        new_body = []
        umqw__bgj = False
        for i, stmt in enumerate(block.body):
            if is_assign(stmt) and is_expr(stmt.value, 'getattr'):
                rhs = stmt.value
                rhs_type = typemap[rhs.value.name]
                if _inline_bodo_getattr(stmt, rhs, rhs_type, new_body,
                    func_ir, typingctx, targetctx, typemap, calltypes):
                    continue
            if is_call_assign(stmt):
                rhs = stmt.value
                omgd__ehhmo = guard(find_callname, func_ir, rhs, typemap)
                if omgd__ehhmo is None:
                    new_body.append(stmt)
                    continue
                func_name, func_mod = omgd__ehhmo
                if _inline_bodo_call(rhs, i, func_mod, func_name, pass_info,
                    new_body, block, typingctx, targetctx, calltypes, work_list
                    ):
                    umqw__bgj = True
                    break
            new_body.append(stmt)
        if not umqw__bgj:
            jbiua__nkl[tfw__olzm].body = new_body
    func_ir.blocks = ir_utils.simplify_CFG(func_ir.blocks)


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoDistributedPass(FunctionPass):
    _name = 'bodo_distributed_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        from bodo.transforms.distributed_pass import DistributedPass
        cdgw__spuvy = DistributedPass(state.func_ir, state.typingctx, state
            .targetctx, state.typemap, state.calltypes, state.return_type,
            state.metadata, state.flags)
        state.return_type = cdgw__spuvy.run()
        return True


@register_pass(mutates_CFG=True, analysis_only=False)
class BodoSeriesPass(FunctionPass):
    _name = 'bodo_series_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        assert state.func_ir
        afebh__qwotb = SeriesPass(state.func_ir, state.typingctx, state.
            targetctx, state.typemap, state.calltypes, state.locals)
        afebh__qwotb.run()
        afebh__qwotb.run()
        afebh__qwotb.run()
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoDumpDistDiagnosticsPass(AnalysisPass):
    _name = 'bodo_dump_diagnostics_pass'

    def __init__(self):
        AnalysisPass.__init__(self)

    def run_pass(self, state):
        aaw__eebvm = 0
        qsu__czdyn = 'BODO_DISTRIBUTED_DIAGNOSTICS'
        try:
            aaw__eebvm = int(os.environ[qsu__czdyn])
        except:
            pass
        if aaw__eebvm > 0 and 'distributed_diagnostics' in state.metadata:
            state.metadata['distributed_diagnostics'].dump(aaw__eebvm,
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
        xkd__logd = TypingInfo(state.typingctx, state.targetctx, state.
            typemap, state.calltypes, state.func_ir.loc)
        remove_dead_table_columns(state.func_ir, state.typemap, xkd__logd)
        for block in state.func_ir.blocks.values():
            new_body = []
            for icb__ucz in block.body:
                if type(icb__ucz) in distributed_run_extensions:
                    tzwx__lne = distributed_run_extensions[type(icb__ucz)]
                    ylci__jpa = tzwx__lne(icb__ucz, None, state.typemap,
                        state.calltypes, state.typingctx, state.targetctx)
                    new_body += ylci__jpa
                elif is_call_assign(icb__ucz):
                    rhs = icb__ucz.value
                    omgd__ehhmo = guard(find_callname, state.func_ir, rhs)
                    if omgd__ehhmo == ('gatherv', 'bodo') or omgd__ehhmo == (
                        'allgatherv', 'bodo'):
                        pka__tlx = state.typemap[icb__ucz.target.name]
                        swkrp__xfr = state.typemap[rhs.args[0].name]
                        if isinstance(swkrp__xfr, types.Array) and isinstance(
                            pka__tlx, types.Array):
                            wckd__urd = swkrp__xfr.copy(readonly=False)
                            orel__vurx = pka__tlx.copy(readonly=False)
                            if wckd__urd == orel__vurx:
                                new_body += compile_func_single_block(eval(
                                    'lambda data: data.copy()'), (rhs.args[
                                    0],), icb__ucz.target, xkd__logd)
                                continue
                        if pka__tlx != swkrp__xfr and to_str_arr_if_dict_array(
                            pka__tlx) == to_str_arr_if_dict_array(swkrp__xfr):
                            new_body += compile_func_single_block(eval(
                                'lambda data: decode_if_dict_array(data)'),
                                (rhs.args[0],), icb__ucz.target, xkd__logd,
                                extra_globals={'decode_if_dict_array':
                                decode_if_dict_array})
                            continue
                        else:
                            icb__ucz.value = rhs.args[0]
                    new_body.append(icb__ucz)
                else:
                    new_body.append(icb__ucz)
            block.body = new_body
        return True


@register_pass(mutates_CFG=False, analysis_only=True)
class BodoTableColumnDelPass(AnalysisPass):
    _name = 'bodo_table_column_del_pass'

    def __init__(self):
        FunctionPass.__init__(self)

    def run_pass(self, state):
        qcw__pfi = TableColumnDelPass(state.func_ir, state.typingctx, state
            .targetctx, state.typemap, state.calltypes)
        return qcw__pfi.run()


def inline_calls(func_ir, _locals, work_list=None, typingctx=None,
    targetctx=None, typemap=None, calltypes=None):
    if work_list is None:
        work_list = list(func_ir.blocks.items())
    eeu__ufoj = set()
    while work_list:
        tfw__olzm, block = work_list.pop()
        eeu__ufoj.add(tfw__olzm)
        for i, zrfiw__njl in enumerate(block.body):
            if isinstance(zrfiw__njl, ir.Assign):
                ynvl__kpfy = zrfiw__njl.value
                if isinstance(ynvl__kpfy, ir.Expr) and ynvl__kpfy.op == 'call':
                    dgtgq__pqc = guard(get_definition, func_ir, ynvl__kpfy.func
                        )
                    if isinstance(dgtgq__pqc, (ir.Global, ir.FreeVar)
                        ) and isinstance(dgtgq__pqc.value, CPUDispatcher
                        ) and issubclass(dgtgq__pqc.value._compiler.
                        pipeline_class, BodoCompiler):
                        vfd__pxhdx = dgtgq__pqc.value.py_func
                        arg_types = None
                        if typingctx:
                            wodd__kicdz = dict(ynvl__kpfy.kws)
                            uax__aczpj = tuple(typemap[myrbn__miz.name] for
                                myrbn__miz in ynvl__kpfy.args)
                            ckwi__djs = {mcg__hkr: typemap[myrbn__miz.name] for
                                mcg__hkr, myrbn__miz in wodd__kicdz.items()}
                            kty__wlll, arg_types = (dgtgq__pqc.value.
                                fold_argument_types(uax__aczpj, ckwi__djs))
                        kty__wlll, jic__lcql = inline_closure_call(func_ir,
                            vfd__pxhdx.__globals__, block, i, vfd__pxhdx,
                            typingctx=typingctx, targetctx=targetctx,
                            arg_typs=arg_types, typemap=typemap, calltypes=
                            calltypes, work_list=work_list)
                        _locals.update((jic__lcql[mcg__hkr].name,
                            myrbn__miz) for mcg__hkr, myrbn__miz in
                            dgtgq__pqc.value.locals.items() if mcg__hkr in
                            jic__lcql)
                        break
    return eeu__ufoj


def udf_jit(signature_or_function=None, **options):
    sbwvn__ldkfc = {'comprehension': True, 'setitem': False,
        'inplace_binop': False, 'reduction': True, 'numpy': True, 'stencil':
        False, 'fusion': True}
    return numba.njit(signature_or_function, parallel=sbwvn__ldkfc,
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
    for xyp__bla, (twv__wnj, kty__wlll) in enumerate(pm.passes):
        if twv__wnj == location:
            break
    else:
        raise bodo.utils.typing.BodoError('Could not find pass %s' % location)
    pm.passes = pm.passes[:xyp__bla + 1]
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
    pmxt__plul = None
    ffoo__adrhv = None
    _locals = {}
    yakq__quhw = numba.core.utils.pysignature(func)
    args = bodo.utils.transform.fold_argument_types(yakq__quhw, arg_types,
        kw_types)
    zrs__kwtfv = numba.core.compiler.Flags()
    ybck__dyy = {'comprehension': True, 'setitem': False, 'inplace_binop': 
        False, 'reduction': True, 'numpy': True, 'stencil': False, 'fusion':
        True}
    tglo__xvhvn = {'nopython': True, 'boundscheck': False, 'parallel':
        ybck__dyy}
    numba.core.registry.cpu_target.options.parse_as_flags(zrs__kwtfv,
        tglo__xvhvn)
    ijm__qxus = TyperCompiler(typingctx, targetctx, pmxt__plul, args,
        ffoo__adrhv, zrs__kwtfv, _locals)
    return ijm__qxus.compile_extra(func)
