from exergenics import ExergenicsApi

api = ExergenicsApi("apiuser@exergenics.com", "M1nd0v3rM4tt3r", False)
api.sendSlackMessage("test", "bigredbutton")
