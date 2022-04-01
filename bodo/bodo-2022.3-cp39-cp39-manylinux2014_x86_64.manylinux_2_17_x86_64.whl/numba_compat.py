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
    yes__wrv = numba.core.bytecode.FunctionIdentity.from_function(func)
    ipyhj__asdge = numba.core.interpreter.Interpreter(yes__wrv)
    fclsr__ecpqq = numba.core.bytecode.ByteCode(func_id=yes__wrv)
    func_ir = ipyhj__asdge.interpret(fclsr__ecpqq)
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
        gcq__dnk = InlineClosureCallPass(func_ir, numba.core.cpu.
            ParallelOptions(False), {}, False)
        gcq__dnk.run()
    swg__uwi = numba.core.postproc.PostProcessor(func_ir)
    swg__uwi.run(emit_dels)
    return func_ir


if _check_numba_change:
    lines = inspect.getsource(numba.core.compiler.run_frontend)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '8c2477a793b2c08d56430997880974ac12c5570e69c9e54d37d694b322ea18b6':
        warnings.warn('numba.core.compiler.run_frontend has changed')
numba.core.compiler.run_frontend = run_frontend


def visit_vars_stmt(stmt, callback, cbdata):
    for t, mmmyu__lykyp in visit_vars_extensions.items():
        if isinstance(stmt, t):
            mmmyu__lykyp(stmt, callback, cbdata)
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
    hgqjo__zmw = ['ravel', 'transpose', 'reshape']
    for trx__yku in blocks.values():
        for rgrt__gis in trx__yku.body:
            if type(rgrt__gis) in alias_analysis_extensions:
                mmmyu__lykyp = alias_analysis_extensions[type(rgrt__gis)]
                mmmyu__lykyp(rgrt__gis, args, typemap, func_ir, alias_map,
                    arg_aliases)
            if isinstance(rgrt__gis, ir.Assign):
                frzl__qyv = rgrt__gis.value
                iynk__hsua = rgrt__gis.target.name
                if is_immutable_type(iynk__hsua, typemap):
                    continue
                if isinstance(frzl__qyv, ir.Var
                    ) and iynk__hsua != frzl__qyv.name:
                    _add_alias(iynk__hsua, frzl__qyv.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr) and (frzl__qyv.op ==
                    'cast' or frzl__qyv.op in ['getitem', 'static_getitem']):
                    _add_alias(iynk__hsua, frzl__qyv.value.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr
                    ) and frzl__qyv.op == 'inplace_binop':
                    _add_alias(iynk__hsua, frzl__qyv.lhs.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr
                    ) and frzl__qyv.op == 'getattr' and frzl__qyv.attr in ['T',
                    'ctypes', 'flat']:
                    _add_alias(iynk__hsua, frzl__qyv.value.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr
                    ) and frzl__qyv.op == 'getattr' and frzl__qyv.attr not in [
                    'shape'] and frzl__qyv.value.name in arg_aliases:
                    _add_alias(iynk__hsua, frzl__qyv.value.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr
                    ) and frzl__qyv.op == 'getattr' and frzl__qyv.attr in (
                    'loc', 'iloc', 'iat', '_obj', 'obj', 'codes', '_df'):
                    _add_alias(iynk__hsua, frzl__qyv.value.name, alias_map,
                        arg_aliases)
                if isinstance(frzl__qyv, ir.Expr) and frzl__qyv.op in (
                    'build_tuple', 'build_list', 'build_set'
                    ) and not is_immutable_type(iynk__hsua, typemap):
                    for agu__zbhc in frzl__qyv.items:
                        _add_alias(iynk__hsua, agu__zbhc.name, alias_map,
                            arg_aliases)
                if isinstance(frzl__qyv, ir.Expr) and frzl__qyv.op == 'call':
                    sqjd__icwdy = guard(find_callname, func_ir, frzl__qyv,
                        typemap)
                    if sqjd__icwdy is None:
                        continue
                    ubxdf__klte, jasg__cgwjx = sqjd__icwdy
                    if sqjd__icwdy in alias_func_extensions:
                        qyzwi__lvy = alias_func_extensions[sqjd__icwdy]
                        qyzwi__lvy(iynk__hsua, frzl__qyv.args, alias_map,
                            arg_aliases)
                    if jasg__cgwjx == 'numpy' and ubxdf__klte in hgqjo__zmw:
                        _add_alias(iynk__hsua, frzl__qyv.args[0].name,
                            alias_map, arg_aliases)
                    if isinstance(jasg__cgwjx, ir.Var
                        ) and ubxdf__klte in hgqjo__zmw:
                        _add_alias(iynk__hsua, jasg__cgwjx.name, alias_map,
                            arg_aliases)
    oattx__erjtb = copy.deepcopy(alias_map)
    for agu__zbhc in oattx__erjtb:
        for kqfh__clngr in oattx__erjtb[agu__zbhc]:
            alias_map[agu__zbhc] |= alias_map[kqfh__clngr]
        for kqfh__clngr in oattx__erjtb[agu__zbhc]:
            alias_map[kqfh__clngr] = alias_map[agu__zbhc]
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
    lnur__extqf = compute_cfg_from_blocks(func_ir.blocks)
    uizo__pmsj = compute_use_defs(func_ir.blocks)
    qdyik__omvce = compute_live_map(lnur__extqf, func_ir.blocks, uizo__pmsj
        .usemap, uizo__pmsj.defmap)
    kpa__hgda = True
    while kpa__hgda:
        kpa__hgda = False
        for mhsr__kkju, block in func_ir.blocks.items():
            lives = {agu__zbhc.name for agu__zbhc in block.terminator.
                list_vars()}
            for rbw__spdsr, chafx__bgp in lnur__extqf.successors(mhsr__kkju):
                lives |= qdyik__omvce[rbw__spdsr]
            gic__woh = [block.terminator]
            for stmt in reversed(block.body[:-1]):
                if isinstance(stmt, ir.Assign):
                    iynk__hsua = stmt.target
                    cny__gxt = stmt.value
                    if iynk__hsua.name not in lives:
                        if isinstance(cny__gxt, ir.Expr
                            ) and cny__gxt.op == 'make_function':
                            continue
                        if isinstance(cny__gxt, ir.Expr
                            ) and cny__gxt.op == 'getattr':
                            continue
                        if isinstance(cny__gxt, ir.Const):
                            continue
                        if typemap and isinstance(typemap.get(iynk__hsua,
                            None), types.Function):
                            continue
                        if isinstance(cny__gxt, ir.Expr
                            ) and cny__gxt.op == 'build_map':
                            continue
                    if isinstance(cny__gxt, ir.Var
                        ) and iynk__hsua.name == cny__gxt.name:
                        continue
                if isinstance(stmt, ir.Del):
                    if stmt.value not in lives:
                        continue
                if type(stmt) in analysis.ir_extension_usedefs:
                    ioqg__rkr = analysis.ir_extension_usedefs[type(stmt)]
                    qnc__qxp, mqxfv__yxjaf = ioqg__rkr(stmt)
                    lives -= mqxfv__yxjaf
                    lives |= qnc__qxp
                else:
                    lives |= {agu__zbhc.name for agu__zbhc in stmt.list_vars()}
                    if isinstance(stmt, ir.Assign):
                        lives.remove(iynk__hsua.name)
                gic__woh.append(stmt)
            gic__woh.reverse()
            if len(block.body) != len(gic__woh):
                kpa__hgda = True
            block.body = gic__woh


ir_utils.dead_code_elimination = mini_dce
numba.core.typed_passes.dead_code_elimination = mini_dce
numba.core.inline_closurecall.dead_code_elimination = mini_dce
from numba.core.cpu_options import InlineOptions


def make_overload_template(func, overload_func, jit_options, strict, inline,
    prefer_literal=False, **kwargs):
    bftm__zyd = getattr(func, '__name__', str(func))
    name = 'OverloadTemplate_%s' % (bftm__zyd,)
    no_unliteral = kwargs.pop('no_unliteral', False)
    base = numba.core.typing.templates._OverloadFunctionTemplate
    djvlt__pngad = dict(key=func, _overload_func=staticmethod(overload_func
        ), _impl_cache={}, _compiled_overloads={}, _jit_options=jit_options,
        _strict=strict, _inline=staticmethod(InlineOptions(inline)),
        _inline_overloads={}, prefer_literal=prefer_literal, _no_unliteral=
        no_unliteral, metadata=kwargs)
    return type(base)(name, (base,), djvlt__pngad)


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
            for kylla__ostve in fnty.templates:
                self._inline_overloads.update(kylla__ostve._inline_overloads)
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
    djvlt__pngad = dict(key=typ, _attr=attr, _impl_cache={}, _inline=
        staticmethod(InlineOptions(inline)), _inline_overloads={},
        _no_unliteral=no_unliteral, _overload_func=staticmethod(
        overload_func), prefer_literal=prefer_literal, metadata=kwargs)
    obj = type(base)(name, (base,), djvlt__pngad)
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
    zdpo__vnxt, yame__wcn = self._get_impl(args, kws)
    if zdpo__vnxt is None:
        return
    caq__ccvb = types.Dispatcher(zdpo__vnxt)
    if not self._inline.is_never_inline:
        from numba.core import compiler, typed_passes
        from numba.core.inline_closurecall import InlineWorker
        pyqik__swlx = zdpo__vnxt._compiler
        flags = compiler.Flags()
        avb__yxkx = pyqik__swlx.targetdescr.typing_context
        bqufh__vam = pyqik__swlx.targetdescr.target_context
        ctch__babg = pyqik__swlx.pipeline_class(avb__yxkx, bqufh__vam, None,
            None, None, flags, None)
        rusm__lyuh = InlineWorker(avb__yxkx, bqufh__vam, pyqik__swlx.locals,
            ctch__babg, flags, None)
        yngy__dvoix = caq__ccvb.dispatcher.get_call_template
        kylla__ostve, ajzp__raeic, lufm__jeu, kws = yngy__dvoix(yame__wcn, kws)
        if lufm__jeu in self._inline_overloads:
            return self._inline_overloads[lufm__jeu]['iinfo'].signature
        ir = rusm__lyuh.run_untyped_passes(caq__ccvb.dispatcher.py_func,
            enable_ssa=True)
        typemap, return_type, calltypes, _ = typed_passes.type_inference_stage(
            self.context, bqufh__vam, ir, lufm__jeu, None)
        ir = PreLowerStripPhis()._strip_phi_nodes(ir)
        ir._definitions = numba.core.ir_utils.build_definitions(ir.blocks)
        sig = Signature(return_type, lufm__jeu, None)
        self._inline_overloads[sig.args] = {'folded_args': lufm__jeu}
        rzdi__wyrkh = _EmptyImplementationEntry('always inlined')
        self._compiled_overloads[sig.args] = rzdi__wyrkh
        if not self._inline.is_always_inline:
            sig = caq__ccvb.get_call_type(self.context, yame__wcn, kws)
            self._compiled_overloads[sig.args] = caq__ccvb.get_overload(sig)
        ufzju__nftu = _inline_info(ir, typemap, calltypes, sig)
        self._inline_overloads[sig.args] = {'folded_args': lufm__jeu,
            'iinfo': ufzju__nftu}
    else:
        sig = caq__ccvb.get_call_type(self.context, yame__wcn, kws)
        if sig is None:
            return None
        self._compiled_overloads[sig.args] = caq__ccvb.get_overload(sig)
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
    bay__ffmq = [True, False]
    ynymw__kgn = [False, True]
    csld__rmvft = _ResolutionFailures(context, self, args, kws, depth=self.
        _depth)
    from numba.core.target_extension import get_local_target
    toqoa__pstwm = get_local_target(context)
    dcu__uceg = utils.order_by_target_specificity(toqoa__pstwm, self.
        templates, fnkey=self.key[0])
    self._depth += 1
    for mpoxe__acq in dcu__uceg:
        jzjqk__ebnd = mpoxe__acq(context)
        mzrl__ofw = bay__ffmq if jzjqk__ebnd.prefer_literal else ynymw__kgn
        mzrl__ofw = [True] if getattr(jzjqk__ebnd, '_no_unliteral', False
            ) else mzrl__ofw
        for qnvo__xrlbb in mzrl__ofw:
            try:
                if qnvo__xrlbb:
                    sig = jzjqk__ebnd.apply(args, kws)
                else:
                    bpgg__ewb = tuple([_unlit_non_poison(a) for a in args])
                    bzh__tlh = {pylc__qawc: _unlit_non_poison(agu__zbhc) for
                        pylc__qawc, agu__zbhc in kws.items()}
                    sig = jzjqk__ebnd.apply(bpgg__ewb, bzh__tlh)
            except Exception as e:
                from numba.core import utils
                if utils.use_new_style_errors() and not isinstance(e,
                    errors.NumbaError):
                    raise e
                else:
                    sig = None
                    csld__rmvft.add_error(jzjqk__ebnd, False, e, qnvo__xrlbb)
            else:
                if sig is not None:
                    self._impl_keys[sig.args] = jzjqk__ebnd.get_impl_key(sig)
                    self._depth -= 1
                    return sig
                else:
                    shuf__rrrnw = getattr(jzjqk__ebnd, 'cases', None)
                    if shuf__rrrnw is not None:
                        msg = 'No match for registered cases:\n%s'
                        msg = msg % '\n'.join(' * {}'.format(x) for x in
                            shuf__rrrnw)
                    else:
                        msg = 'No match.'
                    csld__rmvft.add_error(jzjqk__ebnd, True, msg, qnvo__xrlbb)
    csld__rmvft.raise_error()


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
    kylla__ostve = self.template(context)
    whnj__pkba = None
    omi__ihm = None
    iqdbn__ukny = None
    mzrl__ofw = [True, False] if kylla__ostve.prefer_literal else [False, True]
    mzrl__ofw = [True] if getattr(kylla__ostve, '_no_unliteral', False
        ) else mzrl__ofw
    for qnvo__xrlbb in mzrl__ofw:
        if qnvo__xrlbb:
            try:
                iqdbn__ukny = kylla__ostve.apply(args, kws)
            except Exception as gpq__rzn:
                if isinstance(gpq__rzn, errors.ForceLiteralArg):
                    raise gpq__rzn
                whnj__pkba = gpq__rzn
                iqdbn__ukny = None
            else:
                break
        else:
            ffhdz__fraqe = tuple([_unlit_non_poison(a) for a in args])
            acsb__nlnr = {pylc__qawc: _unlit_non_poison(agu__zbhc) for 
                pylc__qawc, agu__zbhc in kws.items()}
            vgb__kozvc = ffhdz__fraqe == args and kws == acsb__nlnr
            if not vgb__kozvc and iqdbn__ukny is None:
                try:
                    iqdbn__ukny = kylla__ostve.apply(ffhdz__fraqe, acsb__nlnr)
                except Exception as gpq__rzn:
                    from numba.core import utils
                    if utils.use_new_style_errors() and not isinstance(gpq__rzn
                        , errors.NumbaError):
                        raise gpq__rzn
                    if isinstance(gpq__rzn, errors.ForceLiteralArg):
                        if kylla__ostve.prefer_literal:
                            raise gpq__rzn
                    omi__ihm = gpq__rzn
                else:
                    break
    if iqdbn__ukny is None and (omi__ihm is not None or whnj__pkba is not None
        ):
        parf__nvxwr = '- Resolution failure for {} arguments:\n{}\n'
        tzs__fpmei = _termcolor.highlight(parf__nvxwr)
        if numba.core.config.DEVELOPER_MODE:
            jiv__xvuu = ' ' * 4

            def add_bt(error):
                if isinstance(error, BaseException):
                    hocxz__yph = traceback.format_exception(type(error),
                        error, error.__traceback__)
                else:
                    hocxz__yph = ['']
                pcpz__cwr = '\n{}'.format(2 * jiv__xvuu)
                xnhym__htfrf = _termcolor.reset(pcpz__cwr + pcpz__cwr.join(
                    _bt_as_lines(hocxz__yph)))
                return _termcolor.reset(xnhym__htfrf)
        else:
            add_bt = lambda X: ''

        def nested_msg(literalness, e):
            wcax__ctwaf = str(e)
            wcax__ctwaf = wcax__ctwaf if wcax__ctwaf else str(repr(e)
                ) + add_bt(e)
            usomo__uqcf = errors.TypingError(textwrap.dedent(wcax__ctwaf))
            return tzs__fpmei.format(literalness, str(usomo__uqcf))
        import bodo
        if isinstance(whnj__pkba, bodo.utils.typing.BodoError):
            raise whnj__pkba
        if numba.core.config.DEVELOPER_MODE:
            raise errors.TypingError(nested_msg('literal', whnj__pkba) +
                nested_msg('non-literal', omi__ihm))
        else:
            if 'missing a required argument' in whnj__pkba.msg:
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
            raise errors.TypingError(msg, loc=whnj__pkba.loc)
    return iqdbn__ukny


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
    ubxdf__klte = 'PyUnicode_FromStringAndSize'
    fn = self._get_function(fnty, name=ubxdf__klte)
    return self.builder.call(fn, [string, size])


