"""
Numba monkey patches to fix issues related to Bodo. Should be imported before any
other module in bodo package.
"""
import copy
import functools
import hashlib
import inspect
import itertools
import operator
import os
import re
import sys
import textwrap
import traceback
import types as pytypes
import warnings
from collections import OrderedDict
from collections.abc import Sequence
from contextlib import ExitStack
import numba
import numba.core.boxing
import numba.core.inline_closurecall
import numba.core.typing.listdecl
import numba.np.linalg
from numba.core import analysis, cgutils, errors, ir, ir_utils, types
from numba.core.compiler import Compiler
from numba.core.errors import ForceLiteralArg, LiteralTypingError, TypingError
from numba.core.ir_utils import GuardException, _create_function_from_code_obj, analysis, build_definitions, find_callname, guard, has_no_side_effect, mk_unique_var, remove_dead_extensions, replace_vars_inner, require, visit_vars_extensions, visit_vars_inner
from numba.core.types import literal
from numba.core.types.functions import _bt_as_lines, _ResolutionFailures, _termcolor, _unlit_non_poison
from numba.core.typing.templates import AbstractTemplate, Signature, _EmptyImplementationEntry, _inline_info, _OverloadAttributeTemplate, infer_global, signature
from numba.core.typing.typeof import Purpose, typeof
from numba.experimental.jitclass import base as jitclass_base
from numba.experimental.jitclass import decorators as jitclass_decorators
from numba.extending import NativeValue, lower_builtin, typeof_impl
from numba.parfors.parfor import get_expr_args
from bodo.utils.typing import BodoError, get_overload_const_str, is_overload_constant_str, raise_bodo_error
_check_numba_change = False
numba.core.typing.templates._IntrinsicTemplate.prefer_literal = True


def run_frontend(func, inline_closures=False, emit_dels=False):
    ccl__ycfow = numba.core.bytecode.FunctionIdentity.from_function(func)
    wpdz__zwr = numba.core.interpreter.Interpreter(ccl__ycfow)
    lemt__liwuc = numba.core.bytecode.ByteCode(func_id=ccl__ycfow)
    func_ir = wpdz__zwr.interpret(lemt__liwuc)
    if inline_closures:
        from numba.core.inline_closurecall import InlineClosureCallPass


        class DummyPipeline:

            def __init__(self, f_ir):
                self.state = numba.core.compiler.StateDict()
                self.state.typingctx = None
                self.state.targetctx = None
                self.state.args = None
                self.state.func_ir = f_ir
                self.state.typemap = None
                self.state.return_type = None
                self.state.calltypes = None
        numba.core.rewrites.rewrite_registry.apply('before-inference',
            DummyPipeline(func_ir).state)
        jqetv__hol = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        jqetv__hol.run()
    juava__yzm = numba.core.postproc.PostProcessor(func_ir)
    juava__yzm.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, aamar__fpq in visit_vars_extensions.items():
        if isinstance(stmt, t):
            aamar__fpq(stmt, callback, cbdata)
            return
    if isinstance(stmt, ir.Assign):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.value = visit_vars_inner(stmt.value, callback, cbdata)
    elif isinstance(stmt, ir.Arg):
        stmt.name = visit_vars_inner(stmt.name, callback, cbdata)
    elif isinstance(stmt, ir.Return):
        stmt.value = visit_vars_inner(stmt.value, callback, cbdata)
    elif isinstance(stmt, ir.Raise):
        stmt.exception = visit_vars_inner(stmt.exception, callback, cbdata)
    elif isinstance(stmt, ir.Branch):
        stmt.cond = visit_vars_inner(stmt.cond, callback, cbdata)
    elif isinstance(stmt, ir.Jump):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
    elif isinstance(stmt, ir.Del):
        var = ir.Var(None, stmt.value, stmt.loc)
        var = visit_vars_inner(var, callback, cbdata)
        stmt.value = var.name
    elif isinstance(stmt, ir.DelAttr):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.attr = visit_vars_inner(stmt.attr, callback, cbdata)
    elif isinstance(stmt, ir.SetAttr):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.attr = visit_vars_inner(stmt.attr, callback, cbdata)
        stmt.value = visit_vars_inner(stmt.value, callback, cbdata)
    elif isinstance(stmt, ir.DelItem):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.index = visit_vars_inner(stmt.index, callback, cbdata)
    elif isinstance(stmt, ir.StaticSetItem):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.index_var = visit_vars_inner(stmt.index_var, callback, cbdata)
        stmt.value = visit_vars_inner(stmt.value, callback, cbdata)
    elif isinstance(stmt, ir.SetItem):
        stmt.target = visit_vars_inner(stmt.target, callback, cbdata)
        stmt.index = visit_vars_inner(stmt.index, callback, cbdata)
        stmt.value = visit_vars_inner(stmt.value, callback, cbdata)
    elif isinstance(stmt, ir.Print):
        stmt.args = [visit_vars_inner(x, callback, cbdata) for x in stmt.args]
        stmt.vararg = visit_vars_inner(stmt.vararg, callback, cbdata)
    else:
        pass
    return


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.visit_vars_stmt)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '52b7b645ba65c35f3cf564f936e113261db16a2dff1e80fbee2459af58844117':
        warnings.warn('numba.core.ir_utils.visit_vars_stmt has changed')
numba.core.ir_utils.visit_vars_stmt = visit_vars_stmt
old_run_pass = numba.core.typed_passes.InlineOverloads.run_pass


def InlineOverloads_run_pass(self, state):
    import bodo
    bodo.compiler.bodo_overload_inline_pass(state.func_ir, state.typingctx,
        state.targetctx, state.typemap, state.calltypes)
    return old_run_pass(self, state)


numba.core.typed_passes.InlineOverloads.run_pass = InlineOverloads_run_pass
from numba.core.ir_utils import _add_alias, alias_analysis_extensions, alias_func_extensions
_immutable_type_class = (types.Number, types.scalars._NPDatetimeBase, types
    .iterators.RangeType, types.UnicodeType)


def is_immutable_type(var, typemap):
    if typemap is None or var not in typemap:
        return False
    typ = typemap[var]
    if isinstance(typ, _immutable_type_class):
        return True
    if isinstance(typ, types.BaseTuple) and all(isinstance(t,
        _immutable_type_class) for t in typ.types):
        return True
    return False


def find_potential_aliases(blocks, args, typemap, func_ir, alias_map=None,
    arg_aliases=None):
    if alias_map is None:
        alias_map = {}
    if arg_aliases is None:
        arg_aliases = set(a for a in args if not is_immutable_type(a, typemap))
    func_ir._definitions = build_definitions(func_ir.blocks)
    mlpg__bsi = ['ravel', 'transpose', 'reshape']
    for dghd__ojw in blocks.values():
        for bai__kuuv in dghd__ojw.body:
            if type(bai__kuuv) in alias_analysis_extensions:
                aamar__fpq = alias_analysis_extensions[type(bai__kuuv)]
                aamar__fpq(bai__kuuv, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(bai__kuuv, ir.Assign):
                uxdtc__lesvs = bai__kuuv.value
                grt__zmtom = bai__kuuv.target.name
                if is_immutable_type(grt__zmtom, typemap):
                    continue
                if isinstance(uxdtc__lesvs, ir.Var
                    ) and grt__zmtom != uxdtc__lesvs.name:
                    _add_alias(grt__zmtom, uxdtc__lesvs.name, alias_map,
                        arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr) and (uxdtc__lesvs.op ==
                    'cast' or uxdtc__lesvs.op in ['getitem', 'static_getitem']
                    ):
                    _add_alias(grt__zmtom, uxdtc__lesvs.value.name,
                        alias_map, arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr
                    ) and uxdtc__lesvs.op == 'inplace_binop':
                    _add_alias(grt__zmtom, uxdtc__lesvs.lhs.name, alias_map,
                        arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr
                    ) and uxdtc__lesvs.op == 'getattr' and uxdtc__lesvs.attr in [
                    'T', 'ctypes', 'flat']:
                    _add_alias(grt__zmtom, uxdtc__lesvs.value.name,
                        alias_map, arg_aliases)
                if (isinstance(uxdtc__lesvs, ir.Expr) and uxdtc__lesvs.op ==
                    'getattr' and uxdtc__lesvs.attr not in ['shape'] and 
                    uxdtc__lesvs.value.name in arg_aliases):
                    _add_alias(grt__zmtom, uxdtc__lesvs.value.name,
                        alias_map, arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr
                    ) and uxdtc__lesvs.op == 'getattr' and uxdtc__lesvs.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(grt__zmtom, uxdtc__lesvs.value.name,
                        alias_map, arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr) and uxdtc__lesvs.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(grt__zmtom, typemap):
                    for qof__xek in uxdtc__lesvs.items:
                        _add_alias(grt__zmtom, qof__xek.name, alias_map,
                            arg_aliases)
                if isinstance(uxdtc__lesvs, ir.Expr
                    ) and uxdtc__lesvs.op == 'call':
                    zfarx__qdimu = guard(find_callname, func_ir,
                        uxdtc__lesvs, typemap)
                    if zfarx__qdimu is None:
                        continue
                    vnghe__rojci, wky__xjc = zfarx__qdimu
                    if zfarx__qdimu in alias_func_extensions:
                        qooo__cjo = alias_func_extensions[zfarx__qdimu]
                        qooo__cjo(grt__zmtom, uxdtc__lesvs.args, alias_map,
                            arg_aliases)
                    if wky__xjc == 'numpy' and vnghe__rojci in mlpg__bsi:
                        _add_alias(grt__zmtom, uxdtc__lesvs.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(wky__xjc, ir.Var
                        ) and vnghe__rojci in mlpg__bsi:
                        _add_alias(grt__zmtom, wky__xjc.name, alias_map,
                            arg_aliases)
    btis__jldt = copy.deepcopy(alias_map)
    for qof__xek in btis__jldt:
        for rwdh__hti in btis__jldt[qof__xek]:
            alias_map[qof__xek] |= alias_map[rwdh__hti]
        for rwdh__hti in btis__jldt[qof__xek]:
            alias_map[rwdh__hti] = alias_map[qof__xek]
    return alias_map, arg_aliases


if _check_numba_change:
    lines = inspect.getsource(ir_utils.find_potential_aliases)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'e6cf3e0f502f903453eb98346fc6854f87dc4ea1ac62f65c2d6aef3bf690b6c5':
        warnings.warn('ir_utils.find_potential_aliases has changed')
ir_utils.find_potential_aliases = find_potential_aliases
numba.parfors.array_analysis.find_potential_aliases = find_potential_aliases
if _check_numba_change:
    lines = inspect.getsource(ir_utils.dead_code_elimination)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '40a8626300a1a17523944ec7842b093c91258bbc60844bbd72191a35a4c366bf':
        warnings.warn('ir_utils.dead_code_elimination has changed')


def mini_dce(func_ir, typemap=None, alias_map=None, arg_aliases=None):
    from numba.core.analysis import compute_cfg_from_blocks, compute_live_map, compute_use_defs
    ruuy__fqfjd = compute_cfg_from_blocks(func_ir.blocks)
    anhbl__jqft = compute_use_defs(func_ir.blocks)
    awbmw__zko = compute_live_map(ruuy__fqfjd, func_ir.blocks, anhbl__jqft.
        usemap, anhbl__jqft.defmap)
    elk__ajco = True
    while elk__ajco:
        elk__ajco = False
        for xkm__pkbtr, block in func_ir.blocks.items():
            lives = {qof__xek.name for qof__xek in block.terminator.list_vars()
                }
            for rrjx__dtgwt, wsevo__suzc in ruuy__fqfjd.successors(xkm__pkbtr):
                lives |= awbmw__zko[rrjx__dtgwt]
            pwxq__qbd = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    grt__zmtom = stmt.target
                    yvdm__smwjs = stmt.value
                    if grt__zmtom.name not in lives:
                        if isinstance(yvdm__smwjs, ir.Expr
                            ) and yvdm__smwjs.op == 'make_function':
                            continue
                        if isinstance(yvdm__smwjs, ir.Expr
                            ) and yvdm__smwjs.op == 'getattr':
                            continue
                        if isinstance(yvdm__smwjs, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(grt__zmtom,
                            None), types.Function):
                            continue
                        if isinstance(yvdm__smwjs, ir.Expr
                            ) and yvdm__smwjs.op == 'build_map':
                            continue
                    if isinstance(yvdm__smwjs, ir.Var
                        ) and grt__zmtom.name == yvdm__smwjs.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    kkrn__okn = analysis.ir_extension_usedefs[type(stmt)]
                    wxfpb__wau, ncg__hnu = kkrn__okn(stmt)
                    lives -= ncg__hnu
                    lives |= wxfpb__wau
                else:
                    lives |= {qof__xek.name for qof__xek in stmt.list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(grt__zmtom.name)
                pwxq__qbd.append(stmt)
            pwxq__qbd.reverse()
            if len(block.body) != len(pwxq__qbd):
                elk__ajco = True
            block.body = pwxq__qbd


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    secsn__lfi = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (secsn__lfi,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    mkrk__xqhbt = dict(key=func, _overload_func=staticmethod(overload_func),
        _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), mkrk__xqhbt)


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.
        make_overload_template)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '7f6974584cb10e49995b652827540cc6732e497c0b9f8231b44fd83fcc1c0a83':
        warnings.warn(
            'numba.core.typing.templates.make_overload_template has changed')
numba.core.typing.templates.make_overload_template = make_overload_template


def _resolve(self, typ, attr):
    if self._attr != attr:
        return None
    if isinstance(typ, types.TypeRef):
        assert typ == self.key
    else:
        assert isinstance(typ, self.key)


    class MethodTemplate(AbstractTemplate):
        key = self.key, attr
        _inline = self._inline
        _no_unliteral = getattr(self, '_no_unliteral', False)
        _overload_func = staticmethod(self._overload_func)
        _inline_overloads = self._inline_overloads
        prefer_literal = self.prefer_literal

        def generic(_, args, kws):
            args = (typ,) + tuple(args)
            fnty = self._get_function_type(self.context, typ)
            sig = self._get_signature(self.context, fnty, args, kws)
            sig = sig.replace(pysig=numba.core.utils.pysignature(self.
                _overload_func))
            for uqxb__viqj in fnty.templates:
                self._inline_overloads.update(uqxb__viqj._inline_overloads)
            if sig is not None:
                return sig.as_method()
    return types.BoundFunction(MethodTemplate, typ)


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.
        _OverloadMethodTemplate._resolve)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'ce8e0935dc939d0867ef969e1ed2975adb3533a58a4133fcc90ae13c4418e4d6':
        warnings.warn(
            'numba.core.typing.templates._OverloadMethodTemplate._resolve has changed'
            )
numba.core.typing.templates._OverloadMethodTemplate._resolve = _resolve


def make_overload_attribute_template(typ, attr, overload_func, inline,
    prefer_literal=False, base=_OverloadAttributeTemplate, **kwargs):
    assert isinstance(typ, types.Type) or issubclass(typ, types.Type)
    name = 'OverloadAttributeTemplate_%s_%s' % (typ, attr)
    no_unliteral = kwargs.pop('no_unliteral', False)
    mkrk__xqhbt = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), mkrk__xqhbt)
    return obj


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.
        make_overload_attribute_template)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'f066c38c482d6cf8bf5735a529c3264118ba9b52264b24e58aad12a6b1960f5d':
        warnings.warn(
            'numba.core.typing.templates.make_overload_attribute_template has changed'
            )
numba.core.typing.templates.make_overload_attribute_template = (
    make_overload_attribute_template)


