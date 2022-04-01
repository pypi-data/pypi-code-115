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
    ype__vsu = []
    zclv__vajto = []
    bggg__qnvdp = []
    for uabh__jgybj, itgn__yflo in enumerate(json_node.out_vars):
        if itgn__yflo.name in lives:
            ype__vsu.append(json_node.df_colnames[uabh__jgybj])
            zclv__vajto.append(json_node.out_vars[uabh__jgybj])
            bggg__qnvdp.append(json_node.out_types[uabh__jgybj])
    json_node.df_colnames = ype__vsu
    json_node.out_vars = zclv__vajto
    json_node.out_types = bggg__qnvdp
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        cyjdl__zuk = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        rqdiq__kys = json_node.loc.strformat()
        mvi__mfb = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', cyjdl__zuk,
            rqdiq__kys, mvi__mfb)
        fguq__ttgn = [wpj__pfpd for uabh__jgybj, wpj__pfpd in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            uabh__jgybj], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if fguq__ttgn:
            hzi__ehwb = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', hzi__ehwb,
                rqdiq__kys, fguq__ttgn)
    parallel = False
    if array_dists is not None:
        parallel = True
        for zwei__ssam in json_node.out_vars:
            if array_dists[zwei__ssam.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                zwei__ssam.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    bynu__tsvio = len(json_node.out_vars)
    hdkn__fuef = ', '.join('arr' + str(uabh__jgybj) for uabh__jgybj in
        range(bynu__tsvio))
    wsvec__gkcix = 'def json_impl(fname):\n'
    wsvec__gkcix += '    ({},) = _json_reader_py(fname)\n'.format(hdkn__fuef)
    eqmh__eeyig = {}
    exec(wsvec__gkcix, {}, eqmh__eeyig)
    ckbn__dfgqm = eqmh__eeyig['json_impl']
    qblgw__zdwq = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    foz__pxjf = compile_to_numba_ir(ckbn__dfgqm, {'_json_reader_py':
        qblgw__zdwq}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type,), typemap=typemap, calltypes=calltypes).blocks.popitem()[1
        ]
    replace_arg_nodes(foz__pxjf, [json_node.file_name])
    nnvv__valpj = foz__pxjf.body[:-3]
    for uabh__jgybj in range(len(json_node.out_vars)):
        nnvv__valpj[-len(json_node.out_vars) + uabh__jgybj
            ].target = json_node.out_vars[uabh__jgybj]
    return nnvv__valpj


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
    jrrwh__unk = [sanitize_varname(wpj__pfpd) for wpj__pfpd in col_names]
    eabv__xhb = ', '.join(str(uabh__jgybj) for uabh__jgybj, hsie__tmn in
        enumerate(col_typs) if hsie__tmn.dtype == types.NPDatetime('ns'))
    mhmxg__fmu = ', '.join(["{}='{}'".format(wvrap__hzjaw, bodo.ir.csv_ext.
        _get_dtype_str(hsie__tmn)) for wvrap__hzjaw, hsie__tmn in zip(
        jrrwh__unk, col_typs)])
    jcrp__vmqv = ', '.join(["'{}':{}".format(ysf__ohnxj, bodo.ir.csv_ext.
        _get_pd_dtype_str(hsie__tmn)) for ysf__ohnxj, hsie__tmn in zip(
        col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    wsvec__gkcix = 'def json_reader_py(fname):\n'
    wsvec__gkcix += '  check_java_installation(fname)\n'
    wsvec__gkcix += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    wsvec__gkcix += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    wsvec__gkcix += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    wsvec__gkcix += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    wsvec__gkcix += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    wsvec__gkcix += "      raise FileNotFoundError('File does not exist')\n"
    wsvec__gkcix += '  with objmode({}):\n'.format(mhmxg__fmu)
    wsvec__gkcix += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    wsvec__gkcix += '       convert_dates = {}, \n'.format(convert_dates)
    wsvec__gkcix += '       precise_float={}, \n'.format(precise_float)
    wsvec__gkcix += '       lines={}, \n'.format(lines)
    wsvec__gkcix += '       dtype={{{}}},\n'.format(jcrp__vmqv)
    wsvec__gkcix += '       )\n'
    for wvrap__hzjaw, ysf__ohnxj in zip(jrrwh__unk, col_names):
        wsvec__gkcix += '    if len(df) > 0:\n'
        wsvec__gkcix += "        {} = df['{}'].values\n".format(wvrap__hzjaw,
            ysf__ohnxj)
        wsvec__gkcix += '    else:\n'
        wsvec__gkcix += '        {} = np.array([])\n'.format(wvrap__hzjaw)
    wsvec__gkcix += '  return ({},)\n'.format(', '.join(knza__mxhr for
        knza__mxhr in jrrwh__unk))
    cegfw__jaea = globals()
    eqmh__eeyig = {}
    exec(wsvec__gkcix, cegfw__jaea, eqmh__eeyig)
    qblgw__zdwq = eqmh__eeyig['json_reader_py']
    twezw__iyf = numba.njit(qblgw__zdwq)
    compiled_funcs.append(twezw__iyf)
    return twezw__iyf
