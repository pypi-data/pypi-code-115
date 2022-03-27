

import os
import shap
import joblib
import collections
import pandas as pd
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import RepeatedStratifiedKFold,cross_val_score
from matplotlib import pyplot as plt
import seaborn as sns

from sklearn.metrics import  accuracy_score, plot_confusion_matrix, confusion_matrix


# model = LinearDiscriminantAnalysis()
cv = RepeatedStratifiedKFold(n_splits = 10, n_repeats=3, random_state=1)
drop_columns = [
            'Group', 'aln_base', 
            'SymPval', 'MarPval', 
            'IntPval'
        ]


flat_path = '/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/flatfishes'

## flatfishes
iris = pd.read_csv(
    os.path.join(flat_path, 'newProps_features_991exons_fishlife_labels.tsv'),
    sep = '\t')
## flatfishes

for c in drop_columns:
    try:
        iris = iris.drop( c, 1 )
    except KeyError:
        pass

# ## flatfishes
iris = iris[ (iris['tree_id']  == 1) |  (iris['tree_id']  == 10)]
# ## flatfishes


y = iris['tree_id'] == 1
X = iris.drop('tree_id', axis=1)


LDA_clf = LinearDiscriminantAnalysis().fit(X, y)
accuracy = accuracy_score(y, LDA_clf.predict(X))


flat_xgboost_clf = joblib.load(os.path.join(flat_path, "new_Proprs_h1_h10.sav"))
# flat_xgboost_clf.classes_



## prota processing

prota_path = "/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/prota"
prota_drop = ['group', 'rank', 'au_test']

prota_features = pd.read_csv(
                    os.path.join(prota_path, 'features_prota_original.tsv'),
                    sep='\t'
                )
prota_labels = pd.read_csv('/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/prota/joined_out_ggi_1024exons.tax_prop80_TreeId.tsv', sep = '\t')



# prota_labels_c = (prota_labels[prota_labels['rank'] == 1]
#                     .rename(columns={'alignment': 'aln_base'})
#                     .drop(prota_drop, 1)
#                     .reset_index().drop(['index'], 1))

prota_rank1 = prota_labels[prota_labels['rank'] == 1]
prota_H_selected = ( prota_rank1[ (prota_rank1['tree_id'] == 1) | (prota_rank1['tree_id'] == 2) ]
                        .rename(columns={'alignment': 'aln_base'})
                        .drop(prota_drop, 1)
                        .reset_index()
                        .drop(['index'], 1)
                    )

Xy = prota_features.merge(prota_H_selected, on = 'aln_base')

y2 = Xy['tree_id'] == 1


for c in drop_columns:
    try:
        Xy = Xy.drop( c, 1 )
    except KeyError:
        pass

X2 = Xy.drop(['tree_id'], 1)




LDA_clf2 = LinearDiscriminantAnalysis().fit(X2, y2)
accuracy2 = accuracy_score(y2, LDA_clf2.predict(X2))


prota_xgboost_clf = joblib.load(os.path.join(prota_path, "post_ggi_h1_h2.sav"))


# prota_xgboost_clf.classes_

# plot_confusion_matrix(
#     prota_xgboost_clf, X2, y2,
#     values_format  = 'd',
#     display_labels = ["H2", "H1"]
# )



# plt.rcParams["figure.figsize"] = (18, 15)
# plt.rcParams["figure.dpi"] = 400

# plot_confusion_matrix(
#     LDA_clf2, X2, y2,
#     values_format  = 'd',
#     # display_labels = ["H%s" % i for i in LDA_clf2.classes_]
# )

# plt.savefig("/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/prota/lda_prota.png", bbox_inches = 'tight')
# plt.close()


plt.rcParams["figure.figsize"] = (18, 5)
plt.rcParams["figure.dpi"] = 400



