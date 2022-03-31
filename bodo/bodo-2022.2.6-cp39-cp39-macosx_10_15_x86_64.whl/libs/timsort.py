import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    tcr__ixuj = hi - lo
    if tcr__ixuj < 2:
        return
    if tcr__ixuj < MIN_MERGE:
        yfb__vwhc = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + yfb__vwhc, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    fvme__juf = minRunLength(tcr__ixuj)
    while True:
        ftbhy__nytrq = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if ftbhy__nytrq < fvme__juf:
            qqa__eskj = tcr__ixuj if tcr__ixuj <= fvme__juf else fvme__juf
            binarySort(key_arrs, lo, lo + qqa__eskj, lo + ftbhy__nytrq, data)
            ftbhy__nytrq = qqa__eskj
        stackSize = pushRun(stackSize, runBase, runLen, lo, ftbhy__nytrq)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += ftbhy__nytrq
        tcr__ixuj -= ftbhy__nytrq
        if tcr__ixuj == 0:
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
        dcg__mstlo = getitem_arr_tup(key_arrs, start)
        rdpfr__aoz = getitem_arr_tup(data, start)
        ttd__dlhg = lo
        wlmqr__bghj = start
        assert ttd__dlhg <= wlmqr__bghj
        while ttd__dlhg < wlmqr__bghj:
            zqfig__nen = ttd__dlhg + wlmqr__bghj >> 1
            if dcg__mstlo < getitem_arr_tup(key_arrs, zqfig__nen):
                wlmqr__bghj = zqfig__nen
            else:
                ttd__dlhg = zqfig__nen + 1
        assert ttd__dlhg == wlmqr__bghj
        n = start - ttd__dlhg
        copyRange_tup(key_arrs, ttd__dlhg, key_arrs, ttd__dlhg + 1, n)
        copyRange_tup(data, ttd__dlhg, data, ttd__dlhg + 1, n)
        setitem_arr_tup(key_arrs, ttd__dlhg, dcg__mstlo)
        setitem_arr_tup(data, ttd__dlhg, rdpfr__aoz)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    xrxq__xjsn = lo + 1
    if xrxq__xjsn == hi:
        return 1
    if getitem_arr_tup(key_arrs, xrxq__xjsn) < getitem_arr_tup(key_arrs, lo):
        xrxq__xjsn += 1
        while xrxq__xjsn < hi and getitem_arr_tup(key_arrs, xrxq__xjsn
            ) < getitem_arr_tup(key_arrs, xrxq__xjsn - 1):
            xrxq__xjsn += 1
        reverseRange(key_arrs, lo, xrxq__xjsn, data)
    else:
        xrxq__xjsn += 1
        while xrxq__xjsn < hi and getitem_arr_tup(key_arrs, xrxq__xjsn
            ) >= getitem_arr_tup(key_arrs, xrxq__xjsn - 1):
            xrxq__xjsn += 1
    return xrxq__xjsn - lo


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
    huztq__qxp = 0
    while n >= MIN_MERGE:
        huztq__qxp |= n & 1
        n >>= 1
    return n + huztq__qxp


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    gme__mqg = len(key_arrs[0])
    tmpLength = (gme__mqg >> 1 if gme__mqg < 2 * INITIAL_TMP_STORAGE_LENGTH
         else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    uuus__rfpak = (5 if gme__mqg < 120 else 10 if gme__mqg < 1542 else 19 if
        gme__mqg < 119151 else 40)
    runBase = np.empty(uuus__rfpak, np.int64)
    runLen = np.empty(uuus__rfpak, np.int64)
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
    zgirb__bvfx = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert zgirb__bvfx >= 0
    base1 += zgirb__bvfx
    len1 -= zgirb__bvfx
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
    mfbb__akzk = 0
    dlbj__gptjq = 1
    if key > getitem_arr_tup(arr, base + hint):
        ipor__wmekq = _len - hint
        while dlbj__gptjq < ipor__wmekq and key > getitem_arr_tup(arr, base +
            hint + dlbj__gptjq):
            mfbb__akzk = dlbj__gptjq
            dlbj__gptjq = (dlbj__gptjq << 1) + 1
            if dlbj__gptjq <= 0:
                dlbj__gptjq = ipor__wmekq
        if dlbj__gptjq > ipor__wmekq:
            dlbj__gptjq = ipor__wmekq
        mfbb__akzk += hint
        dlbj__gptjq += hint
    else:
        ipor__wmekq = hint + 1
        while dlbj__gptjq < ipor__wmekq and key <= getitem_arr_tup(arr, 
            base + hint - dlbj__gptjq):
            mfbb__akzk = dlbj__gptjq
            dlbj__gptjq = (dlbj__gptjq << 1) + 1
            if dlbj__gptjq <= 0:
                dlbj__gptjq = ipor__wmekq
        if dlbj__gptjq > ipor__wmekq:
            dlbj__gptjq = ipor__wmekq
        tmp = mfbb__akzk
        mfbb__akzk = hint - dlbj__gptjq
        dlbj__gptjq = hint - tmp
    assert -1 <= mfbb__akzk and mfbb__akzk < dlbj__gptjq and dlbj__gptjq <= _len
    mfbb__akzk += 1
    while mfbb__akzk < dlbj__gptjq:
        qar__gkmq = mfbb__akzk + (dlbj__gptjq - mfbb__akzk >> 1)
        if key > getitem_arr_tup(arr, base + qar__gkmq):
            mfbb__akzk = qar__gkmq + 1
        else:
            dlbj__gptjq = qar__gkmq
    assert mfbb__akzk == dlbj__gptjq
    return dlbj__gptjq


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    dlbj__gptjq = 1
    mfbb__akzk = 0
    if key < getitem_arr_tup(arr, base + hint):
        ipor__wmekq = hint + 1
        while dlbj__gptjq < ipor__wmekq and key < getitem_arr_tup(arr, base +
            hint - dlbj__gptjq):
            mfbb__akzk = dlbj__gptjq
            dlbj__gptjq = (dlbj__gptjq << 1) + 1
            if dlbj__gptjq <= 0:
                dlbj__gptjq = ipor__wmekq
        if dlbj__gptjq > ipor__wmekq:
            dlbj__gptjq = ipor__wmekq
        tmp = mfbb__akzk
        mfbb__akzk = hint - dlbj__gptjq
        dlbj__gptjq = hint - tmp
    else:
        ipor__wmekq = _len - hint
        while dlbj__gptjq < ipor__wmekq and key >= getitem_arr_tup(arr, 
            base + hint + dlbj__gptjq):
            mfbb__akzk = dlbj__gptjq
            dlbj__gptjq = (dlbj__gptjq << 1) + 1
            if dlbj__gptjq <= 0:
                dlbj__gptjq = ipor__wmekq
        if dlbj__gptjq > ipor__wmekq:
            dlbj__gptjq = ipor__wmekq
        mfbb__akzk += hint
        dlbj__gptjq += hint
    assert -1 <= mfbb__akzk and mfbb__akzk < dlbj__gptjq and dlbj__gptjq <= _len
    mfbb__akzk += 1
    while mfbb__akzk < dlbj__gptjq:
        qar__gkmq = mfbb__akzk + (dlbj__gptjq - mfbb__akzk >> 1)
        if key < getitem_arr_tup(arr, base + qar__gkmq):
            dlbj__gptjq = qar__gkmq
        else:
            mfbb__akzk = qar__gkmq + 1
    assert mfbb__akzk == dlbj__gptjq
    return dlbj__gptjq


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
        uqhl__fwkzr = 0
        fbkpi__kxdh = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                fbkpi__kxdh += 1
                uqhl__fwkzr = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                uqhl__fwkzr += 1
                fbkpi__kxdh = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not uqhl__fwkzr | fbkpi__kxdh < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            uqhl__fwkzr = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if uqhl__fwkzr != 0:
                copyRange_tup(tmp, cursor1, arr, dest, uqhl__fwkzr)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, uqhl__fwkzr)
                dest += uqhl__fwkzr
                cursor1 += uqhl__fwkzr
                len1 -= uqhl__fwkzr
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            fbkpi__kxdh = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if fbkpi__kxdh != 0:
                copyRange_tup(arr, cursor2, arr, dest, fbkpi__kxdh)
                copyRange_tup(arr_data, cursor2, arr_data, dest, fbkpi__kxdh)
                dest += fbkpi__kxdh
                cursor2 += fbkpi__kxdh
                len2 -= fbkpi__kxdh
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
            if not uqhl__fwkzr >= MIN_GALLOP | fbkpi__kxdh >= MIN_GALLOP:
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
        uqhl__fwkzr = 0
        fbkpi__kxdh = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                uqhl__fwkzr += 1
                fbkpi__kxdh = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                fbkpi__kxdh += 1
                uqhl__fwkzr = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not uqhl__fwkzr | fbkpi__kxdh < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            uqhl__fwkzr = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if uqhl__fwkzr != 0:
                dest -= uqhl__fwkzr
                cursor1 -= uqhl__fwkzr
                len1 -= uqhl__fwkzr
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, uqhl__fwkzr)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    uqhl__fwkzr)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            fbkpi__kxdh = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if fbkpi__kxdh != 0:
                dest -= fbkpi__kxdh
                cursor2 -= fbkpi__kxdh
                len2 -= fbkpi__kxdh
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, fbkpi__kxdh)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    fbkpi__kxdh)
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
            if not uqhl__fwkzr >= MIN_GALLOP | fbkpi__kxdh >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    wrr__tcvki = len(key_arrs[0])
    if tmpLength < minCapacity:
        vxnk__ssone = minCapacity
        vxnk__ssone |= vxnk__ssone >> 1
        vxnk__ssone |= vxnk__ssone >> 2
        vxnk__ssone |= vxnk__ssone >> 4
        vxnk__ssone |= vxnk__ssone >> 8
        vxnk__ssone |= vxnk__ssone >> 16
        vxnk__ssone += 1
        if vxnk__ssone < 0:
            vxnk__ssone = minCapacity
        else:
            vxnk__ssone = min(vxnk__ssone, wrr__tcvki >> 1)
        tmp = alloc_arr_tup(vxnk__ssone, key_arrs)
        tmp_data = alloc_arr_tup(vxnk__ssone, data)
        tmpLength = vxnk__ssone
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        okq__ilhlu = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = okq__ilhlu


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    wnwwi__cgw = arr_tup.count
    utq__siizz = 'def f(arr_tup, lo, hi):\n'
    for i in range(wnwwi__cgw):
        utq__siizz += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        utq__siizz += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        utq__siizz += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    utq__siizz += '  return\n'
    cvteb__nxyxw = {}
    exec(utq__siizz, {}, cvteb__nxyxw)
    fzb__eaphm = cvteb__nxyxw['f']
    return fzb__eaphm


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    wnwwi__cgw = src_arr_tup.count
    assert wnwwi__cgw == dst_arr_tup.count
    utq__siizz = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(wnwwi__cgw):
        utq__siizz += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    utq__siizz += '  return\n'
    cvteb__nxyxw = {}
    exec(utq__siizz, {'copyRange': copyRange}, cvteb__nxyxw)
    klknl__fhcob = cvteb__nxyxw['f']
    return klknl__fhcob


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    wnwwi__cgw = src_arr_tup.count
    assert wnwwi__cgw == dst_arr_tup.count
    utq__siizz = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(wnwwi__cgw):
        utq__siizz += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    utq__siizz += '  return\n'
    cvteb__nxyxw = {}
    exec(utq__siizz, {'copyElement': copyElement}, cvteb__nxyxw)
    klknl__fhcob = cvteb__nxyxw['f']
    return klknl__fhcob