numba.core.pythonapi.PythonAPI.string_from_string_and_size = (
    string_from_string_and_size)


def _compile_for_args(self, *args, **kws):
    assert not kws
    self._compilation_chain_init_hook()
    import bodo

    def error_rewrite(e, issue_type):
        if numba.core.config.SHOW_HELP:
            jijgo__vzuc = errors.error_extras[issue_type]
            e.patch_message('\n'.join((str(e).rstrip(), jijgo__vzuc)))
        if numba.core.config.FULL_TRACEBACKS:
            raise e
        else:
            raise e.with_traceback(None)
    lyye__kisu = []
    for a in args:
        if isinstance(a, numba.core.dispatcher.OmittedArg):
            lyye__kisu.append(types.Omitted(a.value))
        else:
            lyye__kisu.append(self.typeof_pyval(a))
    hne__tqgo = None
    try:
        error = None
        hne__tqgo = self.compile(tuple(lyye__kisu))
    except errors.ForceLiteralArg as e:
        hbuq__mwicq = [i for i in e.requested_args if isinstance(args[i],
            types.Literal) and not isinstance(args[i], types.LiteralStrKeyDict)
            ]
        if hbuq__mwicq:
            quzt__ygfbm = """Repeated literal typing request.
{}.
This is likely caused by an error in typing. Please see nested and suppressed exceptions."""
            inxrs__cju = ', '.join('Arg #{} is {}'.format(i, args[i]) for i in
                sorted(hbuq__mwicq))
            raise errors.CompilerError(quzt__ygfbm.format(inxrs__cju))
        yame__wcn = []
        try:
            for i, agu__zbhc in enumerate(args):
                if i in e.requested_args:
                    if i in e.file_infos:
                        yame__wcn.append(types.FilenameType(args[i], e.
                            file_infos[i]))
                    else:
                        yame__wcn.append(types.literal(args[i]))
                else:
                    yame__wcn.append(args[i])
            args = yame__wcn
        except (OSError, FileNotFoundError) as xpmcr__lvl:
            error = FileNotFoundError(str(xpmcr__lvl) + '\n' + e.loc.
                strformat() + '\n')
        except bodo.utils.typing.BodoError as e:
            error = bodo.utils.typing.BodoError(str(e))
        if error is None:
            try:
                hne__tqgo = self._compile_for_args(*args)
            except TypingError as e:
                error = errors.TypingError(str(e))
            except bodo.utils.typing.BodoError as e:
                error = bodo.utils.typing.BodoError(str(e))
    except errors.TypingError as e:
        ceerw__bza = []
        for i, leg__gow in enumerate(args):
            val = leg__gow.value if isinstance(leg__gow, numba.core.
                dispatcher.OmittedArg) else leg__gow
            try:
                cio__hxmb = typeof(val, Purpose.argument)
            except ValueError as zge__vwt:
                ceerw__bza.append((i, str(zge__vwt)))
            else:
                if cio__hxmb is None:
                    ceerw__bza.append((i,
                        f'cannot determine Numba type of value {val}'))
        if ceerw__bza:
            rakm__gmfs = '\n'.join(f'- argument {i}: {bzb__tlahe}' for i,
                bzb__tlahe in ceerw__bza)
            msg = f"""{str(e).rstrip()} 

This error may have been caused by the following argument(s):
{rakm__gmfs}
"""
            e.patch_message(msg)
        if "Cannot determine Numba type of <class 'numpy.ufunc'>" in e.msg:
            msg = 'Unsupported Numpy ufunc encountered in JIT code'
            error = bodo.utils.typing.BodoError(msg, loc=e.loc)
        elif not numba.core.config.DEVELOPER_MODE:
            if bodo_typing_error_info not in e.msg:
                aeqqy__mtxka = ['Failed in nopython mode pipeline',
                    'Failed in bodo mode pipeline', 'Failed at nopython',
                    'Overload', 'lowering']
                ycwaq__auzm = False
                for hmhk__ovn in aeqqy__mtxka:
                    if hmhk__ovn in e.msg:
                        msg = 'Compilation error. '
                        msg += f'{bodo_typing_error_info}'
                        ycwaq__auzm = True
                        break
                if not ycwaq__auzm:
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
                jijgo__vzuc = errors.error_extras['reportable']
                e.patch_message('\n'.join((str(e).rstrip(), jijgo__vzuc)))
        raise e
    finally:
        self._types_active_call = []
        del args
        if error:
            raise error
    return hne__tqgo


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
    for jcxdp__iksa in cres.library._codegen._engine._defined_symbols:
        if jcxdp__iksa.startswith('cfunc'
            ) and 'get_agg_udf_addr' not in jcxdp__iksa and (
            'bodo_gb_udf_update_local' in jcxdp__iksa or 
            'bodo_gb_udf_combine' in jcxdp__iksa or 'bodo_gb_udf_eval' in
            jcxdp__iksa or 'bodo_gb_apply_general_udfs' in jcxdp__iksa):
            gb_agg_cfunc_addr[jcxdp__iksa
                ] = cres.library.get_pointer_to_function(jcxdp__iksa)


def resolve_join_general_cond_funcs(cres):
    from bodo.ir.join import join_gen_cond_cfunc_addr
    for jcxdp__iksa in cres.library._codegen._engine._defined_symbols:
        if jcxdp__iksa.startswith('cfunc') and ('get_join_cond_addr' not in
            jcxdp__iksa or 'bodo_join_gen_cond' in jcxdp__iksa):
            join_gen_cond_cfunc_addr[jcxdp__iksa
                ] = cres.library.get_pointer_to_function(jcxdp__iksa)


def compile(self, sig):
    import numba.core.event as ev
    from numba.core import sigutils
    from numba.core.compiler_lock import global_compiler_lock
    zdpo__vnxt = self._get_dispatcher_for_current_target()
    if zdpo__vnxt is not self:
        return zdpo__vnxt.compile(sig)
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
            rrqzi__tmjz = self.overloads.get(tuple(args))
            if rrqzi__tmjz is not None:
                return rrqzi__tmjz.entry_point
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
            zuo__ksnxu = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=zuo__ksnxu):
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
    qbeij__ycfww = self._final_module
    nxysh__uyp = []
    ioetj__wobmo = 0
    for fn in qbeij__ycfww.functions:
        ioetj__wobmo += 1
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
            nxysh__uyp.append(fn.name)
    if ioetj__wobmo == 0:
        raise RuntimeError(
            'library unfit for linking: no available functions in %s' % (self,)
            )
    if nxysh__uyp:
        qbeij__ycfww = qbeij__ycfww.clone()
        for name in nxysh__uyp:
            qbeij__ycfww.get_function(name).linkage = 'linkonce_odr'
    self._shared_module = qbeij__ycfww
    return qbeij__ycfww


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
    for hwfb__qemue in self.constraints:
        loc = hwfb__qemue.loc
        with typeinfer.warnings.catch_warnings(filename=loc.filename,
            lineno=loc.line):
            try:
                hwfb__qemue(typeinfer)
            except numba.core.errors.ForceLiteralArg as e:
                errors.append(e)
            except numba.core.errors.TypingError as e:
                numba.core.typeinfer._logger.debug('captured error', exc_info=e
                    )
                skf__tawpz = numba.core.errors.TypingError(str(e), loc=
                    hwfb__qemue.loc, highlighting=False)
                errors.append(numba.core.utils.chain_exception(skf__tawpz, e))
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
                    skf__tawpz = numba.core.errors.TypingError(msg.format(
                        con=hwfb__qemue, err=str(e)), loc=hwfb__qemue.loc,
                        highlighting=False)
                    errors.append(utils.chain_exception(skf__tawpz, e))
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
    for dqes__jjxd in self._failures.values():
        for poqvk__xuww in dqes__jjxd:
            if isinstance(poqvk__xuww.error, ForceLiteralArg):
                raise poqvk__xuww.error
            if isinstance(poqvk__xuww.error, bodo.utils.typing.BodoError):
                raise poqvk__xuww.error
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
    hkia__iotw = False
    gic__woh = [block.terminator]
    for stmt in reversed(block.body[:-1]):
        siu__fdfdr = set()
        pid__ykbdk = lives & alias_set
        for agu__zbhc in pid__ykbdk:
            siu__fdfdr |= alias_map[agu__zbhc]
        lives_n_aliases = lives | siu__fdfdr | arg_aliases
        if type(stmt) in remove_dead_extensions:
            mmmyu__lykyp = remove_dead_extensions[type(stmt)]
            stmt = mmmyu__lykyp(stmt, lives, lives_n_aliases, arg_aliases,
                alias_map, func_ir, typemap)
            if stmt is None:
                hkia__iotw = True
                continue
        if isinstance(stmt, ir.Assign):
            iynk__hsua = stmt.target
            cny__gxt = stmt.value
            if iynk__hsua.name not in lives and has_no_side_effect(cny__gxt,
                lives_n_aliases, call_table):
                hkia__iotw = True
                continue
            if saved_array_analysis and iynk__hsua.name in lives and is_expr(
                cny__gxt, 'getattr'
                ) and cny__gxt.attr == 'shape' and is_array_typ(typemap[
                cny__gxt.value.name]) and cny__gxt.value.name not in lives:
                pnzy__jtti = {agu__zbhc: pylc__qawc for pylc__qawc,
                    agu__zbhc in func_ir.blocks.items()}
                if block in pnzy__jtti:
                    mhsr__kkju = pnzy__jtti[block]
                    cztol__ebg = saved_array_analysis.get_equiv_set(mhsr__kkju)
                    qib__yrz = cztol__ebg.get_equiv_set(cny__gxt.value)
                    if qib__yrz is not None:
                        for agu__zbhc in qib__yrz:
                            if agu__zbhc.endswith('#0'):
                                agu__zbhc = agu__zbhc[:-2]
                            if agu__zbhc in typemap and is_array_typ(typemap
                                [agu__zbhc]) and agu__zbhc in lives:
                                cny__gxt.value = ir.Var(cny__gxt.value.
                                    scope, agu__zbhc, cny__gxt.value.loc)
                                hkia__iotw = True
                                break
            if isinstance(cny__gxt, ir.Var
                ) and iynk__hsua.name == cny__gxt.name:
                hkia__iotw = True
                continue
        if isinstance(stmt, ir.Del):
            if stmt.value not in lives:
                hkia__iotw = True
                continue
        if isinstance(stmt, ir.SetItem):
            name = stmt.target.name
            if name not in lives_n_aliases:
                continue
        if type(stmt) in analysis.ir_extension_usedefs:
            ioqg__rkr = analysis.ir_extension_usedefs[type(stmt)]
            qnc__qxp, mqxfv__yxjaf = ioqg__rkr(stmt)
            lives -= mqxfv__yxjaf
            lives |= qnc__qxp
        else:
            lives |= {agu__zbhc.name for agu__zbhc in stmt.list_vars()}
            if isinstance(stmt, ir.Assign):
                lrnyg__jmaf = set()
                if isinstance(cny__gxt, ir.Expr):
                    lrnyg__jmaf = {agu__zbhc.name for agu__zbhc in cny__gxt
                        .list_vars()}
                if iynk__hsua.name not in lrnyg__jmaf:
                    lives.remove(iynk__hsua.name)
        gic__woh.append(stmt)
    gic__woh.reverse()
    block.body = gic__woh
    return hkia__iotw


