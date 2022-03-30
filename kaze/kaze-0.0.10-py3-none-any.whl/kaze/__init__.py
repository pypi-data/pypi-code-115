import glob
import os.path
from collections import defaultdict

from kaze.file_utils import load_yml, cwd_ancestors
from kaze.utils import NamedList
from params_proto.neo_proto import ParamsProto, Proto


class Envs(ParamsProto, cli=False):
    KAZE_DATASETS_ROOT = Proto(env='KAZE_DATASETS_ROOT', default='$HOME/datasets')
    DATASETS_ROOT = Proto(env='DATASETS', default=KAZE_DATASETS_ROOT.value)


class Datasets(NamedList):
    def __init__(self, config_path=None):
        # todo: need to traverse parents
        if config_path is None:
            for d in cwd_ancestors():
                try:
                    config_path, = glob.glob(d + "/.kaze.yml")
                    break
                except Exception:
                    pass

        super().__init__()

        if config_path is None:
            return

        config = load_yml(config_path) or defaultdict(list)
        # config_lock = load_yml(".kaze-lock.yml") or defaultdict(list)

        for entry in config['datasets']:
            # resolve path
            self.add(**{k: os.path.expandvars(v)
                        for k, v in entry.items()})


datasets = Datasets()