def getitem_arr_tup(arr_tup, ind):
    oumma__tjk = [arr[ind] for arr in arr_tup]
    return tuple(oumma__tjk)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    wnwwi__cgw = arr_tup.count
    utq__siizz = 'def f(arr_tup, ind):\n'
    utq__siizz += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(wnwwi__cgw)]), ',' if wnwwi__cgw == 1 else '')
    cvteb__nxyxw = {}
    exec(utq__siizz, {}, cvteb__nxyxw)
    jdezm__rzeti = cvteb__nxyxw['f']
    return jdezm__rzeti


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, yyz__rpgq in zip(arr_tup, val_tup):
        arr[ind] = yyz__rpgq


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    wnwwi__cgw = arr_tup.count
    utq__siizz = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(wnwwi__cgw):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            utq__siizz += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            utq__siizz += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    utq__siizz += '  return\n'
    cvteb__nxyxw = {}
    exec(utq__siizz, {}, cvteb__nxyxw)
    jdezm__rzeti = cvteb__nxyxw['f']
    return jdezm__rzeti


def test():
    import time
    oahmi__aolpl = time.time()
    jtupe__rqofm = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((jtupe__rqofm,), 0, 3, data)
    print('compile time', time.time() - oahmi__aolpl)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    zqnbk__bzxa = np.random.ranf(n)
    elk__xbazi = pd.DataFrame({'A': zqnbk__bzxa, 'B': data[0], 'C': data[1]})
    oahmi__aolpl = time.time()
    uhp__tqyu = elk__xbazi.sort_values('A', inplace=False)
    lszbf__dlgla = time.time()
    sort((zqnbk__bzxa,), 0, n, data)
    print('Bodo', time.time() - lszbf__dlgla, 'Numpy', lszbf__dlgla -
        oahmi__aolpl)
    np.testing.assert_almost_equal(data[0], uhp__tqyu.B.values)
    np.testing.assert_almost_equal(data[1], uhp__tqyu.C.values)


if __name__ == '__main__':
    test()
