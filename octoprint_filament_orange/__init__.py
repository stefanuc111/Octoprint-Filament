# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import octoprint.settings
import octoprint.util

from octoprint.events import eventManager, Events
from flask import jsonify, request

import logging
import logging.handlers

import threading

class FilamentSensorPlugin(octoprint.plugin.StartupPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin,
							octoprint.plugin.BlueprintPlugin):

	def initialize(self):
		self._logger.setLevel(logging.DEBUG)

		self.GPIO_PIN_NUMBER = 6;

		self._logger.info("Filament Sensor Plugin [%s] initialized..."%self._identifier)

	def on_after_startup(self):
		export = open("/sys/class/gpio/export","w")
    		export.write(str(self.GPIO_PIN_NUMBER))
    		export.close()

		pullup = open("/sys/class/gpio/gpio6/active_low","w")
    		pullup.write(str(1))
    		pullup.close()

		self.pin = open("/sys/class/gpio/gpio6/value","r")
		
		
	def get_settings_defaults(self):
		return dict(
			pin = -1,
		)

	@octoprint.plugin.BlueprintPlugin.route("/status", methods=["GET"])
	def check_status(self):
		status = "1"
		return jsonify( status = status )
		
	def on_event(self, event, payload):
		if event == Events.PRINT_STARTED:
			self._logger.info("Printing started. Filament sensor enabled.")
			self.start_check_loop()
		elif event in (Events.PRINT_DONE, Events.PRINT_FAILED, Events.PRINT_CANCELLED):
			self._logger.info("Printing stopped. Filament sensor disbaled.")
			self.stop_check_loop()

	def start_check_loop(self):
		self.stop_check_loop()
		self.timer = threading.Timer(5.0, self.check_gpio).start();
		
	def stop_check_loop(self):
		try:
			self.timer.cancel()
		except:
			pass

	def check_gpio(self):
		state = self.pin.read()
		self._logger.info("Detected sensor state [%s]? !"%(state))
		if state: #safety pin ?
			self._logger.debug("Sensor [%s]!"%state)
			if self._printer.is_printing():
				self._printer.toggle_pause_print()
		self.start_check_loop()

	def get_version(self):
		return self._plugin_version

	def get_update_information(self):
		return dict(
			octoprint_filament=dict(
				displayName="OrangePI Filament Sensor ",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="stefanuc111",
				repo="OctoPrint-Filament",
				current=self._plugin_version,

				# update method: pip
			)
		)

__plugin_name__ = "Filament Sensor"
__plugin_version__ = "1.12"
__plugin_description__ = "Use a filament sensor to pause printing when fillament runs out."

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FilamentSensorPlugin()

