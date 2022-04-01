from ska_low_cbf_fpga import FpgaPersonality

from ab_nic_sw.hbm_packet_controller import HbmPacketController
from ab_nic_sw.ptp import Ptp


class AbNicFpga(FpgaPersonality):
    _peripheral_class = {
        "timeslave": Ptp,
        "timeslave_b": Ptp,
        "hbm_pktcontroller": HbmPacketController,
    }
