from .tools import make_aligo, download
from . import thermal
from . import suspension
from . import actions
import importlib

aligo_katscript = importlib.resources.read_text("finesse_ligo.katscript", "aligo.kat")

from finesse.script.spec import make_element, KatSpec, make_analysis

spec = KatSpec()  # grabs existing instance
spec.register_element(make_element(suspension.LIGOTripleSuspension, "ligo_triple"))
spec.register_element(make_element(suspension.LIGOQuadSuspension, "ligo_quad"))
spec.register_analysis(
    make_analysis(actions.DARM_RF_to_DC, "darm_rf_to_dc"),
)
spec.register_analysis(
    make_analysis(actions.DRFPMI_state, "drfpmi_state"),
)

__all__ = ("make_aligo", "download", "thermal", "suspension", "actions")
