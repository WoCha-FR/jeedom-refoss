import os
from pathlib import Path

from refoss.configs import refossConfigs

from jeedomdaemon.base_daemon import BaseDaemon
from jeedomdaemon.base_config import BaseConfig

class DaemonConfig(BaseConfig):
  def __init__(self):
    super().__init__()
    self.add_argument("--actu", help="actualisation en secondes", type=int, default=5)

  @property
  def actualisation(self):
    return int(self._args.actu)

class RefossD(BaseDaemon):
  def __init__(self) -> None:
    self._config = DaemonConfig()
    super().__init__(
      config = self._config,
      on_start_cb = self.on_start,
      on_message_cb = self.on_message,
      on_stop_cb = self.on_stop
    )
    self._refossconfigs: refossConfigs = None
    '''self._robots: list[iRobot] = []'''
    ''' end __init__ '''

  async def on_start(self):
    basedir = os.path.dirname(__file__)
    configFile = Path(os.path.abspath(basedir + '/../../data'))
    self._refossconfigs = refossConfigs(path=configFile)

    if len(self._refossconfigs.devices) == 0:
      self._logger.info('No devices configured, trying auto discovery')
      try:
        result = await self._refossconfigs.discover()
        await self.send_to_jeedom({'discover': result})
      except Exception as e:
        self._logger.error('Exception during discovery: %s', e)
        await self.send_to_jeedom({'discover': False})

    if len(self._refossconfigs.devices) == 0:
      self._logger.warning('No devices configured, please run discovery from plugin page')
      await self.send_to_jeedom({'msg': "NO_DEVICES"})
    else:
      ''' asyncio.create_task(self.__connect_robots()) '''

  async def on_message(self, message: list):
    """
    Message reçu de Jeedom
    """
    self._logger.debug(f"'on_message' '''{message}'''")
    """ Discover """
    if message['action'] == 'discover':
      self._logger.debug('Get Discover query')
      try:
        result = await self._refossconfigs.discover(message['address'])
        #if result:
          #await self.__connect_robots()
        await self.send_to_jeedom({'discover': result})
      except Exception as e:
        self._logger.error('Exception during discovery: %s', e)
        await self.send_to_jeedom({'discover': False})

  async def on_stop(self) -> None:
    pass

RefossD().run()