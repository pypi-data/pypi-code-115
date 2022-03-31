import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    dse__oxvr = hi - lo
    if dse__oxvr < 2:
        return
    if dse__oxvr < MIN_MERGE:
        iuq__tnb = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + iuq__tnb, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    jtkoa__gzk = minRunLength(dse__oxvr)
    while True:
        ldc__pfauh = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if ldc__pfauh < jtkoa__gzk:
            wkyy__eanz = dse__oxvr if dse__oxvr <= jtkoa__gzk else jtkoa__gzk
            binarySort(key_arrs, lo, lo + wkyy__eanz, lo + ldc__pfauh, data)
            ldc__pfauh = wkyy__eanz
        stackSize = pushRun(stackSize, runBase, runLen, lo, ldc__pfauh)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += ldc__pfauh
        dse__oxvr -= ldc__pfauh
        if dse__oxvr == 0:
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
        xrqh__nkr = getitem_arr_tup(key_arrs, start)
        grmoo__fchxw = getitem_arr_tup(data, start)
        hncpj__iccug = lo
        xfzjo__cqv = start
        assert hncpj__iccug <= xfzjo__cqv
        while hncpj__iccug < xfzjo__cqv:
            zap__mss = hncpj__iccug + xfzjo__cqv >> 1
            if xrqh__nkr < getitem_arr_tup(key_arrs, zap__mss):
                xfzjo__cqv = zap__mss
            else:
                hncpj__iccug = zap__mss + 1
        assert hncpj__iccug == xfzjo__cqv
        n = start - hncpj__iccug
        copyRange_tup(key_arrs, hncpj__iccug, key_arrs, hncpj__iccug + 1, n)
        copyRange_tup(data, hncpj__iccug, data, hncpj__iccug + 1, n)
        setitem_arr_tup(key_arrs, hncpj__iccug, xrqh__nkr)
        setitem_arr_tup(data, hncpj__iccug, grmoo__fchxw)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    atg__vvz = lo + 1
    if atg__vvz == hi:
        return 1
    if getitem_arr_tup(key_arrs, atg__vvz) < getitem_arr_tup(key_arrs, lo):
        atg__vvz += 1
        while atg__vvz < hi and getitem_arr_tup(key_arrs, atg__vvz
            ) < getitem_arr_tup(key_arrs, atg__vvz - 1):
            atg__vvz += 1
        reverseRange(key_arrs, lo, atg__vvz, data)
    else:
        atg__vvz += 1
        while atg__vvz < hi and getitem_arr_tup(key_arrs, atg__vvz
            ) >= getitem_arr_tup(key_arrs, atg__vvz - 1):
            atg__vvz += 1
    return atg__vvz - lo


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
    dzs__ahu = 0
    while n >= MIN_MERGE:
        dzs__ahu |= n & 1
        n >>= 1
    return n + dzs__ahu


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    qkog__ltzo = len(key_arrs[0])
    tmpLength = (qkog__ltzo >> 1 if qkog__ltzo < 2 *
        INITIAL_TMP_STORAGE_LENGTH else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    luot__zynn = (5 if qkog__ltzo < 120 else 10 if qkog__ltzo < 1542 else 
        19 if qkog__ltzo < 119151 else 40)
    runBase = np.empty(luot__zynn, np.int64)
    runLen = np.empty(luot__zynn, np.int64)
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
    kwo__fjpvz = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert kwo__fjpvz >= 0
    base1 += kwo__fjpvz
    len1 -= kwo__fjpvz
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
    rfyf__qpexa = 0
    ybvuh__btdv = 1
    if key > getitem_arr_tup(arr, base + hint):
        xqt__dghpo = _len - hint
        while ybvuh__btdv < xqt__dghpo and key > getitem_arr_tup(arr, base +
            hint + ybvuh__btdv):
            rfyf__qpexa = ybvuh__btdv
            ybvuh__btdv = (ybvuh__btdv << 1) + 1
            if ybvuh__btdv <= 0:
                ybvuh__btdv = xqt__dghpo
        if ybvuh__btdv > xqt__dghpo:
            ybvuh__btdv = xqt__dghpo
        rfyf__qpexa += hint
        ybvuh__btdv += hint
    else:
        xqt__dghpo = hint + 1
        while ybvuh__btdv < xqt__dghpo and key <= getitem_arr_tup(arr, base +
            hint - ybvuh__btdv):
            rfyf__qpexa = ybvuh__btdv
            ybvuh__btdv = (ybvuh__btdv << 1) + 1
            if ybvuh__btdv <= 0:
                ybvuh__btdv = xqt__dghpo
        if ybvuh__btdv > xqt__dghpo:
            ybvuh__btdv = xqt__dghpo
        tmp = rfyf__qpexa
        rfyf__qpexa = hint - ybvuh__btdv
        ybvuh__btdv = hint - tmp
    assert -1 <= rfyf__qpexa and rfyf__qpexa < ybvuh__btdv and ybvuh__btdv <= _len
    rfyf__qpexa += 1
    while rfyf__qpexa < ybvuh__btdv:
        cybe__cgz = rfyf__qpexa + (ybvuh__btdv - rfyf__qpexa >> 1)
        if key > getitem_arr_tup(arr, base + cybe__cgz):
            rfyf__qpexa = cybe__cgz + 1
        else:
            ybvuh__btdv = cybe__cgz
    assert rfyf__qpexa == ybvuh__btdv
    return ybvuh__btdv


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    ybvuh__btdv = 1
    rfyf__qpexa = 0
    if key < getitem_arr_tup(arr, base + hint):
        xqt__dghpo = hint + 1
        while ybvuh__btdv < xqt__dghpo and key < getitem_arr_tup(arr, base +
            hint - ybvuh__btdv):
            rfyf__qpexa = ybvuh__btdv
            ybvuh__btdv = (ybvuh__btdv << 1) + 1
            if ybvuh__btdv <= 0:
                ybvuh__btdv = xqt__dghpo
        if ybvuh__btdv > xqt__dghpo:
            ybvuh__btdv = xqt__dghpo
        tmp = rfyf__qpexa
        rfyf__qpexa = hint - ybvuh__btdv
        ybvuh__btdv = hint - tmp
    else:
        xqt__dghpo = _len - hint
        while ybvuh__btdv < xqt__dghpo and key >= getitem_arr_tup(arr, base +
            hint + ybvuh__btdv):
            rfyf__qpexa = ybvuh__btdv
            ybvuh__btdv = (ybvuh__btdv << 1) + 1
            if ybvuh__btdv <= 0:
                ybvuh__btdv = xqt__dghpo
        if ybvuh__btdv > xqt__dghpo:
            ybvuh__btdv = xqt__dghpo
        rfyf__qpexa += hint
        ybvuh__btdv += hint
    assert -1 <= rfyf__qpexa and rfyf__qpexa < ybvuh__btdv and ybvuh__btdv <= _len
    rfyf__qpexa += 1
    while rfyf__qpexa < ybvuh__btdv:
        cybe__cgz = rfyf__qpexa + (ybvuh__btdv - rfyf__qpexa >> 1)
        if key < getitem_arr_tup(arr, base + cybe__cgz):
            ybvuh__btdv = cybe__cgz
        else:
            rfyf__qpexa = cybe__cgz + 1
    assert rfyf__qpexa == ybvuh__btdv
    return ybvuh__btdv


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
        zxu__kzkzk = 0
        ymi__qlsbx = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                ymi__qlsbx += 1
                zxu__kzkzk = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                zxu__kzkzk += 1
                ymi__qlsbx = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not zxu__kzkzk | ymi__qlsbx < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            zxu__kzkzk = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if zxu__kzkzk != 0:
                copyRange_tup(tmp, cursor1, arr, dest, zxu__kzkzk)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, zxu__kzkzk)
                dest += zxu__kzkzk
                cursor1 += zxu__kzkzk
                len1 -= zxu__kzkzk
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            ymi__qlsbx = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if ymi__qlsbx != 0:
                copyRange_tup(arr, cursor2, arr, dest, ymi__qlsbx)
                copyRange_tup(arr_data, cursor2, arr_data, dest, ymi__qlsbx)
                dest += ymi__qlsbx
                cursor2 += ymi__qlsbx
                len2 -= ymi__qlsbx
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
            if not zxu__kzkzk >= MIN_GALLOP | ymi__qlsbx >= MIN_GALLOP:
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
        zxu__kzkzk = 0
        ymi__qlsbx = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                zxu__kzkzk += 1
                ymi__qlsbx = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                ymi__qlsbx += 1
                zxu__kzkzk = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not zxu__kzkzk | ymi__qlsbx < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            zxu__kzkzk = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if zxu__kzkzk != 0:
                dest -= zxu__kzkzk
                cursor1 -= zxu__kzkzk
                len1 -= zxu__kzkzk
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, zxu__kzkzk)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    zxu__kzkzk)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            ymi__qlsbx = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if ymi__qlsbx != 0:
                dest -= ymi__qlsbx
                cursor2 -= ymi__qlsbx
                len2 -= ymi__qlsbx
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, ymi__qlsbx)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    ymi__qlsbx)
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
            if not zxu__kzkzk >= MIN_GALLOP | ymi__qlsbx >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    tdfh__buknc = len(key_arrs[0])
    if tmpLength < minCapacity:
        ynf__tuyx = minCapacity
        ynf__tuyx |= ynf__tuyx >> 1
        ynf__tuyx |= ynf__tuyx >> 2
        ynf__tuyx |= ynf__tuyx >> 4
        ynf__tuyx |= ynf__tuyx >> 8
        ynf__tuyx |= ynf__tuyx >> 16
        ynf__tuyx += 1
        if ynf__tuyx < 0:
            ynf__tuyx = minCapacity
        else:
            ynf__tuyx = min(ynf__tuyx, tdfh__buknc >> 1)
        tmp = alloc_arr_tup(ynf__tuyx, key_arrs)
        tmp_data = alloc_arr_tup(ynf__tuyx, data)
        tmpLength = ynf__tuyx
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        nosg__veff = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = nosg__veff


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    uvn__vvq = arr_tup.count
    jckwy__hea = 'def f(arr_tup, lo, hi):\n'
    for i in range(uvn__vvq):
        jckwy__hea += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        jckwy__hea += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        jckwy__hea += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    jckwy__hea += '  return\n'
    xtalt__niz = {}
    exec(jckwy__hea, {}, xtalt__niz)
    jbodm__eyxj = xtalt__niz['f']
    return jbodm__eyxj


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    uvn__vvq = src_arr_tup.count
    assert uvn__vvq == dst_arr_tup.count
    jckwy__hea = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(uvn__vvq):
        jckwy__hea += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    jckwy__hea += '  return\n'
    xtalt__niz = {}
    exec(jckwy__hea, {'copyRange': copyRange}, xtalt__niz)
    xvc__bjh = xtalt__niz['f']
    return xvc__bjh


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    uvn__vvq = src_arr_tup.count
    assert uvn__vvq == dst_arr_tup.count
    jckwy__hea = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(uvn__vvq):
        jckwy__hea += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    jckwy__hea += '  return\n'
    xtalt__niz = {}
    exec(jckwy__hea, {'copyElement': copyElement}, xtalt__niz)
    xvc__bjh = xtalt__niz['f']
    return xvc__bjh


