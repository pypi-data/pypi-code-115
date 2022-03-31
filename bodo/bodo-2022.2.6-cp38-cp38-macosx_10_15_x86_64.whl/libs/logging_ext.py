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
    bvhh__syg = context.get_python_api(builder)
    return bvhh__syg.unserialize(bvhh__syg.serialize_object(pyval))


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
        fypfh__rrhs = ', '.join('e{}'.format(kkpqp__ewtx) for kkpqp__ewtx in
            range(len(args)))
        if fypfh__rrhs:
            fypfh__rrhs += ', '
        qcr__monr = ', '.join("{} = ''".format(vbjss__xxd) for vbjss__xxd in
            kws.keys())
        anpe__pookl = f'def format_stub(string, {fypfh__rrhs} {qcr__monr}):\n'
        anpe__pookl += '    pass\n'
        viir__focme = {}
        exec(anpe__pookl, {}, viir__focme)
        idfa__spmqz = viir__focme['format_stub']
        fyzx__yqvg = numba.core.utils.pysignature(idfa__spmqz)
        ttq__uzjk = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, ttq__uzjk).replace(pysig=fyzx__yqvg)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for ufw__rrh in ('logging.Logger', 'logging.RootLogger'):
        for zfhlg__vnzrf in func_names:
            kqobh__psmx = f'@bound_function("{ufw__rrh}.{zfhlg__vnzrf}")\n'
            kqobh__psmx += (
                f'def resolve_{zfhlg__vnzrf}(self, logger_typ, args, kws):\n')
            kqobh__psmx += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(kqobh__psmx)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for cvh__dsur in logging_logger_unsupported_attrs:
        kuv__wzrz = 'logging.Logger.' + cvh__dsur
        overload_attribute(LoggingLoggerType, cvh__dsur)(
            create_unsupported_overload(kuv__wzrz))
    for kexl__uisnv in logging_logger_unsupported_methods:
        kuv__wzrz = 'logging.Logger.' + kexl__uisnv
        overload_method(LoggingLoggerType, kexl__uisnv)(
            create_unsupported_overload(kuv__wzrz))


_install_logging_logger_unsupported_objects()
