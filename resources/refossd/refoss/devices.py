import asyncio
import json
import random
import string
import logging
import time
from hashlib import md5
from aiohttp import ClientSession

from .configs import refossConfig

class EnergyMonitor:
  def __init__(self, config: refossConfig):
    '''
    Initialize the RefossEnergyMonitor object
    '''
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

    @property
    def read_task(self):
      return self.__read_task

    @property
    def update_interval(self):
      return self._update_seconds

    @update_interval.setter
    def update_interval(self, value: int):
      self._update_seconds = value

  async def start(self):
    self._logger.debug("Update data for device %s every %i seconds", self._config.uuid, self._update_seconds)
    self.__read_task = asyncio.create_task(self.__read_values())

  async def stop(self):
    try:
      self.__read_task.cancel()
    except Exception:
      pass
    self.__read_task = None

  async def __read_values(self):
    while True:
      try:
        ''' RESPONSE
        url = 'http://10.42.10.209/public'
        response = requests.post(url, json=request_data)
        '''
        await asyncio.sleep(self._update_seconds)
      except asyncio.CancelledError:
        break
      except Exception as e:
        self._logger.exception(e)
