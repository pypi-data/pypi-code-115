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
    ufirk__bglr = context.get_python_api(builder)
    return ufirk__bglr.unserialize(ufirk__bglr.serialize_object(pyval))


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
        rpvdx__vjem = ', '.join('e{}'.format(kvdui__rzh) for kvdui__rzh in
            range(len(args)))
        if rpvdx__vjem:
            rpvdx__vjem += ', '
        xhn__hxy = ', '.join("{} = ''".format(rwmy__umjit) for rwmy__umjit in
            kws.keys())
        ruau__somq = f'def format_stub(string, {rpvdx__vjem} {xhn__hxy}):\n'
        ruau__somq += '    pass\n'
        cwuu__zdeo = {}
        exec(ruau__somq, {}, cwuu__zdeo)
        vha__vyr = cwuu__zdeo['format_stub']
        cqfk__fwie = numba.core.utils.pysignature(vha__vyr)
        igln__dbz = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, igln__dbz).replace(pysig=cqfk__fwie)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for hsp__ahoov in ('logging.Logger', 'logging.RootLogger'):
        for xzyk__qcqmt in func_names:
            hdudc__uei = f'@bound_function("{hsp__ahoov}.{xzyk__qcqmt}")\n'
            hdudc__uei += (
                f'def resolve_{xzyk__qcqmt}(self, logger_typ, args, kws):\n')
            hdudc__uei += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(hdudc__uei)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for sanu__lurgn in logging_logger_unsupported_attrs:
        jkd__xau = 'logging.Logger.' + sanu__lurgn
        overload_attribute(LoggingLoggerType, sanu__lurgn)(
            create_unsupported_overload(jkd__xau))
    for ypm__wiar in logging_logger_unsupported_methods:
        jkd__xau = 'logging.Logger.' + ypm__wiar
        overload_method(LoggingLoggerType, ypm__wiar)(
            create_unsupported_overload(jkd__xau))


_install_logging_logger_unsupported_objects()
