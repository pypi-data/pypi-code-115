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
    drjlk__rmbe = numba.core.bytecode.FunctionIdentity.from_function(func)
    aapy__exjq = numba.core.interpreter.Interpreter(drjlk__rmbe)
    giu__oolq = numba.core.bytecode.ByteCode(func_id=drjlk__rmbe)
    func_ir = aapy__exjq.interpret(giu__oolq)
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
        ihnv__aeuha = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        ihnv__aeuha.run()
    xhbd__efj = numba.core.postproc.PostProcessor(func_ir)
    xhbd__efj.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, xja__pmgou in visit_vars_extensions.items():
        if isinstance(stmt, t):
            xja__pmgou(stmt, callback, cbdata)
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
    yhjjo__anad = ['ravel', 'transpose', 'reshape']
    for vazg__nqdf in blocks.values():
        for nsfdr__yhlnr in vazg__nqdf.body:
            if type(nsfdr__yhlnr) in alias_analysis_extensions:
                xja__pmgou = alias_analysis_extensions[type(nsfdr__yhlnr)]
                xja__pmgou(nsfdr__yhlnr, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(nsfdr__yhlnr, ir.Assign):
                hry__hlfb = nsfdr__yhlnr.value
                zmp__otx = nsfdr__yhlnr.target.name
                if is_immutable_type(zmp__otx, typemap):
                    continue
                if isinstance(hry__hlfb, ir.Var
                    ) and zmp__otx != hry__hlfb.name:
                    _add_alias(zmp__otx, hry__hlfb.name, alias_map, arg_aliases
                        )
                if isinstance(hry__hlfb, ir.Expr) and (hry__hlfb.op ==
                    'cast' or hry__hlfb.op in ['getitem', 'static_getitem']):
                    _add_alias(zmp__otx, hry__hlfb.value.name, alias_map,
                        arg_aliases)
                if isinstance(hry__hlfb, ir.Expr
                    ) and hry__hlfb.op == 'inplace_binop':
                    _add_alias(zmp__otx, hry__hlfb.lhs.name, alias_map,
                        arg_aliases)
                if isinstance(hry__hlfb, ir.Expr
                    ) and hry__hlfb.op == 'getattr' and hry__hlfb.attr in ['T',
                    'ctypes', 'flat']:
                    _add_alias(zmp__otx, hry__hlfb.value.name, alias_map,
                        arg_aliases)
                if isinstance(hry__hlfb, ir.Expr
                    ) and hry__hlfb.op == 'getattr' and hry__hlfb.attr not in [
                    'shape'] and hry__hlfb.value.name in arg_aliases:
                    _add_alias(zmp__otx, hry__hlfb.value.name, alias_map,
                        arg_aliases)
                if isinstance(hry__hlfb, ir.Expr
                    ) and hry__hlfb.op == 'getattr' and hry__hlfb.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(zmp__otx, hry__hlfb.value.name, alias_map,
                        arg_aliases)
                if isinstance(hry__hlfb, ir.Expr) and hry__hlfb.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(zmp__otx, typemap):
                    for fiad__nygn in hry__hlfb.items:
                        _add_alias(zmp__otx, fiad__nygn.name, alias_map,
                            arg_aliases)
                if isinstance(hry__hlfb, ir.Expr) and hry__hlfb.op == 'call':
                    qklb__sgnf = guard(find_callname, func_ir, hry__hlfb,
                        typemap)
                    if qklb__sgnf is None:
                        continue
                    zdmb__lcmxh, vwp__fqu = qklb__sgnf
                    if qklb__sgnf in alias_func_extensions:
                        yoq__sxmg = alias_func_extensions[qklb__sgnf]
                        yoq__sxmg(zmp__otx, hry__hlfb.args, alias_map,
                            arg_aliases)
                    if vwp__fqu == 'numpy' and zdmb__lcmxh in yhjjo__anad:
                        _add_alias(zmp__otx, hry__hlfb.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(vwp__fqu, ir.Var
                        ) and zdmb__lcmxh in yhjjo__anad:
                        _add_alias(zmp__otx, vwp__fqu.name, alias_map,
                            arg_aliases)
    xkur__sith = copy.deepcopy(alias_map)
    for fiad__nygn in xkur__sith:
        for gewo__npt in xkur__sith[fiad__nygn]:
            alias_map[fiad__nygn] |= alias_map[gewo__npt]
        for gewo__npt in xkur__sith[fiad__nygn]:
            alias_map[gewo__npt] = alias_map[fiad__nygn]
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
    llz__tgdk = compute_cfg_from_blocks(func_ir.blocks)
    zsj__iwb = compute_use_defs(func_ir.blocks)
    uxen__ruh = compute_live_map(llz__tgdk, func_ir.blocks, zsj__iwb.usemap,
        zsj__iwb.defmap)
    flgp__qeayb = True
    while flgp__qeayb:
        flgp__qeayb = False
        for rpoaa__dzrzf, block in func_ir.blocks.items():
            lives = {fiad__nygn.name for fiad__nygn in block.terminator.
                list_vars()}
            for oqbtp__vhfw, cnmgh__brjtm in llz__tgdk.successors(rpoaa__dzrzf
                ):
                lives |= uxen__ruh[oqbtp__vhfw]
            yqlg__zem = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    zmp__otx = stmt.target
                    cvo__yrnn = stmt.value
                    if zmp__otx.name not in lives:
                        if isinstance(cvo__yrnn, ir.Expr
                            ) and cvo__yrnn.op == 'make_function':
                            continue
                        if isinstance(cvo__yrnn, ir.Expr
                            ) and cvo__yrnn.op == 'getattr':
                            continue
                        if isinstance(cvo__yrnn, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(zmp__otx,
                            None), types.Function):
                            continue
                        if isinstance(cvo__yrnn, ir.Expr
                            ) and cvo__yrnn.op == 'build_map':
                            continue
                    if isinstance(cvo__yrnn, ir.Var
                        ) and zmp__otx.name == cvo__yrnn.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    rqb__ysbs = analysis.ir_extension_usedefs[type(stmt)]
                    gdeiw__stab, yekqx__sljp = rqb__ysbs(stmt)
                    lives -= yekqx__sljp
                    lives |= gdeiw__stab
                else:
                    lives |= {fiad__nygn.name for fiad__nygn in stmt.
                        list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(zmp__otx.name)
                yqlg__zem.append(stmt)
            yqlg__zem.reverse()
            if len(block.body) != len(yqlg__zem):
                flgp__qeayb = True
            block.body = yqlg__zem


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    jysc__wtqi = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (jysc__wtqi,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    jepp__njbk = dict(key=func, _overload_func=staticmethod(overload_func),
        _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), jepp__njbk)


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
            for yixnc__nmahr in fnty.templates:
                self._inline_overloads.update(yixnc__nmahr._inline_overloads)
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
    jepp__njbk = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), jepp__njbk)
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
    eykds__oaim, bjzfi__tkbfy = self._get_impl(args, kws)
    if eykds__oaim is None:
        return
    lesoc__fbffq = types.Dispatcher(eykds__oaim)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        tydud__jok = eykds__oaim._compiler
        flags = compiler.Flags()
        hhu__afa = tydud__jok.targetdescr.typing_context
        ixlu__hmw = tydud__jok.targetdescr.target_context
        ziijx__tddua = tydud__jok.pipeline_class(hhu__afa, ixlu__hmw, None,
            None, None, flags, None)
        enor__ceey = InlineWorker(hhu__afa, ixlu__hmw, tydud__jok.locals,
            ziijx__tddua, flags, None)
        eyzm__xbl = lesoc__fbffq.dispatcher.get_call_template
        yixnc__nmahr, nsmx__achq, ahhi__trmyo, kws = eyzm__xbl(bjzfi__tkbfy,
            kws)
        if ahhi__trmyo in self._inline_overloads:
            return self._inline_overloads[ahhi__trmyo]['iinfo'].signature
        ir = enor__ceey.run_untyped_passes(lesoc__fbffq.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, ixlu__hmw, ir, ahhi__trmyo, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, ahhi__trmyo, None)
        self._inline_overloads[sig.args] = {'folded_args': ahhi__trmyo}
        orzsr__glji = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = orzsr__glji
        if not self._inline.is_always_inline:
            sig = lesoc__fbffq.get_call_type(self.context, bjzfi__tkbfy, kws)
            self._compiled_overloads[sig.args] = lesoc__fbffq.get_overload(sig)
        mewkn__kbz = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': ahhi__trmyo,
            'iinfo': mewkn__kbz}
    else:
        sig = lesoc__fbffq.get_call_type(self.context, bjzfi__tkbfy, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = lesoc__fbffq.get_overload(sig)
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
    xetl__tzgk = [True, False]
    kpblb__wlzo = [False, True]
    gkl__yyd = _ResolutionFailures(context, self, args, kws, depth=self._depth)
    from numba.core.target_extension import get_local_target
    mbsy__rgnp = get_local_target(context)
    wwkz__xoh = utils.order_by_target_specificity(mbsy__rgnp, self.
        templates, fnkey=self.key[0])
    self._depth += 1
    for kbxoe__uwgo in wwkz__xoh:
        lkkqz__oyncm = kbxoe__uwgo(context)
        bqze__wnc = xetl__tzgk if lkkqz__oyncm.prefer_literal else kpblb__wlzo
        bqze__wnc = [True] if getattr(lkkqz__oyncm, '_no_unliteral', False
            ) else bqze__wnc
        for khskw__amoqm in bqze__wnc:
            try:
                if khskw__amoqm:
                    sig = lkkqz__oyncm.apply(args, kws)
                else:
                    yjnml__spm = tuple([_unlit_non_poison(a) for a in args])
                    hsl__dyss = {zswl__shpoc: _unlit_non_poison(fiad__nygn) for
                        zswl__shpoc, fiad__nygn in kws.items()}
                    sig = lkkqz__oyncm.apply(yjnml__spm, hsl__dyss)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    gkl__yyd.add_error(lkkqz__oyncm, False, e, khskw__amoqm)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = lkkqz__oyncm.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    ljjh__wldzc = getattr(lkkqz__oyncm, 'cases', None)
                    if ljjh__wldzc is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            ljjh__wldzc)
                    else:
                        msg = 'No match.'
                    gkl__yyd.add_error(lkkqz__oyncm, True, msg, khskw__amoqm)
    gkl__yyd.raise_error()


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
    yixnc__nmahr = self.template(context)
    paatg__dsy = None
    lzmp__nwf = None
    snmpy__gnxe = None
    bqze__wnc = [True, False] if yixnc__nmahr.prefer_literal else [False, True]
    bqze__wnc = [True] if getattr(yixnc__nmahr, '_no_unliteral', False
        ) else bqze__wnc
    for khskw__amoqm in bqze__wnc:
        if khskw__amoqm:
            try:
                snmpy__gnxe = yixnc__nmahr.apply(args, kws)
            except Exception as vzpuw__tjf:
                if isinstance(vzpuw__tjf, errors.ForceLiteralArg):
                    raise vzpuw__tjf
                paatg__dsy = vzpuw__tjf
                snmpy__gnxe = None
            else:
                break
        else:
            eqvyf__ettt = tuple([_unlit_non_poison(a) for a in args])
            vreii__mxvc = {zswl__shpoc: _unlit_non_poison(fiad__nygn) for 
                zswl__shpoc, fiad__nygn in kws.items()}
            zsxir__plgj = eqvyf__ettt == args and kws == vreii__mxvc
            if not zsxir__plgj and snmpy__gnxe is None:
                try:
                    snmpy__gnxe = yixnc__nmahr.apply(eqvyf__ettt, vreii__mxvc)
                except Exception as vzpuw__tjf:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(
                        vzpuw__tjf, errors.NumbaError):
                        raise vzpuw__tjf
                    if isinstance(vzpuw__tjf, errors.ForceLiteralArg):
                        if yixnc__nmahr.prefer_literal:
                            raise vzpuw__tjf
                    lzmp__nwf = vzpuw__tjf
                else:
                    break
    if snmpy__gnxe is None and (lzmp__nwf is not None or paatg__dsy is not None
        ):
        xrpl__ppv = '- Resolution failure for {} arguments:\n{}\n'
        rrgbz__djls = _termcolor.highlight(xrpl__ppv)
        if numba.core.config.DEVELOPER_MODE:
            myiv__uns = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    cyus__jcn = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    cyus__jcn = ['']
                dsh__erbbz = '\n{}'.format(2 * myiv__uns)
                twn__tvig = _termcolor.reset(dsh__erbbz + dsh__erbbz.join(
                    _bt_as_lines(cyus__jcn)))
                return _termcolor.reset(twn__tvig)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            tzcz__bdwx = str(e)
            tzcz__bdwx = tzcz__bdwx if tzcz__bdwx else str(repr(e)) + add_bt(e)
            iiufe__ehnqq = errors.TypingError(textwrap.dedent(tzcz__bdwx))
            return rrgbz__djls.format(literalness, str(iiufe__ehnqq))
        import bodo
        if isinstance(paatg__dsy, bodo.utils.typing.BodoError):
            raise paatg__dsy
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', paatg__dsy) +
                nested_msg('non-literal', lzmp__nwf))
        else:
            if 'missing a required argument' in paatg__dsy.msg:
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
            raise errors.TypingError(msg, loc=paatg__dsy.loc)
    return snmpy__gnxe


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
    zdmb__lcmxh = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=zdmb__lcmxh)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            xsovs__xjpx = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), xsovs__xjpx)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    zfuc__jmirw = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            zfuc__jmirw.append(types.Omitted(a.value))
        else:
            zfuc__jmirw.append(self.typeof_pyval(a))
    cvee__gxdm = None
    try:
        error = None
        cvee__gxdm = self.compile(tuple(zfuc__jmirw))
    except errors.ForceLiteralArg as e:
        tqv__guhx = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if tqv__guhx:
            fmbg__mdmgo = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            usod__jckjc = ', '.join('Arg #{} is {}'.format(i, args[i]) for
                i in sorted(tqv__guhx))
            raise errors.CompilerError(fmbg__mdmgo.format(usod__jckjc))
        bjzfi__tkbfy = []
        try:
            for i, fiad__nygn in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        bjzfi__tkbfy.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        bjzfi__tkbfy.append(types.literal(args[i]))
                else:
                    bjzfi__tkbfy.append(args[i])
            args = bjzfi__tkbfy
        except (OSError, FileNotFoundError) as ohoy__ztbrv:
            error = FileNotFoundError(str(ohoy__ztbrv) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                cvee__gxdm = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        vjf__ujjq = []
        for i, suq__pcap in enumerate(args):
            val = suq__pcap.value if isinstance(suq__pcap, numba.core.
                dispatcher.OmittedArg) else suq__pcap
            try:
                wvsp__vukpk = typeof(val, Purpose.argument)
            except ValueError as nweul__vfqy:
                vjf__ujjq.append((i, str(nweul__vfqy)))
            else:
                if wvsp__vukpk is None:
                    vjf__ujjq.append((i,
                        f'cannot determine Numba type of value {val}'))
        if vjf__ujjq:
            hxpp__ocnxu = '\n'.join(f'- argument {i}: {bua__pjob}' for i,
                bua__pjob in vjf__ujjq)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{hxpp__ocnxu}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                pqoe__gum = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                soldh__yrse = False
                for onjc__ffn in pqoe__gum:
                    if onjc__ffn in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        soldh__yrse = True
                        break
                if not soldh__yrse:
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
                xsovs__xjpx = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), xsovs__xjpx)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return cvee__gxdm


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
    for cduib__wkvyz in cres.library._codegen._engine._defined_symbols:
        if cduib__wkvyz.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in cduib__wkvyz and (
            'bodo_gb_udf_update_local' in cduib__wkvyz or 
            'bodo_gb_udf_combine' in cduib__wkvyz or 'bodo_gb_udf_eval' in
            cduib__wkvyz or 'bodo_gb_apply_general_udfs' in cduib__wkvyz):
            gb_agg_cfunc_addr[cduib__wkvyz
                ] = cres.library.get_pointer_to_function(cduib__wkvyz)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for cduib__wkvyz in cres.library._codegen._engine._defined_symbols:
        if cduib__wkvyz.startswith('cfunc') and ('get_join_cond_addr' not in
            cduib__wkvyz or 'bodo_join_gen_cond' in cduib__wkvyz):
            join_gen_cond_cfunc_addr[cduib__wkvyz
                ] = cres.library.get_pointer_to_function(cduib__wkvyz)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    eykds__oaim = self._get_dispatcher_for_current_target()
    if eykds__oaim is not self:
        return eykds__oaim.compile(sig)
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
            ukibr__fvp = self.overloads.get(tuple(args))
            if ukibr__fvp is not None:
                return ukibr__fvp.entry_point
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
            zcem__cbkk = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=zcem__cbkk):
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
    qto__dna = self._final_module
    mex__qtmif = []
    bmef__xyvmb = 0
    for fn in qto__dna.functions:
        bmef__xyvmb += 1
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
            mex__qtmif.append(fn.name)
    if bmef__xyvmb == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if mex__qtmif:
        qto__dna = qto__dna.clone()
        for name in mex__qtmif:
            qto__dna.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = qto__dna
    return qto__dna


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
    for brub__oujsg in self.constraints:
        loc = brub__oujsg.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                brub__oujsg(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                jtddu__ldatp = numba.core.errors.TypingError(str(e), loc=
                    brub__oujsg.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(jtddu__ldatp, e)
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
                    jtddu__ldatp = numba.core.errors.TypingError(msg.format
                        (con=brub__oujsg, err=str(e)), loc=brub__oujsg.loc,
                        highlighting=False)
                    errors.append(utils.chain_exception(jtddu__ldatp, e))
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
    for acbbl__qpiq in self._failures.values():
        for dbaw__xsrl in acbbl__qpiq:
            if isinstance(dbaw__xsrl.error, ForceLiteralArg):
                raise dbaw__xsrl.error
            if isinstance(dbaw__xsrl.error, bodo.utils.typing.BodoError):
                raise dbaw__xsrl.error
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
    fyjy__gghlu = False
    yqlg__zem = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        tytw__ogt = set()
        xez__itznj = lives & alias_set
        for fiad__nygn in xez__itznj:
            tytw__ogt |= alias_map[fiad__nygn]
        lives_n_aliases = lives | tytw__ogt | arg_aliases
        if type(stmt) in remove_dead_extensions:
            xja__pmgou = remove_dead_extensions[type(stmt)]
            stmt = xja__pmgou(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                fyjy__gghlu = True
                continue
        if isinstance(stmt, ir.Assign):
            zmp__otx = stmt.target
            cvo__yrnn = stmt.value
            if zmp__otx.name not in lives and has_no_side_effect(cvo__yrnn,
                lives_n_aliases, call_table):
                fyjy__gghlu = True
                continue
            if saved_array_analysis and zmp__otx.name in lives and is_expr(
                cvo__yrnn, 'getattr'
                ) and cvo__yrnn.attr == 'shape' and is_array_typ(typemap[
                cvo__yrnn.value.name]) and cvo__yrnn.value.name not in lives:
                crqa__waqxr = {fiad__nygn: zswl__shpoc for zswl__shpoc,
                    fiad__nygn in func_ir.blocks.items()}
                if block in crqa__waqxr:
                    rpoaa__dzrzf = crqa__waqxr[block]
                    frv__qjd = saved_array_analysis.get_equiv_set(rpoaa__dzrzf)
                    nyevz__jie = frv__qjd.get_equiv_set(cvo__yrnn.value)
                    if nyevz__jie is not None:
                        for fiad__nygn in nyevz__jie:
                            if fiad__nygn.endswith('#0'):
                                fiad__nygn = fiad__nygn[:-2]
                            if fiad__nygn in typemap and is_array_typ(typemap
                                [fiad__nygn]) and fiad__nygn in lives:
                                cvo__yrnn.value = ir.Var(cvo__yrnn.value.
                                    scope, fiad__nygn, cvo__yrnn.value.loc)
                                fyjy__gghlu = True
                                break
            if isinstance(cvo__yrnn, ir.Var
                ) and zmp__otx.name == cvo__yrnn.name:
                fyjy__gghlu = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                fyjy__gghlu = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            rqb__ysbs = analysis.ir_extension_usedefs[type(stmt)]
            gdeiw__stab, yekqx__sljp = rqb__ysbs(stmt)
            lives -= yekqx__sljp
            lives |= gdeiw__stab
        else:
            lives |= {fiad__nygn.name for fiad__nygn in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                nvuqb__xpgm = set()
                if isinstance(cvo__yrnn, ir.Expr):
                    nvuqb__xpgm = {fiad__nygn.name for fiad__nygn in
                        cvo__yrnn.list_vars()}
                if zmp__otx.name not in nvuqb__xpgm:
                    lives.remove(zmp__otx.name)
        yqlg__zem.append(stmt)
    yqlg__zem.reverse()
    block.body = yqlg__zem
    return fyjy__gghlu


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            qyoi__hwte, = args
            if isinstance(qyoi__hwte, types.IterableType):
                dtype = qyoi__hwte.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), qyoi__hwte)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    ljow__vec = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (ljow__vec, self.dtype)
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
        except LiteralTypingError as lzky__uvh:
            return
    try:
        return literal(value)
    except LiteralTypingError as lzky__uvh:
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
        qxkpd__vcu = py_func.__qualname__
    except AttributeError as lzky__uvh:
        qxkpd__vcu = py_func.__name__
    hctwq__bkdb = inspect.getfile(py_func)
    for cls in self._locator_classes:
        aww__lojff = cls.from_function(py_func, hctwq__bkdb)
        if aww__lojff is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (qxkpd__vcu, hctwq__bkdb))
    self._locator = aww__lojff
    chvs__xya = inspect.getfile(py_func)
    ckdq__lshh = os.path.splitext(os.path.basename(chvs__xya))[0]
    if hctwq__bkdb.startswith('<ipython-'):
        danf__qjq = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)',
            '\\1\\3', ckdq__lshh, count=1)
        if danf__qjq == ckdq__lshh:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        ckdq__lshh = danf__qjq
    ktzbr__viyu = '%s.%s' % (ckdq__lshh, qxkpd__vcu)
    spgar__oygya = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(ktzbr__viyu, spgar__oygya)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    esmy__fmnv = list(filter(lambda a: self._istuple(a.name), args))
    if len(esmy__fmnv) == 2 and fn.__name__ == 'add':
        scrab__bebt = self.typemap[esmy__fmnv[0].name]
        onjz__fvxww = self.typemap[esmy__fmnv[1].name]
        if scrab__bebt.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                esmy__fmnv[1]))
        if onjz__fvxww.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                esmy__fmnv[0]))
        try:
            uba__hbc = [equiv_set.get_shape(x) for x in esmy__fmnv]
            if None in uba__hbc:
                return None
            chbfc__iaom = sum(uba__hbc, ())
            return ArrayAnalysis.AnalyzeResult(shape=chbfc__iaom)
        except GuardException as lzky__uvh:
            return None
    kykbp__ukuk = list(filter(lambda a: self._isarray(a.name), args))
    require(len(kykbp__ukuk) > 0)
    dzi__fwylo = [x.name for x in kykbp__ukuk]
    tcrd__tkrq = [self.typemap[x.name].ndim for x in kykbp__ukuk]
    mgv__qhkwx = max(tcrd__tkrq)
    require(mgv__qhkwx > 0)
    uba__hbc = [equiv_set.get_shape(x) for x in kykbp__ukuk]
    if any(a is None for a in uba__hbc):
        return ArrayAnalysis.AnalyzeResult(shape=kykbp__ukuk[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, kykbp__ukuk))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, uba__hbc,
        dzi__fwylo)


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
    kph__mvd = code_obj.code
    bpnep__yfxnx = len(kph__mvd.co_freevars)
    vvih__fpdco = kph__mvd.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        tac__jvj, op = ir_utils.find_build_sequence(caller_ir, code_obj.closure
            )
        assert op == 'build_tuple'
        vvih__fpdco = [fiad__nygn.name for fiad__nygn in tac__jvj]
    gyk__hlrjc = caller_ir.func_id.func.__globals__
    try:
        gyk__hlrjc = getattr(code_obj, 'globals', gyk__hlrjc)
    except KeyError as lzky__uvh:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    kcimk__ehqo = []
    for x in vvih__fpdco:
        try:
            woi__rboh = caller_ir.get_definition(x)
        except KeyError as lzky__uvh:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(woi__rboh, (ir.Const, ir.Global, ir.FreeVar)):
            val = woi__rboh.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                jysc__wtqi = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                gyk__hlrjc[jysc__wtqi] = bodo.jit(distributed=False)(val)
                gyk__hlrjc[jysc__wtqi].is_nested_func = True
                val = jysc__wtqi
            if isinstance(val, CPUDispatcher):
                jysc__wtqi = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                gyk__hlrjc[jysc__wtqi] = val
                val = jysc__wtqi
            kcimk__ehqo.append(val)
        elif isinstance(woi__rboh, ir.Expr
            ) and woi__rboh.op == 'make_function':
            okdmw__jsd = convert_code_obj_to_function(woi__rboh, caller_ir)
            jysc__wtqi = ir_utils.mk_unique_var('nested_func').replace('.', '_'
                )
            gyk__hlrjc[jysc__wtqi] = bodo.jit(distributed=False)(okdmw__jsd)
            gyk__hlrjc[jysc__wtqi].is_nested_func = True
            kcimk__ehqo.append(jysc__wtqi)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    iim__ahqrt = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in enumerate(
        kcimk__ehqo)])
    uvfwh__ulti = ','.join([('c_%d' % i) for i in range(bpnep__yfxnx)])
    uplo__pfma = list(kph__mvd.co_varnames)
    kwn__galbw = 0
    fdhuo__akweh = kph__mvd.co_argcount
    ezfyc__omkv = caller_ir.get_definition(code_obj.defaults)
    if ezfyc__omkv is not None:
        if isinstance(ezfyc__omkv, tuple):
            gyff__rqwpn = [caller_ir.get_definition(x).value for x in
                ezfyc__omkv]
            fih__rrtkt = tuple(gyff__rqwpn)
        else:
            gyff__rqwpn = [caller_ir.get_definition(x).value for x in
                ezfyc__omkv.items]
            fih__rrtkt = tuple(gyff__rqwpn)
        kwn__galbw = len(fih__rrtkt)
    mke__zgx = fdhuo__akweh - kwn__galbw
    spxr__alrj = ','.join([('%s' % uplo__pfma[i]) for i in range(mke__zgx)])
    if kwn__galbw:
        wlt__ujo = [('%s = %s' % (uplo__pfma[i + mke__zgx], fih__rrtkt[i])) for
            i in range(kwn__galbw)]
        spxr__alrj += ', '
        spxr__alrj += ', '.join(wlt__ujo)
    return _create_function_from_code_obj(kph__mvd, iim__ahqrt, spxr__alrj,
        uvfwh__ulti, gyk__hlrjc)


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
    for mdnd__hyh, (ukc__cts, yakug__xya) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % yakug__xya)
            epjuj__mrb = _pass_registry.get(ukc__cts).pass_inst
            if isinstance(epjuj__mrb, CompilerPass):
                self._runPass(mdnd__hyh, epjuj__mrb, state)
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
                    pipeline_name, yakug__xya)
                xhc__misu = self._patch_error(msg, e)
                raise xhc__misu
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
    mrat__yqfwi = None
    yekqx__sljp = {}

    def lookup(var, already_seen, varonly=True):
        val = yekqx__sljp.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    iecfu__ryrz = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        zmp__otx = stmt.target
        cvo__yrnn = stmt.value
        yekqx__sljp[zmp__otx.name] = cvo__yrnn
        if isinstance(cvo__yrnn, ir.Var) and cvo__yrnn.name in yekqx__sljp:
            cvo__yrnn = lookup(cvo__yrnn, set())
        if isinstance(cvo__yrnn, ir.Expr):
            dphj__wwuuc = set(lookup(fiad__nygn, set(), True).name for
                fiad__nygn in cvo__yrnn.list_vars())
            if name in dphj__wwuuc:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(cvo__yrnn)]
                sra__hgrd = [x for x, gyfh__fgd in args if gyfh__fgd.name !=
                    name]
                args = [(x, gyfh__fgd) for x, gyfh__fgd in args if x !=
                    gyfh__fgd.name]
                yicvx__bsk = dict(args)
                if len(sra__hgrd) == 1:
                    yicvx__bsk[sra__hgrd[0]] = ir.Var(zmp__otx.scope, name +
                        '#init', zmp__otx.loc)
                replace_vars_inner(cvo__yrnn, yicvx__bsk)
                mrat__yqfwi = nodes[i:]
                break
    return mrat__yqfwi


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
        spt__jqtpn = expand_aliases({fiad__nygn.name for fiad__nygn in stmt
            .list_vars()}, alias_map, arg_aliases)
        ytprz__psl = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        wmyl__znr = expand_aliases({fiad__nygn.name for fiad__nygn in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        immpt__tqivv = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(ytprz__psl & wmyl__znr | immpt__tqivv & spt__jqtpn) == 0:
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
    ncblb__wfwuu = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            ncblb__wfwuu.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                ncblb__wfwuu.update(get_parfor_writes(stmt, func_ir))
    return ncblb__wfwuu


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    ncblb__wfwuu = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        ncblb__wfwuu.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        ncblb__wfwuu = {fiad__nygn.name for fiad__nygn in stmt.df_out_vars.
            values()}
        if stmt.out_key_vars is not None:
            ncblb__wfwuu.update({fiad__nygn.name for fiad__nygn in stmt.
                out_key_vars})
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        ncblb__wfwuu = {fiad__nygn.name for fiad__nygn in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        ncblb__wfwuu = {fiad__nygn.name for fiad__nygn in stmt.
            out_data_vars.values()}
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            ncblb__wfwuu.update({fiad__nygn.name for fiad__nygn in stmt.
                out_key_arrs})
            ncblb__wfwuu.update({fiad__nygn.name for fiad__nygn in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        qklb__sgnf = guard(find_callname, func_ir, stmt.value)
        if qklb__sgnf in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'),
            ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            ncblb__wfwuu.add(stmt.value.args[0].name)
    return ncblb__wfwuu


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
        xja__pmgou = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        ynhrt__vpu = xja__pmgou.format(self, msg)
        self.args = ynhrt__vpu,
    else:
        xja__pmgou = _termcolor.errmsg('{0}')
        ynhrt__vpu = xja__pmgou.format(self)
        self.args = ynhrt__vpu,
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
        for qbp__xxr in options['distributed']:
            dist_spec[qbp__xxr] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for qbp__xxr in options['distributed_block']:
            dist_spec[qbp__xxr] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    shd__mbn = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, czsy__ujywe in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(czsy__ujywe)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    iuwbb__jjpyn = {}
    for eouty__kshnd in reversed(inspect.getmro(cls)):
        iuwbb__jjpyn.update(eouty__kshnd.__dict__)
    zbsi__nyt, umrjp__hnv, kbpr__gisf, sqjq__kumv = {}, {}, {}, {}
    for zswl__shpoc, fiad__nygn in iuwbb__jjpyn.items():
        if isinstance(fiad__nygn, pytypes.FunctionType):
            zbsi__nyt[zswl__shpoc] = fiad__nygn
        elif isinstance(fiad__nygn, property):
            umrjp__hnv[zswl__shpoc] = fiad__nygn
        elif isinstance(fiad__nygn, staticmethod):
            kbpr__gisf[zswl__shpoc] = fiad__nygn
        else:
            sqjq__kumv[zswl__shpoc] = fiad__nygn
    afxc__gwot = (set(zbsi__nyt) | set(umrjp__hnv) | set(kbpr__gisf)) & set(
        spec)
    if afxc__gwot:
        raise NameError('name shadowing: {0}'.format(', '.join(afxc__gwot)))
    mlcd__sbgo = sqjq__kumv.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(sqjq__kumv)
    if sqjq__kumv:
        msg = 'class members are not yet supported: {0}'
        cwsta__paabf = ', '.join(sqjq__kumv.keys())
        raise TypeError(msg.format(cwsta__paabf))
    for zswl__shpoc, fiad__nygn in umrjp__hnv.items():
        if fiad__nygn.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(zswl__shpoc)
                )
    jit_methods = {zswl__shpoc: bodo.jit(returns_maybe_distributed=shd__mbn
        )(fiad__nygn) for zswl__shpoc, fiad__nygn in zbsi__nyt.items()}
    jit_props = {}
    for zswl__shpoc, fiad__nygn in umrjp__hnv.items():
        jepp__njbk = {}
        if fiad__nygn.fget:
            jepp__njbk['get'] = bodo.jit(fiad__nygn.fget)
        if fiad__nygn.fset:
            jepp__njbk['set'] = bodo.jit(fiad__nygn.fset)
        jit_props[zswl__shpoc] = jepp__njbk
    jit_static_methods = {zswl__shpoc: bodo.jit(fiad__nygn.__func__) for 
        zswl__shpoc, fiad__nygn in kbpr__gisf.items()}
    yjigh__xdxml = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    dtn__wnu = dict(class_type=yjigh__xdxml, __doc__=mlcd__sbgo)
    dtn__wnu.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), dtn__wnu)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, yjigh__xdxml)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(yjigh__xdxml, typingctx, targetctx).register()
    as_numba_type.register(cls, yjigh__xdxml.instance_type)
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
    dsj__dpqv = ','.join('{0}:{1}'.format(zswl__shpoc, fiad__nygn) for 
        zswl__shpoc, fiad__nygn in struct.items())
    zzl__uld = ','.join('{0}:{1}'.format(zswl__shpoc, fiad__nygn) for 
        zswl__shpoc, fiad__nygn in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), dsj__dpqv, zzl__uld)
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
    xrn__ime = numba.core.typeinfer.fold_arg_vars(typevars, self.args, self
        .vararg, self.kws)
    if xrn__ime is None:
        return
    exmb__klgm, wjow__ween = xrn__ime
    for a in itertools.chain(exmb__klgm, wjow__ween.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, exmb__klgm, wjow__ween)
    except ForceLiteralArg as e:
        fxn__opr = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(fxn__opr, self.kws)
        fjjs__ymiom = set()
        rufjd__esey = set()
        rulfp__iegv = {}
        for mdnd__hyh in e.requested_args:
            iqmbm__xqi = typeinfer.func_ir.get_definition(folded[mdnd__hyh])
            if isinstance(iqmbm__xqi, ir.Arg):
                fjjs__ymiom.add(iqmbm__xqi.index)
                if iqmbm__xqi.index in e.file_infos:
                    rulfp__iegv[iqmbm__xqi.index] = e.file_infos[iqmbm__xqi
                        .index]
            else:
                rufjd__esey.add(mdnd__hyh)
        if rufjd__esey:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif fjjs__ymiom:
            raise ForceLiteralArg(fjjs__ymiom, loc=self.loc, file_infos=
                rulfp__iegv)
    if sig is None:
        ljyf__fuya = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in exmb__klgm]
        args += [('%s=%s' % (zswl__shpoc, fiad__nygn)) for zswl__shpoc,
            fiad__nygn in sorted(wjow__ween.items())]
        tzymr__otta = ljyf__fuya.format(fnty, ', '.join(map(str, args)))
        qwv__frlj = context.explain_function_type(fnty)
        msg = '\n'.join([tzymr__otta, qwv__frlj])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        odfqa__ykq = context.unify_pairs(sig.recvr, fnty.this)
        if odfqa__ykq is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if odfqa__ykq is not None and odfqa__ykq.is_precise():
            hlp__wjjzt = fnty.copy(this=odfqa__ykq)
            typeinfer.propagate_refined_type(self.func, hlp__wjjzt)
    if not sig.return_type.is_precise():
        sduol__hrhzq = typevars[self.target]
        if sduol__hrhzq.defined:
            mdit__nlp = sduol__hrhzq.getone()
            if context.unify_pairs(mdit__nlp, sig.return_type) == mdit__nlp:
                sig = sig.replace(return_type=mdit__nlp)
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
        fmbg__mdmgo = '*other* must be a {} but got a {} instead'
        raise TypeError(fmbg__mdmgo.format(ForceLiteralArg, type(other)))
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
    hucv__hoohy = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for zswl__shpoc, fiad__nygn in kwargs.items():
        fjxwc__qbr = None
        try:
            pxn__mhfw = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var(
                'dummy'), loc)
            func_ir._definitions[pxn__mhfw.name] = [fiad__nygn]
            fjxwc__qbr = get_const_value_inner(func_ir, pxn__mhfw)
            func_ir._definitions.pop(pxn__mhfw.name)
            if isinstance(fjxwc__qbr, str):
                fjxwc__qbr = sigutils._parse_signature_string(fjxwc__qbr)
            if isinstance(fjxwc__qbr, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {zswl__shpoc} is annotated as type class {fjxwc__qbr}."""
                    )
            assert isinstance(fjxwc__qbr, types.Type)
            if isinstance(fjxwc__qbr, (types.List, types.Set)):
                fjxwc__qbr = fjxwc__qbr.copy(reflected=False)
            hucv__hoohy[zswl__shpoc] = fjxwc__qbr
        except BodoError as lzky__uvh:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(fjxwc__qbr, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(fiad__nygn, ir.Global):
                    msg = f'Global {fiad__nygn.name!r} is not defined.'
                if isinstance(fiad__nygn, ir.FreeVar):
                    msg = f'Freevar {fiad__nygn.name!r} is not defined.'
            if isinstance(fiad__nygn, ir.Expr) and fiad__nygn.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=zswl__shpoc, msg=msg, loc=loc)
    for name, typ in hucv__hoohy.items():
        self._legalize_arg_type(name, typ, loc)
    return hucv__hoohy


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
    epc__cwlq = inst.arg
    assert epc__cwlq > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(epc__cwlq)]))
    tmps = [state.make_temp() for _ in range(epc__cwlq - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    atxxl__ngk = ir.Global('format', format, loc=self.loc)
    self.store(value=atxxl__ngk, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    lmu__prxn = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=lmu__prxn, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    epc__cwlq = inst.arg
    assert epc__cwlq > 0, 'invalid BUILD_STRING count'
    tapz__ymtc = self.get(strings[0])
    for other, mktn__rectd in zip(strings[1:], tmps):
        other = self.get(other)
        hry__hlfb = ir.Expr.binop(operator.add, lhs=tapz__ymtc, rhs=other,
            loc=self.loc)
        self.store(hry__hlfb, mktn__rectd)
        tapz__ymtc = self.get(mktn__rectd)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    hptoo__elgac = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, hptoo__elgac])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    sevtc__owy = mk_unique_var(f'{var_name}')
    yjv__xmuo = sevtc__owy.replace('<', '_').replace('>', '_')
    yjv__xmuo = yjv__xmuo.replace('.', '_').replace('$', '_v')
    return yjv__xmuo


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
                heaf__tsa = get_overload_const_str(val2)
                if heaf__tsa != 'ns':
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
        tnxsl__zbc = states['defmap']
        if len(tnxsl__zbc) == 0:
            wzvi__ojyy = assign.target
            numba.core.ssa._logger.debug('first assign: %s', wzvi__ojyy)
            if wzvi__ojyy.name not in scope.localvars:
                wzvi__ojyy = scope.define(assign.target.name, loc=assign.loc)
        else:
            wzvi__ojyy = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=wzvi__ojyy, value=assign.value, loc=
            assign.loc)
        tnxsl__zbc[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    lom__ynu = []
    for zswl__shpoc, fiad__nygn in typing.npydecl.registry.globals:
        if zswl__shpoc == func:
            lom__ynu.append(fiad__nygn)
    for zswl__shpoc, fiad__nygn in typing.templates.builtin_registry.globals:
        if zswl__shpoc == func:
            lom__ynu.append(fiad__nygn)
    if len(lom__ynu) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return lom__ynu


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    fooh__izjtj = {}
    nhgwm__tmjfw = find_topo_order(blocks)
    zzoj__rccty = {}
    for rpoaa__dzrzf in nhgwm__tmjfw:
        block = blocks[rpoaa__dzrzf]
        yqlg__zem = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                zmp__otx = stmt.target.name
                cvo__yrnn = stmt.value
                if (cvo__yrnn.op == 'getattr' and cvo__yrnn.attr in
                    arr_math and isinstance(typemap[cvo__yrnn.value.name],
                    types.npytypes.Array)):
                    cvo__yrnn = stmt.value
                    mvra__oipsu = cvo__yrnn.value
                    fooh__izjtj[zmp__otx] = mvra__oipsu
                    scope = mvra__oipsu.scope
                    loc = mvra__oipsu.loc
                    aebq__qmjoc = ir.Var(scope, mk_unique_var('$np_g_var'), loc
                        )
                    typemap[aebq__qmjoc.name] = types.misc.Module(numpy)
                    otcqq__wvor = ir.Global('np', numpy, loc)
                    wypk__zsf = ir.Assign(otcqq__wvor, aebq__qmjoc, loc)
                    cvo__yrnn.value = aebq__qmjoc
                    yqlg__zem.append(wypk__zsf)
                    func_ir._definitions[aebq__qmjoc.name] = [otcqq__wvor]
                    func = getattr(numpy, cvo__yrnn.attr)
                    wgjf__hvaf = get_np_ufunc_typ_lst(func)
                    zzoj__rccty[zmp__otx] = wgjf__hvaf
                if (cvo__yrnn.op == 'call' and cvo__yrnn.func.name in
                    fooh__izjtj):
                    mvra__oipsu = fooh__izjtj[cvo__yrnn.func.name]
                    xuiiy__sdk = calltypes.pop(cvo__yrnn)
                    owoqi__gdxim = xuiiy__sdk.args[:len(cvo__yrnn.args)]
                    twtj__xyo = {name: typemap[fiad__nygn.name] for name,
                        fiad__nygn in cvo__yrnn.kws}
                    gtxg__xdev = zzoj__rccty[cvo__yrnn.func.name]
                    spxoz__amndx = None
                    for cib__kci in gtxg__xdev:
                        try:
                            spxoz__amndx = cib__kci.get_call_type(typingctx,
                                [typemap[mvra__oipsu.name]] + list(
                                owoqi__gdxim), twtj__xyo)
                            typemap.pop(cvo__yrnn.func.name)
                            typemap[cvo__yrnn.func.name] = cib__kci
                            calltypes[cvo__yrnn] = spxoz__amndx
                            break
                        except Exception as lzky__uvh:
                            pass
                    if spxoz__amndx is None:
                        raise TypeError(
                            f'No valid template found for {cvo__yrnn.func.name}'
                            )
                    cvo__yrnn.args = [mvra__oipsu] + cvo__yrnn.args
            yqlg__zem.append(stmt)
        block.body = yqlg__zem


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    jyk__ohrk = ufunc.nin
    fhkh__dlhqq = ufunc.nout
    mke__zgx = ufunc.nargs
    assert mke__zgx == jyk__ohrk + fhkh__dlhqq
    if len(args) < jyk__ohrk:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), jyk__ohrk))
    if len(args) > mke__zgx:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), mke__zgx))
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    qanhk__smq = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    whmt__kbv = max(qanhk__smq)
    djzmu__oear = args[jyk__ohrk:]
    if not all(gyff__rqwpn == whmt__kbv for gyff__rqwpn in qanhk__smq[
        jyk__ohrk:]):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(gvrp__oeq, types.ArrayCompatible) and not
        isinstance(gvrp__oeq, types.Bytes) for gvrp__oeq in djzmu__oear):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(gvrp__oeq.mutable for gvrp__oeq in djzmu__oear):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    kdrb__zyppj = [(x.dtype if isinstance(x, types.ArrayCompatible) and not
        isinstance(x, types.Bytes) else x) for x in args]
    usvp__rwbkb = None
    if whmt__kbv > 0 and len(djzmu__oear) < ufunc.nout:
        usvp__rwbkb = 'C'
        fhxqw__kwim = [(x.layout if isinstance(x, types.ArrayCompatible) and
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in fhxqw__kwim and 'F' in fhxqw__kwim:
            usvp__rwbkb = 'F'
    return kdrb__zyppj, djzmu__oear, whmt__kbv, usvp__rwbkb


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
        omj__xsicf = 'Dict.key_type cannot be of type {}'
        raise TypingError(omj__xsicf.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        omj__xsicf = 'Dict.value_type cannot be of type {}'
        raise TypingError(omj__xsicf.format(valty))
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
    dxxlj__pgd = self.context, tuple(args), tuple(kws.items())
    try:
        rubar__rulo, args = self._impl_cache[dxxlj__pgd]
        return rubar__rulo, args
    except KeyError as lzky__uvh:
        pass
    rubar__rulo, args = self._build_impl(dxxlj__pgd, args, kws)
    return rubar__rulo, args


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
        zrvjb__oxpsb = find_topo_order(parfor.loop_body)
    jop__fwzai = zrvjb__oxpsb[0]
    iyvzw__aofim = {}
    _update_parfor_get_setitems(parfor.loop_body[jop__fwzai].body, parfor.
        index_var, alias_map, iyvzw__aofim, lives_n_aliases)
    vue__kbwm = set(iyvzw__aofim.keys())
    for jlz__opnui in zrvjb__oxpsb:
        if jlz__opnui == jop__fwzai:
            continue
        for stmt in parfor.loop_body[jlz__opnui].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            anlca__bcge = set(fiad__nygn.name for fiad__nygn in stmt.
                list_vars())
            qgxnl__wzoap = anlca__bcge & vue__kbwm
            for a in qgxnl__wzoap:
                iyvzw__aofim.pop(a, None)
    for jlz__opnui in zrvjb__oxpsb:
        if jlz__opnui == jop__fwzai:
            continue
        block = parfor.loop_body[jlz__opnui]
        lpne__euf = iyvzw__aofim.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            lpne__euf, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    kret__wamus = max(blocks.keys())
    qlw__vfo, jdqxj__wzvo = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    zhcn__kttsb = ir.Jump(qlw__vfo, ir.Loc('parfors_dummy', -1))
    blocks[kret__wamus].body.append(zhcn__kttsb)
    llz__tgdk = compute_cfg_from_blocks(blocks)
    zsj__iwb = compute_use_defs(blocks)
    uxen__ruh = compute_live_map(llz__tgdk, blocks, zsj__iwb.usemap,
        zsj__iwb.defmap)
    alias_set = set(alias_map.keys())
    for rpoaa__dzrzf, block in blocks.items():
        yqlg__zem = []
        ihp__ypdvm = {fiad__nygn.name for fiad__nygn in block.terminator.
            list_vars()}
        for oqbtp__vhfw, cnmgh__brjtm in llz__tgdk.successors(rpoaa__dzrzf):
            ihp__ypdvm |= uxen__ruh[oqbtp__vhfw]
        for stmt in reversed(block.body):
            tytw__ogt = ihp__ypdvm & alias_set
            for fiad__nygn in tytw__ogt:
                ihp__ypdvm |= alias_map[fiad__nygn]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in ihp__ypdvm and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                qklb__sgnf = guard(find_callname, func_ir, stmt.value)
                if qklb__sgnf == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in ihp__ypdvm and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            ihp__ypdvm |= {fiad__nygn.name for fiad__nygn in stmt.list_vars()}
            yqlg__zem.append(stmt)
        yqlg__zem.reverse()
        block.body = yqlg__zem
    typemap.pop(jdqxj__wzvo.name)
    blocks[kret__wamus].body.pop()

    def trim_empty_parfor_branches(parfor):
        flgp__qeayb = False
        blocks = parfor.loop_body.copy()
        for rpoaa__dzrzf, block in blocks.items():
            if len(block.body):
                uycc__xsh = block.body[-1]
                if isinstance(uycc__xsh, ir.Branch):
                    if len(blocks[uycc__xsh.truebr].body) == 1 and len(blocks
                        [uycc__xsh.falsebr].body) == 1:
                        dvpot__xlbq = blocks[uycc__xsh.truebr].body[0]
                        ebsmu__jvjtl = blocks[uycc__xsh.falsebr].body[0]
                        if isinstance(dvpot__xlbq, ir.Jump) and isinstance(
                            ebsmu__jvjtl, ir.Jump
                            ) and dvpot__xlbq.target == ebsmu__jvjtl.target:
                            parfor.loop_body[rpoaa__dzrzf].body[-1] = ir.Jump(
                                dvpot__xlbq.target, uycc__xsh.loc)
                            flgp__qeayb = True
                    elif len(blocks[uycc__xsh.truebr].body) == 1:
                        dvpot__xlbq = blocks[uycc__xsh.truebr].body[0]
                        if isinstance(dvpot__xlbq, ir.Jump
                            ) and dvpot__xlbq.target == uycc__xsh.falsebr:
                            parfor.loop_body[rpoaa__dzrzf].body[-1] = ir.Jump(
                                dvpot__xlbq.target, uycc__xsh.loc)
                            flgp__qeayb = True
                    elif len(blocks[uycc__xsh.falsebr].body) == 1:
                        ebsmu__jvjtl = blocks[uycc__xsh.falsebr].body[0]
                        if isinstance(ebsmu__jvjtl, ir.Jump
                            ) and ebsmu__jvjtl.target == uycc__xsh.truebr:
                            parfor.loop_body[rpoaa__dzrzf].body[-1] = ir.Jump(
                                ebsmu__jvjtl.target, uycc__xsh.loc)
                            flgp__qeayb = True
        return flgp__qeayb
    flgp__qeayb = True
    while flgp__qeayb:
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
        flgp__qeayb = trim_empty_parfor_branches(parfor)
    mrep__unwp = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        mrep__unwp &= len(block.body) == 0
    if mrep__unwp:
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
    hsqsc__xuy = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                hsqsc__xuy += 1
                parfor = stmt
                ekl__ubv = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = ekl__ubv.scope
                loc = ir.Loc('parfors_dummy', -1)
                vmju__wewut = ir.Var(scope, mk_unique_var('$const'), loc)
                ekl__ubv.body.append(ir.Assign(ir.Const(0, loc),
                    vmju__wewut, loc))
                ekl__ubv.body.append(ir.Return(vmju__wewut, loc))
                llz__tgdk = compute_cfg_from_blocks(parfor.loop_body)
                for sqjdm__olxvc in llz__tgdk.dead_nodes():
                    del parfor.loop_body[sqjdm__olxvc]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                ekl__ubv = parfor.loop_body[max(parfor.loop_body.keys())]
                ekl__ubv.body.pop()
                ekl__ubv.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return hsqsc__xuy


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
            ukibr__fvp = self.overloads.get(tuple(args))
            if ukibr__fvp is not None:
                return ukibr__fvp.entry_point
            self._pre_compile(args, return_type, flags)
            qfgvp__xcrzt = self.func_ir
            zcem__cbkk = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=zcem__cbkk):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=qfgvp__xcrzt, args=
                    args, return_type=return_type, flags=flags, locals=self
                    .locals, lifted=(), lifted_from=self.lifted_from,
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
        ypzn__yvv = copy.deepcopy(flags)
        ypzn__yvv.no_rewrites = True

        def compile_local(the_ir, the_flags):
            mwo__joj = pipeline_class(typingctx, targetctx, library, args,
                return_type, the_flags, locals)
            return mwo__joj.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        erblg__igynk = compile_local(func_ir, ypzn__yvv)
        jtl__yvp = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    jtl__yvp = compile_local(func_ir, flags)
                except Exception as lzky__uvh:
                    pass
        if jtl__yvp is not None:
            cres = jtl__yvp
        else:
            cres = erblg__igynk
        return cres
    else:
        mwo__joj = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return mwo__joj.compile_ir(func_ir=func_ir, lifted=lifted,
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
    hioet__izvf = self.get_data_type(typ.dtype)
    efmxr__jsc = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        efmxr__jsc):
        dhdpq__nld = ary.ctypes.data
        rwjbu__zjnxp = self.add_dynamic_addr(builder, dhdpq__nld, info=str(
            type(dhdpq__nld)))
        gmssn__agy = self.add_dynamic_addr(builder, id(ary), info=str(type(
            ary)))
        self.global_arrays.append(ary)
    else:
        lts__gnvu = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            lts__gnvu = lts__gnvu.view('int64')
        xlw__iebua = Constant.array(Type.int(8), bytearray(lts__gnvu.data))
        rwjbu__zjnxp = cgutils.global_constant(builder, '.const.array.data',
            xlw__iebua)
        rwjbu__zjnxp.align = self.get_abi_alignment(hioet__izvf)
        gmssn__agy = None
    qnmz__xxigo = self.get_value_type(types.intp)
    agt__mwc = [self.get_constant(types.intp, rja__kawv) for rja__kawv in
        ary.shape]
    bmd__bwaiw = Constant.array(qnmz__xxigo, agt__mwc)
    pmedk__ypmx = [self.get_constant(types.intp, rja__kawv) for rja__kawv in
        ary.strides]
    qbg__ggqc = Constant.array(qnmz__xxigo, pmedk__ypmx)
    nwkqi__rkplh = self.get_constant(types.intp, ary.dtype.itemsize)
    jldr__szz = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        jldr__szz, nwkqi__rkplh, rwjbu__zjnxp.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), bmd__bwaiw, qbg__ggqc])


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
    ibi__ztw = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    arh__ubj = lir.Function(module, ibi__ztw, name='nrt_atomic_{0}'.format(op))
    [uxh__fhcy] = arh__ubj.args
    wozd__qhqh = arh__ubj.append_basic_block()
    builder = lir.IRBuilder(wozd__qhqh)
    opuv__wxovr = lir.Constant(_word_type, 1)
    if False:
        ife__vpvf = builder.atomic_rmw(op, uxh__fhcy, opuv__wxovr, ordering
            =ordering)
        res = getattr(builder, op)(ife__vpvf, opuv__wxovr)
        builder.ret(res)
    else:
        ife__vpvf = builder.load(uxh__fhcy)
        sboio__fhrg = getattr(builder, op)(ife__vpvf, opuv__wxovr)
        ahw__eyk = builder.icmp_signed('!=', ife__vpvf, lir.Constant(
            ife__vpvf.type, -1))
        with cgutils.if_likely(builder, ahw__eyk):
            builder.store(sboio__fhrg, uxh__fhcy)
        builder.ret(sboio__fhrg)
    return arh__ubj


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
        ewvoj__gocqh = state.targetctx.codegen()
        state.library = ewvoj__gocqh.create_library(state.func_id.func_qualname
            )
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    aapy__exjq = state.func_ir
    typemap = state.typemap
    aes__eynr = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    muuw__dogr = state.metadata
    tij__pvcvc = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        yua__lhrl = (funcdesc.PythonFunctionDescriptor.
            from_specialized_function(aapy__exjq, typemap, aes__eynr,
            calltypes, mangler=targetctx.mangler, inline=flags.forceinline,
            noalias=flags.noalias, abi_tags=[flags.get_mangle_string()]))
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            dbe__ldigc = lowering.Lower(targetctx, library, yua__lhrl,
                aapy__exjq, metadata=muuw__dogr)
            dbe__ldigc.lower()
            if not flags.no_cpython_wrapper:
                dbe__ldigc.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(aes__eynr, (types.Optional, types.Generator)
                        ):
                        pass
                    else:
                        dbe__ldigc.create_cfunc_wrapper()
            aatzx__utv = dbe__ldigc.env
            lkerb__ieufc = dbe__ldigc.call_helper
            del dbe__ldigc
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(yua__lhrl, lkerb__ieufc, cfunc=None,
                env=aatzx__utv)
        else:
            skq__pooa = targetctx.get_executable(library, yua__lhrl, aatzx__utv
                )
            targetctx.insert_user_function(skq__pooa, yua__lhrl, [library])
            state['cr'] = _LowerResult(yua__lhrl, lkerb__ieufc, cfunc=
                skq__pooa, env=aatzx__utv)
        muuw__dogr['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        rbkfw__oyr = llvm.passmanagers.dump_refprune_stats()
        muuw__dogr['prune_stats'] = rbkfw__oyr - tij__pvcvc
        muuw__dogr['llvm_pass_timings'] = library.recorded_timings
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
        wgahe__zns = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, wgahe__zns),
            likely=False):
            c.builder.store(cgutils.true_bit, errorptr)
            xwlig__dqqxv.do_break()
        ffip__namom = c.builder.icmp_signed('!=', wgahe__zns, expected_typobj)
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(ffip__namom, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, wgahe__zns)
                c.pyapi.decref(wgahe__zns)
                xwlig__dqqxv.do_break()
        c.pyapi.decref(wgahe__zns)
    obj__fky, list = listobj.ListInstance.allocate_ex(c.context, c.builder,
        typ, size)
    with c.builder.if_else(obj__fky, likely=True) as (czcyx__ecr, uoim__usivy):
        with czcyx__ecr:
            list.size = size
            hqhgi__fpmq = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                hqhgi__fpmq), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        hqhgi__fpmq))
                    with cgutils.for_range(c.builder, size) as xwlig__dqqxv:
                        itemobj = c.pyapi.list_getitem(obj, xwlig__dqqxv.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        jbpie__zwfg = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(jbpie__zwfg.is_error, likely
                            =False):
                            c.builder.store(cgutils.true_bit, errorptr)
                            xwlig__dqqxv.do_break()
                        list.setitem(xwlig__dqqxv.index, jbpie__zwfg.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with uoim__usivy:
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
    xvyhu__slpnr, uijpg__cggpl, zchy__tpmq, pek__obfc, vao__uvwn = (
        compile_time_get_string_data(literal_string))
    qto__dna = builder.module
    gv = context.insert_const_bytes(qto__dna, xvyhu__slpnr)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        uijpg__cggpl), context.get_constant(types.int32, zchy__tpmq),
        context.get_constant(types.uint32, pek__obfc), context.get_constant
        (_Py_hash_t, -1), context.get_constant_null(types.MemInfoPointer(
        types.voidptr)), context.get_constant_null(types.pyobject)])


if _check_numba_change:
    lines = inspect.getsource(numba.cpython.unicode.make_string_from_constant)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '525bd507383e06152763e2f046dae246cd60aba027184f50ef0fc9a80d4cd7fa':
        warnings.warn(
            'numba.cpython.unicode.make_string_from_constant has changed')
numba.cpython.unicode.make_string_from_constant = make_string_from_constant


def parse_shape(shape):
    jyxgy__ldlh = None
    if isinstance(shape, types.Integer):
        jyxgy__ldlh = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(rja__kawv, (types.Integer, types.IntEnumMember)) for
            rja__kawv in shape):
            jyxgy__ldlh = len(shape)
    return jyxgy__ldlh


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
            jyxgy__ldlh = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if jyxgy__ldlh == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(
                    jyxgy__ldlh))
        else:
            return name,
    elif isinstance(obj, ir.Const):
        if isinstance(obj.value, tuple):
            return obj.value
        else:
            return obj.value,
    elif isinstance(obj, tuple):

        def get_names(x):
            dzi__fwylo = self._get_names(x)
            if len(dzi__fwylo) != 0:
                return dzi__fwylo[0]
            return dzi__fwylo
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    dzi__fwylo = self._get_names(obj)
    if len(dzi__fwylo) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(dzi__fwylo[0])


def get_equiv_set(self, obj):
    dzi__fwylo = self._get_names(obj)
    if len(dzi__fwylo) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(dzi__fwylo[0])


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
    knxf__pzg = []
    for kpe__ffkbi in func_ir.arg_names:
        if kpe__ffkbi in typemap and isinstance(typemap[kpe__ffkbi], types.
            containers.UniTuple) and typemap[kpe__ffkbi].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(kpe__ffkbi))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for cbir__duj in func_ir.blocks.values():
        for stmt in cbir__duj.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    mjr__fjh = getattr(val, 'code', None)
                    if mjr__fjh is not None:
                        if getattr(val, 'closure', None) is not None:
                            tjcwd__pozwv = (
                                '<creating a function from a closure>')
                            hry__hlfb = ''
                        else:
                            tjcwd__pozwv = mjr__fjh.co_name
                            hry__hlfb = '(%s) ' % tjcwd__pozwv
                    else:
                        tjcwd__pozwv = '<could not ascertain use case>'
                        hry__hlfb = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (tjcwd__pozwv, hry__hlfb))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                gmdlr__mzh = False
                if isinstance(val, pytypes.FunctionType):
                    gmdlr__mzh = val in {numba.gdb, numba.gdb_init}
                if not gmdlr__mzh:
                    gmdlr__mzh = getattr(val, '_name', '') == 'gdb_internal'
                if gmdlr__mzh:
                    knxf__pzg.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    uih__qkoez = func_ir.get_definition(var)
                    pivq__ysp = guard(find_callname, func_ir, uih__qkoez)
                    if pivq__ysp and pivq__ysp[1] == 'numpy':
                        ty = getattr(numpy, pivq__ysp[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    bgkj__jxeq = '' if var.startswith('$') else "'{}' ".format(
                        var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(bgkj__jxeq), loc=stmt.loc)
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
    if len(knxf__pzg) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        tymgm__frsax = '\n'.join([x.strformat() for x in knxf__pzg])
        raise errors.UnsupportedError(msg % tymgm__frsax)


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
    zswl__shpoc, fiad__nygn = next(iter(val.items()))
    obs__fjdkt = typeof_impl(zswl__shpoc, c)
    nnoa__hcr = typeof_impl(fiad__nygn, c)
    if obs__fjdkt is None or nnoa__hcr is None:
        raise ValueError(
            f'Cannot type dict element type {type(zswl__shpoc)}, {type(fiad__nygn)}'
            )
    return types.DictType(obs__fjdkt, nnoa__hcr)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    nslt__jvby = cgutils.alloca_once_value(c.builder, val)
    vkxq__pbl = c.pyapi.object_hasattr_string(val, '_opaque')
    uyjty__nxoe = c.builder.icmp_unsigned('==', vkxq__pbl, lir.Constant(
        vkxq__pbl.type, 0))
    penun__sdw = typ.key_type
    syng__lfdvb = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(penun__sdw, syng__lfdvb)

    def copy_dict(out_dict, in_dict):
        for zswl__shpoc, fiad__nygn in in_dict.items():
            out_dict[zswl__shpoc] = fiad__nygn
    with c.builder.if_then(uyjty__nxoe):
        nujvb__jgc = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        harby__qlq = c.pyapi.call_function_objargs(nujvb__jgc, [])
        uvzog__ulqr = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(uvzog__ulqr, [harby__qlq, val])
        c.builder.store(harby__qlq, nslt__jvby)
    val = c.builder.load(nslt__jvby)
    zlp__ycnk = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    zwpli__pez = c.pyapi.object_type(val)
    nztwb__nshg = c.builder.icmp_unsigned('==', zwpli__pez, zlp__ycnk)
    with c.builder.if_else(nztwb__nshg) as (rllq__zkxc, tvdg__rcxzq):
        with rllq__zkxc:
            ahnx__kiv = c.pyapi.object_getattr_string(val, '_opaque')
            zoqs__jia = types.MemInfoPointer(types.voidptr)
            jbpie__zwfg = c.unbox(zoqs__jia, ahnx__kiv)
            mi = jbpie__zwfg.value
            zfuc__jmirw = zoqs__jia, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *zfuc__jmirw)
            rjtf__ffu = context.get_constant_null(zfuc__jmirw[1])
            args = mi, rjtf__ffu
            rsnw__ytqt, cjeld__mmy = c.pyapi.call_jit_code(convert, sig, args)
            c.context.nrt.decref(c.builder, typ, cjeld__mmy)
            c.pyapi.decref(ahnx__kiv)
            zqyg__udi = c.builder.basic_block
        with tvdg__rcxzq:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", zwpli__pez, zlp__ycnk)
            fgzgc__hqa = c.builder.basic_block
    ior__hfbk = c.builder.phi(cjeld__mmy.type)
    paqm__oekf = c.builder.phi(rsnw__ytqt.type)
    ior__hfbk.add_incoming(cjeld__mmy, zqyg__udi)
    ior__hfbk.add_incoming(cjeld__mmy.type(None), fgzgc__hqa)
    paqm__oekf.add_incoming(rsnw__ytqt, zqyg__udi)
    paqm__oekf.add_incoming(cgutils.true_bit, fgzgc__hqa)
    c.pyapi.decref(zlp__ycnk)
    c.pyapi.decref(zwpli__pez)
    with c.builder.if_then(uyjty__nxoe):
        c.pyapi.decref(val)
    return NativeValue(ior__hfbk, is_error=paqm__oekf)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, jxnhp__vytxe = args
    if isinstance(a, types.List) and isinstance(jxnhp__vytxe, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(jxnhp__vytxe, types.List):
        return signature(jxnhp__vytxe, types.intp, jxnhp__vytxe)


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
        ypvbh__grhn, eaa__vmdil = 0, 1
    else:
        ypvbh__grhn, eaa__vmdil = 1, 0
    rbec__rne = ListInstance(context, builder, sig.args[ypvbh__grhn], args[
        ypvbh__grhn])
    kvdob__jyiwb = rbec__rne.size
    oylo__byqbj = args[eaa__vmdil]
    hqhgi__fpmq = lir.Constant(oylo__byqbj.type, 0)
    oylo__byqbj = builder.select(cgutils.is_neg_int(builder, oylo__byqbj),
        hqhgi__fpmq, oylo__byqbj)
    jldr__szz = builder.mul(oylo__byqbj, kvdob__jyiwb)
    fetu__uilc = ListInstance.allocate(context, builder, sig.return_type,
        jldr__szz)
    fetu__uilc.size = jldr__szz
    with cgutils.for_range_slice(builder, hqhgi__fpmq, jldr__szz,
        kvdob__jyiwb, inc=True) as (wcj__plt, _):
        with cgutils.for_range(builder, kvdob__jyiwb) as xwlig__dqqxv:
            value = rbec__rne.getitem(xwlig__dqqxv.index)
            fetu__uilc.setitem(builder.add(xwlig__dqqxv.index, wcj__plt),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, fetu__uilc.value
        )


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    jldr__szz = payload.used
    listobj = c.pyapi.list_new(jldr__szz)
    obj__fky = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(obj__fky, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(jldr__szz.
            type, 0))
        with payload._iterate() as xwlig__dqqxv:
            i = c.builder.load(index)
            item = xwlig__dqqxv.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return obj__fky, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    pdyid__vtyh = h.type
    czkg__nyg = self.mask
    dtype = self._ty.dtype
    hhu__afa = context.typing_context
    fnty = hhu__afa.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(hhu__afa, (dtype, dtype), {})
    xvzio__ubaw = context.get_function(fnty, sig)
    ftvq__acmmk = ir.Constant(pdyid__vtyh, 1)
    uxd__iqxrp = ir.Constant(pdyid__vtyh, 5)
    huzv__npwz = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, czkg__nyg))
    if for_insert:
        jbyw__pcltq = czkg__nyg.type(-1)
        iij__ybp = cgutils.alloca_once_value(builder, jbyw__pcltq)
    aate__ggx = builder.append_basic_block('lookup.body')
    ajzxt__xqu = builder.append_basic_block('lookup.found')
    abfto__mobee = builder.append_basic_block('lookup.not_found')
    wly__aaevg = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        isff__uhsrb = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, isff__uhsrb)):
            yfb__kgm = xvzio__ubaw(builder, (item, entry.key))
            with builder.if_then(yfb__kgm):
                builder.branch(ajzxt__xqu)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, isff__uhsrb)):
            builder.branch(abfto__mobee)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, isff__uhsrb)):
                sgh__bmsvd = builder.load(iij__ybp)
                sgh__bmsvd = builder.select(builder.icmp_unsigned('==',
                    sgh__bmsvd, jbyw__pcltq), i, sgh__bmsvd)
                builder.store(sgh__bmsvd, iij__ybp)
    with cgutils.for_range(builder, ir.Constant(pdyid__vtyh, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, ftvq__acmmk)
        i = builder.and_(i, czkg__nyg)
        builder.store(i, index)
    builder.branch(aate__ggx)
    with builder.goto_block(aate__ggx):
        i = builder.load(index)
        check_entry(i)
        aunkt__eqfs = builder.load(huzv__npwz)
        aunkt__eqfs = builder.lshr(aunkt__eqfs, uxd__iqxrp)
        i = builder.add(ftvq__acmmk, builder.mul(i, uxd__iqxrp))
        i = builder.and_(czkg__nyg, builder.add(i, aunkt__eqfs))
        builder.store(i, index)
        builder.store(aunkt__eqfs, huzv__npwz)
        builder.branch(aate__ggx)
    with builder.goto_block(abfto__mobee):
        if for_insert:
            i = builder.load(index)
            sgh__bmsvd = builder.load(iij__ybp)
            i = builder.select(builder.icmp_unsigned('==', sgh__bmsvd,
                jbyw__pcltq), i, sgh__bmsvd)
            builder.store(i, index)
        builder.branch(wly__aaevg)
    with builder.goto_block(ajzxt__xqu):
        builder.branch(wly__aaevg)
    builder.position_at_end(wly__aaevg)
    gmdlr__mzh = builder.phi(ir.IntType(1), 'found')
    gmdlr__mzh.add_incoming(cgutils.true_bit, ajzxt__xqu)
    gmdlr__mzh.add_incoming(cgutils.false_bit, abfto__mobee)
    return gmdlr__mzh, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    bkwek__symya = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    lqjar__ceno = payload.used
    ftvq__acmmk = ir.Constant(lqjar__ceno.type, 1)
    lqjar__ceno = payload.used = builder.add(lqjar__ceno, ftvq__acmmk)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, bkwek__symya), likely=True):
        payload.fill = builder.add(payload.fill, ftvq__acmmk)
    if do_resize:
        self.upsize(lqjar__ceno)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    gmdlr__mzh, i = payload._lookup(item, h, for_insert=True)
    woh__yqhg = builder.not_(gmdlr__mzh)
    with builder.if_then(woh__yqhg):
        entry = payload.get_entry(i)
        bkwek__symya = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        lqjar__ceno = payload.used
        ftvq__acmmk = ir.Constant(lqjar__ceno.type, 1)
        lqjar__ceno = payload.used = builder.add(lqjar__ceno, ftvq__acmmk)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, bkwek__symya), likely=True):
            payload.fill = builder.add(payload.fill, ftvq__acmmk)
        if do_resize:
            self.upsize(lqjar__ceno)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    lqjar__ceno = payload.used
    ftvq__acmmk = ir.Constant(lqjar__ceno.type, 1)
    lqjar__ceno = payload.used = self._builder.sub(lqjar__ceno, ftvq__acmmk)
    if do_resize:
        self.downsize(lqjar__ceno)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    tqs__aezlz = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, tqs__aezlz)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    exhn__jxb = payload
    obj__fky = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(obj__fky), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with exhn__jxb._iterate() as xwlig__dqqxv:
        entry = xwlig__dqqxv.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(exhn__jxb.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as xwlig__dqqxv:
        entry = xwlig__dqqxv.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    obj__fky = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(obj__fky), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    obj__fky = cgutils.alloca_once_value(builder, cgutils.true_bit)
    pdyid__vtyh = context.get_value_type(types.intp)
    hqhgi__fpmq = ir.Constant(pdyid__vtyh, 0)
    ftvq__acmmk = ir.Constant(pdyid__vtyh, 1)
    axi__zavk = context.get_data_type(types.SetPayload(self._ty))
    pgt__xrus = context.get_abi_sizeof(axi__zavk)
    kvou__uucm = self._entrysize
    pgt__xrus -= kvou__uucm
    bep__sgy, nknpr__yhjxo = cgutils.muladd_with_overflow(builder, nentries,
        ir.Constant(pdyid__vtyh, kvou__uucm), ir.Constant(pdyid__vtyh,
        pgt__xrus))
    with builder.if_then(nknpr__yhjxo, likely=False):
        builder.store(cgutils.false_bit, obj__fky)
    with builder.if_then(builder.load(obj__fky), likely=True):
        if realloc:
            lrj__cue = self._set.meminfo
            uxh__fhcy = context.nrt.meminfo_varsize_alloc(builder, lrj__cue,
                size=bep__sgy)
            jbhf__orte = cgutils.is_null(builder, uxh__fhcy)
        else:
            xibhe__azv = _imp_dtor(context, builder.module, self._ty)
            lrj__cue = context.nrt.meminfo_new_varsize_dtor(builder,
                bep__sgy, builder.bitcast(xibhe__azv, cgutils.voidptr_t))
            jbhf__orte = cgutils.is_null(builder, lrj__cue)
        with builder.if_else(jbhf__orte, likely=False) as (ean__skg, czcyx__ecr
            ):
            with ean__skg:
                builder.store(cgutils.false_bit, obj__fky)
            with czcyx__ecr:
                if not realloc:
                    self._set.meminfo = lrj__cue
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, bep__sgy, 255)
                payload.used = hqhgi__fpmq
                payload.fill = hqhgi__fpmq
                payload.finger = hqhgi__fpmq
                qnxvk__zmmd = builder.sub(nentries, ftvq__acmmk)
                payload.mask = qnxvk__zmmd
    return builder.load(obj__fky)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    obj__fky = cgutils.alloca_once_value(builder, cgutils.true_bit)
    pdyid__vtyh = context.get_value_type(types.intp)
    hqhgi__fpmq = ir.Constant(pdyid__vtyh, 0)
    ftvq__acmmk = ir.Constant(pdyid__vtyh, 1)
    axi__zavk = context.get_data_type(types.SetPayload(self._ty))
    pgt__xrus = context.get_abi_sizeof(axi__zavk)
    kvou__uucm = self._entrysize
    pgt__xrus -= kvou__uucm
    czkg__nyg = src_payload.mask
    nentries = builder.add(ftvq__acmmk, czkg__nyg)
    bep__sgy = builder.add(ir.Constant(pdyid__vtyh, pgt__xrus), builder.mul
        (ir.Constant(pdyid__vtyh, kvou__uucm), nentries))
    with builder.if_then(builder.load(obj__fky), likely=True):
        xibhe__azv = _imp_dtor(context, builder.module, self._ty)
        lrj__cue = context.nrt.meminfo_new_varsize_dtor(builder, bep__sgy,
            builder.bitcast(xibhe__azv, cgutils.voidptr_t))
        jbhf__orte = cgutils.is_null(builder, lrj__cue)
        with builder.if_else(jbhf__orte, likely=False) as (ean__skg, czcyx__ecr
            ):
            with ean__skg:
                builder.store(cgutils.false_bit, obj__fky)
            with czcyx__ecr:
                self._set.meminfo = lrj__cue
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = hqhgi__fpmq
                payload.mask = czkg__nyg
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, kvou__uucm)
                with src_payload._iterate() as xwlig__dqqxv:
                    context.nrt.incref(builder, self._ty.dtype,
                        xwlig__dqqxv.entry.key)
    return builder.load(obj__fky)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    pnq__xtvb = context.get_value_type(types.voidptr)
    mpdw__ztpp = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [pnq__xtvb, mpdw__ztpp, pnq__xtvb])
    zdmb__lcmxh = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=zdmb__lcmxh)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        aik__yra = builder.bitcast(fn.args[0], cgutils.voidptr_t.as_pointer())
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, aik__yra)
        with payload._iterate() as xwlig__dqqxv:
            entry = xwlig__dqqxv.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    hwjnn__lop, = sig.args
    tac__jvj, = args
    lxk__yzqv = numba.core.imputils.call_len(context, builder, hwjnn__lop,
        tac__jvj)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, lxk__yzqv)
    with numba.core.imputils.for_iter(context, builder, hwjnn__lop, tac__jvj
        ) as xwlig__dqqxv:
        inst.add(xwlig__dqqxv.value)
        context.nrt.decref(builder, set_type.dtype, xwlig__dqqxv.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    hwjnn__lop = sig.args[1]
    tac__jvj = args[1]
    lxk__yzqv = numba.core.imputils.call_len(context, builder, hwjnn__lop,
        tac__jvj)
    if lxk__yzqv is not None:
        uthdt__kowb = builder.add(inst.payload.used, lxk__yzqv)
        inst.upsize(uthdt__kowb)
    with numba.core.imputils.for_iter(context, builder, hwjnn__lop, tac__jvj
        ) as xwlig__dqqxv:
        sls__ucp = context.cast(builder, xwlig__dqqxv.value, hwjnn__lop.
            dtype, inst.dtype)
        inst.add(sls__ucp)
        context.nrt.decref(builder, hwjnn__lop.dtype, xwlig__dqqxv.value)
    if lxk__yzqv is not None:
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