def generic(self, args, kws):
    from numba.core.typed_passes import PreLowerStripPhis
    ejy__nnlnv, afac__yjy = self._get_impl(args, kws)
    if ejy__nnlnv is None:
        return
    dlcdn__smc = types.Dispatcher(ejy__nnlnv)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        obapf__ywjot = ejy__nnlnv._compiler
        flags = compiler.Flags()
        nqhd__jiuje = obapf__ywjot.targetdescr.typing_context
        niny__mhjl = obapf__ywjot.targetdescr.target_context
        zpf__sazen = obapf__ywjot.pipeline_class(nqhd__jiuje, niny__mhjl,
            None, None, None, flags, None)
        pyrdp__rjiw = InlineWorker(nqhd__jiuje, niny__mhjl, obapf__ywjot.
            locals, zpf__sazen, flags, None)
        ztfi__kzwl = dlcdn__smc.dispatcher.get_call_template
        uqxb__viqj, txajb__sxef, poxp__pcf, kws = ztfi__kzwl(afac__yjy, kws)
        if poxp__pcf in self._inline_overloads:
            return self._inline_overloads[poxp__pcf]['iinfo'].signature
        ir = pyrdp__rjiw.run_untyped_passes(dlcdn__smc.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, niny__mhjl, ir, poxp__pcf, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, poxp__pcf, None)
        self._inline_overloads[sig.args] = {'folded_args': poxp__pcf}
        xuwiz__ixxq = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = xuwiz__ixxq
        if not self._inline.is_always_inline:
            sig = dlcdn__smc.get_call_type(self.context, afac__yjy, kws)
            self._compiled_overloads[sig.args] = dlcdn__smc.get_overload(sig)
        ypt__dtu = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': poxp__pcf,
            'iinfo': ypt__dtu}
    else:
        sig = dlcdn__smc.get_call_type(self.context, afac__yjy, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = dlcdn__smc.get_overload(sig)
    return sig


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.
        _OverloadFunctionTemplate.generic)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5d453a6d0215ebf0bab1279ff59eb0040b34938623be99142ce20acc09cdeb64':
        warnings.warn(
            'numba.core.typing.templates._OverloadFunctionTemplate.generic has changed'
            )
numba.core.typing.templates._OverloadFunctionTemplate.generic = generic


def bound_function(template_key, no_unliteral=False):

    def wrapper(method_resolver):

        @functools.wraps(method_resolver)
        def attribute_resolver(self, ty):


            class MethodTemplate(AbstractTemplate):
                key = template_key

                def generic(_, args, kws):
                    sig = method_resolver(self, ty, args, kws)
                    if sig is not None and sig.recvr is None:
                        sig = sig.replace(recvr=ty)
                    return sig
            MethodTemplate._no_unliteral = no_unliteral
            return types.BoundFunction(MethodTemplate, ty)
        return attribute_resolver
    return wrapper


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.bound_function)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a2feefe64eae6a15c56affc47bf0c1d04461f9566913442d539452b397103322':
        warnings.warn('numba.core.typing.templates.bound_function has changed')
numba.core.typing.templates.bound_function = bound_function


def get_call_type(self, context, args, kws):
    from numba.core import utils
    jhdtc__aqvju = [True, False]
    nfluq__hot = [False, True]
    icmd__kxbfv = _ResolutionFailures(context, self, args, kws, depth=self.
        _depth)
    from numba.core.target_extension import get_local_target
    lxn__fmv = get_local_target(context)
    swlz__glis = utils.order_by_target_specificity(lxn__fmv, self.templates,
        fnkey=self.key[0])
    self._depth += 1
    for tqb__cabwm in swlz__glis:
        xoy__rbzcg = tqb__cabwm(context)
        fzud__zcx = jhdtc__aqvju if xoy__rbzcg.prefer_literal else nfluq__hot
        fzud__zcx = [True] if getattr(xoy__rbzcg, '_no_unliteral', False
            ) else fzud__zcx
        for vvvxo__vacw in fzud__zcx:
            try:
                if vvvxo__vacw:
                    sig = xoy__rbzcg.apply(args, kws)
                else:
                    nau__rmf = tuple([_unlit_non_poison(a) for a in args])
                    mdqc__rddy = {maxo__nqq: _unlit_non_poison(qof__xek) for
                        maxo__nqq, qof__xek in kws.items()}
                    sig = xoy__rbzcg.apply(nau__rmf, mdqc__rddy)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    icmd__kxbfv.add_error(xoy__rbzcg, False, e, vvvxo__vacw)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = xoy__rbzcg.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    bbycq__dpllx = getattr(xoy__rbzcg, 'cases', None)
                    if bbycq__dpllx is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            bbycq__dpllx)
                    else:
                        msg = 'No match.'
                    icmd__kxbfv.add_error(xoy__rbzcg, True, msg, vvvxo__vacw)
    icmd__kxbfv.raise_error()


if _check_numba_change:
    lines = inspect.getsource(numba.core.types.functions.BaseFunction.
        get_call_type)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '25f038a7216f8e6f40068ea81e11fd9af8ad25d19888f7304a549941b01b7015':
        warnings.warn(
            'numba.core.types.functions.BaseFunction.get_call_type has changed'
            )
numba.core.types.functions.BaseFunction.get_call_type = get_call_type
bodo_typing_error_info = """
This is often caused by the use of unsupported features or typing issues.
See https://docs.bodo.ai/
"""


def get_call_type2(self, context, args, kws):
    uqxb__viqj = self.template(context)
    krns__cqtl = None
    fiqbp__ohl = None
    uadm__hgy = None
    fzud__zcx = [True, False] if uqxb__viqj.prefer_literal else [False, True]
    fzud__zcx = [True] if getattr(uqxb__viqj, '_no_unliteral', False
        ) else fzud__zcx
    for vvvxo__vacw in fzud__zcx:
        if vvvxo__vacw:
            try:
                uadm__hgy = uqxb__viqj.apply(args, kws)
            except Exception as sxrby__uyhd:
                if isinstance(sxrby__uyhd, errors.ForceLiteralArg):
                    raise sxrby__uyhd
                krns__cqtl = sxrby__uyhd
                uadm__hgy = None
            else:
                break
        else:
            fky__irczo = tuple([_unlit_non_poison(a) for a in args])
            vrexb__luci = {maxo__nqq: _unlit_non_poison(qof__xek) for 
                maxo__nqq, qof__xek in kws.items()}
            ing__tofy = fky__irczo == args and kws == vrexb__luci
            if not ing__tofy and uadm__hgy is None:
                try:
                    uadm__hgy = uqxb__viqj.apply(fky__irczo, vrexb__luci)
                except Exception as sxrby__uyhd:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(
                        sxrby__uyhd, errors.NumbaError):
                        raise sxrby__uyhd
                    if isinstance(sxrby__uyhd, errors.ForceLiteralArg):
                        if uqxb__viqj.prefer_literal:
                            raise sxrby__uyhd
                    fiqbp__ohl = sxrby__uyhd
                else:
                    break
    if uadm__hgy is None and (fiqbp__ohl is not None or krns__cqtl is not None
        ):
        hitt__how = '- Resolution failure for {} arguments:\n{}\n'
        uij__wjz = _termcolor.highlight(hitt__how)
        if numba.core.config.DEVELOPER_MODE:
            hgr__kwqw = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    niza__hvosv = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    niza__hvosv = ['']
                yho__bhh = '\n{}'.format(2 * hgr__kwqw)
                ucq__lux = _termcolor.reset(yho__bhh + yho__bhh.join(
                    _bt_as_lines(niza__hvosv)))
                return _termcolor.reset(ucq__lux)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            hrg__dljcf = str(e)
            hrg__dljcf = hrg__dljcf if hrg__dljcf else str(repr(e)) + add_bt(e)
            wpcyj__uama = errors.TypingError(textwrap.dedent(hrg__dljcf))
            return uij__wjz.format(literalness, str(wpcyj__uama))
        import bodo
        if isinstance(krns__cqtl, bodo.utils.typing.BodoError):
            raise krns__cqtl
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', krns__cqtl) +
                nested_msg('non-literal', fiqbp__ohl))
        else:
            if 'missing a required argument' in krns__cqtl.msg:
                msg = 'missing a required argument'
            else:
                msg = 'Compilation error for '
                if isinstance(self.this, bodo.hiframes.pd_dataframe_ext.
                    DataFrameType):
                    msg += 'DataFrame.'
                elif isinstance(self.this, bodo.hiframes.pd_series_ext.
                    SeriesType):
                    msg += 'Series.'
                msg += f'{self.typing_key[1]}().{bodo_typing_error_info}'
            raise errors.TypingError(msg, loc=krns__cqtl.loc)
    return uadm__hgy


if _check_numba_change:
    lines = inspect.getsource(numba.core.types.functions.BoundFunction.
        get_call_type)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '502cd77c0084452e903a45a0f1f8107550bfbde7179363b57dabd617ce135f4a':
        warnings.warn(
            'numba.core.types.functions.BoundFunction.get_call_type has changed'
            )
numba.core.types.functions.BoundFunction.get_call_type = get_call_type2


def string_from_string_and_size(self, string, size):
    from llvmlite.llvmpy.core import Type
    fnty = Type.function(self.pyobj, [self.cstring, self.py_ssize_t])
    vnghe__rojci = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=vnghe__rojci)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            oggy__fofw = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), oggy__fofw)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    qurk__gdiav = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            qurk__gdiav.append(types.Omitted(a.value))
        else:
            qurk__gdiav.append(self.typeof_pyval(a))
    ndcwe__ymn = None
    try:
        error = None
        ndcwe__ymn = self.compile(tuple(qurk__gdiav))
    except errors.ForceLiteralArg as e:
        pgb__tlqk = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if pgb__tlqk:
            mnawc__pdh = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            fhoo__ddt = ', '.join('Arg #{} is {}'.format(i, args[i]) for i in
                sorted(pgb__tlqk))
            raise errors.CompilerError(mnawc__pdh.format(fhoo__ddt))
        afac__yjy = []
        try:
            for i, qof__xek in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        afac__yjy.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        afac__yjy.append(types.literal(args[i]))
                else:
                    afac__yjy.append(args[i])
            args = afac__yjy
        except (OSError, FileNotFoundError) as mtkl__lmz:
            error = FileNotFoundError(str(mtkl__lmz) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                ndcwe__ymn = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        mmovr__ptxu = []
        for i, exbh__wfwrk in enumerate(args):
            val = exbh__wfwrk.value if isinstance(exbh__wfwrk, numba.core.
                dispatcher.OmittedArg) else exbh__wfwrk
            try:
                zme__nlqwg = typeof(val, Purpose.argument)
            except ValueError as wef__supl:
                mmovr__ptxu.append((i, str(wef__supl)))
            else:
                if zme__nlqwg is None:
                    mmovr__ptxu.append((i,
                        f'cannot determine Numba type of value {val}'))
        if mmovr__ptxu:
            witk__pmr = '\n'.join(f'- argument {i}: {myc__yzrvl}' for i,
                myc__yzrvl in mmovr__ptxu)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{witk__pmr}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                klcd__wqrn = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                czf__fre = False
                for xpduc__fangl in klcd__wqrn:
                    if xpduc__fangl in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        czf__fre = True
                        break
                if not czf__fre:
                    msg = f'{str(e)}'
                msg += '\n' + e.loc.strformat() + '\n'
                e.patch_message(msg)
        error_rewrite(e, 'typing')
    except errors.UnsupportedError as e:
        error_rewrite(e, 'unsupported_error')
    except (errors.NotDefinedError, errors.RedefinedError, errors.
        VerificationError) as e:
        error_rewrite(e, 'interpreter')
    except errors.ConstantInferenceError as e:
        error_rewrite(e, 'constant_inference')
    except bodo.utils.typing.BodoError as e:
        error = bodo.utils.typing.BodoError(str(e))
    except Exception as e:
        if numba.core.config.SHOW_HELP:
            if hasattr(e, 'patch_message'):
                oggy__fofw = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), oggy__fofw)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return ndcwe__ymn


if _check_numba_change:
    lines = inspect.getsource(numba.core.dispatcher._DispatcherBase.
        _compile_for_args)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5cdfbf0b13a528abf9f0408e70f67207a03e81d610c26b1acab5b2dc1f79bf06':
        warnings.warn(
            'numba.core.dispatcher._DispatcherBase._compile_for_args has changed'
            )
numba.core.dispatcher._DispatcherBase._compile_for_args = _compile_for_args


def resolve_gb_agg_funcs(cres):
    from bodo.ir.aggregate import gb_agg_cfunc_addr
    for obzg__xvhnf in cres.library._codegen._engine._defined_symbols:
        if obzg__xvhnf.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in obzg__xvhnf and (
            'bodo_gb_udf_update_local' in obzg__xvhnf or 
            'bodo_gb_udf_combine' in obzg__xvhnf or 'bodo_gb_udf_eval' in
            obzg__xvhnf or 'bodo_gb_apply_general_udfs' in obzg__xvhnf):
            gb_agg_cfunc_addr[obzg__xvhnf
                ] = cres.library.get_pointer_to_function(obzg__xvhnf)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for obzg__xvhnf in cres.library._codegen._engine._defined_symbols:
        if obzg__xvhnf.startswith('cfunc') and ('get_join_cond_addr' not in
            obzg__xvhnf or 'bodo_join_gen_cond' in obzg__xvhnf):
            join_gen_cond_cfunc_addr[obzg__xvhnf
                ] = cres.library.get_pointer_to_function(obzg__xvhnf)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    ejy__nnlnv = self._get_dispatcher_for_current_target()
    if ejy__nnlnv is not self:
        return ejy__nnlnv.compile(sig)
    with ExitStack() as scope:
        cres = None

        def cb_compiler(dur):
            if cres is not None:
                self._callback_add_compiler_timer(dur, cres)

        def cb_llvm(dur):
            if cres is not None:
                self._callback_add_llvm_timer(dur, cres)
        scope.enter_context(ev.install_timer('numba:compiler_lock',
            cb_compiler))
        scope.enter_context(ev.install_timer('numba:llvm_lock', cb_llvm))
        scope.enter_context(global_compiler_lock)
        if not self._can_compile:
            raise RuntimeError('compilation disabled')
        with self._compiling_counter:
            args, return_type = sigutils.normalize_signature(sig)
            dxtns__yxz = self.overloads.get(tuple(args))
            if dxtns__yxz is not None:
                return dxtns__yxz.entry_point
            cres = self._cache.load_overload(sig, self.targetctx)
            if cres is not None:
                resolve_gb_agg_funcs(cres)
                resolve_join_general_cond_funcs(cres)
                self._cache_hits[sig] += 1
                if not cres.objectmode:
                    self.targetctx.insert_user_function(cres.entry_point,
                        cres.fndesc, [cres.library])
                self.add_overload(cres)
                return cres.entry_point
            self._cache_misses[sig] += 1
            dunyl__ugnb = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=dunyl__ugnb):
                try:
                    cres = self._compiler.compile(args, return_type)
                except errors.ForceLiteralArg as e:

                    def folded(args, kws):
                        return self._compiler.fold_argument_types(args, kws)[1]
                    raise e.bind_fold_arguments(folded)
                self.add_overload(cres)
            self._cache.save_overload(sig, cres)
            return cres.entry_point


if _check_numba_change:
    lines = inspect.getsource(numba.core.dispatcher.Dispatcher.compile)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '934ec993577ea3b1c7dd2181ac02728abf8559fd42c17062cc821541b092ff8f':
        warnings.warn('numba.core.dispatcher.Dispatcher.compile has changed')
numba.core.dispatcher.Dispatcher.compile = compile


