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
    sqx__nrke = []
    hxpvd__cvrtu = []
    wyf__csg = []
    for uzrde__wecud, ydx__wgvl in enumerate(json_node.out_vars):
        if ydx__wgvl.name in lives:
            sqx__nrke.append(json_node.df_colnames[uzrde__wecud])
            hxpvd__cvrtu.append(json_node.out_vars[uzrde__wecud])
            wyf__csg.append(json_node.out_types[uzrde__wecud])
    json_node.df_colnames = sqx__nrke
    json_node.out_vars = hxpvd__cvrtu
    json_node.out_types = wyf__csg
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        qdyhx__svyrr = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        usub__hku = json_node.loc.strformat()
        fbsw__nrhrf = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', qdyhx__svyrr,
            usub__hku, fbsw__nrhrf)
        kawpb__ieh = [iip__lvr for uzrde__wecud, iip__lvr in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            uzrde__wecud], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if kawpb__ieh:
            ohkeo__tsziv = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                ohkeo__tsziv, usub__hku, kawpb__ieh)
    parallel = False
    if array_dists is not None:
        parallel = True
        for ctpgj__lgf in json_node.out_vars:
            if array_dists[ctpgj__lgf.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                ctpgj__lgf.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    azgwq__seir = len(json_node.out_vars)
    wntm__yulju = ', '.join('arr' + str(uzrde__wecud) for uzrde__wecud in
        range(azgwq__seir))
    ezgs__ufet = 'def json_impl(fname):\n'
    ezgs__ufet += '    ({},) = _json_reader_py(fname)\n'.format(wntm__yulju)
    jjlkq__sbysw = {}
    exec(ezgs__ufet, {}, jjlkq__sbysw)
    tfk__vggbg = jjlkq__sbysw['json_impl']
    kyidr__smym = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    rzxk__vgk = compile_to_numba_ir(tfk__vggbg, {'_json_reader_py':
        kyidr__smym}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type,), typemap=typemap, calltypes=calltypes).blocks.popitem()[1
        ]
    replace_arg_nodes(rzxk__vgk, [json_node.file_name])
    ktpo__axhz = rzxk__vgk.body[:-3]
    for uzrde__wecud in range(len(json_node.out_vars)):
        ktpo__axhz[-len(json_node.out_vars) + uzrde__wecud
            ].target = json_node.out_vars[uzrde__wecud]
    return ktpo__axhz


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
    kqzp__ngfkx = [sanitize_varname(iip__lvr) for iip__lvr in col_names]
    gef__opba = ', '.join(str(uzrde__wecud) for uzrde__wecud, fprac__gxry in
        enumerate(col_typs) if fprac__gxry.dtype == types.NPDatetime('ns'))
    oqawz__clm = ', '.join(["{}='{}'".format(bucaz__rht, bodo.ir.csv_ext.
        _get_dtype_str(fprac__gxry)) for bucaz__rht, fprac__gxry in zip(
        kqzp__ngfkx, col_typs)])
    tvgui__stya = ', '.join(["'{}':{}".format(iurx__mkr, bodo.ir.csv_ext.
        _get_pd_dtype_str(fprac__gxry)) for iurx__mkr, fprac__gxry in zip(
        col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    ezgs__ufet = 'def json_reader_py(fname):\n'
    ezgs__ufet += '  check_java_installation(fname)\n'
    ezgs__ufet += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    ezgs__ufet += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    ezgs__ufet += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    ezgs__ufet += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    ezgs__ufet += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    ezgs__ufet += "      raise FileNotFoundError('File does not exist')\n"
    ezgs__ufet += '  with objmode({}):\n'.format(oqawz__clm)
    ezgs__ufet += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    ezgs__ufet += '       convert_dates = {}, \n'.format(convert_dates)
    ezgs__ufet += '       precise_float={}, \n'.format(precise_float)
    ezgs__ufet += '       lines={}, \n'.format(lines)
    ezgs__ufet += '       dtype={{{}}},\n'.format(tvgui__stya)
    ezgs__ufet += '       )\n'
    for bucaz__rht, iurx__mkr in zip(kqzp__ngfkx, col_names):
        ezgs__ufet += '    if len(df) > 0:\n'
        ezgs__ufet += "        {} = df['{}'].values\n".format(bucaz__rht,
            iurx__mkr)
        ezgs__ufet += '    else:\n'
        ezgs__ufet += '        {} = np.array([])\n'.format(bucaz__rht)
    ezgs__ufet += '  return ({},)\n'.format(', '.join(zdqow__mgc for
        zdqow__mgc in kqzp__ngfkx))
    bzn__geaut = globals()
    jjlkq__sbysw = {}
    exec(ezgs__ufet, bzn__geaut, jjlkq__sbysw)
    kyidr__smym = jjlkq__sbysw['json_reader_py']
    byqfv__xrsm = numba.njit(kyidr__smym)
    compiled_funcs.append(byqfv__xrsm)
    return byqfv__xrsm
