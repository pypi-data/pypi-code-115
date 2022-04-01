import os
import inspect
import re
from enum import Enum
import subprocess
from typing import Dict
import yaml
import jsonschema
from functools import wraps
import click

from toolstack.core.exceptions import BeforeError, AfterError

TOOLSTACK_CONFIG_SCHEMA="""
type: object
properties:
  provider:
    type: object
    properties:
      name:
        type: string
        enum:
          - aws
          - azure
      use_alias:
        type: boolean
    required:
      - name
  plugins:
    type: object
    additionalProperties: true
  environment:
    type: array
  before:
    type: array
  after:
    type: array
required:
  - provider
additionalProperties: false
"""

def before_and_after(f):
    """decorator to trigger 'environment', 'before' and 'after' methods"""
    @wraps(f)
    def wrapper(self, *args, **opts):
      try:
        if hasattr(self, 'environment') and inspect.ismethod(self.environment):
          self.environment(*args, **opts)
        if hasattr(self, 'before') and inspect.ismethod(self.before):
          self.before(*args, **opts)
        result = f(self, *args, **opts)
        if hasattr(self, 'after') and inspect.ismethod(self.after):
          self.after(*args, **opts)
        return result
      finally:
        self._flush_to_cache()

    return wrapper

def confirm(msg:str, show:bool=True, abort:bool=False):
  """
  Decorator that asks user to confirm execute method

  Params
  ------
  - msg   : the confirmation
  - show  : conditional flag to (not) show the confirmation
  - abort : default value when pressing 'enter'
  """
  def decorator(func):
    @wraps(func)
    def wrapper(self, *args, **opts):
      if show:
        if not self.confirm(eval(f"""f'''{msg}'''"""), abort):
          return
      return func(self, *args, **opts)
    return wrapper
  return decorator

class PROVIDER(Enum):
    """
    Supporder providers.
    """
    AWS   = 'aws'
    AZURE = 'azure'
    # GCP   = 'google'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_ 

    @classmethod
    def to_list(cls):
        return cls._value2member_map_.keys()

    @classmethod
    def to_string(cls):
        return ", ".join(cls._value2member_map_.keys())