def _get_module_for_linking(self):
    import llvmlite.binding as ll
    self._ensure_finalized()
    if self._shared_module is not None:
        return self._shared_module
    hhn__grs = self._final_module
    sjr__mjrmk = []
    qwwm__ryn = 0
    for fn in hhn__grs.functions:
        qwwm__ryn += 1
        if not fn.is_declaration and fn.linkage == ll.Linkage.external:
            if 'get_agg_udf_addr' not in fn.name:
                if 'bodo_gb_udf_update_local' in fn.name:
                    continue
                if 'bodo_gb_udf_combine' in fn.name:
                    continue
                if 'bodo_gb_udf_eval' in fn.name:
                    continue
                if 'bodo_gb_apply_general_udfs' in fn.name:
                    continue
            if 'get_join_cond_addr' not in fn.name:
                if 'bodo_join_gen_cond' in fn.name:
                    continue
            sjr__mjrmk.append(fn.name)
    if qwwm__ryn == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if sjr__mjrmk:
        hhn__grs = hhn__grs.clone()
        for name in sjr__mjrmk:
            hhn__grs.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = hhn__grs
    return hhn__grs


if _check_numba_change:
    lines = inspect.getsource(numba.core.codegen.CPUCodeLibrary.
        _get_module_for_linking)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '56dde0e0555b5ec85b93b97c81821bce60784515a1fbf99e4542e92d02ff0a73':
        warnings.warn(
            'numba.core.codegen.CPUCodeLibrary._get_module_for_linking has changed'
            )
numba.core.codegen.CPUCodeLibrary._get_module_for_linking = (
    _get_module_for_linking)


def propagate(self, typeinfer):
    import bodo
    errors = []
    for ixaer__tyyxs in self.constraints:
        loc = ixaer__tyyxs.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                ixaer__tyyxs(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                flgzc__galal = numba.core.errors.TypingError(str(e), loc=
                    ixaer__tyyxs.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(flgzc__galal, e)
                    )
            except bodo.utils.typing.BodoError as e:
                if loc not in e.locs_in_msg:
                    errors.append(bodo.utils.typing.BodoError(str(e.msg) +
                        '\n' + loc.strformat() + '\n', locs_in_msg=e.
                        locs_in_msg + [loc]))
                else:
                    errors.append(bodo.utils.typing.BodoError(e.msg,
                        locs_in_msg=e.locs_in_msg))
            except Exception as e:
                from numba.core import utils
                if utils.use_old_style_errors():
                    numba.core.typeinfer._logger.debug('captured error',
                        exc_info=e)
                    msg = """Internal error at {con}.
{err}
Enable logging at debug level for details."""
                    flgzc__galal = numba.core.errors.TypingError(msg.format
                        (con=ixaer__tyyxs, err=str(e)), loc=ixaer__tyyxs.
                        loc, highlighting=False)
                    errors.append(utils.chain_exception(flgzc__galal, e))
                elif utils.use_new_style_errors():
                    raise e
                else:
                    msg = (
                        f"Unknown CAPTURED_ERRORS style: '{numba.core.config.CAPTURED_ERRORS}'."
                        )
                    assert 0, msg
    return errors


if _check_numba_change:
    lines = inspect.getsource(numba.core.typeinfer.ConstraintNetwork.propagate)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '1e73635eeba9ba43cb3372f395b747ae214ce73b729fb0adba0a55237a1cb063':
        warnings.warn(
            'numba.core.typeinfer.ConstraintNetwork.propagate has changed')
numba.core.typeinfer.ConstraintNetwork.propagate = propagate


def raise_error(self):
    import bodo
    for xczh__zhsgw in self._failures.values():
        for mopb__zfwh in xczh__zhsgw:
            if isinstance(mopb__zfwh.error, ForceLiteralArg):
                raise mopb__zfwh.error
            if isinstance(mopb__zfwh.error, bodo.utils.typing.BodoError):
                raise mopb__zfwh.error
    raise TypingError(self.format())


if _check_numba_change:
    lines = inspect.getsource(numba.core.types.functions.
        _ResolutionFailures.raise_error)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '84b89430f5c8b46cfc684804e6037f00a0f170005cd128ad245551787b2568ea':
        warnings.warn(
            'numba.core.types.functions._ResolutionFailures.raise_error has changed'
            )
numba.core.types.functions._ResolutionFailures.raise_error = raise_error


def bodo_remove_dead_block(block, lives, call_table, arg_aliases, alias_map,
    alias_set, func_ir, typemap):
    from bodo.transforms.distributed_pass import saved_array_analysis
    from bodo.utils.utils import is_array_typ, is_expr
    zbsd__lzcxo = False
    pwxq__qbd = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        kfks__sxxo = set()
        zsq__zxg = lives & alias_set
        for qof__xek in zsq__zxg:
            kfks__sxxo |= alias_map[qof__xek]
        lives_n_aliases = lives | kfks__sxxo | arg_aliases
        if type(stmt) in remove_dead_extensions:
            aamar__fpq = remove_dead_extensions[type(stmt)]
            stmt = aamar__fpq(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                zbsd__lzcxo = True
                continue
        if isinstance(stmt, ir.Assign):
            grt__zmtom = stmt.target
            yvdm__smwjs = stmt.value
            if grt__zmtom.name not in lives and has_no_side_effect(yvdm__smwjs,
                lives_n_aliases, call_table):
                zbsd__lzcxo = True
                continue
            if saved_array_analysis and grt__zmtom.name in lives and is_expr(
                yvdm__smwjs, 'getattr'
                ) and yvdm__smwjs.attr == 'shape' and is_array_typ(typemap[
                yvdm__smwjs.value.name]
                ) and yvdm__smwjs.value.name not in lives:
                ajda__uygnt = {qof__xek: maxo__nqq for maxo__nqq, qof__xek in
                    func_ir.blocks.items()}
                if block in ajda__uygnt:
                    xkm__pkbtr = ajda__uygnt[block]
                    ujdxr__qdfxj = saved_array_analysis.get_equiv_set(
                        xkm__pkbtr)
                    oek__zjwb = ujdxr__qdfxj.get_equiv_set(yvdm__smwjs.value)
                    if oek__zjwb is not None:
                        for qof__xek in oek__zjwb:
                            if qof__xek.endswith('#0'):
                                qof__xek = qof__xek[:-2]
                            if qof__xek in typemap and is_array_typ(typemap
                                [qof__xek]) and qof__xek in lives:
                                yvdm__smwjs.value = ir.Var(yvdm__smwjs.
                                    value.scope, qof__xek, yvdm__smwjs.
                                    value.loc)
                                zbsd__lzcxo = True
                                break
            if isinstance(yvdm__smwjs, ir.Var
                ) and grt__zmtom.name == yvdm__smwjs.name:
                zbsd__lzcxo = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                zbsd__lzcxo = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            kkrn__okn = analysis.ir_extension_usedefs[type(stmt)]
            wxfpb__wau, ncg__hnu = kkrn__okn(stmt)
            lives -= ncg__hnu
            lives |= wxfpb__wau
        else:
            lives |= {qof__xek.name for qof__xek in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                moiln__jvekp = set()
                if isinstance(yvdm__smwjs, ir.Expr):
                    moiln__jvekp = {qof__xek.name for qof__xek in
                        yvdm__smwjs.list_vars()}
                if grt__zmtom.name not in moiln__jvekp:
                    lives.remove(grt__zmtom.name)
        pwxq__qbd.append(stmt)
    pwxq__qbd.reverse()
    block.body = pwxq__qbd
    return zbsd__lzcxo


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            gjk__xtpo, = args
            if isinstance(gjk__xtpo, types.IterableType):
                dtype = gjk__xtpo.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), gjk__xtpo)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    dlkbp__vpdi = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (dlkbp__vpdi, self.dtype)
    super(types.Set, self).__init__(name=name)


types.Set.__init__ = Set__init__


@lower_builtin(operator.eq, types.UnicodeType, types.UnicodeType)
def eq_str(context, builder, sig, args):
    func = numba.cpython.unicode.unicode_eq(*sig.args)
    return context.compile_internal(builder, func, sig, args)


numba.parfors.parfor.push_call_vars = (lambda blocks, saved_globals,
    saved_getattrs, typemap, nested=False: None)


def maybe_literal(value):
    if isinstance(value, (list, dict, pytypes.FunctionType)):
        return
    if isinstance(value, tuple):
        try:
            return types.Tuple([literal(x) for x in value])
        except LiteralTypingError as ttw__woxa:
            return
    try:
        return literal(value)
    except LiteralTypingError as ttw__woxa:
        return


if _check_numba_change:
    lines = inspect.getsource(types.maybe_literal)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8fb2fd93acf214b28e33e37d19dc2f7290a42792ec59b650553ac278854b5081':
        warnings.warn('types.maybe_literal has changed')
types.maybe_literal = maybe_literal
types.misc.maybe_literal = maybe_literal


def CacheImpl__init__(self, py_func):
    self._lineno = py_func.__code__.co_firstlineno
    try:
        xdlvr__hntz = py_func.__qualname__
    except AttributeError as ttw__woxa:
        xdlvr__hntz = py_func.__name__
    eakt__lfg = inspect.getfile(py_func)
    for cls in self._locator_classes:
        vndey__kzpkb = cls.from_function(py_func, eakt__lfg)
        if vndey__kzpkb is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (xdlvr__hntz, eakt__lfg))
    self._locator = vndey__kzpkb
    frj__tibxh = inspect.getfile(py_func)
    ntnbb__hhg = os.path.splitext(os.path.basename(frj__tibxh))[0]
    if eakt__lfg.startswith('<ipython-'):
        iajg__ubpg = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)',
            '\\1\\3', ntnbb__hhg, count=1)
        if iajg__ubpg == ntnbb__hhg:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        ntnbb__hhg = iajg__ubpg
    oby__zhw = '%s.%s' % (ntnbb__hhg, xdlvr__hntz)
    mvai__idai = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(oby__zhw, mvai__idai)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    dwemj__qogy = list(filter(lambda a: self._istuple(a.name), args))
    if len(dwemj__qogy) == 2 and fn.__name__ == 'add':
        mswk__rctpw = self.typemap[dwemj__qogy[0].name]
        xitx__bsv = self.typemap[dwemj__qogy[1].name]
        if mswk__rctpw.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                dwemj__qogy[1]))
        if xitx__bsv.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                dwemj__qogy[0]))
        try:
            cqsjr__iaa = [equiv_set.get_shape(x) for x in dwemj__qogy]
            if None in cqsjr__iaa:
                return None
            zpnc__nzrzd = sum(cqsjr__iaa, ())
            return ArrayAnalysis.AnalyzeResult(shape=zpnc__nzrzd)
        except GuardException as ttw__woxa:
            return None
    refz__naz = list(filter(lambda a: self._isarray(a.name), args))
    require(len(refz__naz) > 0)
    lsdm__lvb = [x.name for x in refz__naz]
    pyw__zgje = [self.typemap[x.name].ndim for x in refz__naz]
    xkiv__hylqn = max(pyw__zgje)
    require(xkiv__hylqn > 0)
    cqsjr__iaa = [equiv_set.get_shape(x) for x in refz__naz]
    if any(a is None for a in cqsjr__iaa):
        return ArrayAnalysis.AnalyzeResult(shape=refz__naz[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, refz__naz))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, cqsjr__iaa,
        lsdm__lvb)


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.array_analysis.ArrayAnalysis.
        _analyze_broadcast)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '6c91fec038f56111338ea2b08f5f0e7f61ebdab1c81fb811fe26658cc354e40f':
        warnings.warn(
            'numba.parfors.array_analysis.ArrayAnalysis._analyze_broadcast has changed'
            )
numba.parfors.array_analysis.ArrayAnalysis._analyze_broadcast = (
    _analyze_broadcast)


def slice_size(self, index, dsize, equiv_set, scope, stmts):
    return None, None


numba.parfors.array_analysis.ArrayAnalysis.slice_size = slice_size


def convert_code_obj_to_function(code_obj, caller_ir):
    import bodo
    okej__lieh = code_obj.code
    xrl__uzvyo = len(okej__lieh.co_freevars)
    mjvnv__qvvq = okej__lieh.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        jop__fkdv, op = ir_utils.find_build_sequence(caller_ir, code_obj.
            closure)
        assert op == 'build_tuple'
        mjvnv__qvvq = [qof__xek.name for qof__xek in jop__fkdv]
    firnf__qyyh = caller_ir.func_id.func.__globals__
    try:
        firnf__qyyh = getattr(code_obj, 'globals', firnf__qyyh)
    except KeyError as ttw__woxa:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    mcu__vhx = []
    for x in mjvnv__qvvq:
        try:
            obmi__dcrmz = caller_ir.get_definition(x)
        except KeyError as ttw__woxa:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(obmi__dcrmz, (ir.Const, ir.Global, ir.FreeVar)):
            val = obmi__dcrmz.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                secsn__lfi = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                firnf__qyyh[secsn__lfi] = bodo.jit(distributed=False)(val)
                firnf__qyyh[secsn__lfi].is_nested_func = True
                val = secsn__lfi
            if isinstance(val, CPUDispatcher):
                secsn__lfi = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                firnf__qyyh[secsn__lfi] = val
                val = secsn__lfi
            mcu__vhx.append(val)
        elif isinstance(obmi__dcrmz, ir.Expr
            ) and obmi__dcrmz.op == 'make_function':
            bcq__iioes = convert_code_obj_to_function(obmi__dcrmz, caller_ir)
            secsn__lfi = ir_utils.mk_unique_var('nested_func').replace('.', '_'
                )
            firnf__qyyh[secsn__lfi] = bodo.jit(distributed=False)(bcq__iioes)
            firnf__qyyh[secsn__lfi].is_nested_func = True
            mcu__vhx.append(secsn__lfi)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    hcwf__fggzn = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in enumerate
        (mcu__vhx)])
    fsz__pib = ','.join([('c_%d' % i) for i in range(xrl__uzvyo)])
    tqqpx__khmt = list(okej__lieh.co_varnames)
    wef__ejnv = 0
    bxp__uhs = okej__lieh.co_argcount
    islv__sika = caller_ir.get_definition(code_obj.defaults)
    if islv__sika is not None:
        if isinstance(islv__sika, tuple):
            rohiu__yjfen = [caller_ir.get_definition(x).value for x in
                islv__sika]
            qjn__ujyim = tuple(rohiu__yjfen)
        else:
            rohiu__yjfen = [caller_ir.get_definition(x).value for x in
                islv__sika.items]
            qjn__ujyim = tuple(rohiu__yjfen)
        wef__ejnv = len(qjn__ujyim)
    ovqj__qsray = bxp__uhs - wef__ejnv
    sqm__hfd = ','.join([('%s' % tqqpx__khmt[i]) for i in range(ovqj__qsray)])
    if wef__ejnv:
        dgnaw__nnnq = [('%s = %s' % (tqqpx__khmt[i + ovqj__qsray],
            qjn__ujyim[i])) for i in range(wef__ejnv)]
        sqm__hfd += ', '
        sqm__hfd += ', '.join(dgnaw__nnnq)
    return _create_function_from_code_obj(okej__lieh, hcwf__fggzn, sqm__hfd,
        fsz__pib, firnf__qyyh)


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.convert_code_obj_to_function)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b840769812418d589460e924a15477e83e7919aac8a3dcb0188ff447344aa8ac':
        warnings.warn(
            'numba.core.ir_utils.convert_code_obj_to_function has changed')
numba.core.ir_utils.convert_code_obj_to_function = convert_code_obj_to_function
numba.core.untyped_passes.convert_code_obj_to_function = (
    convert_code_obj_to_function)