ir_utils.remove_dead_block = bodo_remove_dead_block


@infer_global(set)
class SetBuiltin(AbstractTemplate):

    def generic(self, args, kws):
        assert not kws
        if args:
            lgge__dam, = args
            if isinstance(lgge__dam, types.IterableType):
                dtype = lgge__dam.iterator_type.yield_type
                if isinstance(dtype, types.Hashable
                    ) or dtype == numba.core.types.unicode_type:
                    return signature(types.Set(dtype), lgge__dam)
        else:
            return signature(types.Set(types.undefined))


def Set__init__(self, dtype, reflected=False):
    assert isinstance(dtype, (types.Hashable, types.Undefined)
        ) or dtype == numba.core.types.unicode_type
    self.dtype = dtype
    self.reflected = reflected
    woaze__pmro = 'reflected set' if reflected else 'set'
    name = '%s(%s)' % (woaze__pmro, self.dtype)
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
        except LiteralTypingError as xftnc__aqsff:
            return
    try:
        return literal(value)
    except LiteralTypingError as xftnc__aqsff:
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
        ibwtf__gavar = py_func.__qualname__
    except AttributeError as xftnc__aqsff:
        ibwtf__gavar = py_func.__name__
    jcb__tfkwo = inspect.getfile(py_func)
    for cls in self._locator_classes:
        biq__pukc = cls.from_function(py_func, jcb__tfkwo)
        if biq__pukc is not None:
            break
    else:
        raise RuntimeError(
            'cannot cache function %r: no locator available for file %r' %
            (ibwtf__gavar, jcb__tfkwo))
    self._locator = biq__pukc
    pcyuo__eewb = inspect.getfile(py_func)
    vlr__zxf = os.path.splitext(os.path.basename(pcyuo__eewb))[0]
    if jcb__tfkwo.startswith('<ipython-'):
        mimjn__cvsr = re.sub('(ipython-input)(-\\d+)(-[0-9a-fA-F]+)',
            '\\1\\3', vlr__zxf, count=1)
        if mimjn__cvsr == vlr__zxf:
            warnings.warn(
                'Did not recognize ipython module name syntax. Caching might not work'
                )
        vlr__zxf = mimjn__cvsr
    ihiu__rgyh = '%s.%s' % (vlr__zxf, ibwtf__gavar)
    nnpdm__cncxf = getattr(sys, 'abiflags', '')
    self._filename_base = self.get_filename_base(ihiu__rgyh, nnpdm__cncxf)


if _check_numba_change:
    lines = inspect.getsource(numba.core.caching._CacheImpl.__init__)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b46d298146e3844e9eaeef29d36f5165ba4796c270ca50d2b35f9fcdc0fa032a':
        warnings.warn('numba.core.caching._CacheImpl.__init__ has changed')
numba.core.caching._CacheImpl.__init__ = CacheImpl__init__


def _analyze_broadcast(self, scope, equiv_set, loc, args, fn):
    from numba.parfors.array_analysis import ArrayAnalysis
    kebo__lom = list(filter(lambda a: self._istuple(a.name), args))
    if len(kebo__lom) == 2 and fn.__name__ == 'add':
        ebfvm__zyw = self.typemap[kebo__lom[0].name]
        fqvv__zvi = self.typemap[kebo__lom[1].name]
        if ebfvm__zyw.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                kebo__lom[1]))
        if fqvv__zvi.count == 0:
            return ArrayAnalysis.AnalyzeResult(shape=equiv_set.get_shape(
                kebo__lom[0]))
        try:
            chgsz__qxq = [equiv_set.get_shape(x) for x in kebo__lom]
            if None in chgsz__qxq:
                return None
            jnlhg__sik = sum(chgsz__qxq, ())
            return ArrayAnalysis.AnalyzeResult(shape=jnlhg__sik)
        except GuardException as xftnc__aqsff:
            return None
    bojte__kctif = list(filter(lambda a: self._isarray(a.name), args))
    require(len(bojte__kctif) > 0)
    cqzpd__hjer = [x.name for x in bojte__kctif]
    gwjw__vot = [self.typemap[x.name].ndim for x in bojte__kctif]
    umtcs__obabz = max(gwjw__vot)
    require(umtcs__obabz > 0)
    chgsz__qxq = [equiv_set.get_shape(x) for x in bojte__kctif]
    if any(a is None for a in chgsz__qxq):
        return ArrayAnalysis.AnalyzeResult(shape=bojte__kctif[0], pre=self.
            _call_assert_equiv(scope, loc, equiv_set, bojte__kctif))
    return self._broadcast_assert_shapes(scope, equiv_set, loc, chgsz__qxq,
        cqzpd__hjer)


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
    orjuh__qhaz = code_obj.code
    knlbl__xuc = len(orjuh__qhaz.co_freevars)
    fhkc__kpfy = orjuh__qhaz.co_freevars
    if code_obj.closure is not None:
        assert isinstance(code_obj.closure, ir.Var)
        txay__ndzt, op = ir_utils.find_build_sequence(caller_ir, code_obj.
            closure)
        assert op == 'build_tuple'
        fhkc__kpfy = [agu__zbhc.name for agu__zbhc in txay__ndzt]
    lew__mzayr = caller_ir.func_id.func.__globals__
    try:
        lew__mzayr = getattr(code_obj, 'globals', lew__mzayr)
    except KeyError as xftnc__aqsff:
        pass
    msg = (
        "Inner function is using non-constant variable '{}' from outer function. Please pass as argument if possible. See https://docs.bodo.ai/latest/source/programming_with_bodo/bodo_api_reference/udfs.html"
        )
    zupf__xab = []
    for x in fhkc__kpfy:
        try:
            rezvi__pdah = caller_ir.get_definition(x)
        except KeyError as xftnc__aqsff:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
        from numba.core.registry import CPUDispatcher
        if isinstance(rezvi__pdah, (ir.Const, ir.Global, ir.FreeVar)):
            val = rezvi__pdah.value
            if isinstance(val, str):
                val = "'{}'".format(val)
            if isinstance(val, pytypes.FunctionType):
                bftm__zyd = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                lew__mzayr[bftm__zyd] = bodo.jit(distributed=False)(val)
                lew__mzayr[bftm__zyd].is_nested_func = True
                val = bftm__zyd
            if isinstance(val, CPUDispatcher):
                bftm__zyd = ir_utils.mk_unique_var('nested_func').replace('.',
                    '_')
                lew__mzayr[bftm__zyd] = val
                val = bftm__zyd
            zupf__xab.append(val)
        elif isinstance(rezvi__pdah, ir.Expr
            ) and rezvi__pdah.op == 'make_function':
            amz__lvxuo = convert_code_obj_to_function(rezvi__pdah, caller_ir)
            bftm__zyd = ir_utils.mk_unique_var('nested_func').replace('.', '_')
            lew__mzayr[bftm__zyd] = bodo.jit(distributed=False)(amz__lvxuo)
            lew__mzayr[bftm__zyd].is_nested_func = True
            zupf__xab.append(bftm__zyd)
        else:
            raise bodo.utils.typing.BodoError(msg.format(x), loc=code_obj.loc)
    nqhb__zgow = '\n'.join([('\tc_%d = %s' % (i, x)) for i, x in enumerate(
        zupf__xab)])
    nhlvb__vowbv = ','.join([('c_%d' % i) for i in range(knlbl__xuc)])
    ecms__dudz = list(orjuh__qhaz.co_varnames)
    ywhvs__zam = 0
    anvyz__zouo = orjuh__qhaz.co_argcount
    ftzx__yztow = caller_ir.get_definition(code_obj.defaults)
    if ftzx__yztow is not None:
        if isinstance(ftzx__yztow, tuple):
            dyggb__ysnes = [caller_ir.get_definition(x).value for x in
                ftzx__yztow]
            glx__jebc = tuple(dyggb__ysnes)
        else:
            dyggb__ysnes = [caller_ir.get_definition(x).value for x in
                ftzx__yztow.items]
            glx__jebc = tuple(dyggb__ysnes)
        ywhvs__zam = len(glx__jebc)
    eiz__ojbb = anvyz__zouo - ywhvs__zam
    zgz__wcek = ','.join([('%s' % ecms__dudz[i]) for i in range(eiz__ojbb)])
    if ywhvs__zam:
        apsod__hzaz = [('%s = %s' % (ecms__dudz[i + eiz__ojbb], glx__jebc[i
            ])) for i in range(ywhvs__zam)]
        zgz__wcek += ', '
        zgz__wcek += ', '.join(apsod__hzaz)
    return _create_function_from_code_obj(orjuh__qhaz, nqhb__zgow,
        zgz__wcek, nhlvb__vowbv, lew__mzayr)


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
    for mdot__ltkho, (oruxa__cbxrw, tpeek__wucn) in enumerate(self.passes):
        try:
            numba.core.tracing.event('-- %s' % tpeek__wucn)
            eqvuy__pcbn = _pass_registry.get(oruxa__cbxrw).pass_inst
            if isinstance(eqvuy__pcbn, CompilerPass):
                self._runPass(mdot__ltkho, eqvuy__pcbn, state)
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
                    pipeline_name, tpeek__wucn)
                ivu__aqbfg = self._patch_error(msg, e)
                raise ivu__aqbfg
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
    oiove__rlgdq = None
    mqxfv__yxjaf = {}

    def lookup(var, already_seen, varonly=True):
        val = mqxfv__yxjaf.get(var.name, None)
        if isinstance(val, ir.Var):
            if val.name in already_seen:
                return var
            already_seen.add(val.name)
            return lookup(val, already_seen, varonly)
        else:
            return var if varonly or val is None else val
    name = reduction_node.name
    jerd__xprwj = reduction_node.unversioned_name
    for i, stmt in enumerate(nodes):
        iynk__hsua = stmt.target
        cny__gxt = stmt.value
        mqxfv__yxjaf[iynk__hsua.name] = cny__gxt
        if isinstance(cny__gxt, ir.Var) and cny__gxt.name in mqxfv__yxjaf:
            cny__gxt = lookup(cny__gxt, set())
        if isinstance(cny__gxt, ir.Expr):
            tgxp__brkb = set(lookup(agu__zbhc, set(), True).name for
                agu__zbhc in cny__gxt.list_vars())
            if name in tgxp__brkb:
                args = [(x.name, lookup(x, set(), True)) for x in
                    get_expr_args(cny__gxt)]
                oseai__zeh = [x for x, hhd__nxw in args if hhd__nxw.name !=
                    name]
                args = [(x, hhd__nxw) for x, hhd__nxw in args if x !=
                    hhd__nxw.name]
                trcod__wysv = dict(args)
                if len(oseai__zeh) == 1:
                    trcod__wysv[oseai__zeh[0]] = ir.Var(iynk__hsua.scope, 
                        name + '#init', iynk__hsua.loc)
                replace_vars_inner(cny__gxt, trcod__wysv)
                oiove__rlgdq = nodes[i:]
                break
    return oiove__rlgdq


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
        qifd__fbim = expand_aliases({agu__zbhc.name for agu__zbhc in stmt.
            list_vars()}, alias_map, arg_aliases)
        dnu__vkn = expand_aliases(get_parfor_writes(stmt, func_ir),
            alias_map, arg_aliases)
        inc__dkoc = expand_aliases({agu__zbhc.name for agu__zbhc in
            next_stmt.list_vars()}, alias_map, arg_aliases)
        qrrn__rvjg = expand_aliases(get_stmt_writes(next_stmt, func_ir),
            alias_map, arg_aliases)
        if len(dnu__vkn & inc__dkoc | qrrn__rvjg & qifd__fbim) == 0:
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
    wtr__hcudx = set()
    blocks = parfor.loop_body.copy()
    blocks[-1] = parfor.init_block
    for block in blocks.values():
        for stmt in block.body:
            wtr__hcudx.update(get_stmt_writes(stmt, func_ir))
            if isinstance(stmt, Parfor):
                wtr__hcudx.update(get_parfor_writes(stmt, func_ir))
    return wtr__hcudx


if _check_numba_change:
    lines = inspect.getsource(numba.parfors.parfor.get_parfor_writes)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'a7b29cd76832b6f6f1f2d2397ec0678c1409b57a6eab588bffd344b775b1546f':
        warnings.warn('numba.parfors.parfor.get_parfor_writes has changed')


