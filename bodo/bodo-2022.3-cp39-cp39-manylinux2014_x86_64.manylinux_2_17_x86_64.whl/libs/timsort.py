import numpy as np
import pandas as pd
import numba
from numba.extending import overload
from bodo.utils.utils import alloc_arr_tup
MIN_MERGE = 32


@numba.njit(no_cpython_wrapper=True, cache=True)
def sort(key_arrs, lo, hi, data):
    ewyvi__wrwk = hi - lo
    if ewyvi__wrwk < 2:
        return
    if ewyvi__wrwk < MIN_MERGE:
        nnw__uco = countRunAndMakeAscending(key_arrs, lo, hi, data)
        binarySort(key_arrs, lo, hi, lo + nnw__uco, data)
        return
    stackSize, runBase, runLen, tmpLength, tmp, tmp_data, minGallop = (
        init_sort_start(key_arrs, data))
    njsyh__kavk = minRunLength(ewyvi__wrwk)
    while True:
        bet__ctv = countRunAndMakeAscending(key_arrs, lo, hi, data)
        if bet__ctv < njsyh__kavk:
            xge__jlimk = (ewyvi__wrwk if ewyvi__wrwk <= njsyh__kavk else
                njsyh__kavk)
            binarySort(key_arrs, lo, lo + xge__jlimk, lo + bet__ctv, data)
            bet__ctv = xge__jlimk
        stackSize = pushRun(stackSize, runBase, runLen, lo, bet__ctv)
        stackSize, tmpLength, tmp, tmp_data, minGallop = mergeCollapse(
            stackSize, runBase, runLen, key_arrs, data, tmpLength, tmp,
            tmp_data, minGallop)
        lo += bet__ctv
        ewyvi__wrwk -= bet__ctv
        if ewyvi__wrwk == 0:
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
        ilwv__jfx = getitem_arr_tup(key_arrs, start)
        tbxfv__mznkj = getitem_arr_tup(data, start)
        ueff__clxo = lo
        lnaca__bvc = start
        assert ueff__clxo <= lnaca__bvc
        while ueff__clxo < lnaca__bvc:
            wdj__bpyt = ueff__clxo + lnaca__bvc >> 1
            if ilwv__jfx < getitem_arr_tup(key_arrs, wdj__bpyt):
                lnaca__bvc = wdj__bpyt
            else:
                ueff__clxo = wdj__bpyt + 1
        assert ueff__clxo == lnaca__bvc
        n = start - ueff__clxo
        copyRange_tup(key_arrs, ueff__clxo, key_arrs, ueff__clxo + 1, n)
        copyRange_tup(data, ueff__clxo, data, ueff__clxo + 1, n)
        setitem_arr_tup(key_arrs, ueff__clxo, ilwv__jfx)
        setitem_arr_tup(data, ueff__clxo, tbxfv__mznkj)
        start += 1


@numba.njit(no_cpython_wrapper=True, cache=True)
def countRunAndMakeAscending(key_arrs, lo, hi, data):
    assert lo < hi
    ccih__ckq = lo + 1
    if ccih__ckq == hi:
        return 1
    if getitem_arr_tup(key_arrs, ccih__ckq) < getitem_arr_tup(key_arrs, lo):
        ccih__ckq += 1
        while ccih__ckq < hi and getitem_arr_tup(key_arrs, ccih__ckq
            ) < getitem_arr_tup(key_arrs, ccih__ckq - 1):
            ccih__ckq += 1
        reverseRange(key_arrs, lo, ccih__ckq, data)
    else:
        ccih__ckq += 1
        while ccih__ckq < hi and getitem_arr_tup(key_arrs, ccih__ckq
            ) >= getitem_arr_tup(key_arrs, ccih__ckq - 1):
            ccih__ckq += 1
    return ccih__ckq - lo


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
    dzy__cjzl = 0
    while n >= MIN_MERGE:
        dzy__cjzl |= n & 1
        n >>= 1
    return n + dzy__cjzl


MIN_GALLOP = 7
INITIAL_TMP_STORAGE_LENGTH = 256


