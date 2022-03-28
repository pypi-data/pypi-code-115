# please install multipledispatch 0.6.0
import requests
from urllib.parse import urljoin
import json
import polling2


class Error():
    def __init__(self, res = None, proc_msg = None):
        self.status_code = None
        self.packaging_msg = None
        self.program_msg = proc_msg
        self.res = res

        if self.res is not None:
            self.status_code = res.status_code
            self.packaging_msg = res.content
            print(self.packaging_msg)
    
    @property
    def status_msg(self):
        # 4xx error -> client error, 5xx error -> server error
        if self.status_code == 400:
            return f"Bad Request({self.status_code})! Try again."
        elif self.status_code == 401:
            return f"Unauthorized({self.status_code})! Try again."
        elif self.status_code == 403:
            return f"Forbidden({self.status_code})! Try again."
        elif self.status_code == 404:
            return f"Not Found({self.status_code})! Try again."
        elif self.status_code == 500:
            return f"Internal Server Error({self.status_code})! - {self.packaging_msg}"
        else:
            return f"Unknown Error. Original error message - {self.packaging_msg}"

class PackagingServer():
    def __init__(self, addr, port, network_request_time_out=5):
        self.address = f"http://{addr}:{port}/"
        self.timeout = network_request_time_out
        self.headers = {'token': self.get_token()}

    def _node_model_compatibility(self, model_uuid, node_uuid):
        node, error = self.get_node(node_uuid)
        model, error = self.get_model(model_uuid)

        if node is None or model is None:
            return False
        elif model.type not in node.available_model_types:
            return False
        else:
            return True

    def _check_status(self, res):
        if res.status_code >= 400: # More than 400 is seen as an issue on the device farm side.
            return False
        else:
            return True

    def _poll(self, add_str, method, files=None, data=None, params=None, headers=None):
        token = self.get_token()
        headers = {'Content-Type': 'application/json; charset=utf-8', 'token': token}
        res = None
        try:
            if(method == "get"):
                res = polling2.poll(
                    lambda: requests.get(
                        url=urljoin(self.address, add_str),
                        files=files,
                        data=data,
                        params=params,
                        headers=headers
                    ),
                    check_success = self._check_status,
                    step=5,
                    timeout=self.timeout)
            else:
                res = polling2.poll(
                    lambda: requests.post(
                        url=urljoin(self.address, add_str),
                        files=files,
                        data=data,
                        params=params,
                        headers=headers
                    ),
                    check_success = self._check_status,
                    step=5,
                    timeout=self.timeout)
        except polling2.TimeoutException as e:
            return res, Error(e.last)
        return res, None

    def get_token(self):
        url = "https://login.netspresso.ai:8888/api/v1/login"
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps(
                {
                    "username":"seongun", 
                    "password":"12345"
                }
            )
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 201:
            dict_response = json.loads(response.content)
            return dict_response.get("tokens").get("access_token")
        else:
            return None
    
    def get_list(self, folder_name: str = None):
        params = {
            "folder": folder_name
        }
        res, error = self._poll(add_str=f"list", method="get", params=params)
        if error is not None:
            return None, error
        res = json.loads(res.content.decode('utf-8'))
        lists = []
        [lists.append(res["objects"][i]) for i in range(0, len(res["objects"]))]
        return lists, None

    def build_package(self, data: dict):
        res, error = self._poll(add_str=f"build", method="post", data=json.dumps(data))
        if error is not None:
            return error
        return None

    def download_package(self, file_name: str, get_url: bool):
        params = {
            "file_name": file_name,
            "get_url": get_url
        }
        res, error = self._poll(add_str=f"download", method="get", params=params)
        if error is not None:
            return None, error
        return res.content, None