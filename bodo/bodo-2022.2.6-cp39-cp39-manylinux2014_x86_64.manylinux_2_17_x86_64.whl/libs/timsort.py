import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    egxpp__aye = hi - lo
    if egxpp__aye < 2:
        return
    if egxpp__aye < MIN_MERGE:
        dcnsy__iumd = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + dcnsy__iumd, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    gocwc__nmfb = minRunLength(egxpp__aye)
    while True:
        sccuh__cwhbn = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if sccuh__cwhbn < gocwc__nmfb:
            zrmpe__hlr = (egxpp__aye if egxpp__aye <= gocwc__nmfb else
                gocwc__nmfb)
            binarySort(key_arrs, lo, lo + zrmpe__hlr, lo + sccuh__cwhbn, data)
            sccuh__cwhbn = zrmpe__hlr
        stackSize = pushRun(stackSize, runBase, runLen, lo, sccuh__cwhbn)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += sccuh__cwhbn
        egxpp__aye -= sccuh__cwhbn
        if egxpp__aye == 0:
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
        wfi__uplj = getitem_arr_tup(key_arrs, start)
        fyi__lgn = getitem_arr_tup(data, start)
        xhuj__paj = lo
        zvqkm__hub = start
        assert xhuj__paj <= zvqkm__hub
        while xhuj__paj < zvqkm__hub:
            iek__jvvhj = xhuj__paj + zvqkm__hub >> 1
            if wfi__uplj < getitem_arr_tup(key_arrs, iek__jvvhj):
                zvqkm__hub = iek__jvvhj
            else:
                xhuj__paj = iek__jvvhj + 1
        assert xhuj__paj == zvqkm__hub
        n = start - xhuj__paj
        copyRange_tup(key_arrs, xhuj__paj, key_arrs, xhuj__paj + 1, n)
        copyRange_tup(data, xhuj__paj, data, xhuj__paj + 1, n)
        setitem_arr_tup(key_arrs, xhuj__paj, wfi__uplj)
        setitem_arr_tup(data, xhuj__paj, fyi__lgn)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    plb__crho = lo + 1
    if plb__crho == hi:
        return 1
    if getitem_arr_tup(key_arrs, plb__crho) < getitem_arr_tup(key_arrs, lo):
        plb__crho += 1
        while plb__crho < hi and getitem_arr_tup(key_arrs, plb__crho
            ) < getitem_arr_tup(key_arrs, plb__crho - 1):
            plb__crho += 1
        reverseRange(key_arrs, lo, plb__crho, data)
    else:
        plb__crho += 1
        while plb__crho < hi and getitem_arr_tup(key_arrs, plb__crho
            ) >= getitem_arr_tup(key_arrs, plb__crho - 1):
            plb__crho += 1
    return plb__crho - lo


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
    lfjnd__tadrt = 0
    while n >= MIN_MERGE:
        lfjnd__tadrt |= n & 1
        n >>= 1
    return n + lfjnd__tadrt


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    bjc__uxnt = len(key_arrs[0])
    tmpLength = (bjc__uxnt >> 1 if bjc__uxnt < 2 *
        INITIAL_TMP_STORAGE_LENGTH else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    kwpht__koqnk = (5 if bjc__uxnt < 120 else 10 if bjc__uxnt < 1542 else 
        19 if bjc__uxnt < 119151 else 40)
    runBase = np.empty(kwpht__koqnk, np.int64)
    runLen = np.empty(kwpht__koqnk, np.int64)
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
    nje__wrtn = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert nje__wrtn >= 0
    base1 += nje__wrtn
    len1 -= nje__wrtn
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
    tuka__ptchc = 0
    pwrab__ayxds = 1
    if key > getitem_arr_tup(arr, base + hint):
        ogzap__hshum = _len - hint
        while pwrab__ayxds < ogzap__hshum and key > getitem_arr_tup(arr, 
            base + hint + pwrab__ayxds):
            tuka__ptchc = pwrab__ayxds
            pwrab__ayxds = (pwrab__ayxds << 1) + 1
            if pwrab__ayxds <= 0:
                pwrab__ayxds = ogzap__hshum
        if pwrab__ayxds > ogzap__hshum:
            pwrab__ayxds = ogzap__hshum
        tuka__ptchc += hint
        pwrab__ayxds += hint
    else:
        ogzap__hshum = hint + 1
        while pwrab__ayxds < ogzap__hshum and key <= getitem_arr_tup(arr, 
            base + hint - pwrab__ayxds):
            tuka__ptchc = pwrab__ayxds
            pwrab__ayxds = (pwrab__ayxds << 1) + 1
            if pwrab__ayxds <= 0:
                pwrab__ayxds = ogzap__hshum
        if pwrab__ayxds > ogzap__hshum:
            pwrab__ayxds = ogzap__hshum
        tmp = tuka__ptchc
        tuka__ptchc = hint - pwrab__ayxds
        pwrab__ayxds = hint - tmp
    assert -1 <= tuka__ptchc and tuka__ptchc < pwrab__ayxds and pwrab__ayxds <= _len
    tuka__ptchc += 1
    while tuka__ptchc < pwrab__ayxds:
        wijy__plt = tuka__ptchc + (pwrab__ayxds - tuka__ptchc >> 1)
        if key > getitem_arr_tup(arr, base + wijy__plt):
            tuka__ptchc = wijy__plt + 1
        else:
            pwrab__ayxds = wijy__plt
    assert tuka__ptchc == pwrab__ayxds
    return pwrab__ayxds


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    pwrab__ayxds = 1
    tuka__ptchc = 0
    if key < getitem_arr_tup(arr, base + hint):
        ogzap__hshum = hint + 1
        while pwrab__ayxds < ogzap__hshum and key < getitem_arr_tup(arr, 
            base + hint - pwrab__ayxds):
            tuka__ptchc = pwrab__ayxds
            pwrab__ayxds = (pwrab__ayxds << 1) + 1
            if pwrab__ayxds <= 0:
                pwrab__ayxds = ogzap__hshum
        if pwrab__ayxds > ogzap__hshum:
            pwrab__ayxds = ogzap__hshum
        tmp = tuka__ptchc
        tuka__ptchc = hint - pwrab__ayxds
        pwrab__ayxds = hint - tmp
    else:
        ogzap__hshum = _len - hint
        while pwrab__ayxds < ogzap__hshum and key >= getitem_arr_tup(arr, 
            base + hint + pwrab__ayxds):
            tuka__ptchc = pwrab__ayxds
            pwrab__ayxds = (pwrab__ayxds << 1) + 1
            if pwrab__ayxds <= 0:
                pwrab__ayxds = ogzap__hshum
        if pwrab__ayxds > ogzap__hshum:
            pwrab__ayxds = ogzap__hshum
        tuka__ptchc += hint
        pwrab__ayxds += hint
    assert -1 <= tuka__ptchc and tuka__ptchc < pwrab__ayxds and pwrab__ayxds <= _len
    tuka__ptchc += 1
    while tuka__ptchc < pwrab__ayxds:
        wijy__plt = tuka__ptchc + (pwrab__ayxds - tuka__ptchc >> 1)
        if key < getitem_arr_tup(arr, base + wijy__plt):
            pwrab__ayxds = wijy__plt
        else:
            tuka__ptchc = wijy__plt + 1
    assert tuka__ptchc == pwrab__ayxds
    return pwrab__ayxds


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
        ymfar__tgzd = 0
        ytx__yrvq = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                ytx__yrvq += 1
                ymfar__tgzd = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                ymfar__tgzd += 1
                ytx__yrvq = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not ymfar__tgzd | ytx__yrvq < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            ymfar__tgzd = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if ymfar__tgzd != 0:
                copyRange_tup(tmp, cursor1, arr, dest, ymfar__tgzd)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, ymfar__tgzd)
                dest += ymfar__tgzd
                cursor1 += ymfar__tgzd
                len1 -= ymfar__tgzd
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            ytx__yrvq = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if ytx__yrvq != 0:
                copyRange_tup(arr, cursor2, arr, dest, ytx__yrvq)
                copyRange_tup(arr_data, cursor2, arr_data, dest, ytx__yrvq)
                dest += ytx__yrvq
                cursor2 += ytx__yrvq
                len2 -= ytx__yrvq
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
            if not ymfar__tgzd >= MIN_GALLOP | ytx__yrvq >= MIN_GALLOP:
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
        ymfar__tgzd = 0
        ytx__yrvq = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                ymfar__tgzd += 1
                ytx__yrvq = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                ytx__yrvq += 1
                ymfar__tgzd = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not ymfar__tgzd | ytx__yrvq < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            ymfar__tgzd = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if ymfar__tgzd != 0:
                dest -= ymfar__tgzd
                cursor1 -= ymfar__tgzd
                len1 -= ymfar__tgzd
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, ymfar__tgzd)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    ymfar__tgzd)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            ytx__yrvq = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if ytx__yrvq != 0:
                dest -= ytx__yrvq
                cursor2 -= ytx__yrvq
                len2 -= ytx__yrvq
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, ytx__yrvq)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    ytx__yrvq)
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
            if not ymfar__tgzd >= MIN_GALLOP | ytx__yrvq >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    zxhc__hbyn = len(key_arrs[0])
    if tmpLength < minCapacity:
        cego__navj = minCapacity
        cego__navj |= cego__navj >> 1
        cego__navj |= cego__navj >> 2
        cego__navj |= cego__navj >> 4
        cego__navj |= cego__navj >> 8
        cego__navj |= cego__navj >> 16
        cego__navj += 1
        if cego__navj < 0:
            cego__navj = minCapacity
        else:
            cego__navj = min(cego__navj, zxhc__hbyn >> 1)
        tmp = alloc_arr_tup(cego__navj, key_arrs)
        tmp_data = alloc_arr_tup(cego__navj, data)
        tmpLength = cego__navj
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        tmotm__hbqwm = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = tmotm__hbqwm


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    zblh__tcj = arr_tup.count
    ybixc__oqv = 'def f(arr_tup, lo, hi):\n'
    for i in range(zblh__tcj):
        ybixc__oqv += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        ybixc__oqv += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        ybixc__oqv += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    ybixc__oqv += '  return\n'
    xbbrn__wwl = {}
    exec(ybixc__oqv, {}, xbbrn__wwl)
    uuxn__rwib = xbbrn__wwl['f']
    return uuxn__rwib


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    zblh__tcj = src_arr_tup.count
    assert zblh__tcj == dst_arr_tup.count
    ybixc__oqv = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(zblh__tcj):
        ybixc__oqv += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    ybixc__oqv += '  return\n'
    xbbrn__wwl = {}
    exec(ybixc__oqv, {'copyRange': copyRange}, xbbrn__wwl)
    cvwgr__ysti = xbbrn__wwl['f']
    return cvwgr__ysti


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    zblh__tcj = src_arr_tup.count
    assert zblh__tcj == dst_arr_tup.count
    ybixc__oqv = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(zblh__tcj):
        ybixc__oqv += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    ybixc__oqv += '  return\n'
    xbbrn__wwl = {}
    exec(ybixc__oqv, {'copyElement': copyElement}, xbbrn__wwl)
    cvwgr__ysti = xbbrn__wwl['f']
    return cvwgr__ysti