@numba.njit(no_cpython_wrapper=True, cache=True)
def init_sort_start(key_arrs, data):
    minGallop = MIN_GALLOP
    dlonr__rzz = len(key_arrs[0])
    tmpLength = (dlonr__rzz >> 1 if dlonr__rzz < 2 *
        INITIAL_TMP_STORAGE_LENGTH else INITIAL_TMP_STORAGE_LENGTH)
    tmp = alloc_arr_tup(tmpLength, key_arrs)
    tmp_data = alloc_arr_tup(tmpLength, data)
    stackSize = 0
    hhrrq__hfxj = (5 if dlonr__rzz < 120 else 10 if dlonr__rzz < 1542 else 
        19 if dlonr__rzz < 119151 else 40)
    runBase = np.empty(hhrrq__hfxj, np.int64)
    runLen = np.empty(hhrrq__hfxj, np.int64)
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
    cid__lmj = gallopRight(getitem_arr_tup(key_arrs, base2), key_arrs,
        base1, len1, 0)
    assert cid__lmj >= 0
    base1 += cid__lmj
    len1 -= cid__lmj
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
    bhywe__zmdey = 0
    rbx__qiprb = 1
    if key > getitem_arr_tup(arr, base + hint):
        mukq__gkz = _len - hint
        while rbx__qiprb < mukq__gkz and key > getitem_arr_tup(arr, base +
            hint + rbx__qiprb):
            bhywe__zmdey = rbx__qiprb
            rbx__qiprb = (rbx__qiprb << 1) + 1
            if rbx__qiprb <= 0:
                rbx__qiprb = mukq__gkz
        if rbx__qiprb > mukq__gkz:
            rbx__qiprb = mukq__gkz
        bhywe__zmdey += hint
        rbx__qiprb += hint
    else:
        mukq__gkz = hint + 1
        while rbx__qiprb < mukq__gkz and key <= getitem_arr_tup(arr, base +
            hint - rbx__qiprb):
            bhywe__zmdey = rbx__qiprb
            rbx__qiprb = (rbx__qiprb << 1) + 1
            if rbx__qiprb <= 0:
                rbx__qiprb = mukq__gkz
        if rbx__qiprb > mukq__gkz:
            rbx__qiprb = mukq__gkz
        tmp = bhywe__zmdey
        bhywe__zmdey = hint - rbx__qiprb
        rbx__qiprb = hint - tmp
    assert -1 <= bhywe__zmdey and bhywe__zmdey < rbx__qiprb and rbx__qiprb <= _len
    bhywe__zmdey += 1
    while bhywe__zmdey < rbx__qiprb:
        yfm__xhy = bhywe__zmdey + (rbx__qiprb - bhywe__zmdey >> 1)
        if key > getitem_arr_tup(arr, base + yfm__xhy):
            bhywe__zmdey = yfm__xhy + 1
        else:
            rbx__qiprb = yfm__xhy
    assert bhywe__zmdey == rbx__qiprb
    return rbx__qiprb


