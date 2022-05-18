import logging
import uuid

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from . import AlertsDataUpdateCoordinator

from .const import (
    ATTRIBUTION,
    CONF_TIMEOUT,
    CONF_TEAM_ID,
    COORDINATOR,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TEAM_ID): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Configuration from yaml"""
    if DOMAIN not in hass.data.keys():
        hass.data.setdefault(DOMAIN, {})
        config.entry_id = slugify(f"{config.get(CONF_TEAM_ID)}")
        config.data = config
    else:
        config.entry_id = slugify(f"{config.get(CONF_TEAM_ID)}")
        config.data = config

    # Setup the data coordinator
    coordinator = AlertsDataUpdateCoordinator(
        hass,
        config,
        config[CONF_TIMEOUT],
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN][config.entry_id] = {
        COORDINATOR: coordinator,
    }
    async_add_entities([MLBScoresSensor(hass, config)], True)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup the sensor platform."""
    async_add_entities([MLBScoresSensor(hass, entry)], True)


class MLBScoresSensor(CoordinatorEntity):
    """Representation of a Sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(hass.data[DOMAIN][entry.entry_id][COORDINATOR])
        self._config = entry
        self._name = entry.data[CONF_NAME]
        self._icon = DEFAULT_ICON
        self._state = "PRE"
        self._game_length = None
        self._date = None
        self._game_end_time = None
        self._attendance = None
        self._event_name = None
        self._event_short_name = None
        self._venue_name = None
        self._venue_city = None
        self._venue_state = None
        self._venue_capacity = None
        self._venue_indoor = None
        self._inning = None
        self._inning_description = None
        self._weather_conditions = None
        self._weather_temp = None
        self._winning_pitcher = None
        self._winning_pitcher_wins = None
        self._winning_pitcher_losses = None
        self._winning_pitcher_era = None
        self._losing_pitcher = None
        self._losing_pitcher_wins = None
        self._losing_pitcher_losses = None
        self._losing_pitcher_era = None
        self._saving_pitcher = None
        self._saving_pitcher_saves = None
        self._game_status = None
        self._home_team_abbr = None
        self._home_team_id = None
        self._home_team_city = None
        self._home_team_name = None
        self._home_team_color = None
        self._home_team_alt_color = None
        self._home_team_logo = None
        self._home_team_runs = None
        self._home_team_hits = None
        self._home_team_errors = None
        self._home_team_colors = None
        self._home_team_ls_1 = None
        self._home_team_ls_2 = None
        self._home_team_ls_3 = None
        self._home_team_ls_4 = None
        self._home_team_ls_5 = None
        self._home_team_ls_6 = None
        self._home_team_ls_7 = None
        self._home_team_ls_8 = None
        self._home_team_ls_9 = None
        self._home_team_record = None
        self._away_team_abbr = None
        self._away_team_id = None
        self._away_team_city = None
        self._away_team_name = None
        self._away_team_color = None
        self._away_team_alt_color = None
        self._away_team_logo = None
        self._away_team_runs = None
        self._away_team_hits = None
        self._away_team_errors = None
        self._away_team_colors = None
        self._away_team_ls_1 = None
        self._away_team_ls_2 = None
        self._away_team_ls_3 = None
        self._away_team_ls_4 = None
        self._away_team_ls_5 = None
        self._away_team_ls_6 = None
        self._away_team_ls_7 = None
        self._away_team_ls_8 = None
        self._away_team_ls_9 = None
        self._away_team_record = None
        self._first_pitch_in = None
        self._tv_network = None
        self._last_play = None
        self._balls = None
        self._strikes = None
        self._outs = None
        self._runner_on_1st = None
        self._runner_on_2nd = None
        self._runner_on_3rd = None
        self._current_batter = None
        self._current_pitcher = None
        self._home_team_starting_pitcher = None
        self._away_team_starting_pitcher = None
        self._odds = None
        self._overunder = None
        self._home_team_odds_win_pct = None
        self._away_team_odds_win_pct = None
        self._headlines = None
        self._win_or_loss = None
        self._last_update = None
        self._team_id = entry.data[CONF_TEAM_ID]
        self.coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
        
        
        
        #self._kickoff_in = None
        #self._quarter = None
        #self._clock = None
        #self._venue = None
        #self._location = None
        #self._tv_network = None
        #self._odds = None
        #self._overunder = None
        #self._possession = None
        #self._last_play = None
        #self._down_distance_text = None
        #self._team_abbr = None
        #self._team_id = None
        #self._team_name = None
        #self._team_record = None
        #self._team_homeaway = None
        #self._team_logo = None
        #self._team_colors = None
        #self._team_score = None
        #self._team_win_probability = None
        #self._team_timeouts = None
        #self._opponent_abbr = None
        #self._opponent_id = None
        #self._opponent_name = None
        #self._opponent_record = None
        #self._opponent_homeaway = None
        #self._opponent_logo = None
        #self._opponent_colors = None
        #self._opponent_score = None
        #self._opponent_win_probability = None
        #self._opponent_timeouts = None
        #self._team_id = entry.data[CONF_TEAM_ID]

    @property
    def unique_id(self):
        """
        Return a unique, Home Assistant friendly identifier for this entity.
        """
        return f"{slugify(self._name)}_{self._config.entry_id}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        elif "state" in self.coordinator.data.keys():
            return self.coordinator.data["state"]
        else:
            return None

    @property
    def extra_state_attributes(self):
        """Return the state message."""
        attrs = {}

        if self.coordinator.data is None:
            return attrs

        attrs[ATTR_ATTRIBUTION] = ATTRIBUTION
        attrs["game_length"] = self.coordinator.data["game_length"]
        attrs["date"] = self.coordinator.data["date"]
        attrs["game_end_time"] = self.coordinator.data["game_end_time"]
        attrs["attendance"] = self.coordinator.data["attendance"]
        attrs["event_name"] = self.coordinator.data["event_name"]
        attrs["event_short_name"] = self.coordinator.data["event_short_name"]
        attrs["venue_name"] = self.coordinator.data["venue_name"]
        attrs["venue_city"] = self.coordinator.data["venue_city"]
        attrs["venue_state"] = self.coordinator.data["venue_state"]
        attrs["venue_capacity"] = self.coordinator.data["venue_capacity"]
        attrs["venue_indoor"] = self.coordinator.data["venue_indoor"]
        attrs["inning"] = self.coordinator.data["inning"]
        attrs["inning_description"] = self.coordinator.data["inning_description"]
        attrs["weather_conditions"] = self.coordinator.data["weather_conditions"]
        attrs["weather_temp"] = self.coordinator.data["weather_temp"]
        attrs["winning_pitcher"] = self.coordinator.data["winning_pitcher"]
        attrs["winning_pitcher_wins"] = self.coordinator.data["winning_pitcher_wins"]
        attrs["winning_pitcher_losses"] = self.coordinator.data["winning_pitcher_losses"]
        attrs["winning_pitcher_era"] = self.coordinator.data["winning_pitcher_era"]
        attrs["losing_pitcher"] = self.coordinator.data["losing_pitcher"]
        attrs["losing_pitcher_wins"] = self.coordinator.data["losing_pitcher_wins"]
        attrs["losing_pitcher_losses"] = self.coordinator.data["losing_pitcher_losses"]
        attrs["losing_pitcher_era"] = self.coordinator.data["losing_pitcher_era"]
        attrs["saving_pitcher"] = self.coordinator.data["saving_pitcher"]
        attrs["saving_pitcher_saves"] = self.coordinator.data["saving_pitcher_saves"]
        attrs["game_status"] = self.coordinator.data["game_status"]
        attrs["home_team_abbr"] = self.coordinator.data["home_team_abbr"]
        attrs["home_team_id"] = self.coordinator.data["home_team_id"]
        attrs["home_team_city"] = self.coordinator.data["home_team_city"]
        attrs["home_team_name"] = self.coordinator.data["home_team_name"]
        attrs["home_team_color"] = self.coordinator.data["home_team_color"]
        attrs["home_team_alt_color"] = self.coordinator.data["home_team_alt_color"]
        attrs["home_team_logo"] = self.coordinator.data["home_team_logo"]
        attrs["home_team_runs"] = self.coordinator.data["home_team_runs"]
        attrs["home_team_hits"] = self.coordinator.data["home_team_hits"]
        attrs["home_team_errors"] = self.coordinator.data["home_team_errors"]
        attrs["home_team_colors"] = self.coordinator.data["home_team_colors"]
        attrs["home_team_ls_1"] = self.coordinator.data["home_team_ls_1"]
        attrs["home_team_ls_2"] = self.coordinator.data["home_team_ls_2"]
        attrs["home_team_ls_3"] = self.coordinator.data["home_team_ls_3"]
        attrs["home_team_ls_4"] = self.coordinator.data["home_team_ls_4"]
        attrs["home_team_ls_5"] = self.coordinator.data["home_team_ls_5"]
        attrs["home_team_ls_6"] = self.coordinator.data["home_team_ls_6"]
        attrs["home_team_ls_7"] = self.coordinator.data["home_team_ls_7"]
        attrs["home_team_ls_8"] = self.coordinator.data["home_team_ls_8"]
        attrs["home_team_ls_9"] = self.coordinator.data["home_team_ls_9"]
        attrs["home_team_record"] = self.coordinator.data["home_team_record"]
        attrs["away_team_abbr"] = self.coordinator.data["away_team_abbr"]
        attrs["away_team_id"] = self.coordinator.data["away_team_id"]
        attrs["away_team_city"] = self.coordinator.data["away_team_city"]
        attrs["away_team_name"] = self.coordinator.data["away_team_name"]
        attrs["away_team_color"] = self.coordinator.data["away_team_color"]
        attrs["away_team_alt_color"] = self.coordinator.data["away_team_alt_color"]
        attrs["away_team_logo"] = self.coordinator.data["away_team_logo"]
        attrs["away_team_runs"] = self.coordinator.data["away_team_runs"]
        attrs["away_team_hits"] = self.coordinator.data["away_team_hits"]
        attrs["away_team_errors"] = self.coordinator.data["away_team_errors"]
        attrs["away_team_colors"] = self.coordinator.data["away_team_colors"]
        attrs["away_team_ls_1"] = self.coordinator.data["away_team_ls_1"]
        attrs["away_team_ls_2"] = self.coordinator.data["away_team_ls_2"]
        attrs["away_team_ls_3"] = self.coordinator.data["away_team_ls_3"]
        attrs["away_team_ls_4"] = self.coordinator.data["away_team_ls_4"]
        attrs["away_team_ls_5"] = self.coordinator.data["away_team_ls_5"]
        attrs["away_team_ls_6"] = self.coordinator.data["away_team_ls_6"]
        attrs["away_team_ls_7"] = self.coordinator.data["away_team_ls_7"]
        attrs["away_team_ls_8"] = self.coordinator.data["away_team_ls_8"]
        attrs["away_team_ls_9"] = self.coordinator.data["away_team_ls_9"]
        attrs["away_team_record"] = self.coordinator.data["away_team_record"]
        attrs["first_pitch_in"] = self.coordinator.data["first_pitch_in"]
        attrs["tv_network"] = self.coordinator.data["tv_network"]
        attrs["last_play"] = self.coordinator.data["last_play"]
        attrs["balls"] = self.coordinator.data["balls"]
        attrs["strikes"] = self.coordinator.data["strikes"]
        attrs["outs"] = self.coordinator.data["outs"]
        attrs["runner_on_1st"] = self.coordinator.data["runner_on_1st"]
        attrs["runner_on_2nd"] = self.coordinator.data["runner_on_2nd"]
        attrs["runner_on_3rd"] = self.coordinator.data["runner_on_3rd"]
        attrs["current_batter"] = self.coordinator.data["current_batter"]
        attrs["current_pitcher"] = self.coordinator.data["current_pitcher"]
        attrs["home_team_starting_pitcher"] = self.coordinator.data["home_team_starting_pitcher"]
        attrs["away_team_starting_pitcher"] = self.coordinator.data["away_team_starting_pitcher"]
        attrs["odds"] = self.coordinator.data["odds"]
        attrs["overunder"] = self.coordinator.data["overunder"]
        attrs["home_team_odds_win_pct"] = self.coordinator.data["home_team_odds_win_pct"]
        attrs["away_team_odds_win_pct"] = self.coordinator.data["away_team_odds_win_pct"]
        attrs["headlines"] = self.coordinator.data["headlines"]
        attrs["win_or_loss"] = self.coordinator.data["win_or_loss"]
        attrs["last_update"] = self.coordinator.data["last_update"]
      
        
        
        #attrs["kickoff_in"] = self.coordinator.data["kickoff_in"]
        #attrs["quarter"] = self.coordinator.data["quarter"]
        #attrs["clock"] = self.coordinator.data["clock"]
        #attrs["venue"] = self.coordinator.data["venue"]
        #attrs["location"] = self.coordinator.data["location"]
        #attrs["tv_network"] = self.coordinator.data["tv_network"]
        #attrs["odds"] = self.coordinator.data["odds"]
        #attrs["overunder"] = self.coordinator.data["overunder"]
        #attrs["possession"] = self.coordinator.data["possession"]
        #attrs["last_play"] = self.coordinator.data["last_play"]
        #attrs["down_distance_text"] = self.coordinator.data["down_distance_text"]
        #attrs["team_abbr"] = self.coordinator.data["team_abbr"]
        #attrs["team_id"] = self.coordinator.data["team_id"]
        #attrs["team_name"] = self.coordinator.data["team_name"]
        #attrs["team_record"] = self.coordinator.data["team_record"]
        #attrs["team_homeaway"] = self.coordinator.data["team_homeaway"]
        #attrs["team_logo"] = self.coordinator.data["team_logo"]
        #attrs["team_colors"] = self.coordinator.data["team_colors"]
        #attrs["team_score"] = self.coordinator.data["team_score"]
        #attrs["team_win_probability"] = self.coordinator.data["team_win_probability"]
        #attrs["team_timeouts"] = self.coordinator.data["team_timeouts"]
        #attrs["opponent_abbr"] = self.coordinator.data["opponent_abbr"]
        #attrs["opponent_id"] = self.coordinator.data["opponent_id"]
        #attrs["opponent_name"] = self.coordinator.data["opponent_name"]
        #attrs["opponent_record"] = self.coordinator.data["opponent_record"]
        #attrs["opponent_homeaway"] = self.coordinator.data["opponent_homeaway"]
        #attrs["opponent_logo"] = self.coordinator.data["opponent_logo"]
        #attrs["opponent_colors"] = self.coordinator.data["opponent_colors"]
        #attrs["opponent_score"] = self.coordinator.data["opponent_score"]
        #attrs["opponent_win_probability"] = self.coordinator.data["opponent_win_probability"]
        #attrs["opponent_timeouts"] = self.coordinator.data["opponent_timeouts"]
        #attrs["last_update"] = self.coordinator.data["last_update"]

        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
