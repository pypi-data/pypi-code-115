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
    mmvoe__ivl = numba.core.bytecode.FunctionIdentity.from_function(func)
    tws__xmbci = numba.core.interpreter.Interpreter(mmvoe__ivl)
    ool__lmluq = numba.core.bytecode.ByteCode(func_id=mmvoe__ivl)
    func_ir = tws__xmbci.interpret(ool__lmluq)
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
        okv__ihg = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        okv__ihg.run()
    ihy__ncfvr = numba.core.postproc.PostProcessor(func_ir)
    ihy__ncfvr.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, tyko__wifvd in visit_vars_extensions.items():
        if isinstance(stmt, t):
            tyko__wifvd(stmt, callback, cbdata)
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
    nye__rhohw = ['ravel', 'transpose', 'reshape']
    for jcnos__lkxq in blocks.values():
        for ooqm__dmg in jcnos__lkxq.body:
            if type(ooqm__dmg) in alias_analysis_extensions:
                tyko__wifvd = alias_analysis_extensions[type(ooqm__dmg)]
                tyko__wifvd(ooqm__dmg, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(ooqm__dmg, ir.Assign):
                aykg__apuel = ooqm__dmg.value
                hun__bzhso = ooqm__dmg.target.name
                if is_immutable_type(hun__bzhso, typemap):
                    continue
                if isinstance(aykg__apuel, ir.Var
                    ) and hun__bzhso != aykg__apuel.name:
                    _add_alias(hun__bzhso, aykg__apuel.name, alias_map,
                        arg_aliases)
                if isinstance(aykg__apuel, ir.Expr) and (aykg__apuel.op ==
                    'cast' or aykg__apuel.op in ['getitem', 'static_getitem']):
                    _add_alias(hun__bzhso, aykg__apuel.value.name,
                        alias_map, arg_aliases)
                if isinstance(aykg__apuel, ir.Expr
                    ) and aykg__apuel.op == 'inplace_binop':
                    _add_alias(hun__bzhso, aykg__apuel.lhs.name, alias_map,
                        arg_aliases)
                if isinstance(aykg__apuel, ir.Expr
                    ) and aykg__apuel.op == 'getattr' and aykg__apuel.attr in [
                    'T', 'ctypes', 'flat']:
                    _add_alias(hun__bzhso, aykg__apuel.value.name,
                        alias_map, arg_aliases)
                if isinstance(aykg__apuel, ir.Expr
                    ) and aykg__apuel.op == 'getattr' and aykg__apuel.attr not in [
                    'shape'] and aykg__apuel.value.name in arg_aliases:
                    _add_alias(hun__bzhso, aykg__apuel.value.name,
                        alias_map, arg_aliases)
                if isinstance(aykg__apuel, ir.Expr
                    ) and aykg__apuel.op == 'getattr' and aykg__apuel.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(hun__bzhso, aykg__apuel.value.name,
                        alias_map, arg_aliases)
                if isinstance(aykg__apuel, ir.Expr) and aykg__apuel.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(hun__bzhso, typemap):
                    for gdkp__ntx in aykg__apuel.items:
                        _add_alias(hun__bzhso, gdkp__ntx.name, alias_map,
                            arg_aliases)
                if isinstance(aykg__apuel, ir.Expr
                    ) and aykg__apuel.op == 'call':
                    jaa__fprt = guard(find_callname, func_ir, aykg__apuel,
                        typemap)
                    if jaa__fprt is None:
                        continue
                    tamcb__tbk, vquwf__qoh = jaa__fprt
                    if jaa__fprt in alias_func_extensions:
                        avft__rmb = alias_func_extensions[jaa__fprt]
                        avft__rmb(hun__bzhso, aykg__apuel.args, alias_map,
                            arg_aliases)
                    if vquwf__qoh == 'numpy' and tamcb__tbk in nye__rhohw:
                        _add_alias(hun__bzhso, aykg__apuel.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(vquwf__qoh, ir.Var
                        ) and tamcb__tbk in nye__rhohw:
                        _add_alias(hun__bzhso, vquwf__qoh.name, alias_map,
                            arg_aliases)
    erxtl__upkfl = copy.deepcopy(alias_map)
    for gdkp__ntx in erxtl__upkfl:
        for hrlvr__ocg in erxtl__upkfl[gdkp__ntx]:
            alias_map[gdkp__ntx] |= alias_map[hrlvr__ocg]
        for hrlvr__ocg in erxtl__upkfl[gdkp__ntx]:
            alias_map[hrlvr__ocg] = alias_map[gdkp__ntx]
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
    lxsn__gmaw = compute_cfg_from_blocks(func_ir.blocks)
    bsx__bbq = compute_use_defs(func_ir.blocks)
    hej__yvvaw = compute_live_map(lxsn__gmaw, func_ir.blocks, bsx__bbq.
        usemap, bsx__bbq.defmap)
    oeh__axy = True
    while oeh__axy:
        oeh__axy = False
        for tktvw__wflam, block in func_ir.blocks.items():
            lives = {gdkp__ntx.name for gdkp__ntx in block.terminator.
                list_vars()}
            for dxa__sac, skunf__cdbzt in lxsn__gmaw.successors(tktvw__wflam):
                lives |= hej__yvvaw[dxa__sac]
            fbrpy__pjo = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    hun__bzhso = stmt.target
                    kqpp__sexcj = stmt.value
                    if hun__bzhso.name not in lives:
                        if isinstance(kqpp__sexcj, ir.Expr
                            ) and kqpp__sexcj.op == 'make_function':
                            continue
                        if isinstance(kqpp__sexcj, ir.Expr
                            ) and kqpp__sexcj.op == 'getattr':
                            continue
                        if isinstance(kqpp__sexcj, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(hun__bzhso,
                            None), types.Function):
                            continue
                        if isinstance(kqpp__sexcj, ir.Expr
                            ) and kqpp__sexcj.op == 'build_map':
                            continue
                    if isinstance(kqpp__sexcj, ir.Var
                        ) and hun__bzhso.name == kqpp__sexcj.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    bsprz__noh = analysis.ir_extension_usedefs[type(stmt)]
                    ugaq__ftzne, lhc__jok = bsprz__noh(stmt)
                    lives -= lhc__jok
                    lives |= ugaq__ftzne
                else:
                    lives |= {gdkp__ntx.name for gdkp__ntx in stmt.list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(hun__bzhso.name)
                fbrpy__pjo.append(stmt)
            fbrpy__pjo.reverse()
            if len(block.body) != len(fbrpy__pjo):
                oeh__axy = True
            block.body = fbrpy__pjo


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    mwjf__mumdk = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (mwjf__mumdk,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    ocmm__wmu = dict(key=func, _overload_func=staticmethod(overload_func),
        _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), ocmm__wmu)


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
            for qwm__zabcn in fnty.templates:
                self._inline_overloads.update(qwm__zabcn._inline_overloads)
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
    ocmm__wmu = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), ocmm__wmu)
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
    viire__vhipy, ctniv__lhiy = self._get_impl(args, kws)
    if viire__vhipy is None:
        return
    hop__dor = types.Dispatcher(viire__vhipy)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        wrzkf__htl = viire__vhipy._compiler
        flags = compiler.Flags()
        hlvvn__iewlz = wrzkf__htl.targetdescr.typing_context
        rmt__wdqgd = wrzkf__htl.targetdescr.target_context
        plyy__gnwb = wrzkf__htl.pipeline_class(hlvvn__iewlz, rmt__wdqgd,
            None, None, None, flags, None)
        jbhx__ksbxc = InlineWorker(hlvvn__iewlz, rmt__wdqgd, wrzkf__htl.
            locals, plyy__gnwb, flags, None)
        ekh__ower = hop__dor.dispatcher.get_call_template
        qwm__zabcn, hlu__yorm, xmxh__ptmxw, kws = ekh__ower(ctniv__lhiy, kws)
        if xmxh__ptmxw in self._inline_overloads:
            return self._inline_overloads[xmxh__ptmxw]['iinfo'].signature
        ir = jbhx__ksbxc.run_untyped_passes(hop__dor.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, rmt__wdqgd, ir, xmxh__ptmxw, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, xmxh__ptmxw, None)
        self._inline_overloads[sig.args] = {'folded_args': xmxh__ptmxw}
        vhw__rue = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = vhw__rue
        if not self._inline.is_always_inline:
            sig = hop__dor.get_call_type(self.context, ctniv__lhiy, kws)
            self._compiled_overloads[sig.args] = hop__dor.get_overload(sig)
        nuev__xlqoe = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': xmxh__ptmxw,
            'iinfo': nuev__xlqoe}
    else:
        sig = hop__dor.get_call_type(self.context, ctniv__lhiy, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = hop__dor.get_overload(sig)
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
    pevzw__wuz = [True, False]
    hbhf__vgxw = [False, True]
    sktr__bkubq = _ResolutionFailures(context, self, args, kws, depth=self.
        _depth)
    from numba.core.target_extension import get_local_target
    bsos__fqhrq = get_local_target(context)
    iwja__qdvce = utils.order_by_target_specificity(bsos__fqhrq, self.
        templates, fnkey=self.key[0])
    self._depth += 1
    for uxe__pxqck in iwja__qdvce:
        etczv__ibhg = uxe__pxqck(context)
        hurt__ihg = pevzw__wuz if etczv__ibhg.prefer_literal else hbhf__vgxw
        hurt__ihg = [True] if getattr(etczv__ibhg, '_no_unliteral', False
            ) else hurt__ihg
        for rzpig__ilm in hurt__ihg:
            try:
                if rzpig__ilm:
                    sig = etczv__ibhg.apply(args, kws)
                else:
                    gxsav__npdv = tuple([_unlit_non_poison(a) for a in args])
                    sfd__egkpe = {ptgms__gtcb: _unlit_non_poison(gdkp__ntx) for
                        ptgms__gtcb, gdkp__ntx in kws.items()}
                    sig = etczv__ibhg.apply(gxsav__npdv, sfd__egkpe)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    sktr__bkubq.add_error(etczv__ibhg, False, e, rzpig__ilm)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = etczv__ibhg.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    nax__ebgw = getattr(etczv__ibhg, 'cases', None)
                    if nax__ebgw is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            nax__ebgw)
                    else:
                        msg = 'No match.'
                    sktr__bkubq.add_error(etczv__ibhg, True, msg, rzpig__ilm)
    sktr__bkubq.raise_error()


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
    qwm__zabcn = self.template(context)
    iiy__guhtr = None
    tuk__yxsa = None
    hifgb__bbj = None
    hurt__ihg = [True, False] if qwm__zabcn.prefer_literal else [False, True]
    hurt__ihg = [True] if getattr(qwm__zabcn, '_no_unliteral', False
        ) else hurt__ihg
    for rzpig__ilm in hurt__ihg:
        if rzpig__ilm:
            try:
                hifgb__bbj = qwm__zabcn.apply(args, kws)
            except Exception as ysvp__mgadj:
                if isinstance(ysvp__mgadj, errors.ForceLiteralArg):
                    raise ysvp__mgadj
                iiy__guhtr = ysvp__mgadj
                hifgb__bbj = None
            else:
                break
        else:
            mxze__hvz = tuple([_unlit_non_poison(a) for a in args])
            phv__xnem = {ptgms__gtcb: _unlit_non_poison(gdkp__ntx) for 
                ptgms__gtcb, gdkp__ntx in kws.items()}
            eoi__dgfx = mxze__hvz == args and kws == phv__xnem
            if not eoi__dgfx and hifgb__bbj is None:
                try:
                    hifgb__bbj = qwm__zabcn.apply(mxze__hvz, phv__xnem)
                except Exception as ysvp__mgadj:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(
                        ysvp__mgadj, errors.NumbaError):
                        raise ysvp__mgadj
                    if isinstance(ysvp__mgadj, errors.ForceLiteralArg):
                        if qwm__zabcn.prefer_literal:
                            raise ysvp__mgadj
                    tuk__yxsa = ysvp__mgadj
                else:
                    break
    if hifgb__bbj is None and (tuk__yxsa is not None or iiy__guhtr is not None
        ):
        dlvxf__mql = '- Resolution failure for {} arguments:\n{}\n'
        irzn__fjlzy = _termcolor.highlight(dlvxf__mql)
        if numba.core.config.DEVELOPER_MODE:
            qzgt__ter = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    drgk__pyj = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    drgk__pyj = ['']
                uanj__ogh = '\n{}'.format(2 * qzgt__ter)
                yrbj__zoqun = _termcolor.reset(uanj__ogh + uanj__ogh.join(
                    _bt_as_lines(drgk__pyj)))
                return _termcolor.reset(yrbj__zoqun)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            eqqt__vkimp = str(e)
            eqqt__vkimp = eqqt__vkimp if eqqt__vkimp else str(repr(e)
                ) + add_bt(e)
            sxq__aehx = errors.TypingError(textwrap.dedent(eqqt__vkimp))
            return irzn__fjlzy.format(literalness, str(sxq__aehx))
        import bodo
        if isinstance(iiy__guhtr, bodo.utils.typing.BodoError):
            raise iiy__guhtr
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', iiy__guhtr) +
                nested_msg('non-literal', tuk__yxsa))
        else:
            if 'missing a required argument' in iiy__guhtr.msg:
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
            raise errors.TypingError(msg, loc=iiy__guhtr.loc)
    return hifgb__bbj


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
    tamcb__tbk = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=tamcb__tbk)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            cre__arzdj = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), cre__arzdj)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    yybr__osjg = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            yybr__osjg.append(types.Omitted(a.value))
        else:
            yybr__osjg.append(self.typeof_pyval(a))
    vniz__keb = None
    try:
        error = None
        vniz__keb = self.compile(tuple(yybr__osjg))
    except errors.ForceLiteralArg as e:
        ribh__kup = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if ribh__kup:
            scoi__oggzy = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            aqdo__mqhvp = ', '.join('Arg #{} is {}'.format(i, args[i]) for
                i in sorted(ribh__kup))
            raise errors.CompilerError(scoi__oggzy.format(aqdo__mqhvp))
        ctniv__lhiy = []
        try:
            for i, gdkp__ntx in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        ctniv__lhiy.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        ctniv__lhiy.append(types.literal(args[i]))
                else:
                    ctniv__lhiy.append(args[i])
            args = ctniv__lhiy
        except (OSError, FileNotFoundError) as vktng__tyc:
            error = FileNotFoundError(str(vktng__tyc) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                vniz__keb = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        sofo__hiui = []
        for i, iwf__udv in enumerate(args):
            val = iwf__udv.value if isinstance(iwf__udv, numba.core.
                dispatcher.OmittedArg) else iwf__udv
            try:
                vpu__zkrb = typeof(val, Purpose.argument)
            except ValueError as kcrtx__uiw:
                sofo__hiui.append((i, str(kcrtx__uiw)))
            else:
                if vpu__zkrb is None:
                    sofo__hiui.append((i,
                        f'cannot determine Numba type of value {val}'))
        if sofo__hiui:
            konau__its = '\n'.join(f'- argument {i}: {tvjhy__nbwnu}' for i,
                tvjhy__nbwnu in sofo__hiui)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{konau__its}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                ayhee__tdpuk = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                yddp__xxhdx = False
                for pele__teum in ayhee__tdpuk:
                    if pele__teum in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        yddp__xxhdx = True
                        break
                if not yddp__xxhdx:
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
                cre__arzdj = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), cre__arzdj)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return vniz__keb


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
    for bkzdj__rfur in cres.library._codegen._engine._defined_symbols:
        if bkzdj__rfur.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in bkzdj__rfur and (
            'bodo_gb_udf_update_local' in bkzdj__rfur or 
            'bodo_gb_udf_combine' in bkzdj__rfur or 'bodo_gb_udf_eval' in
            bkzdj__rfur or 'bodo_gb_apply_general_udfs' in bkzdj__rfur):
            gb_agg_cfunc_addr[bkzdj__rfur
                ] = cres.library.get_pointer_to_function(bkzdj__rfur)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for bkzdj__rfur in cres.library._codegen._engine._defined_symbols:
        if bkzdj__rfur.startswith('cfunc') and ('get_join_cond_addr' not in
            bkzdj__rfur or 'bodo_join_gen_cond' in bkzdj__rfur):
            join_gen_cond_cfunc_addr[bkzdj__rfur
                ] = cres.library.get_pointer_to_function(bkzdj__rfur)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    viire__vhipy = self._get_dispatcher_for_current_target()
    if viire__vhipy is not self:
        return viire__vhipy.compile(sig)
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
            eacy__kdffi = self.overloads.get(tuple(args))
            if eacy__kdffi is not None:
                return eacy__kdffi.entry_point
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
            mimfw__pbjvl = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=mimfw__pbjvl):
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
    uax__zkb = self._final_module
    sfsc__idhfe = []
    foq__xzy = 0
    for fn in uax__zkb.functions:
        foq__xzy += 1
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
            sfsc__idhfe.append(fn.name)
    if foq__xzy == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if sfsc__idhfe:
        uax__zkb = uax__zkb.clone()
        for name in sfsc__idhfe:
            uax__zkb.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = uax__zkb
    return uax__zkb


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
    for nqt__ais in self.constraints:
        loc = nqt__ais.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                nqt__ais(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                dagiz__lygx = numba.core.errors.TypingError(str(e), loc=
                    nqt__ais.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(dagiz__lygx, e))
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
                    dagiz__lygx = numba.core.errors.TypingError(msg.format(
                        con=nqt__ais, err=str(e)), loc=nqt__ais.loc,
                        highlighting=False)
                    errors.append(utils.chain_exception(dagiz__lygx, e))
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
    for oynk__kddkv in self._failures.values():
        for qlf__heh in oynk__kddkv:
            if isinstance(qlf__heh.error, ForceLiteralArg):
                raise qlf__heh.error
            if isinstance(qlf__heh.error, bodo.utils.typing.BodoError):
                raise qlf__heh.error
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
    xci__xkf = False
    fbrpy__pjo = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        vnrvj__zltl = set()
        jja__gnj = lives & alias_set
        for gdkp__ntx in jja__gnj:
            vnrvj__zltl |= alias_map[gdkp__ntx]
        lives_n_aliases = lives | vnrvj__zltl | arg_aliases
        if type(stmt) in remove_dead_extensions:
            tyko__wifvd = remove_dead_extensions[type(stmt)]
            stmt = tyko__wifvd(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                xci__xkf = True
                continue
        if isinstance(stmt, ir.Assign):
            hun__bzhso = stmt.target
            kqpp__sexcj = stmt.value
            if hun__bzhso.name not in lives and has_no_side_effect(kqpp__sexcj,
                lives_n_aliases, call_table):
                xci__xkf = True
                continue
            if saved_array_analysis and hun__bzhso.name in lives and is_expr(
                kqpp__sexcj, 'getattr'
                ) and kqpp__sexcj.attr == 'shape' and is_array_typ(typemap[
                kqpp__sexcj.value.name]
                ) and kqpp__sexcj.value.name not in lives:
                ueum__cit = {gdkp__ntx: ptgms__gtcb for ptgms__gtcb,
                    gdkp__ntx in func_ir.blocks.items()}
                if block in ueum__cit:
                    tktvw__wflam = ueum__cit[block]
                    utur__bktrp = saved_array_analysis.get_equiv_set(
                        tktvw__wflam)
                    nnpld__cxb = utur__bktrp.get_equiv_set(kqpp__sexcj.value)
                    if nnpld__cxb is not None:
                        for gdkp__ntx in nnpld__cxb:
                            if gdkp__ntx.endswith('#0'):
                                gdkp__ntx = gdkp__ntx[:-2]
                            if gdkp__ntx in typemap and is_array_typ(typemap
                                [gdkp__ntx]) and gdkp__ntx in lives:
                                kqpp__sexcj.value = ir.Var(kqpp__sexcj.
                                    value.scope, gdkp__ntx, kqpp__sexcj.
                                    value.loc)
                                xci__xkf = True
                                break
            if isinstance(kqpp__sexcj, ir.Var
                ) and hun__bzhso.name == kqpp__sexcj.name:
                xci__xkf = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                xci__xkf = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            bsprz__noh = analysis.ir_extension_usedefs[type(stmt)]
            ugaq__ftzne, lhc__jok = bsprz__noh(stmt)
            lives -= lhc__jok
            lives |= ugaq__ftzne
        else:
            lives |= {gdkp__ntx.name for gdkp__ntx in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                oiz__apzlx = set()
                if isinstance(kqpp__sexcj, ir.Expr):
                    oiz__apzlx = {gdkp__ntx.name for gdkp__ntx in
                        kqpp__sexcj.list_vars()}
                if hun__bzhso.name not in oiz__apzlx:
                    lives.remove(hun__bzhso.name)
        fbrpy__pjo.append(stmt)
    fbrpy__pjo.reverse()
    block.body = fbrpy__pjo
    return xci__xkf


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            glq__ovupx, = args
            if isinstance(glq__ovupx, types.IterableType):
                dtype = glq__ovupx.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), glq__ovupx)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    lmg__iuyzt = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (lmg__iuyzt, self.dtype)
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
        except LiteralTypingError as som__qorbe:
            return
    try:
        return literal(value)
    except LiteralTypingError as som__qorbe:
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
        wgeuw__qqw = py_func.__qualname__
    except AttributeError as som__qorbe:
        wgeuw__qqw = py_func.__name__
    wkj__etn = inspect.getfile(py_func)
    for cls in self._locator_classes:
        anfe__vvgue = cls.from_function(py_func, wkj__etn)
        if anfe__vvgue is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (wgeuw__qqw, wkj__etn))
    self._locator = anfe__vvgue
    tggx__yeoe = inspect.getfile(py_func)
    wfse__gxxk = os.path.splitext(os.path.basename(tggx__yeoe))[0]
    if wkj__etn.startswith('<ipython-'):
        ubt__zgj = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)', '\\1\\3',
            wfse__gxxk, count=1)
        if ubt__zgj == wfse__gxxk:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        wfse__gxxk = ubt__zgj
    fhr__eynht = '%s.%s' % (wfse__gxxk, wgeuw__qqw)
    iqaj__ojhw = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(fhr__eynht, iqaj__ojhw)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    pofl__tkld = list(filter(lambda a: self._istuple(a.name), args))
    if len(pofl__tkld) == 2 and fn.__name__ == 'add':
        dzhr__ujhg = self.typemap[pofl__tkld[0].name]
        qmbv__jlf = self.typemap[pofl__tkld[1].name]
        if dzhr__ujhg.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                pofl__tkld[1]))
        if qmbv__jlf.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                pofl__tkld[0]))
        try:
            unhs__voq = [equiv_set.get_shape(x) for x in pofl__tkld]
            if None in unhs__voq:
                return None
            rxkzs__pqu = sum(unhs__voq, ())
            return ArrayAnalysis.AnalyzeResult(shape=rxkzs__pqu)
        except GuardException as som__qorbe:
            return None
    gfs__yrvmz = list(filter(lambda a: self._isarray(a.name), args))
    require(len(gfs__yrvmz) > 0)
    vhgw__qavv = [x.name for x in gfs__yrvmz]
    kxdb__cfd = [self.typemap[x.name].ndim for x in gfs__yrvmz]
    njrvk__non = max(kxdb__cfd)
    require(njrvk__non > 0)
    unhs__voq = [equiv_set.get_shape(x) for x in gfs__yrvmz]
    if any(a is None for a in unhs__voq):
        return ArrayAnalysis.AnalyzeResult(shape=gfs__yrvmz[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, gfs__yrvmz))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, unhs__voq,
        vhgw__qavv)


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
    xtlpm__def = code_obj.code
    lccyz__ston = len(xtlpm__def.co_freevars)
    owaui__lechf = xtlpm__def.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        rnxp__lwsg, op = ir_utils.find_build_sequence(caller_ir, code_obj.
            closure)
        assert op == 'build_tuple'
        owaui__lechf = [gdkp__ntx.name for gdkp__ntx in rnxp__lwsg]
    rtup__hfjbz = caller_ir.func_id.func.__globals__
    try:
        rtup__hfjbz = getattr(code_obj, 'globals', rtup__hfjbz)
    except KeyError as som__qorbe:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    ajrms__yuv = []
    for x in owaui__lechf:
        try:
            pns__thwtq = caller_ir.get_definition(x)
        except KeyError as som__qorbe:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(pns__thwtq, (ir.Const, ir.Global, ir.FreeVar)):
            val = pns__thwtq.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                mwjf__mumdk = ir_utils.mk_unique_var('nested_func').replace('.'
                    , '_')
                rtup__hfjbz[mwjf__mumdk] = bodo.jit(distributed=False)(val)
                rtup__hfjbz[mwjf__mumdk].is_nested_func = True
                val = mwjf__mumdk
            if isinstance(val, CPUDispatcher):
                mwjf__mumdk = ir_utils.mk_unique_var('nested_func').replace('.'
                    , '_')
                rtup__hfjbz[mwjf__mumdk] = val
                val = mwjf__mumdk
            ajrms__yuv.append(val)
        elif isinstance(pns__thwtq, ir.Expr
            ) and pns__thwtq.op == 'make_function':
            nfqf__nkvid = convert_code_obj_to_function(pns__thwtq, caller_ir)
            mwjf__mumdk = ir_utils.mk_unique_var('nested_func').replace('.',
                '_')
            rtup__hfjbz[mwjf__mumdk] = bodo.jit(distributed=False)(nfqf__nkvid)
            rtup__hfjbz[mwjf__mumdk].is_nested_func = True
            ajrms__yuv.append(mwjf__mumdk)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    pgdl__vtr = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in enumerate(
        ajrms__yuv)])
    uib__xsazd = ','.join([('c_%d' % i) for i in range(lccyz__ston)])
    fwxhy__qkkf = list(xtlpm__def.co_varnames)
    nto__aig = 0
    gibz__szl = xtlpm__def.co_argcount
    hjs__ikeok = caller_ir.get_definition(code_obj.defaults)
    if hjs__ikeok is not None:
        if isinstance(hjs__ikeok, tuple):
            eqj__djaol = [caller_ir.get_definition(x).value for x in hjs__ikeok
                ]
            hpnq__reni = tuple(eqj__djaol)
        else:
            eqj__djaol = [caller_ir.get_definition(x).value for x in
                hjs__ikeok.items]
            hpnq__reni = tuple(eqj__djaol)
        nto__aig = len(hpnq__reni)
    ptrsp__pjuy = gibz__szl - nto__aig
    oawa__unlgl = ','.join([('%s' % fwxhy__qkkf[i]) for i in range(
        ptrsp__pjuy)])
    if nto__aig:
        tofm__rang = [('%s = %s' % (fwxhy__qkkf[i + ptrsp__pjuy],
            hpnq__reni[i])) for i in range(nto__aig)]
        oawa__unlgl += ', '
        oawa__unlgl += ', '.join(tofm__rang)
    return _create_function_from_code_obj(xtlpm__def, pgdl__vtr,
        oawa__unlgl, uib__xsazd, rtup__hfjbz)


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
    for ajss__orcg, (pufxs__sgaci, ysqjy__mmuot) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % ysqjy__mmuot)
            zzibh__xcx = _pass_registry.get(pufxs__sgaci).pass_inst
            if isinstance(zzibh__xcx, CompilerPass):
                self._runPass(ajss__orcg, zzibh__xcx, state)
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
                    pipeline_name, ysqjy__mmuot)
                wpx__ucx = self._patch_error(msg, e)
                raise wpx__ucx
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
    wpcyr__rjcj = None
    lhc__jok = {}

    def lookup(var, already_seen, varonly=True):
        val = lhc__jok.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    cqo__dzzb = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        hun__bzhso = stmt.target
        kqpp__sexcj = stmt.value
        lhc__jok[hun__bzhso.name] = kqpp__sexcj
        if isinstance(kqpp__sexcj, ir.Var) and kqpp__sexcj.name in lhc__jok:
            kqpp__sexcj = lookup(kqpp__sexcj, set())
        if isinstance(kqpp__sexcj, ir.Expr):
            fih__jcvpu = set(lookup(gdkp__ntx, set(), True).name for
                gdkp__ntx in kqpp__sexcj.list_vars())
            if name in fih__jcvpu:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(kqpp__sexcj)]
                lnsj__smtz = [x for x, rhsf__sns in args if rhsf__sns.name !=
                    name]
                args = [(x, rhsf__sns) for x, rhsf__sns in args if x !=
                    rhsf__sns.name]
                gfzgi__jofif = dict(args)
                if len(lnsj__smtz) == 1:
                    gfzgi__jofif[lnsj__smtz[0]] = ir.Var(hun__bzhso.scope, 
                        name + '#init', hun__bzhso.loc)
                replace_vars_inner(kqpp__sexcj, gfzgi__jofif)
                wpcyr__rjcj = nodes[i:]
                break
    return wpcyr__rjcj


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
        lcu__quxxe = expand_aliases({gdkp__ntx.name for gdkp__ntx in stmt.
            list_vars()}, alias_map, arg_aliases)
        mhlr__zqci = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        lcecd__skcjs = expand_aliases({gdkp__ntx.name for gdkp__ntx in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        vfpqw__qqz = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(mhlr__zqci & lcecd__skcjs | vfpqw__qqz & lcu__quxxe) == 0:
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
    zqxzk__cakme = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            zqxzk__cakme.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                zqxzk__cakme.update(get_parfor_writes(stmt, func_ir))
    return zqxzk__cakme


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    zqxzk__cakme = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        zqxzk__cakme.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        zqxzk__cakme = {gdkp__ntx.name for gdkp__ntx in stmt.df_out_vars.
            values()}
        if stmt.out_key_vars is not None:
            zqxzk__cakme.update({gdkp__ntx.name for gdkp__ntx in stmt.
                out_key_vars})
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        zqxzk__cakme = {gdkp__ntx.name for gdkp__ntx in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        zqxzk__cakme = {gdkp__ntx.name for gdkp__ntx in stmt.out_data_vars.
            values()}
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            zqxzk__cakme.update({gdkp__ntx.name for gdkp__ntx in stmt.
                out_key_arrs})
            zqxzk__cakme.update({gdkp__ntx.name for gdkp__ntx in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        jaa__fprt = guard(find_callname, func_ir, stmt.value)
        if jaa__fprt in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'),
            ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            zqxzk__cakme.add(stmt.value.args[0].name)
    return zqxzk__cakme


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
        tyko__wifvd = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        npb__ntpr = tyko__wifvd.format(self, msg)
        self.args = npb__ntpr,
    else:
        tyko__wifvd = _termcolor.errmsg('{0}')
        npb__ntpr = tyko__wifvd.format(self)
        self.args = npb__ntpr,
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
        for xioep__ienu in options['distributed']:
            dist_spec[xioep__ienu] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for xioep__ienu in options['distributed_block']:
            dist_spec[xioep__ienu] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    xqh__qlnjb = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, foj__rivg in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(foj__rivg)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    elqv__bre = {}
    for osqa__gfgso in reversed(inspect.getmro(cls)):
        elqv__bre.update(osqa__gfgso.__dict__)
    hyde__seatb, skv__neczj, tfo__rqc, xuxfl__bqrt = {}, {}, {}, {}
    for ptgms__gtcb, gdkp__ntx in elqv__bre.items():
        if isinstance(gdkp__ntx, pytypes.FunctionType):
            hyde__seatb[ptgms__gtcb] = gdkp__ntx
        elif isinstance(gdkp__ntx, property):
            skv__neczj[ptgms__gtcb] = gdkp__ntx
        elif isinstance(gdkp__ntx, staticmethod):
            tfo__rqc[ptgms__gtcb] = gdkp__ntx
        else:
            xuxfl__bqrt[ptgms__gtcb] = gdkp__ntx
    vgm__irqkd = (set(hyde__seatb) | set(skv__neczj) | set(tfo__rqc)) & set(
        spec)
    if vgm__irqkd:
        raise NameError('name shadowing: {0}'.format(', '.join(vgm__irqkd)))
    mtj__uzchk = xuxfl__bqrt.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(xuxfl__bqrt)
    if xuxfl__bqrt:
        msg = 'class members are not yet supported: {0}'
        zxap__fgyew = ', '.join(xuxfl__bqrt.keys())
        raise TypeError(msg.format(zxap__fgyew))
    for ptgms__gtcb, gdkp__ntx in skv__neczj.items():
        if gdkp__ntx.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(ptgms__gtcb)
                )
    jit_methods = {ptgms__gtcb: bodo.jit(returns_maybe_distributed=
        xqh__qlnjb)(gdkp__ntx) for ptgms__gtcb, gdkp__ntx in hyde__seatb.
        items()}
    jit_props = {}
    for ptgms__gtcb, gdkp__ntx in skv__neczj.items():
        ocmm__wmu = {}
        if gdkp__ntx.fget:
            ocmm__wmu['get'] = bodo.jit(gdkp__ntx.fget)
        if gdkp__ntx.fset:
            ocmm__wmu['set'] = bodo.jit(gdkp__ntx.fset)
        jit_props[ptgms__gtcb] = ocmm__wmu
    jit_static_methods = {ptgms__gtcb: bodo.jit(gdkp__ntx.__func__) for 
        ptgms__gtcb, gdkp__ntx in tfo__rqc.items()}
    qcwo__gzjz = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    mywyu__qicv = dict(class_type=qcwo__gzjz, __doc__=mtj__uzchk)
    mywyu__qicv.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), mywyu__qicv)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, qcwo__gzjz)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(qcwo__gzjz, typingctx, targetctx).register()
    as_numba_type.register(cls, qcwo__gzjz.instance_type)
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
    meaw__gax = ','.join('{0}:{1}'.format(ptgms__gtcb, gdkp__ntx) for 
        ptgms__gtcb, gdkp__ntx in struct.items())
    jap__xadd = ','.join('{0}:{1}'.format(ptgms__gtcb, gdkp__ntx) for 
        ptgms__gtcb, gdkp__ntx in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), meaw__gax, jap__xadd)
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
    zff__hrwvl = numba.core.typeinfer.fold_arg_vars(typevars, self.args,
        self.vararg, self.kws)
    if zff__hrwvl is None:
        return
    kvkwb__ttirf, tip__nkhjf = zff__hrwvl
    for a in itertools.chain(kvkwb__ttirf, tip__nkhjf.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, kvkwb__ttirf, tip__nkhjf)
    except ForceLiteralArg as e:
        cvc__lci = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(cvc__lci, self.kws)
        abck__qpi = set()
        mtvx__txegn = set()
        rawyz__xgvf = {}
        for ajss__orcg in e.requested_args:
            feqfr__xlobo = typeinfer.func_ir.get_definition(folded[ajss__orcg])
            if isinstance(feqfr__xlobo, ir.Arg):
                abck__qpi.add(feqfr__xlobo.index)
                if feqfr__xlobo.index in e.file_infos:
                    rawyz__xgvf[feqfr__xlobo.index] = e.file_infos[feqfr__xlobo
                        .index]
            else:
                mtvx__txegn.add(ajss__orcg)
        if mtvx__txegn:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif abck__qpi:
            raise ForceLiteralArg(abck__qpi, loc=self.loc, file_infos=
                rawyz__xgvf)
    if sig is None:
        ifnl__kowto = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in kvkwb__ttirf]
        args += [('%s=%s' % (ptgms__gtcb, gdkp__ntx)) for ptgms__gtcb,
            gdkp__ntx in sorted(tip__nkhjf.items())]
        mfv__eex = ifnl__kowto.format(fnty, ', '.join(map(str, args)))
        olku__oio = context.explain_function_type(fnty)
        msg = '\n'.join([mfv__eex, olku__oio])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        vjgl__cdt = context.unify_pairs(sig.recvr, fnty.this)
        if vjgl__cdt is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if vjgl__cdt is not None and vjgl__cdt.is_precise():
            duyjl__ukhx = fnty.copy(this=vjgl__cdt)
            typeinfer.propagate_refined_type(self.func, duyjl__ukhx)
    if not sig.return_type.is_precise():
        jalle__rrkk = typevars[self.target]
        if jalle__rrkk.defined:
            olyc__dpd = jalle__rrkk.getone()
            if context.unify_pairs(olyc__dpd, sig.return_type) == olyc__dpd:
                sig = sig.replace(return_type=olyc__dpd)
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
        scoi__oggzy = '*other* must be a {} but got a {} instead'
        raise TypeError(scoi__oggzy.format(ForceLiteralArg, type(other)))
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
    lzjci__ipe = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for ptgms__gtcb, gdkp__ntx in kwargs.items():
        nmtk__rdfyb = None
        try:
            tvx__vsa = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var(
                'dummy'), loc)
            func_ir._definitions[tvx__vsa.name] = [gdkp__ntx]
            nmtk__rdfyb = get_const_value_inner(func_ir, tvx__vsa)
            func_ir._definitions.pop(tvx__vsa.name)
            if isinstance(nmtk__rdfyb, str):
                nmtk__rdfyb = sigutils._parse_signature_string(nmtk__rdfyb)
            if isinstance(nmtk__rdfyb, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {ptgms__gtcb} is annotated as type class {nmtk__rdfyb}."""
                    )
            assert isinstance(nmtk__rdfyb, types.Type)
            if isinstance(nmtk__rdfyb, (types.List, types.Set)):
                nmtk__rdfyb = nmtk__rdfyb.copy(reflected=False)
            lzjci__ipe[ptgms__gtcb] = nmtk__rdfyb
        except BodoError as som__qorbe:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(nmtk__rdfyb, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(gdkp__ntx, ir.Global):
                    msg = f'Global {gdkp__ntx.name!r} is not defined.'
                if isinstance(gdkp__ntx, ir.FreeVar):
                    msg = f'Freevar {gdkp__ntx.name!r} is not defined.'
            if isinstance(gdkp__ntx, ir.Expr) and gdkp__ntx.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=ptgms__gtcb, msg=msg, loc=loc)
    for name, typ in lzjci__ipe.items():
        self._legalize_arg_type(name, typ, loc)
    return lzjci__ipe


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
    xobdb__krmg = inst.arg
    assert xobdb__krmg > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(xobdb__krmg)]))
    tmps = [state.make_temp() for _ in range(xobdb__krmg - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    tooof__rpjnw = ir.Global('format', format, loc=self.loc)
    self.store(value=tooof__rpjnw, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    vpx__cstz = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=vpx__cstz, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    xobdb__krmg = inst.arg
    assert xobdb__krmg > 0, 'invalid BUILD_STRING count'
    jgu__ekejs = self.get(strings[0])
    for other, wje__zcaid in zip(strings[1:], tmps):
        other = self.get(other)
        aykg__apuel = ir.Expr.binop(operator.add, lhs=jgu__ekejs, rhs=other,
            loc=self.loc)
        self.store(aykg__apuel, wje__zcaid)
        jgu__ekejs = self.get(wje__zcaid)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    tzsp__bafp = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, tzsp__bafp])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    ynzeu__luid = mk_unique_var(f'{var_name}')
    jds__kjdc = ynzeu__luid.replace('<', '_').replace('>', '_')
    jds__kjdc = jds__kjdc.replace('.', '_').replace('$', '_v')
    return jds__kjdc


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
                rnrui__bnp = get_overload_const_str(val2)
                if rnrui__bnp != 'ns':
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
        nln__kpr = states['defmap']
        if len(nln__kpr) == 0:
            rclsy__htpox = assign.target
            numba.core.ssa._logger.debug('first assign: %s', rclsy__htpox)
            if rclsy__htpox.name not in scope.localvars:
                rclsy__htpox = scope.define(assign.target.name, loc=assign.loc)
        else:
            rclsy__htpox = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=rclsy__htpox, value=assign.value, loc=
            assign.loc)
        nln__kpr[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    khok__can = []
    for ptgms__gtcb, gdkp__ntx in typing.npydecl.registry.globals:
        if ptgms__gtcb == func:
            khok__can.append(gdkp__ntx)
    for ptgms__gtcb, gdkp__ntx in typing.templates.builtin_registry.globals:
        if ptgms__gtcb == func:
            khok__can.append(gdkp__ntx)
    if len(khok__can) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return khok__can


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    cqla__jmwo = {}
    tthss__mlpz = find_topo_order(blocks)
    gewy__onec = {}
    for tktvw__wflam in tthss__mlpz:
        block = blocks[tktvw__wflam]
        fbrpy__pjo = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                hun__bzhso = stmt.target.name
                kqpp__sexcj = stmt.value
                if (kqpp__sexcj.op == 'getattr' and kqpp__sexcj.attr in
                    arr_math and isinstance(typemap[kqpp__sexcj.value.name],
                    types.npytypes.Array)):
                    kqpp__sexcj = stmt.value
                    rxoi__adgua = kqpp__sexcj.value
                    cqla__jmwo[hun__bzhso] = rxoi__adgua
                    scope = rxoi__adgua.scope
                    loc = rxoi__adgua.loc
                    htt__bjg = ir.Var(scope, mk_unique_var('$np_g_var'), loc)
                    typemap[htt__bjg.name] = types.misc.Module(numpy)
                    gcgh__zbhy = ir.Global('np', numpy, loc)
                    koq__vxy = ir.Assign(gcgh__zbhy, htt__bjg, loc)
                    kqpp__sexcj.value = htt__bjg
                    fbrpy__pjo.append(koq__vxy)
                    func_ir._definitions[htt__bjg.name] = [gcgh__zbhy]
                    func = getattr(numpy, kqpp__sexcj.attr)
                    kne__njb = get_np_ufunc_typ_lst(func)
                    gewy__onec[hun__bzhso] = kne__njb
                if (kqpp__sexcj.op == 'call' and kqpp__sexcj.func.name in
                    cqla__jmwo):
                    rxoi__adgua = cqla__jmwo[kqpp__sexcj.func.name]
                    pttjw__ovlx = calltypes.pop(kqpp__sexcj)
                    eitvs__xrt = pttjw__ovlx.args[:len(kqpp__sexcj.args)]
                    hkpel__rgpu = {name: typemap[gdkp__ntx.name] for name,
                        gdkp__ntx in kqpp__sexcj.kws}
                    yfzy__ghnz = gewy__onec[kqpp__sexcj.func.name]
                    rzzn__svd = None
                    for geor__xfrj in yfzy__ghnz:
                        try:
                            rzzn__svd = geor__xfrj.get_call_type(typingctx,
                                [typemap[rxoi__adgua.name]] + list(
                                eitvs__xrt), hkpel__rgpu)
                            typemap.pop(kqpp__sexcj.func.name)
                            typemap[kqpp__sexcj.func.name] = geor__xfrj
                            calltypes[kqpp__sexcj] = rzzn__svd
                            break
                        except Exception as som__qorbe:
                            pass
                    if rzzn__svd is None:
                        raise TypeError(
                            f'No valid template found for {kqpp__sexcj.func.name}'
                            )
                    kqpp__sexcj.args = [rxoi__adgua] + kqpp__sexcj.args
            fbrpy__pjo.append(stmt)
        block.body = fbrpy__pjo


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    kvyjg__zxyab = ufunc.nin
    wnfvg__huibr = ufunc.nout
    ptrsp__pjuy = ufunc.nargs
    assert ptrsp__pjuy == kvyjg__zxyab + wnfvg__huibr
    if len(args) < kvyjg__zxyab:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args),
            kvyjg__zxyab))
    if len(args) > ptrsp__pjuy:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args),
            ptrsp__pjuy))
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    pvnv__udm = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    braz__clnt = max(pvnv__udm)
    sfo__gipv = args[kvyjg__zxyab:]
    if not all(eqj__djaol == braz__clnt for eqj__djaol in pvnv__udm[
        kvyjg__zxyab:]):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(uccm__mzrg, types.ArrayCompatible) and not
        isinstance(uccm__mzrg, types.Bytes) for uccm__mzrg in sfo__gipv):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(uccm__mzrg.mutable for uccm__mzrg in sfo__gipv):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    treqe__klfyu = [(x.dtype if isinstance(x, types.ArrayCompatible) and 
        not isinstance(x, types.Bytes) else x) for x in args]
    cdph__vvefk = None
    if braz__clnt > 0 and len(sfo__gipv) < ufunc.nout:
        cdph__vvefk = 'C'
        zkj__fmtqh = [(x.layout if isinstance(x, types.ArrayCompatible) and
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in zkj__fmtqh and 'F' in zkj__fmtqh:
            cdph__vvefk = 'F'
    return treqe__klfyu, sfo__gipv, braz__clnt, cdph__vvefk


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
        zksrh__sgr = 'Dict.key_type cannot be of type {}'
        raise TypingError(zksrh__sgr.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        zksrh__sgr = 'Dict.value_type cannot be of type {}'
        raise TypingError(zksrh__sgr.format(valty))
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
    rbx__qrk = self.context, tuple(args), tuple(kws.items())
    try:
        jdnpt__wozs, args = self._impl_cache[rbx__qrk]
        return jdnpt__wozs, args
    except KeyError as som__qorbe:
        pass
    jdnpt__wozs, args = self._build_impl(rbx__qrk, args, kws)
    return jdnpt__wozs, args


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
        ydg__kmahz = find_topo_order(parfor.loop_body)
    xps__qpcym = ydg__kmahz[0]
    sryae__lxhfx = {}
    _update_parfor_get_setitems(parfor.loop_body[xps__qpcym].body, parfor.
        index_var, alias_map, sryae__lxhfx, lives_n_aliases)
    wbx__lobh = set(sryae__lxhfx.keys())
    for wnkh__secm in ydg__kmahz:
        if wnkh__secm == xps__qpcym:
            continue
        for stmt in parfor.loop_body[wnkh__secm].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            kymb__thj = set(gdkp__ntx.name for gdkp__ntx in stmt.list_vars())
            lfss__tqbec = kymb__thj & wbx__lobh
            for a in lfss__tqbec:
                sryae__lxhfx.pop(a, None)
    for wnkh__secm in ydg__kmahz:
        if wnkh__secm == xps__qpcym:
            continue
        block = parfor.loop_body[wnkh__secm]
        kvxtn__wvy = sryae__lxhfx.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            kvxtn__wvy, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    upj__oaou = max(blocks.keys())
    lfkni__hhrc, dfwt__yswdt = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    svrlw__oot = ir.Jump(lfkni__hhrc, ir.Loc('parfors_dummy', -1))
    blocks[upj__oaou].body.append(svrlw__oot)
    lxsn__gmaw = compute_cfg_from_blocks(blocks)
    bsx__bbq = compute_use_defs(blocks)
    hej__yvvaw = compute_live_map(lxsn__gmaw, blocks, bsx__bbq.usemap,
        bsx__bbq.defmap)
    alias_set = set(alias_map.keys())
    for tktvw__wflam, block in blocks.items():
        fbrpy__pjo = []
        idk__fdua = {gdkp__ntx.name for gdkp__ntx in block.terminator.
            list_vars()}
        for dxa__sac, skunf__cdbzt in lxsn__gmaw.successors(tktvw__wflam):
            idk__fdua |= hej__yvvaw[dxa__sac]
        for stmt in reversed(block.body):
            vnrvj__zltl = idk__fdua & alias_set
            for gdkp__ntx in vnrvj__zltl:
                idk__fdua |= alias_map[gdkp__ntx]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in idk__fdua and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                jaa__fprt = guard(find_callname, func_ir, stmt.value)
                if jaa__fprt == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in idk__fdua and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            idk__fdua |= {gdkp__ntx.name for gdkp__ntx in stmt.list_vars()}
            fbrpy__pjo.append(stmt)
        fbrpy__pjo.reverse()
        block.body = fbrpy__pjo
    typemap.pop(dfwt__yswdt.name)
    blocks[upj__oaou].body.pop()

    def trim_empty_parfor_branches(parfor):
        oeh__axy = False
        blocks = parfor.loop_body.copy()
        for tktvw__wflam, block in blocks.items():
            if len(block.body):
                eyiwc__zbvx = block.body[-1]
                if isinstance(eyiwc__zbvx, ir.Branch):
                    if len(blocks[eyiwc__zbvx.truebr].body) == 1 and len(blocks
                        [eyiwc__zbvx.falsebr].body) == 1:
                        nlnl__fdhxi = blocks[eyiwc__zbvx.truebr].body[0]
                        byv__rnhgq = blocks[eyiwc__zbvx.falsebr].body[0]
                        if isinstance(nlnl__fdhxi, ir.Jump) and isinstance(
                            byv__rnhgq, ir.Jump
                            ) and nlnl__fdhxi.target == byv__rnhgq.target:
                            parfor.loop_body[tktvw__wflam].body[-1] = ir.Jump(
                                nlnl__fdhxi.target, eyiwc__zbvx.loc)
                            oeh__axy = True
                    elif len(blocks[eyiwc__zbvx.truebr].body) == 1:
                        nlnl__fdhxi = blocks[eyiwc__zbvx.truebr].body[0]
                        if isinstance(nlnl__fdhxi, ir.Jump
                            ) and nlnl__fdhxi.target == eyiwc__zbvx.falsebr:
                            parfor.loop_body[tktvw__wflam].body[-1] = ir.Jump(
                                nlnl__fdhxi.target, eyiwc__zbvx.loc)
                            oeh__axy = True
                    elif len(blocks[eyiwc__zbvx.falsebr].body) == 1:
                        byv__rnhgq = blocks[eyiwc__zbvx.falsebr].body[0]
                        if isinstance(byv__rnhgq, ir.Jump
                            ) and byv__rnhgq.target == eyiwc__zbvx.truebr:
                            parfor.loop_body[tktvw__wflam].body[-1] = ir.Jump(
                                byv__rnhgq.target, eyiwc__zbvx.loc)
                            oeh__axy = True
        return oeh__axy
    oeh__axy = True
    while oeh__axy:
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
        oeh__axy = trim_empty_parfor_branches(parfor)
    kec__xfba = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        kec__xfba &= len(block.body) == 0
    if kec__xfba:
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
    dirh__xeq = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                dirh__xeq += 1
                parfor = stmt
                nwn__jpug = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = nwn__jpug.scope
                loc = ir.Loc('parfors_dummy', -1)
                xntkv__mvkb = ir.Var(scope, mk_unique_var('$const'), loc)
                nwn__jpug.body.append(ir.Assign(ir.Const(0, loc),
                    xntkv__mvkb, loc))
                nwn__jpug.body.append(ir.Return(xntkv__mvkb, loc))
                lxsn__gmaw = compute_cfg_from_blocks(parfor.loop_body)
                for mrvuf__adw in lxsn__gmaw.dead_nodes():
                    del parfor.loop_body[mrvuf__adw]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                nwn__jpug = parfor.loop_body[max(parfor.loop_body.keys())]
                nwn__jpug.body.pop()
                nwn__jpug.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return dirh__xeq


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
            eacy__kdffi = self.overloads.get(tuple(args))
            if eacy__kdffi is not None:
                return eacy__kdffi.entry_point
            self._pre_compile(args, return_type, flags)
            yuuk__bma = self.func_ir
            mimfw__pbjvl = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=mimfw__pbjvl):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=yuuk__bma, args=args,
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
        facx__igydm = copy.deepcopy(flags)
        facx__igydm.no_rewrites = True

        def compile_local(the_ir, the_flags):
            ceurb__aau = pipeline_class(typingctx, targetctx, library, args,
                return_type, the_flags, locals)
            return ceurb__aau.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        xaggp__yggq = compile_local(func_ir, facx__igydm)
        wtek__apmk = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    wtek__apmk = compile_local(func_ir, flags)
                except Exception as som__qorbe:
                    pass
        if wtek__apmk is not None:
            cres = wtek__apmk
        else:
            cres = xaggp__yggq
        return cres
    else:
        ceurb__aau = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return ceurb__aau.compile_ir(func_ir=func_ir, lifted=lifted,
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
    zvs__qzmmn = self.get_data_type(typ.dtype)
    tube__omzkt = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        tube__omzkt):
        gwc__cjrd = ary.ctypes.data
        acu__kfbeu = self.add_dynamic_addr(builder, gwc__cjrd, info=str(
            type(gwc__cjrd)))
        ooze__guzri = self.add_dynamic_addr(builder, id(ary), info=str(type
            (ary)))
        self.global_arrays.append(ary)
    else:
        bjx__tmdyf = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            bjx__tmdyf = bjx__tmdyf.view('int64')
        rmhh__blre = Constant.array(Type.int(8), bytearray(bjx__tmdyf.data))
        acu__kfbeu = cgutils.global_constant(builder, '.const.array.data',
            rmhh__blre)
        acu__kfbeu.align = self.get_abi_alignment(zvs__qzmmn)
        ooze__guzri = None
    dqma__pizc = self.get_value_type(types.intp)
    ffzvs__ukf = [self.get_constant(types.intp, owu__bruxq) for owu__bruxq in
        ary.shape]
    jvxl__zxmj = Constant.array(dqma__pizc, ffzvs__ukf)
    sye__idhj = [self.get_constant(types.intp, owu__bruxq) for owu__bruxq in
        ary.strides]
    etkm__ynqa = Constant.array(dqma__pizc, sye__idhj)
    xaso__hplh = self.get_constant(types.intp, ary.dtype.itemsize)
    swa__sgjnl = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        swa__sgjnl, xaso__hplh, acu__kfbeu.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), jvxl__zxmj, etkm__ynqa])


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
    pquvr__xxv = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    vgr__xghl = lir.Function(module, pquvr__xxv, name='nrt_atomic_{0}'.
        format(op))
    [csugi__jarsq] = vgr__xghl.args
    kjlyi__tjnbz = vgr__xghl.append_basic_block()
    builder = lir.IRBuilder(kjlyi__tjnbz)
    mqk__prpl = lir.Constant(_word_type, 1)
    if False:
        loins__tub = builder.atomic_rmw(op, csugi__jarsq, mqk__prpl,
            ordering=ordering)
        res = getattr(builder, op)(loins__tub, mqk__prpl)
        builder.ret(res)
    else:
        loins__tub = builder.load(csugi__jarsq)
        klgpa__niqu = getattr(builder, op)(loins__tub, mqk__prpl)
        bxc__qhlh = builder.icmp_signed('!=', loins__tub, lir.Constant(
            loins__tub.type, -1))
        with cgutils.if_likely(builder, bxc__qhlh):
            builder.store(klgpa__niqu, csugi__jarsq)
        builder.ret(klgpa__niqu)
    return vgr__xghl


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
        wdcwn__jfp = state.targetctx.codegen()
        state.library = wdcwn__jfp.create_library(state.func_id.func_qualname)
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    tws__xmbci = state.func_ir
    typemap = state.typemap
    gsm__dykor = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    dvprc__yxuj = state.metadata
    wktr__wyo = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        kdms__jgs = (funcdesc.PythonFunctionDescriptor.
            from_specialized_function(tws__xmbci, typemap, gsm__dykor,
            calltypes, mangler=targetctx.mangler, inline=flags.forceinline,
            noalias=flags.noalias, abi_tags=[flags.get_mangle_string()]))
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            gsggk__uqqxt = lowering.Lower(targetctx, library, kdms__jgs,
                tws__xmbci, metadata=dvprc__yxuj)
            gsggk__uqqxt.lower()
            if not flags.no_cpython_wrapper:
                gsggk__uqqxt.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(gsm__dykor, (types.Optional, types.Generator)
                        ):
                        pass
                    else:
                        gsggk__uqqxt.create_cfunc_wrapper()
            mgof__sfgg = gsggk__uqqxt.env
            bnggr__zauz = gsggk__uqqxt.call_helper
            del gsggk__uqqxt
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(kdms__jgs, bnggr__zauz, cfunc=None,
                env=mgof__sfgg)
        else:
            pdq__gapk = targetctx.get_executable(library, kdms__jgs, mgof__sfgg
                )
            targetctx.insert_user_function(pdq__gapk, kdms__jgs, [library])
            state['cr'] = _LowerResult(kdms__jgs, bnggr__zauz, cfunc=
                pdq__gapk, env=mgof__sfgg)
        dvprc__yxuj['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        cnxt__aiv = llvm.passmanagers.dump_refprune_stats()
        dvprc__yxuj['prune_stats'] = cnxt__aiv - wktr__wyo
        dvprc__yxuj['llvm_pass_timings'] = library.recorded_timings
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
        tswx__uhpr = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, tswx__uhpr),
            likely=False):
            c.builder.store(cgutils.true_bit, errorptr)
            yupc__kadff.do_break()
        pizbc__mra = c.builder.icmp_signed('!=', tswx__uhpr, expected_typobj)
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(pizbc__mra, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, tswx__uhpr)
                c.pyapi.decref(tswx__uhpr)
                yupc__kadff.do_break()
        c.pyapi.decref(tswx__uhpr)
    wcwi__bfxr, list = listobj.ListInstance.allocate_ex(c.context, c.
        builder, typ, size)
    with c.builder.if_else(wcwi__bfxr, likely=True) as (gmz__syv, eho__bwdvb):
        with gmz__syv:
            list.size = size
            ptvzr__hentl = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                ptvzr__hentl), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        ptvzr__hentl))
                    with cgutils.for_range(c.builder, size) as yupc__kadff:
                        itemobj = c.pyapi.list_getitem(obj, yupc__kadff.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        mlj__rnrpa = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(mlj__rnrpa.is_error, likely=
                            False):
                            c.builder.store(cgutils.true_bit, errorptr)
                            yupc__kadff.do_break()
                        list.setitem(yupc__kadff.index, mlj__rnrpa.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with eho__bwdvb:
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
    vhmx__gkrtf, kaqjo__fubco, veqk__ygnfj, huehk__hszq, ryrp__huntr = (
        compile_time_get_string_data(literal_string))
    uax__zkb = builder.module
    gv = context.insert_const_bytes(uax__zkb, vhmx__gkrtf)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        kaqjo__fubco), context.get_constant(types.int32, veqk__ygnfj),
        context.get_constant(types.uint32, huehk__hszq), context.
        get_constant(_Py_hash_t, -1), context.get_constant_null(types.
        MemInfoPointer(types.voidptr)), context.get_constant_null(types.
        pyobject)])


if _check_numba_change:
    lines = inspect.getsource(numba.cpython.unicode.make_string_from_constant)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '525bd507383e06152763e2f046dae246cd60aba027184f50ef0fc9a80d4cd7fa':
        warnings.warn(
            'numba.cpython.unicode.make_string_from_constant has changed')
numba.cpython.unicode.make_string_from_constant = make_string_from_constant


def parse_shape(shape):
    aqctb__pot = None
    if isinstance(shape, types.Integer):
        aqctb__pot = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(owu__bruxq, (types.Integer, types.IntEnumMember)) for
            owu__bruxq in shape):
            aqctb__pot = len(shape)
    return aqctb__pot


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
            aqctb__pot = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if aqctb__pot == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(aqctb__pot)
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
            vhgw__qavv = self._get_names(x)
            if len(vhgw__qavv) != 0:
                return vhgw__qavv[0]
            return vhgw__qavv
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    vhgw__qavv = self._get_names(obj)
    if len(vhgw__qavv) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(vhgw__qavv[0])


def get_equiv_set(self, obj):
    vhgw__qavv = self._get_names(obj)
    if len(vhgw__qavv) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(vhgw__qavv[0])


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
    eiix__ugzl = []
    for byf__kpmm in func_ir.arg_names:
        if byf__kpmm in typemap and isinstance(typemap[byf__kpmm], types.
            containers.UniTuple) and typemap[byf__kpmm].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(byf__kpmm))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for lzavx__bulwo in func_ir.blocks.values():
        for stmt in lzavx__bulwo.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    bfah__bab = getattr(val, 'code', None)
                    if bfah__bab is not None:
                        if getattr(val, 'closure', None) is not None:
                            dmic__hpmso = (
                                '<creating a function from a closure>')
                            aykg__apuel = ''
                        else:
                            dmic__hpmso = bfah__bab.co_name
                            aykg__apuel = '(%s) ' % dmic__hpmso
                    else:
                        dmic__hpmso = '<could not ascertain use case>'
                        aykg__apuel = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (dmic__hpmso, aykg__apuel))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                sltss__mxhei = False
                if isinstance(val, pytypes.FunctionType):
                    sltss__mxhei = val in {numba.gdb, numba.gdb_init}
                if not sltss__mxhei:
                    sltss__mxhei = getattr(val, '_name', '') == 'gdb_internal'
                if sltss__mxhei:
                    eiix__ugzl.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    xwzz__won = func_ir.get_definition(var)
                    kub__qjom = guard(find_callname, func_ir, xwzz__won)
                    if kub__qjom and kub__qjom[1] == 'numpy':
                        ty = getattr(numpy, kub__qjom[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    hlke__zrs = '' if var.startswith('$') else "'{}' ".format(
                        var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(hlke__zrs), loc=stmt.loc)
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
    if len(eiix__ugzl) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        uns__nmdo = '\n'.join([x.strformat() for x in eiix__ugzl])
        raise errors.UnsupportedError(msg % uns__nmdo)


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
    ptgms__gtcb, gdkp__ntx = next(iter(val.items()))
    nuvuz__rbm = typeof_impl(ptgms__gtcb, c)
    kfri__jpems = typeof_impl(gdkp__ntx, c)
    if nuvuz__rbm is None or kfri__jpems is None:
        raise ValueError(
            f'Cannot type dict element type {type(ptgms__gtcb)}, {type(gdkp__ntx)}'
            )
    return types.DictType(nuvuz__rbm, kfri__jpems)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    fqo__qypnp = cgutils.alloca_once_value(c.builder, val)
    uejmy__brnou = c.pyapi.object_hasattr_string(val, '_opaque')
    rlttz__dljl = c.builder.icmp_unsigned('==', uejmy__brnou, lir.Constant(
        uejmy__brnou.type, 0))
    ojzrr__tcq = typ.key_type
    uoqye__kwwa = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(ojzrr__tcq, uoqye__kwwa)

    def copy_dict(out_dict, in_dict):
        for ptgms__gtcb, gdkp__ntx in in_dict.items():
            out_dict[ptgms__gtcb] = gdkp__ntx
    with c.builder.if_then(rlttz__dljl):
        lsvkz__tazgj = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        pyq__syvy = c.pyapi.call_function_objargs(lsvkz__tazgj, [])
        jtbdf__orvg = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(jtbdf__orvg, [pyq__syvy, val])
        c.builder.store(pyq__syvy, fqo__qypnp)
    val = c.builder.load(fqo__qypnp)
    bnjql__egcry = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    ozr__rkz = c.pyapi.object_type(val)
    myzkh__whim = c.builder.icmp_unsigned('==', ozr__rkz, bnjql__egcry)
    with c.builder.if_else(myzkh__whim) as (ubkh__awfe, xots__hfy):
        with ubkh__awfe:
            bzv__pmbnb = c.pyapi.object_getattr_string(val, '_opaque')
            zayvx__sen = types.MemInfoPointer(types.voidptr)
            mlj__rnrpa = c.unbox(zayvx__sen, bzv__pmbnb)
            mi = mlj__rnrpa.value
            yybr__osjg = zayvx__sen, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *yybr__osjg)
            efmr__gqv = context.get_constant_null(yybr__osjg[1])
            args = mi, efmr__gqv
            cxyz__vthj, vjr__sxq = c.pyapi.call_jit_code(convert, sig, args)
            c.context.nrt.decref(c.builder, typ, vjr__sxq)
            c.pyapi.decref(bzv__pmbnb)
            qazzr__xvp = c.builder.basic_block
        with xots__hfy:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", ozr__rkz, bnjql__egcry)
            vlkb__opf = c.builder.basic_block
    uzy__xqnko = c.builder.phi(vjr__sxq.type)
    xjgv__hjku = c.builder.phi(cxyz__vthj.type)
    uzy__xqnko.add_incoming(vjr__sxq, qazzr__xvp)
    uzy__xqnko.add_incoming(vjr__sxq.type(None), vlkb__opf)
    xjgv__hjku.add_incoming(cxyz__vthj, qazzr__xvp)
    xjgv__hjku.add_incoming(cgutils.true_bit, vlkb__opf)
    c.pyapi.decref(bnjql__egcry)
    c.pyapi.decref(ozr__rkz)
    with c.builder.if_then(rlttz__dljl):
        c.pyapi.decref(val)
    return NativeValue(uzy__xqnko, is_error=xjgv__hjku)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, zocu__vdv = args
    if isinstance(a, types.List) and isinstance(zocu__vdv, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(zocu__vdv, types.List):
        return signature(zocu__vdv, types.intp, zocu__vdv)


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
        epse__dyrv, dtt__qrx = 0, 1
    else:
        epse__dyrv, dtt__qrx = 1, 0
    paikb__cnq = ListInstance(context, builder, sig.args[epse__dyrv], args[
        epse__dyrv])
    iqh__kkvmh = paikb__cnq.size
    dlihl__gpc = args[dtt__qrx]
    ptvzr__hentl = lir.Constant(dlihl__gpc.type, 0)
    dlihl__gpc = builder.select(cgutils.is_neg_int(builder, dlihl__gpc),
        ptvzr__hentl, dlihl__gpc)
    swa__sgjnl = builder.mul(dlihl__gpc, iqh__kkvmh)
    wtba__fmbc = ListInstance.allocate(context, builder, sig.return_type,
        swa__sgjnl)
    wtba__fmbc.size = swa__sgjnl
    with cgutils.for_range_slice(builder, ptvzr__hentl, swa__sgjnl,
        iqh__kkvmh, inc=True) as (acibs__byjeo, _):
        with cgutils.for_range(builder, iqh__kkvmh) as yupc__kadff:
            value = paikb__cnq.getitem(yupc__kadff.index)
            wtba__fmbc.setitem(builder.add(yupc__kadff.index, acibs__byjeo),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, wtba__fmbc.value
        )


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    swa__sgjnl = payload.used
    listobj = c.pyapi.list_new(swa__sgjnl)
    wcwi__bfxr = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(wcwi__bfxr, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(swa__sgjnl
            .type, 0))
        with payload._iterate() as yupc__kadff:
            i = c.builder.load(index)
            item = yupc__kadff.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return wcwi__bfxr, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    wyws__lnzl = h.type
    nmc__qdm = self.mask
    dtype = self._ty.dtype
    hlvvn__iewlz = context.typing_context
    fnty = hlvvn__iewlz.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(hlvvn__iewlz, (dtype, dtype), {})
    udnj__qffql = context.get_function(fnty, sig)
    ifo__fjiwp = ir.Constant(wyws__lnzl, 1)
    exafe__znzc = ir.Constant(wyws__lnzl, 5)
    juzlm__vhyl = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, nmc__qdm))
    if for_insert:
        zmm__igkb = nmc__qdm.type(-1)
        hnera__ydw = cgutils.alloca_once_value(builder, zmm__igkb)
    usd__gimt = builder.append_basic_block('lookup.body')
    kuta__kpzm = builder.append_basic_block('lookup.found')
    vdix__ywt = builder.append_basic_block('lookup.not_found')
    ubcre__copa = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        woch__gdqwp = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, woch__gdqwp)):
            nuf__cfafv = udnj__qffql(builder, (item, entry.key))
            with builder.if_then(nuf__cfafv):
                builder.branch(kuta__kpzm)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, woch__gdqwp)):
            builder.branch(vdix__ywt)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, woch__gdqwp)):
                iow__isx = builder.load(hnera__ydw)
                iow__isx = builder.select(builder.icmp_unsigned('==',
                    iow__isx, zmm__igkb), i, iow__isx)
                builder.store(iow__isx, hnera__ydw)
    with cgutils.for_range(builder, ir.Constant(wyws__lnzl, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, ifo__fjiwp)
        i = builder.and_(i, nmc__qdm)
        builder.store(i, index)
    builder.branch(usd__gimt)
    with builder.goto_block(usd__gimt):
        i = builder.load(index)
        check_entry(i)
        klw__vwprb = builder.load(juzlm__vhyl)
        klw__vwprb = builder.lshr(klw__vwprb, exafe__znzc)
        i = builder.add(ifo__fjiwp, builder.mul(i, exafe__znzc))
        i = builder.and_(nmc__qdm, builder.add(i, klw__vwprb))
        builder.store(i, index)
        builder.store(klw__vwprb, juzlm__vhyl)
        builder.branch(usd__gimt)
    with builder.goto_block(vdix__ywt):
        if for_insert:
            i = builder.load(index)
            iow__isx = builder.load(hnera__ydw)
            i = builder.select(builder.icmp_unsigned('==', iow__isx,
                zmm__igkb), i, iow__isx)
            builder.store(i, index)
        builder.branch(ubcre__copa)
    with builder.goto_block(kuta__kpzm):
        builder.branch(ubcre__copa)
    builder.position_at_end(ubcre__copa)
    sltss__mxhei = builder.phi(ir.IntType(1), 'found')
    sltss__mxhei.add_incoming(cgutils.true_bit, kuta__kpzm)
    sltss__mxhei.add_incoming(cgutils.false_bit, vdix__ywt)
    return sltss__mxhei, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    liqeo__degg = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    xzitk__qwf = payload.used
    ifo__fjiwp = ir.Constant(xzitk__qwf.type, 1)
    xzitk__qwf = payload.used = builder.add(xzitk__qwf, ifo__fjiwp)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, liqeo__degg), likely=True):
        payload.fill = builder.add(payload.fill, ifo__fjiwp)
    if do_resize:
        self.upsize(xzitk__qwf)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    sltss__mxhei, i = payload._lookup(item, h, for_insert=True)
    nwuql__ixwo = builder.not_(sltss__mxhei)
    with builder.if_then(nwuql__ixwo):
        entry = payload.get_entry(i)
        liqeo__degg = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        xzitk__qwf = payload.used
        ifo__fjiwp = ir.Constant(xzitk__qwf.type, 1)
        xzitk__qwf = payload.used = builder.add(xzitk__qwf, ifo__fjiwp)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, liqeo__degg), likely=True):
            payload.fill = builder.add(payload.fill, ifo__fjiwp)
        if do_resize:
            self.upsize(xzitk__qwf)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    xzitk__qwf = payload.used
    ifo__fjiwp = ir.Constant(xzitk__qwf.type, 1)
    xzitk__qwf = payload.used = self._builder.sub(xzitk__qwf, ifo__fjiwp)
    if do_resize:
        self.downsize(xzitk__qwf)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    tac__gidl = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, tac__gidl)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    toi__lss = payload
    wcwi__bfxr = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(wcwi__bfxr), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with toi__lss._iterate() as yupc__kadff:
        entry = yupc__kadff.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(toi__lss.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as yupc__kadff:
        entry = yupc__kadff.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    wcwi__bfxr = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(wcwi__bfxr), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    wcwi__bfxr = cgutils.alloca_once_value(builder, cgutils.true_bit)
    wyws__lnzl = context.get_value_type(types.intp)
    ptvzr__hentl = ir.Constant(wyws__lnzl, 0)
    ifo__fjiwp = ir.Constant(wyws__lnzl, 1)
    vvzie__llp = context.get_data_type(types.SetPayload(self._ty))
    vjlb__qqoj = context.get_abi_sizeof(vvzie__llp)
    npexq__gdjea = self._entrysize
    vjlb__qqoj -= npexq__gdjea
    pggz__pulo, laof__rabk = cgutils.muladd_with_overflow(builder, nentries,
        ir.Constant(wyws__lnzl, npexq__gdjea), ir.Constant(wyws__lnzl,
        vjlb__qqoj))
    with builder.if_then(laof__rabk, likely=False):
        builder.store(cgutils.false_bit, wcwi__bfxr)
    with builder.if_then(builder.load(wcwi__bfxr), likely=True):
        if realloc:
            aixti__ettpb = self._set.meminfo
            csugi__jarsq = context.nrt.meminfo_varsize_alloc(builder,
                aixti__ettpb, size=pggz__pulo)
            duiq__aofyy = cgutils.is_null(builder, csugi__jarsq)
        else:
            hzxf__mqewd = _imp_dtor(context, builder.module, self._ty)
            aixti__ettpb = context.nrt.meminfo_new_varsize_dtor(builder,
                pggz__pulo, builder.bitcast(hzxf__mqewd, cgutils.voidptr_t))
            duiq__aofyy = cgutils.is_null(builder, aixti__ettpb)
        with builder.if_else(duiq__aofyy, likely=False) as (fuqtf__pgtm,
            gmz__syv):
            with fuqtf__pgtm:
                builder.store(cgutils.false_bit, wcwi__bfxr)
            with gmz__syv:
                if not realloc:
                    self._set.meminfo = aixti__ettpb
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, pggz__pulo, 255)
                payload.used = ptvzr__hentl
                payload.fill = ptvzr__hentl
                payload.finger = ptvzr__hentl
                hyp__skib = builder.sub(nentries, ifo__fjiwp)
                payload.mask = hyp__skib
    return builder.load(wcwi__bfxr)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    wcwi__bfxr = cgutils.alloca_once_value(builder, cgutils.true_bit)
    wyws__lnzl = context.get_value_type(types.intp)
    ptvzr__hentl = ir.Constant(wyws__lnzl, 0)
    ifo__fjiwp = ir.Constant(wyws__lnzl, 1)
    vvzie__llp = context.get_data_type(types.SetPayload(self._ty))
    vjlb__qqoj = context.get_abi_sizeof(vvzie__llp)
    npexq__gdjea = self._entrysize
    vjlb__qqoj -= npexq__gdjea
    nmc__qdm = src_payload.mask
    nentries = builder.add(ifo__fjiwp, nmc__qdm)
    pggz__pulo = builder.add(ir.Constant(wyws__lnzl, vjlb__qqoj), builder.
        mul(ir.Constant(wyws__lnzl, npexq__gdjea), nentries))
    with builder.if_then(builder.load(wcwi__bfxr), likely=True):
        hzxf__mqewd = _imp_dtor(context, builder.module, self._ty)
        aixti__ettpb = context.nrt.meminfo_new_varsize_dtor(builder,
            pggz__pulo, builder.bitcast(hzxf__mqewd, cgutils.voidptr_t))
        duiq__aofyy = cgutils.is_null(builder, aixti__ettpb)
        with builder.if_else(duiq__aofyy, likely=False) as (fuqtf__pgtm,
            gmz__syv):
            with fuqtf__pgtm:
                builder.store(cgutils.false_bit, wcwi__bfxr)
            with gmz__syv:
                self._set.meminfo = aixti__ettpb
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = ptvzr__hentl
                payload.mask = nmc__qdm
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, npexq__gdjea)
                with src_payload._iterate() as yupc__kadff:
                    context.nrt.incref(builder, self._ty.dtype, yupc__kadff
                        .entry.key)
    return builder.load(wcwi__bfxr)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    dklcb__qvgw = context.get_value_type(types.voidptr)
    pjdl__wjztd = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [dklcb__qvgw, pjdl__wjztd,
        dklcb__qvgw])
    tamcb__tbk = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=tamcb__tbk)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        tmb__vwdvx = builder.bitcast(fn.args[0], cgutils.voidptr_t.as_pointer()
            )
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, tmb__vwdvx)
        with payload._iterate() as yupc__kadff:
            entry = yupc__kadff.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    jgusa__byv, = sig.args
    rnxp__lwsg, = args
    sle__unyf = numba.core.imputils.call_len(context, builder, jgusa__byv,
        rnxp__lwsg)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, sle__unyf)
    with numba.core.imputils.for_iter(context, builder, jgusa__byv, rnxp__lwsg
        ) as yupc__kadff:
        inst.add(yupc__kadff.value)
        context.nrt.decref(builder, set_type.dtype, yupc__kadff.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    jgusa__byv = sig.args[1]
    rnxp__lwsg = args[1]
    sle__unyf = numba.core.imputils.call_len(context, builder, jgusa__byv,
        rnxp__lwsg)
    if sle__unyf is not None:
        bnxc__eaud = builder.add(inst.payload.used, sle__unyf)
        inst.upsize(bnxc__eaud)
    with numba.core.imputils.for_iter(context, builder, jgusa__byv, rnxp__lwsg
        ) as yupc__kadff:
        qah__iyge = context.cast(builder, yupc__kadff.value, jgusa__byv.
            dtype, inst.dtype)
        inst.add(qah__iyge)
        context.nrt.decref(builder, jgusa__byv.dtype, yupc__kadff.value)
    if sle__unyf is not None:
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
