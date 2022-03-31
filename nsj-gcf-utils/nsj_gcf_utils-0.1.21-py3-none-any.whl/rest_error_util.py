from nsj_gcf_utils.exception import ERPException

from typing import List, Union, Tuple


def _format_tuple_error(error: Tuple[str, str]):
    return {
        'code': error[0],
        'message': error[1]
    }


def _format_erpexception_error(error: ERPException):
    return {
        'code': error.mope_code,
        'message': error.message
    }


def _format_list_error(error: Union[List[Tuple[str, str]], List[ERPException]]):
    result = []
    for e in error:
        if isinstance(e, tuple):
            formated = _format_tuple_error(e)
        elif isinstance(e, ERPException):
            formated = _format_erpexception_error(e)
        else:
            formated = _format_unknow_error()

        result.append(formated)

    return result


def _format_unknow_error():
    return {
        'code': None,
        'message': 'Erro desconhecido'
    }


def format_error_body(error: Union[Tuple[str, str], List[Tuple[str, str]], ERPException, List[ERPException]]):
    if isinstance(error, tuple):
        return [_format_tuple_error(error)]
    elif isinstance(error, list):
        return _format_list_error(error)
    elif isinstance(error, ERPException):
        return [_format_erpexception_error(error)]
    else:
        return [_format_unknow_error()]
