import requests

from config import config
from project import Project
from simulation import Simulation

class Client(Project, Simulation):
  def __init__(self, options):
    self.options = options

    if options.get("email") and options.get("password"):
      self.method = "jwt"
    else:
      self.method = "key"

    if self.method != "jwt":
      raise Exception("Please supply both 'email' and 'password' in your Client configuration.")

    res = requests.post(config["API_AUTHENTICATION_ENDPOINT"], data = {"email": options["email"], "password": options["password"]})
    rdict = res.json()

    if rdict["success"] == True:
      self.jwt = rdict["payload"]["token"]
    else:
      raise Exception("Error authenticating client. Check email and password.")