from jupyterlite.addons.base import BaseAddon
from pathlib import Path

import json
import traitlets

# or importlib/pkginfo or wathever
DEFAULT_WHEELS = json.loads(
    (Path(__file__).parent / "wheels.json").read_text(encoding="utf-8")
)


from jupyterlite.addons.piplite import PipliteAddon as BasePipliteAddon

class RobotKernelAddon(BaseAddon):
    """Ensures the unique dependencies of robotkernel are available."""
    __all__ = ["post_init", "pre_build"]

    wheel_urls = traitlets.List(DEFAULT_WHEELS).tag(config=True)

    def post_init(self, manager):
        """update the root jupyter-lite.json with pipliteUrls"""
        import pdb; pdb.set_trace()

    def pre_build(self, manager):
        """Downloads wheels."""
        import pdb; pdb.set_trace()
        for wheel in self.wheel_urls():
            dest = self.output_dir / "pypi" / Path(wheel).name
            if dest.exists():
                continue
            yield dict(
                actions=[(self.fetch_one, [wheel, dest])],
                targets=[dest]
            )
