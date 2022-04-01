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
    pzd__hesbl = context.get_python_api(builder)
    return pzd__hesbl.unserialize(pzd__hesbl.serialize_object(pyval))


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
        ktdf__hpkfg = ', '.join('e{}'.format(les__iob) for les__iob in
            range(len(args)))
        if ktdf__hpkfg:
            ktdf__hpkfg += ', '
        wxgr__gkku = ', '.join("{} = ''".format(bfp__fcr) for bfp__fcr in
            kws.keys())
        vozj__fbe = f'def format_stub(string, {ktdf__hpkfg} {wxgr__gkku}):\n'
        vozj__fbe += '    pass\n'
        mmw__sgx = {}
        exec(vozj__fbe, {}, mmw__sgx)
        fwm__ecf = mmw__sgx['format_stub']
        rlli__vqmd = numba.core.utils.pysignature(fwm__ecf)
        ltnkt__wnm = (logger_typ,) + args + tuple(kws.values())
        return signature(logger_typ, ltnkt__wnm).replace(pysig=rlli__vqmd)
    func_names = ('debug', 'warning', 'warn', 'info', 'error', 'exception',
        'critical', 'log', 'setLevel')
    for zrjs__kpyai in ('logging.Logger', 'logging.RootLogger'):
        for hbvy__ciirb in func_names:
            xpbjh__jzjbu = f'@bound_function("{zrjs__kpyai}.{hbvy__ciirb}")\n'
            xpbjh__jzjbu += (
                f'def resolve_{hbvy__ciirb}(self, logger_typ, args, kws):\n')
            xpbjh__jzjbu += (
                '    return self._resolve_helper(logger_typ, args, kws)')
            exec(xpbjh__jzjbu)


logging_logger_unsupported_attrs = {'filters', 'handlers', 'manager'}
logging_logger_unsupported_methods = {'addHandler', 'callHandlers', 'fatal',
    'findCaller', 'getChild', 'getEffectiveLevel', 'handle', 'hasHandlers',
    'isEnabledFor', 'makeRecord', 'removeHandler'}


def _install_logging_logger_unsupported_objects():
    for bmkp__sztq in logging_logger_unsupported_attrs:
        nzoez__lxwhl = 'logging.Logger.' + bmkp__sztq
        overload_attribute(LoggingLoggerType, bmkp__sztq)(
            create_unsupported_overload(nzoez__lxwhl))
    for tjocf__vjzha in logging_logger_unsupported_methods:
        nzoez__lxwhl = 'logging.Logger.' + tjocf__vjzha
        overload_method(LoggingLoggerType, tjocf__vjzha)(
            create_unsupported_overload(nzoez__lxwhl))


_install_logging_logger_unsupported_objects()
