import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    gpdp__rqn = hi - lo
    if gpdp__rqn < 2:
        return
    if gpdp__rqn < MIN_MERGE:
        acrd__ctr = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + acrd__ctr, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    usbk__erma = minRunLength(gpdp__rqn)
    while True:
        pmyh__xats = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if pmyh__xats < usbk__erma:
            acvf__kwzn = gpdp__rqn if gpdp__rqn <= usbk__erma else usbk__erma
            binarySort(key_arrs, lo, lo + acvf__kwzn, lo + pmyh__xats, data)
            pmyh__xats = acvf__kwzn
        stackSize = pushRun(stackSize, runBase, runLen, lo, pmyh__xats)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += pmyh__xats
        gpdp__rqn -= pmyh__xats
        if gpdp__rqn == 0:
            break
    assert lo == hi
    stackSize, tmpLength, tmp, tmp_data, minGallop = mergeForceCollapse(
        stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
        tmp_data, minGallop)
    assert stackSize == 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def binarySort(key_arrs, lo, hi, start, data):
    assert lo <= start and start <= hi
    if start == lo:
        start += 1
    while start < hi:
        kax__xkc = getitem_arr_tup(key_arrs, start)
        ufe__qkwrx = getitem_arr_tup(data, start)
        uzgab__qcaj = lo
        cxtb__rzdxb = start
        assert uzgab__qcaj <= cxtb__rzdxb
        while uzgab__qcaj < cxtb__rzdxb:
            pbpf__rpiwm = uzgab__qcaj + cxtb__rzdxb >> 1
            if kax__xkc < getitem_arr_tup(key_arrs, pbpf__rpiwm):
                cxtb__rzdxb = pbpf__rpiwm
            else:
                uzgab__qcaj = pbpf__rpiwm + 1
        assert uzgab__qcaj == cxtb__rzdxb
        n = start - uzgab__qcaj
        copyRange_tup(key_arrs, uzgab__qcaj, key_arrs, uzgab__qcaj + 1, n)
        copyRange_tup(data, uzgab__qcaj, data, uzgab__qcaj + 1, n)
        setitem_arr_tup(key_arrs, uzgab__qcaj, kax__xkc)
        setitem_arr_tup(data, uzgab__qcaj, ufe__qkwrx)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    xpu__rth = lo + 1
    if xpu__rth == hi:
        return 1
    if getitem_arr_tup(key_arrs, xpu__rth) < getitem_arr_tup(key_arrs, lo):
        xpu__rth += 1
        while xpu__rth < hi and getitem_arr_tup(key_arrs, xpu__rth
            ) < getitem_arr_tup(key_arrs, xpu__rth - 1):
            xpu__rth += 1
        reverseRange(key_arrs, lo, xpu__rth, data)
    else:
        xpu__rth += 1
        while xpu__rth < hi and getitem_arr_tup(key_arrs, xpu__rth
            ) >= getitem_arr_tup(key_arrs, xpu__rth - 1):
            xpu__rth += 1
    return xpu__rth - lo