def getitem_arr_tup(arr_tup, ind):
    yzt__rgr = [arr[ind] for arr in arr_tup]
    return tuple(yzt__rgr)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    uvn__vvq = arr_tup.count
    jckwy__hea = 'def f(arr_tup, ind):\n'
    jckwy__hea += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(uvn__vvq)]), ',' if uvn__vvq == 1 else '')
    xtalt__niz = {}
    exec(jckwy__hea, {}, xtalt__niz)
    ldlnf__izf = xtalt__niz['f']
    return ldlnf__izf


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, yjpfx__ijoj in zip(arr_tup, val_tup):
        arr[ind] = yjpfx__ijoj


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    uvn__vvq = arr_tup.count
    jckwy__hea = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(uvn__vvq):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            jckwy__hea += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            jckwy__hea += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    jckwy__hea += '  return\n'
    xtalt__niz = {}
    exec(jckwy__hea, {}, xtalt__niz)
    ldlnf__izf = xtalt__niz['f']
    return ldlnf__izf


def test():
    import time
    slpdq__vdig = time.time()
    cbmny__isulf = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((cbmny__isulf,), 0, 3, data)
    print('compile time', time.time() - slpdq__vdig)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    puq__oogi = np.random.ranf(n)
    dntcv__xzpi = pd.DataFrame({'A': puq__oogi, 'B': data[0], 'C': data[1]})
    slpdq__vdig = time.time()
    dyvsw__yehu = dntcv__xzpi.sort_values('A', inplace=False)
    zys__mez = time.time()
    sort((puq__oogi,), 0, n, data)
    print('Bodo', time.time() - zys__mez, 'Numpy', zys__mez - slpdq__vdig)
    np.testing.assert_almost_equal(data[0], dyvsw__yehu.B.values)
    np.testing.assert_almost_equal(data[1], dyvsw__yehu.C.values)


if __name__ == '__main__':
    test()