@numba.njit(no_cpython_wrapper=True, cache=True)
def gallopRight(key, arr, base, _len, hint):
    assert _len > 0 and hint >= 0 and hint < _len
    rbx__qiprb = 1
    bhywe__zmdey = 0
    if key < getitem_arr_tup(arr, base + hint):
        mukq__gkz = hint + 1
        while rbx__qiprb < mukq__gkz and key < getitem_arr_tup(arr, base +
            hint - rbx__qiprb):
            bhywe__zmdey = rbx__qiprb
            rbx__qiprb = (rbx__qiprb << 1) + 1
            if rbx__qiprb <= 0:
                rbx__qiprb = mukq__gkz
        if rbx__qiprb > mukq__gkz:
            rbx__qiprb = mukq__gkz
        tmp = bhywe__zmdey
        bhywe__zmdey = hint - rbx__qiprb
        rbx__qiprb = hint - tmp
    else:
        mukq__gkz = _len - hint
        while rbx__qiprb < mukq__gkz and key >= getitem_arr_tup(arr, base +
            hint + rbx__qiprb):
            bhywe__zmdey = rbx__qiprb
            rbx__qiprb = (rbx__qiprb << 1) + 1
            if rbx__qiprb <= 0:
                rbx__qiprb = mukq__gkz
        if rbx__qiprb > mukq__gkz:
            rbx__qiprb = mukq__gkz
        bhywe__zmdey += hint
        rbx__qiprb += hint
    assert -1 <= bhywe__zmdey and bhywe__zmdey < rbx__qiprb and rbx__qiprb <= _len
    bhywe__zmdey += 1
    while bhywe__zmdey < rbx__qiprb:
        yfm__xhy = bhywe__zmdey + (rbx__qiprb - bhywe__zmdey >> 1)
        if key < getitem_arr_tup(arr, base + yfm__xhy):
            rbx__qiprb = yfm__xhy
        else:
            bhywe__zmdey = yfm__xhy + 1
    assert bhywe__zmdey == rbx__qiprb
    return rbx__qiprb


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
        gfhu__jgc = 0
        ynr__eyuu = 0
        while True:
            assert len1 > 1 and len2 > 0
            if getitem_arr_tup(arr, cursor2) < getitem_arr_tup(tmp, cursor1):
                copyElement_tup(arr, cursor2, arr, dest)
                copyElement_tup(arr_data, cursor2, arr_data, dest)
                cursor2 += 1
                dest += 1
                ynr__eyuu += 1
                gfhu__jgc = 0
                len2 -= 1
                if len2 == 0:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor1, arr, dest)
                copyElement_tup(tmp_data, cursor1, arr_data, dest)
                cursor1 += 1
                dest += 1
                gfhu__jgc += 1
                ynr__eyuu = 0
                len1 -= 1
                if len1 == 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            if not gfhu__jgc | ynr__eyuu < minGallop:
                break
        while True:
            assert len1 > 1 and len2 > 0
            gfhu__jgc = gallopRight(getitem_arr_tup(arr, cursor2), tmp,
                cursor1, len1, 0)
            if gfhu__jgc != 0:
                copyRange_tup(tmp, cursor1, arr, dest, gfhu__jgc)
                copyRange_tup(tmp_data, cursor1, arr_data, dest, gfhu__jgc)
                dest += gfhu__jgc
                cursor1 += gfhu__jgc
                len1 -= gfhu__jgc
                if len1 <= 1:
                    return len1, len2, cursor1, cursor2, dest, minGallop
            copyElement_tup(arr, cursor2, arr, dest)
            copyElement_tup(arr_data, cursor2, arr_data, dest)
            cursor2 += 1
            dest += 1
            len2 -= 1
            if len2 == 0:
                return len1, len2, cursor1, cursor2, dest, minGallop
            ynr__eyuu = gallopLeft(getitem_arr_tup(tmp, cursor1), arr,
                cursor2, len2, 0)
            if ynr__eyuu != 0:
                copyRange_tup(arr, cursor2, arr, dest, ynr__eyuu)
                copyRange_tup(arr_data, cursor2, arr_data, dest, ynr__eyuu)
                dest += ynr__eyuu
                cursor2 += ynr__eyuu
                len2 -= ynr__eyuu
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
            if not gfhu__jgc >= MIN_GALLOP | ynr__eyuu >= MIN_GALLOP:
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
        gfhu__jgc = 0
        ynr__eyuu = 0
        while True:
            assert len1 > 0 and len2 > 1
            if getitem_arr_tup(tmp, cursor2) < getitem_arr_tup(arr, cursor1):
                copyElement_tup(arr, cursor1, arr, dest)
                copyElement_tup(arr_data, cursor1, arr_data, dest)
                cursor1 -= 1
                dest -= 1
                gfhu__jgc += 1
                ynr__eyuu = 0
                len1 -= 1
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            else:
                copyElement_tup(tmp, cursor2, arr, dest)
                copyElement_tup(tmp_data, cursor2, arr_data, dest)
                cursor2 -= 1
                dest -= 1
                ynr__eyuu += 1
                gfhu__jgc = 0
                len2 -= 1
                if len2 == 1:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            if not gfhu__jgc | ynr__eyuu < minGallop:
                break
        while True:
            assert len1 > 0 and len2 > 1
            gfhu__jgc = len1 - gallopRight(getitem_arr_tup(tmp, cursor2),
                arr, base1, len1, len1 - 1)
            if gfhu__jgc != 0:
                dest -= gfhu__jgc
                cursor1 -= gfhu__jgc
                len1 -= gfhu__jgc
                copyRange_tup(arr, cursor1 + 1, arr, dest + 1, gfhu__jgc)
                copyRange_tup(arr_data, cursor1 + 1, arr_data, dest + 1,
                    gfhu__jgc)
                if len1 == 0:
                    return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            copyElement_tup(tmp, cursor2, arr, dest)
            copyElement_tup(tmp_data, cursor2, arr_data, dest)
            cursor2 -= 1
            dest -= 1
            len2 -= 1
            if len2 == 1:
                return len1, len2, tmp, cursor1, cursor2, dest, minGallop
            ynr__eyuu = len2 - gallopLeft(getitem_arr_tup(arr, cursor1),
                tmp, 0, len2, len2 - 1)
            if ynr__eyuu != 0:
                dest -= ynr__eyuu
                cursor2 -= ynr__eyuu
                len2 -= ynr__eyuu
                copyRange_tup(tmp, cursor2 + 1, arr, dest + 1, ynr__eyuu)
                copyRange_tup(tmp_data, cursor2 + 1, arr_data, dest + 1,
                    ynr__eyuu)
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
            if not gfhu__jgc >= MIN_GALLOP | ynr__eyuu >= MIN_GALLOP:
                break
        if minGallop < 0:
            minGallop = 0
        minGallop += 2
    return len1, len2, tmp, cursor1, cursor2, dest, minGallop


