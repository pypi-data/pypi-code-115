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
    izfry__gune = numba.core.bytecode.FunctionIdentity.from_function(func)
    czqx__wdpsr = numba.core.interpreter.Interpreter(izfry__gune)
    nxxqr__edck = numba.core.bytecode.ByteCode(func_id=izfry__gune)
    func_ir = czqx__wdpsr.interpret(nxxqr__edck)
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
        uawbe__gyb = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        uawbe__gyb.run()
    utri__soko = numba.core.postproc.PostProcessor(func_ir)
    utri__soko.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, upo__fcofd in visit_vars_extensions.items():
        if isinstance(stmt, t):
            upo__fcofd(stmt, callback, cbdata)
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
    pog__fbg = ['ravel', 'transpose', 'reshape']
    for uhow__jyb in blocks.values():
        for twi__lec in uhow__jyb.body:
            if type(twi__lec) in alias_analysis_extensions:
                upo__fcofd = alias_analysis_extensions[type(twi__lec)]
                upo__fcofd(twi__lec, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(twi__lec, ir.Assign):
                nbjy__sbn = twi__lec.value
                mpxtu__gqo = twi__lec.target.name
                if is_immutable_type(mpxtu__gqo, typemap):
                    continue
                if isinstance(nbjy__sbn, ir.Var
                    ) and mpxtu__gqo != nbjy__sbn.name:
                    _add_alias(mpxtu__gqo, nbjy__sbn.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr) and (nbjy__sbn.op ==
                    'cast' or nbjy__sbn.op in ['getitem', 'static_getitem']):
                    _add_alias(mpxtu__gqo, nbjy__sbn.value.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr
                    ) and nbjy__sbn.op == 'inplace_binop':
                    _add_alias(mpxtu__gqo, nbjy__sbn.lhs.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr
                    ) and nbjy__sbn.op == 'getattr' and nbjy__sbn.attr in ['T',
                    'ctypes', 'flat']:
                    _add_alias(mpxtu__gqo, nbjy__sbn.value.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr
                    ) and nbjy__sbn.op == 'getattr' and nbjy__sbn.attr not in [
                    'shape'] and nbjy__sbn.value.name in arg_aliases:
                    _add_alias(mpxtu__gqo, nbjy__sbn.value.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr
                    ) and nbjy__sbn.op == 'getattr' and nbjy__sbn.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(mpxtu__gqo, nbjy__sbn.value.name, alias_map,
                        arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr) and nbjy__sbn.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(mpxtu__gqo, typemap):
                    for rroii__ynd in nbjy__sbn.items:
                        _add_alias(mpxtu__gqo, rroii__ynd.name, alias_map,
                            arg_aliases)
                if isinstance(nbjy__sbn, ir.Expr) and nbjy__sbn.op == 'call':
                    rntms__asqm = guard(find_callname, func_ir, nbjy__sbn,
                        typemap)
                    if rntms__asqm is None:
                        continue
                    aanpo__gwtd, nqmtr__xrgv = rntms__asqm
                    if rntms__asqm in alias_func_extensions:
                        jwam__hsbpi = alias_func_extensions[rntms__asqm]
                        jwam__hsbpi(mpxtu__gqo, nbjy__sbn.args, alias_map,
                            arg_aliases)
                    if nqmtr__xrgv == 'numpy' and aanpo__gwtd in pog__fbg:
                        _add_alias(mpxtu__gqo, nbjy__sbn.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(nqmtr__xrgv, ir.Var
                        ) and aanpo__gwtd in pog__fbg:
                        _add_alias(mpxtu__gqo, nqmtr__xrgv.name, alias_map,
                            arg_aliases)
    sto__ywfo = copy.deepcopy(alias_map)
    for rroii__ynd in sto__ywfo:
        for ohlik__rxksj in sto__ywfo[rroii__ynd]:
            alias_map[rroii__ynd] |= alias_map[ohlik__rxksj]
        for ohlik__rxksj in sto__ywfo[rroii__ynd]:
            alias_map[ohlik__rxksj] = alias_map[rroii__ynd]
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
    hdcah__naqoa = compute_cfg_from_blocks(func_ir.blocks)
    hnj__obvo = compute_use_defs(func_ir.blocks)
    yaue__eyano = compute_live_map(hdcah__naqoa, func_ir.blocks, hnj__obvo.
        usemap, hnj__obvo.defmap)
    qprb__uejef = True
    while qprb__uejef:
        qprb__uejef = False
        for gnh__lezh, block in func_ir.blocks.items():
            lives = {rroii__ynd.name for rroii__ynd in block.terminator.
                list_vars()}
            for xwhfe__hkkjk, cdh__aawy in hdcah__naqoa.successors(gnh__lezh):
                lives |= yaue__eyano[xwhfe__hkkjk]
            tuizd__sirye = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    mpxtu__gqo = stmt.target
                    shs__qkf = stmt.value
                    if mpxtu__gqo.name not in lives:
                        if isinstance(shs__qkf, ir.Expr
                            ) and shs__qkf.op == 'make_function':
                            continue
                        if isinstance(shs__qkf, ir.Expr
                            ) and shs__qkf.op == 'getattr':
                            continue
                        if isinstance(shs__qkf, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(mpxtu__gqo,
                            None), types.Function):
                            continue
                        if isinstance(shs__qkf, ir.Expr
                            ) and shs__qkf.op == 'build_map':
                            continue
                    if isinstance(shs__qkf, ir.Var
                        ) and mpxtu__gqo.name == shs__qkf.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    vxei__bfdne = analysis.ir_extension_usedefs[type(stmt)]
                    nzhb__hcbwe, ocx__ddewi = vxei__bfdne(stmt)
                    lives -= ocx__ddewi
                    lives |= nzhb__hcbwe
                else:
                    lives |= {rroii__ynd.name for rroii__ynd in stmt.
                        list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(mpxtu__gqo.name)
                tuizd__sirye.append(stmt)
            tuizd__sirye.reverse()
            if len(block.body) != len(tuizd__sirye):
                qprb__uejef = True
            block.body = tuizd__sirye


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    zpd__wyxnv = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (zpd__wyxnv,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    qoy__zodj = dict(key=func, _overload_func=staticmethod(overload_func),
        _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), qoy__zodj)


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
            for htzo__qsha in fnty.templates:
                self._inline_overloads.update(htzo__qsha._inline_overloads)
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
    qoy__zodj = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), qoy__zodj)
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
    rof__szz, jsk__yfwy = self._get_impl(args, kws)
    if rof__szz is None:
        return
    ioi__zrqu = types.Dispatcher(rof__szz)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        yqe__pln = rof__szz._compiler
        flags = compiler.Flags()
        poko__yqc = yqe__pln.targetdescr.typing_context
        dfix__ssque = yqe__pln.targetdescr.target_context
        qwgf__edg = yqe__pln.pipeline_class(poko__yqc, dfix__ssque, None,
            None, None, flags, None)
        uvj__diye = InlineWorker(poko__yqc, dfix__ssque, yqe__pln.locals,
            qwgf__edg, flags, None)
        ffz__zwrn = ioi__zrqu.dispatcher.get_call_template
        htzo__qsha, nah__ylux, gqm__dox, kws = ffz__zwrn(jsk__yfwy, kws)
        if gqm__dox in self._inline_overloads:
            return self._inline_overloads[gqm__dox]['iinfo'].signature
        ir = uvj__diye.run_untyped_passes(ioi__zrqu.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, dfix__ssque, ir, gqm__dox, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, gqm__dox, None)
        self._inline_overloads[sig.args] = {'folded_args': gqm__dox}
        rufr__myyyw = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = rufr__myyyw
        if not self._inline.is_always_inline:
            sig = ioi__zrqu.get_call_type(self.context, jsk__yfwy, kws)
            self._compiled_overloads[sig.args] = ioi__zrqu.get_overload(sig)
        ynd__tuv = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': gqm__dox,
            'iinfo': ynd__tuv}
    else:
        sig = ioi__zrqu.get_call_type(self.context, jsk__yfwy, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = ioi__zrqu.get_overload(sig)
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
    gbsf__evi = [True, False]
    kqdtj__mtax = [False, True]
    yxzq__jgn = _ResolutionFailures(context, self, args, kws, depth=self._depth
        )
    from numba.core.target_extension import get_local_target
    jdnnw__whcxc = get_local_target(context)
    noyth__qnq = utils.order_by_target_specificity(jdnnw__whcxc, self.
        templates, fnkey=self.key[0])
    self._depth += 1
    for uax__kgdcy in noyth__qnq:
        nblct__nxj = uax__kgdcy(context)
        rge__yyhoj = gbsf__evi if nblct__nxj.prefer_literal else kqdtj__mtax
        rge__yyhoj = [True] if getattr(nblct__nxj, '_no_unliteral', False
            ) else rge__yyhoj
        for kpcuv__ogjxd in rge__yyhoj:
            try:
                if kpcuv__ogjxd:
                    sig = nblct__nxj.apply(args, kws)
                else:
                    dyz__cla = tuple([_unlit_non_poison(a) for a in args])
                    opb__onsga = {yadbw__lkdjg: _unlit_non_poison(
                        rroii__ynd) for yadbw__lkdjg, rroii__ynd in kws.items()
                        }
                    sig = nblct__nxj.apply(dyz__cla, opb__onsga)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    yxzq__jgn.add_error(nblct__nxj, False, e, kpcuv__ogjxd)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = nblct__nxj.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    bbgkj__jukrv = getattr(nblct__nxj, 'cases', None)
                    if bbgkj__jukrv is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            bbgkj__jukrv)
                    else:
                        msg = 'No match.'
                    yxzq__jgn.add_error(nblct__nxj, True, msg, kpcuv__ogjxd)
    yxzq__jgn.raise_error()


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
    htzo__qsha = self.template(context)
    wrmtq__ufez = None
    sls__yybws = None
    uzkbb__doe = None
    rge__yyhoj = [True, False] if htzo__qsha.prefer_literal else [False, True]
    rge__yyhoj = [True] if getattr(htzo__qsha, '_no_unliteral', False
        ) else rge__yyhoj
    for kpcuv__ogjxd in rge__yyhoj:
        if kpcuv__ogjxd:
            try:
                uzkbb__doe = htzo__qsha.apply(args, kws)
            except Exception as luf__hkbbb:
                if isinstance(luf__hkbbb, errors.ForceLiteralArg):
                    raise luf__hkbbb
                wrmtq__ufez = luf__hkbbb
                uzkbb__doe = None
            else:
                break
        else:
            pqtz__iktif = tuple([_unlit_non_poison(a) for a in args])
            nkzg__lmlvm = {yadbw__lkdjg: _unlit_non_poison(rroii__ynd) for 
                yadbw__lkdjg, rroii__ynd in kws.items()}
            orw__ixq = pqtz__iktif == args and kws == nkzg__lmlvm
            if not orw__ixq and uzkbb__doe is None:
                try:
                    uzkbb__doe = htzo__qsha.apply(pqtz__iktif, nkzg__lmlvm)
                except Exception as luf__hkbbb:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(
                        luf__hkbbb, errors.NumbaError):
                        raise luf__hkbbb
                    if isinstance(luf__hkbbb, errors.ForceLiteralArg):
                        if htzo__qsha.prefer_literal:
                            raise luf__hkbbb
                    sls__yybws = luf__hkbbb
                else:
                    break
    if uzkbb__doe is None and (sls__yybws is not None or wrmtq__ufez is not
        None):
        vjukd__zpor = '- Resolution failure for {} arguments:\n{}\n'
        nljl__ume = _termcolor.highlight(vjukd__zpor)
        if numba.core.config.DEVELOPER_MODE:
            zyu__wycfy = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    cfaww__aes = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    cfaww__aes = ['']
                nfved__xkwxz = '\n{}'.format(2 * zyu__wycfy)
                ezqn__hvz = _termcolor.reset(nfved__xkwxz + nfved__xkwxz.
                    join(_bt_as_lines(cfaww__aes)))
                return _termcolor.reset(ezqn__hvz)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            upem__conq = str(e)
            upem__conq = upem__conq if upem__conq else str(repr(e)) + add_bt(e)
            upgmv__scu = errors.TypingError(textwrap.dedent(upem__conq))
            return nljl__ume.format(literalness, str(upgmv__scu))
        import bodo
        if isinstance(wrmtq__ufez, bodo.utils.typing.BodoError):
            raise wrmtq__ufez
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', wrmtq__ufez) +
                nested_msg('non-literal', sls__yybws))
        else:
            if 'missing a required argument' in wrmtq__ufez.msg:
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
            raise errors.TypingError(msg, loc=wrmtq__ufez.loc)
    return uzkbb__doe


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
    aanpo__gwtd = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=aanpo__gwtd)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            nbq__stli = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), nbq__stli)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    osybs__srx = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            osybs__srx.append(types.Omitted(a.value))
        else:
            osybs__srx.append(self.typeof_pyval(a))
    przz__wen = None
    try:
        error = None
        przz__wen = self.compile(tuple(osybs__srx))
    except errors.ForceLiteralArg as e:
        onu__lqp = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if onu__lqp:
            ppn__zcmq = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            dqjxb__pyh = ', '.join('Arg #{} is {}'.format(i, args[i]) for i in
                sorted(onu__lqp))
            raise errors.CompilerError(ppn__zcmq.format(dqjxb__pyh))
        jsk__yfwy = []
        try:
            for i, rroii__ynd in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        jsk__yfwy.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        jsk__yfwy.append(types.literal(args[i]))
                else:
                    jsk__yfwy.append(args[i])
            args = jsk__yfwy
        except (OSError, FileNotFoundError) as lvbf__gaiys:
            error = FileNotFoundError(str(lvbf__gaiys) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                przz__wen = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        rgrb__bjp = []
        for i, ydibf__ztzm in enumerate(args):
            val = ydibf__ztzm.value if isinstance(ydibf__ztzm, numba.core.
                dispatcher.OmittedArg) else ydibf__ztzm
            try:
                pqr__ansm = typeof(val, Purpose.argument)
            except ValueError as jtgn__lcdne:
                rgrb__bjp.append((i, str(jtgn__lcdne)))
            else:
                if pqr__ansm is None:
                    rgrb__bjp.append((i,
                        f'cannot determine Numba type of value {val}'))
        if rgrb__bjp:
            wzxhu__dnu = '\n'.join(f'- argument {i}: {drb__zres}' for i,
                drb__zres in rgrb__bjp)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{wzxhu__dnu}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                nbfr__vgkan = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                iszac__mmkk = False
                for pzoe__semm in nbfr__vgkan:
                    if pzoe__semm in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        iszac__mmkk = True
                        break
                if not iszac__mmkk:
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
                nbq__stli = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), nbq__stli)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return przz__wen


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
    for wvd__xuv in cres.library._codegen._engine._defined_symbols:
        if wvd__xuv.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in wvd__xuv and (
            'bodo_gb_udf_update_local' in wvd__xuv or 'bodo_gb_udf_combine' in
            wvd__xuv or 'bodo_gb_udf_eval' in wvd__xuv or 
            'bodo_gb_apply_general_udfs' in wvd__xuv):
            gb_agg_cfunc_addr[wvd__xuv] = cres.library.get_pointer_to_function(
                wvd__xuv)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for wvd__xuv in cres.library._codegen._engine._defined_symbols:
        if wvd__xuv.startswith('cfunc') and ('get_join_cond_addr' not in
            wvd__xuv or 'bodo_join_gen_cond' in wvd__xuv):
            join_gen_cond_cfunc_addr[wvd__xuv
                ] = cres.library.get_pointer_to_function(wvd__xuv)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    rof__szz = self._get_dispatcher_for_current_target()
    if rof__szz is not self:
        return rof__szz.compile(sig)
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
            rze__filnf = self.overloads.get(tuple(args))
            if rze__filnf is not None:
                return rze__filnf.entry_point
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
            jhqj__cudw = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=jhqj__cudw):
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
    wwnwv__qleaw = self._final_module
    dba__iozms = []
    xou__tygtn = 0
    for fn in wwnwv__qleaw.functions:
        xou__tygtn += 1
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
            dba__iozms.append(fn.name)
    if xou__tygtn == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if dba__iozms:
        wwnwv__qleaw = wwnwv__qleaw.clone()
        for name in dba__iozms:
            wwnwv__qleaw.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = wwnwv__qleaw
    return wwnwv__qleaw


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
    for shgfc__drc in self.constraints:
        loc = shgfc__drc.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                shgfc__drc(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                swv__stwfp = numba.core.errors.TypingError(str(e), loc=
                    shgfc__drc.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(swv__stwfp, e))
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
                    swv__stwfp = numba.core.errors.TypingError(msg.format(
                        con=shgfc__drc, err=str(e)), loc=shgfc__drc.loc,
                        highlighting=False)
                    errors.append(utils.chain_exception(swv__stwfp, e))
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
    for vnu__jtj in self._failures.values():
        for hurky__lkq in vnu__jtj:
            if isinstance(hurky__lkq.error, ForceLiteralArg):
                raise hurky__lkq.error
            if isinstance(hurky__lkq.error, bodo.utils.typing.BodoError):
                raise hurky__lkq.error
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
    opxol__weiq = False
    tuizd__sirye = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        hox__ouep = set()
        jqhtn__hkfbk = lives & alias_set
        for rroii__ynd in jqhtn__hkfbk:
            hox__ouep |= alias_map[rroii__ynd]
        lives_n_aliases = lives | hox__ouep | arg_aliases
        if type(stmt) in remove_dead_extensions:
            upo__fcofd = remove_dead_extensions[type(stmt)]
            stmt = upo__fcofd(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                opxol__weiq = True
                continue
        if isinstance(stmt, ir.Assign):
            mpxtu__gqo = stmt.target
            shs__qkf = stmt.value
            if mpxtu__gqo.name not in lives and has_no_side_effect(shs__qkf,
                lives_n_aliases, call_table):
                opxol__weiq = True
                continue
            if saved_array_analysis and mpxtu__gqo.name in lives and is_expr(
                shs__qkf, 'getattr'
                ) and shs__qkf.attr == 'shape' and is_array_typ(typemap[
                shs__qkf.value.name]) and shs__qkf.value.name not in lives:
                hrfkf__kvec = {rroii__ynd: yadbw__lkdjg for yadbw__lkdjg,
                    rroii__ynd in func_ir.blocks.items()}
                if block in hrfkf__kvec:
                    gnh__lezh = hrfkf__kvec[block]
                    lkl__ygmg = saved_array_analysis.get_equiv_set(gnh__lezh)
                    aztfa__cpquv = lkl__ygmg.get_equiv_set(shs__qkf.value)
                    if aztfa__cpquv is not None:
                        for rroii__ynd in aztfa__cpquv:
                            if rroii__ynd.endswith('#0'):
                                rroii__ynd = rroii__ynd[:-2]
                            if rroii__ynd in typemap and is_array_typ(typemap
                                [rroii__ynd]) and rroii__ynd in lives:
                                shs__qkf.value = ir.Var(shs__qkf.value.
                                    scope, rroii__ynd, shs__qkf.value.loc)
                                opxol__weiq = True
                                break
            if isinstance(shs__qkf, ir.Var
                ) and mpxtu__gqo.name == shs__qkf.name:
                opxol__weiq = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                opxol__weiq = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            vxei__bfdne = analysis.ir_extension_usedefs[type(stmt)]
            nzhb__hcbwe, ocx__ddewi = vxei__bfdne(stmt)
            lives -= ocx__ddewi
            lives |= nzhb__hcbwe
        else:
            lives |= {rroii__ynd.name for rroii__ynd in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                yubtv__tvdo = set()
                if isinstance(shs__qkf, ir.Expr):
                    yubtv__tvdo = {rroii__ynd.name for rroii__ynd in
                        shs__qkf.list_vars()}
                if mpxtu__gqo.name not in yubtv__tvdo:
                    lives.remove(mpxtu__gqo.name)
        tuizd__sirye.append(stmt)
    tuizd__sirye.reverse()
    block.body = tuizd__sirye
    return opxol__weiq


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            zlxl__cjgiw, = args
            if isinstance(zlxl__cjgiw, types.IterableType):
                dtype = zlxl__cjgiw.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), zlxl__cjgiw)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    jgk__xdewj = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (jgk__xdewj, self.dtype)
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
        except LiteralTypingError as fbfkk__iiyjt:
            return
    try:
        return literal(value)
    except LiteralTypingError as fbfkk__iiyjt:
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
        rcvq__qay = py_func.__qualname__
    except AttributeError as fbfkk__iiyjt:
        rcvq__qay = py_func.__name__
    rrgz__oqje = inspect.getfile(py_func)
    for cls in self._locator_classes:
        ntj__mmqoh = cls.from_function(py_func, rrgz__oqje)
        if ntj__mmqoh is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (rcvq__qay, rrgz__oqje))
    self._locator = ntj__mmqoh
    uimvj__zhal = inspect.getfile(py_func)
    vcwre__djfts = os.path.splitext(os.path.basename(uimvj__zhal))[0]
    if rrgz__oqje.startswith('<ipython-'):
        cbjl__zkeq = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)',
            '\\1\\3', vcwre__djfts, count=1)
        if cbjl__zkeq == vcwre__djfts:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        vcwre__djfts = cbjl__zkeq
    mfdfl__yqab = '%s.%s' % (vcwre__djfts, rcvq__qay)
    hupot__vmhgd = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(mfdfl__yqab, hupot__vmhgd)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    kfkt__amy = list(filter(lambda a: self._istuple(a.name), args))
    if len(kfkt__amy) == 2 and fn.__name__ == 'add':
        eqmcb__ptx = self.typemap[kfkt__amy[0].name]
        kys__qvad = self.typemap[kfkt__amy[1].name]
        if eqmcb__ptx.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                kfkt__amy[1]))
        if kys__qvad.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                kfkt__amy[0]))
        try:
            alupm__omqm = [equiv_set.get_shape(x) for x in kfkt__amy]
            if None in alupm__omqm:
                return None
            fai__oahl = sum(alupm__omqm, ())
            return ArrayAnalysis.AnalyzeResult(shape=fai__oahl)
        except GuardException as fbfkk__iiyjt:
            return None
    tlobx__qjgt = list(filter(lambda a: self._isarray(a.name), args))
    require(len(tlobx__qjgt) > 0)
    epn__frgz = [x.name for x in tlobx__qjgt]
    ues__cgrb = [self.typemap[x.name].ndim for x in tlobx__qjgt]
    zyz__bpg = max(ues__cgrb)
    require(zyz__bpg > 0)
    alupm__omqm = [equiv_set.get_shape(x) for x in tlobx__qjgt]
    if any(a is None for a in alupm__omqm):
        return ArrayAnalysis.AnalyzeResult(shape=tlobx__qjgt[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, tlobx__qjgt))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, alupm__omqm,
        epn__frgz)


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
    rjh__kbbic = code_obj.code
    fkgzz__kpao = len(rjh__kbbic.co_freevars)
    kkg__uvu = rjh__kbbic.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        qxxg__femqs, op = ir_utils.find_build_sequence(caller_ir, code_obj.
            closure)
        assert op == 'build_tuple'
        kkg__uvu = [rroii__ynd.name for rroii__ynd in qxxg__femqs]
    rodxj__nvj = caller_ir.func_id.func.__globals__
    try:
        rodxj__nvj = getattr(code_obj, 'globals', rodxj__nvj)
    except KeyError as fbfkk__iiyjt:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    uppzw__ixhcq = []
    for x in kkg__uvu:
        try:
            bgbr__txxv = caller_ir.get_definition(x)
        except KeyError as fbfkk__iiyjt:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(bgbr__txxv, (ir.Const, ir.Global, ir.FreeVar)):
            val = bgbr__txxv.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                zpd__wyxnv = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                rodxj__nvj[zpd__wyxnv] = bodo.jit(distributed=False)(val)
                rodxj__nvj[zpd__wyxnv].is_nested_func = True
                val = zpd__wyxnv
            if isinstance(val, CPUDispatcher):
                zpd__wyxnv = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                rodxj__nvj[zpd__wyxnv] = val
                val = zpd__wyxnv
            uppzw__ixhcq.append(val)
        elif isinstance(bgbr__txxv, ir.Expr
            ) and bgbr__txxv.op == 'make_function':
            bmf__upobx = convert_code_obj_to_function(bgbr__txxv, caller_ir)
            zpd__wyxnv = ir_utils.mk_unique_var('nested_func').replace('.', '_'
                )
            rodxj__nvj[zpd__wyxnv] = bodo.jit(distributed=False)(bmf__upobx)
            rodxj__nvj[zpd__wyxnv].is_nested_func = True
            uppzw__ixhcq.append(zpd__wyxnv)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    ikncj__bfram = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in
        enumerate(uppzw__ixhcq)])
    xtcnn__vktsv = ','.join([('c_%d' % i) for i in range(fkgzz__kpao)])
    dqttk__jxj = list(rjh__kbbic.co_varnames)
    grtjx__muh = 0
    gngs__xkl = rjh__kbbic.co_argcount
    ltl__awaqd = caller_ir.get_definition(code_obj.defaults)
    if ltl__awaqd is not None:
        if isinstance(ltl__awaqd, tuple):
            dxpc__fdrxg = [caller_ir.get_definition(x).value for x in
                ltl__awaqd]
            hkykx__nva = tuple(dxpc__fdrxg)
        else:
            dxpc__fdrxg = [caller_ir.get_definition(x).value for x in
                ltl__awaqd.items]
            hkykx__nva = tuple(dxpc__fdrxg)
        grtjx__muh = len(hkykx__nva)
    kgy__yqzby = gngs__xkl - grtjx__muh
    vukh__qbqtz = ','.join([('%s' % dqttk__jxj[i]) for i in range(kgy__yqzby)])
    if grtjx__muh:
        jirhi__cjrbj = [('%s = %s' % (dqttk__jxj[i + kgy__yqzby],
            hkykx__nva[i])) for i in range(grtjx__muh)]
        vukh__qbqtz += ', '
        vukh__qbqtz += ', '.join(jirhi__cjrbj)
    return _create_function_from_code_obj(rjh__kbbic, ikncj__bfram,
        vukh__qbqtz, xtcnn__vktsv, rodxj__nvj)


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
    for gxk__ljd, (dianh__acry, qhx__lle) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % qhx__lle)
            gxsd__czs = _pass_registry.get(dianh__acry).pass_inst
            if isinstance(gxsd__czs, CompilerPass):
                self._runPass(gxk__ljd, gxsd__czs, state)
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
                    pipeline_name, qhx__lle)
                pcukw__qgk = self._patch_error(msg, e)
                raise pcukw__qgk
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
    wcfy__rgc = None
    ocx__ddewi = {}

    def lookup(var, already_seen, varonly=True):
        val = ocx__ddewi.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    rztjg__jhvib = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        mpxtu__gqo = stmt.target
        shs__qkf = stmt.value
        ocx__ddewi[mpxtu__gqo.name] = shs__qkf
        if isinstance(shs__qkf, ir.Var) and shs__qkf.name in ocx__ddewi:
            shs__qkf = lookup(shs__qkf, set())
        if isinstance(shs__qkf, ir.Expr):
            sbuna__laikw = set(lookup(rroii__ynd, set(), True).name for
                rroii__ynd in shs__qkf.list_vars())
            if name in sbuna__laikw:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(shs__qkf)]
                rhwlk__tbbu = [x for x, gtjid__zhzvi in args if 
                    gtjid__zhzvi.name != name]
                args = [(x, gtjid__zhzvi) for x, gtjid__zhzvi in args if x !=
                    gtjid__zhzvi.name]
                iaqfi__fqpbp = dict(args)
                if len(rhwlk__tbbu) == 1:
                    iaqfi__fqpbp[rhwlk__tbbu[0]] = ir.Var(mpxtu__gqo.scope,
                        name + '#init', mpxtu__gqo.loc)
                replace_vars_inner(shs__qkf, iaqfi__fqpbp)
                wcfy__rgc = nodes[i:]
                break
    return wcfy__rgc


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
        sjoea__qkcoj = expand_aliases({rroii__ynd.name for rroii__ynd in
            stmt.list_vars()}, alias_map, arg_aliases)
        dkesi__zzltu = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        uqjhl__xqhu = expand_aliases({rroii__ynd.name for rroii__ynd in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        jmq__jmqwc = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(dkesi__zzltu & uqjhl__xqhu | jmq__jmqwc & sjoea__qkcoj) == 0:
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
    pyp__ear = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            pyp__ear.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                pyp__ear.update(get_parfor_writes(stmt, func_ir))
    return pyp__ear


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    pyp__ear = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        pyp__ear.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        pyp__ear = {rroii__ynd.name for rroii__ynd in stmt.df_out_vars.values()
            }
        if stmt.out_key_vars is not None:
            pyp__ear.update({rroii__ynd.name for rroii__ynd in stmt.
                out_key_vars})
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        pyp__ear = {rroii__ynd.name for rroii__ynd in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        pyp__ear = {rroii__ynd.name for rroii__ynd in stmt.out_data_vars.
            values()}
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            pyp__ear.update({rroii__ynd.name for rroii__ynd in stmt.
                out_key_arrs})
            pyp__ear.update({rroii__ynd.name for rroii__ynd in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        rntms__asqm = guard(find_callname, func_ir, stmt.value)
        if rntms__asqm in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'),
            ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            pyp__ear.add(stmt.value.args[0].name)
    return pyp__ear


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
        upo__fcofd = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        sesd__lnwri = upo__fcofd.format(self, msg)
        self.args = sesd__lnwri,
    else:
        upo__fcofd = _termcolor.errmsg('{0}')
        sesd__lnwri = upo__fcofd.format(self)
        self.args = sesd__lnwri,
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
        for xoa__liwp in options['distributed']:
            dist_spec[xoa__liwp] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for xoa__liwp in options['distributed_block']:
            dist_spec[xoa__liwp] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    pke__kgqbm = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, hdlt__fybtn in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(hdlt__fybtn)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    rtjrs__txp = {}
    for nhm__fvcdr in reversed(inspect.getmro(cls)):
        rtjrs__txp.update(nhm__fvcdr.__dict__)
    nga__quwn, wddfo__sii, ixccy__lfdz, obl__ogq = {}, {}, {}, {}
    for yadbw__lkdjg, rroii__ynd in rtjrs__txp.items():
        if isinstance(rroii__ynd, pytypes.FunctionType):
            nga__quwn[yadbw__lkdjg] = rroii__ynd
        elif isinstance(rroii__ynd, property):
            wddfo__sii[yadbw__lkdjg] = rroii__ynd
        elif isinstance(rroii__ynd, staticmethod):
            ixccy__lfdz[yadbw__lkdjg] = rroii__ynd
        else:
            obl__ogq[yadbw__lkdjg] = rroii__ynd
    skq__qbf = (set(nga__quwn) | set(wddfo__sii) | set(ixccy__lfdz)) & set(spec
        )
    if skq__qbf:
        raise NameError('name shadowing: {0}'.format(', '.join(skq__qbf)))
    bfl__xqsx = obl__ogq.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(obl__ogq)
    if obl__ogq:
        msg = 'class members are not yet supported: {0}'
        mzj__mhay = ', '.join(obl__ogq.keys())
        raise TypeError(msg.format(mzj__mhay))
    for yadbw__lkdjg, rroii__ynd in wddfo__sii.items():
        if rroii__ynd.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(
                yadbw__lkdjg))
    jit_methods = {yadbw__lkdjg: bodo.jit(returns_maybe_distributed=
        pke__kgqbm)(rroii__ynd) for yadbw__lkdjg, rroii__ynd in nga__quwn.
        items()}
    jit_props = {}
    for yadbw__lkdjg, rroii__ynd in wddfo__sii.items():
        qoy__zodj = {}
        if rroii__ynd.fget:
            qoy__zodj['get'] = bodo.jit(rroii__ynd.fget)
        if rroii__ynd.fset:
            qoy__zodj['set'] = bodo.jit(rroii__ynd.fset)
        jit_props[yadbw__lkdjg] = qoy__zodj
    jit_static_methods = {yadbw__lkdjg: bodo.jit(rroii__ynd.__func__) for 
        yadbw__lkdjg, rroii__ynd in ixccy__lfdz.items()}
    ipn__pgeb = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    mynf__ikwg = dict(class_type=ipn__pgeb, __doc__=bfl__xqsx)
    mynf__ikwg.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), mynf__ikwg)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, ipn__pgeb)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(ipn__pgeb, typingctx, targetctx).register()
    as_numba_type.register(cls, ipn__pgeb.instance_type)
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
    omwd__ksi = ','.join('{0}:{1}'.format(yadbw__lkdjg, rroii__ynd) for 
        yadbw__lkdjg, rroii__ynd in struct.items())
    cqwzw__ybxc = ','.join('{0}:{1}'.format(yadbw__lkdjg, rroii__ynd) for 
        yadbw__lkdjg, rroii__ynd in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), omwd__ksi, cqwzw__ybxc)
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
    ied__ebnx = numba.core.typeinfer.fold_arg_vars(typevars, self.args,
        self.vararg, self.kws)
    if ied__ebnx is None:
        return
    woft__ikv, ikso__lmbzl = ied__ebnx
    for a in itertools.chain(woft__ikv, ikso__lmbzl.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, woft__ikv, ikso__lmbzl)
    except ForceLiteralArg as e:
        oqc__rqa = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(oqc__rqa, self.kws)
        joaai__olgoa = set()
        cssaz__ros = set()
        fxd__kvyt = {}
        for gxk__ljd in e.requested_args:
            rgh__tep = typeinfer.func_ir.get_definition(folded[gxk__ljd])
            if isinstance(rgh__tep, ir.Arg):
                joaai__olgoa.add(rgh__tep.index)
                if rgh__tep.index in e.file_infos:
                    fxd__kvyt[rgh__tep.index] = e.file_infos[rgh__tep.index]
            else:
                cssaz__ros.add(gxk__ljd)
        if cssaz__ros:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif joaai__olgoa:
            raise ForceLiteralArg(joaai__olgoa, loc=self.loc, file_infos=
                fxd__kvyt)
    if sig is None:
        kxhe__cecie = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in woft__ikv]
        args += [('%s=%s' % (yadbw__lkdjg, rroii__ynd)) for yadbw__lkdjg,
            rroii__ynd in sorted(ikso__lmbzl.items())]
        uoy__gzvpz = kxhe__cecie.format(fnty, ', '.join(map(str, args)))
        hqldl__almz = context.explain_function_type(fnty)
        msg = '\n'.join([uoy__gzvpz, hqldl__almz])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        eafx__xjt = context.unify_pairs(sig.recvr, fnty.this)
        if eafx__xjt is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if eafx__xjt is not None and eafx__xjt.is_precise():
            iek__khgts = fnty.copy(this=eafx__xjt)
            typeinfer.propagate_refined_type(self.func, iek__khgts)
    if not sig.return_type.is_precise():
        agsut__frj = typevars[self.target]
        if agsut__frj.defined:
            bjg__hazcd = agsut__frj.getone()
            if context.unify_pairs(bjg__hazcd, sig.return_type) == bjg__hazcd:
                sig = sig.replace(return_type=bjg__hazcd)
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
        ppn__zcmq = '*other* must be a {} but got a {} instead'
        raise TypeError(ppn__zcmq.format(ForceLiteralArg, type(other)))
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
    bpew__qirz = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for yadbw__lkdjg, rroii__ynd in kwargs.items():
        rgfoq__jiso = None
        try:
            kfx__usb = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var(
                'dummy'), loc)
            func_ir._definitions[kfx__usb.name] = [rroii__ynd]
            rgfoq__jiso = get_const_value_inner(func_ir, kfx__usb)
            func_ir._definitions.pop(kfx__usb.name)
            if isinstance(rgfoq__jiso, str):
                rgfoq__jiso = sigutils._parse_signature_string(rgfoq__jiso)
            if isinstance(rgfoq__jiso, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {yadbw__lkdjg} is annotated as type class {rgfoq__jiso}."""
                    )
            assert isinstance(rgfoq__jiso, types.Type)
            if isinstance(rgfoq__jiso, (types.List, types.Set)):
                rgfoq__jiso = rgfoq__jiso.copy(reflected=False)
            bpew__qirz[yadbw__lkdjg] = rgfoq__jiso
        except BodoError as fbfkk__iiyjt:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(rgfoq__jiso, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(rroii__ynd, ir.Global):
                    msg = f'Global {rroii__ynd.name!r} is not defined.'
                if isinstance(rroii__ynd, ir.FreeVar):
                    msg = f'Freevar {rroii__ynd.name!r} is not defined.'
            if isinstance(rroii__ynd, ir.Expr) and rroii__ynd.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=yadbw__lkdjg, msg=msg, loc=loc)
    for name, typ in bpew__qirz.items():
        self._legalize_arg_type(name, typ, loc)
    return bpew__qirz


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
    cnt__tybwl = inst.arg
    assert cnt__tybwl > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(cnt__tybwl)]))
    tmps = [state.make_temp() for _ in range(cnt__tybwl - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    fulrm__ykv = ir.Global('format', format, loc=self.loc)
    self.store(value=fulrm__ykv, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    bak__fye = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=bak__fye, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    cnt__tybwl = inst.arg
    assert cnt__tybwl > 0, 'invalid BUILD_STRING count'
    bzjs__utprk = self.get(strings[0])
    for other, wrkky__qmc in zip(strings[1:], tmps):
        other = self.get(other)
        nbjy__sbn = ir.Expr.binop(operator.add, lhs=bzjs__utprk, rhs=other,
            loc=self.loc)
        self.store(nbjy__sbn, wrkky__qmc)
        bzjs__utprk = self.get(wrkky__qmc)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    pqna__iylit = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, pqna__iylit])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    ttm__rdor = mk_unique_var(f'{var_name}')
    hyf__acmad = ttm__rdor.replace('<', '_').replace('>', '_')
    hyf__acmad = hyf__acmad.replace('.', '_').replace('$', '_v')
    return hyf__acmad


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
                cmfu__joqy = get_overload_const_str(val2)
                if cmfu__joqy != 'ns':
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
        nya__oxqh = states['defmap']
        if len(nya__oxqh) == 0:
            liy__eucv = assign.target
            numba.core.ssa._logger.debug('first assign: %s', liy__eucv)
            if liy__eucv.name not in scope.localvars:
                liy__eucv = scope.define(assign.target.name, loc=assign.loc)
        else:
            liy__eucv = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=liy__eucv, value=assign.value, loc=assign.loc
            )
        nya__oxqh[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    vhdml__lwrr = []
    for yadbw__lkdjg, rroii__ynd in typing.npydecl.registry.globals:
        if yadbw__lkdjg == func:
            vhdml__lwrr.append(rroii__ynd)
    for yadbw__lkdjg, rroii__ynd in typing.templates.builtin_registry.globals:
        if yadbw__lkdjg == func:
            vhdml__lwrr.append(rroii__ynd)
    if len(vhdml__lwrr) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return vhdml__lwrr


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    kkux__rsye = {}
    ttt__qfb = find_topo_order(blocks)
    tzj__cfugi = {}
    for gnh__lezh in ttt__qfb:
        block = blocks[gnh__lezh]
        tuizd__sirye = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                mpxtu__gqo = stmt.target.name
                shs__qkf = stmt.value
                if (shs__qkf.op == 'getattr' and shs__qkf.attr in arr_math and
                    isinstance(typemap[shs__qkf.value.name], types.npytypes
                    .Array)):
                    shs__qkf = stmt.value
                    kfk__dik = shs__qkf.value
                    kkux__rsye[mpxtu__gqo] = kfk__dik
                    scope = kfk__dik.scope
                    loc = kfk__dik.loc
                    dkrkd__xwpzo = ir.Var(scope, mk_unique_var('$np_g_var'),
                        loc)
                    typemap[dkrkd__xwpzo.name] = types.misc.Module(numpy)
                    yfr__nbdpv = ir.Global('np', numpy, loc)
                    jzik__kzruf = ir.Assign(yfr__nbdpv, dkrkd__xwpzo, loc)
                    shs__qkf.value = dkrkd__xwpzo
                    tuizd__sirye.append(jzik__kzruf)
                    func_ir._definitions[dkrkd__xwpzo.name] = [yfr__nbdpv]
                    func = getattr(numpy, shs__qkf.attr)
                    mkrh__pfea = get_np_ufunc_typ_lst(func)
                    tzj__cfugi[mpxtu__gqo] = mkrh__pfea
                if shs__qkf.op == 'call' and shs__qkf.func.name in kkux__rsye:
                    kfk__dik = kkux__rsye[shs__qkf.func.name]
                    jmdw__kvz = calltypes.pop(shs__qkf)
                    zkxf__tvk = jmdw__kvz.args[:len(shs__qkf.args)]
                    eyz__gtj = {name: typemap[rroii__ynd.name] for name,
                        rroii__ynd in shs__qkf.kws}
                    pomu__yupjc = tzj__cfugi[shs__qkf.func.name]
                    hugq__eyi = None
                    for wrn__tnnzx in pomu__yupjc:
                        try:
                            hugq__eyi = wrn__tnnzx.get_call_type(typingctx,
                                [typemap[kfk__dik.name]] + list(zkxf__tvk),
                                eyz__gtj)
                            typemap.pop(shs__qkf.func.name)
                            typemap[shs__qkf.func.name] = wrn__tnnzx
                            calltypes[shs__qkf] = hugq__eyi
                            break
                        except Exception as fbfkk__iiyjt:
                            pass
                    if hugq__eyi is None:
                        raise TypeError(
                            f'No valid template found for {shs__qkf.func.name}'
                            )
                    shs__qkf.args = [kfk__dik] + shs__qkf.args
            tuizd__sirye.append(stmt)
        block.body = tuizd__sirye


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    wvdm__maky = ufunc.nin
    ixg__kvsnx = ufunc.nout
    kgy__yqzby = ufunc.nargs
    assert kgy__yqzby == wvdm__maky + ixg__kvsnx
    if len(args) < wvdm__maky:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), wvdm__maky)
            )
    if len(args) > kgy__yqzby:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), kgy__yqzby)
            )
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    oax__axr = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    dkc__jms = max(oax__axr)
    qfzjm__xnjb = args[wvdm__maky:]
    if not all(dxpc__fdrxg == dkc__jms for dxpc__fdrxg in oax__axr[wvdm__maky:]
        ):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(irud__kpy, types.ArrayCompatible) and not
        isinstance(irud__kpy, types.Bytes) for irud__kpy in qfzjm__xnjb):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(irud__kpy.mutable for irud__kpy in qfzjm__xnjb):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    mkw__ahma = [(x.dtype if isinstance(x, types.ArrayCompatible) and not
        isinstance(x, types.Bytes) else x) for x in args]
    wnnsf__bfw = None
    if dkc__jms > 0 and len(qfzjm__xnjb) < ufunc.nout:
        wnnsf__bfw = 'C'
        qas__tjt = [(x.layout if isinstance(x, types.ArrayCompatible) and 
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in qas__tjt and 'F' in qas__tjt:
            wnnsf__bfw = 'F'
    return mkw__ahma, qfzjm__xnjb, dkc__jms, wnnsf__bfw


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
        huxn__qant = 'Dict.key_type cannot be of type {}'
        raise TypingError(huxn__qant.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        huxn__qant = 'Dict.value_type cannot be of type {}'
        raise TypingError(huxn__qant.format(valty))
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
    wej__ozz = self.context, tuple(args), tuple(kws.items())
    try:
        flrxc__uyux, args = self._impl_cache[wej__ozz]
        return flrxc__uyux, args
    except KeyError as fbfkk__iiyjt:
        pass
    flrxc__uyux, args = self._build_impl(wej__ozz, args, kws)
    return flrxc__uyux, args


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
        bmb__mrsw = find_topo_order(parfor.loop_body)
    gbr__yyq = bmb__mrsw[0]
    brlfp__iuxe = {}
    _update_parfor_get_setitems(parfor.loop_body[gbr__yyq].body, parfor.
        index_var, alias_map, brlfp__iuxe, lives_n_aliases)
    csf__fqk = set(brlfp__iuxe.keys())
    for fpbke__krmg in bmb__mrsw:
        if fpbke__krmg == gbr__yyq:
            continue
        for stmt in parfor.loop_body[fpbke__krmg].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            cyoi__gnv = set(rroii__ynd.name for rroii__ynd in stmt.list_vars())
            bvxyp__pvnh = cyoi__gnv & csf__fqk
            for a in bvxyp__pvnh:
                brlfp__iuxe.pop(a, None)
    for fpbke__krmg in bmb__mrsw:
        if fpbke__krmg == gbr__yyq:
            continue
        block = parfor.loop_body[fpbke__krmg]
        siiz__ckr = brlfp__iuxe.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            siiz__ckr, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    veozx__sdmzw = max(blocks.keys())
    vqs__gkank, iuk__tyh = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    pic__pbiud = ir.Jump(vqs__gkank, ir.Loc('parfors_dummy', -1))
    blocks[veozx__sdmzw].body.append(pic__pbiud)
    hdcah__naqoa = compute_cfg_from_blocks(blocks)
    hnj__obvo = compute_use_defs(blocks)
    yaue__eyano = compute_live_map(hdcah__naqoa, blocks, hnj__obvo.usemap,
        hnj__obvo.defmap)
    alias_set = set(alias_map.keys())
    for gnh__lezh, block in blocks.items():
        tuizd__sirye = []
        afnqv__lcrd = {rroii__ynd.name for rroii__ynd in block.terminator.
            list_vars()}
        for xwhfe__hkkjk, cdh__aawy in hdcah__naqoa.successors(gnh__lezh):
            afnqv__lcrd |= yaue__eyano[xwhfe__hkkjk]
        for stmt in reversed(block.body):
            hox__ouep = afnqv__lcrd & alias_set
            for rroii__ynd in hox__ouep:
                afnqv__lcrd |= alias_map[rroii__ynd]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in afnqv__lcrd and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                rntms__asqm = guard(find_callname, func_ir, stmt.value)
                if rntms__asqm == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in afnqv__lcrd and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            afnqv__lcrd |= {rroii__ynd.name for rroii__ynd in stmt.list_vars()}
            tuizd__sirye.append(stmt)
        tuizd__sirye.reverse()
        block.body = tuizd__sirye
    typemap.pop(iuk__tyh.name)
    blocks[veozx__sdmzw].body.pop()

    def trim_empty_parfor_branches(parfor):
        qprb__uejef = False
        blocks = parfor.loop_body.copy()
        for gnh__lezh, block in blocks.items():
            if len(block.body):
                zxf__elckf = block.body[-1]
                if isinstance(zxf__elckf, ir.Branch):
                    if len(blocks[zxf__elckf.truebr].body) == 1 and len(blocks
                        [zxf__elckf.falsebr].body) == 1:
                        nwcd__awp = blocks[zxf__elckf.truebr].body[0]
                        tvh__vchwk = blocks[zxf__elckf.falsebr].body[0]
                        if isinstance(nwcd__awp, ir.Jump) and isinstance(
                            tvh__vchwk, ir.Jump
                            ) and nwcd__awp.target == tvh__vchwk.target:
                            parfor.loop_body[gnh__lezh].body[-1] = ir.Jump(
                                nwcd__awp.target, zxf__elckf.loc)
                            qprb__uejef = True
                    elif len(blocks[zxf__elckf.truebr].body) == 1:
                        nwcd__awp = blocks[zxf__elckf.truebr].body[0]
                        if isinstance(nwcd__awp, ir.Jump
                            ) and nwcd__awp.target == zxf__elckf.falsebr:
                            parfor.loop_body[gnh__lezh].body[-1] = ir.Jump(
                                nwcd__awp.target, zxf__elckf.loc)
                            qprb__uejef = True
                    elif len(blocks[zxf__elckf.falsebr].body) == 1:
                        tvh__vchwk = blocks[zxf__elckf.falsebr].body[0]
                        if isinstance(tvh__vchwk, ir.Jump
                            ) and tvh__vchwk.target == zxf__elckf.truebr:
                            parfor.loop_body[gnh__lezh].body[-1] = ir.Jump(
                                tvh__vchwk.target, zxf__elckf.loc)
                            qprb__uejef = True
        return qprb__uejef
    qprb__uejef = True
    while qprb__uejef:
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
        qprb__uejef = trim_empty_parfor_branches(parfor)
    wwe__psec = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        wwe__psec &= len(block.body) == 0
    if wwe__psec:
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
    pprrz__jmy = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                pprrz__jmy += 1
                parfor = stmt
                zrk__ipkox = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = zrk__ipkox.scope
                loc = ir.Loc('parfors_dummy', -1)
                ekj__sjpv = ir.Var(scope, mk_unique_var('$const'), loc)
                zrk__ipkox.body.append(ir.Assign(ir.Const(0, loc),
                    ekj__sjpv, loc))
                zrk__ipkox.body.append(ir.Return(ekj__sjpv, loc))
                hdcah__naqoa = compute_cfg_from_blocks(parfor.loop_body)
                for ezsn__dgr in hdcah__naqoa.dead_nodes():
                    del parfor.loop_body[ezsn__dgr]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                zrk__ipkox = parfor.loop_body[max(parfor.loop_body.keys())]
                zrk__ipkox.body.pop()
                zrk__ipkox.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return pprrz__jmy


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
            rze__filnf = self.overloads.get(tuple(args))
            if rze__filnf is not None:
                return rze__filnf.entry_point
            self._pre_compile(args, return_type, flags)
            uodt__uzhf = self.func_ir
            jhqj__cudw = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=jhqj__cudw):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=uodt__uzhf, args=args,
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
        wtt__ellit = copy.deepcopy(flags)
        wtt__ellit.no_rewrites = True

        def compile_local(the_ir, the_flags):
            gyjz__lksj = pipeline_class(typingctx, targetctx, library, args,
                return_type, the_flags, locals)
            return gyjz__lksj.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        kcay__quofa = compile_local(func_ir, wtt__ellit)
        wugu__hjma = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    wugu__hjma = compile_local(func_ir, flags)
                except Exception as fbfkk__iiyjt:
                    pass
        if wugu__hjma is not None:
            cres = wugu__hjma
        else:
            cres = kcay__quofa
        return cres
    else:
        gyjz__lksj = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return gyjz__lksj.compile_ir(func_ir=func_ir, lifted=lifted,
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
    istl__fspqx = self.get_data_type(typ.dtype)
    ruy__ush = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        ruy__ush):
        fohe__lqn = ary.ctypes.data
        cfrz__jtyi = self.add_dynamic_addr(builder, fohe__lqn, info=str(
            type(fohe__lqn)))
        bkffw__osi = self.add_dynamic_addr(builder, id(ary), info=str(type(
            ary)))
        self.global_arrays.append(ary)
    else:
        tnf__xmi = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            tnf__xmi = tnf__xmi.view('int64')
        yxu__fduk = Constant.array(Type.int(8), bytearray(tnf__xmi.data))
        cfrz__jtyi = cgutils.global_constant(builder, '.const.array.data',
            yxu__fduk)
        cfrz__jtyi.align = self.get_abi_alignment(istl__fspqx)
        bkffw__osi = None
    xjbq__klld = self.get_value_type(types.intp)
    weod__vxiyu = [self.get_constant(types.intp, jzx__xrntl) for jzx__xrntl in
        ary.shape]
    qoz__cfx = Constant.array(xjbq__klld, weod__vxiyu)
    fak__usgdi = [self.get_constant(types.intp, jzx__xrntl) for jzx__xrntl in
        ary.strides]
    otb__gktnj = Constant.array(xjbq__klld, fak__usgdi)
    knvjz__hnyzp = self.get_constant(types.intp, ary.dtype.itemsize)
    ytn__ocf = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        ytn__ocf, knvjz__hnyzp, cfrz__jtyi.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), qoz__cfx, otb__gktnj])


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
    ero__hys = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    zpo__ftgwu = lir.Function(module, ero__hys, name='nrt_atomic_{0}'.
        format(op))
    [gqt__lhamj] = zpo__ftgwu.args
    uhlw__nym = zpo__ftgwu.append_basic_block()
    builder = lir.IRBuilder(uhlw__nym)
    vqywn__izvk = lir.Constant(_word_type, 1)
    if False:
        vgsn__zns = builder.atomic_rmw(op, gqt__lhamj, vqywn__izvk,
            ordering=ordering)
        res = getattr(builder, op)(vgsn__zns, vqywn__izvk)
        builder.ret(res)
    else:
        vgsn__zns = builder.load(gqt__lhamj)
        znb__wlkb = getattr(builder, op)(vgsn__zns, vqywn__izvk)
        ezlid__qerq = builder.icmp_signed('!=', vgsn__zns, lir.Constant(
            vgsn__zns.type, -1))
        with cgutils.if_likely(builder, ezlid__qerq):
            builder.store(znb__wlkb, gqt__lhamj)
        builder.ret(znb__wlkb)
    return zpo__ftgwu


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
        ndvsy__hge = state.targetctx.codegen()
        state.library = ndvsy__hge.create_library(state.func_id.func_qualname)
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    czqx__wdpsr = state.func_ir
    typemap = state.typemap
    xgalg__udlf = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    del__ntmdl = state.metadata
    kjvsv__kuyi = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        douov__txpqa = (funcdesc.PythonFunctionDescriptor.
            from_specialized_function(czqx__wdpsr, typemap, xgalg__udlf,
            calltypes, mangler=targetctx.mangler, inline=flags.forceinline,
            noalias=flags.noalias, abi_tags=[flags.get_mangle_string()]))
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            wgg__urbh = lowering.Lower(targetctx, library, douov__txpqa,
                czqx__wdpsr, metadata=del__ntmdl)
            wgg__urbh.lower()
            if not flags.no_cpython_wrapper:
                wgg__urbh.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(xgalg__udlf, (types.Optional, types.
                        Generator)):
                        pass
                    else:
                        wgg__urbh.create_cfunc_wrapper()
            wrd__bxs = wgg__urbh.env
            qiiw__rrg = wgg__urbh.call_helper
            del wgg__urbh
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(douov__txpqa, qiiw__rrg, cfunc=None,
                env=wrd__bxs)
        else:
            wnc__qyz = targetctx.get_executable(library, douov__txpqa, wrd__bxs
                )
            targetctx.insert_user_function(wnc__qyz, douov__txpqa, [library])
            state['cr'] = _LowerResult(douov__txpqa, qiiw__rrg, cfunc=
                wnc__qyz, env=wrd__bxs)
        del__ntmdl['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        xarj__uuu = llvm.passmanagers.dump_refprune_stats()
        del__ntmdl['prune_stats'] = xarj__uuu - kjvsv__kuyi
        del__ntmdl['llvm_pass_timings'] = library.recorded_timings
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
        isa__yzk = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, isa__yzk), likely
            =False):
            c.builder.store(cgutils.true_bit, errorptr)
            iovws__cpe.do_break()
        ttkbf__qhzr = c.builder.icmp_signed('!=', isa__yzk, expected_typobj)
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(ttkbf__qhzr, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, isa__yzk)
                c.pyapi.decref(isa__yzk)
                iovws__cpe.do_break()
        c.pyapi.decref(isa__yzk)
    wzhl__dec, list = listobj.ListInstance.allocate_ex(c.context, c.builder,
        typ, size)
    with c.builder.if_else(wzhl__dec, likely=True) as (ngi__tfxb, drop__sdalq):
        with ngi__tfxb:
            list.size = size
            lty__syys = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                lty__syys), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        lty__syys))
                    with cgutils.for_range(c.builder, size) as iovws__cpe:
                        itemobj = c.pyapi.list_getitem(obj, iovws__cpe.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        tmge__ayjs = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(tmge__ayjs.is_error, likely=
                            False):
                            c.builder.store(cgutils.true_bit, errorptr)
                            iovws__cpe.do_break()
                        list.setitem(iovws__cpe.index, tmge__ayjs.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with drop__sdalq:
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
    sfgaa__buiq, ufye__ate, umy__oceen, wqdf__kwrhz, nbir__ktg = (
        compile_time_get_string_data(literal_string))
    wwnwv__qleaw = builder.module
    gv = context.insert_const_bytes(wwnwv__qleaw, sfgaa__buiq)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        ufye__ate), context.get_constant(types.int32, umy__oceen), context.
        get_constant(types.uint32, wqdf__kwrhz), context.get_constant(
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
    mtv__sfy = None
    if isinstance(shape, types.Integer):
        mtv__sfy = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(jzx__xrntl, (types.Integer, types.IntEnumMember)) for
            jzx__xrntl in shape):
            mtv__sfy = len(shape)
    return mtv__sfy


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
            mtv__sfy = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if mtv__sfy == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(mtv__sfy))
        else:
            return name,
    elif isinstance(obj, ir.Const):
        if isinstance(obj.value, tuple):
            return obj.value
        else:
            return obj.value,
    elif isinstance(obj, tuple):

        def get_names(x):
            epn__frgz = self._get_names(x)
            if len(epn__frgz) != 0:
                return epn__frgz[0]
            return epn__frgz
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    epn__frgz = self._get_names(obj)
    if len(epn__frgz) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(epn__frgz[0])


def get_equiv_set(self, obj):
    epn__frgz = self._get_names(obj)
    if len(epn__frgz) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(epn__frgz[0])


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
    snd__ehgqg = []
    for dldwe__wor in func_ir.arg_names:
        if dldwe__wor in typemap and isinstance(typemap[dldwe__wor], types.
            containers.UniTuple) and typemap[dldwe__wor].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(dldwe__wor))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for vaj__luts in func_ir.blocks.values():
        for stmt in vaj__luts.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    nzf__duoad = getattr(val, 'code', None)
                    if nzf__duoad is not None:
                        if getattr(val, 'closure', None) is not None:
                            cahl__eney = '<creating a function from a closure>'
                            nbjy__sbn = ''
                        else:
                            cahl__eney = nzf__duoad.co_name
                            nbjy__sbn = '(%s) ' % cahl__eney
                    else:
                        cahl__eney = '<could not ascertain use case>'
                        nbjy__sbn = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (cahl__eney, nbjy__sbn))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                mmu__wjtzw = False
                if isinstance(val, pytypes.FunctionType):
                    mmu__wjtzw = val in {numba.gdb, numba.gdb_init}
                if not mmu__wjtzw:
                    mmu__wjtzw = getattr(val, '_name', '') == 'gdb_internal'
                if mmu__wjtzw:
                    snd__ehgqg.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    sgts__hkds = func_ir.get_definition(var)
                    mkjir__xtzyh = guard(find_callname, func_ir, sgts__hkds)
                    if mkjir__xtzyh and mkjir__xtzyh[1] == 'numpy':
                        ty = getattr(numpy, mkjir__xtzyh[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    itqab__aurm = '' if var.startswith('$'
                        ) else "'{}' ".format(var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(itqab__aurm), loc=stmt.loc)
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
    if len(snd__ehgqg) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        ebs__zexyg = '\n'.join([x.strformat() for x in snd__ehgqg])
        raise errors.UnsupportedError(msg % ebs__zexyg)


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
    yadbw__lkdjg, rroii__ynd = next(iter(val.items()))
    ihdir__nyxd = typeof_impl(yadbw__lkdjg, c)
    gjq__enl = typeof_impl(rroii__ynd, c)
    if ihdir__nyxd is None or gjq__enl is None:
        raise ValueError(
            f'Cannot type dict element type {type(yadbw__lkdjg)}, {type(rroii__ynd)}'
            )
    return types.DictType(ihdir__nyxd, gjq__enl)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    mmrh__duu = cgutils.alloca_once_value(c.builder, val)
    wte__ngeg = c.pyapi.object_hasattr_string(val, '_opaque')
    dnlll__foljv = c.builder.icmp_unsigned('==', wte__ngeg, lir.Constant(
        wte__ngeg.type, 0))
    hfpmu__teg = typ.key_type
    hgipf__yxct = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(hfpmu__teg, hgipf__yxct)

    def copy_dict(out_dict, in_dict):
        for yadbw__lkdjg, rroii__ynd in in_dict.items():
            out_dict[yadbw__lkdjg] = rroii__ynd
    with c.builder.if_then(dnlll__foljv):
        vqymn__cred = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        ejwd__rxqa = c.pyapi.call_function_objargs(vqymn__cred, [])
        xwik__gjww = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(xwik__gjww, [ejwd__rxqa, val])
        c.builder.store(ejwd__rxqa, mmrh__duu)
    val = c.builder.load(mmrh__duu)
    ekw__bqwya = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    okejr__gps = c.pyapi.object_type(val)
    ljm__dqi = c.builder.icmp_unsigned('==', okejr__gps, ekw__bqwya)
    with c.builder.if_else(ljm__dqi) as (tuwcc__bit, bthuu__dfqup):
        with tuwcc__bit:
            hbtol__gofn = c.pyapi.object_getattr_string(val, '_opaque')
            dxcyi__rhq = types.MemInfoPointer(types.voidptr)
            tmge__ayjs = c.unbox(dxcyi__rhq, hbtol__gofn)
            mi = tmge__ayjs.value
            osybs__srx = dxcyi__rhq, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *osybs__srx)
            elk__wfce = context.get_constant_null(osybs__srx[1])
            args = mi, elk__wfce
            ilqqj__ycx, owwtj__rxn = c.pyapi.call_jit_code(convert, sig, args)
            c.context.nrt.decref(c.builder, typ, owwtj__rxn)
            c.pyapi.decref(hbtol__gofn)
            wkkrf__visl = c.builder.basic_block
        with bthuu__dfqup:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", okejr__gps, ekw__bqwya)
            xsq__iau = c.builder.basic_block
    inxyx__tkc = c.builder.phi(owwtj__rxn.type)
    rmhsu__ser = c.builder.phi(ilqqj__ycx.type)
    inxyx__tkc.add_incoming(owwtj__rxn, wkkrf__visl)
    inxyx__tkc.add_incoming(owwtj__rxn.type(None), xsq__iau)
    rmhsu__ser.add_incoming(ilqqj__ycx, wkkrf__visl)
    rmhsu__ser.add_incoming(cgutils.true_bit, xsq__iau)
    c.pyapi.decref(ekw__bqwya)
    c.pyapi.decref(okejr__gps)
    with c.builder.if_then(dnlll__foljv):
        c.pyapi.decref(val)
    return NativeValue(inxyx__tkc, is_error=rmhsu__ser)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, ncu__tif = args
    if isinstance(a, types.List) and isinstance(ncu__tif, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(ncu__tif, types.List):
        return signature(ncu__tif, types.intp, ncu__tif)


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
        lhyag__sfupz, syhd__sngxe = 0, 1
    else:
        lhyag__sfupz, syhd__sngxe = 1, 0
    ftuqs__seprc = ListInstance(context, builder, sig.args[lhyag__sfupz],
        args[lhyag__sfupz])
    sdzkj__gygb = ftuqs__seprc.size
    yclb__thr = args[syhd__sngxe]
    lty__syys = lir.Constant(yclb__thr.type, 0)
    yclb__thr = builder.select(cgutils.is_neg_int(builder, yclb__thr),
        lty__syys, yclb__thr)
    ytn__ocf = builder.mul(yclb__thr, sdzkj__gygb)
    zep__wxxe = ListInstance.allocate(context, builder, sig.return_type,
        ytn__ocf)
    zep__wxxe.size = ytn__ocf
    with cgutils.for_range_slice(builder, lty__syys, ytn__ocf, sdzkj__gygb,
        inc=True) as (mcw__bkk, _):
        with cgutils.for_range(builder, sdzkj__gygb) as iovws__cpe:
            value = ftuqs__seprc.getitem(iovws__cpe.index)
            zep__wxxe.setitem(builder.add(iovws__cpe.index, mcw__bkk),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, zep__wxxe.value)


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    ytn__ocf = payload.used
    listobj = c.pyapi.list_new(ytn__ocf)
    wzhl__dec = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(wzhl__dec, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(ytn__ocf.
            type, 0))
        with payload._iterate() as iovws__cpe:
            i = c.builder.load(index)
            item = iovws__cpe.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return wzhl__dec, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    gso__utyi = h.type
    ljtty__fxp = self.mask
    dtype = self._ty.dtype
    poko__yqc = context.typing_context
    fnty = poko__yqc.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(poko__yqc, (dtype, dtype), {})
    sulp__ceaj = context.get_function(fnty, sig)
    xpw__bvwc = ir.Constant(gso__utyi, 1)
    kayx__byduu = ir.Constant(gso__utyi, 5)
    txuy__uau = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, ljtty__fxp))
    if for_insert:
        lqvag__igmf = ljtty__fxp.type(-1)
        htp__rksu = cgutils.alloca_once_value(builder, lqvag__igmf)
    ryl__gvoao = builder.append_basic_block('lookup.body')
    sud__sleju = builder.append_basic_block('lookup.found')
    xkz__bxpz = builder.append_basic_block('lookup.not_found')
    tmvud__varbq = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        lehy__bfi = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, lehy__bfi)):
            fchv__alw = sulp__ceaj(builder, (item, entry.key))
            with builder.if_then(fchv__alw):
                builder.branch(sud__sleju)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, lehy__bfi)):
            builder.branch(xkz__bxpz)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, lehy__bfi)):
                akc__ftu = builder.load(htp__rksu)
                akc__ftu = builder.select(builder.icmp_unsigned('==',
                    akc__ftu, lqvag__igmf), i, akc__ftu)
                builder.store(akc__ftu, htp__rksu)
    with cgutils.for_range(builder, ir.Constant(gso__utyi, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, xpw__bvwc)
        i = builder.and_(i, ljtty__fxp)
        builder.store(i, index)
    builder.branch(ryl__gvoao)
    with builder.goto_block(ryl__gvoao):
        i = builder.load(index)
        check_entry(i)
        rgcc__kigt = builder.load(txuy__uau)
        rgcc__kigt = builder.lshr(rgcc__kigt, kayx__byduu)
        i = builder.add(xpw__bvwc, builder.mul(i, kayx__byduu))
        i = builder.and_(ljtty__fxp, builder.add(i, rgcc__kigt))
        builder.store(i, index)
        builder.store(rgcc__kigt, txuy__uau)
        builder.branch(ryl__gvoao)
    with builder.goto_block(xkz__bxpz):
        if for_insert:
            i = builder.load(index)
            akc__ftu = builder.load(htp__rksu)
            i = builder.select(builder.icmp_unsigned('==', akc__ftu,
                lqvag__igmf), i, akc__ftu)
            builder.store(i, index)
        builder.branch(tmvud__varbq)
    with builder.goto_block(sud__sleju):
        builder.branch(tmvud__varbq)
    builder.position_at_end(tmvud__varbq)
    mmu__wjtzw = builder.phi(ir.IntType(1), 'found')
    mmu__wjtzw.add_incoming(cgutils.true_bit, sud__sleju)
    mmu__wjtzw.add_incoming(cgutils.false_bit, xkz__bxpz)
    return mmu__wjtzw, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    sqre__nbi = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    mouq__gqcig = payload.used
    xpw__bvwc = ir.Constant(mouq__gqcig.type, 1)
    mouq__gqcig = payload.used = builder.add(mouq__gqcig, xpw__bvwc)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, sqre__nbi), likely=True):
        payload.fill = builder.add(payload.fill, xpw__bvwc)
    if do_resize:
        self.upsize(mouq__gqcig)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    mmu__wjtzw, i = payload._lookup(item, h, for_insert=True)
    okq__tkwvv = builder.not_(mmu__wjtzw)
    with builder.if_then(okq__tkwvv):
        entry = payload.get_entry(i)
        sqre__nbi = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        mouq__gqcig = payload.used
        xpw__bvwc = ir.Constant(mouq__gqcig.type, 1)
        mouq__gqcig = payload.used = builder.add(mouq__gqcig, xpw__bvwc)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, sqre__nbi), likely=True):
            payload.fill = builder.add(payload.fill, xpw__bvwc)
        if do_resize:
            self.upsize(mouq__gqcig)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    mouq__gqcig = payload.used
    xpw__bvwc = ir.Constant(mouq__gqcig.type, 1)
    mouq__gqcig = payload.used = self._builder.sub(mouq__gqcig, xpw__bvwc)
    if do_resize:
        self.downsize(mouq__gqcig)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    izftu__iydxb = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, izftu__iydxb)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    hvit__ljt = payload
    wzhl__dec = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(wzhl__dec), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with hvit__ljt._iterate() as iovws__cpe:
        entry = iovws__cpe.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(hvit__ljt.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as iovws__cpe:
        entry = iovws__cpe.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    wzhl__dec = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(wzhl__dec), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    wzhl__dec = cgutils.alloca_once_value(builder, cgutils.true_bit)
    gso__utyi = context.get_value_type(types.intp)
    lty__syys = ir.Constant(gso__utyi, 0)
    xpw__bvwc = ir.Constant(gso__utyi, 1)
    pecwp__fkphi = context.get_data_type(types.SetPayload(self._ty))
    eztr__cmew = context.get_abi_sizeof(pecwp__fkphi)
    luptd__sdl = self._entrysize
    eztr__cmew -= luptd__sdl
    qovm__nkly, mohnz__knk = cgutils.muladd_with_overflow(builder, nentries,
        ir.Constant(gso__utyi, luptd__sdl), ir.Constant(gso__utyi, eztr__cmew))
    with builder.if_then(mohnz__knk, likely=False):
        builder.store(cgutils.false_bit, wzhl__dec)
    with builder.if_then(builder.load(wzhl__dec), likely=True):
        if realloc:
            krtw__rnbjl = self._set.meminfo
            gqt__lhamj = context.nrt.meminfo_varsize_alloc(builder,
                krtw__rnbjl, size=qovm__nkly)
            dgndp__yxks = cgutils.is_null(builder, gqt__lhamj)
        else:
            zbl__wlqoj = _imp_dtor(context, builder.module, self._ty)
            krtw__rnbjl = context.nrt.meminfo_new_varsize_dtor(builder,
                qovm__nkly, builder.bitcast(zbl__wlqoj, cgutils.voidptr_t))
            dgndp__yxks = cgutils.is_null(builder, krtw__rnbjl)
        with builder.if_else(dgndp__yxks, likely=False) as (rye__blr, ngi__tfxb
            ):
            with rye__blr:
                builder.store(cgutils.false_bit, wzhl__dec)
            with ngi__tfxb:
                if not realloc:
                    self._set.meminfo = krtw__rnbjl
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, qovm__nkly, 255)
                payload.used = lty__syys
                payload.fill = lty__syys
                payload.finger = lty__syys
                fsw__zcpm = builder.sub(nentries, xpw__bvwc)
                payload.mask = fsw__zcpm
    return builder.load(wzhl__dec)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    wzhl__dec = cgutils.alloca_once_value(builder, cgutils.true_bit)
    gso__utyi = context.get_value_type(types.intp)
    lty__syys = ir.Constant(gso__utyi, 0)
    xpw__bvwc = ir.Constant(gso__utyi, 1)
    pecwp__fkphi = context.get_data_type(types.SetPayload(self._ty))
    eztr__cmew = context.get_abi_sizeof(pecwp__fkphi)
    luptd__sdl = self._entrysize
    eztr__cmew -= luptd__sdl
    ljtty__fxp = src_payload.mask
    nentries = builder.add(xpw__bvwc, ljtty__fxp)
    qovm__nkly = builder.add(ir.Constant(gso__utyi, eztr__cmew), builder.
        mul(ir.Constant(gso__utyi, luptd__sdl), nentries))
    with builder.if_then(builder.load(wzhl__dec), likely=True):
        zbl__wlqoj = _imp_dtor(context, builder.module, self._ty)
        krtw__rnbjl = context.nrt.meminfo_new_varsize_dtor(builder,
            qovm__nkly, builder.bitcast(zbl__wlqoj, cgutils.voidptr_t))
        dgndp__yxks = cgutils.is_null(builder, krtw__rnbjl)
        with builder.if_else(dgndp__yxks, likely=False) as (rye__blr, ngi__tfxb
            ):
            with rye__blr:
                builder.store(cgutils.false_bit, wzhl__dec)
            with ngi__tfxb:
                self._set.meminfo = krtw__rnbjl
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = lty__syys
                payload.mask = ljtty__fxp
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, luptd__sdl)
                with src_payload._iterate() as iovws__cpe:
                    context.nrt.incref(builder, self._ty.dtype, iovws__cpe.
                        entry.key)
    return builder.load(wzhl__dec)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    gct__qov = context.get_value_type(types.voidptr)
    lamyz__xbbej = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [gct__qov, lamyz__xbbej, gct__qov])
    aanpo__gwtd = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=aanpo__gwtd)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        uzor__tsc = builder.bitcast(fn.args[0], cgutils.voidptr_t.as_pointer())
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, uzor__tsc)
        with payload._iterate() as iovws__cpe:
            entry = iovws__cpe.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    qqzb__brndq, = sig.args
    qxxg__femqs, = args
    ufq__dueva = numba.core.imputils.call_len(context, builder, qqzb__brndq,
        qxxg__femqs)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, ufq__dueva)
    with numba.core.imputils.for_iter(context, builder, qqzb__brndq,
        qxxg__femqs) as iovws__cpe:
        inst.add(iovws__cpe.value)
        context.nrt.decref(builder, set_type.dtype, iovws__cpe.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    qqzb__brndq = sig.args[1]
    qxxg__femqs = args[1]
    ufq__dueva = numba.core.imputils.call_len(context, builder, qqzb__brndq,
        qxxg__femqs)
    if ufq__dueva is not None:
        xkv__cvkhv = builder.add(inst.payload.used, ufq__dueva)
        inst.upsize(xkv__cvkhv)
    with numba.core.imputils.for_iter(context, builder, qqzb__brndq,
        qxxg__femqs) as iovws__cpe:
        gyiy__wuk = context.cast(builder, iovws__cpe.value, qqzb__brndq.
            dtype, inst.dtype)
        inst.add(gyiy__wuk)
        context.nrt.decref(builder, qqzb__brndq.dtype, iovws__cpe.value)
    if ufq__dueva is not None:
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
