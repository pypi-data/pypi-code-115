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
    pzah__qdj = []
    qgj__jav = []
    xzjf__zdxk = []
    for epntm__docah, vtwhf__bpzp in enumerate(json_node.out_vars):
        if vtwhf__bpzp.name in lives:
            pzah__qdj.append(json_node.df_colnames[epntm__docah])
            qgj__jav.append(json_node.out_vars[epntm__docah])
            xzjf__zdxk.append(json_node.out_types[epntm__docah])
    json_node.df_colnames = pzah__qdj
    json_node.out_vars = qgj__jav
    json_node.out_types = xzjf__zdxk
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        alca__xcqgu = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        qmu__ioas = json_node.loc.strformat()
        nwojh__lbmrg = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', alca__xcqgu,
            qmu__ioas, nwojh__lbmrg)
        ygjbc__rck = [unyh__gzj for epntm__docah, unyh__gzj in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            epntm__docah], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if ygjbc__rck:
            jznc__xuxrb = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding',
                jznc__xuxrb, qmu__ioas, ygjbc__rck)
    parallel = False
    if array_dists is not None:
        parallel = True
        for qzuq__zlelj in json_node.out_vars:
            if array_dists[qzuq__zlelj.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                qzuq__zlelj.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    prfqx__legr = len(json_node.out_vars)
    nrgj__zgn = ', '.join('arr' + str(epntm__docah) for epntm__docah in
        range(prfqx__legr))
    lrmb__fuok = 'def json_impl(fname):\n'
    lrmb__fuok += '    ({},) = _json_reader_py(fname)\n'.format(nrgj__zgn)
    orp__iazh = {}
    exec(lrmb__fuok, {}, orp__iazh)
    xkytf__urn = orp__iazh['json_impl']
    edg__yeup = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    jelf__gaotb = compile_to_numba_ir(xkytf__urn, {'_json_reader_py':
        edg__yeup}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type,), typemap=typemap, calltypes=calltypes).blocks.popitem()[1
        ]
    replace_arg_nodes(jelf__gaotb, [json_node.file_name])
    idzgt__uqy = jelf__gaotb.body[:-3]
    for epntm__docah in range(len(json_node.out_vars)):
        idzgt__uqy[-len(json_node.out_vars) + epntm__docah
            ].target = json_node.out_vars[epntm__docah]
    return idzgt__uqy


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
    ouw__kzzl = [sanitize_varname(unyh__gzj) for unyh__gzj in col_names]
    mow__slgu = ', '.join(str(epntm__docah) for epntm__docah, dmczo__ufim in
        enumerate(col_typs) if dmczo__ufim.dtype == types.NPDatetime('ns'))
    sdmw__avbss = ', '.join(["{}='{}'".format(qktjh__gphno, bodo.ir.csv_ext
        ._get_dtype_str(dmczo__ufim)) for qktjh__gphno, dmczo__ufim in zip(
        ouw__kzzl, col_typs)])
    vrep__pjrgo = ', '.join(["'{}':{}".format(cwxu__mdkyo, bodo.ir.csv_ext.
        _get_pd_dtype_str(dmczo__ufim)) for cwxu__mdkyo, dmczo__ufim in zip
        (col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    lrmb__fuok = 'def json_reader_py(fname):\n'
    lrmb__fuok += '  check_java_installation(fname)\n'
    lrmb__fuok += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    lrmb__fuok += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    lrmb__fuok += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    lrmb__fuok += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    lrmb__fuok += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    lrmb__fuok += "      raise FileNotFoundError('File does not exist')\n"
    lrmb__fuok += '  with objmode({}):\n'.format(sdmw__avbss)
    lrmb__fuok += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    lrmb__fuok += '       convert_dates = {}, \n'.format(convert_dates)
    lrmb__fuok += '       precise_float={}, \n'.format(precise_float)
    lrmb__fuok += '       lines={}, \n'.format(lines)
    lrmb__fuok += '       dtype={{{}}},\n'.format(vrep__pjrgo)
    lrmb__fuok += '       )\n'
    for qktjh__gphno, cwxu__mdkyo in zip(ouw__kzzl, col_names):
        lrmb__fuok += '    if len(df) > 0:\n'
        lrmb__fuok += "        {} = df['{}'].values\n".format(qktjh__gphno,
            cwxu__mdkyo)
        lrmb__fuok += '    else:\n'
        lrmb__fuok += '        {} = np.array([])\n'.format(qktjh__gphno)
    lrmb__fuok += '  return ({},)\n'.format(', '.join(irxo__jnc for
        irxo__jnc in ouw__kzzl))
    udk__amw = globals()
    orp__iazh = {}
    exec(lrmb__fuok, udk__amw, orp__iazh)
    edg__yeup = orp__iazh['json_reader_py']
    evsjn__dozqi = numba.njit(edg__yeup)
    compiled_funcs.append(evsjn__dozqi)
    return evsjn__dozqi