def get_stmt_writes(stmt, func_ir):
    import bodo
    from bodo.utils.utils import is_call_assign
    wtr__hcudx = set()
    if isinstance(stmt, (ir.Assign, ir.SetItem, ir.StaticSetItem)):
        wtr__hcudx.add(stmt.target.name)
    if isinstance(stmt, bodo.ir.aggregate.Aggregate):
        wtr__hcudx = {agu__zbhc.name for agu__zbhc in stmt.df_out_vars.values()
            }
        if stmt.out_key_vars is not None:
            wtr__hcudx.update({agu__zbhc.name for agu__zbhc in stmt.
                out_key_vars})
    if isinstance(stmt, (bodo.ir.csv_ext.CsvReader, bodo.ir.parquet_ext.
        ParquetReader)):
        wtr__hcudx = {agu__zbhc.name for agu__zbhc in stmt.out_vars}
    if isinstance(stmt, bodo.ir.join.Join):
        wtr__hcudx = {agu__zbhc.name for agu__zbhc in stmt.out_data_vars.
            values()}
    if isinstance(stmt, bodo.ir.sort.Sort):
        if not stmt.inplace:
            wtr__hcudx.update({agu__zbhc.name for agu__zbhc in stmt.
                out_key_arrs})
            wtr__hcudx.update({agu__zbhc.name for agu__zbhc in stmt.
                df_out_vars.values()})
    if is_call_assign(stmt):
        sqjd__icwdy = guard(find_callname, func_ir, stmt.value)
        if sqjd__icwdy in (('setitem_str_arr_ptr', 'bodo.libs.str_arr_ext'),
            ('setna', 'bodo.libs.array_kernels'), (
            'str_arr_item_to_numeric', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_int_to_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_setitem_NA_str', 'bodo.libs.str_arr_ext'), (
            'str_arr_set_not_na', 'bodo.libs.str_arr_ext'), (
            'get_str_arr_item_copy', 'bodo.libs.str_arr_ext'), (
            'set_bit_to_arr', 'bodo.libs.int_arr_ext')):
            wtr__hcudx.add(stmt.value.args[0].name)
    return wtr__hcudx


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
        mmmyu__lykyp = _termcolor.errmsg('{0}') + _termcolor.filename(
            'During: {1}')
        zwe__bwgv = mmmyu__lykyp.format(self, msg)
        self.args = zwe__bwgv,
    else:
        mmmyu__lykyp = _termcolor.errmsg('{0}')
        zwe__bwgv = mmmyu__lykyp.format(self)
        self.args = zwe__bwgv,
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
        for ewqmw__dcm in options['distributed']:
            dist_spec[ewqmw__dcm] = Distribution.OneD_Var
    if 'distributed_block' in options:
        for ewqmw__dcm in options['distributed_block']:
            dist_spec[ewqmw__dcm] = Distribution.OneD
    return dist_spec


def register_class_type(cls, spec, class_ctor, builder, **options):
    import typing as pt
    from numba.core.typing.asnumbatype import as_numba_type
    import bodo
    dist_spec = _get_dist_spec_from_options(spec, **options)
    nwpm__njyg = options.get('returns_maybe_distributed', True)
    if spec is None:
        spec = OrderedDict()
    elif isinstance(spec, Sequence):
        spec = OrderedDict(spec)
    for attr, pdjhy__ibc in pt.get_type_hints(cls).items():
        if attr not in spec:
            spec[attr] = as_numba_type(pdjhy__ibc)
    jitclass_base._validate_spec(spec)
    spec = jitclass_base._fix_up_private_attr(cls.__name__, spec)
    quur__jwo = {}
    for vwxhz__aoz in reversed(inspect.getmro(cls)):
        quur__jwo.update(vwxhz__aoz.__dict__)
    afzw__tnav, cli__vbve, btcsl__wcjg, hrj__tlyqn = {}, {}, {}, {}
    for pylc__qawc, agu__zbhc in quur__jwo.items():
        if isinstance(agu__zbhc, pytypes.FunctionType):
            afzw__tnav[pylc__qawc] = agu__zbhc
        elif isinstance(agu__zbhc, property):
            cli__vbve[pylc__qawc] = agu__zbhc
        elif isinstance(agu__zbhc, staticmethod):
            btcsl__wcjg[pylc__qawc] = agu__zbhc
        else:
            hrj__tlyqn[pylc__qawc] = agu__zbhc
    rapl__tptp = (set(afzw__tnav) | set(cli__vbve) | set(btcsl__wcjg)) & set(
        spec)
    if rapl__tptp:
        raise NameError('name shadowing: {0}'.format(', '.join(rapl__tptp)))
    vrj__sxs = hrj__tlyqn.pop('__doc__', '')
    jitclass_base._drop_ignored_attrs(hrj__tlyqn)
    if hrj__tlyqn:
        msg = 'class members are not yet supported: {0}'
        sjor__hkdzg = ', '.join(hrj__tlyqn.keys())
        raise TypeError(msg.format(sjor__hkdzg))
    for pylc__qawc, agu__zbhc in cli__vbve.items():
        if agu__zbhc.fdel is not None:
            raise TypeError('deleter is not supported: {0}'.format(pylc__qawc))
    jit_methods = {pylc__qawc: bodo.jit(returns_maybe_distributed=
        nwpm__njyg)(agu__zbhc) for pylc__qawc, agu__zbhc in afzw__tnav.items()}
    jit_props = {}
    for pylc__qawc, agu__zbhc in cli__vbve.items():
        djvlt__pngad = {}
        if agu__zbhc.fget:
            djvlt__pngad['get'] = bodo.jit(agu__zbhc.fget)
        if agu__zbhc.fset:
            djvlt__pngad['set'] = bodo.jit(agu__zbhc.fset)
        jit_props[pylc__qawc] = djvlt__pngad
    jit_static_methods = {pylc__qawc: bodo.jit(agu__zbhc.__func__) for 
        pylc__qawc, agu__zbhc in btcsl__wcjg.items()}
    lbn__lzg = class_ctor(cls, jitclass_base.ConstructorTemplate, spec,
        jit_methods, jit_props, jit_static_methods, dist_spec)
    xsd__cvadl = dict(class_type=lbn__lzg, __doc__=vrj__sxs)
    xsd__cvadl.update(jit_static_methods)
    cls = jitclass_base.JitClassType(cls.__name__, (cls,), xsd__cvadl)
    typingctx = numba.core.registry.cpu_target.typing_context
    typingctx.insert_global(cls, lbn__lzg)
    targetctx = numba.core.registry.cpu_target.target_context
    builder(lbn__lzg, typingctx, targetctx).register()
    as_numba_type.register(cls, lbn__lzg.instance_type)
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
    gszaf__pmpdt = ','.join('{0}:{1}'.format(pylc__qawc, agu__zbhc) for 
        pylc__qawc, agu__zbhc in struct.items())
    coha__uzd = ','.join('{0}:{1}'.format(pylc__qawc, agu__zbhc) for 
        pylc__qawc, agu__zbhc in dist_spec.items())
    name = '{0}.{1}#{2:x}<{3}><{4}>'.format(self.name_prefix, self.
        class_name, id(self), gszaf__pmpdt, coha__uzd)
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
    dxak__pvvwd = numba.core.typeinfer.fold_arg_vars(typevars, self.args,
        self.vararg, self.kws)
    if dxak__pvvwd is None:
        return
    vkcw__umo, olkoz__axz = dxak__pvvwd
    for a in itertools.chain(vkcw__umo, olkoz__axz.values()):
        if not a.is_precise() and not isinstance(a, types.Array):
            return
    if isinstance(fnty, types.TypeRef):
        fnty = fnty.instance_type
    try:
        sig = typeinfer.resolve_call(fnty, vkcw__umo, olkoz__axz)
    except ForceLiteralArg as e:
        iglk__arsp = (fnty.this,) + tuple(self.args) if isinstance(fnty,
            types.BoundFunction) else self.args
        folded = e.fold_arguments(iglk__arsp, self.kws)
        jnepb__pvfq = set()
        jhuji__fivl = set()
        wfv__gwedb = {}
        for mdot__ltkho in e.requested_args:
            ecv__iyv = typeinfer.func_ir.get_definition(folded[mdot__ltkho])
            if isinstance(ecv__iyv, ir.Arg):
                jnepb__pvfq.add(ecv__iyv.index)
                if ecv__iyv.index in e.file_infos:
                    wfv__gwedb[ecv__iyv.index] = e.file_infos[ecv__iyv.index]
            else:
                jhuji__fivl.add(mdot__ltkho)
        if jhuji__fivl:
            raise TypingError('Cannot request literal type.', loc=self.loc)
        elif jnepb__pvfq:
            raise ForceLiteralArg(jnepb__pvfq, loc=self.loc, file_infos=
                wfv__gwedb)
    if sig is None:
        bjcm__vmck = 'Invalid use of {0} with parameters ({1})'
        args = [str(a) for a in vkcw__umo]
        args += [('%s=%s' % (pylc__qawc, agu__zbhc)) for pylc__qawc,
            agu__zbhc in sorted(olkoz__axz.items())]
        mhzh__jkfc = bjcm__vmck.format(fnty, ', '.join(map(str, args)))
        cthlr__gzz = context.explain_function_type(fnty)
        msg = '\n'.join([mhzh__jkfc, cthlr__gzz])
        raise TypingError(msg)
    typeinfer.add_type(self.target, sig.return_type, loc=self.loc)
    if isinstance(fnty, types.BoundFunction
        ) and sig.recvr is not None and sig.recvr != fnty.this:
        tkg__tdrhz = context.unify_pairs(sig.recvr, fnty.this)
        if tkg__tdrhz is None and fnty.this.is_precise(
            ) and sig.recvr.is_precise():
            msg = 'Cannot refine type {} to {}'.format(sig.recvr, fnty.this)
            raise TypingError(msg, loc=self.loc)
        if tkg__tdrhz is not None and tkg__tdrhz.is_precise():
            qvcg__sxdq = fnty.copy(this=tkg__tdrhz)
            typeinfer.propagate_refined_type(self.func, qvcg__sxdq)
    if not sig.return_type.is_precise():
        ybmi__miz = typevars[self.target]
        if ybmi__miz.defined:
            loos__zco = ybmi__miz.getone()
            if context.unify_pairs(loos__zco, sig.return_type) == loos__zco:
                sig = sig.replace(return_type=loos__zco)
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
        quzt__ygfbm = '*other* must be a {} but got a {} instead'
        raise TypeError(quzt__ygfbm.format(ForceLiteralArg, type(other)))
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
    zxxtv__rzxt = {}

    def report_error(varname, msg, loc):
        raise errors.CompilerError(
            f'Error handling objmode argument {varname!r}. {msg}', loc=loc)
    for pylc__qawc, agu__zbhc in kwargs.items():
        okdy__hdw = None
        try:
            lkfj__xhzj = ir.Var(ir.Scope(None, loc), ir_utils.mk_unique_var
                ('dummy'), loc)
            func_ir._definitions[lkfj__xhzj.name] = [agu__zbhc]
            okdy__hdw = get_const_value_inner(func_ir, lkfj__xhzj)
            func_ir._definitions.pop(lkfj__xhzj.name)
            if isinstance(okdy__hdw, str):
                okdy__hdw = sigutils._parse_signature_string(okdy__hdw)
            if isinstance(okdy__hdw, types.abstract._TypeMetaclass):
                raise BodoError(
                    f"""objmode type annotations require full data types, not just data type classes. For example, 'bodo.DataFrameType((bodo.float64[::1],), bodo.RangeIndexType(), ('A',))' is a valid data type but 'bodo.DataFrameType' is not.
Variable {pylc__qawc} is annotated as type class {okdy__hdw}."""
                    )
            assert isinstance(okdy__hdw, types.Type)
            if isinstance(okdy__hdw, (types.List, types.Set)):
                okdy__hdw = okdy__hdw.copy(reflected=False)
            zxxtv__rzxt[pylc__qawc] = okdy__hdw
        except BodoError as xftnc__aqsff:
            raise
        except:
            msg = (
                'The value must be a compile-time constant either as a non-local variable or an expression that refers to a Bodo type.'
                )
            if isinstance(okdy__hdw, ir.UndefinedType):
                msg = f'not defined.'
                if isinstance(agu__zbhc, ir.Global):
                    msg = f'Global {agu__zbhc.name!r} is not defined.'
                if isinstance(agu__zbhc, ir.FreeVar):
                    msg = f'Freevar {agu__zbhc.name!r} is not defined.'
            if isinstance(agu__zbhc, ir.Expr) and agu__zbhc.op == 'getattr':
                msg = 'Getattr cannot be resolved at compile-time.'
            report_error(varname=pylc__qawc, msg=msg, loc=loc)
    for name, typ in zxxtv__rzxt.items():
        self._legalize_arg_type(name, typ, loc)
    return zxxtv__rzxt


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
    qls__ltz = inst.arg
    assert qls__ltz > 0, 'invalid BUILD_STRING count'
    strings = list(reversed([state.pop() for _ in range(qls__ltz)]))
    tmps = [state.make_temp() for _ in range(qls__ltz - 1)]
    state.append(inst, strings=strings, tmps=tmps)
    state.push(tmps[-1])


numba.core.byteflow.TraceRunner.op_FORMAT_VALUE = op_FORMAT_VALUE_byteflow
numba.core.byteflow.TraceRunner.op_BUILD_STRING = op_BUILD_STRING_byteflow


