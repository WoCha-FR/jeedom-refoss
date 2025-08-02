import asyncio
import logging

from .configs import refossConfig

class EnergyMonitor:
  def __init__(self, config: refossConfig):
    '''
    Initialize the iRobot object
    '''
    self._loop = asyncio.get_running_loop()
    self._logger = logging.getLogger()


    if not all([config.uuid, config.ip]):
      missing_params = []
      if not config.uuid:
        missing_params.append("uuid")
      if not config.ip:
        missing_params.append("ip")
      raise ValueError(f"Missing parameter(s): {', '.join(missing_params)}. Could not configure device")

    self._config = config
    self._update_seconds = 5
    self._loop.create_task(self.__periodic_update())

    @property
    def update_interval(self):
      return self._update_seconds

    @update_interval.setter
    def update_interval(self, value: int):
      self._update_seconds = value

  async def __periodic_update(self):
    while True:
      try:
        self._logger.debug("Update data for device %s every %i seconds", self._config.uuid, self._update_seconds)
        await asyncio.sleep(self._update_seconds)
        '''await self._loop.run_in_executor(None, self.decode_topics)'''
      except asyncio.CancelledError:
        break
      except Exception as e:
        self._logger.exception(e)