def passmanager_run(self, state):
    from numba.core.compiler import _EarlyPipelineCompletion
    if not self.finalized:
        raise RuntimeError('Cannot run non-finalised pipeline')
    from numba.core.compiler_machinery import CompilerPass, _pass_registry
    import bodo
    for vojz__aukx, (pxokh__cbvln, jsk__xem) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % jsk__xem)
            shehc__edljp = _pass_registry.get(pxokh__cbvln).pass_inst
            if isinstance(shehc__edljp, CompilerPass):
                self._runPass(vojz__aukx, shehc__edljp, state)
            else:
                raise BaseException('Legacy pass in use')
        except _EarlyPipelineCompletion as e:
            raise e
        except bodo.utils.typing.BodoError as e:
            raise
        except Exception as e:
            if numba.core.config.DEVELOPER_MODE:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                msg = 'Failed in %s mode pipeline (step: %s)' % (self.
                    pipeline_name, jsk__xem)
                hrzw__uouu = self._patch_error(msg, e)
                raise hrzw__uouu
            else:
                raise e


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler_machinery.PassManager.run)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '43505782e15e690fd2d7e53ea716543bec37aa0633502956864edf649e790cdb':
        warnings.warn(
            'numba.core.compiler_machinery.PassManager.run has changed')
numba.core.compiler_machinery.PassManager.run = passmanager_run
if _check_numba_change:
    lines = inspect.getsource(numba.np.ufunc.parallel._launch_threads)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a57ef28c4168fdd436a5513bba4351ebc6d9fba76c5819f44046431a79b9030f':
        warnings.warn('numba.np.ufunc.parallel._launch_threads has changed')
numba.np.ufunc.parallel._launch_threads = lambda : None


def get_reduce_nodes(reduction_node, nodes, func_ir):
    npa__qti = None
    ncg__hnu = {}

    def lookup(var, already_seen, varonly=True):
        val = ncg__hnu.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    lfp__vel = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        grt__zmtom = stmt.target
        yvdm__smwjs = stmt.value
        ncg__hnu[grt__zmtom.name] = yvdm__smwjs
        if isinstance(yvdm__smwjs, ir.Var) and yvdm__smwjs.name in ncg__hnu:
            yvdm__smwjs = lookup(yvdm__smwjs, set())
        if isinstance(yvdm__smwjs, ir.Expr):
            zuxi__vxr = set(lookup(qof__xek, set(), True).name for qof__xek in
                yvdm__smwjs.list_vars())
            if name in zuxi__vxr:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(yvdm__smwjs)]
                whoh__fyqn = [x for x, wwxje__dvmas in args if wwxje__dvmas
                    .name != name]
                args = [(x, wwxje__dvmas) for x, wwxje__dvmas in args if x !=
                    wwxje__dvmas.name]
                qwsy__lge = dict(args)
                if len(whoh__fyqn) == 1:
                    qwsy__lge[whoh__fyqn[0]] = ir.Var(grt__zmtom.scope, 
                        name + '#init', grt__zmtom.loc)
                replace_vars_inner(yvdm__smwjs, qwsy__lge)
                npa__qti = nodes[i:]
                break
    return npa__qti


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_reduce_nodes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a05b52aff9cb02e595a510cd34e973857303a71097fc5530567cb70ca183ef3b':
        warnings.warn('numba.parfors.parfor.get_reduce_nodes has changed')
numba.parfors.parfor.get_reduce_nodes = get_reduce_nodes


def _can_reorder_stmts(stmt, next_stmt, func_ir, call_table, alias_map,
    arg_aliases):
    from numba.parfors.parfor import Parfor, expand_aliases, is_assert_equiv
    if isinstance(stmt, Parfor) and not isinstance(next_stmt, Parfor
        ) and not isinstance(next_stmt, ir.Print) and (not isinstance(
        next_stmt, ir.Assign) or has_no_side_effect(next_stmt.value, set(),
        call_table) or guard(is_assert_equiv, func_ir, next_stmt.value)):
        ubq__eikte = expand_aliases({qof__xek.name for qof__xek in stmt.
            list_vars()}, alias_map, arg_aliases)
        rfdz__dtw = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        gypu__wqyvh = expand_aliases({qof__xek.name for qof__xek in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        toqhh__vhky = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(rfdz__dtw & gypu__wqyvh | toqhh__vhky & ubq__eikte) == 0:
            return True
    return False


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor._can_reorder_stmts)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '18caa9a01b21ab92b4f79f164cfdbc8574f15ea29deedf7bafdf9b0e755d777c':
        warnings.warn('numba.parfors.parfor._can_reorder_stmts has changed')
numba.parfors.parfor._can_reorder_stmts = _can_reorder_stmts


def get_parfor_writes(parfor, func_ir):
    from numba.parfors.parfor import Parfor
    assert isinstance(parfor, Parfor)
    ixkks__krx = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            ixkks__krx.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                ixkks__krx.update(get_parfor_writes(stmt, func_ir))
    return ixkks__krx


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    ixkks__krx = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        ixkks__krx.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        ixkks__krx = {qof__xek.name for qof__xek in stmt.df_out_vars.values()}
        if stmt.out_key_vars is not None:
            ixkks__krx.update({qof__xek.name for qof__xek in stmt.out_key_vars}
                )
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        ixkks__krx = {qof__xek.name for qof__xek in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        ixkks__krx = {qof__xek.name for qof__xek in stmt.out_data_vars.values()
            }
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            ixkks__krx.update({qof__xek.name for qof__xek in stmt.out_key_arrs}
                )
            ixkks__krx.update({qof__xek.name for qof__xek in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        zfarx__qdimu = guard(find_callname, func_ir, stmt.value)
        if zfarx__qdimu in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'
            ), ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            ixkks__krx.add(stmt.value.args[0].name)
    return ixkks__krx


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.get_stmt_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '1a7a80b64c9a0eb27e99dc8eaae187bde379d4da0b74c84fbf87296d87939974':
        warnings.warn('numba.core.ir_utils.get_stmt_writes has changed')


def patch_message(self, new_message):
    self.msg = new_message
    self.args = (new_message,) + self.args[1:]


if _check_numba_change:
    lines = inspect.getsource(numba.core.errors.NumbaError.patch_message)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'ed189a428a7305837e76573596d767b6e840e99f75c05af6941192e0214fa899':
        warnings.warn('numba.core.errors.NumbaError.patch_message has changed')
numba.core.errors.NumbaError.patch_message = patch_message


def add_context(self, msg):
    if numba.core.config.DEVELOPER_MODE:
        self.contexts.append(msg)
        aamar__fpq = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        rwr__uscdj = aamar__fpq.format(self, msg)
        self.args = rwr__uscdj,
    else:
        aamar__fpq = _termcolor.errmsg('{0}')
        rwr__uscdj = aamar__fpq.format(self)
        self.args = rwr__uscdj,
    return self


if _check_numba_change:
    lines = inspect.getsource(numba.core.errors.NumbaError.add_context)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '6a388d87788f8432c2152ac55ca9acaa94dbc3b55be973b2cf22dd4ee7179ab8':
        warnings.warn('numba.core.errors.NumbaError.add_context has changed')
numba.core.errors.NumbaError.add_context = add_context


def _get_dist_spec_from_options(spec, **options):
    from bodo.transforms.distributed_analysis import Distribution
    dist_spec = {}
    if 'distributed' in options:
        for flxoz__rpya in options['distributed']:
            dist_spec[flxoz__rpya] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for flxoz__rpya in options['distributed_block']:
            dist_spec[flxoz__rpya] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    qpmtu__auukj = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, edm__nxbo in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(edm__nxbo)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    rnv__nqdvt = {}
    for khbfl__mucc in reversed(inspect.getmro(cls)):
        rnv__nqdvt.update(khbfl__mucc.__dict__)
    evf__lqrl, manjj__qwnbe, trj__zosi, tbq__sah = {}, {}, {}, {}
    for maxo__nqq, qof__xek in rnv__nqdvt.items():
        if isinstance(qof__xek, pytypes.FunctionType):
            evf__lqrl[maxo__nqq] = qof__xek
        elif isinstance(qof__xek, property):
            manjj__qwnbe[maxo__nqq] = qof__xek
        elif isinstance(qof__xek, staticmethod):
            trj__zosi[maxo__nqq] = qof__xek
        else:
            tbq__sah[maxo__nqq] = qof__xek
    leo__ceitv = (set(evf__lqrl) | set(manjj__qwnbe) | set(trj__zosi)) & set(
        spec)
    if leo__ceitv:
        raise NameError('name shadowing: {0}'.format(', '.join(leo__ceitv)))
    pdaua__nqi = tbq__sah.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(tbq__sah)
    if tbq__sah:
        msg = 'class members are not yet supported: {0}'
        wzffq__gpm = ', '.join(tbq__sah.keys())
        raise TypeError(msg.format(wzffq__gpm))
    for maxo__nqq, qof__xek in manjj__qwnbe.items():
        if qof__xek.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(maxo__nqq))
    jit_methods = {maxo__nqq: bodo.jit(returns_maybe_distributed=
        qpmtu__auukj)(qof__xek) for maxo__nqq, qof__xek in evf__lqrl.items()}
    jit_props = {}
    for maxo__nqq, qof__xek in manjj__qwnbe.items():
        mkrk__xqhbt = {}
        if qof__xek.fget:
            mkrk__xqhbt['get'] = bodo.jit(qof__xek.fget)
        if qof__xek.fset:
            mkrk__xqhbt['set'] = bodo.jit(qof__xek.fset)
        jit_props[maxo__nqq] = mkrk__xqhbt
    jit_static_methods = {maxo__nqq: bodo.jit(qof__xek.__func__) for 
        maxo__nqq, qof__xek in trj__zosi.items()}
    qzp__oae = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    anif__feb = dict(class_type=qzp__oae, __doc__=pdaua__nqi)
    anif__feb.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), anif__feb)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, qzp__oae)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(qzp__oae, typingctx, targetctx).register()
    as_numba_type.register(cls, qzp__oae.instance_type)
    return cls


if _check_numba_change:
    lines = inspect.getsource(jitclass_base.register_class_type)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '005e6e2e89a47f77a19ba86305565050d4dbc2412fc4717395adf2da348671a9':
        warnings.warn('jitclass_base.register_class_type has changed')
jitclass_base.register_class_type = register_class_type


def ClassType__init__(self, class_def, ctor_template_cls, struct,
    jit_methods, jit_props, jit_static_methods, dist_spec=None):
    if dist_spec is None:
        dist_spec = {}
    self.class_name = class_def.__name__
    self.class_doc = class_def.__doc__
    self._ctor_template_class = ctor_template_cls
    self.jit_methods = jit_methods
    self.jit_props = jit_props
    self.jit_static_methods = jit_static_methods
    self.struct = struct
    self.dist_spec = dist_spec
    spo__jzek = ','.join('{0}:{1}'.format(maxo__nqq, qof__xek) for 
        maxo__nqq, qof__xek in struct.items())
    amxsa__bmu = ','.join('{0}:{1}'.format(maxo__nqq, qof__xek) for 
        maxo__nqq, qof__xek in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), spo__jzek, amxsa__bmu)
    super(types.misc.ClassType, self).__init__(name)


if _check_numba_change:
    lines = inspect.getsource(types.misc.ClassType.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '2b848ea82946c88f540e81f93ba95dfa7cd66045d944152a337fe2fc43451c30':
        warnings.warn('types.misc.ClassType.__init__ has changed')
types.misc.ClassType.__init__ = ClassType__init__


def jitclass(cls_or_spec=None, spec=None, **options):
    if cls_or_spec is not None and spec is None and not isinstance(cls_or_spec,
        type):
        spec = cls_or_spec
        cls_or_spec = None

    def wrap(cls):
        if numba.core.config.DISABLE_JIT:
            return cls
        else:
            from numba.experimental.jitclass.base import ClassBuilder
            return register_class_type(cls, spec, types.ClassType,
                ClassBuilder, **options)
    if cls_or_spec is None:
        return wrap
    else:
        return wrap(cls_or_spec)


if _check_numba_change:
    lines = inspect.getsource(jitclass_decorators.jitclass)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '265f1953ee5881d1a5d90238d3c932cd300732e41495657e65bf51e59f7f4af5':
        warnings.warn('jitclass_decorators.jitclass has changed')


def CallConstraint_resolve(self, typeinfer, typevars, fnty):
    assert fnty
    context = typeinfer.context
    iycx__dkmr = numba.core.typeinfer.fold_arg_vars(typevars, self.args,
        self.vararg, self.kws)
    if iycx__dkmr is None:
        return
    aew__wjvzh, cabo__jyvl = iycx__dkmr
    for a in itertools.chain(aew__wjvzh, cabo__jyvl.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, aew__wjvzh, cabo__jyvl)
    except ForceLiteralArg as e:
        dbli__kle = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(dbli__kle, self.kws)
        nlcem__sog = set()
        xyeii__jpwcf = set()
        prb__xlgyt = {}
        for vojz__aukx in e.requested_args:
            abqt__xalpd = typeinfer.func_ir.get_definition(folded[vojz__aukx])
            if isinstance(abqt__xalpd, ir.Arg):
                nlcem__sog.add(abqt__xalpd.index)
                if abqt__xalpd.index in e.file_infos:
                    prb__xlgyt[abqt__xalpd.index] = e.file_infos[abqt__xalpd
                        .index]
            else:
                xyeii__jpwcf.add(vojz__aukx)
        if xyeii__jpwcf:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif nlcem__sog:
            raise ForceLiteralArg(nlcem__sog, loc=self.loc, file_infos=
                prb__xlgyt)
    if sig is None:
        hqbm__cgc = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in aew__wjvzh]
        args += [('%s=%s' % (maxo__nqq, qof__xek)) for maxo__nqq, qof__xek in
            sorted(cabo__jyvl.items())]
        tnaga__foyuh = hqbm__cgc.format(fnty, ', '.join(map(str, args)))
        oxcfr__sgtw = context.explain_function_type(fnty)
        msg = '\n'.join([tnaga__foyuh, oxcfr__sgtw])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        ffcf__zmn = context.unify_pairs(sig.recvr, fnty.this)
        if ffcf__zmn is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if ffcf__zmn is not None and ffcf__zmn.is_precise():
            tlu__ipd = fnty.copy(this=ffcf__zmn)
            typeinfer.propagate_refined_type(self.func, tlu__ipd)
    if not sig.return_type.is_precise():
        daqhj__ygrjx = typevars[self.target]
        if daqhj__ygrjx.defined:
            pupz__nksy = daqhj__ygrjx.getone()
            if context.unify_pairs(pupz__nksy, sig.return_type) == pupz__nksy:
                sig = sig.replace(return_type=pupz__nksy)
    self.signature = sig
    self._add_refine_map(typeinfer, typevars, sig)


if _check_numba_change:
    lines = inspect.getsource(numba.core.typeinfer.CallConstraint.resolve)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'c78cd8ffc64b836a6a2ddf0362d481b52b9d380c5249920a87ff4da052ce081f':
        warnings.warn('numba.core.typeinfer.CallConstraint.resolve has changed'
            )
numba.core.typeinfer.CallConstraint.resolve = CallConstraint_resolve


def ForceLiteralArg__init__(self, arg_indices, fold_arguments=None, loc=
    None, file_infos=None):
    super(ForceLiteralArg, self).__init__(
        'Pseudo-exception to force literal arguments in the dispatcher',
        loc=loc)
    self.requested_args = frozenset(arg_indices)
    self.fold_arguments = fold_arguments
    if file_infos is None:
        self.file_infos = {}
    else:
        self.file_infos = file_infos


