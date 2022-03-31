import requests as request

ID = "notset"
baseurl = 'http://magma-mc.net/Modules/filez/filez.php/?ID='+ID
 # ID = the folder name of where the files will be stored please make sure -
 # you have created the project at http://magma-mc.net/projects.php
def _colorit(rgb, text):
    r, g, b = rgb
    return "\033[38;2;{};{};{}m{}\033[38;2;255;255;255m".format(r, g, b, text)
def _check():
    if ID == "notset":
        print(_colorit((255, 0, 0), """
              \n filez.ID, not set,
              \n please set and make sure that the project exists,
              \n http://magma-mc.net/projects.php
              \n"""))
        return False
    else:
        return True
        
def fread(file):
    if _check():
       return str(request.get(baseurl+"&filez=read&filename="+file).text)
    else:
        raise
def scan(folder):
    if _check():
        return str(request.get(baseurl+"&filez=scan&filename="+folder).text)
    else:
        raise
def fwrite(file, data, type):
    try:
        if _check():
            request.post(baseurl+"&filez=write&content="+data+"&filename="+file+"&type="+type)
        else:
            raise
    except:
        return False
    return True
