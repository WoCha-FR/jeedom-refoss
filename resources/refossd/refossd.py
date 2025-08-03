import os
import asyncio
from pathlib import Path

from refoss.configs import refossConfigs
from refoss.devices import EnergyMonitor

from jeedomdaemon.base_daemon import BaseDaemon
from jeedomdaemon.base_config import BaseConfig

class DaemonConfig(BaseConfig):
  def __init__(self):
    super().__init__()

    self.add_argument("--actu", help="actualisation en secondes", type=int, default=5)
    self.add_argument("--excluded_uuid", type=str)

  @property
  def actualisation(self):
    return int(self._args.actu)

  @property
  def excluded_uuid(self):
    uuids = blids = str(self._args.excluded_uuid)
    return [str(x) for x in uuids.split(',') if x != '']


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
    self._refossems: list[EnergyMonitor] = []

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
      await self.__connect_devices()

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
        if result:
          await self.__connect_devices()
        await self.send_to_jeedom({'discover': result})
      except Exception as e:
        self._logger.error('Exception during discovery: %s', e)
        await self.send_to_jeedom({'discover': False})

  async def on_stop(self) -> None:
    await self.__disconnect_devices()

  async def __connect_devices(self):
    await self.__disconnect_devices()

    for device_config in self._refossconfigs.devices.values():
      self._logger.info('device : %s', device_config.uuid)
      try:
        if device_config.uuid in self._config.excluded_uuid:
          self.logger.debug('Device desactivated: %s', device_config.uuid)
          continue

        new_device = EnergyMonitor(device_config)
        new_device.update_interval = self._config.actualisation
        await new_device.start()

        self._refossems.append(new_device)
      except Exception as e:
        self._logger.error('Exception during connection of device %s: %s', device_config.uuid, e)

  async def __disconnect_devices(self):
    self._logger.debug('Disconnection of %i devices', len(self._refossems))
    for device in self._refossems:
      await device.stop()

    self._refossems.clear()
    await asyncio.sleep(1)

RefossD().run()