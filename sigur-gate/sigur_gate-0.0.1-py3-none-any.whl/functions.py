def parse_ap_status(status):
    status_str = status.decode()
    status_list = status_str.split(' ')
    print("STATUS_LIST", status_list)
    status_final = status_list[10]
    return status_final
