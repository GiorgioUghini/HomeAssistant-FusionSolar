"""FusionSolar sensor."""
import homeassistant.helpers.config_validation as cv
import logging
import voluptuous as vol

from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .fusion_solar.const import ATTR_DATA_REALKPI, ATTR_REALTIME_POWER, ATTR_TOTAL_CURRENT_DAY_ENERGY, \
    ATTR_TOTAL_CURRENT_MONTH_ENERGY, ATTR_TOTAL_CURRENT_YEAR_ENERGY, ATTR_TOTAL_LIFETIME_ENERGY
from .fusion_solar.kiosk.kiosk import Kiosk
from .fusion_solar.kiosk.kiosk_api import FusionSolarKioskApi
from .fusion_solar.energy_sensor import FusionSolarEnergySensorTotalCurrentDay, \
    FusionSolarEnergySensorTotalCurrentMonth, FusionSolarEnergySensorTotalCurrentYear, \
    FusionSolarEnergySensorTotalLifetime
from .fusion_solar.power_entity import FusionSolarPowerEntityRealtime

from .const import CONF_KIOSKS, DOMAIN, ID_REALTIME_POWER, NAME_REALTIME_POWER, \
    ID_TOTAL_CURRENT_DAY_ENERGY, NAME_TOTAL_CURRENT_DAY_ENERGY, \
    ID_TOTAL_CURRENT_MONTH_ENERGY, NAME_TOTAL_CURRENT_MONTH_ENERGY, \
    ID_TOTAL_CURRENT_YEAR_ENERGY, NAME_TOTAL_CURRENT_YEAR_ENERGY, \
    ID_TOTAL_LIFETIME_ENERGY, NAME_TOTAL_LIFETIME_ENERGY

KIOSK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): cv.string,
        vol.Required(CONF_NAME): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_KIOSKS): vol.All(cv.ensure_list, [KIOSK_SCHEMA]),
    }
)

_LOGGER = logging.getLogger(__name__)


async def add_entities_for_kiosk(hass, async_add_entities, kiosk: Kiosk):
    _LOGGER.debug(f'Adding entities for kiosk {kiosk.id}')

    async def async_update_data():
        """Fetch data"""
        data = {}
        api = FusionSolarKioskApi(kiosk.apiUrl())
        data[f'{DOMAIN}-{kiosk.id}'] = {
            ATTR_DATA_REALKPI: await hass.async_add_executor_job(api.getRealTimeKpi, kiosk.id)
        }
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name='FusionSolarKiosk',
        update_method=async_update_data,
        update_interval=timedelta(seconds=300),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities([
        FusionSolarPowerEntityRealtime(
            coordinator,
            f'{DOMAIN}-{kiosk.id}-{ID_REALTIME_POWER}',
            f'{kiosk.name} ({kiosk.id}) - {NAME_REALTIME_POWER}',
            ATTR_REALTIME_POWER,
            f'{DOMAIN}-{kiosk.id}',
        ),

        FusionSolarEnergySensorTotalCurrentDay(
            coordinator,
            f'{DOMAIN}-{kiosk.id}-{ID_TOTAL_CURRENT_DAY_ENERGY}',
            f'{kiosk.name} ({kiosk.id}) - {NAME_TOTAL_CURRENT_DAY_ENERGY}',
            ATTR_TOTAL_CURRENT_DAY_ENERGY,
            f'{DOMAIN}-{kiosk.id}',
        ),
        FusionSolarEnergySensorTotalCurrentMonth(
            coordinator,
            f'{DOMAIN}-{kiosk.id}-{ID_TOTAL_CURRENT_MONTH_ENERGY}',
            f'{kiosk.name} ({kiosk.id}) - {NAME_TOTAL_CURRENT_MONTH_ENERGY}',
            ATTR_TOTAL_CURRENT_MONTH_ENERGY,
            f'{DOMAIN}-{kiosk.id}',
        ),
        FusionSolarEnergySensorTotalCurrentYear(
            coordinator,
            f'{DOMAIN}-{kiosk.id}-{ID_TOTAL_CURRENT_YEAR_ENERGY}',
            f'{kiosk.name} ({kiosk.id}) - {NAME_TOTAL_CURRENT_YEAR_ENERGY}',
            ATTR_TOTAL_CURRENT_YEAR_ENERGY,
            f'{DOMAIN}-{kiosk.id}',
        ),
        FusionSolarEnergySensorTotalLifetime(
            coordinator,
            f'{DOMAIN}-{kiosk.id}-{ID_TOTAL_LIFETIME_ENERGY}',
            f'{kiosk.name} ({kiosk.id}) - {NAME_TOTAL_LIFETIME_ENERGY}',
            ATTR_TOTAL_LIFETIME_ENERGY,
            f'{DOMAIN}-{kiosk.id}',
        )
    ])


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)

    for kioskConfig in config[CONF_KIOSKS]:
        kiosk = Kiosk(kioskConfig[CONF_URL], kioskConfig[CONF_NAME])
        await add_entities_for_kiosk(hass, async_add_entities, kiosk)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    for kioskConfig in config[CONF_KIOSKS]:
        kiosk = Kiosk(kioskConfig[CONF_URL], kioskConfig[CONF_NAME])
        await add_entities_for_kiosk(hass, async_add_entities, kiosk)
