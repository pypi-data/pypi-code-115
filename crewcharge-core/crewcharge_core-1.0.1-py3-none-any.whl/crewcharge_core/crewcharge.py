import sys
import hashlib
import requests
import json

if sys.version_info < (3, 6):
    import sha3

crewcharge_end_point = "https://app.crewcharge.com"

def attach_user_attributes(api_key, uid, attributes, test_user=False):
    """
        The function attaches a new user with Crewcharge or modifies the existing user preferences.

        Parameters:
            api_key (String) - Your API key within Crewcharge.
            
            uid (String) -  Identifier of the user that can be user id or email.
            
            attributes (Dictionary) - Contains information about the user.
            You can attach any attributes, but the needed ones are {@see recommended_user_attributes}

            test_user (Boolean) - Refers to whether the user must be attached as a test user within Crewcharge.
    """

    try: 
        attach_attributes_end_point = crewcharge_end_point + "/api/v1/attach_user_attributes"

        headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        } 

        json_attributes_object = json.dumps(attributes, indent = 4) 

        payload = {
            "uid": uid,
            "attributes": json_attributes_object,
            "test_user": test_user
        }

        response = requests.request("POST", attach_attributes_end_point, headers=headers, data=payload)

        return response.json()

    except ValueError as ve:
        return ("Invalid JSON returned")
    except requests.RequestException as reqEx:
        return (reqEx)

def change_privacy_preferences(api_key, uid, privacy_preferences):
    """
        The function changes a user's privacy options.

        Parameters:
            api_key (String) - Your API key within Crewcharge.
            
            uid (String) -  Identifier of the user that can be user id or email.
            
            privacy_preferences (Dictionary) - Refers to modifying user's options with collecting data on analytics, email, feedback, sms, etc. Valid values are {@see valid_privacy_preferences}
    """

    try: 
        attach_attributes_end_point = crewcharge_end_point + "/api/v1/attach_user_attributes"

        headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        } 

        json_privacy_object = json.dumps(privacy_preferences, indent = 4)

        payload = {
            "uid": uid,
            "privacy_preferences": json_privacy_object,
        }

        response = requests.request("POST", attach_attributes_end_point, headers=headers, data=payload)

        return response.json()

    except ValueError as ve:
        return ("Invalid JSON returned")
    except requests.RequestException as reqEx:
        return (reqEx)

def log_trigger(analytics_tag, uid, trigger_key):
    """
        The function attaches a new user with Crewcharge or modifies the existing user preferences.

        Parameters:
            trigger_key (String) - the key you want to track (Obtain this from your Crewcharge Console).
            
            analytics_tag (String) - is your tag obtained for this project.

            uid (String) - Identifier of the user that can be user id or email.
    """

    try: 
        log_trigger_end_point = crewcharge_end_point + "/api/v1/log"

        headers = {
        'Content-Type': 'application/json',
        } 

        payload = {
            "uid": uid,
            "analytics_tag": analytics_tag,
            "trigger_key": trigger_key
        }

        response = requests.post(url=log_trigger_end_point, headers=headers, json=payload)

        return response.json()

    except ValueError as ve:
        return ("Invalid JSON returned")
    except requests.RequestException as reqEx:
        return (reqEx)


recommended_user_attributes = {
    "pii_name": "pii_name",
    "pii_email": "pii_email",
    "pii_image": "pii_image",
    "locale": "locale"
}

## Please note, all values are in booleans.
valid_privacy_preferences = {
    "analytics": {
        "pii": "false"
    }, "feedback": {
        "email": "false",
        "push": "false",
        "sms": "false",
        "in_app": "true"
    }, "marketing": {
        "email": "false",
        "push": "false",
        "sms": "false",
        "in_app": "true",
    },
}