def op_FORMAT_VALUE_interpreter(self, inst, value, res, fmtvar, format_spec):
    value = self.get(value)
    unb__jmi = ir.Global('format', format, loc=self.loc)
    self.store(value=unb__jmi, name=fmtvar)
    args = (value, self.get(format_spec)) if format_spec else (value,)
    pfu__yss = ir.Expr.call(self.get(fmtvar), args, (), loc=self.loc)
    self.store(value=pfu__yss, name=res)


def op_BUILD_STRING_interpreter(self, inst, strings, tmps):
    qls__ltz = inst.arg
    assert qls__ltz > 0, 'invalid BUILD_STRING count'
    irqc__ajcjq = self.get(strings[0])
    for other, dmj__wuicp in zip(strings[1:], tmps):
        other = self.get(other)
        frzl__qyv = ir.Expr.binop(operator.add, lhs=irqc__ajcjq, rhs=other,
            loc=self.loc)
        self.store(frzl__qyv, dmj__wuicp)
        irqc__ajcjq = self.get(dmj__wuicp)


numba.core.interpreter.Interpreter.op_FORMAT_VALUE = (
    op_FORMAT_VALUE_interpreter)
numba.core.interpreter.Interpreter.op_BUILD_STRING = (
    op_BUILD_STRING_interpreter)


def object_hasattr_string(self, obj, attr):
    from llvmlite.llvmpy.core import Type
    sxidk__vbm = self.context.insert_const_string(self.module, attr)
    fnty = Type.function(Type.int(), [self.pyobj, self.cstring])
    fn = self._get_function(fnty, name='PyObject_HasAttrString')
    return self.builder.call(fn, [obj, sxidk__vbm])


numba.core.pythonapi.PythonAPI.object_hasattr_string = object_hasattr_string


def _created_inlined_var_name(function_name, var_name):
    cbz__eoaa = mk_unique_var(f'{var_name}')
    pnzqg__pxk = cbz__eoaa.replace('<', '_').replace('>', '_')
    pnzqg__pxk = pnzqg__pxk.replace('.', '_').replace('$', '_v')
    return pnzqg__pxk


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
                seo__ofntk = get_overload_const_str(val2)
                if seo__ofntk != 'ns':
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
        otbw__dqgub = states['defmap']
        if len(otbw__dqgub) == 0:
            hqpwa__bnvb = assign.target
            numba.core.ssa._logger.debug('first assign: %s', hqpwa__bnvb)
            if hqpwa__bnvb.name not in scope.localvars:
                hqpwa__bnvb = scope.define(assign.target.name, loc=assign.loc)
        else:
            hqpwa__bnvb = scope.redefine(assign.target.name, loc=assign.loc)
        assign = ir.Assign(target=hqpwa__bnvb, value=assign.value, loc=
            assign.loc)
        otbw__dqgub[states['label']].append(assign)
    return assign


if _check_numba_change:
    lines = inspect.getsource(numba.core.ssa._FreshVarHandler.on_assign)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '922c4f9807455f81600b794bbab36f9c6edfecfa83fda877bf85f465db7865e8':
        warnings.warn('_FreshVarHandler on_assign has changed')
numba.core.ssa._FreshVarHandler.on_assign = on_assign


def get_np_ufunc_typ_lst(func):
    from numba.core import typing
    ulzvi__gug = []
    for pylc__qawc, agu__zbhc in typing.npydecl.registry.globals:
        if pylc__qawc == func:
            ulzvi__gug.append(agu__zbhc)
    for pylc__qawc, agu__zbhc in typing.templates.builtin_registry.globals:
        if pylc__qawc == func:
            ulzvi__gug.append(agu__zbhc)
    if len(ulzvi__gug) == 0:
        raise RuntimeError('type for func ', func, ' not found')
    return ulzvi__gug


def canonicalize_array_math(func_ir, typemap, calltypes, typingctx):
    import numpy
    from numba.core.ir_utils import arr_math, find_topo_order, mk_unique_var
    blocks = func_ir.blocks
    sek__iyjce = {}
    tcgrs__xkty = find_topo_order(blocks)
    fqi__aqauw = {}
    for mhsr__kkju in tcgrs__xkty:
        block = blocks[mhsr__kkju]
        gic__woh = []
        for stmt in block.body:
            if isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr):
                iynk__hsua = stmt.target.name
                cny__gxt = stmt.value
                if (cny__gxt.op == 'getattr' and cny__gxt.attr in arr_math and
                    isinstance(typemap[cny__gxt.value.name], types.npytypes
                    .Array)):
                    cny__gxt = stmt.value
                    bakn__lfr = cny__gxt.value
                    sek__iyjce[iynk__hsua] = bakn__lfr
                    scope = bakn__lfr.scope
                    loc = bakn__lfr.loc
                    xcnko__jyzp = ir.Var(scope, mk_unique_var('$np_g_var'), loc
                        )
                    typemap[xcnko__jyzp.name] = types.misc.Module(numpy)
                    qxqx__rfvuk = ir.Global('np', numpy, loc)
                    gxn__zja = ir.Assign(qxqx__rfvuk, xcnko__jyzp, loc)
                    cny__gxt.value = xcnko__jyzp
                    gic__woh.append(gxn__zja)
                    func_ir._definitions[xcnko__jyzp.name] = [qxqx__rfvuk]
                    func = getattr(numpy, cny__gxt.attr)
                    amo__afdva = get_np_ufunc_typ_lst(func)
                    fqi__aqauw[iynk__hsua] = amo__afdva
                if cny__gxt.op == 'call' and cny__gxt.func.name in sek__iyjce:
                    bakn__lfr = sek__iyjce[cny__gxt.func.name]
                    nuvt__uokj = calltypes.pop(cny__gxt)
                    etg__vmeo = nuvt__uokj.args[:len(cny__gxt.args)]
                    bzqcc__myqm = {name: typemap[agu__zbhc.name] for name,
                        agu__zbhc in cny__gxt.kws}
                    finsf__rwl = fqi__aqauw[cny__gxt.func.name]
                    jzxb__flzio = None
                    for yqd__hzvq in finsf__rwl:
                        try:
                            jzxb__flzio = yqd__hzvq.get_call_type(typingctx,
                                [typemap[bakn__lfr.name]] + list(etg__vmeo),
                                bzqcc__myqm)
                            typemap.pop(cny__gxt.func.name)
                            typemap[cny__gxt.func.name] = yqd__hzvq
                            calltypes[cny__gxt] = jzxb__flzio
                            break
                        except Exception as xftnc__aqsff:
                            pass
                    if jzxb__flzio is None:
                        raise TypeError(
                            f'No valid template found for {cny__gxt.func.name}'
                            )
                    cny__gxt.args = [bakn__lfr] + cny__gxt.args
            gic__woh.append(stmt)
        block.body = gic__woh


if _check_numba_change:
    lines = inspect.getsource(numba.core.ir_utils.canonicalize_array_math)
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != 'b2200e9100613631cc554f4b640bc1181ba7cea0ece83630122d15b86941be2e':
        warnings.warn('canonicalize_array_math has changed')
numba.core.ir_utils.canonicalize_array_math = canonicalize_array_math
numba.parfors.parfor.canonicalize_array_math = canonicalize_array_math
numba.core.inline_closurecall.canonicalize_array_math = canonicalize_array_math


