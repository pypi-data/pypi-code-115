#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:46:46 2022

@author: patrick
"""

import argparse
from functions_and_stuff import *
import time



parser = argparse.ArgumentParser()

parser.add_argument('--base_folder',
                    default='/home/',
                    help="Specify the folder where you plan to store the data - note, you should have also imported ALL crypto data into this folder (or a sub directory of this folder) too.",
                    type=str)
parser.add_argument('--coin',
                    default='XMRBTC',
                    help="Currency Symbol - as stated on Binance",
                    type=str)
parser.add_argument('--candle_size',
                    default='25',
                    help="Candle Size: SPecified in MINUTES",
                    type=str)
parser.add_argument('--remove_temp_files',
                    default=False,
                    help="If you wish to remove the Feather files that have been created in the Unpack Zips Step",
                    type=bool)
parser.add_argument('--remove_intermediate_files',
                    default=False,
                    help="If you wish to remove the intermediate candle files that have been created in previous step",
                    type=bool)
args = vars(parser.parse_args())


def main(kwargs):
    start_time=time.time()

    #Creates some base candles
    create_all_candles(**kwargs)

    #Finalises candles
    order_and_interpolate(**kwargs)

    #print('Finished everything for %s %s Candles, took %s Minutes' %(coin, candle_size, (time.time-start_time)/60))



if __name__ == '__main__':
    main(kwargs=args)