mytables = [
    [X2, y2, LDA_clf2         , ("H2" , "H1")],
    [X,   y, LDA_clf          , ('H10', 'H1')],
    [X2, y2, prota_xgboost_clf, ("H2" , "H1")],
    [X,   y, flat_xgboost_clf , ('H10', 'H1')],
]

prota_xgboost_clf.__str__().startswith('XGBClassifier')
LDA_clf2.__str__().startswith('XGBClassifier')


plt.rcParams["figure.figsize"] = (9.68, 8.5)

width = 9.68
height = 8.5 + 1.5


width = 12
height = 10

f,axes = plt.subplots(nrows = 2, ncols = 2, figsize=(width, height), dpi = 200)
ax = axes.flatten()

for i in range(len(mytables)):
    tmp_X, tmp_y, tmp_model, tmp_labels = mytables[i]

    tmp_score  = round(accuracy_score( tmp_y, tmp_model.predict(tmp_X) ), 4)
    cnf_matrix = confusion_matrix(tmp_y, tmp_model.predict(tmp_X))

    ones = np.ones( (cnf_matrix.shape[0], 1) )
    B    = (cnf_matrix.dot(ones)**-1).flatten()
    cnf_rowise = (cnf_matrix.T.dot( np.diag( B ) ).T * 100).round(2)

    box_combined_arr = np.asarray([

        f"{n}\n{per}%" for n,per in zip( cnf_matrix.flatten(), cnf_rowise.flatten() )
    ]).reshape(2,2)

    sns.heatmap(
        cnf_rowise, 
        annot = box_combined_arr,
        fmt   = '', 
        cmap  = 'viridis',
        xticklabels = tmp_labels,
        yticklabels = tmp_labels,
        ax=ax[i]
    )
    ax[i].set_xlabel('Predicted label')
    ax[i].set_ylabel('True label')
    ax[i].set_title('Accuracy: %s' % tmp_score)

plt.savefig(
    "/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/lda_vs_xgboost_v3.png", 
    bbox_inches = 'tight', 
    dpi = 250)
plt.close()








 
def shap_plot(model, all_num, labels, plot_size, color_bar, color = None):

    # xgb_clf_no_nor, all_num, new_prefix = xgb_clf_no_nor, all_num, new_prefix
    # bee_20_filename = "20best_beeswarm_%s.png" % new_prefix
    explainer   = shap.Explainer(model, all_num)
    shap_values = explainer(all_num)

    shap.plots.beeswarm(shap_values,
                        max_display = 20,
                        color = color,
                        plot_size = plot_size,
                        color_bar = color_bar,
                        color_bar_label = None,
                        show = False)

    right_label = labels[1]
    left_label = labels[0]

    plt.title(right_label, loc = 'right')
    plt.title(left_label, loc = 'left')
    plt.tight_layout(pad=0.05)


# shap_plot(prota_xgboost_clf, X2, ["H2" , "H1"])


from shap.plots._labels import labels
labels['VALUE'] = 'SHAP value'


xgboost_table = []

for i in range(len(mytables)):
    tmp_X, tmp_y, tmp_model, tmp_labels = mytables[i]

    if tmp_model.__str__().startswith('XGBClassifier'):
        xgboost_table.append([tmp_X, tmp_y, tmp_model, tmp_labels])
        


from matplotlib import gridspec


gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1.25]) 

index = 1
for i in range(len(xgboost_table)):
    tmp_X, tmp_y, tmp_model, tmp_labels = xgboost_table[i]

    # plt.subplot(1,2, index)
    plt.subplot(gs[i])

    if i + 1 == len(xgboost_table):
        shap_plot(
            tmp_model, 
            tmp_X, 
            tmp_labels, 
            plot_size = (10.68, 8.5),
            color_bar = True,
            color = plt.cm.get_cmap('viridis'),
            # color = None
            )
    else:
        shap_plot(
            tmp_model, 
            tmp_X, 
            tmp_labels, 
            plot_size = (10.68, 8.5),
            color_bar = False,
            color = plt.cm.get_cmap('viridis'),
            # color = None
            )

    index += 1

