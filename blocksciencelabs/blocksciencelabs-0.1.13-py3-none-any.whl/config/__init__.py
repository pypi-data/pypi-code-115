config = {
  "API_BASE_URL": "https://api.blocksciencelabs.com",
  "WHEEL_BASE_URL": "https://models-private.s3.us-east-2.amazonaws.com",
  "WHEEL_NAME": "pkg-0.0.0-py3-none-any.whl"
}

config["API_AUTHENTICATION_ENDPOINT"] = config["API_BASE_URL"] + "/login"
config["API_GET_PROJECTS_ENDPOINT"] = config["API_BASE_URL"] + "/get-projects"
config["API_GET_SIMULATIONS_ENDPOINT"] = config["API_BASE_URL"] + "/get-simulations"