@numba.njit(no_cpython_wrapper=True, cache=True)
def ensureCapacity(tmpLength, tmp, tmp_data, key_arrs, data, minCapacity):
    uieo__exrz = len(key_arrs[0])
    if tmpLength < minCapacity:
        azf__pvelt = minCapacity
        azf__pvelt |= azf__pvelt >> 1
        azf__pvelt |= azf__pvelt >> 2
        azf__pvelt |= azf__pvelt >> 4
        azf__pvelt |= azf__pvelt >> 8
        azf__pvelt |= azf__pvelt >> 16
        azf__pvelt += 1
        if azf__pvelt < 0:
            azf__pvelt = minCapacity
        else:
            azf__pvelt = min(azf__pvelt, uieo__exrz >> 1)
        tmp = alloc_arr_tup(azf__pvelt, key_arrs)
        tmp_data = alloc_arr_tup(azf__pvelt, data)
        tmpLength = azf__pvelt
    return tmpLength, tmp, tmp_data


def swap_arrs(data, lo, hi):
    for arr in data:
        nvsl__hdxf = arr[lo]
        arr[lo] = arr[hi]
        arr[hi] = nvsl__hdxf


@overload(swap_arrs, no_unliteral=True)
def swap_arrs_overload(arr_tup, lo, hi):
    xmpw__dysve = arr_tup.count
    fzb__zvrnx = 'def f(arr_tup, lo, hi):\n'
    for i in range(xmpw__dysve):
        fzb__zvrnx += '  tmp_v_{} = arr_tup[{}][lo]\n'.format(i, i)
        fzb__zvrnx += '  arr_tup[{}][lo] = arr_tup[{}][hi]\n'.format(i, i)
        fzb__zvrnx += '  arr_tup[{}][hi] = tmp_v_{}\n'.format(i, i)
    fzb__zvrnx += '  return\n'
    sndl__zkwcd = {}
    exec(fzb__zvrnx, {}, sndl__zkwcd)
    rjt__fjhg = sndl__zkwcd['f']
    return rjt__fjhg


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyRange(src_arr, src_pos, dst_arr, dst_pos, n):
    dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


def copyRange_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos:dst_pos + n] = src_arr[src_pos:src_pos + n]


@overload(copyRange_tup, no_unliteral=True)
def copyRange_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):
    xmpw__dysve = src_arr_tup.count
    assert xmpw__dysve == dst_arr_tup.count
    fzb__zvrnx = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos, n):\n'
    for i in range(xmpw__dysve):
        fzb__zvrnx += (
            '  copyRange(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos, n)\n'
            .format(i, i))
    fzb__zvrnx += '  return\n'
    sndl__zkwcd = {}
    exec(fzb__zvrnx, {'copyRange': copyRange}, sndl__zkwcd)
    byh__rsfz = sndl__zkwcd['f']
    return byh__rsfz