plt.savefig(
    "/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/xgboost_prota_flat_v3.png",
    dpi = 200)
plt.close()

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

def mypca_plot(
    score, 
    coeff,
    my_y,
    labels=None,
    xlabel='PC 1',
    ylabel='PC 2',
    legend = ['H0', 'H1']
     ):

    xs = score[:,0]
    ys = score[:,1]
    n = coeff.shape[0]
    scalex = 1.0/(xs.max() - xs.min())
    scaley = 1.0/(ys.max() - ys.min())
    # plt.grid()
    plt.hlines(0, -1,1,colors='gray')
    plt.vlines(0, -1,1,colors='gray')
    scatter = plt.scatter(xs * scalex, ys * scaley, c = my_y, alpha=0.75)
    plt.legend(
        handles = scatter.legend_elements()[0], labels = legend,
        loc='upper left'
        )

    # for i in range(n):
    #     plt.arrow(0, 0, coeff[i,0], coeff[i,1], color = 'black', alpha = 0.5)
    #     if labels is None:
    #         plt.text(coeff[i,0]* 1.15, coeff[i,1] * 1.15,
    #                  "Var"+str(i+1), color = 'black',
    #                   ha = 'center', va = 'center')
    #     else:
    #         plt.text(coeff[i,0]* 1.15, coeff[i,1] * 1.15,
    #                  labels[i], color = 'black',
    #                  ha = 'center', va = 'center')

    plt.xlim(-0.6,1)
    plt.ylim(-0.6,1)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    

pca_datasets = [
    [X2, y2,("H2" , "H1")],
    [X,   y, ('H10', 'H1')],
]



width = 11

# plt.rcParams["figure.figsize"] = (width, width/2)

# gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])
width = 10 + 0.1
height = 5

# plt.scatter()

f,axes = plt.subplots(nrows = 1, ncols = 2, figsize=(width, height), dpi = 200)
ax = axes.flatten()




for i in range(len(pca_datasets)):

    tmp_X, tmp_y, tmp_labels = pca_datasets[i]
    labels = tmp_X.columns

    scaler = StandardScaler()
    scaler.fit(tmp_X)
    X_transformed = scaler.transform(tmp_X)

    pca = PCA()
    X_new = pca.fit_transform(X_transformed)

    pca_ratios = pca.explained_variance_ratio_[0:2]

    xlabel = "PC1 (%s %%)" % round(pca_ratios[0]*100, 2)
    ylabel = "PC2 (%s %%)" % round(pca_ratios[1]*100, 2)

    # plt.subplot(gs[i])

    score  = X_new[:,0:2]
    coeff  = np.transpose(pca.components_[0:2, :])


    # colors = []
    # for h in tmp_y:
    #     if h:
    #         colors.append('blue')
    #     else:
    #         colors.append('red')
    

    xs = score[:,0]
    ys = score[:,1]
    n = coeff.shape[0]
    scalex = 1.0/(xs.max() - xs.min())
    scaley = 1.0/(ys.max() - ys.min())
    # plt.grid()
    ax[i].hlines(0, -1,1,colors='gray')
    ax[i].vlines(0, -1,1,colors='gray')
    scatter = ax[i].scatter(xs * scalex, ys * scaley, c = tmp_y, alpha=0.70)
    # scatter = ax[i].scatter(xs * scalex, ys * scaley, c = colors, alpha=0.75)
    ax[i].legend(
        handles = scatter.legend_elements()[0], labels = tmp_labels,
        loc='upper left'
        )
    ax[i].axis(xmin=-0.6,xmax=1, ymin = -0.6, ymax = 1)
    ax[i].set_xlabel(xlabel)
    ax[i].set_ylabel(ylabel)

plt.savefig(
    "/Users/ulises/Desktop/GOL/software/GGpy/proofs_ggi/pcas.png",
    dpi = 200)
plt.close()