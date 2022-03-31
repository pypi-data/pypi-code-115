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
    gin__eshcj = numba.core.bytecode.FunctionIdentity.from_function(func)
    njlk__efph = numba.core.interpreter.Interpreter(gin__eshcj)
    uvs__xmpu = numba.core.bytecode.ByteCode(func_id=gin__eshcj)
    func_ir = njlk__efph.interpret(uvs__xmpu)
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
        hmkrf__svsd = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        hmkrf__svsd.run()
    fxbc__yfd = numba.core.postproc.PostProcessor(func_ir)
    fxbc__yfd.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, rqda__rlb in visit_vars_extensions.items():
        if isinstance(stmt, t):
            rqda__rlb(stmt, callback, cbdata)
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
    saxup__mcal = ['ravel', 'transpose', 'reshape']
    for sovge__mdhtc in blocks.values():
        for sun__bev in sovge__mdhtc.body:
            if type(sun__bev) in alias_analysis_extensions:
                rqda__rlb = alias_analysis_extensions[type(sun__bev)]
                rqda__rlb(sun__bev, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(sun__bev, ir.Assign):
                hnvbm__rtgpl = sun__bev.value
                qpizp__wzmqq = sun__bev.target.name
                if is_immutable_type(qpizp__wzmqq, typemap):
                    continue
                if isinstance(hnvbm__rtgpl, ir.Var
                    ) and qpizp__wzmqq != hnvbm__rtgpl.name:
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.name, alias_map,
                        arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr) and (hnvbm__rtgpl.op ==
                    'cast' or hnvbm__rtgpl.op in ['getitem', 'static_getitem']
                    ):
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.value.name,
                        alias_map, arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr
                    ) and hnvbm__rtgpl.op == 'inplace_binop':
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.lhs.name,
                        alias_map, arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr
                    ) and hnvbm__rtgpl.op == 'getattr' and hnvbm__rtgpl.attr in [
                    'T', 'ctypes', 'flat']:
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.value.name,
                        alias_map, arg_aliases)
                if (isinstance(hnvbm__rtgpl, ir.Expr) and hnvbm__rtgpl.op ==
                    'getattr' and hnvbm__rtgpl.attr not in ['shape'] and 
                    hnvbm__rtgpl.value.name in arg_aliases):
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.value.name,
                        alias_map, arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr
                    ) and hnvbm__rtgpl.op == 'getattr' and hnvbm__rtgpl.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(qpizp__wzmqq, hnvbm__rtgpl.value.name,
                        alias_map, arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr) and hnvbm__rtgpl.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(qpizp__wzmqq, typemap):
                    for zwl__spy in hnvbm__rtgpl.items:
                        _add_alias(qpizp__wzmqq, zwl__spy.name, alias_map,
                            arg_aliases)
                if isinstance(hnvbm__rtgpl, ir.Expr
                    ) and hnvbm__rtgpl.op == 'call':
                    oiock__onoc = guard(find_callname, func_ir,
                        hnvbm__rtgpl, typemap)
                    if oiock__onoc is None:
                        continue
                    bda__otmfr, yrhmb__rtae = oiock__onoc
                    if oiock__onoc in alias_func_extensions:
                        tcq__motc = alias_func_extensions[oiock__onoc]
                        tcq__motc(qpizp__wzmqq, hnvbm__rtgpl.args,
                            alias_map, arg_aliases)
                    if yrhmb__rtae == 'numpy' and bda__otmfr in saxup__mcal:
                        _add_alias(qpizp__wzmqq, hnvbm__rtgpl.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(yrhmb__rtae, ir.Var
                        ) and bda__otmfr in saxup__mcal:
                        _add_alias(qpizp__wzmqq, yrhmb__rtae.name,
                            alias_map, arg_aliases)
    xrlm__cavux = copy.deepcopy(alias_map)
    for zwl__spy in xrlm__cavux:
        for ybitp__obv in xrlm__cavux[zwl__spy]:
            alias_map[zwl__spy] |= alias_map[ybitp__obv]
        for ybitp__obv in xrlm__cavux[zwl__spy]:
            alias_map[ybitp__obv] = alias_map[zwl__spy]
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
    zjish__fhrra = compute_cfg_from_blocks(func_ir.blocks)
    jpq__iqa = compute_use_defs(func_ir.blocks)
    rjw__nhpu = compute_live_map(zjish__fhrra, func_ir.blocks, jpq__iqa.
        usemap, jpq__iqa.defmap)
    nbijv__zdolv = True
    while nbijv__zdolv:
        nbijv__zdolv = False
        for jnzj__dfbcs, block in func_ir.blocks.items():
            lives = {zwl__spy.name for zwl__spy in block.terminator.list_vars()
                }
            for njv__xdi, tfy__sub in zjish__fhrra.successors(jnzj__dfbcs):
                lives |= rjw__nhpu[njv__xdi]
            guhy__idejo = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    qpizp__wzmqq = stmt.target
                    mgbgh__zdfy = stmt.value
                    if qpizp__wzmqq.name not in lives:
                        if isinstance(mgbgh__zdfy, ir.Expr
                            ) and mgbgh__zdfy.op == 'make_function':
                            continue
                        if isinstance(mgbgh__zdfy, ir.Expr
                            ) and mgbgh__zdfy.op == 'getattr':
                            continue
                        if isinstance(mgbgh__zdfy, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(qpizp__wzmqq,
                            None), types.Function):
                            continue
                        if isinstance(mgbgh__zdfy, ir.Expr
                            ) and mgbgh__zdfy.op == 'build_map':
                            continue
                    if isinstance(mgbgh__zdfy, ir.Var
                        ) and qpizp__wzmqq.name == mgbgh__zdfy.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    tws__aszm = analysis.ir_extension_usedefs[type(stmt)]
                    rik__tlh, feg__nelkk = tws__aszm(stmt)
                    lives -= feg__nelkk
                    lives |= rik__tlh
                else:
                    lives |= {zwl__spy.name for zwl__spy in stmt.list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(qpizp__wzmqq.name)
                guhy__idejo.append(stmt)
            guhy__idejo.reverse()
            if len(block.body) != len(guhy__idejo):
                nbijv__zdolv = True
            block.body = guhy__idejo


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    fcon__svka = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (fcon__svka,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    ycjww__aqj = dict(key=func, _overload_func=staticmethod(overload_func),
        _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), ycjww__aqj)


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
            for xlw__gqk in fnty.templates:
                self._inline_overloads.update(xlw__gqk._inline_overloads)
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
    ycjww__aqj = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), ycjww__aqj)
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
    crds__awlzd, brqe__blc = self._get_impl(args, kws)
    if crds__awlzd is None:
        return
    vnn__zeqey = types.Dispatcher(crds__awlzd)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        twri__cmynv = crds__awlzd._compiler
        flags = compiler.Flags()
        ncup__tqigg = twri__cmynv.targetdescr.typing_context
        nhbij__eoqi = twri__cmynv.targetdescr.target_context
        gxwz__nkgj = twri__cmynv.pipeline_class(ncup__tqigg, nhbij__eoqi,
            None, None, None, flags, None)
        ijia__kskf = InlineWorker(ncup__tqigg, nhbij__eoqi, twri__cmynv.
            locals, gxwz__nkgj, flags, None)
        fndxz__klaky = vnn__zeqey.dispatcher.get_call_template
        xlw__gqk, rxza__yrbfi, gdayz__yvjq, kws = fndxz__klaky(brqe__blc, kws)
        if gdayz__yvjq in self._inline_overloads:
            return self._inline_overloads[gdayz__yvjq]['iinfo'].signature
        ir = ijia__kskf.run_untyped_passes(vnn__zeqey.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, nhbij__eoqi, ir, gdayz__yvjq, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, gdayz__yvjq, None)
        self._inline_overloads[sig.args] = {'folded_args': gdayz__yvjq}
        ejpk__ylqdj = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = ejpk__ylqdj
        if not self._inline.is_always_inline:
            sig = vnn__zeqey.get_call_type(self.context, brqe__blc, kws)
            self._compiled_overloads[sig.args] = vnn__zeqey.get_overload(sig)
        zusp__nap = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': gdayz__yvjq,
            'iinfo': zusp__nap}
    else:
        sig = vnn__zeqey.get_call_type(self.context, brqe__blc, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = vnn__zeqey.get_overload(sig)
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
    jopt__cbtae = [True, False]
    hlwa__hac = [False, True]
    avoo__njn = _ResolutionFailures(context, self, args, kws, depth=self._depth
        )
    from numba.core.target_extension import get_local_target
    ksvqh__ndaf = get_local_target(context)
    rik__bkrma = utils.order_by_target_specificity(ksvqh__ndaf, self.
        templates, fnkey=self.key[0])
    self._depth += 1
    for vrby__ivyvy in rik__bkrma:
        nfos__flhrw = vrby__ivyvy(context)
        derl__fqh = jopt__cbtae if nfos__flhrw.prefer_literal else hlwa__hac
        derl__fqh = [True] if getattr(nfos__flhrw, '_no_unliteral', False
            ) else derl__fqh
        for lwnz__ubop in derl__fqh:
            try:
                if lwnz__ubop:
                    sig = nfos__flhrw.apply(args, kws)
                else:
                    sgk__qipuk = tuple([_unlit_non_poison(a) for a in args])
                    fqjm__ohaoy = {crp__cnln: _unlit_non_poison(zwl__spy) for
                        crp__cnln, zwl__spy in kws.items()}
                    sig = nfos__flhrw.apply(sgk__qipuk, fqjm__ohaoy)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    avoo__njn.add_error(nfos__flhrw, False, e, lwnz__ubop)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = nfos__flhrw.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    pnjxr__psx = getattr(nfos__flhrw, 'cases', None)
                    if pnjxr__psx is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            pnjxr__psx)
                    else:
                        msg = 'No match.'
                    avoo__njn.add_error(nfos__flhrw, True, msg, lwnz__ubop)
    avoo__njn.raise_error()


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
    xlw__gqk = self.template(context)
    byole__rxx = None
    wogxb__oyjf = None
    fla__uvbs = None
    derl__fqh = [True, False] if xlw__gqk.prefer_literal else [False, True]
    derl__fqh = [True] if getattr(xlw__gqk, '_no_unliteral', False
        ) else derl__fqh
    for lwnz__ubop in derl__fqh:
        if lwnz__ubop:
            try:
                fla__uvbs = xlw__gqk.apply(args, kws)
            except Exception as bdgdz__fdga:
                if isinstance(bdgdz__fdga, errors.ForceLiteralArg):
                    raise bdgdz__fdga
                byole__rxx = bdgdz__fdga
                fla__uvbs = None
            else:
                break
        else:
            paj__wcfzi = tuple([_unlit_non_poison(a) for a in args])
            qeez__gcfnb = {crp__cnln: _unlit_non_poison(zwl__spy) for 
                crp__cnln, zwl__spy in kws.items()}
            eumo__xlnud = paj__wcfzi == args and kws == qeez__gcfnb
            if not eumo__xlnud and fla__uvbs is None:
                try:
                    fla__uvbs = xlw__gqk.apply(paj__wcfzi, qeez__gcfnb)
                except Exception as bdgdz__fdga:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(
                        bdgdz__fdga, errors.NumbaError):
                        raise bdgdz__fdga
                    if isinstance(bdgdz__fdga, errors.ForceLiteralArg):
                        if xlw__gqk.prefer_literal:
                            raise bdgdz__fdga
                    wogxb__oyjf = bdgdz__fdga
                else:
                    break
    if fla__uvbs is None and (wogxb__oyjf is not None or byole__rxx is not None
        ):
        ctp__dch = '- Resolution failure for {} arguments:\n{}\n'
        zmjk__hnqzf = _termcolor.highlight(ctp__dch)
        if numba.core.config.DEVELOPER_MODE:
            qolzj__unoz = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    jszld__arja = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    jszld__arja = ['']
                zooib__tyqto = '\n{}'.format(2 * qolzj__unoz)
                vrla__kxq = _termcolor.reset(zooib__tyqto + zooib__tyqto.
                    join(_bt_as_lines(jszld__arja)))
                return _termcolor.reset(vrla__kxq)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            zkimv__xnzy = str(e)
            zkimv__xnzy = zkimv__xnzy if zkimv__xnzy else str(repr(e)
                ) + add_bt(e)
            trplz__zsbrm = errors.TypingError(textwrap.dedent(zkimv__xnzy))
            return zmjk__hnqzf.format(literalness, str(trplz__zsbrm))
        import bodo
        if isinstance(byole__rxx, bodo.utils.typing.BodoError):
            raise byole__rxx
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', byole__rxx) +
                nested_msg('non-literal', wogxb__oyjf))
        else:
            if 'missing a required argument' in byole__rxx.msg:
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
            raise errors.TypingError(msg, loc=byole__rxx.loc)
    return fla__uvbs


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
    bda__otmfr = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=bda__otmfr)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            dril__xjk = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), dril__xjk)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    ppxan__cdkfq = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            ppxan__cdkfq.append(types.Omitted(a.value))
        else:
            ppxan__cdkfq.append(self.typeof_pyval(a))
    kesoo__joxc = None
    try:
        error = None
        kesoo__joxc = self.compile(tuple(ppxan__cdkfq))
    except errors.ForceLiteralArg as e:
        exp__fef = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if exp__fef:
            feu__qlz = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            vekm__onrhd = ', '.join('Arg #{} is {}'.format(i, args[i]) for
                i in sorted(exp__fef))
            raise errors.CompilerError(feu__qlz.format(vekm__onrhd))
        brqe__blc = []
        try:
            for i, zwl__spy in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        brqe__blc.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        brqe__blc.append(types.literal(args[i]))
                else:
                    brqe__blc.append(args[i])
            args = brqe__blc
        except (OSError, FileNotFoundError) as sew__jjf:
            error = FileNotFoundError(str(sew__jjf) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                kesoo__joxc = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        qwxth__gnhta = []
        for i, kxw__cip in enumerate(args):
            val = kxw__cip.value if isinstance(kxw__cip, numba.core.
                dispatcher.OmittedArg) else kxw__cip
            try:
                forp__xjzi = typeof(val, Purpose.argument)
            except ValueError as hbxvk__cpw:
                qwxth__gnhta.append((i, str(hbxvk__cpw)))
            else:
                if forp__xjzi is None:
                    qwxth__gnhta.append((i,
                        f'cannot determine Numba type of value {val}'))
        if qwxth__gnhta:
            sime__fga = '\n'.join(f'- argument {i}: {tixuh__ioy}' for i,
                tixuh__ioy in qwxth__gnhta)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{sime__fga}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                jyzk__shrxo = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                uazpq__anqv = False
                for becy__dtntt in jyzk__shrxo:
                    if becy__dtntt in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        uazpq__anqv = True
                        break
                if not uazpq__anqv:
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
                dril__xjk = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), dril__xjk)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return kesoo__joxc


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
    for pqez__vcf in cres.library._codegen._engine._defined_symbols:
        if pqez__vcf.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in pqez__vcf and (
            'bodo_gb_udf_update_local' in pqez__vcf or 
            'bodo_gb_udf_combine' in pqez__vcf or 'bodo_gb_udf_eval' in
            pqez__vcf or 'bodo_gb_apply_general_udfs' in pqez__vcf):
            gb_agg_cfunc_addr[pqez__vcf
                ] = cres.library.get_pointer_to_function(pqez__vcf)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for pqez__vcf in cres.library._codegen._engine._defined_symbols:
        if pqez__vcf.startswith('cfunc') and ('get_join_cond_addr' not in
            pqez__vcf or 'bodo_join_gen_cond' in pqez__vcf):
            join_gen_cond_cfunc_addr[pqez__vcf
                ] = cres.library.get_pointer_to_function(pqez__vcf)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    crds__awlzd = self._get_dispatcher_for_current_target()
    if crds__awlzd is not self:
        return crds__awlzd.compile(sig)
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
            ixcda__vzni = self.overloads.get(tuple(args))
            if ixcda__vzni is not None:
                return ixcda__vzni.entry_point
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
            phnjd__nzfoo = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=phnjd__nzfoo):
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
    nzo__dtpa = self._final_module
    yyg__gclr = []
    bekyw__fnsjo = 0
    for fn in nzo__dtpa.functions:
        bekyw__fnsjo += 1
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
            yyg__gclr.append(fn.name)
    if bekyw__fnsjo == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if yyg__gclr:
        nzo__dtpa = nzo__dtpa.clone()
        for name in yyg__gclr:
            nzo__dtpa.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = nzo__dtpa
    return nzo__dtpa


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
    for boiae__dpb in self.constraints:
        loc = boiae__dpb.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                boiae__dpb(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                rpxm__qzf = numba.core.errors.TypingError(str(e), loc=
                    boiae__dpb.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(rpxm__qzf, e))
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
                    rpxm__qzf = numba.core.errors.TypingError(msg.format(
                        con=boiae__dpb, err=str(e)), loc=boiae__dpb.loc,
                        highlighting=False)
                    errors.append(utils.chain_exception(rpxm__qzf, e))
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
    for blqiz__uegz in self._failures.values():
        for jos__xitss in blqiz__uegz:
            if isinstance(jos__xitss.error, ForceLiteralArg):
                raise jos__xitss.error
            if isinstance(jos__xitss.error, bodo.utils.typing.BodoError):
                raise jos__xitss.error
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
    wlvd__rlbuu = False
    guhy__idejo = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        fqny__snpl = set()
        uaq__lyaya = lives & alias_set
        for zwl__spy in uaq__lyaya:
            fqny__snpl |= alias_map[zwl__spy]
        lives_n_aliases = lives | fqny__snpl | arg_aliases
        if type(stmt) in remove_dead_extensions:
            rqda__rlb = remove_dead_extensions[type(stmt)]
            stmt = rqda__rlb(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                wlvd__rlbuu = True
                continue
        if isinstance(stmt, ir.Assign):
            qpizp__wzmqq = stmt.target
            mgbgh__zdfy = stmt.value
            if qpizp__wzmqq.name not in lives and has_no_side_effect(
                mgbgh__zdfy, lives_n_aliases, call_table):
                wlvd__rlbuu = True
                continue
            if saved_array_analysis and qpizp__wzmqq.name in lives and is_expr(
                mgbgh__zdfy, 'getattr'
                ) and mgbgh__zdfy.attr == 'shape' and is_array_typ(typemap[
                mgbgh__zdfy.value.name]
                ) and mgbgh__zdfy.value.name not in lives:
                zda__cvba = {zwl__spy: crp__cnln for crp__cnln, zwl__spy in
                    func_ir.blocks.items()}
                if block in zda__cvba:
                    jnzj__dfbcs = zda__cvba[block]
                    xoltr__bqq = saved_array_analysis.get_equiv_set(jnzj__dfbcs
                        )
                    vocce__fzzfc = xoltr__bqq.get_equiv_set(mgbgh__zdfy.value)
                    if vocce__fzzfc is not None:
                        for zwl__spy in vocce__fzzfc:
                            if zwl__spy.endswith('#0'):
                                zwl__spy = zwl__spy[:-2]
                            if zwl__spy in typemap and is_array_typ(typemap
                                [zwl__spy]) and zwl__spy in lives:
                                mgbgh__zdfy.value = ir.Var(mgbgh__zdfy.
                                    value.scope, zwl__spy, mgbgh__zdfy.
                                    value.loc)
                                wlvd__rlbuu = True
                                break
            if isinstance(mgbgh__zdfy, ir.Var
                ) and qpizp__wzmqq.name == mgbgh__zdfy.name:
                wlvd__rlbuu = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                wlvd__rlbuu = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            tws__aszm = analysis.ir_extension_usedefs[type(stmt)]
            rik__tlh, feg__nelkk = tws__aszm(stmt)
            lives -= feg__nelkk
            lives |= rik__tlh
        else:
            lives |= {zwl__spy.name for zwl__spy in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                ooge__lkc = set()
                if isinstance(mgbgh__zdfy, ir.Expr):
                    ooge__lkc = {zwl__spy.name for zwl__spy in mgbgh__zdfy.
                        list_vars()}
                if qpizp__wzmqq.name not in ooge__lkc:
                    lives.remove(qpizp__wzmqq.name)
        guhy__idejo.append(stmt)
    guhy__idejo.reverse()
    block.body = guhy__idejo
    return wlvd__rlbuu


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            xqq__ehh, = args
            if isinstance(xqq__ehh, types.IterableType):
                dtype = xqq__ehh.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), xqq__ehh)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    foda__eaxu = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (foda__eaxu, self.dtype)
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
        except LiteralTypingError as hgtsg__azw:
            return
    try:
        return literal(value)
    except LiteralTypingError as hgtsg__azw:
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
        tnvzo__hbrf = py_func.__qualname__
    except AttributeError as hgtsg__azw:
        tnvzo__hbrf = py_func.__name__
    hks__siukr = inspect.getfile(py_func)
    for cls in self._locator_classes:
        ympk__ozu = cls.from_function(py_func, hks__siukr)
        if ympk__ozu is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (tnvzo__hbrf, hks__siukr))
    self._locator = ympk__ozu
    viwn__gglrt = inspect.getfile(py_func)
    zxjlj__djb = os.path.splitext(os.path.basename(viwn__gglrt))[0]
    if hks__siukr.startswith('<ipython-'):
        xollg__cvso = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)',
            '\\1\\3', zxjlj__djb, count=1)
        if xollg__cvso == zxjlj__djb:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        zxjlj__djb = xollg__cvso
    pwel__gxz = '%s.%s' % (zxjlj__djb, tnvzo__hbrf)
    xllqw__txk = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(pwel__gxz, xllqw__txk)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    mpxxe__yvlr = list(filter(lambda a: self._istuple(a.name), args))
    if len(mpxxe__yvlr) == 2 and fn.__name__ == 'add':
        jusx__luk = self.typemap[mpxxe__yvlr[0].name]
        bpyb__tfxgj = self.typemap[mpxxe__yvlr[1].name]
        if jusx__luk.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                mpxxe__yvlr[1]))
        if bpyb__tfxgj.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                mpxxe__yvlr[0]))
        try:
            oprrr__shrj = [equiv_set.get_shape(x) for x in mpxxe__yvlr]
            if None in oprrr__shrj:
                return None
            skgrk__htats = sum(oprrr__shrj, ())
            return ArrayAnalysis.AnalyzeResult(shape=skgrk__htats)
        except GuardException as hgtsg__azw:
            return None
    onf__lyw = list(filter(lambda a: self._isarray(a.name), args))
    require(len(onf__lyw) > 0)
    ktw__pbrn = [x.name for x in onf__lyw]
    ngj__kgvvs = [self.typemap[x.name].ndim for x in onf__lyw]
    jkdt__qsrj = max(ngj__kgvvs)
    require(jkdt__qsrj > 0)
    oprrr__shrj = [equiv_set.get_shape(x) for x in onf__lyw]
    if any(a is None for a in oprrr__shrj):
        return ArrayAnalysis.AnalyzeResult(shape=onf__lyw[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, onf__lyw))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, oprrr__shrj,
        ktw__pbrn)


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
    pysa__txd = code_obj.code
    dvo__nbo = len(pysa__txd.co_freevars)
    nydhx__echh = pysa__txd.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        mgrzv__kawjt, op = ir_utils.find_build_sequence(caller_ir, code_obj
            .closure)
        assert op == 'build_tuple'
        nydhx__echh = [zwl__spy.name for zwl__spy in mgrzv__kawjt]
    pgeh__bhe = caller_ir.func_id.func.__globals__
    try:
        pgeh__bhe = getattr(code_obj, 'globals', pgeh__bhe)
    except KeyError as hgtsg__azw:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    lun__wrap = []
    for x in nydhx__echh:
        try:
            wekvq__baxk = caller_ir.get_definition(x)
        except KeyError as hgtsg__azw:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(wekvq__baxk, (ir.Const, ir.Global, ir.FreeVar)):
            val = wekvq__baxk.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                fcon__svka = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                pgeh__bhe[fcon__svka] = bodo.jit(distributed=False)(val)
                pgeh__bhe[fcon__svka].is_nested_func = True
                val = fcon__svka
            if isinstance(val, CPUDispatcher):
                fcon__svka = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                pgeh__bhe[fcon__svka] = val
                val = fcon__svka
            lun__wrap.append(val)
        elif isinstance(wekvq__baxk, ir.Expr
            ) and wekvq__baxk.op == 'make_function':
            nxsn__nfqm = convert_code_obj_to_function(wekvq__baxk, caller_ir)
            fcon__svka = ir_utils.mk_unique_var('nested_func').replace('.', '_'
                )
            pgeh__bhe[fcon__svka] = bodo.jit(distributed=False)(nxsn__nfqm)
            pgeh__bhe[fcon__svka].is_nested_func = True
            lun__wrap.append(fcon__svka)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    zxdx__ycidg = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in enumerate
        (lun__wrap)])
    enfb__xpgsw = ','.join([('c_%d' % i) for i in range(dvo__nbo)])
    yolhq__mid = list(pysa__txd.co_varnames)
    yih__rqj = 0
    ozd__bal = pysa__txd.co_argcount
    mwf__pkypy = caller_ir.get_definition(code_obj.defaults)
    if mwf__pkypy is not None:
        if isinstance(mwf__pkypy, tuple):
            vbf__kuf = [caller_ir.get_definition(x).value for x in mwf__pkypy]
            rvkpw__bqf = tuple(vbf__kuf)
        else:
            vbf__kuf = [caller_ir.get_definition(x).value for x in
                mwf__pkypy.items]
            rvkpw__bqf = tuple(vbf__kuf)
        yih__rqj = len(rvkpw__bqf)
    noddg__iyz = ozd__bal - yih__rqj
    ffj__cfnrj = ','.join([('%s' % yolhq__mid[i]) for i in range(noddg__iyz)])
    if yih__rqj:
        ddesf__gudwg = [('%s = %s' % (yolhq__mid[i + noddg__iyz],
            rvkpw__bqf[i])) for i in range(yih__rqj)]
        ffj__cfnrj += ', '
        ffj__cfnrj += ', '.join(ddesf__gudwg)
    return _create_function_from_code_obj(pysa__txd, zxdx__ycidg,
        ffj__cfnrj, enfb__xpgsw, pgeh__bhe)


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
    for taq__ogcnf, (tudil__bvvxm, ipye__qhq) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % ipye__qhq)
            ueac__kigm = _pass_registry.get(tudil__bvvxm).pass_inst
            if isinstance(ueac__kigm, CompilerPass):
                self._runPass(taq__ogcnf, ueac__kigm, state)
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
                    pipeline_name, ipye__qhq)
                fqv__qiow = self._patch_error(msg, e)
                raise fqv__qiow
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
    lnd__prjru = None
    feg__nelkk = {}

    def lookup(var, already_seen, varonly=True):
        val = feg__nelkk.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    vnlv__fwtd = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        qpizp__wzmqq = stmt.target
        mgbgh__zdfy = stmt.value
        feg__nelkk[qpizp__wzmqq.name] = mgbgh__zdfy
        if isinstance(mgbgh__zdfy, ir.Var) and mgbgh__zdfy.name in feg__nelkk:
            mgbgh__zdfy = lookup(mgbgh__zdfy, set())
        if isinstance(mgbgh__zdfy, ir.Expr):
            pnwq__lpn = set(lookup(zwl__spy, set(), True).name for zwl__spy in
                mgbgh__zdfy.list_vars())
            if name in pnwq__lpn:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(mgbgh__zdfy)]
                pquxl__oci = [x for x, tonn__eno in args if tonn__eno.name !=
                    name]
                args = [(x, tonn__eno) for x, tonn__eno in args if x !=
                    tonn__eno.name]
                gpgjo__agxn = dict(args)
                if len(pquxl__oci) == 1:
                    gpgjo__agxn[pquxl__oci[0]] = ir.Var(qpizp__wzmqq.scope,
                        name + '#init', qpizp__wzmqq.loc)
                replace_vars_inner(mgbgh__zdfy, gpgjo__agxn)
                lnd__prjru = nodes[i:]
                break
    return lnd__prjru


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
        bby__uknf = expand_aliases({zwl__spy.name for zwl__spy in stmt.
            list_vars()}, alias_map, arg_aliases)
        orzov__hejeu = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        kzapl__xfa = expand_aliases({zwl__spy.name for zwl__spy in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        xosye__bzta = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(orzov__hejeu & kzapl__xfa | xosye__bzta & bby__uknf) == 0:
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
    jfde__hsqdj = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            jfde__hsqdj.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                jfde__hsqdj.update(get_parfor_writes(stmt, func_ir))
    return jfde__hsqdj


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    jfde__hsqdj = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        jfde__hsqdj.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        jfde__hsqdj = {zwl__spy.name for zwl__spy in stmt.df_out_vars.values()}
        if stmt.out_key_vars is not None:
            jfde__hsqdj.update({zwl__spy.name for zwl__spy in stmt.
                out_key_vars})
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        jfde__hsqdj = {zwl__spy.name for zwl__spy in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        jfde__hsqdj = {zwl__spy.name for zwl__spy in stmt.out_data_vars.
            values()}
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            jfde__hsqdj.update({zwl__spy.name for zwl__spy in stmt.
                out_key_arrs})
            jfde__hsqdj.update({zwl__spy.name for zwl__spy in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        oiock__onoc = guard(find_callname, func_ir, stmt.value)
        if oiock__onoc in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'),
            ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            jfde__hsqdj.add(stmt.value.args[0].name)
    return jfde__hsqdj


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
        rqda__rlb = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        jhuqx__gqo = rqda__rlb.format(self, msg)
        self.args = jhuqx__gqo,
    else:
        rqda__rlb = _termcolor.errmsg('{0}')
        jhuqx__gqo = rqda__rlb.format(self)
        self.args = jhuqx__gqo,
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
        for vvvv__yrlx in options['distributed']:
            dist_spec[vvvv__yrlx] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for vvvv__yrlx in options['distributed_block']:
            dist_spec[vvvv__yrlx] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    wwfel__kdy = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, gqka__fgk in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(gqka__fgk)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    iovhp__zep = {}
    for kqvr__hahdz in reversed(inspect.getmro(cls)):
        iovhp__zep.update(kqvr__hahdz.__dict__)
    zwvmj__lwlh, mdnpc__qwwi, bhln__eetp, bcxm__vdbub = {}, {}, {}, {}
    for crp__cnln, zwl__spy in iovhp__zep.items():
        if isinstance(zwl__spy, pytypes.FunctionType):
            zwvmj__lwlh[crp__cnln] = zwl__spy
        elif isinstance(zwl__spy, property):
            mdnpc__qwwi[crp__cnln] = zwl__spy
        elif isinstance(zwl__spy, staticmethod):
            bhln__eetp[crp__cnln] = zwl__spy
        else:
            bcxm__vdbub[crp__cnln] = zwl__spy
    kdu__duk = (set(zwvmj__lwlh) | set(mdnpc__qwwi) | set(bhln__eetp)) & set(
        spec)
    if kdu__duk:
        raise NameError('name shadowing: {0}'.format(', '.join(kdu__duk)))
    mgqt__jnkf = bcxm__vdbub.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(bcxm__vdbub)
    if bcxm__vdbub:
        msg = 'class members are not yet supported: {0}'
        ujvsh__wlgqy = ', '.join(bcxm__vdbub.keys())
        raise TypeError(msg.format(ujvsh__wlgqy))
    for crp__cnln, zwl__spy in mdnpc__qwwi.items():
        if zwl__spy.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(crp__cnln))
    jit_methods = {crp__cnln: bodo.jit(returns_maybe_distributed=wwfel__kdy
        )(zwl__spy) for crp__cnln, zwl__spy in zwvmj__lwlh.items()}
    jit_props = {}
    for crp__cnln, zwl__spy in mdnpc__qwwi.items():
        ycjww__aqj = {}
        if zwl__spy.fget:
            ycjww__aqj['get'] = bodo.jit(zwl__spy.fget)
        if zwl__spy.fset:
            ycjww__aqj['set'] = bodo.jit(zwl__spy.fset)
        jit_props[crp__cnln] = ycjww__aqj
    jit_static_methods = {crp__cnln: bodo.jit(zwl__spy.__func__) for 
        crp__cnln, zwl__spy in bhln__eetp.items()}
    yjwqw__hxd = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    api__lmw = dict(class_type=yjwqw__hxd, __doc__=mgqt__jnkf)
    api__lmw.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), api__lmw)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, yjwqw__hxd)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(yjwqw__hxd, typingctx, targetctx).register()
    as_numba_type.register(cls, yjwqw__hxd.instance_type)
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
    upop__chr = ','.join('{0}:{1}'.format(crp__cnln, zwl__spy) for 
        crp__cnln, zwl__spy in struct.items())
    jennt__grh = ','.join('{0}:{1}'.format(crp__cnln, zwl__spy) for 
        crp__cnln, zwl__spy in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), upop__chr, jennt__grh)
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
    jex__cup = numba.core.typeinfer.fold_arg_vars(typevars, self.args, self
        .vararg, self.kws)
    if jex__cup is None:
        return
    tyakx__umm, rofs__dnv = jex__cup
    for a in itertools.chain(tyakx__umm, rofs__dnv.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, tyakx__umm, rofs__dnv)
    except ForceLiteralArg as e:
        bifr__tymb = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(bifr__tymb, self.kws)
        pmec__izbwg = set()
        vrdpw__whm = set()
        saaw__qedku = {}
        for taq__ogcnf in e.requested_args:
            kagjs__kswdo = typeinfer.func_ir.get_definition(folded[taq__ogcnf])
            if isinstance(kagjs__kswdo, ir.Arg):
                pmec__izbwg.add(kagjs__kswdo.index)
                if kagjs__kswdo.index in e.file_infos:
                    saaw__qedku[kagjs__kswdo.index] = e.file_infos[kagjs__kswdo
                        .index]
            else:
                vrdpw__whm.add(taq__ogcnf)
        if vrdpw__whm:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif pmec__izbwg:
            raise ForceLiteralArg(pmec__izbwg, loc=self.loc, file_infos=
                saaw__qedku)
    if sig is None:
        ipsi__joqb = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in tyakx__umm]
        args += [('%s=%s' % (crp__cnln, zwl__spy)) for crp__cnln, zwl__spy in
            sorted(rofs__dnv.items())]
        fkwl__gxze = ipsi__joqb.format(fnty, ', '.join(map(str, args)))
        hpes__gfo = context.explain_function_type(fnty)
        msg = '\n'.join([fkwl__gxze, hpes__gfo])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        epuh__dqxs = context.unify_pairs(sig.recvr, fnty.this)
        if epuh__dqxs is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if epuh__dqxs is not None and epuh__dqxs.is_precise():
            nhjbg__gpn = fnty.copy(this=epuh__dqxs)
            typeinfer.propagate_refined_type(self.func, nhjbg__gpn)
    if not sig.return_type.is_precise():
        vmfk__fsy = typevars[self.target]
        if vmfk__fsy.defined:
            lfz__efybn = vmfk__fsy.getone()
            if context.unify_pairs(lfz__efybn, sig.return_type) == lfz__efybn:
                sig = sig.replace(return_type=lfz__efybn)
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
        feu__qlz = '*other* must be a {} but got a {} instead'
        raise TypeError(feu__qlz.format(ForceLiteralArg, type(other)))
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
    hsm__aos = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for crp__cnln, zwl__spy in kwargs.items():
        hbu__qwjft = None
        try:
            cmfm__yzca = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var
                ('dummy'), loc)
            func_ir._definitions[cmfm__yzca.name] = [zwl__spy]
            hbu__qwjft = get_const_value_inner(func_ir, cmfm__yzca)
            func_ir._definitions.pop(cmfm__yzca.name)
            if isinstance(hbu__qwjft, str):
                hbu__qwjft = sigutils._parse_signature_string(hbu__qwjft)
            if isinstance(hbu__qwjft, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {crp__cnln} is annotated as type class {hbu__qwjft}."""
                    )
            assert isinstance(hbu__qwjft, types.Type)
            if isinstance(hbu__qwjft, (types.List, types.Set)):
                hbu__qwjft = hbu__qwjft.copy(reflected=False)
            hsm__aos[crp__cnln] = hbu__qwjft
        except BodoError as hgtsg__azw:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(hbu__qwjft, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(zwl__spy, ir.Global):
                    msg = f'Global {zwl__spy.name!r} is not defined.'
                if isinstance(zwl__spy, ir.FreeVar):
                    msg = f'Freevar {zwl__spy.name!r} is not defined.'
            if isinstance(zwl__spy, ir.Expr) and zwl__spy.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=crp__cnln, msg=msg, loc=loc)
    for name, typ in hsm__aos.items():
        self._legalize_arg_type(name, typ, loc)
    return hsm__aos


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
    wgnp__aetxb = inst.arg
    assert wgnp__aetxb > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(wgnp__aetxb)]))
    tmps = [state.make_temp() for _ in range(wgnp__aetxb - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    gzbd__ssvom = ir.Global('format', format, loc=self.loc)
    self.store(value=gzbd__ssvom, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    lgxv__sxrrj = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=lgxv__sxrrj, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    wgnp__aetxb = inst.arg
    assert wgnp__aetxb > 0, 'invalid BUILD_STRING count'
    tcke__rofkz = self.get(strings[0])
    for other, rjebn__rxp in zip(strings[1:], tmps):
        other = self.get(other)
        hnvbm__rtgpl = ir.Expr.binop(operator.add, lhs=tcke__rofkz, rhs=
            other, loc=self.loc)
        self.store(hnvbm__rtgpl, rjebn__rxp)
        tcke__rofkz = self.get(rjebn__rxp)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    rujcd__xedrc = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, rujcd__xedrc])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    izsb__emkc = mk_unique_var(f'{var_name}')
    xfd__tbq = izsb__emkc.replace('<', '_').replace('>', '_')
    xfd__tbq = xfd__tbq.replace('.', '_').replace('$', '_v')
    return xfd__tbq


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
            if val1 == bodo.hiframes.pd_timestamp_ext.pd_timestamp_type:
                if not is_overload_constant_str(val2):
                    raise_bodo_error(
                        "datetime64(): 'units' must be a 'str' specifying 'ns'"
                        )
                nvsnj__xmci = get_overload_const_str(val2)
                if nvsnj__xmci != 'ns':
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
        qhef__aukf = states['defmap']
        if len(qhef__aukf) == 0:
            mqj__kbl = assign.target
            numba.core.ssa._logger.debug('first assign: %s', mqj__kbl)
            if mqj__kbl.name not in scope.localvars:
                mqj__kbl = scope.define(assign.target.name, loc=assign.loc)
        else:
            mqj__kbl = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=mqj__kbl, value=assign.value, loc=assign.loc)
        qhef__aukf[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    ytl__szfc = []
    for crp__cnln, zwl__spy in typing.npydecl.registry.globals:
        if crp__cnln == func:
            ytl__szfc.append(zwl__spy)
    for crp__cnln, zwl__spy in typing.templates.builtin_registry.globals:
        if crp__cnln == func:
            ytl__szfc.append(zwl__spy)
    if len(ytl__szfc) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return ytl__szfc


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    xbmnj__xdvtj = {}
    iig__znyji = find_topo_order(blocks)
    jhd__klgu = {}
    for jnzj__dfbcs in iig__znyji:
        block = blocks[jnzj__dfbcs]
        guhy__idejo = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                qpizp__wzmqq = stmt.target.name
                mgbgh__zdfy = stmt.value
                if (mgbgh__zdfy.op == 'getattr' and mgbgh__zdfy.attr in
                    arr_math and isinstance(typemap[mgbgh__zdfy.value.name],
                    types.npytypes.Array)):
                    mgbgh__zdfy = stmt.value
                    sjk__znza = mgbgh__zdfy.value
                    xbmnj__xdvtj[qpizp__wzmqq] = sjk__znza
                    scope = sjk__znza.scope
                    loc = sjk__znza.loc
                    wvpc__mkt = ir.Var(scope, mk_unique_var('$np_g_var'), loc)
                    typemap[wvpc__mkt.name] = types.misc.Module(numpy)
                    urdwb__jhes = ir.Global('np', numpy, loc)
                    mnsj__glx = ir.Assign(urdwb__jhes, wvpc__mkt, loc)
                    mgbgh__zdfy.value = wvpc__mkt
                    guhy__idejo.append(mnsj__glx)
                    func_ir._definitions[wvpc__mkt.name] = [urdwb__jhes]
                    func = getattr(numpy, mgbgh__zdfy.attr)
                    nujdl__lfu = get_np_ufunc_typ_lst(func)
                    jhd__klgu[qpizp__wzmqq] = nujdl__lfu
                if (mgbgh__zdfy.op == 'call' and mgbgh__zdfy.func.name in
                    xbmnj__xdvtj):
                    sjk__znza = xbmnj__xdvtj[mgbgh__zdfy.func.name]
                    ufb__rkjx = calltypes.pop(mgbgh__zdfy)
                    dvv__dnzi = ufb__rkjx.args[:len(mgbgh__zdfy.args)]
                    ncww__fxvov = {name: typemap[zwl__spy.name] for name,
                        zwl__spy in mgbgh__zdfy.kws}
                    rtq__xhcqf = jhd__klgu[mgbgh__zdfy.func.name]
                    dcw__ekl = None
                    for oodk__dtdpu in rtq__xhcqf:
                        try:
                            dcw__ekl = oodk__dtdpu.get_call_type(typingctx,
                                [typemap[sjk__znza.name]] + list(dvv__dnzi),
                                ncww__fxvov)
                            typemap.pop(mgbgh__zdfy.func.name)
                            typemap[mgbgh__zdfy.func.name] = oodk__dtdpu
                            calltypes[mgbgh__zdfy] = dcw__ekl
                            break
                        except Exception as hgtsg__azw:
                            pass
                    if dcw__ekl is None:
                        raise TypeError(
                            f'No valid template found for {mgbgh__zdfy.func.name}'
                            )
                    mgbgh__zdfy.args = [sjk__znza] + mgbgh__zdfy.args
            guhy__idejo.append(stmt)
        block.body = guhy__idejo


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    grh__cztxc = ufunc.nin
    dslle__lta = ufunc.nout
    noddg__iyz = ufunc.nargs
    assert noddg__iyz == grh__cztxc + dslle__lta
    if len(args) < grh__cztxc:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), grh__cztxc)
            )
    if len(args) > noddg__iyz:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), noddg__iyz)
            )
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    ekaih__fww = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    ckk__nmm = max(ekaih__fww)
    mtnuk__ubg = args[grh__cztxc:]
    if not all(vbf__kuf == ckk__nmm for vbf__kuf in ekaih__fww[grh__cztxc:]):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(xxcde__jzfp, types.ArrayCompatible) and not
        isinstance(xxcde__jzfp, types.Bytes) for xxcde__jzfp in mtnuk__ubg):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(xxcde__jzfp.mutable for xxcde__jzfp in mtnuk__ubg):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    jja__xblcb = [(x.dtype if isinstance(x, types.ArrayCompatible) and not
        isinstance(x, types.Bytes) else x) for x in args]
    wbdjo__dyz = None
    if ckk__nmm > 0 and len(mtnuk__ubg) < ufunc.nout:
        wbdjo__dyz = 'C'
        amxd__ahc = [(x.layout if isinstance(x, types.ArrayCompatible) and 
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in amxd__ahc and 'F' in amxd__ahc:
            wbdjo__dyz = 'F'
    return jja__xblcb, mtnuk__ubg, ckk__nmm, wbdjo__dyz


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
        epa__vva = 'Dict.key_type cannot be of type {}'
        raise TypingError(epa__vva.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        epa__vva = 'Dict.value_type cannot be of type {}'
        raise TypingError(epa__vva.format(valty))
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
    xgx__idv = self.context, tuple(args), tuple(kws.items())
    try:
        betr__jjtbe, args = self._impl_cache[xgx__idv]
        return betr__jjtbe, args
    except KeyError as hgtsg__azw:
        pass
    betr__jjtbe, args = self._build_impl(xgx__idv, args, kws)
    return betr__jjtbe, args


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
        aamf__eoo = find_topo_order(parfor.loop_body)
    vlpcd__ryt = aamf__eoo[0]
    wfh__jyd = {}
    _update_parfor_get_setitems(parfor.loop_body[vlpcd__ryt].body, parfor.
        index_var, alias_map, wfh__jyd, lives_n_aliases)
    trs__hokeg = set(wfh__jyd.keys())
    for fadc__djz in aamf__eoo:
        if fadc__djz == vlpcd__ryt:
            continue
        for stmt in parfor.loop_body[fadc__djz].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            mtyn__rfhy = set(zwl__spy.name for zwl__spy in stmt.list_vars())
            mwqqg__esj = mtyn__rfhy & trs__hokeg
            for a in mwqqg__esj:
                wfh__jyd.pop(a, None)
    for fadc__djz in aamf__eoo:
        if fadc__djz == vlpcd__ryt:
            continue
        block = parfor.loop_body[fadc__djz]
        dfb__zwh = wfh__jyd.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            dfb__zwh, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    hvmlp__dzlok = max(blocks.keys())
    khij__ifo, szbpe__abed = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    fybqy__bafe = ir.Jump(khij__ifo, ir.Loc('parfors_dummy', -1))
    blocks[hvmlp__dzlok].body.append(fybqy__bafe)
    zjish__fhrra = compute_cfg_from_blocks(blocks)
    jpq__iqa = compute_use_defs(blocks)
    rjw__nhpu = compute_live_map(zjish__fhrra, blocks, jpq__iqa.usemap,
        jpq__iqa.defmap)
    alias_set = set(alias_map.keys())
    for jnzj__dfbcs, block in blocks.items():
        guhy__idejo = []
        pngbi__awz = {zwl__spy.name for zwl__spy in block.terminator.
            list_vars()}
        for njv__xdi, tfy__sub in zjish__fhrra.successors(jnzj__dfbcs):
            pngbi__awz |= rjw__nhpu[njv__xdi]
        for stmt in reversed(block.body):
            fqny__snpl = pngbi__awz & alias_set
            for zwl__spy in fqny__snpl:
                pngbi__awz |= alias_map[zwl__spy]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in pngbi__awz and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                oiock__onoc = guard(find_callname, func_ir, stmt.value)
                if oiock__onoc == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in pngbi__awz and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            pngbi__awz |= {zwl__spy.name for zwl__spy in stmt.list_vars()}
            guhy__idejo.append(stmt)
        guhy__idejo.reverse()
        block.body = guhy__idejo
    typemap.pop(szbpe__abed.name)
    blocks[hvmlp__dzlok].body.pop()

    def trim_empty_parfor_branches(parfor):
        nbijv__zdolv = False
        blocks = parfor.loop_body.copy()
        for jnzj__dfbcs, block in blocks.items():
            if len(block.body):
                cdzfv__tvrc = block.body[-1]
                if isinstance(cdzfv__tvrc, ir.Branch):
                    if len(blocks[cdzfv__tvrc.truebr].body) == 1 and len(blocks
                        [cdzfv__tvrc.falsebr].body) == 1:
                        gmugk__zxfn = blocks[cdzfv__tvrc.truebr].body[0]
                        ltqx__mirbc = blocks[cdzfv__tvrc.falsebr].body[0]
                        if isinstance(gmugk__zxfn, ir.Jump) and isinstance(
                            ltqx__mirbc, ir.Jump
                            ) and gmugk__zxfn.target == ltqx__mirbc.target:
                            parfor.loop_body[jnzj__dfbcs].body[-1] = ir.Jump(
                                gmugk__zxfn.target, cdzfv__tvrc.loc)
                            nbijv__zdolv = True
                    elif len(blocks[cdzfv__tvrc.truebr].body) == 1:
                        gmugk__zxfn = blocks[cdzfv__tvrc.truebr].body[0]
                        if isinstance(gmugk__zxfn, ir.Jump
                            ) and gmugk__zxfn.target == cdzfv__tvrc.falsebr:
                            parfor.loop_body[jnzj__dfbcs].body[-1] = ir.Jump(
                                gmugk__zxfn.target, cdzfv__tvrc.loc)
                            nbijv__zdolv = True
                    elif len(blocks[cdzfv__tvrc.falsebr].body) == 1:
                        ltqx__mirbc = blocks[cdzfv__tvrc.falsebr].body[0]
                        if isinstance(ltqx__mirbc, ir.Jump
                            ) and ltqx__mirbc.target == cdzfv__tvrc.truebr:
                            parfor.loop_body[jnzj__dfbcs].body[-1] = ir.Jump(
                                ltqx__mirbc.target, cdzfv__tvrc.loc)
                            nbijv__zdolv = True
        return nbijv__zdolv
    nbijv__zdolv = True
    while nbijv__zdolv:
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
        nbijv__zdolv = trim_empty_parfor_branches(parfor)
    gvzak__sdysa = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        gvzak__sdysa &= len(block.body) == 0
    if gvzak__sdysa:
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
    npw__vtw = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                npw__vtw += 1
                parfor = stmt
                agay__ndu = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = agay__ndu.scope
                loc = ir.Loc('parfors_dummy', -1)
                bdhaq__ahcp = ir.Var(scope, mk_unique_var('$const'), loc)
                agay__ndu.body.append(ir.Assign(ir.Const(0, loc),
                    bdhaq__ahcp, loc))
                agay__ndu.body.append(ir.Return(bdhaq__ahcp, loc))
                zjish__fhrra = compute_cfg_from_blocks(parfor.loop_body)
                for gltst__ikmb in zjish__fhrra.dead_nodes():
                    del parfor.loop_body[gltst__ikmb]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                agay__ndu = parfor.loop_body[max(parfor.loop_body.keys())]
                agay__ndu.body.pop()
                agay__ndu.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return npw__vtw


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
            ixcda__vzni = self.overloads.get(tuple(args))
            if ixcda__vzni is not None:
                return ixcda__vzni.entry_point
            self._pre_compile(args, return_type, flags)
            qqa__qju = self.func_ir
            phnjd__nzfoo = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=phnjd__nzfoo):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=qqa__qju, args=args,
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
        osvc__itbiz = copy.deepcopy(flags)
        osvc__itbiz.no_rewrites = True

        def compile_local(the_ir, the_flags):
            obwvi__tqoe = pipeline_class(typingctx, targetctx, library,
                args, return_type, the_flags, locals)
            return obwvi__tqoe.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        jhy__gfyys = compile_local(func_ir, osvc__itbiz)
        iasp__javz = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    iasp__javz = compile_local(func_ir, flags)
                except Exception as hgtsg__azw:
                    pass
        if iasp__javz is not None:
            cres = iasp__javz
        else:
            cres = jhy__gfyys
        return cres
    else:
        obwvi__tqoe = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return obwvi__tqoe.compile_ir(func_ir=func_ir, lifted=lifted,
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
    xhixc__efv = self.get_data_type(typ.dtype)
    jmz__wvym = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        jmz__wvym):
        zbqyz__xii = ary.ctypes.data
        orgp__vfpjd = self.add_dynamic_addr(builder, zbqyz__xii, info=str(
            type(zbqyz__xii)))
        fsnll__aso = self.add_dynamic_addr(builder, id(ary), info=str(type(
            ary)))
        self.global_arrays.append(ary)
    else:
        owe__bkto = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            owe__bkto = owe__bkto.view('int64')
        vbyt__ywyru = Constant.array(Type.int(8), bytearray(owe__bkto.data))
        orgp__vfpjd = cgutils.global_constant(builder, '.const.array.data',
            vbyt__ywyru)
        orgp__vfpjd.align = self.get_abi_alignment(xhixc__efv)
        fsnll__aso = None
    mgxa__wnpz = self.get_value_type(types.intp)
    sggqd__sqfz = [self.get_constant(types.intp, oirs__halwl) for
        oirs__halwl in ary.shape]
    ruqov__fhht = Constant.array(mgxa__wnpz, sggqd__sqfz)
    siymf__wlse = [self.get_constant(types.intp, oirs__halwl) for
        oirs__halwl in ary.strides]
    akczo__sau = Constant.array(mgxa__wnpz, siymf__wlse)
    cnlk__fkqkh = self.get_constant(types.intp, ary.dtype.itemsize)
    yew__cbrz = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        yew__cbrz, cnlk__fkqkh, orgp__vfpjd.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), ruqov__fhht, akczo__sau])


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
    ild__kknde = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    ujz__huz = lir.Function(module, ild__kknde, name='nrt_atomic_{0}'.
        format(op))
    [tsbv__iojt] = ujz__huz.args
    jkepv__cuin = ujz__huz.append_basic_block()
    builder = lir.IRBuilder(jkepv__cuin)
    ywxqj__ebuik = lir.Constant(_word_type, 1)
    if False:
        rnku__xlvge = builder.atomic_rmw(op, tsbv__iojt, ywxqj__ebuik,
            ordering=ordering)
        res = getattr(builder, op)(rnku__xlvge, ywxqj__ebuik)
        builder.ret(res)
    else:
        rnku__xlvge = builder.load(tsbv__iojt)
        wzz__ycxpi = getattr(builder, op)(rnku__xlvge, ywxqj__ebuik)
        dha__vrvgr = builder.icmp_signed('!=', rnku__xlvge, lir.Constant(
            rnku__xlvge.type, -1))
        with cgutils.if_likely(builder, dha__vrvgr):
            builder.store(wzz__ycxpi, tsbv__iojt)
        builder.ret(wzz__ycxpi)
    return ujz__huz


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
        cbfcv__omz = state.targetctx.codegen()
        state.library = cbfcv__omz.create_library(state.func_id.func_qualname)
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    njlk__efph = state.func_ir
    typemap = state.typemap
    gby__ich = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    dhfn__kkrih = state.metadata
    kuyaj__ibvym = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        vqj__wfk = funcdesc.PythonFunctionDescriptor.from_specialized_function(
            njlk__efph, typemap, gby__ich, calltypes, mangler=targetctx.
            mangler, inline=flags.forceinline, noalias=flags.noalias,
            abi_tags=[flags.get_mangle_string()])
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            brr__qpbtc = lowering.Lower(targetctx, library, vqj__wfk,
                njlk__efph, metadata=dhfn__kkrih)
            brr__qpbtc.lower()
            if not flags.no_cpython_wrapper:
                brr__qpbtc.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(gby__ich, (types.Optional, types.Generator)):
                        pass
                    else:
                        brr__qpbtc.create_cfunc_wrapper()
            vex__abu = brr__qpbtc.env
            vgub__ynv = brr__qpbtc.call_helper
            del brr__qpbtc
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(vqj__wfk, vgub__ynv, cfunc=None, env
                =vex__abu)
        else:
            khtj__wvlu = targetctx.get_executable(library, vqj__wfk, vex__abu)
            targetctx.insert_user_function(khtj__wvlu, vqj__wfk, [library])
            state['cr'] = _LowerResult(vqj__wfk, vgub__ynv, cfunc=
                khtj__wvlu, env=vex__abu)
        dhfn__kkrih['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        ena__izv = llvm.passmanagers.dump_refprune_stats()
        dhfn__kkrih['prune_stats'] = ena__izv - kuyaj__ibvym
        dhfn__kkrih['llvm_pass_timings'] = library.recorded_timings
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
        ige__qkpxz = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, ige__qkpxz),
            likely=False):
            c.builder.store(cgutils.true_bit, errorptr)
            iaedt__nxr.do_break()
        wba__zrvk = c.builder.icmp_signed('!=', ige__qkpxz, expected_typobj)
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(wba__zrvk, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, ige__qkpxz)
                c.pyapi.decref(ige__qkpxz)
                iaedt__nxr.do_break()
        c.pyapi.decref(ige__qkpxz)
    hudk__rxfng, list = listobj.ListInstance.allocate_ex(c.context, c.
        builder, typ, size)
    with c.builder.if_else(hudk__rxfng, likely=True) as (ztx__racxx,
        lpdck__mmss):
        with ztx__racxx:
            list.size = size
            yzmvb__keud = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                yzmvb__keud), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        yzmvb__keud))
                    with cgutils.for_range(c.builder, size) as iaedt__nxr:
                        itemobj = c.pyapi.list_getitem(obj, iaedt__nxr.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        qam__qhn = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(qam__qhn.is_error, likely=False
                            ):
                            c.builder.store(cgutils.true_bit, errorptr)
                            iaedt__nxr.do_break()
                        list.setitem(iaedt__nxr.index, qam__qhn.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with lpdck__mmss:
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
    ijya__lyyl, rool__csdt, eikc__ceo, dqtk__skyui, kxut__kcod = (
        compile_time_get_string_data(literal_string))
    nzo__dtpa = builder.module
    gv = context.insert_const_bytes(nzo__dtpa, ijya__lyyl)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        rool__csdt), context.get_constant(types.int32, eikc__ceo), context.
        get_constant(types.uint32, dqtk__skyui), context.get_constant(
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
    nps__yypwq = None
    if isinstance(shape, types.Integer):
        nps__yypwq = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(oirs__halwl, (types.Integer, types.IntEnumMember)
            ) for oirs__halwl in shape):
            nps__yypwq = len(shape)
    return nps__yypwq


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
            nps__yypwq = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if nps__yypwq == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(nps__yypwq)
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
            ktw__pbrn = self._get_names(x)
            if len(ktw__pbrn) != 0:
                return ktw__pbrn[0]
            return ktw__pbrn
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    ktw__pbrn = self._get_names(obj)
    if len(ktw__pbrn) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(ktw__pbrn[0])


def get_equiv_set(self, obj):
    ktw__pbrn = self._get_names(obj)
    if len(ktw__pbrn) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(ktw__pbrn[0])


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
    skugy__ckvd = []
    for lclj__pxmwm in func_ir.arg_names:
        if lclj__pxmwm in typemap and isinstance(typemap[lclj__pxmwm],
            types.containers.UniTuple) and typemap[lclj__pxmwm].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(lclj__pxmwm))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for kvo__mta in func_ir.blocks.values():
        for stmt in kvo__mta.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    yzm__wun = getattr(val, 'code', None)
                    if yzm__wun is not None:
                        if getattr(val, 'closure', None) is not None:
                            pyhmk__feddl = (
                                '<creating a function from a closure>')
                            hnvbm__rtgpl = ''
                        else:
                            pyhmk__feddl = yzm__wun.co_name
                            hnvbm__rtgpl = '(%s) ' % pyhmk__feddl
                    else:
                        pyhmk__feddl = '<could not ascertain use case>'
                        hnvbm__rtgpl = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (pyhmk__feddl, hnvbm__rtgpl))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                zknj__qhh = False
                if isinstance(val, pytypes.FunctionType):
                    zknj__qhh = val in {numba.gdb, numba.gdb_init}
                if not zknj__qhh:
                    zknj__qhh = getattr(val, '_name', '') == 'gdb_internal'
                if zknj__qhh:
                    skugy__ckvd.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    kccd__otrh = func_ir.get_definition(var)
                    audgm__uyo = guard(find_callname, func_ir, kccd__otrh)
                    if audgm__uyo and audgm__uyo[1] == 'numpy':
                        ty = getattr(numpy, audgm__uyo[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    kqwy__zbc = '' if var.startswith('$') else "'{}' ".format(
                        var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(kqwy__zbc), loc=stmt.loc)
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
    if len(skugy__ckvd) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        wkl__mzg = '\n'.join([x.strformat() for x in skugy__ckvd])
        raise errors.UnsupportedError(msg % wkl__mzg)


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
    crp__cnln, zwl__spy = next(iter(val.items()))
    gzeq__tbprd = typeof_impl(crp__cnln, c)
    uph__gtqgn = typeof_impl(zwl__spy, c)
    if gzeq__tbprd is None or uph__gtqgn is None:
        raise ValueError(
            f'Cannot type dict element type {type(crp__cnln)}, {type(zwl__spy)}'
            )
    return types.DictType(gzeq__tbprd, uph__gtqgn)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    goedx__gxww = cgutils.alloca_once_value(c.builder, val)
    pdy__efiob = c.pyapi.object_hasattr_string(val, '_opaque')
    mavnh__lqtw = c.builder.icmp_unsigned('==', pdy__efiob, lir.Constant(
        pdy__efiob.type, 0))
    hbfaa__ebwlw = typ.key_type
    qtte__bbyw = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(hbfaa__ebwlw, qtte__bbyw)

    def copy_dict(out_dict, in_dict):
        for crp__cnln, zwl__spy in in_dict.items():
            out_dict[crp__cnln] = zwl__spy
    with c.builder.if_then(mavnh__lqtw):
        ifis__hkl = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        xjfn__zhdal = c.pyapi.call_function_objargs(ifis__hkl, [])
        cnax__fixg = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(cnax__fixg, [xjfn__zhdal, val])
        c.builder.store(xjfn__zhdal, goedx__gxww)
    val = c.builder.load(goedx__gxww)
    vczrl__bzbr = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    zepa__vqr = c.pyapi.object_type(val)
    hjtux__uwv = c.builder.icmp_unsigned('==', zepa__vqr, vczrl__bzbr)
    with c.builder.if_else(hjtux__uwv) as (xxg__vtess, ikspw__yaj):
        with xxg__vtess:
            xbwq__fjrfb = c.pyapi.object_getattr_string(val, '_opaque')
            adqd__chf = types.MemInfoPointer(types.voidptr)
            qam__qhn = c.unbox(adqd__chf, xbwq__fjrfb)
            mi = qam__qhn.value
            ppxan__cdkfq = adqd__chf, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *ppxan__cdkfq)
            cwcgx__aqmc = context.get_constant_null(ppxan__cdkfq[1])
            args = mi, cwcgx__aqmc
            fxzs__ojed, bclmx__iyc = c.pyapi.call_jit_code(convert, sig, args)
            c.context.nrt.decref(c.builder, typ, bclmx__iyc)
            c.pyapi.decref(xbwq__fjrfb)
            sbsi__qqvc = c.builder.basic_block
        with ikspw__yaj:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", zepa__vqr, vczrl__bzbr)
            afdd__ytmh = c.builder.basic_block
    cfzfv__sejo = c.builder.phi(bclmx__iyc.type)
    tqchc__vpr = c.builder.phi(fxzs__ojed.type)
    cfzfv__sejo.add_incoming(bclmx__iyc, sbsi__qqvc)
    cfzfv__sejo.add_incoming(bclmx__iyc.type(None), afdd__ytmh)
    tqchc__vpr.add_incoming(fxzs__ojed, sbsi__qqvc)
    tqchc__vpr.add_incoming(cgutils.true_bit, afdd__ytmh)
    c.pyapi.decref(vczrl__bzbr)
    c.pyapi.decref(zepa__vqr)
    with c.builder.if_then(mavnh__lqtw):
        c.pyapi.decref(val)
    return NativeValue(cfzfv__sejo, is_error=tqchc__vpr)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, uul__rdl = args
    if isinstance(a, types.List) and isinstance(uul__rdl, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(uul__rdl, types.List):
        return signature(uul__rdl, types.intp, uul__rdl)


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
        kbawu__kih, fmg__bck = 0, 1
    else:
        kbawu__kih, fmg__bck = 1, 0
    tsz__cehnl = ListInstance(context, builder, sig.args[kbawu__kih], args[
        kbawu__kih])
    thk__wqojy = tsz__cehnl.size
    ghjb__acg = args[fmg__bck]
    yzmvb__keud = lir.Constant(ghjb__acg.type, 0)
    ghjb__acg = builder.select(cgutils.is_neg_int(builder, ghjb__acg),
        yzmvb__keud, ghjb__acg)
    yew__cbrz = builder.mul(ghjb__acg, thk__wqojy)
    oadn__cujlh = ListInstance.allocate(context, builder, sig.return_type,
        yew__cbrz)
    oadn__cujlh.size = yew__cbrz
    with cgutils.for_range_slice(builder, yzmvb__keud, yew__cbrz,
        thk__wqojy, inc=True) as (tst__pyvkn, _):
        with cgutils.for_range(builder, thk__wqojy) as iaedt__nxr:
            value = tsz__cehnl.getitem(iaedt__nxr.index)
            oadn__cujlh.setitem(builder.add(iaedt__nxr.index, tst__pyvkn),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, oadn__cujlh.
        value)


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    yew__cbrz = payload.used
    listobj = c.pyapi.list_new(yew__cbrz)
    hudk__rxfng = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(hudk__rxfng, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(yew__cbrz.
            type, 0))
        with payload._iterate() as iaedt__nxr:
            i = c.builder.load(index)
            item = iaedt__nxr.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return hudk__rxfng, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    jbem__fsgju = h.type
    vgmzp__esbpd = self.mask
    dtype = self._ty.dtype
    ncup__tqigg = context.typing_context
    fnty = ncup__tqigg.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(ncup__tqigg, (dtype, dtype), {})
    kylun__ofk = context.get_function(fnty, sig)
    ybsj__hkjz = ir.Constant(jbem__fsgju, 1)
    rdyk__aouq = ir.Constant(jbem__fsgju, 5)
    zbun__qmr = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, vgmzp__esbpd))
    if for_insert:
        eia__wokv = vgmzp__esbpd.type(-1)
        qatps__gnt = cgutils.alloca_once_value(builder, eia__wokv)
    puo__awd = builder.append_basic_block('lookup.body')
    lpaa__dksj = builder.append_basic_block('lookup.found')
    arf__pjp = builder.append_basic_block('lookup.not_found')
    mfv__lvey = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        xymz__scvx = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, xymz__scvx)):
            qwh__kuktq = kylun__ofk(builder, (item, entry.key))
            with builder.if_then(qwh__kuktq):
                builder.branch(lpaa__dksj)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, xymz__scvx)):
            builder.branch(arf__pjp)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, xymz__scvx)):
                tyflr__vwuaw = builder.load(qatps__gnt)
                tyflr__vwuaw = builder.select(builder.icmp_unsigned('==',
                    tyflr__vwuaw, eia__wokv), i, tyflr__vwuaw)
                builder.store(tyflr__vwuaw, qatps__gnt)
    with cgutils.for_range(builder, ir.Constant(jbem__fsgju, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, ybsj__hkjz)
        i = builder.and_(i, vgmzp__esbpd)
        builder.store(i, index)
    builder.branch(puo__awd)
    with builder.goto_block(puo__awd):
        i = builder.load(index)
        check_entry(i)
        xxs__yyca = builder.load(zbun__qmr)
        xxs__yyca = builder.lshr(xxs__yyca, rdyk__aouq)
        i = builder.add(ybsj__hkjz, builder.mul(i, rdyk__aouq))
        i = builder.and_(vgmzp__esbpd, builder.add(i, xxs__yyca))
        builder.store(i, index)
        builder.store(xxs__yyca, zbun__qmr)
        builder.branch(puo__awd)
    with builder.goto_block(arf__pjp):
        if for_insert:
            i = builder.load(index)
            tyflr__vwuaw = builder.load(qatps__gnt)
            i = builder.select(builder.icmp_unsigned('==', tyflr__vwuaw,
                eia__wokv), i, tyflr__vwuaw)
            builder.store(i, index)
        builder.branch(mfv__lvey)
    with builder.goto_block(lpaa__dksj):
        builder.branch(mfv__lvey)
    builder.position_at_end(mfv__lvey)
    zknj__qhh = builder.phi(ir.IntType(1), 'found')
    zknj__qhh.add_incoming(cgutils.true_bit, lpaa__dksj)
    zknj__qhh.add_incoming(cgutils.false_bit, arf__pjp)
    return zknj__qhh, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    fdd__drwq = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    wvg__fuhhm = payload.used
    ybsj__hkjz = ir.Constant(wvg__fuhhm.type, 1)
    wvg__fuhhm = payload.used = builder.add(wvg__fuhhm, ybsj__hkjz)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, fdd__drwq), likely=True):
        payload.fill = builder.add(payload.fill, ybsj__hkjz)
    if do_resize:
        self.upsize(wvg__fuhhm)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    zknj__qhh, i = payload._lookup(item, h, for_insert=True)
    yrtd__hkjo = builder.not_(zknj__qhh)
    with builder.if_then(yrtd__hkjo):
        entry = payload.get_entry(i)
        fdd__drwq = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        wvg__fuhhm = payload.used
        ybsj__hkjz = ir.Constant(wvg__fuhhm.type, 1)
        wvg__fuhhm = payload.used = builder.add(wvg__fuhhm, ybsj__hkjz)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, fdd__drwq), likely=True):
            payload.fill = builder.add(payload.fill, ybsj__hkjz)
        if do_resize:
            self.upsize(wvg__fuhhm)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    wvg__fuhhm = payload.used
    ybsj__hkjz = ir.Constant(wvg__fuhhm.type, 1)
    wvg__fuhhm = payload.used = self._builder.sub(wvg__fuhhm, ybsj__hkjz)
    if do_resize:
        self.downsize(wvg__fuhhm)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    yrk__bfrvj = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, yrk__bfrvj)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    myk__jyze = payload
    hudk__rxfng = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(hudk__rxfng), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with myk__jyze._iterate() as iaedt__nxr:
        entry = iaedt__nxr.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(myk__jyze.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as iaedt__nxr:
        entry = iaedt__nxr.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    hudk__rxfng = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(hudk__rxfng), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    hudk__rxfng = cgutils.alloca_once_value(builder, cgutils.true_bit)
    jbem__fsgju = context.get_value_type(types.intp)
    yzmvb__keud = ir.Constant(jbem__fsgju, 0)
    ybsj__hkjz = ir.Constant(jbem__fsgju, 1)
    dib__ilaq = context.get_data_type(types.SetPayload(self._ty))
    yny__rhjwb = context.get_abi_sizeof(dib__ilaq)
    kiwl__nhp = self._entrysize
    yny__rhjwb -= kiwl__nhp
    kbkew__ark, xlnkj__dpuxz = cgutils.muladd_with_overflow(builder,
        nentries, ir.Constant(jbem__fsgju, kiwl__nhp), ir.Constant(
        jbem__fsgju, yny__rhjwb))
    with builder.if_then(xlnkj__dpuxz, likely=False):
        builder.store(cgutils.false_bit, hudk__rxfng)
    with builder.if_then(builder.load(hudk__rxfng), likely=True):
        if realloc:
            hwoc__wuzoz = self._set.meminfo
            tsbv__iojt = context.nrt.meminfo_varsize_alloc(builder,
                hwoc__wuzoz, size=kbkew__ark)
            xqq__hlo = cgutils.is_null(builder, tsbv__iojt)
        else:
            zqxq__nhoza = _imp_dtor(context, builder.module, self._ty)
            hwoc__wuzoz = context.nrt.meminfo_new_varsize_dtor(builder,
                kbkew__ark, builder.bitcast(zqxq__nhoza, cgutils.voidptr_t))
            xqq__hlo = cgutils.is_null(builder, hwoc__wuzoz)
        with builder.if_else(xqq__hlo, likely=False) as (htbt__qxeq, ztx__racxx
            ):
            with htbt__qxeq:
                builder.store(cgutils.false_bit, hudk__rxfng)
            with ztx__racxx:
                if not realloc:
                    self._set.meminfo = hwoc__wuzoz
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, kbkew__ark, 255)
                payload.used = yzmvb__keud
                payload.fill = yzmvb__keud
                payload.finger = yzmvb__keud
                krz__xesqb = builder.sub(nentries, ybsj__hkjz)
                payload.mask = krz__xesqb
    return builder.load(hudk__rxfng)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    hudk__rxfng = cgutils.alloca_once_value(builder, cgutils.true_bit)
    jbem__fsgju = context.get_value_type(types.intp)
    yzmvb__keud = ir.Constant(jbem__fsgju, 0)
    ybsj__hkjz = ir.Constant(jbem__fsgju, 1)
    dib__ilaq = context.get_data_type(types.SetPayload(self._ty))
    yny__rhjwb = context.get_abi_sizeof(dib__ilaq)
    kiwl__nhp = self._entrysize
    yny__rhjwb -= kiwl__nhp
    vgmzp__esbpd = src_payload.mask
    nentries = builder.add(ybsj__hkjz, vgmzp__esbpd)
    kbkew__ark = builder.add(ir.Constant(jbem__fsgju, yny__rhjwb), builder.
        mul(ir.Constant(jbem__fsgju, kiwl__nhp), nentries))
    with builder.if_then(builder.load(hudk__rxfng), likely=True):
        zqxq__nhoza = _imp_dtor(context, builder.module, self._ty)
        hwoc__wuzoz = context.nrt.meminfo_new_varsize_dtor(builder,
            kbkew__ark, builder.bitcast(zqxq__nhoza, cgutils.voidptr_t))
        xqq__hlo = cgutils.is_null(builder, hwoc__wuzoz)
        with builder.if_else(xqq__hlo, likely=False) as (htbt__qxeq, ztx__racxx
            ):
            with htbt__qxeq:
                builder.store(cgutils.false_bit, hudk__rxfng)
            with ztx__racxx:
                self._set.meminfo = hwoc__wuzoz
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = yzmvb__keud
                payload.mask = vgmzp__esbpd
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, kiwl__nhp)
                with src_payload._iterate() as iaedt__nxr:
                    context.nrt.incref(builder, self._ty.dtype, iaedt__nxr.
                        entry.key)
    return builder.load(hudk__rxfng)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    bxfe__mhvea = context.get_value_type(types.voidptr)
    drjw__jqa = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [bxfe__mhvea, drjw__jqa, bxfe__mhvea]
        )
    bda__otmfr = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=bda__otmfr)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        rvzh__ozy = builder.bitcast(fn.args[0], cgutils.voidptr_t.as_pointer())
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, rvzh__ozy)
        with payload._iterate() as iaedt__nxr:
            entry = iaedt__nxr.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    tzkj__sux, = sig.args
    mgrzv__kawjt, = args
    eqjql__twhii = numba.core.imputils.call_len(context, builder, tzkj__sux,
        mgrzv__kawjt)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, eqjql__twhii)
    with numba.core.imputils.for_iter(context, builder, tzkj__sux, mgrzv__kawjt
        ) as iaedt__nxr:
        inst.add(iaedt__nxr.value)
        context.nrt.decref(builder, set_type.dtype, iaedt__nxr.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    tzkj__sux = sig.args[1]
    mgrzv__kawjt = args[1]
    eqjql__twhii = numba.core.imputils.call_len(context, builder, tzkj__sux,
        mgrzv__kawjt)
    if eqjql__twhii is not None:
        szey__jqgr = builder.add(inst.payload.used, eqjql__twhii)
        inst.upsize(szey__jqgr)
    with numba.core.imputils.for_iter(context, builder, tzkj__sux, mgrzv__kawjt
        ) as iaedt__nxr:
        mpdfj__vmx = context.cast(builder, iaedt__nxr.value, tzkj__sux.
            dtype, inst.dtype)
        inst.add(mpdfj__vmx)
        context.nrt.decref(builder, tzkj__sux.dtype, iaedt__nxr.value)
    if eqjql__twhii is not None:
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
