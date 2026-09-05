"""Example plugin package for Antigravity."""

from plugins.example_plugin.sensors import JiraTicketAgeSensor
from plugins.example_plugin.thrusters import CustomCacheWarmerThruster

__all__ = ["JiraTicketAgeSensor", "CustomCacheWarmerThruster"]
