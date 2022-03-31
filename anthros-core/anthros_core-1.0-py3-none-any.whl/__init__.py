import  sys
if sys.platform in ['win32']: sb = '\\'
else: sb = '/'
_path = __file__
_path = _path.split(sb)
_path = _path[:len(_path) - 1]
_path = sb.join(_path)

save_path = sys.path[0]
sys.path[0] = _path
import core, tools, interfaces
sys.path[0] = save_path

del sys
del sb
del _path
del save_path