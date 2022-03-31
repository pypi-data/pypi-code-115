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
    npi__cecl = []
    fdzw__dvi = []
    wng__nsuka = []
    for iznf__dtcx, numg__zqanq in enumerate(json_node.out_vars):
        if numg__zqanq.name in lives:
            npi__cecl.append(json_node.df_colnames[iznf__dtcx])
            fdzw__dvi.append(json_node.out_vars[iznf__dtcx])
            wng__nsuka.append(json_node.out_types[iznf__dtcx])
    json_node.df_colnames = npi__cecl
    json_node.out_vars = fdzw__dvi
    json_node.out_types = wng__nsuka
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        xkuoe__qae = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        toih__ahe = json_node.loc.strformat()
        uqx__bifgv = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', xkuoe__qae,
            toih__ahe, uqx__bifgv)
        vcv__demb = [eihmh__qti for iznf__dtcx, eihmh__qti in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            iznf__dtcx], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if vcv__demb:
            qjd__pmpxb = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', qjd__pmpxb,
                toih__ahe, vcv__demb)
    parallel = False
    if array_dists is not None:
        parallel = True
        for xra__ofljh in json_node.out_vars:
            if array_dists[xra__ofljh.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                xra__ofljh.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    qwxyo__zqb = len(json_node.out_vars)
    weztt__lvvny = ', '.join('arr' + str(iznf__dtcx) for iznf__dtcx in
        range(qwxyo__zqb))
    ukfs__yuyl = 'def json_impl(fname):\n'
    ukfs__yuyl += '    ({},) = _json_reader_py(fname)\n'.format(weztt__lvvny)
    ctac__zsue = {}
    exec(ukfs__yuyl, {}, ctac__zsue)
    uvdpt__kxt = ctac__zsue['json_impl']
    grdb__snqt = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    ixrb__lgnn = compile_to_numba_ir(uvdpt__kxt, {'_json_reader_py':
        grdb__snqt}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type,), typemap=typemap, calltypes=calltypes).blocks.popitem()[1
        ]
    replace_arg_nodes(ixrb__lgnn, [json_node.file_name])
    mdno__krpd = ixrb__lgnn.body[:-3]
    for iznf__dtcx in range(len(json_node.out_vars)):
        mdno__krpd[-len(json_node.out_vars) + iznf__dtcx
            ].target = json_node.out_vars[iznf__dtcx]
    return mdno__krpd


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
    qzu__zhwxj = [sanitize_varname(eihmh__qti) for eihmh__qti in col_names]
    pnf__zvgxs = ', '.join(str(iznf__dtcx) for iznf__dtcx, mairf__ebjs in
        enumerate(col_typs) if mairf__ebjs.dtype == types.NPDatetime('ns'))
    wzig__lfjua = ', '.join(["{}='{}'".format(qycp__bdw, bodo.ir.csv_ext.
        _get_dtype_str(mairf__ebjs)) for qycp__bdw, mairf__ebjs in zip(
        qzu__zhwxj, col_typs)])
    rngi__vbdg = ', '.join(["'{}':{}".format(rvx__cku, bodo.ir.csv_ext.
        _get_pd_dtype_str(mairf__ebjs)) for rvx__cku, mairf__ebjs in zip(
        col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    ukfs__yuyl = 'def json_reader_py(fname):\n'
    ukfs__yuyl += '  check_java_installation(fname)\n'
    ukfs__yuyl += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    ukfs__yuyl += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    ukfs__yuyl += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    ukfs__yuyl += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    ukfs__yuyl += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    ukfs__yuyl += "      raise FileNotFoundError('File does not exist')\n"
    ukfs__yuyl += '  with objmode({}):\n'.format(wzig__lfjua)
    ukfs__yuyl += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    ukfs__yuyl += '       convert_dates = {}, \n'.format(convert_dates)
    ukfs__yuyl += '       precise_float={}, \n'.format(precise_float)
    ukfs__yuyl += '       lines={}, \n'.format(lines)
    ukfs__yuyl += '       dtype={{{}}},\n'.format(rngi__vbdg)
    ukfs__yuyl += '       )\n'
    for qycp__bdw, rvx__cku in zip(qzu__zhwxj, col_names):
        ukfs__yuyl += '    if len(df) > 0:\n'
        ukfs__yuyl += "        {} = df['{}'].values\n".format(qycp__bdw,
            rvx__cku)
        ukfs__yuyl += '    else:\n'
        ukfs__yuyl += '        {} = np.array([])\n'.format(qycp__bdw)
    ukfs__yuyl += '  return ({},)\n'.format(', '.join(cvomq__eqju for
        cvomq__eqju in qzu__zhwxj))
    egsjx__ivzgj = globals()
    ctac__zsue = {}
    exec(ukfs__yuyl, egsjx__ivzgj, ctac__zsue)
    grdb__snqt = ctac__zsue['json_reader_py']
    rsdar__hnb = numba.njit(grdb__snqt)
    compiled_funcs.append(rsdar__hnb)
    return rsdar__hnb
