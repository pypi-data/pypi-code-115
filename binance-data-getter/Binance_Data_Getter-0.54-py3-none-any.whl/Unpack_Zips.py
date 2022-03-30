#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:40:23 2022

@author: patrick
"""
import argparse
from .functions_and_stuff import *



parser = argparse.ArgumentParser()

parser.add_argument('--base_folder',
                    default='/home/',
                    help="Specify the folder where you plan to store the data - note, you should have also imported ALL crypto data into this folder (or a sub directory of this folder) too.",
                    type=str)
parser.add_argument('--coin',
                    default='LTCBTC',
                    help="Currency Symbol - as stated on Binance",
                    type=str)
args = vars(parser.parse_args())


def main(kwargs):
    unpack_zips(**kwargs)


if __name__ == '__main__':
    main(kwargs=args)









