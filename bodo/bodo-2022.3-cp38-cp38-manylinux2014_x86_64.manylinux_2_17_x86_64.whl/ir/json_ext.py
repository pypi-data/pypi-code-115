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
    ipck__vxvqh = []
    jbd__thywf = []
    ppu__gbxav = []
    for nhilf__vmidm, qiqm__jdkrx in enumerate(json_node.out_vars):
        if qiqm__jdkrx.name in lives:
            ipck__vxvqh.append(json_node.df_colnames[nhilf__vmidm])
            jbd__thywf.append(json_node.out_vars[nhilf__vmidm])
            ppu__gbxav.append(json_node.out_types[nhilf__vmidm])
    json_node.df_colnames = ipck__vxvqh
    json_node.out_vars = jbd__thywf
    json_node.out_types = ppu__gbxav
    if len(json_node.out_vars) == 0:
        return None
    return json_node


def json_distributed_run(json_node, array_dists, typemap, calltypes,
    typingctx, targetctx):
    if bodo.user_logging.get_verbose_level() >= 1:
        vggvy__qugn = (
            'Finish column pruning on read_json node:\n%s\nColumns loaded %s\n'
            )
        sfd__ouot = json_node.loc.strformat()
        acuo__eylai = json_node.df_colnames
        bodo.user_logging.log_message('Column Pruning', vggvy__qugn,
            sfd__ouot, acuo__eylai)
        uid__iivi = [vacou__nma for nhilf__vmidm, vacou__nma in enumerate(
            json_node.df_colnames) if isinstance(json_node.out_types[
            nhilf__vmidm], bodo.libs.dict_arr_ext.DictionaryArrayType)]
        if uid__iivi:
            crv__lhzr = """Finished optimized encoding on read_json node:
%s
Columns %s using dictionary encoding to reduce memory usage.
"""
            bodo.user_logging.log_message('Dictionary Encoding', crv__lhzr,
                sfd__ouot, uid__iivi)
    parallel = False
    if array_dists is not None:
        parallel = True
        for aoru__nvi in json_node.out_vars:
            if array_dists[aoru__nvi.name
                ] != distributed_pass.Distribution.OneD and array_dists[
                aoru__nvi.name] != distributed_pass.Distribution.OneD_Var:
                parallel = False
    aof__ansoh = len(json_node.out_vars)
    vdwe__ycsej = ', '.join('arr' + str(nhilf__vmidm) for nhilf__vmidm in
        range(aof__ansoh))
    ervl__kprpk = 'def json_impl(fname):\n'
    ervl__kprpk += '    ({},) = _json_reader_py(fname)\n'.format(vdwe__ycsej)
    slfvr__nxc = {}
    exec(ervl__kprpk, {}, slfvr__nxc)
    xqeqj__fra = slfvr__nxc['json_impl']
    qnowo__gnu = _gen_json_reader_py(json_node.df_colnames, json_node.
        out_types, typingctx, targetctx, parallel, json_node.orient,
        json_node.convert_dates, json_node.precise_float, json_node.lines,
        json_node.compression)
    uwmq__vqgjc = compile_to_numba_ir(xqeqj__fra, {'_json_reader_py':
        qnowo__gnu}, typingctx=typingctx, targetctx=targetctx, arg_typs=(
        string_type,), typemap=typemap, calltypes=calltypes).blocks.popitem()[1
        ]
    replace_arg_nodes(uwmq__vqgjc, [json_node.file_name])
    jkfb__rbamm = uwmq__vqgjc.body[:-3]
    for nhilf__vmidm in range(len(json_node.out_vars)):
        jkfb__rbamm[-len(json_node.out_vars) + nhilf__vmidm
            ].target = json_node.out_vars[nhilf__vmidm]
    return jkfb__rbamm


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
    bkzmt__mwffp = [sanitize_varname(vacou__nma) for vacou__nma in col_names]
    qgwmw__klch = ', '.join(str(nhilf__vmidm) for nhilf__vmidm, hib__zziey in
        enumerate(col_typs) if hib__zziey.dtype == types.NPDatetime('ns'))
    cajl__pzprj = ', '.join(["{}='{}'".format(hhjsn__dfhqe, bodo.ir.csv_ext
        ._get_dtype_str(hib__zziey)) for hhjsn__dfhqe, hib__zziey in zip(
        bkzmt__mwffp, col_typs)])
    uzzq__phlw = ', '.join(["'{}':{}".format(jzux__eni, bodo.ir.csv_ext.
        _get_pd_dtype_str(hib__zziey)) for jzux__eni, hib__zziey in zip(
        col_names, col_typs)])
    if compression is None:
        compression = 'uncompressed'
    ervl__kprpk = 'def json_reader_py(fname):\n'
    ervl__kprpk += '  check_java_installation(fname)\n'
    ervl__kprpk += f"""  bucket_region = bodo.io.fs_io.get_s3_bucket_region_njit(fname, parallel={parallel})
"""
    ervl__kprpk += (
        '  f_reader = bodo.ir.json_ext.json_file_chunk_reader(bodo.libs.str_ext.unicode_to_utf8(fname), '
        )
    ervl__kprpk += (
        """    {}, {}, -1, bodo.libs.str_ext.unicode_to_utf8('{}'), bodo.libs.str_ext.unicode_to_utf8(bucket_region) )
"""
        .format(lines, parallel, compression))
    ervl__kprpk += '  bodo.utils.utils.check_and_propagate_cpp_exception()\n'
    ervl__kprpk += '  if bodo.utils.utils.is_null_pointer(f_reader):\n'
    ervl__kprpk += "      raise FileNotFoundError('File does not exist')\n"
    ervl__kprpk += '  with objmode({}):\n'.format(cajl__pzprj)
    ervl__kprpk += "    df = pd.read_json(f_reader, orient='{}',\n".format(
        orient)
    ervl__kprpk += '       convert_dates = {}, \n'.format(convert_dates)
    ervl__kprpk += '       precise_float={}, \n'.format(precise_float)
    ervl__kprpk += '       lines={}, \n'.format(lines)
    ervl__kprpk += '       dtype={{{}}},\n'.format(uzzq__phlw)
    ervl__kprpk += '       )\n'
    for hhjsn__dfhqe, jzux__eni in zip(bkzmt__mwffp, col_names):
        ervl__kprpk += '    if len(df) > 0:\n'
        ervl__kprpk += "        {} = df['{}'].values\n".format(hhjsn__dfhqe,
            jzux__eni)
        ervl__kprpk += '    else:\n'
        ervl__kprpk += '        {} = np.array([])\n'.format(hhjsn__dfhqe)
    ervl__kprpk += '  return ({},)\n'.format(', '.join(zjiok__rxy for
        zjiok__rxy in bkzmt__mwffp))
    qjj__mlyz = globals()
    slfvr__nxc = {}
    exec(ervl__kprpk, qjj__mlyz, slfvr__nxc)
    qnowo__gnu = slfvr__nxc['json_reader_py']
    qbxdh__iqtr = numba.njit(qnowo__gnu)
    compiled_funcs.append(qbxdh__iqtr)
    return qbxdh__iqtr
