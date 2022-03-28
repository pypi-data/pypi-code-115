import numpy as np
import pandas as pd
import datetime

def data_preprocesser():
    print("====start preprocess====")
    

def write_dat_files_config(data_file_config):
    dat_file_path = data_file_config["dimension"]+"//"+data_file_config["element_type"]+"//raw_data//dat_file//"
    pkl_file_path = data_file_config["dimension"]+"//"+data_file_config["element_type"]+"//raw_data//pkl_file//"
    user_input = input()
    with open(pkl_file_path+"//config.txt", "a") as f:
        f.write("time : {}\n".format(data_file_config["write_time"]))
        f.write("dat_file_path : {}\n".format(dat_file_path))
        f.write("dat_file_name : {}\n".format(data_file_config["file_name"]))
        f.write("dat_file_num : {}\n".format(data_file_config["file_num"]))
        f.write("user messgae : {}\n\n\n".format(user_input))
    
""" data_file_path에 있는 모든 .dat file 을 동일한 이름의 .pkl file로 변환 + 총 pkl 파일 제작"""
def convert_dat_files_to_pkl_files(data_file_config):
    dat_file_path = data_file_config["dimension"]+"//"+data_file_config["element_type"]+"//dat_file//"
    pkl_file_path = data_file_config["dimension"]+"//"+data_file_config["element_type"]+"//pkl_file//"
    data_frame_list = []
    for one_dat_file_name in (data_file_config["file_names"]):
        data = read_dat_file(dat_file_path+one_dat_file_name+".dat")
        data_frame = pd.DataFrame(data=data, columns = ["feature", "label"])
        data_frame.to_pickle(pkl_file_path+one_dat_file_name+".pkl") 
        data_frame_list.append(data_frame)
    total_data_frame = pd.concat(data_frame_list, ignore_index=True)
    total_data_frame.to_pickle(pkl_file_path+"dataset_"+data_file_config["write_time"]+".pkl")

    write_dat_files_config(data_file_config)

""" .dat file을 line by line 으로 read """
def read_dat_file(dat_file):
    print("open and read the file : {}".format(dat_file))
    data = []
    with open(dat_file) as f:
        lines = f.readlines()
        for idx in range(len(lines)):
            if lines[idx].startswith("#"):
                prev_data_dict = {}
            elif lines[idx].startswith("@"):
                prev_key_value = lines[idx][1:].strip()
                prev_data_dict[prev_key_value] = []
            elif not lines[idx].startswith("\n"):
                prev_data_dict[prev_key_value].append(lines[idx].strip())
            else:
                final_data_dict = make_final_dictionary(prev_data_dict)
                data.append(final_data_dict)   
    return data



""" make feature_labal dictionary """
def make_final_dictionary(prev_data_dict):
    data_dict = {}
    
    data_dict["space_dimension"] = int(prev_data_dict["space_dimension"][0])
    data_dict["node_connectivity"] = [np.array(i.split("\t"), dtype = np.int64) for i in prev_data_dict["node_connectivity"]]
    data_dict["node_indexes"] = [int(i) for i in prev_data_dict["node_indexes"]]
    data_dict["cell_avgs"] = [ float(i) for i in prev_data_dict["cell_averages"]]
    data_dict["cell_gradient"] = np.array(prev_data_dict["cell_gradient"][0].split("\t"), dtype = np.float64)
    data_dict["target_cell_index"] = int(prev_data_dict["node_indexes"][0])
    data_dict["target_cell_vertex_num"] = int(prev_data_dict["cell_coords"][0])
    data_dict["target_cell_avg"] = [float(prev_data_dict["cell_averages"][0])]
    """ temporary """
    data_dict["cell_gradient"] = [data_dict["cell_gradient"][0], 0, data_dict["cell_gradient"][1]]
    data_dict["cell_avgs_dict"] = {data_dict["node_indexes"][i] : data_dict["cell_avgs"][i] for i in range(len(data_dict["cell_avgs"]))}
    data_dict["target_cell_vertex_coords"] = [np.array(prev_data_dict["cell_coords"][i+1].split("\t"), dtype = np.float64) for i in range(data_dict["target_cell_vertex_num"])]
    data_dict["target_cell_center_coords"] = np.transpose(np.array(data_dict["target_cell_vertex_coords"])).sum(axis=1)/data_dict["target_cell_vertex_num"]
    data_dict["target_cell_vertex_distance"] = [np.array([coords[i]-data_dict["target_cell_center_coords"][i] for i in range(len(coords)) ], dtype = np.float64) for coords in data_dict["target_cell_vertex_coords"]]
    data_dict["target_cell_vertex_value"] = sorted(data_dict["target_cell_avg"][0]+sum([data_dict["cell_gradient"][i]*coords[i] for i in range(len(coords))]) for coords in data_dict["target_cell_vertex_distance"])
    data_dict["face_neighboring_cell_index"] = [connects[1] for connects in data_dict["node_connectivity"] if int(connects[0]) == data_dict["target_cell_index"]]
    data_dict["face_neighboring_cell_avg"] = sorted([data_dict["cell_avgs_dict"][k] for k in data_dict["face_neighboring_cell_index"]])
    data_dict["feature"] = data_dict["target_cell_avg"] + data_dict["face_neighboring_cell_avg"] + data_dict["target_cell_vertex_value"]
    data_dict["label"] = float(prev_data_dict["limiting_value"][0])
   
    return data_dict