def _Numpy_Rules_ufunc_handle_inputs(cls, ufunc, args, kws):
    pukye__gntlh = ufunc.nin
    dki__nemyx = ufunc.nout
    eiz__ojbb = ufunc.nargs
    assert eiz__ojbb == pukye__gntlh + dki__nemyx
    if len(args) < pukye__gntlh:
        msg = "ufunc '{0}': not enough arguments ({1} found, {2} required)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args),
            pukye__gntlh))
    if len(args) > eiz__ojbb:
        msg = "ufunc '{0}': too many arguments ({1} found, {2} maximum)"
        raise TypingError(msg=msg.format(ufunc.__name__, len(args), eiz__ojbb))
    args = [(a.as_array if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else a) for a in args]
    lwx__xbn = [(a.ndim if isinstance(a, types.ArrayCompatible) and not
        isinstance(a, types.Bytes) else 0) for a in args]
    szn__ykf = max(lwx__xbn)
    maqxo__ajlb = args[pukye__gntlh:]
    if not all(dyggb__ysnes == szn__ykf for dyggb__ysnes in lwx__xbn[
        pukye__gntlh:]):
        msg = "ufunc '{0}' called with unsuitable explicit output arrays."
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(isinstance(yon__zjen, types.ArrayCompatible) and not
        isinstance(yon__zjen, types.Bytes) for yon__zjen in maqxo__ajlb):
        msg = "ufunc '{0}' called with an explicit output that is not an array"
        raise TypingError(msg=msg.format(ufunc.__name__))
    if not all(yon__zjen.mutable for yon__zjen in maqxo__ajlb):
        msg = "ufunc '{0}' called with an explicit output that is read-only"
        raise TypingError(msg=msg.format(ufunc.__name__))
    hbsqw__hqx = [(x.dtype if isinstance(x, types.ArrayCompatible) and not
        isinstance(x, types.Bytes) else x) for x in args]
    ldc__hxvm = None
    if szn__ykf > 0 and len(maqxo__ajlb) < ufunc.nout:
        ldc__hxvm = 'C'
        gnyo__fmx = [(x.layout if isinstance(x, types.ArrayCompatible) and 
            not isinstance(x, types.Bytes) else '') for x in args]
        if 'C' not in gnyo__fmx and 'F' in gnyo__fmx:
            ldc__hxvm = 'F'
    return hbsqw__hqx, maqxo__ajlb, szn__ykf, ldc__hxvm


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
        gumss__hsrg = 'Dict.key_type cannot be of type {}'
        raise TypingError(gumss__hsrg.format(keyty))
    if isinstance(valty, (Optional, NoneType)):
        gumss__hsrg = 'Dict.value_type cannot be of type {}'
        raise TypingError(gumss__hsrg.format(valty))
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
    swiy__vwtwh = self.context, tuple(args), tuple(kws.items())
    try:
        xjmxp__bynu, args = self._impl_cache[swiy__vwtwh]
        return xjmxp__bynu, args
    except KeyError as xftnc__aqsff:
        pass
    xjmxp__bynu, args = self._build_impl(swiy__vwtwh, args, kws)
    return xjmxp__bynu, args


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
        vkv__ahymq = find_topo_order(parfor.loop_body)
    pej__bvcx = vkv__ahymq[0]
    vrv__wewwp = {}
    _update_parfor_get_setitems(parfor.loop_body[pej__bvcx].body, parfor.
        index_var, alias_map, vrv__wewwp, lives_n_aliases)
    kwxei__tht = set(vrv__wewwp.keys())
    for ixuw__ruwmo in vkv__ahymq:
        if ixuw__ruwmo == pej__bvcx:
            continue
        for stmt in parfor.loop_body[ixuw__ruwmo].body:
            if (isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.
                Expr) and stmt.value.op == 'getitem' and stmt.value.index.
                name == parfor.index_var.name):
                continue
            tfn__hgxsh = set(agu__zbhc.name for agu__zbhc in stmt.list_vars())
            szzgn__zdjao = tfn__hgxsh & kwxei__tht
            for a in szzgn__zdjao:
                vrv__wewwp.pop(a, None)
    for ixuw__ruwmo in vkv__ahymq:
        if ixuw__ruwmo == pej__bvcx:
            continue
        block = parfor.loop_body[ixuw__ruwmo]
        pfklq__wysef = vrv__wewwp.copy()
        _update_parfor_get_setitems(block.body, parfor.index_var, alias_map,
            pfklq__wysef, lives_n_aliases)
    blocks = parfor.loop_body.copy()
    jmodr__vxne = max(blocks.keys())
    bryr__wsxy, cnx__nfv = _add_liveness_return_block(blocks,
        lives_n_aliases, typemap)
    cehif__bimd = ir.Jump(bryr__wsxy, ir.Loc('parfors_dummy', -1))
    blocks[jmodr__vxne].body.append(cehif__bimd)
    lnur__extqf = compute_cfg_from_blocks(blocks)
    uizo__pmsj = compute_use_defs(blocks)
    qdyik__omvce = compute_live_map(lnur__extqf, blocks, uizo__pmsj.usemap,
        uizo__pmsj.defmap)
    alias_set = set(alias_map.keys())
    for mhsr__kkju, block in blocks.items():
        gic__woh = []
        jfsid__shjcj = {agu__zbhc.name for agu__zbhc in block.terminator.
            list_vars()}
        for rbw__spdsr, chafx__bgp in lnur__extqf.successors(mhsr__kkju):
            jfsid__shjcj |= qdyik__omvce[rbw__spdsr]
        for stmt in reversed(block.body):
            siu__fdfdr = jfsid__shjcj & alias_set
            for agu__zbhc in siu__fdfdr:
                jfsid__shjcj |= alias_map[agu__zbhc]
            if (isinstance(stmt, (ir.StaticSetItem, ir.SetItem)) and 
                get_index_var(stmt).name == parfor.index_var.name and stmt.
                target.name not in jfsid__shjcj and stmt.target.name not in
                arg_aliases):
                continue
            elif isinstance(stmt, ir.Assign) and isinstance(stmt.value, ir.Expr
                ) and stmt.value.op == 'call':
                sqjd__icwdy = guard(find_callname, func_ir, stmt.value)
                if sqjd__icwdy == ('setna', 'bodo.libs.array_kernels'
                    ) and stmt.value.args[0
                    ].name not in jfsid__shjcj and stmt.value.args[0
                    ].name not in arg_aliases:
                    continue
            jfsid__shjcj |= {agu__zbhc.name for agu__zbhc in stmt.list_vars()}
            gic__woh.append(stmt)
        gic__woh.reverse()
        block.body = gic__woh
    typemap.pop(cnx__nfv.name)
    blocks[jmodr__vxne].body.pop()

    def trim_empty_parfor_branches(parfor):
        kpa__hgda = False
        blocks = parfor.loop_body.copy()
        for mhsr__kkju, block in blocks.items():
            if len(block.body):
                wbz__koeek = block.body[-1]
                if isinstance(wbz__koeek, ir.Branch):
                    if len(blocks[wbz__koeek.truebr].body) == 1 and len(blocks
                        [wbz__koeek.falsebr].body) == 1:
                        khgi__uhvhj = blocks[wbz__koeek.truebr].body[0]
                        fetu__cnucd = blocks[wbz__koeek.falsebr].body[0]
                        if isinstance(khgi__uhvhj, ir.Jump) and isinstance(
                            fetu__cnucd, ir.Jump
                            ) and khgi__uhvhj.target == fetu__cnucd.target:
                            parfor.loop_body[mhsr__kkju].body[-1] = ir.Jump(
                                khgi__uhvhj.target, wbz__koeek.loc)
                            kpa__hgda = True
                    elif len(blocks[wbz__koeek.truebr].body) == 1:
                        khgi__uhvhj = blocks[wbz__koeek.truebr].body[0]
                        if isinstance(khgi__uhvhj, ir.Jump
                            ) and khgi__uhvhj.target == wbz__koeek.falsebr:
                            parfor.loop_body[mhsr__kkju].body[-1] = ir.Jump(
                                khgi__uhvhj.target, wbz__koeek.loc)
                            kpa__hgda = True
                    elif len(blocks[wbz__koeek.falsebr].body) == 1:
                        fetu__cnucd = blocks[wbz__koeek.falsebr].body[0]
                        if isinstance(fetu__cnucd, ir.Jump
                            ) and fetu__cnucd.target == wbz__koeek.truebr:
                            parfor.loop_body[mhsr__kkju].body[-1] = ir.Jump(
                                fetu__cnucd.target, wbz__koeek.loc)
                            kpa__hgda = True
        return kpa__hgda
    kpa__hgda = True
    while kpa__hgda:
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
        kpa__hgda = trim_empty_parfor_branches(parfor)
    dpm__mwx = len(parfor.init_block.body) == 0
    for block in parfor.loop_body.values():
        dpm__mwx &= len(block.body) == 0
    if dpm__mwx:
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
    coj__ervp = 0
    for block in blocks.values():
        for stmt in block.body:
            if isinstance(stmt, Parfor):
                coj__ervp += 1
                parfor = stmt
                xgvr__vmv = parfor.loop_body[max(parfor.loop_body.keys())]
                scope = xgvr__vmv.scope
                loc = ir.Loc('parfors_dummy', -1)
                mdq__sjwj = ir.Var(scope, mk_unique_var('$const'), loc)
                xgvr__vmv.body.append(ir.Assign(ir.Const(0, loc), mdq__sjwj,
                    loc))
                xgvr__vmv.body.append(ir.Return(mdq__sjwj, loc))
                lnur__extqf = compute_cfg_from_blocks(parfor.loop_body)
                for iquf__seeb in lnur__extqf.dead_nodes():
                    del parfor.loop_body[iquf__seeb]
                parfor.loop_body = simplify_CFG(parfor.loop_body)
                xgvr__vmv = parfor.loop_body[max(parfor.loop_body.keys())]
                xgvr__vmv.body.pop()
                xgvr__vmv.body.pop()
                simplify_parfor_body_CFG(parfor.loop_body)
    return coj__ervp


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
            rrqzi__tmjz = self.overloads.get(tuple(args))
            if rrqzi__tmjz is not None:
                return rrqzi__tmjz.entry_point
            self._pre_compile(args, return_type, flags)
            sfjzu__hocy = self.func_ir
            zuo__ksnxu = dict(dispatcher=self, args=args, return_type=
                return_type)
            with ev.trigger_event('numba:compile', data=zuo__ksnxu):
                cres = compiler.compile_ir(typingctx=self.typingctx,
                    targetctx=self.targetctx, func_ir=sfjzu__hocy, args=
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
        rdji__eyvq = copy.deepcopy(flags)
        rdji__eyvq.no_rewrites = True

        def compile_local(the_ir, the_flags):
            diz__ibjs = pipeline_class(typingctx, targetctx, library, args,
                return_type, the_flags, locals)
            return diz__ibjs.compile_ir(func_ir=the_ir, lifted=lifted,
                lifted_from=lifted_from)
        hxvf__ighfn = compile_local(func_ir, rdji__eyvq)
        tmsl__tjeu = None
        if not flags.no_rewrites:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', errors.NumbaWarning)
                try:
                    tmsl__tjeu = compile_local(func_ir, flags)
                except Exception as xftnc__aqsff:
                    pass
        if tmsl__tjeu is not None:
            cres = tmsl__tjeu
        else:
            cres = hxvf__ighfn
        return cres
    else:
        diz__ibjs = pipeline_class(typingctx, targetctx, library, args,
            return_type, flags, locals)
        return diz__ibjs.compile_ir(func_ir=func_ir, lifted=lifted,
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
    pni__qaagd = self.get_data_type(typ.dtype)
    eni__mgt = 10 ** 7
    if self.allow_dynamic_globals and (typ.layout not in 'FC' or ary.nbytes >
        eni__mgt):
        itlc__gab = ary.ctypes.data
        vmi__uzmhc = self.add_dynamic_addr(builder, itlc__gab, info=str(
            type(itlc__gab)))
        gnvn__bod = self.add_dynamic_addr(builder, id(ary), info=str(type(ary))
            )
        self.global_arrays.append(ary)
    else:
        jit__fukbv = ary.flatten(order=typ.layout)
        if isinstance(typ.dtype, (types.NPDatetime, types.NPTimedelta)):
            jit__fukbv = jit__fukbv.view('int64')
        fyxs__zgcmy = Constant.array(Type.int(8), bytearray(jit__fukbv.data))
        vmi__uzmhc = cgutils.global_constant(builder, '.const.array.data',
            fyxs__zgcmy)
        vmi__uzmhc.align = self.get_abi_alignment(pni__qaagd)
        gnvn__bod = None
    fcva__jbk = self.get_value_type(types.intp)
    zknpk__juudt = [self.get_constant(types.intp, zgytb__ars) for
        zgytb__ars in ary.shape]
    jlbf__jfnj = Constant.array(fcva__jbk, zknpk__juudt)
    opu__xmjge = [self.get_constant(types.intp, zgytb__ars) for zgytb__ars in
        ary.strides]
    edsq__ngvt = Constant.array(fcva__jbk, opu__xmjge)
    jafh__ivnul = self.get_constant(types.intp, ary.dtype.itemsize)
    gvkzk__xni = self.get_constant(types.intp, math.prod(ary.shape))
    return lir.Constant.literal_struct([self.get_constant_null(types.
        MemInfoPointer(typ.dtype)), self.get_constant_null(types.pyobject),
        gvkzk__xni, jafh__ivnul, vmi__uzmhc.bitcast(self.get_value_type(
        types.CPointer(typ.dtype))), jlbf__jfnj, edsq__ngvt])


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
    gqiq__hjl = lir.FunctionType(_word_type, [_word_type.as_pointer()])
    sdew__tjd = lir.Function(module, gqiq__hjl, name='nrt_atomic_{0}'.
        format(op))
    [ipar__mfhx] = sdew__tjd.args
    xfy__zfxx = sdew__tjd.append_basic_block()
    builder = lir.IRBuilder(xfy__zfxx)
    acyj__jwp = lir.Constant(_word_type, 1)
    if False:
        nfii__emea = builder.atomic_rmw(op, ipar__mfhx, acyj__jwp, ordering
            =ordering)
        res = getattr(builder, op)(nfii__emea, acyj__jwp)
        builder.ret(res)
    else:
        nfii__emea = builder.load(ipar__mfhx)
        ech__agxkd = getattr(builder, op)(nfii__emea, acyj__jwp)
        fxx__rzz = builder.icmp_signed('!=', nfii__emea, lir.Constant(
            nfii__emea.type, -1))
        with cgutils.if_likely(builder, fxx__rzz):
            builder.store(ech__agxkd, ipar__mfhx)
        builder.ret(ech__agxkd)
    return sdew__tjd


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
        tamlw__qlzs = state.targetctx.codegen()
        state.library = tamlw__qlzs.create_library(state.func_id.func_qualname)
        state.library.enable_object_caching()
    library = state.library
    targetctx = state.targetctx
    ipyhj__asdge = state.func_ir
    typemap = state.typemap
    cvga__wscmm = state.return_type
    calltypes = state.calltypes
    flags = state.flags
    tia__ynn = state.metadata
    pag__pgsx = llvm.passmanagers.dump_refprune_stats()
    msg = 'Function %s failed at nopython mode lowering' % (state.func_id.
        func_name,)
    with fallback_context(state, msg):
        bonbx__amuyw = (funcdesc.PythonFunctionDescriptor.
            from_specialized_function(ipyhj__asdge, typemap, cvga__wscmm,
            calltypes, mangler=targetctx.mangler, inline=flags.forceinline,
            noalias=flags.noalias, abi_tags=[flags.get_mangle_string()]))
        targetctx.global_arrays = []
        with targetctx.push_code_library(library):
            rdz__zakde = lowering.Lower(targetctx, library, bonbx__amuyw,
                ipyhj__asdge, metadata=tia__ynn)
            rdz__zakde.lower()
            if not flags.no_cpython_wrapper:
                rdz__zakde.create_cpython_wrapper(flags.release_gil)
            if not flags.no_cfunc_wrapper:
                for t in state.args:
                    if isinstance(t, (types.Omitted, types.Generator)):
                        break
                else:
                    if isinstance(cvga__wscmm, (types.Optional, types.
                        Generator)):
                        pass
                    else:
                        rdz__zakde.create_cfunc_wrapper()
            atby__zmllv = rdz__zakde.env
            dtwn__vnr = rdz__zakde.call_helper
            del rdz__zakde
        from numba.core.compiler import _LowerResult
        if flags.no_compile:
            state['cr'] = _LowerResult(bonbx__amuyw, dtwn__vnr, cfunc=None,
                env=atby__zmllv)
        else:
            ptefi__bdcpj = targetctx.get_executable(library, bonbx__amuyw,
                atby__zmllv)
            targetctx.insert_user_function(ptefi__bdcpj, bonbx__amuyw, [
                library])
            state['cr'] = _LowerResult(bonbx__amuyw, dtwn__vnr, cfunc=
                ptefi__bdcpj, env=atby__zmllv)
        tia__ynn['global_arrs'] = targetctx.global_arrays
        targetctx.global_arrays = []
        agrk__xdrsi = llvm.passmanagers.dump_refprune_stats()
        tia__ynn['prune_stats'] = agrk__xdrsi - pag__pgsx
        tia__ynn['llvm_pass_timings'] = library.recorded_timings
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
        vrwa__fog = nth.typeof(itemobj)
        with c.builder.if_then(cgutils.is_null(c.builder, vrwa__fog),
            likely=False):
            c.builder.store(cgutils.true_bit, errorptr)
            kpssk__dge.do_break()
        xxznc__xmh = c.builder.icmp_signed('!=', vrwa__fog, expected_typobj)
        if not isinstance(typ.dtype, types.Optional):
            with c.builder.if_then(xxznc__xmh, likely=False):
                c.builder.store(cgutils.true_bit, errorptr)
                c.pyapi.err_format('PyExc_TypeError',
                    "can't unbox heterogeneous list: %S != %S",
                    expected_typobj, vrwa__fog)
                c.pyapi.decref(vrwa__fog)
                kpssk__dge.do_break()
        c.pyapi.decref(vrwa__fog)
    dxmn__yibqj, list = listobj.ListInstance.allocate_ex(c.context, c.
        builder, typ, size)
    with c.builder.if_else(dxmn__yibqj, likely=True) as (ljruf__bbk, ouf__ugdus
        ):
        with ljruf__bbk:
            list.size = size
            lqb__itra = lir.Constant(size.type, 0)
            with c.builder.if_then(c.builder.icmp_signed('>', size,
                lqb__itra), likely=True):
                with _NumbaTypeHelper(c) as nth:
                    expected_typobj = nth.typeof(c.pyapi.list_getitem(obj,
                        lqb__itra))
                    with cgutils.for_range(c.builder, size) as kpssk__dge:
                        itemobj = c.pyapi.list_getitem(obj, kpssk__dge.index)
                        check_element_type(nth, itemobj, expected_typobj)
                        ibh__axp = c.unbox(typ.dtype, itemobj)
                        with c.builder.if_then(ibh__axp.is_error, likely=False
                            ):
                            c.builder.store(cgutils.true_bit, errorptr)
                            kpssk__dge.do_break()
                        list.setitem(kpssk__dge.index, ibh__axp.value,
                            incref=False)
                    c.pyapi.decref(expected_typobj)
            if typ.reflected:
                list.parent = obj
            with c.builder.if_then(c.builder.not_(c.builder.load(errorptr)),
                likely=False):
                c.pyapi.object_set_private_data(obj, list.meminfo)
            list.set_dirty(False)
            c.builder.store(list.value, listptr)
        with ouf__ugdus:
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
    rvuo__vhjvh, mpa__cdxqj, uilp__jpxnq, gijfj__iltb, rft__rtd = (
        compile_time_get_string_data(literal_string))
    qbeij__ycfww = builder.module
    gv = context.insert_const_bytes(qbeij__ycfww, rvuo__vhjvh)
    return lir.Constant.literal_struct([gv, context.get_constant(types.intp,
        mpa__cdxqj), context.get_constant(types.int32, uilp__jpxnq),
        context.get_constant(types.uint32, gijfj__iltb), context.
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
    fdi__ezhy = None
    if isinstance(shape, types.Integer):
        fdi__ezhy = 1
    elif isinstance(shape, (types.Tuple, types.UniTuple)):
        if all(isinstance(zgytb__ars, (types.Integer, types.IntEnumMember)) for
            zgytb__ars in shape):
            fdi__ezhy = len(shape)
    return fdi__ezhy


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
            fdi__ezhy = typ.ndim if isinstance(typ, types.ArrayCompatible
                ) else len(typ)
            if fdi__ezhy == 0:
                return name,
            else:
                return tuple('{}#{}'.format(name, i) for i in range(fdi__ezhy))
        else:
            return name,
    elif isinstance(obj, ir.Const):
        if isinstance(obj.value, tuple):
            return obj.value
        else:
            return obj.value,
    elif isinstance(obj, tuple):

        def get_names(x):
            cqzpd__hjer = self._get_names(x)
            if len(cqzpd__hjer) != 0:
                return cqzpd__hjer[0]
            return cqzpd__hjer
        return tuple(get_names(x) for x in obj)
    elif isinstance(obj, int):
        return obj,
    return ()


def get_equiv_const(self, obj):
    cqzpd__hjer = self._get_names(obj)
    if len(cqzpd__hjer) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_const(cqzpd__hjer[0])


def get_equiv_set(self, obj):
    cqzpd__hjer = self._get_names(obj)
    if len(cqzpd__hjer) != 1:
        return None
    return super(numba.parfors.array_analysis.ShapeEquivSet, self
        ).get_equiv_set(cqzpd__hjer[0])


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
    spj__pfo = []
    for shfop__kjyv in func_ir.arg_names:
        if shfop__kjyv in typemap and isinstance(typemap[shfop__kjyv],
            types.containers.UniTuple) and typemap[shfop__kjyv].count > 1000:
            msg = (
                """Tuple '{}' length must be smaller than 1000.
Large tuples lead to the generation of a prohibitively large LLVM IR which causes excessive memory pressure and large compile times.
As an alternative, the use of a 'list' is recommended in place of a 'tuple' as lists do not suffer from this problem."""
                .format(shfop__kjyv))
            raise errors.UnsupportedError(msg, func_ir.loc)
    for gaw__kiule in func_ir.blocks.values():
        for stmt in gaw__kiule.find_insts(ir.Assign):
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'make_function':
                    val = stmt.value
                    nxdi__nhn = getattr(val, 'code', None)
                    if nxdi__nhn is not None:
                        if getattr(val, 'closure', None) is not None:
                            lukq__qzlx = '<creating a function from a closure>'
                            frzl__qyv = ''
                        else:
                            lukq__qzlx = nxdi__nhn.co_name
                            frzl__qyv = '(%s) ' % lukq__qzlx
                    else:
                        lukq__qzlx = '<could not ascertain use case>'
                        frzl__qyv = ''
                    msg = (
                        'Numba encountered the use of a language feature it does not support in this context: %s (op code: make_function not supported). If the feature is explicitly supported it is likely that the result of the expression %sis being used in an unsupported manner.'
                         % (lukq__qzlx, frzl__qyv))
                    raise errors.UnsupportedError(msg, stmt.value.loc)
            if isinstance(stmt.value, (ir.Global, ir.FreeVar)):
                val = stmt.value
                val = getattr(val, 'value', None)
                if val is None:
                    continue
                tgrqu__kotts = False
                if isinstance(val, pytypes.FunctionType):
                    tgrqu__kotts = val in {numba.gdb, numba.gdb_init}
                if not tgrqu__kotts:
                    tgrqu__kotts = getattr(val, '_name', '') == 'gdb_internal'
                if tgrqu__kotts:
                    spj__pfo.append(stmt.loc)
            if isinstance(stmt.value, ir.Expr):
                if stmt.value.op == 'getattr' and stmt.value.attr == 'view':
                    var = stmt.value.value.name
                    if isinstance(typemap[var], types.Array):
                        continue
                    rzcq__odcii = func_ir.get_definition(var)
                    ocky__pbdy = guard(find_callname, func_ir, rzcq__odcii)
                    if ocky__pbdy and ocky__pbdy[1] == 'numpy':
                        ty = getattr(numpy, ocky__pbdy[0])
                        if numpy.issubdtype(ty, numpy.integer
                            ) or numpy.issubdtype(ty, numpy.floating):
                            continue
                    vfxha__drbn = '' if var.startswith('$'
                        ) else "'{}' ".format(var)
                    raise TypingError(
                        "'view' can only be called on NumPy dtypes, try wrapping the variable {}with 'np.<dtype>()'"
                        .format(vfxha__drbn), loc=stmt.loc)
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
    if len(spj__pfo) > 1:
        msg = """Calling either numba.gdb() or numba.gdb_init() more than once in a function is unsupported (strange things happen!), use numba.gdb_breakpoint() to create additional breakpoints instead.

Relevant documentation is available here:
https://numba.pydata.org/numba-doc/latest/user/troubleshoot.html/troubleshoot.html#using-numba-s-direct-gdb-bindings-in-nopython-mode

Conflicting calls found at:
 %s"""
        dljh__icct = '\n'.join([x.strformat() for x in spj__pfo])
        raise errors.UnsupportedError(msg % dljh__icct)


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
    pylc__qawc, agu__zbhc = next(iter(val.items()))
    hfbqr__ecpdv = typeof_impl(pylc__qawc, c)
    xfw__add = typeof_impl(agu__zbhc, c)
    if hfbqr__ecpdv is None or xfw__add is None:
        raise ValueError(
            f'Cannot type dict element type {type(pylc__qawc)}, {type(agu__zbhc)}'
            )
    return types.DictType(hfbqr__ecpdv, xfw__add)


def unbox_dicttype(typ, val, c):
    from llvmlite import ir as lir
    from numba.typed import dictobject
    from numba.typed.typeddict import Dict
    context = c.context
    ghg__wid = cgutils.alloca_once_value(c.builder, val)
    qvdjt__uqozk = c.pyapi.object_hasattr_string(val, '_opaque')
    vncd__smyxe = c.builder.icmp_unsigned('==', qvdjt__uqozk, lir.Constant(
        qvdjt__uqozk.type, 0))
    zwn__njjy = typ.key_type
    ufil__ngmo = typ.value_type

    def make_dict():
        return numba.typed.Dict.empty(zwn__njjy, ufil__ngmo)

    def copy_dict(out_dict, in_dict):
        for pylc__qawc, agu__zbhc in in_dict.items():
            out_dict[pylc__qawc] = agu__zbhc
    with c.builder.if_then(vncd__smyxe):
        fbyzd__obwu = c.pyapi.unserialize(c.pyapi.serialize_object(make_dict))
        ebnn__hxfwd = c.pyapi.call_function_objargs(fbyzd__obwu, [])
        idxa__rxjuu = c.pyapi.unserialize(c.pyapi.serialize_object(copy_dict))
        c.pyapi.call_function_objargs(idxa__rxjuu, [ebnn__hxfwd, val])
        c.builder.store(ebnn__hxfwd, ghg__wid)
    val = c.builder.load(ghg__wid)
    jagp__mklt = c.pyapi.unserialize(c.pyapi.serialize_object(Dict))
    lgak__muqfx = c.pyapi.object_type(val)
    mxtqq__lprs = c.builder.icmp_unsigned('==', lgak__muqfx, jagp__mklt)
    with c.builder.if_else(mxtqq__lprs) as (hxh__cwlzr, nnqel__plif):
        with hxh__cwlzr:
            xwp__ukoxo = c.pyapi.object_getattr_string(val, '_opaque')
            bvlrb__uhw = types.MemInfoPointer(types.voidptr)
            ibh__axp = c.unbox(bvlrb__uhw, xwp__ukoxo)
            mi = ibh__axp.value
            lyye__kisu = bvlrb__uhw, typeof(typ)

            def convert(mi, typ):
                return dictobject._from_meminfo(mi, typ)
            sig = signature(typ, *lyye__kisu)
            rdq__iys = context.get_constant_null(lyye__kisu[1])
            args = mi, rdq__iys
            ujmxq__yib, bnayh__mpvrd = c.pyapi.call_jit_code(convert, sig, args
                )
            c.context.nrt.decref(c.builder, typ, bnayh__mpvrd)
            c.pyapi.decref(xwp__ukoxo)
            qxtzs__ihzsn = c.builder.basic_block
        with nnqel__plif:
            c.pyapi.err_format('PyExc_TypeError',
                "can't unbox a %S as a %S", lgak__muqfx, jagp__mklt)
            aswau__jxzd = c.builder.basic_block
    ude__mhurg = c.builder.phi(bnayh__mpvrd.type)
    tfwxj__higgf = c.builder.phi(ujmxq__yib.type)
    ude__mhurg.add_incoming(bnayh__mpvrd, qxtzs__ihzsn)
    ude__mhurg.add_incoming(bnayh__mpvrd.type(None), aswau__jxzd)
    tfwxj__higgf.add_incoming(ujmxq__yib, qxtzs__ihzsn)
    tfwxj__higgf.add_incoming(cgutils.true_bit, aswau__jxzd)
    c.pyapi.decref(jagp__mklt)
    c.pyapi.decref(lgak__muqfx)
    with c.builder.if_then(vncd__smyxe):
        c.pyapi.decref(val)
    return NativeValue(ude__mhurg, is_error=tfwxj__higgf)


import numba.typed.typeddict
if _check_numba_change:
    lines = inspect.getsource(numba.core.pythonapi._unboxers.functions[
        numba.core.types.DictType])
    if hashlib.sha256(lines.encode()).hexdigest(
        ) != '5f6f183b94dc57838538c668a54c2476576c85d8553843f3219f5162c61e7816':
        warnings.warn('unbox_dicttype has changed')
numba.core.pythonapi._unboxers.functions[types.DictType] = unbox_dicttype


def mul_list_generic(self, args, kws):
    a, efsw__vbps = args
    if isinstance(a, types.List) and isinstance(efsw__vbps, types.Integer):
        return signature(a, a, types.intp)
    elif isinstance(a, types.Integer) and isinstance(efsw__vbps, types.List):
        return signature(efsw__vbps, types.intp, efsw__vbps)


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
        fbwre__gstsu, vjo__dtw = 0, 1
    else:
        fbwre__gstsu, vjo__dtw = 1, 0
    lhtte__danab = ListInstance(context, builder, sig.args[fbwre__gstsu],
        args[fbwre__gstsu])
    fgnss__dubru = lhtte__danab.size
    khbju__wbxb = args[vjo__dtw]
    lqb__itra = lir.Constant(khbju__wbxb.type, 0)
    khbju__wbxb = builder.select(cgutils.is_neg_int(builder, khbju__wbxb),
        lqb__itra, khbju__wbxb)
    gvkzk__xni = builder.mul(khbju__wbxb, fgnss__dubru)
    clkpc__ugezs = ListInstance.allocate(context, builder, sig.return_type,
        gvkzk__xni)
    clkpc__ugezs.size = gvkzk__xni
    with cgutils.for_range_slice(builder, lqb__itra, gvkzk__xni,
        fgnss__dubru, inc=True) as (gbkq__cnlx, _):
        with cgutils.for_range(builder, fgnss__dubru) as kpssk__dge:
            value = lhtte__danab.getitem(kpssk__dge.index)
            clkpc__ugezs.setitem(builder.add(kpssk__dge.index, gbkq__cnlx),
                value, incref=True)
    return impl_ret_new_ref(context, builder, sig.return_type, clkpc__ugezs
        .value)


def _native_set_to_python_list(typ, payload, c):
    from llvmlite import ir
    gvkzk__xni = payload.used
    listobj = c.pyapi.list_new(gvkzk__xni)
    dxmn__yibqj = cgutils.is_not_null(c.builder, listobj)
    with c.builder.if_then(dxmn__yibqj, likely=True):
        index = cgutils.alloca_once_value(c.builder, ir.Constant(gvkzk__xni
            .type, 0))
        with payload._iterate() as kpssk__dge:
            i = c.builder.load(index)
            item = kpssk__dge.entry.key
            c.context.nrt.incref(c.builder, typ.dtype, item)
            itemobj = c.box(typ.dtype, item)
            c.pyapi.list_setitem(listobj, i, itemobj)
            i = c.builder.add(i, ir.Constant(i.type, 1))
            c.builder.store(i, index)
    return dxmn__yibqj, listobj


def _lookup(self, item, h, for_insert=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    zje__dzchi = h.type
    xhz__zbnih = self.mask
    dtype = self._ty.dtype
    avb__yxkx = context.typing_context
    fnty = avb__yxkx.resolve_value_type(operator.eq)
    sig = fnty.get_call_type(avb__yxkx, (dtype, dtype), {})
    xawlp__poemk = context.get_function(fnty, sig)
    dkfvb__osay = ir.Constant(zje__dzchi, 1)
    unr__xzx = ir.Constant(zje__dzchi, 5)
    iqnkl__ojgc = cgutils.alloca_once_value(builder, h)
    index = cgutils.alloca_once_value(builder, builder.and_(h, xhz__zbnih))
    if for_insert:
        sevs__yntzc = xhz__zbnih.type(-1)
        txah__swq = cgutils.alloca_once_value(builder, sevs__yntzc)
    shk__kgnid = builder.append_basic_block('lookup.body')
    mgi__suh = builder.append_basic_block('lookup.found')
    ihgp__jqw = builder.append_basic_block('lookup.not_found')
    fabxe__cqsas = builder.append_basic_block('lookup.end')

    def check_entry(i):
        entry = self.get_entry(i)
        isi__gvqw = entry.hash
        with builder.if_then(builder.icmp_unsigned('==', h, isi__gvqw)):
            azgx__zwa = xawlp__poemk(builder, (item, entry.key))
            with builder.if_then(azgx__zwa):
                builder.branch(mgi__suh)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, isi__gvqw)):
            builder.branch(ihgp__jqw)
        if for_insert:
            with builder.if_then(numba.cpython.setobj.is_hash_deleted(
                context, builder, isi__gvqw)):
                jobz__man = builder.load(txah__swq)
                jobz__man = builder.select(builder.icmp_unsigned('==',
                    jobz__man, sevs__yntzc), i, jobz__man)
                builder.store(jobz__man, txah__swq)
    with cgutils.for_range(builder, ir.Constant(zje__dzchi, numba.cpython.
        setobj.LINEAR_PROBES)):
        i = builder.load(index)
        check_entry(i)
        i = builder.add(i, dkfvb__osay)
        i = builder.and_(i, xhz__zbnih)
        builder.store(i, index)
    builder.branch(shk__kgnid)
    with builder.goto_block(shk__kgnid):
        i = builder.load(index)
        check_entry(i)
        baluo__dne = builder.load(iqnkl__ojgc)
        baluo__dne = builder.lshr(baluo__dne, unr__xzx)
        i = builder.add(dkfvb__osay, builder.mul(i, unr__xzx))
        i = builder.and_(xhz__zbnih, builder.add(i, baluo__dne))
        builder.store(i, index)
        builder.store(baluo__dne, iqnkl__ojgc)
        builder.branch(shk__kgnid)
    with builder.goto_block(ihgp__jqw):
        if for_insert:
            i = builder.load(index)
            jobz__man = builder.load(txah__swq)
            i = builder.select(builder.icmp_unsigned('==', jobz__man,
                sevs__yntzc), i, jobz__man)
            builder.store(i, index)
        builder.branch(fabxe__cqsas)
    with builder.goto_block(mgi__suh):
        builder.branch(fabxe__cqsas)
    builder.position_at_end(fabxe__cqsas)
    tgrqu__kotts = builder.phi(ir.IntType(1), 'found')
    tgrqu__kotts.add_incoming(cgutils.true_bit, mgi__suh)
    tgrqu__kotts.add_incoming(cgutils.false_bit, ihgp__jqw)
    return tgrqu__kotts, builder.load(index)


def _add_entry(self, payload, entry, item, h, do_resize=True):
    context = self._context
    builder = self._builder
    wzpko__tmfh = entry.hash
    entry.hash = h
    context.nrt.incref(builder, self._ty.dtype, item)
    entry.key = item
    dtj__vevcs = payload.used
    dkfvb__osay = ir.Constant(dtj__vevcs.type, 1)
    dtj__vevcs = payload.used = builder.add(dtj__vevcs, dkfvb__osay)
    with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
        builder, wzpko__tmfh), likely=True):
        payload.fill = builder.add(payload.fill, dkfvb__osay)
    if do_resize:
        self.upsize(dtj__vevcs)
    self.set_dirty(True)


def _add_key(self, payload, item, h, do_resize=True):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    tgrqu__kotts, i = payload._lookup(item, h, for_insert=True)
    yfmt__csc = builder.not_(tgrqu__kotts)
    with builder.if_then(yfmt__csc):
        entry = payload.get_entry(i)
        wzpko__tmfh = entry.hash
        entry.hash = h
        context.nrt.incref(builder, self._ty.dtype, item)
        entry.key = item
        dtj__vevcs = payload.used
        dkfvb__osay = ir.Constant(dtj__vevcs.type, 1)
        dtj__vevcs = payload.used = builder.add(dtj__vevcs, dkfvb__osay)
        with builder.if_then(numba.cpython.setobj.is_hash_empty(context,
            builder, wzpko__tmfh), likely=True):
            payload.fill = builder.add(payload.fill, dkfvb__osay)
        if do_resize:
            self.upsize(dtj__vevcs)
        self.set_dirty(True)


def _remove_entry(self, payload, entry, do_resize=True):
    from llvmlite import ir
    entry.hash = ir.Constant(entry.hash.type, numba.cpython.setobj.DELETED)
    self._context.nrt.decref(self._builder, self._ty.dtype, entry.key)
    dtj__vevcs = payload.used
    dkfvb__osay = ir.Constant(dtj__vevcs.type, 1)
    dtj__vevcs = payload.used = self._builder.sub(dtj__vevcs, dkfvb__osay)
    if do_resize:
        self.downsize(dtj__vevcs)
    self.set_dirty(True)


def pop(self):
    context = self._context
    builder = self._builder
    qlm__mvpgz = context.get_value_type(self._ty.dtype)
    key = cgutils.alloca_once(builder, qlm__mvpgz)
    payload = self.payload
    with payload._next_entry() as entry:
        builder.store(entry.key, key)
        context.nrt.incref(builder, self._ty.dtype, entry.key)
        self._remove_entry(payload, entry)
    return builder.load(key)


def _resize(self, payload, nentries, errmsg):
    context = self._context
    builder = self._builder
    sca__qjalw = payload
    dxmn__yibqj = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(dxmn__yibqj), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (errmsg,))
    payload = self.payload
    with sca__qjalw._iterate() as kpssk__dge:
        entry = kpssk__dge.entry
        self._add_key(payload, entry.key, entry.hash, do_resize=False)
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(sca__qjalw.ptr)


