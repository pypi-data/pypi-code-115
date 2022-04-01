"""
JIT support for Python's logging module
"""
import logging
import numba
from numba.core import types
from numba.core.imputils import lower_constant
from numba.core.typing.templates import bound_function
from numba.core.typing.templates import AttributeTemplate, infer_getattr, signature
from numba.extending import NativeValue, box, models, overload_attribute, overload_method, register_model, typeof_impl, unbox
from bodo.utils.typing import create_unsupported_overload, gen_objmode_attr_overload


class LoggingLoggerType(types.Type):

    def __init__(self, is_root=False):
        self.is_root = is_root
        super(LoggingLoggerType, self).__init__(name=
            f'LoggingLoggerType(is_root={is_root})')


@typeof_impl.register(logging.RootLogger)
@typeof_impl.register(logging.Logger)
def typeof_logging(val, c):
    if isinstance(val, logging.RootLogger):
        return LoggingLoggerType(is_root=True)
    else:
        return LoggingLoggerType(is_root=False)


register_model(LoggingLoggerType)(models.OpaqueModel)


@box(LoggingLoggerType)
def box_logging_logger(typ, val, c):
    c.pyapi.incref(val)
    return val


@unbox(LoggingLoggerType)
def unbox_logging_logger(typ, obj, c):
    c.pyapi.incref(obj)
    return NativeValue(obj)


@lower_constant(LoggingLoggerType)
def lower_constant_logger(context, builder, ty, pyval):
    ylk__fiwi = context.get_python_api(builder)
    return ylk__fiwi.unserialize(ylk__fiwi.serialize_object(pyval))


gen_objmode_attr_overload(LoggingLoggerType, 'level', None, types.int64)
gen_objmode_attr_overload(LoggingLoggerType, 'name', None, 'unicode_type')
gen_objmode_attr_overload(LoggingLoggerType, 'propagate', None, types.boolean)
gen_objmode_attr_overload(LoggingLoggerType, 'disabled', None, types.boolean)
gen_objmode_attr_overload(LoggingLoggerType, 'parent', None,
    LoggingLoggerType())
gen_objmode_attr_overload(LoggingLoggerType, 'root', None,
    LoggingLoggerType(is_root=True))


@infer_getattr
class LoggingLoggerAttribute(AttributeTemplate):
    key = LoggingLoggerType

    def _resolve_helper(self, logger_typ, args, kws):
        kws = dict(kws)
        jqpi__wsl = ', '.join('e{}'.format(mbsyk__vwj) for mbsyk__vwj in
            range(len(args)))
        if jqpi__wsl:
            jqpi__wsl += ', '
        rsq__mdu = ', '.join("{} = ''".format(mlxff__ckk) for mlxff__ckk in
            kws.keys())
        nsg__cyztb = f'def format_stub(string, {jqpi__wsl} {rsq__mdu}):\n'
        nsg__cyztb += '    pass\n'
        gus__fcr = {}
        exec(nsg__cyztb, {}, gus__fcr)
        mmmxg__hhvy = gus__fcr['format_stub']
        ygvw__jlxz = numba.core.utils.pysignature(mmmxg__hhvy)
        gyxaa__qdkf = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, gyxaa__qdkf).replace(pysig=ygvw__jlxz)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for lbd__dcv in ('logging.Logger', 'logging.RootLogger'):
        for hfet__ggr in func_names:
            ycgjh__urmm = f'@bound_function("{lbd__dcv}.{hfet__ggr}")\n'
            ycgjh__urmm += (
                f'def resolve_{hfet__ggr}(self, logger_typ, args, kws):\n')
            ycgjh__urmm += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(ycgjh__urmm)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for wbf__tvh in logging_logger_unsupported_attrs:
        sbu__piqq = 'logging.Logger.' + wbf__tvh
        overload_attribute(LoggingLoggerType, wbf__tvh)(
            create_unsupported_overload(sbu__piqq))
    for nxt__auedc in logging_logger_unsupported_methods:
        sbu__piqq = 'logging.Logger.' + nxt__auedc
        overload_method(LoggingLoggerType, nxt__auedc)(
            create_unsupported_overload(sbu__piqq))


_install_logging_logger_unsupported_objects()
