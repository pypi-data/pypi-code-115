import subprocess
from pathlib import Path
from sys import platform

from .colors import Colors
from .layers import Begin, End, Head, Layer
from .styles import Ball, Box, PDFExport, RightBandedBox


class Architecture:
    def __init__(self, depth_factor: float):
        self.layers_list: list[Layer] = []
        self.depth_factor = depth_factor

    def add(self, layer: Layer):
        self.layers_list.append(layer)

    @property
    def lastname(self):
        return self.layers_list[-1].name

    def to_pdf(self, pathname: str):
        path = Path(f"{pathname}.tex")
        path.parents[0].mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(Head(".").text())
            f.write(Colors().text())
            f.write(Begin().text())

            last_to = "(0,0,0)"
            for idx, c in enumerate(self.layers_list):
                if hasattr(c, "to") and not c.to:
                    c.to = last_to

                f.write(c.text(self.depth_factor, idx))

                last_to = f"({c.name}-east)"

            f.write(End().text())

        Ball().generate()
        RightBandedBox().generate()
        Box().generate()

        PDFExport("to_pdf.sh").export(pathname)

        subprocess.Popen(f"bash to_pdf.sh {pathname}", shell=True).wait()

        Path("to_pdf.sh").unlink()

        if platform == "linux" or platform == "linux2":
            subprocess.Popen(f"xdg-open {pathname}.pdf", shell=True).wait()
        elif platform == "darwin":
            subprocess.Popen(f"open {pathname}.pdf", shell=True).wait()
        elif platform == "win32":
            subprocess.Popen(f"start {pathname}.pdf", shell=True).wait()
        else:
            raise EnvironmentError("Unknown platform")
