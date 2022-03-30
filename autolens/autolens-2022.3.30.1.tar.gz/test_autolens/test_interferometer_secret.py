import autolens as al


def test___fit_figure_of_merit__different_settings(
    interferometer_7, interferometer_7_lop
):

    pix = al.pix.Rectangular(shape=(3, 3))
    reg = al.reg.Constant(coefficient=0.01)

    g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

    tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

    fit = al.FitInterferometer(
        dataset=interferometer_7,
        tracer=tracer,
        settings_inversion=al.SettingsInversion(
            use_w_tilde=True, use_linear_operators=False
        ),
    )
