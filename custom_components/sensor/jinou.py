"""
Support for the Jinou JO-BEC07-2 BLE temperature/humidity sensor.
"""
import logging

import voluptuous as vol

from homeassistant.const import ATTR_BATTERY_LEVEL, TEMP_CELSIUS
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_NAME, CONF_MAC)

REQUIREMENTS = ['bluepy==1.1.2']

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Optional(CONF_NAME, default=""): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Jinou sensor."""
    from bluepy.btle import Peripheral
    from bluepy.btle import AssignedNumbers

    _LOGGER.info("Jinou: connecting to %s", config.get(CONF_MAC))
    p = Peripheral(config.get(CONF_MAC))
    
    sensor = p.getServiceByUUID(0XAA20).getCharacteristics(0xAA21)[0]
    sensor.getDescriptors()[0].write(b"\x01\x00", True) 

    battery = p.getServiceByUUID(AssignedNumbers.batteryService).getCharacteristics(AssignedNumbers.batteryLevel)[0]
    battery.getDescriptors()[0].write(b"\x01\x00", True) 

    main = JinouMain(sensor, battery, config.get(CONF_NAME))
    add_devices([
        main,
        JinouHumidity(main, config.get(CONF_NAME)),
    ])

class JinouMain(Entity):
    """Implement polling the Jinou sensor."""

    def __init__(self, characteristic, battery, name):
        """Initialize the sensor."""
        self._characteristic = characteristic
        self._battery = battery
        self._name = name
        self.reading = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.reading:
             return None
        return -1 * self.reading[0] + self.reading[1] + self.reading[2]/10

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return TEMP_CELSIUS

    def update(self):
        """
        Update current conditions.
        """
        _LOGGER.debug("Polling data for %s", self._name)
        self.reading = self._characteristic.read()
        _LOGGER.debug("Data collected: %s", self.reading)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
             ATTR_BATTERY_LEVEL: ord(self._battery.read())
        }

class JinouHumidity(Entity):
    """Export the sensors humidity only."""

    def __init__(self, sensor, name):
        """Initialize the sensor."""
        self._sensor = sensor
        self._name = name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""

        reading = self._sensor.reading
        if not reading:
             return None
        return reading[4] + reading[5]/10

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return "%"

