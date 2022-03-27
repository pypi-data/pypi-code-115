try:
    from PyQt5 import QtWidgets
    from propeller_design_tools.helper_ui_subclasses import PDT_Label, PDT_GroupBox, PDT_ComboBox
    from propeller_design_tools.helper_ui_classes import SingleAxCanvas
except:
    pass


class PropellerSweepWidget(QtWidgets.QWidget):
    def __init__(self):
        super(PropellerSweepWidget, self).__init__()
        main_lay = QtWidgets.QHBoxLayout()
        self.setLayout(main_lay)

        left_lay = QtWidgets.QVBoxLayout()
        center_lay = QtWidgets.QVBoxLayout()
        right_lay = QtWidgets.QVBoxLayout()
        main_lay.addLayout(left_lay)
        main_lay.addLayout(center_lay)
        main_lay.addLayout(right_lay)

        # left layout
        left_lay.addStretch()
        exist_data_grp = PDT_GroupBox('Existing Data (plot controls)')
        exist_data_grp.setMinimumSize(400, 250)
        exist_data_grp.setLayout(QtWidgets.QVBoxLayout())
        left_lay.addWidget(exist_data_grp)
        left_lay.addStretch()
        add_data_grp = PDT_GroupBox('Add Data Points By Range')
        add_data_grp.setMinimumSize(400, 250)
        add_data_grp.setLayout(QtWidgets.QVBoxLayout())
        left_lay.addWidget(add_data_grp)
        left_lay.addStretch()

        # center layout
        select_prop_cb = PDT_ComboBox(width=200)
        select_prop_cb.setEnabled(False)
        select_prop_cb.currentTextChanged.connect(self.select_prop_cb_changed)
        center_lay.addStretch()
        center_top_lay = QtWidgets.QHBoxLayout()
        center_top_lay.addStretch()
        center_top_lay.addWidget(PDT_Label('Select Propeller:', font_size=14, bold=True))
        center_top_lay.addWidget(select_prop_cb)
        center_top_lay.addStretch()
        center_lay.addLayout(center_top_lay)
        self.wvel_3d_canvas = wvel_3d_canvas = SingleAxCanvas(projection='3d', height=6, width=6)
        center_lay.addWidget(wvel_3d_canvas)

        # right layout
        metric_lay = QtWidgets.QHBoxLayout()
        x_param_cb = PDT_ComboBox(width=150)
        y_param_cb = PDT_ComboBox(width=150)
        metric_lay.addStretch()
        metric_lay.addWidget(PDT_Label('Plot Metric:', font_size=14, bold=True))
        metric_lay.addStretch()
        metric_lay.addWidget(y_param_cb)
        metric_lay.addWidget(PDT_Label('vs'))
        metric_lay.addWidget(x_param_cb)
        metric_lay.addStretch()
        right_lay.addLayout(metric_lay)
        self.metric_canvas = metric_canvas = SingleAxCanvas()
        right_lay.addWidget(metric_canvas)

    def select_prop_cb_changed(self):
        pass

