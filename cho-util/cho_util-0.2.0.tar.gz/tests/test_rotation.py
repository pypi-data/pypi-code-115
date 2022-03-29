from unittest import TestCase
import numpy as np
import time

from cho_util.math.common import *
from cho_util.math import rotation

def random_point(size, *args, **kwargs):
    size = tuple(np.reshape(size, [-1])) + (3,)
    out = np.random.normal(size=size, *args, **kwargs)
    return out

def test_inverse():
    seed = np.random.randint(low=0,high=65535)
    print('seed  : {}'.format(seed))
    np.random.seed( seed )
    size = (1)
    n_iter = 100

    rtypes = {
            'm' : rotation.matrix,
            'q' : rotation.quaternion,
            #'e' : rotation.euler,
            'a' : rotation.axis_angle
            }
    source_set = list(rtypes.keys())

    seq = np.random.choice(len(source_set), size=n_iter, replace=True)
    seq = np.array(source_set)[seq]
    seq = ''.join(seq)

    for s in seq:
        r = rtypes[s].random(size=size, scale=1e-3)
        ri = rtypes[s].inverse(r)
        p = random_point(size)
        
        rir_p = rtypes[s].rotate(ri, rtypes[s].rotate(r, p))
        irr_p = rtypes[s].rotate(r, rtypes[s].rotate(ri, p))
        if not np.allclose(p, rir_p):
            print('rir_p failed for type : {}'.format(s))
        if not np.allclose(p, irr_p):
            print('irr_p failed for type : {}'.format(s))

def test_rotate():
    seed = np.random.randint(low=0,high=65535)
    print('seed  : {}'.format(seed))
    np.random.seed( seed )
    source_set = ['m', 'q', 'e', 'a']
    size = (1024)
    n_iter = 100
    seq_len = 2

    gen = {
        'm': rotation.matrix.random,
        'q': rotation.quaternion.random,
        'e': rotation.euler.random,
        'a': rotation.axis_angle.random,
    }

    r = {
            'm' : rotation.matrix.rotate,
            'q' : rotation.quaternion.rotate,
            'e' : rotation.euler.rotate,
            'a' : rotation.axis_angle.rotate
            }

    f = {
        'm,m': rotation.matrix.to_matrix,
        'm,q': rotation.matrix.to_quaternion,
        'm,e': rotation.matrix.to_euler,
        'm,a': rotation.matrix.to_axis_angle,

        'q,m': rotation.quaternion.to_matrix,
        'q,q': rotation.quaternion.to_quaternion,
        'q,e': rotation.quaternion.to_euler,
        'q,a': rotation.quaternion.to_axis_angle,

        'e,m': rotation.euler.to_matrix,
        'e,q': rotation.euler.to_quaternion,
        'e,e': rotation.euler.to_euler,
        'e,a': rotation.euler.to_axis_angle,

        'a,m': rotation.axis_angle.to_matrix,
        'a,q': rotation.axis_angle.to_quaternion,
        'a,e': rotation.axis_angle.to_euler,
        'a,a': rotation.axis_angle.to_axis_angle,
    }

    for _ in range(n_iter):
        ts = []
        ts.append(time.time())

        # random conversion sequence
        seq = np.random.choice(len(source_set), size=seq_len, replace=True)
        seq = np.array(source_set)[seq]
        seq = ''.join(seq)
        # uncomment below to debug
        #print(seq[:3] + '..' + seq[-3:])

        # initialization
        x = gen[seq[0]](size=size, scale=1e-3).astype(np.float32)
        point = random_point(size=size)

        R0 = f['{},{}'.format(seq[0], 'm')](x)
        initial_rotated_point = r[seq[0]](x, point)
        initial_rotated_point_m = r['m'](R0, point)
        #print('initial')
        #print(initial_rotated_point)

        for prv, nxt in zip(seq[:-1], seq[1:]):
            # print('{}->{}'.format(prv,nxt))
            # functions
            f_fw = f['{},{}'.format(prv, nxt)]
            f_bw = f['{},{}'.format(nxt, prv)]
            x = f_fw(x)
            if np.any(np.isnan(x)):
                print('x is nan : {}->{}'.format(prv, nxt))
                return

        R1 = f['{},{}'.format(seq[-1], 'm')](x)
        final_rotated_point = r[seq[-1]](x, point)
        final_rotated_point_m = r['m'](R1, point)
        #print('final'
        #print(final_rotated_point)

        error  = norm(final_rotated_point-initial_rotated_point)
        error_m  = norm(final_rotated_point_m-initial_rotated_point_m)
        Rerror = norm(R1-R0, axis=(-2,-1))
        if error.max() > 0.05:
            print('error (point) stats', error.min(), error.mean(), error.max())
            print('error (point-m) stats', error_m.min(), error_m.mean(), error_m.max())
            print('error (matrix) stats', Rerror.min(), Rerror.mean(), Rerror.max())
            ts.append(time.time())
            print('took {} sec'.format(np.diff(ts)))

def main():
    test_rotate()
    test_inverse()

if __name__ == '__main__':
    main()
