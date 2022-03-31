import numba
import numpy as np
import pandas as pd
from numba.core import ir, ir_utils, typeinfer, types
from numba.core.ir_utils import compile_to_numba_ir, replace_arg_nodes
import bodo
import bodo.ir.connector
from bodo import objmode
from bodo.libs.str_ext import string_type
from bodo.transforms import distributed_analysis, distributed_pass
from bodo.utils.utils import check_java_installation
from bodo.utils.utils import sanitize_varname


class JsonReader(ir.Stmt):

    def __init__(self, df_out, loc, out_vars, out_types, file_name,
        df_colnames, orient, convert_dates, precise_float, lines, compression):
        self.connector_typ = 'json'
        self.df_out = df_out
        self.loc = loc
        self.out_vars = out_vars
        self.out_types = out_types
        self.file_name = file_name
        self.df_colnames = df_colnames
        self.orient = orient
        self.convert_dates = convert_dates
        self.precise_float = precise_float
        self.lines = lines
        self.compression = compression

    def __repr__(self):
        return ('{} = ReadJson(file={}, col_names={}, types={}, vars={})'.
            format(self.df_out, self.file_name, self.df_colnames, self.
            out_types, self.out_vars))


import llvmlite.binding as ll
from bodo.io import json_cpp
ll.add_symbol('json_file_chunk_reader', json_cpp.json_file_chunk_reader)
json_file_chunk_reader = types.ExternalFunction('json_file_chunk_reader',
    bodo.ir.connector.stream_reader_type(types.voidptr, types.bool_, types.
    bool_, types.int64, types.voidptr, types.voidptr))


