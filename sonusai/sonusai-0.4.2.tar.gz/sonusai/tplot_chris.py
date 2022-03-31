#! /usr/bin/env python3

from datetime import datetime

import h5py
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sh
import shutil
from docopt import docopt
from matplotlib.backends.backend_pdf import PdfPages

import sonusai
from sonusai.genft import genft
from sonusai.genmix import genmix
from sonusai.genmixdb import genmixdb
from sonusai.mixture import get_config_from_file
from sonusai.utils import trim_docstring

# define global constants
sample_rate = 16000
bit_depth = 16
channel_count = 1
sample_bytes = int(bit_depth / 8)
default_noise = '/etc/sonusai/whitenoise.wav'
default_snr = 80
# other global constants
trfrm_frame_samples = 64  # Aaware transform frame has 64 samples
dscale = 2 ** 15  # scaling for 16bit audio


def tplot_f(argv):
    """tplot

    usage: tplot [-hv] [-t TARGET] [-c CONFIG.YML] [-f FEAT] [--sedthr SEDTHR] [-m MODEL]

    options:
       -h, --help
       -v, --verbose            Be verbose.
       -t, --target TARGET      Target .wav or .txt, else use target section in config.yml
       -c, --config CONFIG.YML  genft config yaml file, optional.
       -f, --feature FEAT       feature override, i.e. gfh64to128
       -m, --model MODEL        Aaware .onnx model file
       --sedthr SEDTHR          sed thresholds override, i.e. [-30, -33, -36]

       Plot truth and waveforms for:
        1) TARGET .wav or .txt list file     if no CONFIG.YML: use default config
        2) TARGET .wav or .txt list file     CONFIG.YML: override default config with params from CONFIG.YML
        3) CONFIG.YML (no TARGET provided)   use CONFIG.YML (all targets & config params)

       A multi-page plot TARGET-truthplot.pdf or CONFIG-truthplot.pdf is generated.

       When both TARGET and CONFIG.YML files are provided, CONFIG.YML is expected to have parameters
       used to override the default configuration, thus it does not need to be a complete
       genmixdb config parameter set, only desired overrides like truth function its configs.

       Note a TARGET .txt list file supports the same format as sonusai genmixdb which is a
       list of regex expressions for finding sound files.

       Examples:
          tplot.py -t 4-esc50-dogbark.txt -c config.yml --sedthr '[-24, -27, -30]'
    """
    args = docopt(trim_docstring(tplot_f.__doc__), version=sonusai.__version__, options_first=True)

    # create tmp config file log output file in /tmp/
    now = datetime.now()
    cfg_fname = '/tmp/sonusai-tplot-{:%Y%m%d-%H%M%S}.yml'.format(now)
    try:
        shutil.copyfile('/etc/sonusai/tplot-ref.yml', cfg_fname)  # ref file in known place

    except shutil.Error as error:
        print('Could not create tmp config file, {}: {}'.format(cfg_fname, error))
        exit()

    cfg_default = get_config_from_file(cfg_fname)
    tgpath = []

    if args['--config']:
        cfarg = args['--config']
        try:
            cfg_cli = get_config_from_file(cfarg)
            cfn_base, cfn_ext = os.path.splitext(cfarg)
            head_tail = os.path.split(cfn_base)  # remove path
            oname = "./" + head_tail[1] + "-truthplot.pdf"
            tgpath = cfarg

        except Exception as e:
            print('Error opening config file: {}'.format(e))
            exit()

    else:
        if not args['--target']:
            print('Error: No target or config file provided, see --help')
            exit()

    if args['--target']:
        tfarg = args['--target']  # target filename arg
        if not os.path.exists(tfarg):
            sys.exit("Could not open target input file, exiting.")

        tfn_base, tfn_ext = os.path.splitext(tfarg)
        cfg_default['targets'][0]['target_name'] = tfarg
        if tfn_ext.lower() == '.wav':
            print('Generating truth for single .wav file {}'.format(tfarg))
        else:
            print('Generating truth for list file {}'.format(tfarg))

        head_tail = os.path.split(tfn_base)  # remove path
        oname = "./" + head_tail[1] + "-truthplot.pdf"
        tgpath = tfarg

    if args['--target'] and args['--config']:  # target with .yml overrides
        # Overwrite default only feature+truth parameters from provided config file
        # Retrieve feature + truth values and replace in config, use defaults by doing nothing
        if cfg_cli['feature']:
            if cfg_cli['feature'] != cfg_default['feature']:
                cfg_default['feature'] = cfg_cli['feature']
                print('Override feature to {} from file {}'.format(cfg_cli['feature'], cfarg))

        if cfg_cli['num_classes']:
            if cfg_cli['num_classes'] != cfg_default['num_classes']:
                cfg_default['num_classes'] = cfg_cli['num_classes']
                print('Override num_classes to {} from file {}'.format(cfg_cli['num_classes'], cfarg))

        if cfg_cli['truth_mode']:
            if cfg_cli['truth_mode'] != cfg_default['truth_mode']:
                cfg_default['truth_mode'] = cfg_cli['truth_mode']
                print('Override truth_mode to {} from file {}'.format(cfg_cli['truth_mode'], cfarg))

        if cfg_cli['truth_index']:
            if cfg_cli['truth_index'] != cfg_default['truth_index']:
                cfg_default['truth_index'] = cfg_cli['truth_index']
                print('Override truth_index to {} from file {}'.format(cfg_cli['truth_index'], cfarg))

        if cfg_cli['truth_function']:
            if cfg_cli['truth_function'] != cfg_default['truth_function']:
                cfg_default['truth_function'] = cfg_cli['truth_function']
                print('Override truth_function to {} from file {}'.format(cfg_cli['truth_function'], cfarg))

        if cfg_cli['truth_config']:
            if cfg_cli['truth_config'] != cfg_default['truth_config']:
                cfg_default['truth_config'] = cfg_cli['truth_config']
                print('Override truth_config to {} from file {}'.format(cfg_cli['truth_config'], cfarg))

    # if no target file use all the specified config file
    if args['--config'] and not args['--target']:
        try:
            shutil.copyfile(cfarg, cfg_fname)  # copy cli cfg file over default
            cfg_default = get_config_from_file(cfg_fname)

        except shutil.Error as error:
            print('Could not copy/read specified config file, {}: {}'.format(cfarg, error))
            exit()

        print('No target file specified, using full config from file {}'.format(cfarg))

    if not args['--config'] and args['--target']:
        print('Using default feature+truth config, see {}'.format(cfg_fname))

    ######## Apply command line config override
    if args['--sedthr']:
        sedthr = json.loads(args['--sedthr'])
        if sedthr != cfg_default['truth_config']['thresholds']:
            cfg_default['truth_config']['thresholds'] = sedthr
            print('Override global sedthr config with cli arg {}'.format(sedthr))

    if args['--feature']:
        # TBD need to change featval_def with read of whatever is there
        # sh.sed("-i","s/feature: "+featval_def+"/feature: "+args['--feature']+"/",cfg_fname)
        if args['--feature'] != cfg_default['feature']:
            cfg_default['feature'] = args['--feature']
            print('Override feature with cli arg {}'.format(args['--feature']))

    ########## Run genmixdb and genmix and read results ########
    mixdb = genmixdb(cfg_default)
    NM = len(mixdb['mixtures'])  # Number of mixtures
    print('Generating data for {} mixture plots'.format(NM))
    mxwav, tr_t, tgwav, noise, segsnr_t, mixdbo = genmix(mixdb=mixdb,
                                                         mixid=':',
                                                         compute_segsnr=True,
                                                         compute_truth=True,
                                                         logging=False)

    featdat, tr_f, segsnr_f, _ = genft(mixdb=mixdb,
                                       mixid=':',
                                       compute_segsnr=True,
                                       logging=False)

    (F, NCL) = tr_f.shape  # Total # of feature frames and # classes
    NMS = mxwav.shape[0]  # Total number of samples over all mixtures
    NFR = featdat.shape[0]  # Total transform frames over all mixtures
    frame_ms = float(mixdb['frame_size']) / float(sample_rate / 1000)
    feature_ms = float(mixdb['feature_samples']) / float(sample_rate / 1000)

    ######## If model provided, read and check it
    pred_enable = False
    pr_f = np.zeros(0)
    if args['--model']:
        import onnx
        marg = args['--model']
        onnx_model = onnx.load(marg)  # onnx_model is an in-memory ModelProto
        num_mdatprops = len(onnx_model.metadata_props)  # number of metadata entries (5)
        pred_enable = True
        if num_mdatprops < 5:
            print('Error: Model metadata indicates this is not an Aaware model, ignoring.')
            pred_enable = False
        else:
            if onnx_model.metadata_props[4].key != 'feature':
                print('Error: metadata does not have Aaware feature, ignoring.')
                pred_enable = False
            else:
                model_feature = onnx_model.metadata_props[4].value
                print('Model feature is {}'.format(model_feature))
                # TBD check and read other params, flatten, addch, etc.
                print('Running prediction with {}'.format(marg))
                opath = '/tmp'
                mfid = h5py.File(opath + '/tplot-featdat.h5', 'w')
                mfid.create_dataset('feature', data=featdat)
                # mfid.create_dataset('vtruth', data=vtruth)
                mfid.close()
                sh.rm("-rf", opath + "/predict")
                sh.sonusai_predict("-n", "-m" + marg, "-i" + opath + "/tplot-featdat.h5", "-o" + opath + "/predict")
                h5pf = h5py.File(opath + "/predict/predict.h5", 'r')
                pr_f = np.array(h5pf['predict'])
                h5pf.close()
                sh.rm("-rf", opath + "/predict")
                sh.rm("-rf", opath + '/tplot-featdat.h5')

    print('Plotting {} target-truth results to {}\n\n'.format(NM, oname))
    pdf = PdfPages('{}'.format(oname))
    for mi in range(NM):
        mxbegin = mixdbo['mixtures'][mi]['i_sample_offset']
        fbegin = mixdbo['mixtures'][mi]['o_frame_offset']
        # For each target/mixture, get index endpoint (mix,noise,target sample,...)
        if mi == NM - 1:
            mxend = NMS
            fend = F
            ifend = NFR
        else:
            mxend = mixdbo['mixtures'][mi + 1]['i_sample_offset']
            # out frames are possibly decimated/stride-combined
            fend = mixdbo['mixtures'][mi + 1]['o_frame_offset']
            # in frames are transform
            ifend = mixdbo['mixtures'][mi + 1]['i_frame_offset']

        # Trim waveform data,
        mx = mxwav[mxbegin:mxend] / dscale
        tt = tgwav[mxbegin:mxend] / dscale
        # Provide subset defined by mixture using tridx array of indices (multi-channel truth)
        tridx = np.array(mixdbo['targets'][mixdbo['mixtures'][mi]['target_file_index']]['truth_index'][0]) - 1
        tr = tr_f[fbegin:fend, tridx]

        if pr_f.shape[0] > 0:
            pr = pr_f[fbegin:fend, :]
            # Prediction Activity analysis to select top prediction class
            pr_act = np.any(pr >= mixdb['class_weights_threshold'], axis=0)  # true if active in any frame
            pr_actidx = np.array([i for i, x in enumerate(pr_act) if x]) + 1
            print('Prediction active in classes based on threshold {}: \n{}'.
                  format(mixdb['class_weights_threshold'], pr_actidx))
            pr_mean = np.mean(pr, axis=0)
            top_active_classes = np.argsort(pr_mean)[::-1] + 1
            print('Top 10 active prediction classes by mean:\n{}'.format(top_active_classes[0:10]))
            pr = pr[:, top_active_classes[0] - 1]  # plot most active prediction
            print('Plotting prediction class {}'.format(top_active_classes[0]))

        # Setup plot of target waveform with truth on top
        # ----------- TBD make a func w/args mx, tt, tr_f, pr, mixdat, mi, tridx, tgpath -----------
        # plt.figure(figsize=(10, 8))
        # calc # samples per frame for plotting, should be int but check anyway
        NPLOTF = tr.shape[0]
        NPLOTSPF = int(np.floor(len(tt) / NPLOTF))
        NPLOTSAM = int(NPLOTSPF * NPLOTF)  # number of plot samples multiple of frames
        secu = np.arange(NPLOTSAM, dtype=np.float32) / sample_rate  # x-axis in sec
        NPTCL = tr.shape[1]  # Number of plot truth classes
        # Reshape/extend truth to #samples in waveform
        trex = np.reshape(np.tile(np.expand_dims(tr, 1), [1, NPLOTSPF, 1]), [NPLOTSAM, NPTCL])

        fig, ax0 = plt.subplots(1, 1, constrained_layout=True, figsize=(11.69, 8.27))
        ax = np.array([ax0], dtype=object)
        plots = []

        # Plot the time-domain waveforms then truth/prediction on second axis
        if mx.shape[0] > 0:
            color = 'mistyrose'
            mix_plot, = ax[0].plot(secu, mx[0:NPLOTSAM], color=color, label='MIX')
            ax[0].tick_params(axis='y', labelcolor='red')
            plots.append(mix_plot)

        if tt.shape[0] > 0:
            color = 'tab:blue'
            tt_plot, = ax[0].plot(secu, tt[0:NPLOTSAM], color=color, label='TAR')
            ax[0].set_ylabel('ampl', color=color)
            ax[0].tick_params(axis='y', labelcolor=color)
            plots.append(tt_plot)

        ax2 = ax[0].twinx()  # instantiate 2nd y axis that shares the same x-axis

        if tr.shape[0] > 0:  # Plot first truth TBD support multi-channel
            color = 'tab:green'
            label2 = 'truth{}'.format(tridx[0] + 1)
            ax2.set_ylabel(label2, color=color)  # we already handled the x-label with ax1
            # print('Mixture num {}, tridx={}'.format(mi,tridx))
            tr_plot, = ax2.plot(secu, trex[:, 0], color=color, label=label2)
            ax2.set_ylim([-0.05, 1.05])
            ax2.tick_params(axis='y', labelcolor=color)
            plots.append(tr_plot)

        if pr_f.shape[0] > 0:
            color = 'tab:brown'
            label2 = 'prcl{}'.format(top_active_classes[0])
            ax2.set_ylabel(label2, color=color)  # we already handled the x-label with ax1
            prex = np.reshape(np.tile(np.expand_dims(pr, 1), [1, NPLOTSPF, 1]), [NPLOTSAM, NPTCL])
            pr_plot, = ax2.plot(secu, prex, color=color, label=label2)
            ax2.set_ylim([-0.05, 1.05])
            ax2.tick_params(axis='y', labelcolor=color)
            # nno_plot, = ax1.plot(secu, nnoex[:,1], 'k', label='NN Predict All')
            plots.append(pr_plot)

        ax[0].set_xlabel('time (s)')  # set pnly on last/bottom plot
        # ax[0].legend(handles=plots, bbox_to_anchor=(1.15, 1.0), loc='upper left')

        # Get actual mixture target config parameters
        tgfname = mixdb['targets'][mixdb['mixtures'][mi]['target_file_index']]['name']
        taugm = mixdb['target_augmentations'][mixdb['mixtures'][mi]['target_augmentation_index']]
        tridx = str(mixdb['targets'][mixdbo['mixtures'][mi]['target_file_index']]['truth_index'][0])
        tfunc = mixdb['targets'][mixdbo['mixtures'][mi]['target_file_index']]['truth_function'][0]
        tcfg = mixdb['targets'][mixdbo['mixtures'][mi]['target_file_index']]['truth_config']
        # taugm = mixdb['target_augmentations'][taugi]

        fig.suptitle('{} of {}: {}\n{}\nTarget aug: {}\nTruth indices: {}\nGlobal Truth Function:Config {} : {}'
                     .format(mi + 1, NM, tgpath, tgfname, taugm, tridx, tfunc, tcfg), fontsize=10)
        # fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    # open config file read in as text, then print to last page
    logf = open(cfg_fname, "r")
    logtxt = logf.read()
    cmdtxt = 'Command:   {}\n'.format(' '.join(sys.argv))
    lastPage = plt.figure(figsize=(11.69, 8.27))
    lastPage.clf()
    # txt = 'Configuration details:'
    lastPage.text(0.05, 0.95, cmdtxt + logtxt, transform=lastPage.transFigure, size=10, ha="left", va="top")
    pdf.savefig()
    plt.close()

    pdf.close()
    # h5f.close()
    # sh.rm(tf_base+".h5")         # remove temp ft files
    # sh.rm(tf_base+".log")
    # sh.rm(tf_base+"-genft.log")
    os.remove(cfg_fname)  # remove temp config file


if __name__ == '__main__':
    import sys

    tplot_f(sys.argv)
