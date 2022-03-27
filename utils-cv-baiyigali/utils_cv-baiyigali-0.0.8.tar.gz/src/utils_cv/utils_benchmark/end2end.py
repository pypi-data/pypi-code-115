import pandas as pd
from nltk import edit_distance

def get_match_num(texts_gt, texts_pd, ed_thresh=0):
    """
    texts_gt: [text1, text2], ground truth texts on one page
    texts_pd: [text1, text2], predicted texts on one page
    """    
    texts_gt = ' '.join(texts_gt).split()
    texts_pd = ' '.join(texts_pd).split()
    texts_pd = list(texts_pd) # copy
    texts_gt = list(texts_gt)
    texts_pd = sorted(texts_pd)
    texts_gt = sorted(texts_gt)

    num_tp = 0
    pop_list = []
    for i, text_gt in enumerate(texts_gt):
        for j, text_pd in enumerate(texts_pd):
            if text_gt == text_pd:
                texts_pd.pop(j)
                num_tp += 1
                pop_list.append(i)
                break

    texts_gt = [texts_gt[i] for i in range(len(texts_gt)) if i not in pop_list]

    for text_gt in texts_gt:
        for j, text_pd in enumerate(texts_pd):
            if edit_distance(text_gt, text_pd) <= ed_thresh:
                texts_pd.pop(j)
                num_tp += 1
                break

    return num_tp

def get_prf(texts_gt, texts_pd, ed_thresh=0):
    """
    texts_gt: [texts1, texts2], texts1 is ground truth texts on page1
    texts_pd: [texts1, texts2], texts1 is predicted texts on page1
    """
    assert len(texts_gt) == len(texts_pd)

    def prf(gt_n, pd_n, match_n):
        p = pd_n / match_n
        r = gt_n / match_n
        f = p * r * 2 / (p + r)
        return p, r, f

    # per page prf
    gt_n = [len(texts) for texts in texts_gt]
    pd_n = [len(texts) for texts in texts_pd]
    match_n = [get_match_num(texts_gt[i], texts_pd[i], ed_thresh=ed_thresh) for i in range(len(texts_gt))]
    per_page_prf = [prf(gt_n[i], pd_n[i], match_n[i]) for i in range(len(gt_n))]

    # total average prf
    total_match_n = sum(match_n)
    total_gt_n = sum(gt_n)
    total_pd_n = sum(pd_n)
    precision, recall, fscore = prf(total_gt_n, total_pd_n, total_match_n)

    results = {
        'precision': precision,
        'recall': recall,
        'fscore': fscore,
        'per_page_gt_n': gt_n,
        'per_page_pd_n': pd_n,
        'per_page_match_n': match_n,
        'per_page_prf': per_page_prf,
    }

    return results

def benchmark(df, ed_thresh=0):
    """
    df: dataframe must include keys, texts_gt and texts_pd, each row of them represents ground truth and prediction texts in one page
    """
    eps =  1e-12
    df = df.copy()

    df['texts_gt'] = df['texts_gt'].apply(lambda x: [str(s) for s in x])
    df['texts_pd'] = df['texts_pd'].apply(lambda x: [str(s) for s in x])

    df['texts_gt'] = df['texts_gt'].apply(lambda x: ' '.join(x).split())
    df['texts_pd'] = df['texts_pd'].apply(lambda x: ' '.join(x).split())

    df['match_num'] = df.apply(lambda row: get_match_num(row['texts_gt'], row['texts_pd'], ed_thresh=ed_thresh), axis=1)
    df['num_pd'] = df['texts_pd'].apply(len)
    df['num_gt'] = df['texts_gt'].apply(len)
    df['precision'] = df['match_num']/(df[f'num_pd'] + eps)
    df['recall'] = df['match_num']/(df[f'num_gt'] + eps)
    df['fmeasure'] = 2 * df['precision']*df['recall'] / (df['precision'] + df['recall']  + eps)

    precision_ = df['match_num'].sum()/(df[f'num_pd'].sum() + eps)
    recall_ = df['match_num'].sum()/(df[f'num_gt'].sum() + eps)
    fmeasure_ = precision_ * recall_ * 2 / (precision_ + recall_  + eps)

    return precision_, recall_, fmeasure_, df
