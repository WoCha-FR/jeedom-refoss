import asyncio
import json
import random
import string
import logging
import time
from hashlib import md5
from aiohttp import ClientSession

from jeedomdaemon.base_daemon import BaseDaemon

from .configs import refossConfig
from .const import CHANNEL_NAME

class EnergyMonitor:
  def __init__(self, daemon: BaseDaemon, config: refossConfig):
    '''
    Initialize the RefossEnergyMonitor object
    '''
    self._logger = logging.getLogger()
    self._config = config
    self._update_seconds = 5

    self.__read_elec = None
    self.__read_conso = None
    self.__daemon = daemon

    @property
    def update_interval(self):
      return self._update_seconds

    @update_interval.setter
    def update_interval(self, value: int):
      self._update_seconds = value

  async def start(self):
    if not all([self._config.uuid, self._config.ip]):
      missing_params = []
      if not self._config.uuid:
        missing_params.append("uuid")
      if not self._config.ip:
        missing_params.append("ip")
      self._logger.warning(f"Missing parameter(s): {', '.join(missing_params)}. Could not configure device")
    else :
      self._logger.debug("Update data for device %s every %i seconds", self._config.uuid, self._update_seconds)
      self.__read_elec = asyncio.create_task(self.__read_elec_values())
      self.__read_elec = asyncio.create_task(self.__read_conso_values())

  async def stop(self):
    try:
      self.__read_elec.cancel()
      self.__read_conso.cancel()
    except Exception:
      pass
    self.__read_elec = None
    self.__read_conso = None

  async def __read_elec_values(self):
    try:
      while True:
        try:
          # Build Electricity message
          message, message_id = self._build_http_message()
          # Format url
          url = f"http://{self._config.ip}/public"
          # Request
          async with ClientSession() as session, session.post(url,json=json.loads(message.decode()),timeout=5) as response :
            data = await response.json()
            # Verify data
            if data is not None:
              header = data.get("header", {})
              messageId = header.get("messageId")
              ack_method = header.get("method")
              payload = data.get("payload", {})
              # Check validity
              if messageId == message_id and ack_method == "GETACK" and "electricity" in payload:
                #self._logger.debug(payload)
                jsonObject = payload.get("electricity")
                ret = {}
                for item in jsonObject:
                  prefix = CHANNEL_NAME[item['channel']]
                  ret.update({
                      f"{prefix}voltage": item['voltage']/1000,
                      f"{prefix}current": item['current']/1000,
                      f"{prefix}power": item['power']/1000,
                      f"{prefix}factor": item['factor'],
                    })
                await self.__daemon.send_to_jeedom({f"{self._config.uuid}": ret})
              else :
                self._logger.warning("[%s] incorrect response.", self._config.uuid)
            else :
              self._logger.warning("[%s] no response.", self._config.uuid)
            # Loop
            await asyncio.sleep(self.update_interval)
        except asyncio.TimeoutError:
          self._logger.warning("[%s] Timeout reading values, retry in 60 seconds.", self._config.uuid)
          await asyncio.sleep(60)
        except Exception as e:
          self._logger.warning(f"[{self._config.uuid}] Http fail: {e}, ip:{self._config.ip}, retry in 60 seconds.")
          await asyncio.sleep(60)
    except asyncio.CancelledError:
      self._logger.info(f"[{self._config.uuid}] Stop electricity auto update")

  async def __read_conso_values(self):
    try:
      while True:
        try:
          # Build Conso message
          message, message_id = self._build_http_message(datatype="conso")
          # Format url
          url = f"http://{self._config.ip}/public"
          # Request
          async with ClientSession() as session, session.post(url,json=json.loads(message.decode()),timeout=5) as response :
            data = await response.json()
            # Verify data
            if data is not None:
              header = data.get("header", {})
              messageId = header.get("messageId")
              ack_method = header.get("method")
              payload = data.get("payload", {})
              # Check validity
              if messageId == message_id and ack_method == "GETACK" and "consumptionH" in payload:
                #self._logger.debug(payload)
                jsonObject = payload.get("consumptionH")
                ret = {}
                for item in jsonObject:
                  prefix = CHANNEL_NAME[item['channel']]
                  ret.update(
                    {f"{prefix}total": item['total']/1000}
                  )
                await self.__daemon.send_to_jeedom({f"{self._config.uuid}": ret})
              else :
                self._logger.warning("[%s] incorrect response.", self._config.uuid)
            else :
              self._logger.warning("[%s] no response.", self._config.uuid)
            # Loop
            await asyncio.sleep(300)
        except asyncio.TimeoutError:
          self._logger.warning("[%s] Timeout reading values, retry in 60 seconds.", self._config.uuid)
          await asyncio.sleep(60)
        except Exception as e:
          self._logger.warning(f"[{self._config.uuid}] Http fail: {e}, ip:{self._config.ip}, retry in 60 seconds.")
          await asyncio.sleep(60)
    except asyncio.CancelledError:
      self._logger.info(f"[{self._config.uuid}] Stop conso auto update")

  def _build_http_message(self, datatype: str = 'elec'):
    if datatype == "elec":
      namespace = "Appliance.Control.ElectricityX"
      payload = {"electricity": {"channel": 65535}}
    else:
      namespace = "Appliance.Control.ConsumptionH"
      payload = {"consumptionH": {"channel": 65535}}

    # Generate random string
    randomstring = "".join(
      random.SystemRandom().choice(string.ascii_uppercase + string.digits)
      for i in range(16)
    )
    # messageId
    md5_hash = md5()
    md5_hash.update(randomstring.encode("utf8"))
    messageId = md5_hash.hexdigest().lower()
    # timestamp
    timestamp = int(round(time.time()))
    # sign
    md5_hash = md5()
    strtohash = f"{messageId}{timestamp}"
    md5_hash.update(strtohash.encode("utf8"))
    signature = md5_hash.hexdigest().lower()
    # json data
    data = {
      "header": {
        "from": f"/app/{randomstring}/sub",
        "messageId": messageId,
        "method": "GET",
        "namespace": namespace,
        "payloadVersion": 1,
        "sign": signature,
        "timestamp": timestamp,
        "triggerSrc": "JEEDOM",
        "uuid": self._config.uuid,
      },
      "payload": payload
    }
    strdata = json.dumps(data)
    # return
    return strdata.encode("utf-8"), messageId
