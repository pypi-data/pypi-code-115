# -*- coding: utf-8 -*-
import sys
import numpy as np
sys.path.append('..')
from seqmetric.scheme import IOBS,IOBES,IOB2
from seqmetric.metrics import classification_report,f1_score

#场景1
mode = 2
trues = [['O', 'O', 'B-MISC', 'I-MISC', 'B-MISC', 'O', 'O'], ['B-PER', 'I-PER', 'O']]
preds = [['O', 'O', 'B-MISC', 'I-MISC', 'B-MISC', 'I-MISC', 'O'], ['B-PER', 'I-PER', 'O']]

if mode == 0:
    scheme = IOBES
elif mode == 1:
    scheme = IOBS
else:
    scheme = IOB2
f1 = f1_score(trues, preds, average='weighted',scheme=scheme)
report = classification_report(trues, preds, scheme=scheme,digits=4)
print(f1)
print(report)

from seqmetric.metrics import pt_class_report,pt_class_report_by_triple_list
#from seqmetric.metrics import pt_single_class_report as pt_class_report_pretty  兼容旧版本
# 场景2

label_list = ['0','1']
#label_id 0 , 1
trues = [[(0 , 10,20 ),], [(0 , 10,20)]] # label_id ,start ,end

preds = [[(0 , 10,20 ),],[]]

report ,f1 = pt_class_report_by_triple_list(trues,preds,label_list)
print(report ,f1)


print()

preds = {
    '0': [[(0 , 10,20 ),], [(0 , 10,20)]],
    '1': [
        [],
        []
    ]
}

trues = {
    '0': [[(0 , 10,20 )], [(0 , 10,20)]],
    '1': [[(0 , 10,20 )], [(0 , 10,20)]]
}



report ,f1 = pt_class_report(trues,preds,average='micro')
print(report ,f1)