def getitem_arr_tup(arr_tup, ind):
    rozrd__omru = [arr[ind] for arr in arr_tup]
    return tuple(rozrd__omru)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    zblh__tcj = arr_tup.count
    ybixc__oqv = 'def f(arr_tup, ind):\n'
    ybixc__oqv += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(zblh__tcj)]), ',' if zblh__tcj == 1 else '')
    xbbrn__wwl = {}
    exec(ybixc__oqv, {}, xbbrn__wwl)
    rcile__rdabz = xbbrn__wwl['f']
    return rcile__rdabz


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, yrc__ahp in zip(arr_tup, val_tup):
        arr[ind] = yrc__ahp


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    zblh__tcj = arr_tup.count
    ybixc__oqv = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(zblh__tcj):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            ybixc__oqv += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            ybixc__oqv += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    ybixc__oqv += '  return\n'
    xbbrn__wwl = {}
    exec(ybixc__oqv, {}, xbbrn__wwl)
    rcile__rdabz = xbbrn__wwl['f']
    return rcile__rdabz


def test():
    import time
    oiet__qro = time.time()
    bmxx__ldnox = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((bmxx__ldnox,), 0, 3, data)
    print('compile time', time.time() - oiet__qro)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    clx__hgrqa = np.random.ranf(n)
    oul__dml = pd.DataFrame({'A': clx__hgrqa, 'B': data[0], 'C': data[1]})
    oiet__qro = time.time()
    tsd__vpss = oul__dml.sort_values('A', inplace=False)
    ebnfh__nhg = time.time()
    sort((clx__hgrqa,), 0, n, data)
    print('Bodo', time.time() - ebnfh__nhg, 'Numpy', ebnfh__nhg - oiet__qro)
    np.testing.assert_almost_equal(data[0], tsd__vpss.B.values)
    np.testing.assert_almost_equal(data[1], tsd__vpss.C.values)


if __name__ == '__main__':
    test()