class ToolManager(object):

  def __init__(self, tool:str, working_dir:str, dry_run:bool=False, debug:bool=False) -> None:

    self.__tool           = tool
    self.__alias          = None
    self.__dry_run        = dry_run
    self.__debug          = debug
    self.__working_dir    = working_dir
    self.__config         = None
    self.__extra_env_vars = dict()

    self.__toolstack_env = {key: value for key, value in os.environ.items() if key.startswith('TOOLSTACK_')}

    base = os.path.join(self._working_dir, '.toolstack')

    if not os.path.isdir(base):
      os.mkdir(base)

    self.__config_file = os.path.join(base, 'config')
    self.__cache_file  = os.path.join(base, 'cache')

    # read config
    if os.path.isfile(self.__config_file) and os.path.getsize(self.__config_file) > 0:
      with open(self.__config_file, 'r') as f:
        try:
          self.__config = yaml.safe_load(f)

          # validate 'config'
          self._validate(data=self.__config, schema=TOOLSTACK_CONFIG_SCHEMA)

        except yaml.parser.ParserError:
          raise click.ClickException(f'could not parse {self.__config_file}')

    # evaluate provider (default: aws)
    self.__provider = self._config.get('provider', dict()).get('name', 'aws') if self._config else 'aws'

    if not PROVIDER.has_value(str(self._provider)):
      raise click.ClickException(f"Invalid provider '{self._provider}' (expecting: {PROVIDER.to_string()})")

    # get (or create) cache
    # TODO: move 'cache' to separate object.
    if os.path.isfile(self.__cache_file) and os.path.getsize(self.__cache_file) > 0:
      with open(self.__cache_file, 'r') as f:
        try:
          self.__cache = yaml.safe_load(f)
        except yaml.parser.ParserError:
          raise click.ClickException(f'could not parse {self.__cache_file}')
    else:
        self.__cache = dict()

  @property
  def _tool(self) -> str:
    return self.__tool

  @property
  def _working_dir(self) -> str:
    return self.__working_dir

  @property
  def _provider(self) -> str:
    return self.__provider

  @property
  def _dry_run(self) -> bool:
    return self.__dry_run

  @property
  def _debug(self) -> bool:
    return self.__debug

  @property
  def _config(self) -> dict:
    return self.__config

  @property
  def _cache(self) -> dict:
    return self.__cache

  def _validate(self, data:dict, schema:str) -> None:

    validator = jsonschema.Draft4Validator(yaml.safe_load(schema))
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if len(errors) > 0:
      # construct 'error' message + raise exception
      raise click.ClickException("validating errors found:\n\n" + '\n'.join([f"* {'.'.join(e.path) + ': ' if e.path else ''}{e.message}".replace("'","") for e in errors]))

  def _flush_to_cache(self):
    _cache_file = os.path.join(self._working_dir, '.toolstack', 'cache')

    with open(_cache_file, 'w+') as f:
        yaml.safe_dump(self._cache, f, encoding='utf-8', allow_unicode=True)

  def _cmd(self, cmd:str, capture_output:bool=False, raise_on_error:bool=True) -> str:
    try:
      output = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, cwd=self.__working_dir, universal_newlines=True)
      # NOTE: if 'return_code' != 0, an exception will be raised.
      return output.strip()

    except subprocess.CalledProcessError as e:
      if raise_on_error:
        raise click.ClickException(str(e))
      else:
        click.secho(f"Error running command '{cmd}': {str(e)}", fg='red', bold=True)

  # def _cmd2(self, cmd:str, capture_output:bool=False, raise_on_error:bool=True):
  #   """
  #   [wip] Improved way of running 'cmd'
  #   """

  #   if capture_output is True:
  #     stderr = subprocess.PIPE
  #     stdout = subprocess.STDOUT
  #   else:
  #     stderr = sys.stderr
  #     stdout = sys.stdout

  #   _full_cmd = cmd.split()

  #   p = subprocess.Popen(
  #       _full_cmd, stdout=stdout, stderr=stderr, cwd=self.__working_dir, universal_newlines=True, shell=True
  #   )

  #   out, err = p.communicate()
  #   ret_code = p.returncode

  #   if capture_output is True:
  #     out = out.decode()
  #     err = err.decode()
  #   else:
  #     out = None
  #     err = None

  #   if ret_code and raise_on_error:
  #     raise click.ClickException(f'error executing {cmd} -> rtn={ret_code}')

  #   return ret_code, out, err

  def _get_provider_id(self):
    """Get account (or subscription) alias depending on the 'provider' in the configuration."""
    if not self.__alias:
      if PROVIDER(self._provider) == PROVIDER.AWS:
        _alias = self._cmd("aws iam list-account-aliases --query AccountAliases[*] --output text")
        # self._id = self._cmd("aws sts get-caller-identity --query 'Account' --output text") 
      elif PROVIDER(self._provider) == PROVIDER.AZURE:
        _alias = self._cmd("az account show --query 'name' --output tsv")
        # raw = self._cmd("az account show --output json")
      else:
        # this should not happen
        raise click.ClickException(f"Invalid provider '{self.provider}' (expecting: {PROVIDER.to_string()})")

      self.__alias = _alias

    return self.__alias

  def __eval(self, return_code:int) -> None:
    """
    Evaluate return return_code from 'os.system'.
    Parameters
    ----------
    return_code: int
        return code from 'os.system'
    Raises
    ------
    ClickException
        when 'return_code' is not equal to '0'
    """
    if return_code != 0:
      raise click.ClickException(return_code)

  def confirm(self, message:str, abort:bool=False):
    return click.confirm(message, abort)

  def environment(self, *args, **kwargs) -> Dict:
    if not self._config or self._dry_run:
      return

    if len(self.__config.get('environment', [])) > 0:
      click.secho(f"\nPreparing 'environment'...\n",  bold=True)
    else:
      click.secho(f"INFO: 'environment' variables not found. You can define them in {self.__config_file}")

    _env = dict()

    for e in self.__config.get('environment', []) or []:
      k,v = map(str.strip, e.split('='))
      v = v.split('#',1)[0] # Value 'v' could still contain hashtag to comment out rest of line
      if v.startswith('$(') and v.endswith(')'):
        try:
          cmd     = re.search("\$\((.*?)\)", v).group(1) # get substring between $(...)
          output  = self._cmd(cmd)
          _env[k] = output
        except subprocess.CalledProcessError as e:
          raise click.ClickException("exception executing '{}':\n\n{}".format(cmd, e.output))
      else:
        _env[k] = v

    # merge with os.environ
    for k,v in _env.items():
      if self.__debug:
        click.secho(f'{k}={v}')
      os.environ[k] = v

    # add extra items (if any)
    for k,v in self.__extra_env_vars.items():
      os.environ[k] = v

    return _env

  def before(self, *args, **kwargs) -> None:
    if not self._config or self._dry_run:
      return

    if len(self._config.get('before', [])) > 0:
      click.secho(f"\nExecuting 'before' commands...\n",  bold=True)
    else:
      click.secho(f"INFO: 'before' steps not found. You can define them in {self.__config_file}")

    # change work directory before 'execute'
    os.chdir(self.__working_dir)

    for pre in self._config.get('before', []) or []:
      try:
        if self.__debug:
          print(pre)

        self.__eval(os.system(pre))
        # out = self._cmd(pre, capture_output=True)

      except Exception as e:
        print(str(e))
        raise BeforeError(pre)

  def after(self, *args, **kwargs) -> None:
    if not self._config or self._dry_run:
      return

    if len(self._config.get('after', [])) > 0:
      click.secho(f"\nExecuting 'after' commands...\n",  bold=True)
    else:
      click.secho(f"INFO: 'after' steps not found. You can define them in {self.__config_file}")

    # change work directory before 'execute'
    os.chdir(self.__working_dir)

    for post in self._config.get('after', []) or []:
      try:
        if self.__debug:
          print(post)

        self.__eval(os.system(post))
        # out = self._cmd(post, capture_output=True)

      except:
        raise AfterError(post)
