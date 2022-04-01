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
    sfuf__ezcjz = context.get_python_api(builder)
    return sfuf__ezcjz.unserialize(sfuf__ezcjz.serialize_object(pyval))


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
        nrf__aopy = ', '.join('e{}'.format(jpk__ajda) for jpk__ajda in
            range(len(args)))
        if nrf__aopy:
            nrf__aopy += ', '
        ubkxe__jwkl = ', '.join("{} = ''".format(zhafx__luymr) for
            zhafx__luymr in kws.keys())
        dflhi__zkplg = f'def format_stub(string, {nrf__aopy} {ubkxe__jwkl}):\n'
        dflhi__zkplg += '    pass\n'
        lyy__wbm = {}
        exec(dflhi__zkplg, {}, lyy__wbm)
        ivei__jmtcm = lyy__wbm['format_stub']
        zyeuo__wdi = numba.core.utils.pysignature(ivei__jmtcm)
        chss__zxw = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, chss__zxw).replace(pysig=zyeuo__wdi)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for befbh__hdcu in ('logging.Logger', 'logging.RootLogger'):
        for eey__bfis in func_names:
            rxmmc__qkbak = f'@bound_function("{befbh__hdcu}.{eey__bfis}")\n'
            rxmmc__qkbak += (
                f'def resolve_{eey__bfis}(self, logger_typ, args, kws):\n')
            rxmmc__qkbak += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(rxmmc__qkbak)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for jyqyz__xknf in logging_logger_unsupported_attrs:
        lzcpp__eicdl = 'logging.Logger.' + jyqyz__xknf
        overload_attribute(LoggingLoggerType, jyqyz__xknf)(
            create_unsupported_overload(lzcpp__eicdl))
    for iqsu__nixs in logging_logger_unsupported_methods:
        lzcpp__eicdl = 'logging.Logger.' + iqsu__nixs
        overload_method(LoggingLoggerType, iqsu__nixs)(
            create_unsupported_overload(lzcpp__eicdl))


_install_logging_logger_unsupported_objects()
