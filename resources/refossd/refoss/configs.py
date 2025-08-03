#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
from pathlib import Path
from pprint import pformat
import json
import logging
import socket
from ast import literal_eval
import configparser

from .const import BROADCAST_IP, DISCOVERY_TIMEOUT
from .exceptions import SocketError

class refossConfig(object):
  def __init__(self, uuid: str, data: dict):
    self.__uuid: str = uuid
    self.__data: dict = data

    self.__name: str = str(self.__data.get('devName', 'unknown'))
    self.__ip: str = str(self.__data.get('ip', ''))
    self.__soft: str = str(self.__data.get('devSoftWare', ''))

  @property
  def uuid(self):
    return self.__uuid

  @property
  def ip(self):
    return self.__ip

  @ip.setter
  def ip(self, value):
    self.__ip = value

  @property
  def name(self):
    return self.__name

  @name.setter
  def name(self, value: str):
    self.__name = value

  @property
  def softversion(self):
    return self.__soft

  @softversion.setter
  def softversion(self, value: str):
    self.__soft = value

  def toJSON(self):
    return self.__data

class refossConfigs:
  '''
  Manage the configuration of the Refoss devices
  '''
  def __init__(self, path: Path):
    self.__path = path
    self._logger = logging.getLogger()
    self.__json_file = self.__path/'config.json'

    self.__devices: dict[str, refossConfig] = {}

    self.__load_config()

  def __load_config(self):
    if self.__json_file.exists():
      self._logger.info("Load config file %s", self.__json_file)
      configs = json.loads(self.__json_file.read_text(encoding='utf-8'))
      for uuid, data in configs.items():
        self.__devices[uuid] = refossConfig(uuid, data)

  def __save_config_file(self):
    data = {}
    for device in self.__devices.values():
      data[device.uuid] = device.toJSON()
    self.__json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return True

  @property
  def devices(self):
    return self.__devices

  async def __receive_udp(self, timeout: int = DISCOVERY_TIMEOUT, address: str = BROADCAST_IP):
    # set up UDP socket to receive data from robot
    port = 9989
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    if address == BROADCAST_IP:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.bind(("", port))  # bind all interfaces to port
    self._logger.debug("waiting on port: %s for data", port)
    # message
    msg = json.dumps(
      {"id": "48cbd88f969eb3c486085cfe7b5eb1e4", "devName": "*"}
    ).encode("utf-8")
    s.sendto(msg, (address, 9988))
    configs: dict[str, refossConfig] = {}
    # Boucle
    while True:
      try:
        udp_data, addr = s.recvfrom(1024)  # wait for udp data
        if udp_data and udp_data.decode("utf-8") != msg.decode("utf-8"):
          try:
            parsedMsg = json.loads(udp_data.decode("utf-8"))
            # EM06 ?
            if "channels" in parsedMsg and "uuid" in parsedMsg:
              uuid = parsedMsg["uuid"]
              if uuid not in configs.keys():
                self._logger.debug('Device at IP: %s Data: %s', addr[0], json.dumps(parsedMsg))
                new_device = refossConfig(uuid, parsedMsg)
                self._logger.info("Found device %s - %s at IP %s", new_device.name, new_device.uuid, new_device.ip)
                configs[uuid] = new_device
          except Exception as e:
            self._logger.info("json decode error: %s", e)
            self._logger.info('RECEIVED: %s', pformat(udp_data))
      except socket.timeout:
         break
    # Fin
    s.close()
    return configs

  async def discover(self, address: str = BROADCAST_IP):
    self._logger.info("Discovering devices on network...")
    discovered_devices = await self.__receive_udp(timeout=15, address=address)

    if len(discovered_devices) == 0:
      if address == BROADCAST_IP:
        self._logger.warning("No device found on network, make sure your devices are connected on the same network then try again...")
      return False
    self._logger.info("Found %i devices on network", len(discovered_devices))

    for discovered_device in discovered_devices.values():
      if discovered_device.uuid in self.__devices.keys():
        self._logger.info("Device %s - %s already configured, updating data", discovered_device.name, discovered_device.uuid)
        self.__devices[discovered_device.uuid].ip = discovered_device.ip
        self.__devices[discovered_device.uuid].name = discovered_device.name
        self.__devices[discovered_device.uuid].softversion = discovered_device.softversion
      else:
        self._logger.info("Device %s - %s added to configuration", discovered_device.name, discovered_device.uuid)
        self.__devices[discovered_device.uuid] = discovered_device

    return self.__save_config_file()
