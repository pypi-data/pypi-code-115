import os
import json
from minecraft_backup.config import USER_CONFIG_FILE_PATH


class Config:
    @classmethod
    def save_json_file(cls, json_file):
        with open(USER_CONFIG_FILE_PATH, "w") as f:
            f.write(json.dumps(json_file))

    @classmethod
    def get_user_config_json(cls):
        if os.path.exists(USER_CONFIG_FILE_PATH):
            with open(USER_CONFIG_FILE_PATH, "r") as f:
                log_conf = json.load(f)
            return log_conf
        else:
            raise FileNotFoundError(USER_CONFIG_FILE_PATH)

    @classmethod
    def get_auto_delete(cls) -> bool:
        setting_file = cls.get_user_config_json()

        return setting_file["auto_delete"]

    @classmethod
    def turn_auto_delete(cls):
        setting_file = cls.get_user_config_json()
        setting_file["auto_delete"] = not setting_file["auto_delete"]

        cls.save_json_file(setting_file)

    @classmethod
    def get_delete_target(cls):
        setting_file = cls.get_user_config_json()

        return setting_file["delete_target"]

    @classmethod
    def change_delete_target(cls, delete_target):
        setting_file = cls.get_user_config_json()
        setting_file["delete_target"] = delete_target

        cls.save_json_file(setting_file)

    @classmethod
    def is_user_changed_logs_path_config(cls) -> bool:
        setting_file = cls.get_user_config_json()
        return setting_file["logs_path"].lower() != "default"

    @classmethod
    def get_logs_path(cls):
        setting_file = cls.get_user_config_json()

        return setting_file["logs_path"]

    @classmethod
    def change_logs_path(cls, path):
        setting_file = cls.get_user_config_json()
        setting_file["logs_path"] = path

        cls.save_json_file(setting_file)