@numba.njit(no_cpython_wrapper=True, cache=True)
def reverseRange(key_arrs, lo, hi, data):
    hi -= 1
    while lo < hi:
        swap_arrs(key_arrs, lo, hi)
        swap_arrs(data, lo, hi)
        lo += 1
        hi -= 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def minRunLength(n):
    assert n >= 0
    edngs__cvll = 0
    while n >= MIN_MERGE:
        edngs__cvll |= n & 1
        n >>= 1
    return n + edngs__cvll


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    gkga__zdx = len(key_arrs[0])
    tmpLength = (gkga__zdx >> 1 if gkga__zdx < 2 *
        INITIAL_TMP_STORAGE_LENGTH else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    yvgj__nooc = (5 if gkga__zdx < 120 else 10 if gkga__zdx < 1542 else 19 if
        gkga__zdx < 119151 else 40)
    runBase = np.empty(yvgj__nooc, np.int64)
    runLen = np.empty(yvgj__nooc, np.int64)
    return stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def pushRun(stackSize, runBase, runLen, runBase_val, runLen_val):
    runBase[stackSize] = runBase_val
    runLen[stackSize] = runLen_val
    stackSize += 1
    return stackSize


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeCollapse(stackSize, runBase, runLen, key_arrs, data, tmpLength,
    tmp, tmp_data, minGallop):
    while stackSize > 1:
        n = stackSize - 2
        if n >= 1 and runLen[n - 1] <= runLen[n] + runLen[n + 1
            ] or n >= 2 and runLen[n - 2] <= runLen[n] + runLen[n - 1]:
            if runLen[n - 1] < runLen[n + 1]:
                n -= 1
        elif runLen[n] > runLen[n + 1]:
            break
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeAt(stackSize,
            runBase, runLen, key_arrs, data, tmpLength, tmp, tmp_data,
            minGallop, n)
    return stackSize, tmpLength, tmp, tmp_data, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeForceCollapse(stackSize, runBase, runLen, key_arrs, data,
    tmpLength, tmp, tmp_data, minGallop):
    while stackSize > 1:
        n = stackSize - 2
        if n > 0 and runLen[n - 1] < runLen[n + 1]:
            n -= 1
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeAt(stackSize,
            runBase, runLen, key_arrs, data, tmpLength, tmp, tmp_data,
            minGallop, n)
    return stackSize, tmpLength, tmp, tmp_data, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeAt(stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
    tmp_data, minGallop, i):
    assert stackSize >= 2
    assert i >= 0
    assert i == stackSize - 2 or i == stackSize - 3
    base1 = runBase[i]
    len1 = runLen[i]
    base2 = runBase[i + 1]
    len2 = runLen[i + 1]
    assert len1 > 0 and len2 > 0
    assert base1 + len1 == base2
    runLen[i] = len1 + len2
    if i == stackSize - 3:
        runBase[i + 1] = runBase[i + 2]
        runLen[i + 1] = runLen[i + 2]
    stackSize -= 1
    gslx__zcya = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert gslx__zcya >= 0
    base1 += gslx__zcya
    len1 -= gslx__zcya
    if len1 == 0:
        return stackSize, tmpLength, tmp, tmp_data, minGallop
    len2 = gallopLeft(getitem_arr_tup(key_arrs, base1 + len1 - 1), key_arrs,
        base2, len2, len2 - 1)
    assert len2 >= 0
    if len2 == 0:
        return stackSize, tmpLength, tmp, tmp_data, minGallop
    if len1 <= len2:
        tmpLength, tmp, tmp_data = ensureCapacity(tmpLength, tmp, tmp_data,
            key_arrs, data, len1)
        minGallop = mergeLo(key_arrs, data, tmp, tmp_data, minGallop, base1,
            len1, base2, len2)
    else:
        tmpLength, tmp, tmp_data = ensureCapacity(tmpLength, tmp, tmp_data,
            key_arrs, data, len2)
        minGallop = mergeHi(key_arrs, data, tmp, tmp_data, minGallop, base1,
            len1, base2, len2)
    return stackSize, tmpLength, tmp, tmp_data, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopLeft(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    ccvwu__eqkhl = 0
    qbbg__nksep = 1
    if key > getitem_arr_tup(arr, base + hint):
        knmkf__kms = _len - hint
        while qbbg__nksep < knmkf__kms and key > getitem_arr_tup(arr, base +
            hint + qbbg__nksep):
            ccvwu__eqkhl = qbbg__nksep
            qbbg__nksep = (qbbg__nksep << 1) + 1
            if qbbg__nksep <= 0:
                qbbg__nksep = knmkf__kms
        if qbbg__nksep > knmkf__kms:
            qbbg__nksep = knmkf__kms
        ccvwu__eqkhl += hint
        qbbg__nksep += hint
    else:
        knmkf__kms = hint + 1
        while qbbg__nksep < knmkf__kms and key <= getitem_arr_tup(arr, base +
            hint - qbbg__nksep):
            ccvwu__eqkhl = qbbg__nksep
            qbbg__nksep = (qbbg__nksep << 1) + 1
            if qbbg__nksep <= 0:
                qbbg__nksep = knmkf__kms
        if qbbg__nksep > knmkf__kms:
            qbbg__nksep = knmkf__kms
        tmp = ccvwu__eqkhl
        ccvwu__eqkhl = hint - qbbg__nksep
        qbbg__nksep = hint - tmp
    assert -1 <= ccvwu__eqkhl and ccvwu__eqkhl < qbbg__nksep and qbbg__nksep <= _len
    ccvwu__eqkhl += 1
    while ccvwu__eqkhl < qbbg__nksep:
        qzplc__lez = ccvwu__eqkhl + (qbbg__nksep - ccvwu__eqkhl >> 1)
        if key > getitem_arr_tup(arr, base + qzplc__lez):
            ccvwu__eqkhl = qzplc__lez + 1
        else:
            qbbg__nksep = qzplc__lez
    assert ccvwu__eqkhl == qbbg__nksep
    return qbbg__nksep


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    qbbg__nksep = 1
    ccvwu__eqkhl = 0
    if key < getitem_arr_tup(arr, base + hint):
        knmkf__kms = hint + 1
        while qbbg__nksep < knmkf__kms and key < getitem_arr_tup(arr, base +
            hint - qbbg__nksep):
            ccvwu__eqkhl = qbbg__nksep
            qbbg__nksep = (qbbg__nksep << 1) + 1
            if qbbg__nksep <= 0:
                qbbg__nksep = knmkf__kms
        if qbbg__nksep > knmkf__kms:
            qbbg__nksep = knmkf__kms
        tmp = ccvwu__eqkhl
        ccvwu__eqkhl = hint - qbbg__nksep
        qbbg__nksep = hint - tmp
    else:
        knmkf__kms = _len - hint
        while qbbg__nksep < knmkf__kms and key >= getitem_arr_tup(arr, base +
            hint + qbbg__nksep):
            ccvwu__eqkhl = qbbg__nksep
            qbbg__nksep = (qbbg__nksep << 1) + 1
            if qbbg__nksep <= 0:
                qbbg__nksep = knmkf__kms
        if qbbg__nksep > knmkf__kms:
            qbbg__nksep = knmkf__kms
        ccvwu__eqkhl += hint
        qbbg__nksep += hint
    assert -1 <= ccvwu__eqkhl and ccvwu__eqkhl < qbbg__nksep and qbbg__nksep <= _len
    ccvwu__eqkhl += 1
    while ccvwu__eqkhl < qbbg__nksep:
        qzplc__lez = ccvwu__eqkhl + (qbbg__nksep - ccvwu__eqkhl >> 1)
        if key < getitem_arr_tup(arr, base + qzplc__lez):
            qbbg__nksep = qzplc__lez
        else:
            ccvwu__eqkhl = qzplc__lez + 1
    assert ccvwu__eqkhl == qbbg__nksep
    return qbbg__nksep


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeLo(key_arrs, data, tmp, tmp_data, minGallop, base1, len1, base2, len2
    ):
    assert len1 > 0 and len2 > 0 and base1 + len1 == base2
    arr = key_arrs
    arr_data = data
    copyRange_tup(arr, base1, tmp, 0, len1)
    copyRange_tup(arr_data, base1, tmp_data, 0, len1)
    cursor1 = 0
    cursor2 = base2
    dest = base1
    setitem_arr_tup(arr, dest, getitem_arr_tup(arr, cursor2))
    copyElement_tup(arr_data, cursor2, arr_data, dest)
    cursor2 += 1
    dest += 1
    len2 -= 1
    if len2 == 0:
        copyRange_tup(tmp, cursor1, arr, dest, len1)
        copyRange_tup(tmp_data, cursor1, arr_data, dest, len1)
        return minGallop
    if len1 == 1:
        copyRange_tup(arr, cursor2, arr, dest, len2)
        copyRange_tup(arr_data, cursor2, arr_data, dest, len2)
        copyElement_tup(tmp, cursor1, arr, dest + len2)
        copyElement_tup(tmp_data, cursor1, arr_data, dest + len2)
        return minGallop
    len1, len2, cursor1, cursor2, dest, minGallop = mergeLo_inner(key_arrs,
        data, tmp_data, len1, len2, tmp, cursor1, cursor2, dest, minGallop)
    minGallop = 1 if minGallop < 1 else minGallop
    if len1 == 1:
        assert len2 > 0
        copyRange_tup(arr, cursor2, arr, dest, len2)
        copyRange_tup(arr_data, cursor2, arr_data, dest, len2)
        copyElement_tup(tmp, cursor1, arr, dest + len2)
        copyElement_tup(tmp_data, cursor1, arr_data, dest + len2)
    elif len1 == 0:
        raise ValueError('Comparison method violates its general contract!')
    else:
        assert len2 == 0
        assert len1 > 1
        copyRange_tup(tmp, cursor1, arr, dest, len1)
        copyRange_tup(tmp_data, cursor1, arr_data, dest, len1)
    return minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeLo_inner(arr, arr_data, tmp_data, len1, len2, tmp, cursor1,
    cursor2, dest, minGallop):
    while True:
        wmjj__xyiu = 0
        asaaz__hytu = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                asaaz__hytu += 1
                wmjj__xyiu = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                wmjj__xyiu += 1
                asaaz__hytu = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not wmjj__xyiu | asaaz__hytu < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            wmjj__xyiu = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if wmjj__xyiu != 0:
                copyRange_tup(tmp, cursor1, arr, dest, wmjj__xyiu)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, wmjj__xyiu)
                dest += wmjj__xyiu
                cursor1 += wmjj__xyiu
                len1 -= wmjj__xyiu
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            asaaz__hytu = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if asaaz__hytu != 0:
                copyRange_tup(arr, cursor2, arr, dest, asaaz__hytu)
                copyRange_tup(arr_data, cursor2, arr_data, dest, asaaz__hytu)
                dest += asaaz__hytu
                cursor2 += asaaz__hytu
                len2 -= asaaz__hytu
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor1, arr, dest)
            copyElement_tup(tmp_data, cursor1, arr_data, dest)
            cursor1 += 1
            dest += 1
            len1 -= 1
            if len1 == 1:
                return len1, len2, cursor1, cursor2, dest, minGallop
            minGallop -= 1
            if not wmjj__xyiu >= MIN_GALLOP | asaaz__hytu >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeHi(key_arrs, data, tmp, tmp_data, minGallop, base1, len1, base2, len2
    ):
    assert len1 > 0 and len2 > 0 and base1 + len1 == base2
    arr = key_arrs
    arr_data = data
    copyRange_tup(arr, base2, tmp, 0, len2)
    copyRange_tup(arr_data, base2, tmp_data, 0, len2)
    cursor1 = base1 + len1 - 1
    cursor2 = len2 - 1
    dest = base2 + len2 - 1
    copyElement_tup(arr, cursor1, arr, dest)
    copyElement_tup(arr_data, cursor1, arr_data, dest)
    cursor1 -= 1
    dest -= 1
    len1 -= 1
    if len1 == 0:
        copyRange_tup(tmp, 0, arr, dest - (len2 - 1), len2)
        copyRange_tup(tmp_data, 0, arr_data, dest - (len2 - 1), len2)
        return minGallop
    if len2 == 1:
        dest -= len1
        cursor1 -= len1
        copyRange_tup(arr, cursor1 + 1, arr, dest + 1, len1)
        copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1, len1)
        copyElement_tup(tmp, cursor2, arr, dest)
        copyElement_tup(tmp_data, cursor2, arr_data, dest)
        return minGallop
    len1, len2, tmp, cursor1, cursor2, dest, minGallop = mergeHi_inner(key_arrs
        , data, tmp_data, base1, len1, len2, tmp, cursor1, cursor2, dest,
        minGallop)
    minGallop = 1 if minGallop < 1 else minGallop
    if len2 == 1:
        assert len1 > 0
        dest -= len1
        cursor1 -= len1
        copyRange_tup(arr, cursor1 + 1, arr, dest + 1, len1)
        copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1, len1)
        copyElement_tup(tmp, cursor2, arr, dest)
        copyElement_tup(tmp_data, cursor2, arr_data, dest)
    elif len2 == 0:
        raise ValueError('Comparison method violates its general contract!')
    else:
        assert len1 == 0
        assert len2 > 0
        copyRange_tup(tmp, 0, arr, dest - (len2 - 1), len2)
        copyRange_tup(tmp_data, 0, arr_data, dest - (len2 - 1), len2)
    return minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def mergeHi_inner(arr, arr_data, tmp_data, base1, len1, len2, tmp, cursor1,
    cursor2, dest, minGallop):
    while True:
        wmjj__xyiu = 0
        asaaz__hytu = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                wmjj__xyiu += 1
                asaaz__hytu = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                asaaz__hytu += 1
                wmjj__xyiu = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not wmjj__xyiu | asaaz__hytu < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            wmjj__xyiu = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if wmjj__xyiu != 0:
                dest -= wmjj__xyiu
                cursor1 -= wmjj__xyiu
                len1 -= wmjj__xyiu
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, wmjj__xyiu)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    wmjj__xyiu)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            asaaz__hytu = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if asaaz__hytu != 0:
                dest -= asaaz__hytu
                cursor2 -= asaaz__hytu
                len2 -= asaaz__hytu
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, asaaz__hytu)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    asaaz__hytu)
                if len2 <= 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor1, arr, dest)
            copyElement_tup(arr_data, cursor1, arr_data, dest)
            cursor1 -= 1
            dest -= 1
            len1 -= 1
            if len1 == 0:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            minGallop -= 1
            if not wmjj__xyiu >= MIN_GALLOP | asaaz__hytu >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    qtg__ehq = len(key_arrs[0])
    if tmpLength < minCapacity:
        xdo__zlls = minCapacity
        xdo__zlls |= xdo__zlls >> 1
        xdo__zlls |= xdo__zlls >> 2
        xdo__zlls |= xdo__zlls >> 4
        xdo__zlls |= xdo__zlls >> 8
        xdo__zlls |= xdo__zlls >> 16
        xdo__zlls += 1
        if xdo__zlls < 0:
            xdo__zlls = minCapacity
        else:
            xdo__zlls = min(xdo__zlls, qtg__ehq >> 1)
        tmp = alloc_arr_tup(xdo__zlls, key_arrs)
        tmp_data = alloc_arr_tup(xdo__zlls, data)
        tmpLength = xdo__zlls
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        gtfzc__geh = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = gtfzc__geh


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    lbh__scwr = arr_tup.count
    wan__lpzit = 'def f(arr_tup, lo, hi):\n'
    for i in range(lbh__scwr):
        wan__lpzit += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        wan__lpzit += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        wan__lpzit += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    wan__lpzit += '  return\n'
    elt__jkfa = {}
    exec(wan__lpzit, {}, elt__jkfa)
    spyiz__gdv = elt__jkfa['f']
    return spyiz__gdv


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    lbh__scwr = src_arr_tup.count
    assert lbh__scwr == dst_arr_tup.count
    wan__lpzit = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(lbh__scwr):
        wan__lpzit += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    wan__lpzit += '  return\n'
    elt__jkfa = {}
    exec(wan__lpzit, {'copyRange': copyRange}, elt__jkfa)
    bzz__nlb = elt__jkfa['f']
    return bzz__nlb


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    lbh__scwr = src_arr_tup.count
    assert lbh__scwr == dst_arr_tup.count
    wan__lpzit = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(lbh__scwr):
        wan__lpzit += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    wan__lpzit += '  return\n'
    elt__jkfa = {}
    exec(wan__lpzit, {'copyElement': copyElement}, elt__jkfa)
    bzz__nlb = elt__jkfa['f']
    return bzz__nlb


