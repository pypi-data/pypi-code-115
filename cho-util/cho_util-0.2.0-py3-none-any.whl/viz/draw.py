#!/usr/bin/env python2
import numpy as np
try:
    import cv2
except ImportError as e:
    print('OpenCV Import Error : {}'.format(e))

from cho_util import math as vm

def draw_lines(img1,img2,lines,pts1,pts2,cols,
        draw_pt=False
        ):
    ''' img1 - image on which we draw the epilines for the points in img2
        lines - corresponding epilines '''
    h,w = img1.shape[:2]
    for r,pt1,pt2,color in zip(lines,pts1,pts2,cols):
        x0,y0 = map(int, [0, -r[2]/r[1] ])
        x1,y1 = map(int, [w, -(r[2]+r[0]*w)/r[1] ])
        img1 = cv2.line(img1, (x0,y0), (x1,y1), color,1)
        if draw_pt:
            img1 = cv2.circle(img1, tuple(vm.rint(pt1)),5,color,-1)
            img2 = cv2.circle(img2, tuple(vm.rint(pt2)),5,color,-1)
    return img1,img2

def draw_points(img, pt,
        radius=None,
        color=None
        ):
    if radius is None:
        radius = vm.rint( 0.005 * np.min([img.shape[:2]]))
    pt = vm.rint(pt)
    for p in pt:
        cv2.circle(img, tuple(p), radius, color, radius)
    return img

def draw_matches(img1, img2, pt1, pt2,
        msk=None,
        radius=None,
        single=False
        ):
    if radius is None:
        radius = vm.rint( 0.005 * np.min([img1.shape[:2], img2.shape[:2]]) )
    h,w = np.shape(img1)[:2]

    if single:
        pt1 = np.round(pt1).astype(np.int32)
        pt2 = np.round(pt2).astype(np.int32)
        mim = img2.copy()
        mim0 = mim.copy()
    else:
        pt1 = np.round(pt1).astype(np.int32)
        pt2 = np.round(pt2 + [[w,0]]).astype(np.int32)
        mim = np.concatenate([img1, img2], axis=1)
        mim[:,w ] = 0
        mim0 = mim.copy()

    if msk is None:
        msk = np.ones(len(pt1), dtype=np.bool)

    n = msk.sum()
    col = np.random.randint(255, size=(n,3))

    for (p1, p2, c) in zip(pt1[msk], pt2[msk], col):
        p1 = tuple(p1)
        p2 = tuple(p2)
        cc = tuple([int(e) for e in vm.rint(c)])
        cv2.line(mim, p1, p2, cc, radius)
    mim = cv2.addWeighted(mim0, 0.5, mim, 0.5, 0.0)

    for (p1, p2, c) in zip(pt1[msk], pt2[msk], col):
        cc = tuple([int(e) for e in vm.rint(c)])
        #cc = (255,255,255)
        cv2.circle(mim, tuple(p1), radius, cc, -1)
        cv2.circle(mim, tuple(p2), radius, cc, -1)

    for p in pt1[~msk]:
        cv2.circle(mim, tuple(p), radius, (255,0,0), -1)

    for p in pt2[~msk]:
        cv2.circle(mim, tuple(p), radius, (255,0,0), -1)
    return mim

def make_color_wheel():
    """
    Generate color wheel according Middlebury color code
    :return: Color wheel
    """
    RY = 15
    YG = 6
    GC = 4
    CB = 11
    BM = 13
    MR = 6

    ncols = RY + YG + GC + CB + BM + MR

    colorwheel = np.zeros([ncols, 3])

    col = 0

    # RY
    colorwheel[0:RY, 0] = 255
    colorwheel[0:RY, 1] = np.transpose(np.floor(255*np.arange(0, RY) / RY))
    col += RY

    # YG
    colorwheel[col:col+YG, 0] = 255 - np.transpose(np.floor(255*np.arange(0, YG) / YG))
    colorwheel[col:col+YG, 1] = 255
    col += YG

    # GC
    colorwheel[col:col+GC, 1] = 255
    colorwheel[col:col+GC, 2] = np.transpose(np.floor(255*np.arange(0, GC) / GC))
    col += GC

    # CB
    colorwheel[col:col+CB, 1] = 255 - np.transpose(np.floor(255*np.arange(0, CB) / CB))
    colorwheel[col:col+CB, 2] = 255
    col += CB

    # BM
    colorwheel[col:col+BM, 2] = 255
    colorwheel[col:col+BM, 0] = np.transpose(np.floor(255*np.arange(0, BM) / BM))
    col += + BM

    # MR
    colorwheel[col:col+MR, 2] = 255 - np.transpose(np.floor(255 * np.arange(0, MR) / MR))
    colorwheel[col:col+MR, 0] = 255

    return colorwheel

def compute_color(u, v):
    """
    compute optical flow color map
    :param u: optical flow horizontal map
    :param v: optical flow vertical map
    :return: optical flow in color code
    """
    [h, w] = u.shape
    img = np.zeros([h, w, 3])
    nanIdx = np.isnan(u) | np.isnan(v)
    u[nanIdx] = 0
    v[nanIdx] = 0

    colorwheel = make_color_wheel()
    ncols = np.size(colorwheel, 0)

    rad = np.sqrt(u**2+v**2)

    a = np.arctan2(-v, -u) / np.pi

    fk = (a+1) / 2 * (ncols - 1) + 1

    k0 = np.floor(fk).astype(int)

    k1 = k0 + 1
    k1[k1 == ncols+1] = 1
    f = fk - k0

    for i in range(0, np.size(colorwheel,1)):
        tmp = colorwheel[:, i]
        col0 = tmp[k0-1] / 255
        col1 = tmp[k1-1] / 255
        col = (1-f) * col0 + f * col1

        idx = rad <= 1
        col[idx] = 1-rad[idx]*(1-col[idx])
        notidx = np.logical_not(idx)

        col[notidx] *= 0.75
        img[:, :, i] = np.uint8(np.floor(255 * col*(1-nanIdx)))

    return img

def flow_to_image(flow, display=False, thresh=1e7):
    """
    Convert flow into middlebury color code image
    :param flow: optical flow map
    :return: optical flow image in middlebury color
    """
    # from https://github.com/vt-vl-lab/tf_flownet2.git
    u = flow[:, :, 0]
    v = flow[:, :, 1]

    maxu = -999.
    maxv = -999.
    minu = 999.
    minv = 999.

    idxUnknow = (abs(u) > thresh) | (abs(v) > thresh)
    u[idxUnknow] = 0
    v[idxUnknow] = 0

    maxu = max(maxu, np.max(u))
    minu = min(minu, np.min(u))

    maxv = max(maxv, np.max(v))
    minv = min(minv, np.min(v))

    rad = np.sqrt(u ** 2 + v ** 2)
    maxrad = max(-1, np.max(rad))

    if display:
        print("max flow: %.4f\nflow range:\nu = %.3f .. %.3f\nv = %.3f .. %.3f" % (maxrad, minu,maxu, minv, maxv))

    u = u/(maxrad + np.finfo(float).eps)
    v = v/(maxrad + np.finfo(float).eps)

    img = compute_color(u, v)

    idx = np.repeat(idxUnknow[:, :, np.newaxis], 3, axis=2)
    img[idx] = 0

    return np.uint8(img)

