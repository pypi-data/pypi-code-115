import fire

from y5gg.train import run as train
from y5gg.val import run as val
from y5gg.detect import run as detect
from y5gg.export import run as export


def app() -> None:
    """Cli app."""
    fire.Fire(
        {
            "train": train,
            "val": val,
            "detect": detect,
            "export": export,
        }
    )