if _check_numba_change:
    lines = inspect.getsource(numba.core.errors.ForceLiteralArg.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b241d5e36a4cf7f4c73a7ad3238693612926606c7a278cad1978070b82fb55ef':
        warnings.warn('numba.core.errors.ForceLiteralArg.__init__ has changed')
numba.core.errors.ForceLiteralArg.__init__ = ForceLiteralArg__init__


def ForceLiteralArg_bind_fold_arguments(self, fold_arguments):
    e = ForceLiteralArg(self.requested_args, fold_arguments, loc=self.loc,
        file_infos=self.file_infos)
    return numba.core.utils.chain_exception(e, self)


if _check_numba_change:
    lines = inspect.getsource(numba.core.errors.ForceLiteralArg.
        bind_fold_arguments)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '1e93cca558f7c604a47214a8f2ec33ee994104cb3e5051166f16d7cc9315141d':
        warnings.warn(
            'numba.core.errors.ForceLiteralArg.bind_fold_arguments has changed'
            )
numba.core.errors.ForceLiteralArg.bind_fold_arguments = (
    ForceLiteralArg_bind_fold_arguments)


def ForceLiteralArg_combine(self, other):
    if not isinstance(other, ForceLiteralArg):
        mnawc__pdh = '*other* must be a {} but got a {} instead'
        raise TypeError(mnawc__pdh.format(ForceLiteralArg, type(other)))
    return ForceLiteralArg(self.requested_args | other.requested_args, {**
        self.file_infos, **other.file_infos})


if _check_numba_change:
    lines = inspect.getsource(numba.core.errors.ForceLiteralArg.combine)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '49bf06612776f5d755c1c7d1c5eb91831a57665a8fed88b5651935f3bf33e899':
        warnings.warn('numba.core.errors.ForceLiteralArg.combine has changed')
numba.core.errors.ForceLiteralArg.combine = ForceLiteralArg_combine


def _get_global_type(self, gv):
    from bodo.utils.typing import FunctionLiteral
    ty = self._lookup_global(gv)
    if ty is not None:
        return ty
    if isinstance(gv, pytypes.ModuleType):
        return types.Module(gv)
    if isinstance(gv, pytypes.FunctionType):
        return FunctionLiteral(gv)


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.context.BaseContext.
        _get_global_type)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8ffe6b81175d1eecd62a37639b5005514b4477d88f35f5b5395041ac8c945a4a':
        warnings.warn(
            'numba.core.typing.context.BaseContext._get_global_type has changed'
            )
numba.core.typing.context.BaseContext._get_global_type = _get_global_type


