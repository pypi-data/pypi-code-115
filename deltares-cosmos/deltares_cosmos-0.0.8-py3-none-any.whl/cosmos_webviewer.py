# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:28:48 2021

@author: ormondt
"""

import datetime
import os
from geojson import Point, Feature, FeatureCollection, dump
import io

from .cosmos_main import cosmos
from .cosmos_timeseries import merge_timeseries as merge

import cht.fileops as fo
import cht.misc_tools

class WebViewer:
    
    def __init__(self, name):

        self.name    = name
        self.path    = os.path.join(cosmos.config.main_path, "webviewers", name)
        self.version = cosmos.config.webviewer_version
        if fo.exists(self.path):
            self.exists = True
        else:
            self.exists = False
    
    def make(self):
        
        # Makes local copy of the web viewer
        # If such a copy already exists, data will be copied to the existing web viewer

        cosmos.log("")
        cosmos.log("Starting web viewer " + self.name +" ...")
        
        # Check whether web viewer already exists
        # If not, copy empty web viewer from templates
        if not self.exists:
            
            cosmos.log("Making new web viewer from " + self.version + " ...")

            fo.mkdir(self.path)

            template_path = os.path.join(cosmos.config.main_path,
                                         "templates",
                                         "webviewers",
                                         self.version,
                                         "*")
            fo.copy_file(template_path, self.path)

            # Change the title string in index.html to the scenario long name
            cht.misc_tools.findreplace(os.path.join(self.path, "index.html"),
                                       "COSMOS_VIEWER",
                                       cosmos.scenario.long_name)

        cosmos.log("Updating scenario.js ...")

        # Check if there is a scenarios.js file
        # If so, append it with the current scenario
        sc_file = os.path.join(self.path, "data", "scenarios.js")
        isame = -1
        if fo.exists(sc_file):
            scs = cht.misc_tools.read_json_js(sc_file)
            for isc, sc in enumerate(scs):
                if sc["name"] == cosmos.scenario.name:
                    isame = isc
        else:
            scs = []

        # Current scenario        
        newsc = {}
        newsc["name"]        = cosmos.scenario.name    
        newsc["long_name"]   = cosmos.scenario.long_name    
        newsc["description"] = cosmos.scenario.description    
        newsc["lon"]         = cosmos.scenario.lon    
        newsc["lat"]         = cosmos.scenario.lat
        newsc["zoom"]        = cosmos.scenario.zoom    
        newsc["cycle"]       = cosmos.cycle_time.strftime('%Y-%m-%dT%H:%M:%S')
        newsc["duration"]    = str(cosmos.scenario.run_duration)

        now = datetime.datetime.utcnow()
        newsc["last_update"] = now.strftime("%Y/%m/%d %H:%M:%S" + " (UTC)")

        if isame>-1:
            # Scenario already existed in web viewer
            scs[isame] = newsc
        else:
            # New scenario in web viewer    
            scs.append(newsc)        

        cht.misc_tools.write_json_js(sc_file, scs, "var scenario =")
        
        # Make scenario folder in web viewer
        scenario_path = os.path.join(self.path,
                                     "data",
                                     cosmos.scenario.name)
        fo.rmdir(scenario_path)
        fo.mkdir(os.path.join(scenario_path))
        fo.mkdir(os.path.join(scenario_path, "timeseries"))

        cosmos.log("Copying time series ...")
                
        # Stations and buoys
        
        # Set stations to upload (only upload for high-res nested models)
        for model in cosmos.scenario.model:
            
            all_nested_models = model.get_all_nested_models("flow")
            if all_nested_models:
                all_nested_stations = []
                for mdl in all_nested_models:
                    for st in mdl.station:
                        all_nested_stations.append(st.name)
                for station in model.station:
                    if station.type == "tide_gauge":
                        if station.name in all_nested_stations:
                            station.upload = False 
    
            all_nested_models = model.get_all_nested_models("wave")
            if all_nested_models:
                all_nested_stations = []
                for mdl in all_nested_models:
                    for st in mdl.station:
                        all_nested_stations.append(st.name)
                for station in model.station:
                    if station.type == "wave_buoy":
                        if station.name in all_nested_stations:
                            station.upload = False 
        
        # Tide stations

        features = []

        for model in cosmos.scenario.model:
            if model.station and model.flow:
                for station in model.station:                
                    if station.type == "tide_gauge" and station.upload:
                        
                        point = Point((station.longitude, station.latitude))
                        name = station.long_name + " (" + station.id + ")"
                        
                        # Check if there is a file in the observations that matches this station
                        obs_file = None
                        if cosmos.scenario.observations_path and station.id:
                            obs_pth = os.path.join(cosmos.config.main_path,
                                               "observations",
                                               cosmos.scenario.observations_path,
                                               "water_levels")                        
                            fname = "waterlevel." + station.id + ".observed.csv.js"
                            if os.path.exists(os.path.join(obs_pth, fname)):
                                obs_file = fname
                                                                        
                        features.append(Feature(geometry=point,
                                                properties={"name":station.name,
                                                            "long_name":name,
                                                            "id": station.id,
                                                            "mllw":station.mllw,
                                                            "model_name":model.name,
                                                            "model_type":model.type,
                                                            "obs_file":obs_file}))
                        
                        # Merge time series from previous cycles
                        # Go two days back
                        path = model.archive_path
                        t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
                        t1 = cosmos.cycle_time
                        v  = merge(path,
                                   station.name,
                                   t0=t0.replace(tzinfo=None),
                                   t1=t1.replace(tzinfo=None),
                                   prefix='waterlevel')
                        
                        v += model.vertical_reference_level_difference_with_msl
                        
                        csv_file = "waterlevel." + model.name + "." + station.name + ".csv.js"
                        csv_file = os.path.join(scenario_path,
                                                "timeseries",
                                                csv_file)
                        s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                     float_format='%.3f',
                                     header=False) 
                        
                        cht.misc_tools.write_csv_js(csv_file, s, 'var csv = `date_time,wl')
        
        # Save stations geojson file
        if features:
            feature_collection = FeatureCollection(features)
            stations_file = os.path.join(scenario_path,
                                    "stations.geojson.js")
            cht.misc_tools.write_json_js(stations_file, feature_collection, "var stations =")
                        

        # Wave buoys
    
        features = []
    
        for model in cosmos.scenario.model:
            if model.station and model.wave:
                for station in model.station:
                    if station.type == "wave_buoy" and station.upload:                
                        point = Point((station.longitude, station.latitude))
                        if station.ndbc_id:
                            name = station.long_name + " (" + station.ndbc_id + ")"
                        else:
                            name = station.long_name
                        features.append(Feature(geometry=point,
                                                properties={"name":station.name,
                                                            "long_name":name,
                                                            "id": station.ndbc_id,
                                                            "model_name":model.name,
                                                            "model_type":model.type}))
    
                        path = model.archive_path
                        t0 = cosmos.cycle_time - datetime.timedelta(hours=48)
                        t1 = cosmos.cycle_time
                        
                        # Hm0
                        v  = merge(path,
                                   station.name,
                                   t0=t0.replace(tzinfo=None),
                                   t1=t1.replace(tzinfo=None),
                                   prefix='hm0')
                        
                        # Write csv js file
                        csv_file = "hm0." + station.name + ".csv"
                        csv_file = os.path.join(scenario_path,
                                                "timeseries",
                                                csv_file)
                        s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                     float_format='%.3f')        
                        cht.misc_tools.write_csv_js(csv_file, s, "var csv = date_time,hm0`")
    
                        # Tp
                        v  = merge(path,
                                   station.name,
                                   t0=t0.replace(tzinfo=None),
                                   t1=t1.replace(tzinfo=None),
                                   prefix='tp')
                        
                        csv_file = "tp." + station.name + ".csv"
                        csv_file = os.path.join(scenario_path,
                                                "timeseries",
                                                csv_file)
                        s = v.to_csv(date_format='%Y-%m-%dT%H:%M:%S',
                                     float_format='%.3f')        
                        cht.misc_tools.write_csv_js(csv_file, s, "var csv = date_time,tp`")

        if features:
            feature_collection = FeatureCollection(features)
            buoys_file = os.path.join(scenario_path,
                                    "wavebuoys.geojson.js")
            cht.misc_tools.write_json_js(buoys_file, feature_collection, "var buoys =")
        
        # Map variables
        map_variables = []
        
        # Flood maps
        
        # Check if flood maps are available
        flood_map_path = os.path.join(cosmos.scenario.path,
                                      "tiles",   
                                      "flood_map")
        
        if fo.exists(flood_map_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(flood_map_path, wvpath)
            dct={}
            dct["name"]        = "flood_map"
            dct["long_name"]   = "Flood map"
            dct["description"] = "This is a flood map. It can tell if you will drown."
            dct["format"]      = "xyz_tile_layer"
            
            lgn = {}
            lgn["text"] = "Flood depth"

            contours = []

            contour = {}
            contour["text"]  = " 0.0&nbsp-&nbsp;0.33&#8201;m"
            contour["color"] = "#CCFFFF"
            contours.append(contour)

            contour = {}
            contour["text"]  = " 0.33&nbsp;-&nbsp;1.0&#8201;m"
            contour["color"] = "#40E0D0"
            contours.append(contour)

            contour = {}
            contour["text"]  = " 1.0&nbsp-&nbsp;2.0&#8201;m"
            contour["color"] = "#00BFFF"
            contours.append(contour)

            contour = {}
            contour["text"]  = "&gt; 2.0&#8201;m"
            contour["color"] ="#0909FF"
            contours.append(contour)

            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            map_variables.append(dct)
            
        # Wave maps
        
        # Check if flood maps are available
        wave_map_path = os.path.join(cosmos.scenario.path,
                                      "tiles",   
                                      "hm0")
        
        if fo.exists(wave_map_path):

            wvpath = os.path.join(scenario_path)
            fo.copy_file(wave_map_path, wvpath)
            dct={}
            dct["name"]        = "hm0" 
            dct["long_name"]   = "Wave height"

            dct["description"] = "These are Hm0 wave heights."
            dct["format"]      = "xyz_tile_layer"
            
            lgn = {}
            lgn["text"] = "Wave heights"

            contours = []

            contour = {}
            contour["text"]  = " 0.0&nbsp-&nbsp;0.33&#8201;m"
            contour["color"] = "#CCFFFF"
            contours.append(contour)

            contour = {}
            contour["text"]  = " 0.33&nbsp;-&nbsp;1.0&#8201;m"
            contour["color"] = "#40E0D0"
            contours.append(contour)

            contour = {}
            contour["text"]  = " 1.0&nbsp-&nbsp;2.0&#8201;m"
            contour["color"] = "#00BFFF"
            contours.append(contour)

            contour = {}
            contour["text"]  = "&gt; 2.0&#8201;m"
            contour["color"] ="#0909FF"
            contours.append(contour)

            lgn["contours"] = contours
            dct["legend"]   = lgn
            
            map_variables.append(dct)
            
        mv_file = os.path.join(scenario_path,
                               "variables.js")
        cht.misc_tools.write_json_js(mv_file, map_variables, "var map_variables =")

    def upload(self):        
        
        # Upload entire copy of local web viewer to web server

        # f = open_sftp_connection()
        # upload_latest_json(f)
        # upload_tide_gauges(f)
        # upload_wave_buoys(f)
        # upload_png_tiles(f)
        # upload_wind_fields(f)
        # close_sftp_connection(f)
        cosmos.log("Done uploading.")

    def upload_data(self):        
        # Upload data from local web viewer to web server
        pass

def open_sftp_connection():

    from cht.sftp import SSHSession

    f = SSHSession(cosmos.config.ftp_hostname,
                   username=cosmos.config.ftp_username,
                   password=cosmos.config.ftp_password)
    
    return f

def close_sftp_connection(f):
    
    f.sftp.close()    