@numba.njit(no_cpython_wrapper=True, cache=True)
def copyElement(src_arr, src_pos, dst_arr, dst_pos):
    dst_arr[dst_pos] = src_arr[src_pos]


def copyElement_tup(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    for src_arr, dst_arr in zip(src_arr_tup, dst_arr_tup):
        dst_arr[dst_pos] = src_arr[src_pos]


@overload(copyElement_tup, no_unliteral=True)
def copyElement_tup_overload(src_arr_tup, src_pos, dst_arr_tup, dst_pos):
    xmpw__dysve = src_arr_tup.count
    assert xmpw__dysve == dst_arr_tup.count
    fzb__zvrnx = 'def f(src_arr_tup, src_pos, dst_arr_tup, dst_pos):\n'
    for i in range(xmpw__dysve):
        fzb__zvrnx += (
            '  copyElement(src_arr_tup[{}], src_pos, dst_arr_tup[{}], dst_pos)\n'
            .format(i, i))
    fzb__zvrnx += '  return\n'
    sndl__zkwcd = {}
    exec(fzb__zvrnx, {'copyElement': copyElement}, sndl__zkwcd)
    byh__rsfz = sndl__zkwcd['f']
    return byh__rsfz


def getitem_arr_tup(arr_tup, ind):
    pig__obc = [arr[ind] for arr in arr_tup]
    return tuple(pig__obc)


@overload(getitem_arr_tup, no_unliteral=True)
def getitem_arr_tup_overload(arr_tup, ind):
    xmpw__dysve = arr_tup.count
    fzb__zvrnx = 'def f(arr_tup, ind):\n'
    fzb__zvrnx += '  return ({}{})\n'.format(','.join(['arr_tup[{}][ind]'.
        format(i) for i in range(xmpw__dysve)]), ',' if xmpw__dysve == 1 else
        '')
    sndl__zkwcd = {}
    exec(fzb__zvrnx, {}, sndl__zkwcd)
    zfqih__mxkoe = sndl__zkwcd['f']
    return zfqih__mxkoe


def setitem_arr_tup(arr_tup, ind, val_tup):
    for arr, jhdl__iei in zip(arr_tup, val_tup):
        arr[ind] = jhdl__iei


@overload(setitem_arr_tup, no_unliteral=True)
def setitem_arr_tup_overload(arr_tup, ind, val_tup):
    xmpw__dysve = arr_tup.count
    fzb__zvrnx = 'def f(arr_tup, ind, val_tup):\n'
    for i in range(xmpw__dysve):
        if isinstance(val_tup, numba.core.types.BaseTuple):
            fzb__zvrnx += '  arr_tup[{}][ind] = val_tup[{}]\n'.format(i, i)
        else:
            assert arr_tup.count == 1
            fzb__zvrnx += '  arr_tup[{}][ind] = val_tup\n'.format(i)
    fzb__zvrnx += '  return\n'
    sndl__zkwcd = {}
    exec(fzb__zvrnx, {}, sndl__zkwcd)
    zfqih__mxkoe = sndl__zkwcd['f']
    return zfqih__mxkoe


def test():
    import time
    xvk__kgi = time.time()
    iin__vsrcc = np.ones(3)
    data = np.arange(3), np.ones(3)
    sort((iin__vsrcc,), 0, 3, data)
    print('compile time', time.time() - xvk__kgi)
    n = 210000
    np.random.seed(2)
    data = np.arange(n), np.random.ranf(n)
    rfumv__hwid = np.random.ranf(n)
    febcp__ecz = pd.DataFrame({'A': rfumv__hwid, 'B': data[0], 'C': data[1]})
    xvk__kgi = time.time()
    homq__ujsz = febcp__ecz.sort_values('A', inplace=False)
    pcr__xug = time.time()
    sort((rfumv__hwid,), 0, n, data)
    print('Bodo', time.time() - pcr__xug, 'Numpy', pcr__xug - xvk__kgi)
    np.testing.assert_almost_equal(data[0], homq__ujsz.B.values)
    np.testing.assert_almost_equal(data[1], homq__ujsz.C.values)


if __name__ == '__main__':
    test()