def _legalize_args(self, func_ir, args, kwargs, loc, func_globals,
    func_closures):
    from numba.core import sigutils
    from bodo.utils.transform import get_const_value_inner
    if args:
        raise errors.CompilerError(
            "objectmode context doesn't take any positional arguments")
    avky__ezgu = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for maxo__nqq, qof__xek in kwargs.items():
        sgtes__hxq = None
        try:
            ynyy__onvu = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var
                ('dummy'), loc)
            func_ir._definitions[ynyy__onvu.name] = [qof__xek]
            sgtes__hxq = get_const_value_inner(func_ir, ynyy__onvu)
            func_ir._definitions.pop(ynyy__onvu.name)
            if isinstance(sgtes__hxq, str):
                sgtes__hxq = sigutils._parse_signature_string(sgtes__hxq)
            if isinstance(sgtes__hxq, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {maxo__nqq} is annotated as type class {sgtes__hxq}."""
                    )
            assert isinstance(sgtes__hxq, types.Type)
            if isinstance(sgtes__hxq, (types.List, types.Set)):
                sgtes__hxq = sgtes__hxq.copy(reflected=False)
            avky__ezgu[maxo__nqq] = sgtes__hxq
        except BodoError as ttw__woxa:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(sgtes__hxq, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(qof__xek, ir.Global):
                    msg = f'Global {qof__xek.name!r} is not defined.'
                if isinstance(qof__xek, ir.FreeVar):
                    msg = f'Freevar {qof__xek.name!r} is not defined.'
            if isinstance(qof__xek, ir.Expr) and qof__xek.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=maxo__nqq, msg=msg, loc=loc)
    for name, typ in avky__ezgu.items():
        self._legalize_arg_type(name, typ, loc)
    return avky__ezgu


if _check_numba_change:
    lines = inspect.getsource(numba.core.withcontexts._ObjModeContextType.
        _legalize_args)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '867c9ba7f1bcf438be56c38e26906bb551f59a99f853a9f68b71208b107c880e':
        warnings.warn(
            'numba.core.withcontexts._ObjModeContextType._legalize_args has changed'
            )
numba.core.withcontexts._ObjModeContextType._legalize_args = _legalize_args


def op_FORMAT_VALUE_byteflow(self, state, inst):
    flags = inst.arg
    if flags & 3 != 0:
        msg = 'str/repr/ascii conversion in f-strings not supported yet'
        raise errors.UnsupportedError(msg, loc=self.get_debug_loc(inst.lineno))
    format_spec = None
    if flags & 4 == 4:
        format_spec = state.pop()
    value = state.pop()
    fmtvar = state.make_temp()
    res = state.make_temp()
    state.append(inst, value=value, res=res, fmtvar=fmtvar, format_spec=
        format_spec)
    state.push(res)


def op_BUILD_STRING_byteflow(self, state, inst):
    jxwkh__zou = inst.arg
    assert jxwkh__zou > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(jxwkh__zou)]))
    tmps = [state.make_temp() for _ in range(jxwkh__zou - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    tdfad__porgh = ir.Global('format', format, loc=self.loc)
    self.store(value=tdfad__porgh, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    qil__iiwxe = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=qil__iiwxe, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    jxwkh__zou = inst.arg
    assert jxwkh__zou > 0, 'invalid BUILD_STRING count'
    tcvcu__ttyny = self.get(strings[0])
    for other, zchkb__qbtdu in zip(strings[1:], tmps):
        other = self.get(other)
        uxdtc__lesvs = ir.Expr.binop(operator.add, lhs=tcvcu__ttyny, rhs=
            other, loc=self.loc)
        self.store(uxdtc__lesvs, zchkb__qbtdu)
        tcvcu__ttyny = self.get(zchkb__qbtdu)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    nef__ksph = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, nef__ksph])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    dfmn__osjoo = mk_unique_var(f'{var_name}')
    nppha__cwgt = dfmn__osjoo.replace('<', '_').replace('>', '_')
    nppha__cwgt = nppha__cwgt.replace('.', '_').replace('$', '_v')
    return nppha__cwgt


if _check_numba_change:
    lines = inspect.getsource(numba.core.inline_closurecall.
        _created_inlined_var_name)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '0d91aac55cd0243e58809afe9d252562f9ae2899cde1112cc01a46804e01821e':
        warnings.warn(
            'numba.core.inline_closurecall._created_inlined_var_name has changed'
            )
numba.core.inline_closurecall._created_inlined_var_name = (
    _created_inlined_var_name)


def resolve_number___call__(self, classty):
    import numpy as np
    from numba.core.typing.templates import make_callable_template
    import bodo
    ty = classty.instance_type
    if isinstance(ty, types.NPDatetime):

        def typer(val1, val2):
            bodo.hiframes.pd_timestamp_ext.check_tz_aware_unsupported(val1,
                'numpy.datetime64')
            if val1 == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
                if not is_overload_constant_str(val2):
                    raise_bodo_error(
                        "datetime64(): 'units' must be a 'str' specifying 'ns'"
                        )
                aef__xladx = get_overload_const_str(val2)
                if aef__xladx != 'ns':
                    raise BodoError("datetime64(): 'units' must be 'ns'")
                return types.NPDatetime('ns')
    else:

        def typer(val):
            if isinstance(val, (types.BaseTuple, types.Sequence)):
                fnty = self.context.resolve_value_type(np.array)
                sig = fnty.get_call_type(self.context, (val, types.DType(ty
                    )), {})
                return sig.return_type
            elif isinstance(val, (types.Number, types.Boolean, types.
                IntEnumMember)):
                return ty
            elif val == types.unicode_type:
                return ty
            elif isinstance(val, (types.NPDatetime, types.NPTimedelta)):
                if ty.bitwidth == 64:
                    return ty
                else:
                    msg = (
                        f'Cannot cast {val} to {ty} as {ty} is not 64 bits wide.'
                        )
                    raise errors.TypingError(msg)
            elif isinstance(val, types.Array
                ) and val.ndim == 0 and val.dtype == ty:
                return ty
            else:
                msg = f'Casting {val} to {ty} directly is unsupported.'
                if isinstance(val, types.Array):
                    msg += f" Try doing '<array>.astype(np.{ty})' instead"
                raise errors.TypingError(msg)
    return types.Function(make_callable_template(key=ty, typer=typer))


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.builtins.
        NumberClassAttribute.resolve___call__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'fdaf0c7d0820130481bb2bd922985257b9281b670f0bafffe10e51cabf0d5081':
        warnings.warn(
            'numba.core.typing.builtins.NumberClassAttribute.resolve___call__ has changed'
            )
numba.core.typing.builtins.NumberClassAttribute.resolve___call__ = (
    resolve_number___call__)


def on_assign(self, states, assign):
    if assign.target.name == states['varname']:
        scope = states['scope']
        vkik__svl = states['defmap']
        if len(vkik__svl) == 0:
            uuexm__tot = assign.target
            numba.core.ssa._logger.debug('first assign: %s', uuexm__tot)
            if uuexm__tot.name not in scope.localvars:
                uuexm__tot = scope.define(assign.target.name, loc=assign.loc)
        else:
            uuexm__tot = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=uuexm__tot, value=assign.value, loc=
            assign.loc)
        vkik__svl[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    pigmc__rzdj = []
    for maxo__nqq, qof__xek in typing.npydecl.registry.globals:
        if maxo__nqq == func:
            pigmc__rzdj.append(qof__xek)
    for maxo__nqq, qof__xek in typing.templates.builtin_registry.globals:
        if maxo__nqq == func:
            pigmc__rzdj.append(qof__xek)
    if len(pigmc__rzdj) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return pigmc__rzdj


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    fsyt__fyyv = {}
    uus__cneqz = find_topo_order(blocks)
    soj__qrwk = {}
    for xkm__pkbtr in uus__cneqz:
        block = blocks[xkm__pkbtr]
        pwxq__qbd = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                grt__zmtom = stmt.target.name
                yvdm__smwjs = stmt.value
                if (yvdm__smwjs.op == 'getattr' and yvdm__smwjs.attr in
                    arr_math and isinstance(typemap[yvdm__smwjs.value.name],
                    types.npytypes.Array)):
                    yvdm__smwjs = stmt.value
                    fer__ntz = yvdm__smwjs.value
                    fsyt__fyyv[grt__zmtom] = fer__ntz
                    scope = fer__ntz.scope
                    loc = fer__ntz.loc
                    uubh__bsqh = ir.Var(scope, mk_unique_var('$np_g_var'), loc)
                    typemap[uubh__bsqh.name] = types.misc.Module(numpy)
                    dcq__ivbtb = ir.Global('np', numpy, loc)
                    dqx__ujmx = ir.Assign(dcq__ivbtb, uubh__bsqh, loc)
                    yvdm__smwjs.value = uubh__bsqh
                    pwxq__qbd.append(dqx__ujmx)
                    func_ir._definitions[uubh__bsqh.name] = [dcq__ivbtb]
                    func = getattr(numpy, yvdm__smwjs.attr)
                    twlo__fhna = get_np_ufunc_typ_lst(func)
                    soj__qrwk[grt__zmtom] = twlo__fhna
                if (yvdm__smwjs.op == 'call' and yvdm__smwjs.func.name in
                    fsyt__fyyv):
                    fer__ntz = fsyt__fyyv[yvdm__smwjs.func.name]
                    umzt__xpt = calltypes.pop(yvdm__smwjs)
                    zvheq__ivk = umzt__xpt.args[:len(yvdm__smwjs.args)]
                    velat__pvl = {name: typemap[qof__xek.name] for name,
                        qof__xek in yvdm__smwjs.kws}
                    ior__uipnj = soj__qrwk[yvdm__smwjs.func.name]
                    imrr__qcx = None
                    for hyr__varhv in ior__uipnj:
                        try:
                            imrr__qcx = hyr__varhv.get_call_type(typingctx,
                                [typemap[fer__ntz.name]] + list(zvheq__ivk),
                                velat__pvl)
                            typemap.pop(yvdm__smwjs.func.name)
                            typemap[yvdm__smwjs.func.name] = hyr__varhv
                            calltypes[yvdm__smwjs] = imrr__qcx
                            break
                        except Exception as ttw__woxa:
                            pass
                    if imrr__qcx is None:
                        raise TypeError(
                            f'No valid template found for {yvdm__smwjs.func.name}'
                            )
                    yvdm__smwjs.args = [fer__ntz] + yvdm__smwjs.args
            pwxq__qbd.append(stmt)
        block.body = pwxq__qbd


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    siv__bpy = ufunc.nin
    lul__pbem = ufunc.nout
    ovqj__qsray = ufunc.nargs
    assert ovqj__qsray == siv__bpy + lul__pbem
    if len(args) < siv__bpy:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), siv__bpy))
    if len(args) > ovqj__qsray:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args),
            ovqj__qsray))
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    ixi__wkcek = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    rdaux__qcreu = max(ixi__wkcek)
    ahmud__tgd = args[siv__bpy:]
    if not all(rohiu__yjfen == rdaux__qcreu for rohiu__yjfen in ixi__wkcek[
        siv__bpy:]):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(ncw__edo, types.ArrayCompatible) and not
        isinstance(ncw__edo, types.Bytes) for ncw__edo in ahmud__tgd):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(ncw__edo.mutable for ncw__edo in ahmud__tgd):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    dzozq__xbgh = [(x.dtype if isinstance(x, types.ArrayCompatible) and not
        isinstance(x, types.Bytes) else x) for x in args]
    mob__nbmag = None
    if rdaux__qcreu > 0 and len(ahmud__tgd) < ufunc.nout:
        mob__nbmag = 'C'
        olxb__amaa = [(x.layout if isinstance(x, types.ArrayCompatible) and
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in olxb__amaa and 'F' in olxb__amaa:
            mob__nbmag = 'F'
    return dzozq__xbgh, ahmud__tgd, rdaux__qcreu, mob__nbmag


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.npydecl.Numpy_rules_ufunc.
        _handle_inputs)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '4b97c64ad9c3d50e082538795054f35cf6d2fe962c3ca40e8377a4601b344d5c':
        warnings.warn('Numpy_rules_ufunc._handle_inputs has changed')
numba.core.typing.npydecl.Numpy_rules_ufunc._handle_inputs = (
    _Numpy_Rules_ufunc_handle_inputs)
numba.np.ufunc.dufunc.npydecl.Numpy_rules_ufunc._handle_inputs = (
    _Numpy_Rules_ufunc_handle_inputs)


def DictType__init__(self, keyty, valty, initial_value=None):
    from numba.types import DictType, InitialValue, NoneType, Optional, Tuple, TypeRef, unliteral
    assert not isinstance(keyty, TypeRef)
    assert not isinstance(valty, TypeRef)
    keyty = unliteral(keyty)
    valty = unliteral(valty)
    if isinstance(keyty, (Optional, NoneType)):
        fwwl__colcv = 'Dict.key_type cannot be of type {}'
        raise TypingError(fwwl__colcv.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        fwwl__colcv = 'Dict.value_type cannot be of type {}'
        raise TypingError(fwwl__colcv.format(valty))
    self.key_type = keyty
    self.value_type = valty
    self.keyvalue_type = Tuple([keyty, valty])
    name = '{}[{},{}]<iv={}>'.format(self.__class__.__name__, keyty, valty,
        initial_value)
    super(DictType, self).__init__(name)
    InitialValue.__init__(self, initial_value)


if _check_numba_change:
    lines = inspect.getsource(numba.core.types.containers.DictType.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '475acd71224bd51526750343246e064ff071320c0d10c17b8b8ac81d5070d094':
        warnings.warn('DictType.__init__ has changed')
numba.core.types.containers.DictType.__init__ = DictType__init__


def _legalize_arg_types(self, args):
    for i, a in enumerate(args, start=1):
        if isinstance(a, types.Dispatcher):
            msg = (
                'Does not support function type inputs into with-context for arg {}'
                )
            raise errors.TypingError(msg.format(i))


if _check_numba_change:
    lines = inspect.getsource(numba.core.dispatcher.ObjModeLiftedWith.
        _legalize_arg_types)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '4793f44ebc7da8843e8f298e08cd8a5428b4b84b89fd9d5c650273fdb8fee5ee':
        warnings.warn('ObjModeLiftedWith._legalize_arg_types has changed')
numba.core.dispatcher.ObjModeLiftedWith._legalize_arg_types = (
    _legalize_arg_types)


def _overload_template_get_impl(self, args, kws):
    wlrdz__imvx = self.context, tuple(args), tuple(kws.items())
    try:
        qnq__ymlmu, args = self._impl_cache[wlrdz__imvx]
        return qnq__ymlmu, args
    except KeyError as ttw__woxa:
        pass
    qnq__ymlmu, args = self._build_impl(wlrdz__imvx, args, kws)
    return qnq__ymlmu, args


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.templates.
        _OverloadFunctionTemplate._get_impl)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '4e27d07b214ca16d6e8ed88f70d886b6b095e160d8f77f8df369dd4ed2eb3fae':
        warnings.warn(
            'numba.core.typing.templates._OverloadFunctionTemplate._get_impl has changed'
            )
numba.core.typing.templates._OverloadFunctionTemplate._get_impl = (
    _overload_template_get_impl)


def remove_dead_parfor(parfor, lives, lives_n_aliases, arg_aliases,
    alias_map, func_ir, typemap):
    from numba.core.analysis import compute_cfg_from_blocks, compute_live_map, compute_use_defs
    from numba.core.ir_utils import find_topo_order
    from numba.parfors.parfor import _add_liveness_return_block, _update_parfor_get_setitems, dummy_return_in_loop_body, get_index_var, remove_dead_parfor_recursive, simplify_parfor_body_CFG
    with dummy_return_in_loop_body(parfor.loop_body):
        fdlr__rrc = find_topo_order(parfor.loop_body)
    elf__mytaf = fdlr__rrc[0]
    qkc__nkl = {}
    _update_parfor_get_setitems(parfor.loop_body[elf__mytaf].body, parfor.
        index_var, alias_map, qkc__nkl, lives_n_aliases)
    fwvis__inskt = set(qkc__nkl.keys())
    for qpcq__xogli in fdlr__rrc:
        if qpcq__xogli == elf__mytaf:
            continue
        for stmt in parfor.loop_body[qpcq__xogli].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            qwx__itv = set(qof__xek.name for qof__xek in stmt.list_vars())
            ujxh__zaoa = qwx__itv & fwvis__inskt
            for a in ujxh__zaoa:
                qkc__nkl.pop(a, None)
    for qpcq__xogli in fdlr__rrc:
        if qpcq__xogli == elf__mytaf:
            continue
        block = parfor.loop_body[qpcq__xogli]
        adq__olj = qkc__nkl.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            adq__olj, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    jqxbt__fyrv = max(blocks.keys())
    nye__cqqzd, sgu__wsde = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    tuxp__jimqv = ir.Jump(nye__cqqzd, ir.Loc('parfors_dummy', -1))
    blocks[jqxbt__fyrv].body.append(tuxp__jimqv)
    ruuy__fqfjd = compute_cfg_from_blocks(blocks)
    anhbl__jqft = compute_use_defs(blocks)
    awbmw__zko = compute_live_map(ruuy__fqfjd, blocks, anhbl__jqft.usemap,
        anhbl__jqft.defmap)
    alias_set = set(alias_map.keys())
    for xkm__pkbtr, block in blocks.items():
        pwxq__qbd = []
        jrxnm__awd = {qof__xek.name for qof__xek in block.terminator.
            list_vars()}
        for rrjx__dtgwt, wsevo__suzc in ruuy__fqfjd.successors(xkm__pkbtr):
            jrxnm__awd |= awbmw__zko[rrjx__dtgwt]
        for stmt in reversed(block.body):
            kfks__sxxo = jrxnm__awd & alias_set
            for qof__xek in kfks__sxxo:
                jrxnm__awd |= alias_map[qof__xek]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in jrxnm__awd and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                zfarx__qdimu = guard(find_callname, func_ir, stmt.value)
                if zfarx__qdimu == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in jrxnm__awd and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            jrxnm__awd |= {qof__xek.name for qof__xek in stmt.list_vars()}
            pwxq__qbd.append(stmt)
        pwxq__qbd.reverse()
        block.body = pwxq__qbd
    typemap.pop(sgu__wsde.name)
    blocks[jqxbt__fyrv].body.pop()

    def trim_empty_parfor_branches(parfor):
        elk__ajco = False
        blocks = parfor.loop_body.copy()
        for xkm__pkbtr, block in blocks.items():
            if len(block.body):
                gio__drsm = block.body[-1]
                if isinstance(gio__drsm, ir.Branch):
                    if len(blocks[gio__drsm.truebr].body) == 1 and len(blocks
                        [gio__drsm.falsebr].body) == 1:
                        mnq__kdcg = blocks[gio__drsm.truebr].body[0]
                        rwf__wsh = blocks[gio__drsm.falsebr].body[0]
                        if isinstance(mnq__kdcg, ir.Jump) and isinstance(
                            rwf__wsh, ir.Jump
                            ) and mnq__kdcg.target == rwf__wsh.target:
                            parfor.loop_body[xkm__pkbtr].body[-1] = ir.Jump(
                                mnq__kdcg.target, gio__drsm.loc)
                            elk__ajco = True
                    elif len(blocks[gio__drsm.truebr].body) == 1:
                        mnq__kdcg = blocks[gio__drsm.truebr].body[0]
                        if isinstance(mnq__kdcg, ir.Jump
                            ) and mnq__kdcg.target == gio__drsm.falsebr:
                            parfor.loop_body[xkm__pkbtr].body[-1] = ir.Jump(
                                mnq__kdcg.target, gio__drsm.loc)
                            elk__ajco = True
                    elif len(blocks[gio__drsm.falsebr].body) == 1:
                        rwf__wsh = blocks[gio__drsm.falsebr].body[0]
                        if isinstance(rwf__wsh, ir.Jump
                            ) and rwf__wsh.target == gio__drsm.truebr:
                            parfor.loop_body[xkm__pkbtr].body[-1] = ir.Jump(
                                rwf__wsh.target, gio__drsm.loc)
                            elk__ajco = True
        return elk__ajco
    elk__ajco = True
    while elk__ajco:
        """
        Process parfor body recursively.
        Note that this is the only place in this function that uses the
        argument lives instead of lives_n_aliases.  The former does not
        include the aliases of live variables but only the live variable
        names themselves.  See a comment in this function for how that
        is used.
        """
        remove_dead_parfor_recursive(parfor, lives, arg_aliases, alias_map,
            func_ir, typemap)
        simplify_parfor_body_CFG(func_ir.blocks)
        elk__ajco = trim_empty_parfor_branches(parfor)
    zrja__iqzn = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        zrja__iqzn &= len(block.body) == 0
    if zrja__iqzn:
        return None
    return parfor


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.remove_dead_parfor)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '1c9b008a7ead13e988e1efe67618d8f87f0b9f3d092cc2cd6bfcd806b1fdb859':
        warnings.warn('remove_dead_parfor has changed')
numba.parfors.parfor.remove_dead_parfor = remove_dead_parfor
numba.core.ir_utils.remove_dead_extensions[numba.parfors.parfor.Parfor
    ] = remove_dead_parfor


def simplify_parfor_body_CFG(blocks):
    from numba.core.analysis import compute_cfg_from_blocks
    from numba.core.ir_utils import simplify_CFG
    from numba.parfors.parfor import Parfor
    biduh__smem = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                biduh__smem += 1
                parfor = stmt
                varp__exl = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = varp__exl.scope
                loc = ir.Loc('parfors_dummy', -1)
                hmv__idlmc = ir.Var(scope, mk_unique_var('$const'), loc)
                varp__exl.body.append(ir.Assign(ir.Const(0, loc),
                    hmv__idlmc, loc))
                varp__exl.body.append(ir.Return(hmv__idlmc, loc))
                ruuy__fqfjd = compute_cfg_from_blocks(parfor.loop_body)
                for ngt__hdnjt in ruuy__fqfjd.dead_nodes():
                    del parfor.loop_body[ngt__hdnjt]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                varp__exl = parfor.loop_body[max(parfor.loop_body.keys())]
                varp__exl.body.pop()
                varp__exl.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return biduh__smem


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.simplify_parfor_body_CFG)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '437ae96a5e8ec64a2b69a4f23ba8402a1d170262a5400aa0aa7bfe59e03bf726':
        warnings.warn('simplify_parfor_body_CFG has changed')
numba.parfors.parfor.simplify_parfor_body_CFG = simplify_parfor_body_CFG


def _lifted_compile(self, sig):
    import numba.core.event as ev
    from numba.core import compiler, sigutils
    from numba.core.compiler_lock import global_compiler_lock
    from numba.core.ir_utils import remove_dels
    with ExitStack() as scope:
        cres = None

        def cb_compiler(dur):
            if cres is not None:
                self._callback_add_compiler_timer(dur, cres)

        def cb_llvm(dur):
            if cres is not None:
                self._callback_add_llvm_timer(dur, cres)
        scope.enter_context(ev.install_timer('numba:compiler_lock',
            cb_compiler))
        scope.enter_context(ev.install_timer('numba:llvm_lock', cb_llvm))
        scope.enter_context(global_compiler_lock)
        with self._compiling_counter:
            flags = self.flags
            args, return_type = sigutils.normalize_signature(sig)
            dxtns__yxz = self.overloads.get(tuple(args))
            if dxtns__yxz is not None:
                return dxtns__yxz.entry_point
            self._pre_compile(args, return_type, flags)
            ivd__hlj = self.func_ir
            dunyl__ugnb = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=dunyl__ugnb):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=ivd__hlj, args=args,
                    return_type=return_type, flags=flags, locals=self.
                    locals, lifted=(), lifted_from=self.lifted_from,
                    is_lifted_loop=True)
                if cres.typing_error is not None and not flags.enable_pyobject:
                    raise cres.typing_error
                self.add_overload(cres)
            remove_dels(self.func_ir.blocks)
            return cres.entry_point


if _check_numba_change:
    lines = inspect.getsource(numba.core.dispatcher.LiftedCode.compile)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '1351ebc5d8812dc8da167b30dad30eafb2ca9bf191b49aaed6241c21e03afff1':
        warnings.warn('numba.core.dispatcher.LiftedCode.compile has changed')
numba.core.dispatcher.LiftedCode.compile = _lifted_compile


def compile_ir(typingctx, targetctx, func_ir, args, return_type, flags,
    locals, lifted=(), lifted_from=None, is_lifted_loop=False, library=None,
    pipeline_class=Compiler):
    if is_lifted_loop:
        pdc__dgjse = copy.deepcopy(flags)
        pdc__dgjse.no_rewrites = True

        def compile_local(the_ir, the_flags):
            gyrre__axuuc = pipeline_class(typingctx, targetctx, library,
                args, return_type, the_flags, locals)
            return gyrre__axuuc.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        avquj__kxhd = compile_local(func_ir, pdc__dgjse)
        hwp__jskq = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    hwp__jskq = compile_local(func_ir, flags)
                except Exception as ttw__woxa:
                    pass
        if hwp__jskq is not None:
            cres = hwp__jskq
        else:
            cres = avquj__kxhd
        return cres
    else:
        gyrre__axuuc = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return gyrre__axuuc.compile_ir(func_ir=func_ir, lifted=lifted,
            lifted_from=lifted_from)


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.compile_ir)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'c48ce5493f4c43326e8cbdd46f3ea038b2b9045352d9d25894244798388e5e5b':
        warnings.warn('numba.core.compiler.compile_ir has changed')
numba.core.compiler.compile_ir = compile_ir


def make_constant_array(self, builder, typ, ary):
    import math
    from llvmlite import ir as lir
    from llvmlite.llvmpy.core import Constant, Type
    armm__kxdu = self.get_data_type(typ.dtype)
    gdwz__haaq = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        gdwz__haaq):
        tati__txtyq = ary.ctypes.data
        xrba__yblzy = self.add_dynamic_addr(builder, tati__txtyq, info=str(
            type(tati__txtyq)))
        yrz__okfaz = self.add_dynamic_addr(builder, id(ary), info=str(type(
            ary)))
        self.global_arrays.append(ary)
    else:
        noi__bouo = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            noi__bouo = noi__bouo.view('int64')
        aoe__wdbua = Constant.array(Type.int(8), bytearray(noi__bouo.data))
        xrba__yblzy = cgutils.global_constant(builder, '.const.array.data',
            aoe__wdbua)
        xrba__yblzy.align = self.get_abi_alignment(armm__kxdu)
        yrz__okfaz = None
    wew__yyi = self.get_value_type(types.intp)
    wkop__ssw = [self.get_constant(types.intp, jxtyw__nzrub) for
        jxtyw__nzrub in ary.shape]
    uvct__ktn = Constant.array(wew__yyi, wkop__ssw)
    mkyse__tunc = [self.get_constant(types.intp, jxtyw__nzrub) for
        jxtyw__nzrub in ary.strides]
    djy__rqy = Constant.array(wew__yyi, mkyse__tunc)
    dlbar__eedjf = self.get_constant(types.intp, ary.dtype.itemsize)
    syyqk__qvzz = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        syyqk__qvzz, dlbar__eedjf, xrba__yblzy.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), uvct__ktn, djy__rqy])


if _check_numba_change:
    lines = inspect.getsource(numba.core.base.BaseContext.make_constant_array)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5721b5360b51f782f79bd794f7bf4d48657911ecdc05c30db22fd55f15dad821':
        warnings.warn(
            'numba.core.base.BaseContext.make_constant_array has changed')
numba.core.base.BaseContext.make_constant_array = make_constant_array


def _define_atomic_inc_dec(module, op, ordering):
    from llvmlite import ir as lir
    from numba.core.runtime.nrtdynmod import _word_type
    xmrvf__ttr = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    wxryj__uhaa = lir.Function(module, xmrvf__ttr, name='nrt_atomic_{0}'.
        format(op))
    [dpaeq__qmfff] = wxryj__uhaa.args
    gpv__zvo = wxryj__uhaa.append_basic_block()
    builder = lir.IRBuilder(gpv__zvo)
    ozv__xut = lir.Constant(_word_type, 1)
    if False:
        lfxaa__gmr = builder.atomic_rmw(op, dpaeq__qmfff, ozv__xut,
            ordering=ordering)
        res = getattr(builder, op)(lfxaa__gmr, ozv__xut)
        builder.ret(res)
    else:
        lfxaa__gmr = builder.load(dpaeq__qmfff)
        ykhr__klvwb = getattr(builder, op)(lfxaa__gmr, ozv__xut)
        sgura__dkvkt = builder.icmp_signed('!=', lfxaa__gmr, lir.Constant(
            lfxaa__gmr.type, -1))
        with cgutils.if_likely(builder, sgura__dkvkt):
            builder.store(ykhr__klvwb, dpaeq__qmfff)
        builder.ret(ykhr__klvwb)
    return wxryj__uhaa


if _check_numba_change:
    lines = inspect.getsource(numba.core.runtime.nrtdynmod.
        _define_atomic_inc_dec)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '9cc02c532b2980b6537b702f5608ea603a1ff93c6d3c785ae2cf48bace273f48':
        warnings.warn(
            'numba.core.runtime.nrtdynmod._define_atomic_inc_dec has changed')
numba.core.runtime.nrtdynmod._define_atomic_inc_dec = _define_atomic_inc_dec


def NativeLowering_run_pass(self, state):
    from llvmlite import binding as llvm
    from numba.core import funcdesc, lowering
    from numba.core.typed_passes import fallback_context
    if state.library is None:
        bgb__hvu = state.targetctx.codegen()
        state.library = bgb__hvu.create_library(state.func_id.func_qualname)
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    wpdz__zwr = state.func_ir
    typemap = state.typemap
    ohceb__ockr = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    ohsp__lia = state.metadata
    ujdhl__qkp = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        dka__vuxi = (funcdesc.PythonFunctionDescriptor.
            from_specialized_function(wpdz__zwr, typemap, ohceb__ockr,
            calltypes, mangler=targetctx.mangler, inline=flags.forceinline,
            noalias=flags.noalias, abi_tags=[flags.get_mangle_string()]))
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            cuw__njan = lowering.Lower(targetctx, library, dka__vuxi,
                wpdz__zwr, metadata=ohsp__lia)
            cuw__njan.lower()
            if not flags.no_cpython_wrapper:
                cuw__njan.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(ohceb__ockr, (types.Optional, types.
                        Generator)):
                        pass
                    else:
                        cuw__njan.create_cfunc_wrapper()
            yjrmy__yax = cuw__njan.env
            oyhmg__tlt = cuw__njan.call_helper
            del cuw__njan
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(dka__vuxi, oyhmg__tlt, cfunc=None,
                env=yjrmy__yax)
        else:
            lpu__owv = targetctx.get_executable(library, dka__vuxi, yjrmy__yax)
            targetctx.insert_user_function(lpu__owv, dka__vuxi, [library])
            state['cr'] = _LowerResult(dka__vuxi, oyhmg__tlt, cfunc=
                lpu__owv, env=yjrmy__yax)
        ohsp__lia['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        pel__rvbpd = llvm.passmanagers.dump_refprune_stats()
        ohsp__lia['prune_stats'] = pel__rvbpd - ujdhl__qkp
        ohsp__lia['llvm_pass_timings'] = library.recorded_timings
    return True


if _check_numba_change:
    lines = inspect.getsource(numba.core.typed_passes.NativeLowering.run_pass)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a777ce6ce1bb2b1cbaa3ac6c2c0e2adab69a9c23888dff5f1cbb67bfb176b5de':
        warnings.warn(
            'numba.core.typed_passes.NativeLowering.run_pass has changed')
numba.core.typed_passes.NativeLowering.run_pass = NativeLowering_run_pass


def _python_list_to_native(typ, obj, c, size, listptr, errorptr):
    from llvmlite import ir as lir
    from numba.core.boxing import _NumbaTypeHelper
    from numba.cpython import listobj

    def check_element_type(nth, itemobj, expected_typobj):
        mxcop__gjqvk = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, mxcop__gjqvk),
            likely=False):
            c.builder.store(cgutils.true_bit, errorptr)
            qfc__wqif.do_break()
        hlsa__ifhck = c.builder.icmp_signed('!=', mxcop__gjqvk, expected_typobj
            )
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(hlsa__ifhck, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, mxcop__gjqvk)
                c.pyapi.decref(mxcop__gjqvk)
                qfc__wqif.do_break()
        c.pyapi.decref(mxcop__gjqvk)
    feel__mdz, list = listobj.ListInstance.allocate_ex(c.context, c.builder,
        typ, size)
    with c.builder.if_else(feel__mdz, likely=True) as (whv__olnq, fwwh__uxmhq):
        with whv__olnq:
            list.size = size
            kaj__dps = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                kaj__dps), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        kaj__dps))
                    with cgutils.for_range(c.builder, size) as qfc__wqif:
                        itemobj = c.pyapi.list_getitem(obj, qfc__wqif.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        bix__ohw = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(bix__ohw.is_error, likely=False
                            ):
                            c.builder.store(cgutils.true_bit, errorptr)
                            qfc__wqif.do_break()
                        list.setitem(qfc__wqif.index, bix__ohw.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with fwwh__uxmhq:
            c.builder.store(cgutils.true_bit, errorptr)
    with c.builder.if_then(c.builder.load(errorptr)):
        c.context.nrt.decref(c.builder, typ, list.value)


if _check_numba_change:
    lines = inspect.getsource(numba.core.boxing._python_list_to_native)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'f8e546df8b07adfe74a16b6aafb1d4fddbae7d3516d7944b3247cc7c9b7ea88a':
        warnings.warn('numba.core.boxing._python_list_to_native has changed')
numba.core.boxing._python_list_to_native = _python_list_to_native


def make_string_from_constant(context, builder, typ, literal_string):
    from llvmlite import ir as lir
    from numba.cpython.hashing import _Py_hash_t
    from numba.cpython.unicode import compile_time_get_string_data
    qnab__ckdv, ttlb__hxec, mfp__tuk, auhhs__sbgr, wajw__eoxuf = (
        compile_time_get_string_data(literal_string))
    hhn__grs = builder.module
    gv = context.insert_const_bytes(hhn__grs, qnab__ckdv)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        ttlb__hxec), context.get_constant(types.int32, mfp__tuk), context.
        get_constant(types.uint32, auhhs__sbgr), context.get_constant(
        _Py_hash_t, -1), context.get_constant_null(types.MemInfoPointer(
        types.voidptr)), context.get_constant_null(types.pyobject)])


if _check_numba_change:
    lines = inspect.getsource(numba.cpython.unicode.make_string_from_constant)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '525bd507383e06152763e2f046dae246cd60aba027184f50ef0fc9a80d4cd7fa':
        warnings.warn(
            'numba.cpython.unicode.make_string_from_constant has changed')
numba.cpython.unicode.make_string_from_constant = make_string_from_constant


def parse_shape(shape):
    fymvg__dun = None
    if isinstance(shape, types.Integer):
        fymvg__dun = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(jxtyw__nzrub, (types.Integer, types.IntEnumMember
            )) for jxtyw__nzrub in shape):
            fymvg__dun = len(shape)
    return fymvg__dun


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.npydecl.parse_shape)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'e62e3ff09d36df5ac9374055947d6a8be27160ce32960d3ef6cb67f89bd16429':
        warnings.warn('numba.core.typing.npydecl.parse_shape has changed')
numba.core.typing.npydecl.parse_shape = parse_shape


def _get_names(self, obj):
    if isinstance(obj, ir.Var) or isinstance(obj, str):
        name = obj if isinstance(obj, str) else obj.name
        if name not in self.typemap:
            return name,
        typ = self.typemap[name]
        if isinstance(typ, (types.BaseTuple, types.ArrayCompatible)):
            fymvg__dun = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if fymvg__dun == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(fymvg__dun)
                    )
        else:
            return name,
    elif isinstance(obj, ir.Const):
        if isinstance(obj.value, tuple):
            return obj.value
        else:
            return obj.value,
    elif isinstance(obj, tuple):

        def get_names(x):
            lsdm__lvb = self._get_names(x)
            if len(lsdm__lvb) != 0:
                return lsdm__lvb[0]
            return lsdm__lvb
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    lsdm__lvb = self._get_names(obj)
    if len(lsdm__lvb) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(lsdm__lvb[0])


def get_equiv_set(self, obj):
    lsdm__lvb = self._get_names(obj)
    if len(lsdm__lvb) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(lsdm__lvb[0])


if _check_numba_change:
    for name, orig, new, hash in ((
        'numba.parfors.array_analysis.ShapeEquivSet._get_names', numba.
        parfors.array_analysis.ShapeEquivSet._get_names, _get_names,
        '8c9bf136109028d5445fd0a82387b6abeb70c23b20b41e2b50c34ba5359516ee'),
        ('numba.parfors.array_analysis.ShapeEquivSet.get_equiv_const',
        numba.parfors.array_analysis.ShapeEquivSet.get_equiv_const,
        get_equiv_const,
        'bef410ca31a9e29df9ee74a4a27d339cc332564e4a237828b8a4decf625ce44e'),
        ('numba.parfors.array_analysis.ShapeEquivSet.get_equiv_set', numba.
        parfors.array_analysis.ShapeEquivSet.get_equiv_set, get_equiv_set,
        'ec936d340c488461122eb74f28a28b88227cb1f1bca2b9ba3c19258cfe1eb40a')):
        lines = inspect.getsource(orig)
        if hashlib.sha256(lines.encode()).hexdigest() != hash:
            warnings.warn(f'{name} has changed')
numba.parfors.array_analysis.ShapeEquivSet._get_names = _get_names
numba.parfors.array_analysis.ShapeEquivSet.get_equiv_const = get_equiv_const
numba.parfors.array_analysis.ShapeEquivSet.get_equiv_set = get_equiv_set


def raise_on_unsupported_feature(func_ir, typemap):
    import numpy
    wkq__lzukz = []
    for hzbt__lxcq in func_ir.arg_names:
        if hzbt__lxcq in typemap and isinstance(typemap[hzbt__lxcq], types.
            containers.UniTuple) and typemap[hzbt__lxcq].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(hzbt__lxcq))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for npe__jepzh in func_ir.blocks.values():
        for stmt in npe__jepzh.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    yivh__tzng = getattr(val, 'code', None)
                    if yivh__tzng is not None:
                        if getattr(val, 'closure', None) is not None:
                            ulow__uqz = '<creating a function from a closure>'
                            uxdtc__lesvs = ''
                        else:
                            ulow__uqz = yivh__tzng.co_name
                            uxdtc__lesvs = '(%s) ' % ulow__uqz
                    else:
                        ulow__uqz = '<could not ascertain use case>'
                        uxdtc__lesvs = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (ulow__uqz, uxdtc__lesvs))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                endxz__bsl = False
                if isinstance(val, pytypes.FunctionType):
                    endxz__bsl = val in {numba.gdb, numba.gdb_init}
                if not endxz__bsl:
                    endxz__bsl = getattr(val, '_name', '') == 'gdb_internal'
                if endxz__bsl:
                    wkq__lzukz.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    qoxw__clf = func_ir.get_definition(var)
                    iiu__exk = guard(find_callname, func_ir, qoxw__clf)
                    if iiu__exk and iiu__exk[1] == 'numpy':
                        ty = getattr(numpy, iiu__exk[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    llj__miigj = '' if var.startswith('$') else "'{}' ".format(
                        var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(llj__miigj), loc=stmt.loc)
            if isinstance(stmt.value, ir.Global):
                ty = typemap[stmt.target.name]
                msg = (
                    "The use of a %s type, assigned to variable '%s' in globals, is not supported as globals are considered compile-time constants and there is no known way to compile a %s type as a constant."
                    )
                if isinstance(ty, types.ListType):
                    raise TypingError(msg % (ty, stmt.value.name, ty), loc=
                        stmt.loc)
            if isinstance(stmt.value, ir.Yield) and not func_ir.is_generator:
                msg = 'The use of generator expressions is unsupported.'
                raise errors.UnsupportedError(msg, loc=stmt.loc)
    if len(wkq__lzukz) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        aerb__iombm = '\n'.join([x.strformat() for x in wkq__lzukz])
        raise errors.UnsupportedError(msg % aerb__iombm)


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.raise_on_unsupported_feature)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '237a4fe8395a40899279c718bc3754102cd2577463ef2f48daceea78d79b2d5e':
        warnings.warn(
            'numba.core.ir_utils.raise_on_unsupported_feature has changed')
numba.core.ir_utils.raise_on_unsupported_feature = raise_on_unsupported_feature
numba.core.typed_passes.raise_on_unsupported_feature = (
    raise_on_unsupported_feature)


@typeof_impl.register(dict)
def _typeof_dict(val, c):
    if len(val) == 0:
        raise ValueError('Cannot type empty dict')
    maxo__nqq, qof__xek = next(iter(val.items()))
    bsgii__kqrmy = typeof_impl(maxo__nqq, c)
    czrjd__scu = typeof_impl(qof__xek, c)
    if bsgii__kqrmy is None or czrjd__scu is None:
        raise ValueError(
            f'Cannot type dict element type {type(maxo__nqq)}, {type(qof__xek)}'
            )
    return types.DictType(bsgii__kqrmy, czrjd__scu)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    iqcar__qikk = cgutils.alloca_once_value(c.builder, val)
    vjsmm__pzdvc = c.pyapi.object_hasattr_string(val, '_opaque')
    olkde__jsvq = c.builder.icmp_unsigned('==', vjsmm__pzdvc, lir.Constant(
        vjsmm__pzdvc.type, 0))
    uuxnx__uryg = typ.key_type
    emid__qedij = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(uuxnx__uryg, emid__qedij)

    def copy_dict(out_dict, in_dict):
        for maxo__nqq, qof__xek in in_dict.items():
            out_dict[maxo__nqq] = qof__xek
    with c.builder.if_then(olkde__jsvq):
        ynjk__jkip = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        phpxn__qmxi = c.pyapi.call_function_objargs(ynjk__jkip, [])
        yeok__rhp = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(yeok__rhp, [phpxn__qmxi, val])
        c.builder.store(phpxn__qmxi, iqcar__qikk)
    val = c.builder.load(iqcar__qikk)
    iga__fin = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    wdsa__amv = c.pyapi.object_type(val)
    zdtdn__oqoz = c.builder.icmp_unsigned('==', wdsa__amv, iga__fin)
    with c.builder.if_else(zdtdn__oqoz) as (buoih__tkeh, pauxd__rud):
        with buoih__tkeh:
            vel__ohhb = c.pyapi.object_getattr_string(val, '_opaque')
            cuaq__iofpl = types.MemInfoPointer(types.voidptr)
            bix__ohw = c.unbox(cuaq__iofpl, vel__ohhb)
            mi = bix__ohw.value
            qurk__gdiav = cuaq__iofpl, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *qurk__gdiav)
            yndym__czlp = context.get_constant_null(qurk__gdiav[1])
            args = mi, yndym__czlp
            xlfwm__ljh, rhuwo__yfs = c.pyapi.call_jit_code(convert, sig, args)
            c.context.nrt.decref(c.builder, typ, rhuwo__yfs)
            c.pyapi.decref(vel__ohhb)
            yiu__izfpw = c.builder.basic_block
        with pauxd__rud:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", wdsa__amv, iga__fin)
            ajxbz__mihh = c.builder.basic_block
    yzh__wxmy = c.builder.phi(rhuwo__yfs.type)
    qly__sadp = c.builder.phi(xlfwm__ljh.type)
    yzh__wxmy.add_incoming(rhuwo__yfs, yiu__izfpw)
    yzh__wxmy.add_incoming(rhuwo__yfs.type(None), ajxbz__mihh)
    qly__sadp.add_incoming(xlfwm__ljh, yiu__izfpw)
    qly__sadp.add_incoming(cgutils.true_bit, ajxbz__mihh)
    c.pyapi.decref(iga__fin)
    c.pyapi.decref(wdsa__amv)
    with c.builder.if_then(olkde__jsvq):
        c.pyapi.decref(val)
    return NativeValue(yzh__wxmy, is_error=qly__sadp)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, zmj__kdbx = args
    if isinstance(a, types.List) and isinstance(zmj__kdbx, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(zmj__kdbx, types.List):
        return signature(zmj__kdbx, types.intp, zmj__kdbx)


if _check_numba_change:
    lines = inspect.getsource(numba.core.typing.listdecl.MulList.generic)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '95882385a8ffa67aa576e8169b9ee6b3197e0ad3d5def4b47fa65ce8cd0f1575':
        warnings.warn('numba.core.typing.listdecl.MulList.generic has changed')
numba.core.typing.listdecl.MulList.generic = mul_list_generic


@lower_builtin(operator.mul, types.Integer, types.List)
def list_mul(context, builder, sig, args):
    from llvmlite import ir as lir
    from numba.core.imputils import impl_ret_new_ref
    from numba.cpython.listobj import ListInstance
    if isinstance(sig.args[0], types.List):
        qrpzy__zsyet, yqlqy__ihh = 0, 1
    else:
        qrpzy__zsyet, yqlqy__ihh = 1, 0
    smbxh__uoz = ListInstance(context, builder, sig.args[qrpzy__zsyet],
        args[qrpzy__zsyet])
    vilqp__can = smbxh__uoz.size
    tkrz__ootkf = args[yqlqy__ihh]
    kaj__dps = lir.Constant(tkrz__ootkf.type, 0)
    tkrz__ootkf = builder.select(cgutils.is_neg_int(builder, tkrz__ootkf),
        kaj__dps, tkrz__ootkf)
    syyqk__qvzz = builder.mul(tkrz__ootkf, vilqp__can)
    cruow__cbp = ListInstance.allocate(context, builder, sig.return_type,
        syyqk__qvzz)
    cruow__cbp.size = syyqk__qvzz
    with cgutils.for_range_slice(builder, kaj__dps, syyqk__qvzz, vilqp__can,
        inc=True) as (nnmvh__ckrct, _):
        with cgutils.for_range(builder, vilqp__can) as qfc__wqif:
            value = smbxh__uoz.getitem(qfc__wqif.index)
            cruow__cbp.setitem(builder.add(qfc__wqif.index, nnmvh__ckrct),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, cruow__cbp.value
        )


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    syyqk__qvzz = payload.used
    listobj = c.pyapi.list_new(syyqk__qvzz)
    feel__mdz = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(feel__mdz, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(
            syyqk__qvzz.type, 0))
        with payload._iterate() as qfc__wqif:
            i = c.builder.load(index)
            item = qfc__wqif.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return feel__mdz, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    hqme__pylxw = h.type
    miso__quyzj = self.mask
    dtype = self._ty.dtype
    nqhd__jiuje = context.typing_context
    fnty = nqhd__jiuje.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(nqhd__jiuje, (dtype, dtype), {})
    oleys__rkvd = context.get_function(fnty, sig)
    dma__vqspg = ir.Constant(hqme__pylxw, 1)
    ybuvb__qce = ir.Constant(hqme__pylxw, 5)
    fwg__fyzq = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, miso__quyzj))
    if for_insert:
        uxooc__tpavm = miso__quyzj.type(-1)
        bvbq__zmmn = cgutils.alloca_once_value(builder, uxooc__tpavm)
    isffg__sffy = builder.append_basic_block('lookup.body')
    eux__jau = builder.append_basic_block('lookup.found')
    jzvh__cqpm = builder.append_basic_block('lookup.not_found')
    sgkz__cacn = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        loomf__uev = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, loomf__uev)):
            oyoa__tsuzr = oleys__rkvd(builder, (item, entry.key))
            with builder.if_then(oyoa__tsuzr):
                builder.branch(eux__jau)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, loomf__uev)):
            builder.branch(jzvh__cqpm)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, loomf__uev)):
                lhzuq__onxk = builder.load(bvbq__zmmn)
                lhzuq__onxk = builder.select(builder.icmp_unsigned('==',
                    lhzuq__onxk, uxooc__tpavm), i, lhzuq__onxk)
                builder.store(lhzuq__onxk, bvbq__zmmn)
    with cgutils.for_range(builder, ir.Constant(hqme__pylxw, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, dma__vqspg)
        i = builder.and_(i, miso__quyzj)
        builder.store(i, index)
    builder.branch(isffg__sffy)
    with builder.goto_block(isffg__sffy):
        i = builder.load(index)
        check_entry(i)
        vlatk__hopo = builder.load(fwg__fyzq)
        vlatk__hopo = builder.lshr(vlatk__hopo, ybuvb__qce)
        i = builder.add(dma__vqspg, builder.mul(i, ybuvb__qce))
        i = builder.and_(miso__quyzj, builder.add(i, vlatk__hopo))
        builder.store(i, index)
        builder.store(vlatk__hopo, fwg__fyzq)
        builder.branch(isffg__sffy)
    with builder.goto_block(jzvh__cqpm):
        if for_insert:
            i = builder.load(index)
            lhzuq__onxk = builder.load(bvbq__zmmn)
            i = builder.select(builder.icmp_unsigned('==', lhzuq__onxk,
                uxooc__tpavm), i, lhzuq__onxk)
            builder.store(i, index)
        builder.branch(sgkz__cacn)
    with builder.goto_block(eux__jau):
        builder.branch(sgkz__cacn)
    builder.position_at_end(sgkz__cacn)
    endxz__bsl = builder.phi(ir.IntType(1), 'found')
    endxz__bsl.add_incoming(cgutils.true_bit, eux__jau)
    endxz__bsl.add_incoming(cgutils.false_bit, jzvh__cqpm)
    return endxz__bsl, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    wacv__srcs = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    bgxq__etefe = payload.used
    dma__vqspg = ir.Constant(bgxq__etefe.type, 1)
    bgxq__etefe = payload.used = builder.add(bgxq__etefe, dma__vqspg)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, wacv__srcs), likely=True):
        payload.fill = builder.add(payload.fill, dma__vqspg)
    if do_resize:
        self.upsize(bgxq__etefe)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    endxz__bsl, i = payload._lookup(item, h, for_insert=True)
    wbt__vuzmp = builder.not_(endxz__bsl)
    with builder.if_then(wbt__vuzmp):
        entry = payload.get_entry(i)
        wacv__srcs = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        bgxq__etefe = payload.used
        dma__vqspg = ir.Constant(bgxq__etefe.type, 1)
        bgxq__etefe = payload.used = builder.add(bgxq__etefe, dma__vqspg)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, wacv__srcs), likely=True):
            payload.fill = builder.add(payload.fill, dma__vqspg)
        if do_resize:
            self.upsize(bgxq__etefe)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    bgxq__etefe = payload.used
    dma__vqspg = ir.Constant(bgxq__etefe.type, 1)
    bgxq__etefe = payload.used = self._builder.sub(bgxq__etefe, dma__vqspg)
    if do_resize:
        self.downsize(bgxq__etefe)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    qjtra__mlq = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, qjtra__mlq)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    rrcvx__hczz = payload
    feel__mdz = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(feel__mdz), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with rrcvx__hczz._iterate() as qfc__wqif:
        entry = qfc__wqif.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(rrcvx__hczz.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as qfc__wqif:
        entry = qfc__wqif.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    feel__mdz = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(feel__mdz), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    feel__mdz = cgutils.alloca_once_value(builder, cgutils.true_bit)
    hqme__pylxw = context.get_value_type(types.intp)
    kaj__dps = ir.Constant(hqme__pylxw, 0)
    dma__vqspg = ir.Constant(hqme__pylxw, 1)
    oqzly__xtbay = context.get_data_type(types.SetPayload(self._ty))
    qqz__tbpc = context.get_abi_sizeof(oqzly__xtbay)
    oubg__zqm = self._entrysize
    qqz__tbpc -= oubg__zqm
    wxjl__wghfq, rxgli__xvr = cgutils.muladd_with_overflow(builder,
        nentries, ir.Constant(hqme__pylxw, oubg__zqm), ir.Constant(
        hqme__pylxw, qqz__tbpc))
    with builder.if_then(rxgli__xvr, likely=False):
        builder.store(cgutils.false_bit, feel__mdz)
    with builder.if_then(builder.load(feel__mdz), likely=True):
        if realloc:
            ruyx__jlikj = self._set.meminfo
            dpaeq__qmfff = context.nrt.meminfo_varsize_alloc(builder,
                ruyx__jlikj, size=wxjl__wghfq)
            oeifi__tzfyd = cgutils.is_null(builder, dpaeq__qmfff)
        else:
            dqhca__etmh = _imp_dtor(context, builder.module, self._ty)
            ruyx__jlikj = context.nrt.meminfo_new_varsize_dtor(builder,
                wxjl__wghfq, builder.bitcast(dqhca__etmh, cgutils.voidptr_t))
            oeifi__tzfyd = cgutils.is_null(builder, ruyx__jlikj)
        with builder.if_else(oeifi__tzfyd, likely=False) as (juz__unpp,
            whv__olnq):
            with juz__unpp:
                builder.store(cgutils.false_bit, feel__mdz)
            with whv__olnq:
                if not realloc:
                    self._set.meminfo = ruyx__jlikj
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, wxjl__wghfq, 255)
                payload.used = kaj__dps
                payload.fill = kaj__dps
                payload.finger = kaj__dps
                qlu__gmd = builder.sub(nentries, dma__vqspg)
                payload.mask = qlu__gmd
    return builder.load(feel__mdz)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    feel__mdz = cgutils.alloca_once_value(builder, cgutils.true_bit)
    hqme__pylxw = context.get_value_type(types.intp)
    kaj__dps = ir.Constant(hqme__pylxw, 0)
    dma__vqspg = ir.Constant(hqme__pylxw, 1)
    oqzly__xtbay = context.get_data_type(types.SetPayload(self._ty))
    qqz__tbpc = context.get_abi_sizeof(oqzly__xtbay)
    oubg__zqm = self._entrysize
    qqz__tbpc -= oubg__zqm
    miso__quyzj = src_payload.mask
    nentries = builder.add(dma__vqspg, miso__quyzj)
    wxjl__wghfq = builder.add(ir.Constant(hqme__pylxw, qqz__tbpc), builder.
        mul(ir.Constant(hqme__pylxw, oubg__zqm), nentries))
    with builder.if_then(builder.load(feel__mdz), likely=True):
        dqhca__etmh = _imp_dtor(context, builder.module, self._ty)
        ruyx__jlikj = context.nrt.meminfo_new_varsize_dtor(builder,
            wxjl__wghfq, builder.bitcast(dqhca__etmh, cgutils.voidptr_t))
        oeifi__tzfyd = cgutils.is_null(builder, ruyx__jlikj)
        with builder.if_else(oeifi__tzfyd, likely=False) as (juz__unpp,
            whv__olnq):
            with juz__unpp:
                builder.store(cgutils.false_bit, feel__mdz)
            with whv__olnq:
                self._set.meminfo = ruyx__jlikj
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = kaj__dps
                payload.mask = miso__quyzj
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, oubg__zqm)
                with src_payload._iterate() as qfc__wqif:
                    context.nrt.incref(builder, self._ty.dtype, qfc__wqif.
                        entry.key)
    return builder.load(feel__mdz)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    rej__tmiad = context.get_value_type(types.voidptr)
    voj__pigiy = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [rej__tmiad, voj__pigiy, rej__tmiad])
    vnghe__rojci = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=vnghe__rojci)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        ktxyl__bppl = builder.bitcast(fn.args[0], cgutils.voidptr_t.
            as_pointer())
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, ktxyl__bppl)
        with payload._iterate() as qfc__wqif:
            entry = qfc__wqif.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    ynsd__aqkp, = sig.args
    jop__fkdv, = args
    nze__ttlxe = numba.core.imputils.call_len(context, builder, ynsd__aqkp,
        jop__fkdv)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, nze__ttlxe)
    with numba.core.imputils.for_iter(context, builder, ynsd__aqkp, jop__fkdv
        ) as qfc__wqif:
        inst.add(qfc__wqif.value)
        context.nrt.decref(builder, set_type.dtype, qfc__wqif.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    ynsd__aqkp = sig.args[1]
    jop__fkdv = args[1]
    nze__ttlxe = numba.core.imputils.call_len(context, builder, ynsd__aqkp,
        jop__fkdv)
    if nze__ttlxe is not None:
        jpukl__sqljh = builder.add(inst.payload.used, nze__ttlxe)
        inst.upsize(jpukl__sqljh)
    with numba.core.imputils.for_iter(context, builder, ynsd__aqkp, jop__fkdv
        ) as qfc__wqif:
        qtg__lnnl = context.cast(builder, qfc__wqif.value, ynsd__aqkp.dtype,
            inst.dtype)
        inst.add(qtg__lnnl)
        context.nrt.decref(builder, ynsd__aqkp.dtype, qfc__wqif.value)
    if nze__ttlxe is not None:
        inst.downsize(inst.payload.used)
    return context.get_dummy_value()


if _check_numba_change:
    for name, orig, hash in ((
        'numba.core.boxing._native_set_to_python_list', numba.core.boxing.
        _native_set_to_python_list,
        'b47f3d5e582c05d80899ee73e1c009a7e5121e7a660d42cb518bb86933f3c06f'),
        ('numba.cpython.setobj._SetPayload._lookup', numba.cpython.setobj.
        _SetPayload._lookup,
        'c797b5399d7b227fe4eea3a058b3d3103f59345699388afb125ae47124bee395'),
        ('numba.cpython.setobj.SetInstance._add_entry', numba.cpython.
        setobj.SetInstance._add_entry,
        'c5ed28a5fdb453f242e41907cb792b66da2df63282c17abe0b68fc46782a7f94'),
        ('numba.cpython.setobj.SetInstance._add_key', numba.cpython.setobj.
        SetInstance._add_key,
        '324d6172638d02a361cfa0ca7f86e241e5a56a008d4ab581a305f9ae5ea4a75f'),
        ('numba.cpython.setobj.SetInstance._remove_entry', numba.cpython.
        setobj.SetInstance._remove_entry,
        '2c441b00daac61976e673c0e738e8e76982669bd2851951890dd40526fa14da1'),
        ('numba.cpython.setobj.SetInstance.pop', numba.cpython.setobj.
        SetInstance.pop,
        '1a7b7464cbe0577f2a38f3af9acfef6d4d25d049b1e216157275fbadaab41d1b'),
        ('numba.cpython.setobj.SetInstance._resize', numba.cpython.setobj.
        SetInstance._resize,
        '5ca5c2ba4f8c4bf546fde106b9c2656d4b22a16d16e163fb64c5d85ea4d88746'),
        ('numba.cpython.setobj.SetInstance._replace_payload', numba.cpython
        .setobj.SetInstance._replace_payload,
        'ada75a6c85828bff69c8469538c1979801f560a43fb726221a9c21bf208ae78d'),
        ('numba.cpython.setobj.SetInstance._allocate_payload', numba.
        cpython.setobj.SetInstance._allocate_payload,
        '2e80c419df43ebc71075b4f97fc1701c10dbc576aed248845e176b8d5829e61b'),
        ('numba.cpython.setobj.SetInstance._copy_payload', numba.cpython.
        setobj.SetInstance._copy_payload,
        '0885ac36e1eb5a0a0fc4f5d91e54b2102b69e536091fed9f2610a71d225193ec'),
        ('numba.cpython.setobj.set_constructor', numba.cpython.setobj.
        set_constructor,
        '3d521a60c3b8eaf70aa0f7267427475dfddd8f5e5053b5bfe309bb5f1891b0ce'),
        ('numba.cpython.setobj.set_update', numba.cpython.setobj.set_update,
        '965c4f7f7abcea5cbe0491b602e6d4bcb1800fa1ec39b1ffccf07e1bc56051c3')):
        lines = inspect.getsource(orig)
        if hashlib.sha256(lines.encode()).hexdigest() != hash:
            warnings.warn(f'{name} has changed')
        orig = new
numba.core.boxing._native_set_to_python_list = _native_set_to_python_list
numba.cpython.setobj._SetPayload._lookup = _lookup
numba.cpython.setobj.SetInstance._add_entry = _add_entry
numba.cpython.setobj.SetInstance._add_key = _add_key
numba.cpython.setobj.SetInstance._remove_entry = _remove_entry
numba.cpython.setobj.SetInstance.pop = pop
numba.cpython.setobj.SetInstance._resize = _resize
numba.cpython.setobj.SetInstance._replace_payload = _replace_payload
numba.cpython.setobj.SetInstance._allocate_payload = _allocate_payload
numba.cpython.setobj.SetInstance._copy_payload = _copy_payload