def _replace_payload(self, nentries):
    context = self._context
    builder = self._builder
    with self.payload._iterate() as kpssk__dge:
        entry = kpssk__dge.entry
        context.nrt.decref(builder, self._ty.dtype, entry.key)
    self._free_payload(self.payload.ptr)
    dxmn__yibqj = self._allocate_payload(nentries, realloc=True)
    with builder.if_then(builder.not_(dxmn__yibqj), likely=False):
        context.call_conv.return_user_exc(builder, MemoryError, (
            'cannot reallocate set',))


def _allocate_payload(self, nentries, realloc=False):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    dxmn__yibqj = cgutils.alloca_once_value(builder, cgutils.true_bit)
    zje__dzchi = context.get_value_type(types.intp)
    lqb__itra = ir.Constant(zje__dzchi, 0)
    dkfvb__osay = ir.Constant(zje__dzchi, 1)
    vezry__oyjbx = context.get_data_type(types.SetPayload(self._ty))
    bvl__swlwd = context.get_abi_sizeof(vezry__oyjbx)
    tqd__onhka = self._entrysize
    bvl__swlwd -= tqd__onhka
    mowl__dled, qujo__imo = cgutils.muladd_with_overflow(builder, nentries,
        ir.Constant(zje__dzchi, tqd__onhka), ir.Constant(zje__dzchi,
        bvl__swlwd))
    with builder.if_then(qujo__imo, likely=False):
        builder.store(cgutils.false_bit, dxmn__yibqj)
    with builder.if_then(builder.load(dxmn__yibqj), likely=True):
        if realloc:
            mczum__zwzx = self._set.meminfo
            ipar__mfhx = context.nrt.meminfo_varsize_alloc(builder,
                mczum__zwzx, size=mowl__dled)
            lgu__volr = cgutils.is_null(builder, ipar__mfhx)
        else:
            qhrxu__asult = _imp_dtor(context, builder.module, self._ty)
            mczum__zwzx = context.nrt.meminfo_new_varsize_dtor(builder,
                mowl__dled, builder.bitcast(qhrxu__asult, cgutils.voidptr_t))
            lgu__volr = cgutils.is_null(builder, mczum__zwzx)
        with builder.if_else(lgu__volr, likely=False) as (ttd__arfle,
            ljruf__bbk):
            with ttd__arfle:
                builder.store(cgutils.false_bit, dxmn__yibqj)
            with ljruf__bbk:
                if not realloc:
                    self._set.meminfo = mczum__zwzx
                    self._set.parent = context.get_constant_null(types.pyobject
                        )
                payload = self.payload
                cgutils.memset(builder, payload.ptr, mowl__dled, 255)
                payload.used = lqb__itra
                payload.fill = lqb__itra
                payload.finger = lqb__itra
                ojq__zzo = builder.sub(nentries, dkfvb__osay)
                payload.mask = ojq__zzo
    return builder.load(dxmn__yibqj)