def getitem_arr_tup(arr_tup, ind):
    oqzu__ugs = [arr[ind] for arr in arr_tup]
    return tuple(oqzu__ugs)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    lbh__scwr = arr_tup.count
    wan__lpzit = 'def f(arr_tup, ind):\n'
    wan__lpzit += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(lbh__scwr)]), ',' if lbh__scwr == 1 else '')
    elt__jkfa = {}
    exec(wan__lpzit, {}, elt__jkfa)
    grur__sktgf = elt__jkfa['f']
    return grur__sktgf


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, xno__abeq in zip(arr_tup, val_tup):
        arr[ind] = xno__abeq


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    lbh__scwr = arr_tup.count
    wan__lpzit = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(lbh__scwr):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            wan__lpzit += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            wan__lpzit += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    wan__lpzit += '  return\n'
    elt__jkfa = {}
    exec(wan__lpzit, {}, elt__jkfa)
    grur__sktgf = elt__jkfa['f']
    return grur__sktgf


def test():
    import time
    tphj__mekje = time.time()
    uli__umpzg = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((uli__umpzg,), 0, 3, data)
    print('compile time', time.time() - tphj__mekje)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    whbri__egqdr = np.random.ranf(n)
    puo__lgzqw = pd.DataFrame({'A': whbri__egqdr, 'B': data[0], 'C': data[1]})
    tphj__mekje = time.time()
    zym__bjj = puo__lgzqw.sort_values('A', inplace=False)
    qbd__jkgkf = time.time()
    sort((whbri__egqdr,), 0, n, data)
    print('Bodo', time.time() - qbd__jkgkf, 'Numpy', qbd__jkgkf - tphj__mekje)
    np.testing.assert_almost_equal(data[0], zym__bjj.B.values)
    np.testing.assert_almost_equal(data[1], zym__bjj.C.values)


if __name__ == '__main__':
    test()
