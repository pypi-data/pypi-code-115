

from scipy.signal import find_peaks
from scipy import stats
import pandas as pd
import numpy as np







FEATURES = ['sensor_1', 'sensor_2',
       'sensor_3', 'sensor_4', 'sensor_5', 'sensor_6', 'sensor_7', 'sensor_8',
       'sensor_9', 'sensor_10', 'sensor_11', 'sensor_12', 'sensor_13',
       'sensor_14', 'sensor_15', 'sensor_16', 'sensor_17', 'sensor_18',
       'sensor_19', 'sensor_20', 'sensor_21', 'sensor_22', 'sensor_23',
       'sensor_24']


def iqr(x):
    q3, q1 = np.percentile(x, [75 ,25])
    return q3 - q1

def avg_absolute_diff(x):
    return np.mean(np.absolute(x - np.mean(x)))

def max_min_diff(x):
    return np.max(x) - np.min(x)

def median_abs_dev(x):
     return np.median(np.absolute(x - np.median(x)))

def negative_count(x):
    return np.sum(x < 0)

def positive_count(x):
    return np.sum(x > 0)

def values_above_mean(x):
    return np.sum(x > x.mean())

def baseline(x):
    return x.iloc[:8].mean()

def avg_of_pause(x):
    return x.iloc[[37,38,39,40]].mean()

def pause_phase_area(x):
    x = x.iloc[[37,38,39,40]]
    return np.trapz(x) 


def peaks(x):
    return len(find_peaks(x)[0])


def extract_features(df, unique_id='unique_id', label='result', features=FEATURES):

    features.extend([unique_id, label])
    df = df[features].groupby(by=[unique_id, label]).agg([min, max, np.std, iqr, np.median, stats.skew, stats.kurtosis, \
    np.trapz, avg_absolute_diff, peaks, values_above_mean, positive_count, negative_count, median_abs_dev, \
    max_min_diff, baseline, avg_of_pause, pause_phase_area]).reset_index()[features]

    df.columns = ["_".join(col) for col in df.columns.to_flat_index()]
    return df, features