def _copy_payload(self, src_payload):
    from llvmlite import ir
    context = self._context
    builder = self._builder
    dxmn__yibqj = cgutils.alloca_once_value(builder, cgutils.true_bit)
    zje__dzchi = context.get_value_type(types.intp)
    lqb__itra = ir.Constant(zje__dzchi, 0)
    dkfvb__osay = ir.Constant(zje__dzchi, 1)
    vezry__oyjbx = context.get_data_type(types.SetPayload(self._ty))
    bvl__swlwd = context.get_abi_sizeof(vezry__oyjbx)
    tqd__onhka = self._entrysize
    bvl__swlwd -= tqd__onhka
    xhz__zbnih = src_payload.mask
    nentries = builder.add(dkfvb__osay, xhz__zbnih)
    mowl__dled = builder.add(ir.Constant(zje__dzchi, bvl__swlwd), builder.
        mul(ir.Constant(zje__dzchi, tqd__onhka), nentries))
    with builder.if_then(builder.load(dxmn__yibqj), likely=True):
        qhrxu__asult = _imp_dtor(context, builder.module, self._ty)
        mczum__zwzx = context.nrt.meminfo_new_varsize_dtor(builder,
            mowl__dled, builder.bitcast(qhrxu__asult, cgutils.voidptr_t))
        lgu__volr = cgutils.is_null(builder, mczum__zwzx)
        with builder.if_else(lgu__volr, likely=False) as (ttd__arfle,
            ljruf__bbk):
            with ttd__arfle:
                builder.store(cgutils.false_bit, dxmn__yibqj)
            with ljruf__bbk:
                self._set.meminfo = mczum__zwzx
                payload = self.payload
                payload.used = src_payload.used
                payload.fill = src_payload.fill
                payload.finger = lqb__itra
                payload.mask = xhz__zbnih
                cgutils.raw_memcpy(builder, payload.entries, src_payload.
                    entries, nentries, tqd__onhka)
                with src_payload._iterate() as kpssk__dge:
                    context.nrt.incref(builder, self._ty.dtype, kpssk__dge.
                        entry.key)
    return builder.load(dxmn__yibqj)


def _imp_dtor(context, module, set_type):
    from llvmlite import ir
    beo__cemis = context.get_value_type(types.voidptr)
    dtw__pmaky = context.get_value_type(types.uintp)
    fnty = ir.FunctionType(ir.VoidType(), [beo__cemis, dtw__pmaky, beo__cemis])
    ubxdf__klte = f'_numba_set_dtor_{set_type}'
    fn = cgutils.get_or_insert_function(module, fnty, name=ubxdf__klte)
    if fn.is_declaration:
        fn.linkage = 'linkonce_odr'
        builder = ir.IRBuilder(fn.append_basic_block())
        uskes__hnog = builder.bitcast(fn.args[0], cgutils.voidptr_t.
            as_pointer())
        payload = numba.cpython.setobj._SetPayload(context, builder,
            set_type, uskes__hnog)
        with payload._iterate() as kpssk__dge:
            entry = kpssk__dge.entry
            context.nrt.decref(builder, set_type.dtype, entry.key)
        builder.ret_void()
    return fn


@lower_builtin(set, types.IterableType)
def set_constructor(context, builder, sig, args):
    set_type = sig.return_type
    akbt__dvp, = sig.args
    txay__ndzt, = args
    zpx__ntqd = numba.core.imputils.call_len(context, builder, akbt__dvp,
        txay__ndzt)
    inst = numba.cpython.setobj.SetInstance.allocate(context, builder,
        set_type, zpx__ntqd)
    with numba.core.imputils.for_iter(context, builder, akbt__dvp, txay__ndzt
        ) as kpssk__dge:
        inst.add(kpssk__dge.value)
        context.nrt.decref(builder, set_type.dtype, kpssk__dge.value)
    return numba.core.imputils.impl_ret_new_ref(context, builder, set_type,
        inst.value)


@lower_builtin('set.update', types.Set, types.IterableType)
def set_update(context, builder, sig, args):
    inst = numba.cpython.setobj.SetInstance(context, builder, sig.args[0],
        args[0])
    akbt__dvp = sig.args[1]
    txay__ndzt = args[1]
    zpx__ntqd = numba.core.imputils.call_len(context, builder, akbt__dvp,
        txay__ndzt)
    if zpx__ntqd is not None:
        yml__xifon = builder.add(inst.payload.used, zpx__ntqd)
        inst.upsize(yml__xifon)
    with numba.core.imputils.for_iter(context, builder, akbt__dvp, txay__ndzt
        ) as kpssk__dge:
        kwg__frv = context.cast(builder, kpssk__dge.value, akbt__dvp.dtype,
            inst.dtype)
        inst.add(kwg__frv)
        context.nrt.decref(builder, akbt__dvp.dtype, kpssk__dge.value)
    if zpx__ntqd is not None:
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
