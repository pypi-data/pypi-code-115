import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    huhf__ofhh = hi - lo
    if huhf__ofhh < 2:
        return
    if huhf__ofhh < MIN_MERGE:
        pnov__qlut = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + pnov__qlut, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    fzyoa__eafyk = minRunLength(huhf__ofhh)
    while True:
        usgpg__dyct = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if usgpg__dyct < fzyoa__eafyk:
            sak__miw = (huhf__ofhh if huhf__ofhh <= fzyoa__eafyk else
                fzyoa__eafyk)
            binarySort(key_arrs, lo, lo + sak__miw, lo + usgpg__dyct, data)
            usgpg__dyct = sak__miw
        stackSize = pushRun(stackSize, runBase, runLen, lo, usgpg__dyct)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += usgpg__dyct
        huhf__ofhh -= usgpg__dyct
        if huhf__ofhh == 0:
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
        cnuqd__pqir = getitem_arr_tup(key_arrs, start)
        mredl__kptf = getitem_arr_tup(data, start)
        uiitw__yne = lo
        ldi__qcds = start
        assert uiitw__yne <= ldi__qcds
        while uiitw__yne < ldi__qcds:
            ibv__xxh = uiitw__yne + ldi__qcds >> 1
            if cnuqd__pqir < getitem_arr_tup(key_arrs, ibv__xxh):
                ldi__qcds = ibv__xxh
            else:
                uiitw__yne = ibv__xxh + 1
        assert uiitw__yne == ldi__qcds
        n = start - uiitw__yne
        copyRange_tup(key_arrs, uiitw__yne, key_arrs, uiitw__yne + 1, n)
        copyRange_tup(data, uiitw__yne, data, uiitw__yne + 1, n)
        setitem_arr_tup(key_arrs, uiitw__yne, cnuqd__pqir)
        setitem_arr_tup(data, uiitw__yne, mredl__kptf)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    wxcqy__tkteg = lo + 1
    if wxcqy__tkteg == hi:
        return 1
    if getitem_arr_tup(key_arrs, wxcqy__tkteg) < getitem_arr_tup(key_arrs, lo):
        wxcqy__tkteg += 1
        while wxcqy__tkteg < hi and getitem_arr_tup(key_arrs, wxcqy__tkteg
            ) < getitem_arr_tup(key_arrs, wxcqy__tkteg - 1):
            wxcqy__tkteg += 1
        reverseRange(key_arrs, lo, wxcqy__tkteg, data)
    else:
        wxcqy__tkteg += 1
        while wxcqy__tkteg < hi and getitem_arr_tup(key_arrs, wxcqy__tkteg
            ) >= getitem_arr_tup(key_arrs, wxcqy__tkteg - 1):
            wxcqy__tkteg += 1
    return wxcqy__tkteg - lo


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
    coiol__jqn = 0
    while n >= MIN_MERGE:
        coiol__jqn |= n & 1
        n >>= 1
    return n + coiol__jqn


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    bwa__uaujm = len(key_arrs[0])
    tmpLength = (bwa__uaujm >> 1 if bwa__uaujm < 2 *
        INITIAL_TMP_STORAGE_LENGTH else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    kfm__ddwq = (5 if bwa__uaujm < 120 else 10 if bwa__uaujm < 1542 else 19 if
        bwa__uaujm < 119151 else 40)
    runBase = np.empty(kfm__ddwq, np.int64)
    runLen = np.empty(kfm__ddwq, np.int64)
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
    stho__akdgj = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert stho__akdgj >= 0
    base1 += stho__akdgj
    len1 -= stho__akdgj
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
    gsxj__mzvw = 0
    itffk__tad = 1
    if key > getitem_arr_tup(arr, base + hint):
        ayrc__uza = _len - hint
        while itffk__tad < ayrc__uza and key > getitem_arr_tup(arr, base +
            hint + itffk__tad):
            gsxj__mzvw = itffk__tad
            itffk__tad = (itffk__tad << 1) + 1
            if itffk__tad <= 0:
                itffk__tad = ayrc__uza
        if itffk__tad > ayrc__uza:
            itffk__tad = ayrc__uza
        gsxj__mzvw += hint
        itffk__tad += hint
    else:
        ayrc__uza = hint + 1
        while itffk__tad < ayrc__uza and key <= getitem_arr_tup(arr, base +
            hint - itffk__tad):
            gsxj__mzvw = itffk__tad
            itffk__tad = (itffk__tad << 1) + 1
            if itffk__tad <= 0:
                itffk__tad = ayrc__uza
        if itffk__tad > ayrc__uza:
            itffk__tad = ayrc__uza
        tmp = gsxj__mzvw
        gsxj__mzvw = hint - itffk__tad
        itffk__tad = hint - tmp
    assert -1 <= gsxj__mzvw and gsxj__mzvw < itffk__tad and itffk__tad <= _len
    gsxj__mzvw += 1
    while gsxj__mzvw < itffk__tad:
        jfcql__nwk = gsxj__mzvw + (itffk__tad - gsxj__mzvw >> 1)
        if key > getitem_arr_tup(arr, base + jfcql__nwk):
            gsxj__mzvw = jfcql__nwk + 1
        else:
            itffk__tad = jfcql__nwk
    assert gsxj__mzvw == itffk__tad
    return itffk__tad


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    itffk__tad = 1
    gsxj__mzvw = 0
    if key < getitem_arr_tup(arr, base + hint):
        ayrc__uza = hint + 1
        while itffk__tad < ayrc__uza and key < getitem_arr_tup(arr, base +
            hint - itffk__tad):
            gsxj__mzvw = itffk__tad
            itffk__tad = (itffk__tad << 1) + 1
            if itffk__tad <= 0:
                itffk__tad = ayrc__uza
        if itffk__tad > ayrc__uza:
            itffk__tad = ayrc__uza
        tmp = gsxj__mzvw
        gsxj__mzvw = hint - itffk__tad
        itffk__tad = hint - tmp
    else:
        ayrc__uza = _len - hint
        while itffk__tad < ayrc__uza and key >= getitem_arr_tup(arr, base +
            hint + itffk__tad):
            gsxj__mzvw = itffk__tad
            itffk__tad = (itffk__tad << 1) + 1
            if itffk__tad <= 0:
                itffk__tad = ayrc__uza
        if itffk__tad > ayrc__uza:
            itffk__tad = ayrc__uza
        gsxj__mzvw += hint
        itffk__tad += hint
    assert -1 <= gsxj__mzvw and gsxj__mzvw < itffk__tad and itffk__tad <= _len
    gsxj__mzvw += 1
    while gsxj__mzvw < itffk__tad:
        jfcql__nwk = gsxj__mzvw + (itffk__tad - gsxj__mzvw >> 1)
        if key < getitem_arr_tup(arr, base + jfcql__nwk):
            itffk__tad = jfcql__nwk
        else:
            gsxj__mzvw = jfcql__nwk + 1
    assert gsxj__mzvw == itffk__tad
    return itffk__tad


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
        ryue__gmjn = 0
        ekz__dcrcf = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                ekz__dcrcf += 1
                ryue__gmjn = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                ryue__gmjn += 1
                ekz__dcrcf = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not ryue__gmjn | ekz__dcrcf < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            ryue__gmjn = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if ryue__gmjn != 0:
                copyRange_tup(tmp, cursor1, arr, dest, ryue__gmjn)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, ryue__gmjn)
                dest += ryue__gmjn
                cursor1 += ryue__gmjn
                len1 -= ryue__gmjn
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            ekz__dcrcf = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if ekz__dcrcf != 0:
                copyRange_tup(arr, cursor2, arr, dest, ekz__dcrcf)
                copyRange_tup(arr_data, cursor2, arr_data, dest, ekz__dcrcf)
                dest += ekz__dcrcf
                cursor2 += ekz__dcrcf
                len2 -= ekz__dcrcf
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
            if not ryue__gmjn >= MIN_GALLOP | ekz__dcrcf >= MIN_GALLOP:
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
        ryue__gmjn = 0
        ekz__dcrcf = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                ryue__gmjn += 1
                ekz__dcrcf = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                ekz__dcrcf += 1
                ryue__gmjn = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not ryue__gmjn | ekz__dcrcf < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            ryue__gmjn = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if ryue__gmjn != 0:
                dest -= ryue__gmjn
                cursor1 -= ryue__gmjn
                len1 -= ryue__gmjn
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, ryue__gmjn)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    ryue__gmjn)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            ekz__dcrcf = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if ekz__dcrcf != 0:
                dest -= ekz__dcrcf
                cursor2 -= ekz__dcrcf
                len2 -= ekz__dcrcf
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, ekz__dcrcf)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    ekz__dcrcf)
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
            if not ryue__gmjn >= MIN_GALLOP | ekz__dcrcf >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    hvfd__ngatj = len(key_arrs[0])
    if tmpLength < minCapacity:
        avt__gfi = minCapacity
        avt__gfi |= avt__gfi >> 1
        avt__gfi |= avt__gfi >> 2
        avt__gfi |= avt__gfi >> 4
        avt__gfi |= avt__gfi >> 8
        avt__gfi |= avt__gfi >> 16
        avt__gfi += 1
        if avt__gfi < 0:
            avt__gfi = minCapacity
        else:
            avt__gfi = min(avt__gfi, hvfd__ngatj >> 1)
        tmp = alloc_arr_tup(avt__gfi, key_arrs)
        tmp_data = alloc_arr_tup(avt__gfi, data)
        tmpLength = avt__gfi
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        kbwmp__tqi = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = kbwmp__tqi


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    zbz__kuo = arr_tup.count
    yew__sjjw = 'def f(arr_tup, lo, hi):\n'
    for i in range(zbz__kuo):
        yew__sjjw += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        yew__sjjw += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        yew__sjjw += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    yew__sjjw += '  return\n'
    qsx__legwr = {}
    exec(yew__sjjw, {}, qsx__legwr)
    bvlqq__zxeld = qsx__legwr['f']
    return bvlqq__zxeld


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    zbz__kuo = src_arr_tup.count
    assert zbz__kuo == dst_arr_tup.count
    yew__sjjw = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(zbz__kuo):
        yew__sjjw += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    yew__sjjw += '  return\n'
    qsx__legwr = {}
    exec(yew__sjjw, {'copyRange': copyRange}, qsx__legwr)
    gehkd__nri = qsx__legwr['f']
    return gehkd__nri


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    zbz__kuo = src_arr_tup.count
    assert zbz__kuo == dst_arr_tup.count
    yew__sjjw = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(zbz__kuo):
        yew__sjjw += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    yew__sjjw += '  return\n'
    qsx__legwr = {}
    exec(yew__sjjw, {'copyElement': copyElement}, qsx__legwr)
    gehkd__nri = qsx__legwr['f']
    return gehkd__nri