def remove_dead_json(json_node, lives_no_aliases, lives, arg_aliases,
    alias_map, func_ir, typemap):
    cdec__wibr = []
    rbk__aypf = []
    cmejq__cdnq = []
    for bhfio__jvum, jgs__dxbuy in enumerate(json_node.out_vars):
        if jgs__dxbuy.name in lives:
            cdec__wibr.append(json_node.df_colnames[bhfio__jvum])
            rbk__aypf.append(json_node.out_vars[bhfio__jvum])
            cmejq__cdnq.append(json_node.out_types[bhfio__jvum])
    json_node.df_colnames = cdec__wibr
    json_node.out_vars = rbk__aypf
    json_node.out_types = cmejq__cdnq
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        gicm__mga = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        sghtr__wjqr = json_node.loc.strformat()
        cnt__jwww = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', gicm__mga,
            sghtr__wjqr, cnt__jwww)
        cqc__vdyi = [ypvad__trj for bhfio__jvum, ypvad__trj in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            bhfio__jvum], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if cqc__vdyi:
            guby__ckq = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', guby__ckq,
                sghtr__wjqr, cqc__vdyi)
    parallel = False
    if array_dists is not None:
        parallel = True
        for oogsd__eiw in json_node.out_vars:
            if array_dists[oogsd__eiw.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                oogsd__eiw.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    lwv__jrbg = len(json_node.out_vars)
    ktqb__aiz = ', '.join('arr' + str(bhfio__jvum) for bhfio__jvum in range
        (lwv__jrbg))
    xbsy__lzeo = 'def json_impl(fname):\n'
    xbsy__lzeo += '    ({},) = _json_reader_py(fname)\n'.format(ktqb__aiz)
    wetlz__blpyc = {}
    exec(xbsy__lzeo, {}, wetlz__blpyc)
    hxm__awh = wetlz__blpyc['json_impl']
    bsk__ckjv = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    pnic__olq = compile_to_numba_ir(hxm__awh, {'_json_reader_py': bsk__ckjv
        }, typingctx=typingctx, targetctx=targetctx, arg_typs=(string_type,
        ), typemap=typemap, calltypes=calltypes).blocks.popitem()[1]
    replace_arg_nodes(pnic__olq, [json_node.file_name])
    rojr__nzgm = pnic__olq.body[:-3]
    for bhfio__jvum in range(len(json_node.out_vars)):
        rojr__nzgm[-len(json_node.out_vars) + bhfio__jvum
            ].target = json_node.out_vars[bhfio__jvum]
    return rojr__nzgm


numba.parfors.array_analysis.array_analysis_extensions[JsonReader
    ] = bodo.ir.connector.connector_array_analysis
distributed_analysis.distributed_analysis_extensions[JsonReader
    ] = bodo.ir.connector.connector_distributed_analysis
typeinfer.typeinfer_extensions[JsonReader
    ] = bodo.ir.connector.connector_typeinfer
ir_utils.visit_vars_extensions[JsonReader
    ] = bodo.ir.connector.visit_vars_connector
ir_utils.remove_dead_extensions[JsonReader] = remove_dead_json
numba.core.analysis.ir_extension_usedefs[JsonReader
    ] = bodo.ir.connector.connector_usedefs
ir_utils.copy_propagate_extensions[JsonReader
    ] = bodo.ir.connector.get_copies_connector
ir_utils.apply_copy_propagate_extensions[JsonReader
    ] = bodo.ir.connector.apply_copies_connector
ir_utils.build_defs_extensions[JsonReader
    ] = bodo.ir.connector.build_connector_definitions
distributed_pass.distributed_run_extensions[JsonReader] = json_distributed_run
compiled_funcs = []


def _gen_json_reader_py(col_names, col_typs, typingctx, targetctx, parallel,
    orient, convert_dates, precise_float, lines, compression):
    jfrm__sal = [sanitize_varname(ypvad__trj) for ypvad__trj in col_names]
    oqrb__gaxm = ', '.join(str(bhfio__jvum) for bhfio__jvum, kzohk__anaz in
        enumerate(col_typs) if kzohk__anaz.dtype == types.NPDatetime('ns'))
    yhg__yexs = ', '.join(["{}='{}'".format(vtvz__oyv, bodo.ir.csv_ext.
        _get_dtype_str(kzohk__anaz)) for vtvz__oyv, kzohk__anaz in zip(
        jfrm__sal, col_typs)])
    ckk__rupf = ', '.join(["'{}':{}".format(uge__zylfc, bodo.ir.csv_ext.
        _get_pd_dtype_str(kzohk__anaz)) for uge__zylfc, kzohk__anaz in zip(
        col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    xbsy__lzeo = 'def json_reader_py(fname):\n'
    xbsy__lzeo += '  check_java_installation(fname)\n'
    xbsy__lzeo += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    xbsy__lzeo += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    xbsy__lzeo += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    xbsy__lzeo += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    xbsy__lzeo += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    xbsy__lzeo += "      raise FileNotFoundError('File does not exist')\n"
    xbsy__lzeo += '  with objmode({}):\n'.format(yhg__yexs)
    xbsy__lzeo += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    xbsy__lzeo += '       convert_dates = {}, \n'.format(convert_dates)
    xbsy__lzeo += '       precise_float={}, \n'.format(precise_float)
    xbsy__lzeo += '       lines={}, \n'.format(lines)
    xbsy__lzeo += '       dtype={{{}}},\n'.format(ckk__rupf)
    xbsy__lzeo += '       )\n'
    for vtvz__oyv, uge__zylfc in zip(jfrm__sal, col_names):
        xbsy__lzeo += '    if len(df) > 0:\n'
        xbsy__lzeo += "        {} = df['{}'].values\n".format(vtvz__oyv,
            uge__zylfc)
        xbsy__lzeo += '    else:\n'
        xbsy__lzeo += '        {} = np.array([])\n'.format(vtvz__oyv)
    xbsy__lzeo += '  return ({},)\n'.format(', '.join(mok__kyv for mok__kyv in
        jfrm__sal))
    xbym__biqh = globals()
    wetlz__blpyc = {}
    exec(xbsy__lzeo, xbym__biqh, wetlz__blpyc)
    bsk__ckjv = wetlz__blpyc['json_reader_py']
    gjf__njevd = numba.njit(bsk__ckjv)
    compiled_funcs.append(gjf__njevd)
    return gjf__njevd
