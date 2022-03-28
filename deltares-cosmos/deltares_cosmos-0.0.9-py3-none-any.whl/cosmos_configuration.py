# -*- coding: utf-8 -*-
"""
Created on Tue May 11 16:02:04 2021

@author: ormondt
"""

import os

import cht.xmlkit as xml
from .cosmos_main import cosmos


def read_config_file():
    
    main_path = cosmos.config.main_path
    
    config_file = os.path.join(main_path,
                               "configurations",
                               cosmos.config.config_file)
    
    # Defaults
    cosmos.config.ftp_hostname       = None
    cosmos.config.ftp_path           = None
    cosmos.config.ftp_username       = None
    cosmos.config.ftp_password       = None
    cosmos.config.webviewer_version  = None
    cosmos.config.sfincs_exe_path    = os.path.join(main_path, "exe", "sfincs")
    cosmos.config.hurrywave_exe_path = os.path.join(main_path, "exe", "hurrywave")
    cosmos.config.xbeach_exe_path    = os.path.join(main_path, "exe", "xbeach")
    cosmos.config.delft3dfm_exe_path = os.path.join(main_path, "exe", "delft3dfm")
    cosmos.config.cycle_interval     = 6
    cosmos.config.run_mode           = "serial"

    # Read xml config file
    xml_obj = xml.xml2obj(config_file)

    if hasattr(xml_obj, "ftp_hostname"):
        if hasattr(xml_obj.ftp_hostname[0],"value"):
            cosmos.config.ftp_hostname = xml_obj.ftp_hostname[0].value
    if hasattr(xml_obj, "ftp_path"):
        if hasattr(xml_obj.ftp_path[0],"value"):
            cosmos.config.ftp_path = xml_obj.ftp_path[0].value
    if hasattr(xml_obj, "ftp_username"):
        if hasattr(xml_obj.ftp_username[0],"value"):
            cosmos.config.ftp_username = xml_obj.ftp_username[0].value
    if hasattr(xml_obj, "ftp_password"):
        if hasattr(xml_obj.ftp_password[0],"value"):
            cosmos.config.ftp_password = xml_obj.ftp_password[0].value
    if hasattr(xml_obj, "webviewer_version"):
        cosmos.config.webviewer_version = xml_obj.webviewer_version[0].value
    if hasattr(xml_obj, "sfincs_exe_path"):
        cosmos.config.sfincs_exe_path = xml_obj.sfincs_exe_path[0].value
    if hasattr(xml_obj, "hurrywave_exe_path"):
        cosmos.config.hurrywave_exe_path = xml_obj.hurrywave_exe_path[0].value
    if hasattr(xml_obj, "xbeach_exe_path"):
        cosmos.config.xbeach_exe_path = xml_obj.xbeach_exe_path[0].value
    if hasattr(xml_obj, "delft3dfm_exe_path"):
        cosmos.config.delft3dfm_exe_path = xml_obj.delft3dfm_exe_path[0].value
    if hasattr(xml_obj, "cycle_interval"):
        cosmos.config.cycle_interval = xml_obj.cycle_interval[0].value

