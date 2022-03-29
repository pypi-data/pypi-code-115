# -*- coding: utf-8 -*-
import os
import numpy as np

import fractalshades as fs
import fractalshades.models as fsm

import fractalshades.colors as fscolors
from fractalshades.postproc import (
    Postproc_batch,
    Continuous_iter_pp,
    DEM_normal_pp,
    DEM_pp,
    Raw_pp,
)
from fractalshades.colors.layers import (
    Color_layer,
    Bool_layer,
    Normal_map_layer,
    Virtual_layer,
    Blinn_lighting,
)


def plot(plot_dir):
    
    fractal = fsm.Perturbation_burning_ship(plot_dir)
    calc_name = 'test'
    _1 = 'Zoom parameters'
    x = '0.970193665269692902532075329102164006969265453931619299869092310940164086795599366134840255511363955171038910126654241597171394248685321639381364916297907254780241722434065232326234915838933422262781164401625359739191002965931635730199812758722291111706869293733226373468810716227643072586589137702771321943511832074912922279563095526782820714964032633039698852400236704874722320455372124231859218077809746056717666859221129056498448553172153456220373414078134468853732108402893685008321662905454306421'
    y = '1.21850295274166974285702071299767293230448362783030256370418850426357812057287765795952909924874314330508539969297886115274649834200989268894208451239482225013300749456502263345911904061918405882267247319640688051306115980517738668779489717879501797247258224809897775280770852170258524412633558130505883724476866966974371473251563448410252590223833273123652952200132788056694464942551320989013925952175665055440557610052497527253547022960443081777458813806836350419852744739668281970810865926085518542'
    dx = '1.0e-314'
    xy_ratio = 1.0
    theta_deg = 0.0
    dps = 500
    nx = 3200
    _1b = 'Skew parameters /!\\ Re-run when modified!'
    has_skew = True
    skew_00 = 0.7270379024905976
    skew_01 = 0.46070490548507187
    skew_10 = 0.23453177132939212
    skew_11 = 1.524060759071476
    _2 = 'Calculation parameters'
    max_iter = 500000
    _3 = 'Bilinear series parameters'
    eps = 1e-06
    _4 = 'Plotting parameters: base field'
    base_layer = "distance_estimation"#"continuous_iter"# 'distance_estimation'
    interior_color = (0.1, 0.1, 0.1)
    colormap = fscolors.cmap_register["classic"]
    invert_cmap = False
    DEM_min = 1e-06
    cmap_z_kind = 'relative'
    zmin = 0.0
    zmax = 0.5
    _5 = 'Plotting parameters: shading'
    shade_kind = 'glossy'
    gloss_intensity = 10.0
    light_angle_deg = 65.0
    light_color = (1.0, 1.0, 1.0)
    gloss_light_color = (1.0, 1.0, 1.0)
  
    fractal.zoom(precision=dps, x=x, y=y, dx=dx, nx=nx, xy_ratio=xy_ratio,
         theta_deg=theta_deg, projection="cartesian", antialiasing=False,
         has_skew=has_skew, skew_00=skew_00, skew_01=skew_01,
         skew_10=skew_10, skew_11=skew_11
    )
    fractal.calc_std_div(
        calc_name=calc_name,
        subset=None,
        max_iter=max_iter,
        M_divergence=1.e3,
        BLA_params={"eps": eps},
    )

    if fractal.res_available():
        print("RES AVAILABLE, no compute")
    else:
        print("RES NOT AVAILABLE, clean-up")
        fractal.clean_up(calc_name)

    fractal.run()

    pp = Postproc_batch(fractal, calc_name)
    
    if base_layer == "continuous_iter":
        pp.add_postproc(base_layer, Continuous_iter_pp())
    elif base_layer == "distance_estimation":
        pp.add_postproc("continuous_iter", Continuous_iter_pp())
        pp.add_postproc(base_layer, DEM_pp())

    pp.add_postproc("interior", Raw_pp("stop_reason",
                    func=lambda x: x != 1))
    if shade_kind != "None":
        pp.add_postproc("DEM_map", DEM_normal_pp(kind="potential"))

    plotter = fs.Fractal_plotter(pp)   
    plotter.add_layer(Bool_layer("interior", output=False))

#    if field_kind == "twin":
#        plotter.add_layer(Virtual_layer(
#                "fieldlines", func=None, output=False
#        ))
#    elif field_kind == "overlay":
#        plotter.add_layer(Grey_layer(
#                "fieldlines", func=None, output=False
#        ))

    if shade_kind != "None":
        plotter.add_layer(Normal_map_layer(
            "DEM_map", max_slope=60, output=True
        ))

    if base_layer != 'continuous_iter':
        plotter.add_layer(
            Virtual_layer("continuous_iter", func=None, output=False)
        )

    sign = {False: 1., True: -1.}[invert_cmap]
    if base_layer == 'distance_estimation':
        cmap_func = lambda x: sign * np.where(
           np.isinf(x),
           np.log(DEM_min),
           np.log(np.clip(x, DEM_min, None))
        )
    else:
        cmap_func = lambda x: sign * np.log(x)

    plotter.add_layer(Color_layer(
            base_layer,
            func=cmap_func,
            colormap=colormap,
            probes_z=[zmin, zmax],
            probes_kind=cmap_z_kind,
            output=True))
    plotter[base_layer].set_mask(
        plotter["interior"], mask_color=interior_color
    )
    if shade_kind != "None":
        light = Blinn_lighting(0.4, np.array([1., 1., 1.]))
        light.add_light_source(
            k_diffuse=0.8,
            k_specular=.0,
            shininess=350.,
            angles=(light_angle_deg, 20.),
            coords=None,
            color=np.array(light_color))

        if shade_kind == "glossy":
            light.add_light_source(
                k_diffuse=0.2,
                k_specular=gloss_intensity,
                shininess=400.,
                angles=(light_angle_deg, 20.),
                coords=None,
                color=np.array(gloss_light_color))

        plotter[base_layer].shade(plotter["DEM_map"], light)

    plotter.plot()



if __name__ == "__main__":
    realpath = os.path.realpath(__file__)
    plot_dir = os.path.splitext(realpath)[0]
    plot(plot_dir)

"""
Resolution
iter 0 :

"""
