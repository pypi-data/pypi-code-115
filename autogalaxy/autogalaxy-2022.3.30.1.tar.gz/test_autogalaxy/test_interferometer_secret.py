import numpy as np
import pytest

import autogalaxy as ag


def test___fit_figure_of_merit__different_settings(
    interferometer_7, interferometer_7_lop
):

    pix = ag.pix.Rectangular(shape=(3, 3))
    reg = ag.reg.Constant(coefficient=0.01)

    g0 = ag.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

    plane = ag.Plane(galaxies=[ag.Galaxy(redshift=0.5), g0])

    fit = ag.FitInterferometer(
        dataset=interferometer_7,
        plane=plane,
        settings_inversion=ag.SettingsInversion(
            use_w_tilde=True, use_linear_operators=False
        ),
    )

    assert (fit.noise_map.slim == np.full(fill_value=2.0 + 2.0j, shape=(7,))).all()
    assert fit.log_evidence == pytest.approx(-66.90612, 1e-4)
    assert fit.figure_of_merit == pytest.approx(-66.90612, 1.0e-4)
