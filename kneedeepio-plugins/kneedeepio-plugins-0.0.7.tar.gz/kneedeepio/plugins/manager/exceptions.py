#!/usr/bin/env python3

### IMPORTS ###

### GLOBALS ###

### FUNCTIONS ###

### CLASSES ###
class KneeDeepIOPluginsManagerException(Exception):
    pass

class ServiceAlreadyRegisteredException(KneeDeepIOPluginsManagerException):
    pass

class ServiceNotRegisteredException(KneeDeepIOPluginsManagerException):
    pass

class PluginAlreadyLoadedException(KneeDeepIOPluginsManagerException):
    pass

class PluginNotLoadedException(KneeDeepIOPluginsManagerException):
    pass