def getitem_arr_tup(arr_tup, ind):
    vfla__evi = [arr[ind] for arr in arr_tup]
    return tuple(vfla__evi)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    zbz__kuo = arr_tup.count
    yew__sjjw = 'def f(arr_tup, ind):\n'
    yew__sjjw += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(zbz__kuo)]), ',' if zbz__kuo == 1 else '')
    qsx__legwr = {}
    exec(yew__sjjw, {}, qsx__legwr)
    ismpz__ctbf = qsx__legwr['f']
    return ismpz__ctbf


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, odtm__mgmo in zip(arr_tup, val_tup):
        arr[ind] = odtm__mgmo


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    zbz__kuo = arr_tup.count
    yew__sjjw = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(zbz__kuo):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            yew__sjjw += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            yew__sjjw += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    yew__sjjw += '  return\n'
    qsx__legwr = {}
    exec(yew__sjjw, {}, qsx__legwr)
    ismpz__ctbf = qsx__legwr['f']
    return ismpz__ctbf


def test():
    import time
    bcj__tkwt = time.time()
    ldwk__hzr = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((ldwk__hzr,), 0, 3, data)
    print('compile time', time.time() - bcj__tkwt)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    kdt__ory = np.random.ranf(n)
    yynrx__vpfyc = pd.DataFrame({'A': kdt__ory, 'B': data[0], 'C': data[1]})
    bcj__tkwt = time.time()
    tmzvn__tlxad = yynrx__vpfyc.sort_values('A', inplace=False)
    talf__ukwjx = time.time()
    sort((kdt__ory,), 0, n, data)
    print('Bodo', time.time() - talf__ukwjx, 'Numpy', talf__ukwjx - bcj__tkwt)
    np.testing.assert_almost_equal(data[0], tmzvn__tlxad.B.values)
    np.testing.assert_almost_equal(data[1], tmzvn__tlxad.C.values)


if __name__ == '__main__':
    test()
