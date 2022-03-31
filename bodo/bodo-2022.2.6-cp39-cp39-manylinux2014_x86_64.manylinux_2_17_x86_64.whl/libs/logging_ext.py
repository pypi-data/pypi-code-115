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
    hmrjj__gtxxo = context.get_python_api(builder)
    return hmrjj__gtxxo.unserialize(hmrjj__gtxxo.serialize_object(pyval))


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
        xwwws__lbd = ', '.join('e{}'.format(zefpw__irge) for zefpw__irge in
            range(len(args)))
        if xwwws__lbd:
            xwwws__lbd += ', '
        vajh__suztt = ', '.join("{} = ''".format(yhw__mxo) for yhw__mxo in
            kws.keys())
        xzyi__ojv = f'def format_stub(string, {xwwws__lbd} {vajh__suztt}):\n'
        xzyi__ojv += '    pass\n'
        hyhvi__heyia = {}
        exec(xzyi__ojv, {}, hyhvi__heyia)
        ygyc__sxurt = hyhvi__heyia['format_stub']
        dpg__mmw = numba.core.utils.pysignature(ygyc__sxurt)
        gjob__ouof = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, gjob__ouof).replace(pysig=dpg__mmw)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for vfr__rnw in ('logging.Logger', 'logging.RootLogger'):
        for ytuv__xottl in func_names:
            xkr__rcjnm = f'@bound_function("{vfr__rnw}.{ytuv__xottl}")\n'
            xkr__rcjnm += (
                f'def resolve_{ytuv__xottl}(self, logger_typ, args, kws):\n')
            xkr__rcjnm += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(xkr__rcjnm)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for bfyka__wnd in logging_logger_unsupported_attrs:
        gyrq__tgfc = 'logging.Logger.' + bfyka__wnd
        overload_attribute(LoggingLoggerType, bfyka__wnd)(
            create_unsupported_overload(gyrq__tgfc))
    for xlw__wqte in logging_logger_unsupported_methods:
        gyrq__tgfc = 'logging.Logger.' + xlw__wqte
        overload_method(LoggingLoggerType, xlw__wqte)(
            create_unsupported_overload(gyrq__tgfc))


_install_logging_logger_unsupported_objects()
