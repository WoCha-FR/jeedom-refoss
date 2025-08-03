"""Refoss exceptions."""
from __future__ import annotations

class SocketError(Exception):
  """Exception raised when socket send msg."""

class DeviceTimeoutError(Exception):
  """Exception raised when http request timeout."""
