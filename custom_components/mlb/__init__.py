""" MLB Team Status """
import logging
from datetime import timedelta
from datetime import datetime
import arrow
import time

import aiohttp
from async_timeout import timeout
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_SCOREBOARD_ENDPOINT,
    API_TEAM_ENDPOINT,
    CONF_TIMEOUT,
    CONF_TEAM_ID,
    COORDINATOR,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ISSUE_URL,
    PLATFORMS,
    USER_AGENT,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

today = datetime.today().strftime('%Y-%m-%d')

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    _LOGGER.info(offset)
    return utc_datetime + offset

_LOGGER.info(
        "Debugging todays date and time: %s",
        datetime.now(),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load the saved entities."""
    # Print startup message
    _LOGGER.info(
        "MLB version %s is starting, if you have any issues please report them here: %s",
        VERSION,
        ISSUE_URL,
    )
    hass.data.setdefault(DOMAIN, {})

    if entry.unique_id is not None:
        hass.config_entries.async_update_entry(entry, unique_id=None)

        ent_reg = async_get(hass)
        for entity in async_entries_for_config_entry(ent_reg, entry.entry_id):
            ent_reg.async_update_entity(entity.entity_id, new_unique_id=entry.entry_id)

    # Setup the data coordinator
    coordinator = AlertsDataUpdateCoordinator(
        hass,
        entry.data,
        entry.data.get(CONF_TIMEOUT)
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the " + DOMAIN + " integration")
    except ValueError:
        pass
    return True


async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

async def async_migrate_entry(hass, config_entry):
     """Migrate an old config entry."""
     version = config_entry.version

     # 1-> 2: Migration format
     if version == 1:
         _LOGGER.debug("Migrating from version %s", version)
         updated_config = config_entry.data.copy()

         if CONF_TIMEOUT not in updated_config.keys():
             updated_config[CONF_TIMEOUT] = DEFAULT_TIMEOUT

         if updated_config != config_entry.data:
             hass.config_entries.async_update_entry(config_entry, data=updated_config)

         config_entry.version = 2
         _LOGGER.debug("Migration to version %s complete", config_entry.version)

     return True

class AlertsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MLB data."""

    def __init__(self, hass, config, the_timeout: int):
        """Initialize."""
        self.interval = timedelta(minutes=20)
        self.name = config[CONF_NAME]
        self.timeout = the_timeout
        self.config = config
        self.hass = hass

        _LOGGER.debug("Data will be updated every %s", self.interval)

        super().__init__(hass, _LOGGER, name=self.name, update_interval=self.interval)

    async def _async_update_data(self):
        """Fetch data"""
        async with timeout(self.timeout):
            try:
                data = await update_game(self.config)
                # update the interval based on flag
                if data["private_fast_refresh"] == True:
                    self.update_interval = timedelta(seconds=5)
                else:
                    self.update_interval = timedelta(minutes=20)
            except Exception as error:
                raise UpdateFailed(error) from error
            return data
        


async def update_game(config) -> dict:
    """Fetch new state data for the sensor.
    This is the only method that should fetch new data for Home Assistant.
    """

    data = await async_get_state(config)
    return data

async def async_get_state(config) -> dict:
    """Query API for status."""

    values = {}
    headers = {"User-Agent": USER_AGENT, "Accept": "application/ld+json"}
    data = None
    gameday_url = API_SCOREBOARD_ENDPOINT
    team_id = config[CONF_TEAM_ID]
    async with aiohttp.ClientSession() as session:
        async with session.get(gameday_url, headers=headers) as r:
            _LOGGER.debug("Getting state for %s from %s" % (team_id, gameday_url))
            if r.status == 200:
                data = await r.json()

    found_team = False
    if data is not None:
        for event in data["events"]:
            #_LOGGER.debug("Looking at this event: %s" % event)
            if team_id in event["shortName"]:
                _LOGGER.debug("Found team event for %s; parsing data." % (team_id))
                found_team = True
                # Determine whether our team is Competitor 0 or 1
                team_index = 0 if event["competitions"][0]["competitors"][0]["team"]["abbreviation"] == team_id else 1
                team_home_away = event["competitions"][0]["competitors"][team_index]["homeAway"]
                oppo_index = abs((team_index-1))
                
                try:
                    values["state"] = event["status"]["type"]["name"]
                except:
                    values["state"] = None
                
                try:
                    values["date"] = event["date"]
                except:
                    values["date"] = None
                
                try:
                    values["attendance"] = event["competitions"][0]["attendance"]
                except:
                    values["attendance"] = None
                
                # Formatted as full team names like "New York Mets at Washington Nationals"
                try:
                    values["event_name"] = event["name"]
                except:
                    values["event_name"] = None
                
                # Formatted as abbreviations like "NYM @ WSH"
                try:
                    values["event_short_name"] = event["shortName"]
                except:
                    values["event_short_name"] = None

                 # Formatted as "STD", "RD16", "QTR"
                try:
                    values["event_type"] = event["competitions"][0]["type"]["abbreviation"]
                except:
                    values["event_type"] = None
                
                # Formatted as "East 1st Round - Game 7", "East 2nd Round - Game 1"
                try:
                    values["game_notes"] = event["competitions"][0]["notes"][0]["headline"]
                except:
                    values["game_notes"] = None
                
                # Formatted as "Series Tied 3-3"
                try:
                    values["series_summary"] = event["competitions"][0]["series"]["summary"]
                except:
                    values["series_summary"] = None   
            
                try:
                    values["venue_name"] = event["competitions"][0]["venue"]["fullName"]
                except:
                    values["venue_name"] = None
                
                try:
                    values["venue_city"] = event["competitions"][0]["venue"]["address"]["city"]
                except:
                    values["venue_city"] = None
                
                try:
                    values["venue_state"] = event["competitions"][0]["venue"]["address"]["state"]
                except:
                    values["venue_state"] = None
                
                try:
                    values["venue_capacity"] = event["competitions"][0]["venue"]["capacity"]
                except:
                    values["venue_capacity"] = None
                
                # Formatted as true/false
                try:
                    values["venue_indoor"] = event["competitions"][0]["venue"]["indoor"]
                except:
                    values["venue_indoor"] = None
                
                # Formatted as an integer like "3"
                try:
                    values["inning"] = event["competitions"][0]["status"]["period"]
                except:
                    values["inning"] = None
                
                # Formatted like "Top 3rd"
                try:
                    values["inning_description"] = event["competitions"][0]["status"]["type"]["shortDetail"]
                except:
                    values["inning_description"] = None
                
                # Formatted like "Mostly clear"
                try:
                    values["weather_conditions"] = event["weather"]["displayValue"]
                except:
                    values["weather_conditions"] = None

                # Integer like "68"
                try:
                    values["weather_temp"] = event["weather"]["temperature"]
                except:
                    values["weather_temp"] = None

                if values["state"] in ['STATUS_FINAL']:
                    try:
                        featuredAthlete_0_Type = event["competitions"][0]["status"]["featuredAthletes"][0]["name"]
                    except:
                        featuredAthlete_0_Type = None

                    try:
                        featuredAthlete_1_Type = event["competitions"][0]["status"]["featuredAthletes"][1]["name"]
                    except:
                        featuredAthlete_1_Type = None

                    try:
                        featuredAthlete_2_Type = event["competitions"][0]["status"]["featuredAthletes"][2]["name"]

                    except:
                        featuredAthlete_2_Type = None

                    wp_index = -1
                    lp_index = -1
                    sp_index = -1

                    if featuredAthlete_0_Type == 'winningPitcher':
                        wp_index = 0
                    elif featuredAthlete_0_Type == 'losingPitcher':
                        lp_index = 0
                    elif featuredAthlete_0_Type == 'savingPitcher':
                        sp_index = 0

                    if featuredAthlete_1_Type == 'winningPitcher':
                        wp_index = 1
                    elif featuredAthlete_1_Type == 'losingPitcher':
                        lp_index = 1
                    elif featuredAthlete_1_Type == 'savingPitcher':
                        sp_index = 1

                    if featuredAthlete_2_Type == 'winningPitcher':
                        wp_index = 2
                    elif featuredAthlete_2_Type == 'losingPitcher':
                        lp_index = 2
                    elif featuredAthlete_2_Type == 'savingPitcher':
                        sp_index = 2

                    try:
                        values["winning_pitcher"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["athlete"]["fullName"]
                    except:
                        values["winning_pitcher"] = None
                    
                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["name"] == "wins":
                            values["winning_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["displayValue"]
                        else:
                            values["winning_pitcher_wins"] = None
                    except:
                        values["winning_pitcher_wins"] = None
                    
                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["name"] == "losses":
                            values["winning_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["displayValue"]
                        else:
                            values["winning_pitcher_losses"] = None
                    except:
                        values["winning_pitcher_losses"] = None

                    
                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["name"] == "ERA":
                            values["winning_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][wp_index]["statistics"][6]["displayValue"]
                        else:
                            values["winning_pitcher_era"] = None
                    except:
                        values["winning_pitcher_era"] = None

                    try:
                        values["losing_pitcher"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["athlete"]["fullName"]
                    except:
                        values["losing_pitcher"] = None
                        

                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["name"] == "wins":
                            values["losing_pitcher_wins"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["displayValue"]
                        else:
                            values["losing_pitcher_wins"] = None
                    except:
                        values["losing_pitcher_wins"] = None
                    
                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["name"] == "losses":
                            values["losing_pitcher_losses"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["displayValue"]
                        else:
                            values["losing_pitcher_losses"] = None
                    except:
                        values["losing_pitcher_losses"] = None

                    
                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["name"] == "ERA":
                            values["losing_pitcher_era"] = event["competitions"][0]["status"]["featuredAthletes"][lp_index]["statistics"][6]["displayValue"]
                        else:
                            values["losing_pitcher_era"] = None
                    except:
                        values["losing_pitcher_era"] = None

                    try:
                        values["saving_pitcher"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["athlete"]["fullName"]
                    except:
                        values["saving_pitcher"] = None
                        

                    try:
                        if event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][0]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][0]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][1]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][1]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][2]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][2]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][3]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][3]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][4]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][4]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][5]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][5]["displayValue"]
                        elif event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][6]["name"] == "saves":
                            values["saving_pitcher_saves"] = event["competitions"][0]["status"]["featuredAthletes"][sp_index]["statistics"][6]["displayValue"]
                        else:
                            values["saving_pitcher_saves"] = None
                    except:
                        values["saving_pitcher_saves"] = None
                    

                else:
                    values["winning_pitcher"] = None
                    values["winning_pitcher_wins"] = None
                    values["winning_pitcher_losses"] = None
                    values["winning_pitcher_era"] = None
                    values["losing_pitcher"] = None
                    values["losing_pitcher_wins"] = None
                    values["losing_pitcher_losses"] = None
                    values["losing_pitcher_era"] = None
                    values["saving_pitcher"] = None
                    values["saving_pitcher_saves"] = None


                try:
                    values["game_status"] = event["status"]["type"]["shortDetail"]
                except:
                    values["game_status"] = None
                
                values["home_team_abbr"] = event["competitions"][0]["competitors"][0]["team"]["abbreviation"]
                values["home_team_id"] = event["competitions"][0]["competitors"][0]["team"]["id"]
                values["home_team_city"] = event["competitions"][0]["competitors"][0]["team"]["location"]
                values["home_team_name"] = event["competitions"][0]["competitors"][0]["team"]["name"]
                values["home_team_color"] = event["competitions"][0]["competitors"][0]["team"]["color"]
                values["home_team_alt_color"] = event["competitions"][0]["competitors"][0]["team"]["alternateColor"]
                values["home_team_logo"] = event["competitions"][0]["competitors"][0]["team"]["logo"]
                values["home_team_runs"] = event["competitions"][0]["competitors"][0]["score"]
                values["home_team_hits"] = event["competitions"][0]["competitors"][0]["hits"]
                values["home_team_errors"] = event["competitions"][0]["competitors"][0]["errors"]

                try:
                    values["home_team_colors"] = [''.join(('#',event["competitions"][0]["competitors"][0]["team"]["color"])), 
                        ''.join(('#',event["competitions"][0]["competitors"][0]["team"]["alternateColor"]))]
                except:
                    values["home_team_colors"] = ['#013369','#013369']
                
                try:
                    values["home_team_ls_1"] = event["competitions"][0]["competitors"][0]["linescores"][0]["value"]
                except:
                    values["home_team_ls_1"] = None

                try:
                    values["home_team_ls_2"] = event["competitions"][0]["competitors"][0]["linescores"][1]["value"]
                except:
                    values["home_team_ls_2"] = None

                try:
                    values["home_team_ls_3"] = event["competitions"][0]["competitors"][0]["linescores"][2]["value"]
                except:
                    values["home_team_ls_3"] = None

                try:
                    values["home_team_ls_4"] = event["competitions"][0]["competitors"][0]["linescores"][3]["value"]
                except:
                    values["home_team_ls_4"] = None

                try:
                    values["home_team_ls_5"] = event["competitions"][0]["competitors"][0]["linescores"][4]["value"]
                except:
                    values["home_team_ls_5"] = None

                try:
                    values["home_team_ls_6"] = event["competitions"][0]["competitors"][0]["linescores"][5]["value"]
                except:
                    values["home_team_ls_6"] = None

                try:
                    values["home_team_ls_7"] = event["competitions"][0]["competitors"][0]["linescores"][6]["value"]
                except:
                    values["home_team_ls_7"] = None

                try:
                    values["home_team_ls_8"] = event["competitions"][0]["competitors"][0]["linescores"][7]["value"]
                except:
                    values["home_team_ls_8"] = None

                try:
                    values["home_team_ls_9"] = event["competitions"][0]["competitors"][0]["linescores"][8]["value"]
                except:
                    values["home_team_ls_9"] = None
                
                values["home_team_record"] = event["competitions"][0]["competitors"][0]["records"][0]["summary"]
                
                values["away_team_abbr"] = event["competitions"][0]["competitors"][1]["team"]["abbreviation"]
                values["away_team_id"] = event["competitions"][0]["competitors"][1]["team"]["id"]
                values["away_team_city"] = event["competitions"][0]["competitors"][1]["team"]["location"]
                values["away_team_name"] = event["competitions"][0]["competitors"][1]["team"]["name"]
                values["away_team_color"] = event["competitions"][0]["competitors"][1]["team"]["color"]
                values["away_team_alt_color"] = event["competitions"][0]["competitors"][1]["team"]["alternateColor"]
                values["away_team_logo"] = event["competitions"][0]["competitors"][1]["team"]["logo"]
                values["away_team_runs"] = event["competitions"][0]["competitors"][1]["score"]
                values["away_team_hits"] = event["competitions"][0]["competitors"][1]["hits"]
                values["away_team_errors"] = event["competitions"][0]["competitors"][1]["errors"]

                try:
                    values["away_team_colors"] = [''.join(('#',event["competitions"][0]["competitors"][1]["team"]["color"])), 
                        ''.join(('#',event["competitions"][0]["competitors"][1]["team"]["alternateColor"]))]
                except:
                    values["away_team_colors"] = ['#D50A0A','#D50A0A']
                
                #if event["status"]["type"]["state"].lower() in ['in']:
                try:
                    values["away_team_ls_1"] = event["competitions"][0]["competitors"][1]["linescores"][0]["value"]
                except:
                    values["away_team_ls_1"] = None

                try:
                    values["away_team_ls_2"] = event["competitions"][0]["competitors"][1]["linescores"][1]["value"]
                except:
                    values["away_team_ls_2"] = None

                try:
                    values["away_team_ls_3"] = event["competitions"][0]["competitors"][1]["linescores"][2]["value"]
                except:
                    values["away_team_ls_3"] = None

                try:
                    values["away_team_ls_4"] = event["competitions"][0]["competitors"][1]["linescores"][3]["value"]
                except:
                    values["away_team_ls_4"] = None

                try:
                    values["away_team_ls_5"] = event["competitions"][0]["competitors"][1]["linescores"][4]["value"]
                except:
                    values["away_team_ls_5"] = None

                try:
                    values["away_team_ls_6"] = event["competitions"][0]["competitors"][1]["linescores"][5]["value"]
                except:
                    values["away_team_ls_6"] = None

                try:
                    values["away_team_ls_7"] = event["competitions"][0]["competitors"][1]["linescores"][6]["value"]
                except:
                    values["away_team_ls_7"] = None

                try:
                    values["away_team_ls_8"] = event["competitions"][0]["competitors"][1]["linescores"][7]["value"]
                except:
                    values["away_team_ls_8"] = None

                try:
                    values["away_team_ls_9"] = event["competitions"][0]["competitors"][1]["linescores"][8]["value"]
                except:
                    values["away_team_ls_9"] = None
                
                values["away_team_record"] = event["competitions"][0]["competitors"][1]["records"][0]["summary"]
                
                values["first_pitch_in"] = arrow.get(event["date"]).humanize()
                
                try:
                    values["tv_network"] = event["competitions"][0]["broadcasts"][0]["names"]
                except:
                    values["tv_network"] = None
                
                try:
                    values["last_play"] = event["competitions"][0]["situation"]["lastPlay"]["text"]
                except:
                    values["last_play"] = None

                try:
                    values["balls"] = event["competitions"][0]["situation"]["balls"]
                except:
                    values["balls"] = None

                try:
                    values["strikes"] = event["competitions"][0]["situation"]["strikes"]
                except:
                    values["strikes"] = None

                try:
                    values["outs"] = event["competitions"][0]["situation"]["outs"]
                except:
                    values["outs"] = None
                
                try:
                    values["runner_on_1st"] = event["competitions"][0]["situation"]["onFirst"]
                except:
                    values["runner_on_1st"] = None
                
                try:
                    values["runner_on_2nd"] = event["competitions"][0]["situation"]["onSecond"]
                except:
                    values["runner_on_2nd"] = None
                
                try:
                    values["runner_on_3rd"] = event["competitions"][0]["situation"]["onThird"]
                except:
                    values["runner_on_3rd"] = None
                
                try:
                    values["current_batter"] = event["competitions"][0]["situation"]["batter"]["athlete"]["fullName"]
                except:
                    values["current_batter"] = None
                    
                try:
                    values["current_pitcher"] = event["competitions"][0]["situation"]["pitcher"]["athlete"]["fullName"]
                except:
                    values["current_pitcher"] = None
                
                # Starting Pitcher
                try:
                    values["home_team_starting_pitcher"] = event["competitions"][0]["competitors"][0]["probables"][0]["athlete"]["displayName"]
                except:
                    values["home_team_starting_pitcher"] = None
                
                try:
                    values["away_team_starting_pitcher"] = event["competitions"][0]["competitors"][1]["probables"][0]["athlete"]["displayName"]
                except:
                    values["away_team_starting_pitcher"] = None
                
                try:
                    values["odds"] = event["competitions"][0]["odds"][0]["details"]
                except:
                    values["odds"] = None
                    
                try:
                    values["overunder"] = event["competitions"][0]["odds"][0]["overUnder"]
                except:
                    values["overunder"] = None
                
                try:
                    values["home_team_odds_win_pct"] = event["competitions"][0]["odds"][1]["homeTeamOdds"]["winPercentage"]
                except:
                    values["home_team_odds_win_pct"] = None
                
                try:
                    values["away_team_odds_win_pct"] = event["competitions"][0]["odds"][1]["awayTeamOdds"]["winPercentage"]
                except:
                    values["away_team_odds_win_pct"] = None
                
                try:
                    values["headlines"] = event["competitions"][0]["headlines"][0]["shortLinkText"]
                except:
                    values["headlines"] = None

                try:
                    if values["state"] in ['STATUS_FINAL']:
                        if values["home_team_abbr"] == team_id:
                            if values["home_team_runs"] > values["away_team_runs"]:
                                values["win_or_loss"] = "win"
                            else:
                                values["win_or_loss"] = "loss"
                        else:
                            if values["home_team_runs"] > values["away_team_runs"]:
                                values["win_or_loss"] = "loss"
                            else:
                                values["win_or_loss"] = "win"
                    else:
                        values["win_or_loss"] = None
                except:
                    values["win_or_loss"] = None

                if values["state"] in ['STATUS_POSTPONED']:
                    try:
                        values["headlines"] = event["competitions"][0]["notes"][0]["headline"]
                    except:
                        values["headlines"] = None
                
                values["last_update"] = arrow.now().format(arrow.FORMAT_W3C)
                values["private_fast_refresh"] = False
        
        # Never found the team. Either off today or a post-season condition
        if not found_team:
            _LOGGER.debug("Team not found on scoreboard feed.  Using team API.")
            
            team_url = API_TEAM_ENDPOINT + team_id
            _LOGGER.debug(team_url)
            async with aiohttp.ClientSession() as session:
                async with session.get(team_url, headers=headers) as r:
                    if r.status == 200:
                        data = await r.json()
            team_data = data["team"]

            # Determine if our team is home or away.  hoome team is always index 0.
            team_index = 0 if team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["abbreviation"] == team_id else 1
            oppo_index = abs((team_index - 1))
            
            # Determine our opponents team id (abbreviation) so that we can lookup their information as well
            oppo_id = team_data["nextEvent"][0]["competitions"][0]["competitors"][oppo_index]["team"]["abbreviation"]
            oppo_url = API_TEAM_ENDPOINT + oppo_id
            _LOGGER.debug(oppo_url)
            async with aiohttp.ClientSession() as session:
                async with session.get(oppo_url, headers=headers) as r:
                    if r.status == 200:
                        data = await r.json()
            oppo_data = data["team"]

            try:
                values["state"] = team_data["nextEvent"][0]["competitions"][0]["status"]["type"]["name"]
            except:
                values["state"] = None

            try:
                values["date"] = team_data["nextEvent"][0]["date"]
            except:
                values["date"] = None
            
            values["last_update"] = arrow.now().format(arrow.FORMAT_W3C)

            values["attendance"] = None

            try:
                values["event_name"] = team_data["nextEvent"][0]["name"]
            except:
                values["event_name"] = None

            try:
                values["event_short_name"] = team_data["nextEvent"][0]["shortName"]
            except:
                values["event_short_name"] = None

            try:
                values["event_type"] = team_data["nextEvent"][0]["competitions"][0]["type"]["abbreviation"]
            except:
                values["event_type"] = None
            
            try:
                values["game_notes"] = team_data["nextEvent"][0]["competitions"][0]["notes"]["headline"]
            except:
                values["game_notes"] = None
            
            try:
                values["series_summary"] = team_data["nextEvent"][0]["competitions"][0]["series"]["summary"]
            except:
                values["series_summary"] = None
 
            try:           
                values["venue_name"] = team_data["nextEvent"][0]["competitions"][0]["venue"]["fullName"]
            except:
                values["venue_name"] = None

            try:
                values["venue_city"] = team_data["nextEvent"][0]["competitions"][0]["venue"]["address"]["city"]
            except:
                values["venue_city"] = None

            try:
                values["venue_state"] = team_data["nextEvent"][0]["competitions"][0]["venue"]["address"]["state"]
            except:
                values["venue_state"] = None
            
            if team_index == 0:
                try:
                    values["venue_capacity"] = team_data["franchise"]["venue"]["capacity"]
                except:
                    values["venue_capacity"] = None
                
                # Formatted as true/false
                try:
                    values["venue_indoor"] = team_data["franchise"]["venue"]["indoor"]
                except:
                    values["venue_indoor"] = None
            else:
                try:
                    values["venue_capacity"] = oppo_data["franchise"]["venue"]["capacity"]
                except:
                    values["venue_capacity"] = None
                
                # Formatted as true/false
                try:
                    values["venue_indoor"] = oppo_data["franchise"]["venue"]["indoor"]
                except:
                    values["venue_indoor"] = None
                    
            values["inning"] = None
            values["inning_description"] = None
            values["weather_conditions"] = None
            values["weather_temp"] = None
            values["winning_pitcher"] = None
            values["winning_pitcher_wins"] = None
            values["winning_pitcher_losses"] = None
            values["winning_pitcher_era"] = None
            values["losing_pitcher"] = None
            values["losing_pitcher_wins"] = None
            values["losing_pitcher_losses"] = None
            values["losing_pitcher_era"] = None
            values["saving_pitcher"] = None
            values["saving_pitcher_saves"] = None
            values["game_status"] = None

            try:
                values["home_team_abbr"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["abbreviation"]
            except:
                values["home_team_abbr"] = None

            try:
                values["home_team_id"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["id"]
            except:
                values["home_team_id"] = None

            try:
                values["home_team_city"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["location"]
            except:
                values["home_team_city"] = None

            try:
                values["home_team_name"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["shortDisplayName"]
            except:
                values["home_team_name"] = None

            if team_index == 0:
                values["home_team_color"] = team_data["color"]
                values["home_team_alt_color"] = team_data["alternateColor"]
                values["home_team_colors"] = [''.join(('#',team_data["color"])), 
                        ''.join(('#',team_data["alternateColor"]))]

                try:
                    values["home_team_record"] = team_data["record"]["items"][0]["summary"]
                except:
                    values["home_team_record"] = None
            else:
                values["home_team_color"] = oppo_data["color"]
                values["home_team_alt_color"] = oppo_data["alternateColor"]
                values["home_team_colors"] = [''.join(('#',oppo_data["color"])), 
                        ''.join(('#',oppo_data["alternateColor"]))]

                try:
                    values["home_team_record"] = oppo_data["record"]["items"][0]["summary"]
                except:
                    values["home_team_record"] = None

            try:            
                values["home_team_logo"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["team"]["logos"][2]["href"]
            except:
                values["home_team_logo"] = None

            values["home_team_runs"] = None
            values["home_team_hits"] = None
            values["home_team_errors"] = None
            values["home_team_ls_1"] = None
            values["home_team_ls_2"] = None
            values["home_team_ls_3"] = None
            values["home_team_ls_4"] = None
            values["home_team_ls_5"] = None
            values["home_team_ls_6"] = None
            values["home_team_ls_7"] = None
            values["home_team_ls_8"] = None
            values["home_team_ls_9"] = None

            try:
                values["away_team_abbr"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["team"]["abbreviation"]
            except:
                values["away_team_abbr"] = None

            try:
                values["away_team_id"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["team"]["id"]
            except:
                values["away_team_id"] = None

            try:
                values["away_team_city"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["team"]["location"]
            except:
                values["away_team_city"] = None

            try:
                values["away_team_name"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["team"]["shortDisplayName"]
            except:
                values["away_team_name"] = None

            if team_index == 1:
                values["away_team_color"] = team_data["color"]
                values["away_team_alt_color"] = team_data["alternateColor"]
                values["away_team_colors"] = [''.join(('#',team_data["color"])), 
                        ''.join(('#',team_data["alternateColor"]))]

                try:
                    values["away_team_record"] = team_data["record"]["items"][0]["summary"]
                except:
                    values["away_team_record"] = None
            else:
                values["away_team_color"] = oppo_data["color"]
                values["away_team_alt_color"] = oppo_data["alternateColor"]
                values["away_team_colors"] = [''.join(('#',oppo_data["color"])), 
                        ''.join(('#',oppo_data["alternateColor"]))]

                try:
                    values["away_team_record"] = oppo_data["record"]["items"][0]["summary"]
                except:
                    values["away_team_record"] = None

            try:            
                values["away_team_logo"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["team"]["logos"][2]["href"]
            except:
                values["away_team_logo"] = None

            values["away_team_runs"] = None
            values["away_team_hits"] = None
            values["away_team_errors"] = None
            values["away_team_ls_1"] = None
            values["away_team_ls_2"] = None
            values["away_team_ls_3"] = None
            values["away_team_ls_4"] = None
            values["away_team_ls_5"] = None
            values["away_team_ls_6"] = None
            values["away_team_ls_7"] = None
            values["away_team_ls_8"] = None
            values["away_team_ls_9"] = None

            try:
                values["first_pitch_in"] = arrow.get(team_data["nextEvent"][0]["date"]).humanize()  
            except:
                values["first_pitch_in"] = None

            try:     
                values["tv_network"] = team_data["nextEvent"][0]["competitions"][0]["broadcasts"][0]["media"]["shortName"]
            except:
                values["tv_network"] = None

            values["last_play"] = None
            values["balls"] = None
            values["strikes"] = None
            values["outs"] = None
            values["runner_on_1st"] = None
            values["runner_on_2nd"] = None
            values["runner_on_3rd"] = None
            values["current_batter"] = None
            values["current_pitcher"] = None

            try:
                values["home_team_starting_pitcher"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][0]["probables"][0]["athlete"]["displayName"]
            except:
                values["home_team_starting_pitcher"] = None

            try:
                values["away_team_starting_pitcher"] = team_data["nextEvent"][0]["competitions"][0]["competitors"][1]["probables"][0]["athlete"]["displayName"]
            except:
                values["away_team_starting_pitcher"] = None

            values["odds"] = None
            values["overunder"] = None
            values["home_team_odds_win_pct"] = None
            values["away_team_odds_win_pct"] = None
 
            try:
                values["headlines"] = team_data["nextEvent"][0]["competitions"][0]["notes"][0]["headline"]
            except:
                values["headlines"] = None

            values["win_or_loss"] = None

        if values["state"] == 'STATUS_SCHEDULED' and ((arrow.get(values["date"])-arrow.now()).total_seconds() < 1200):
            _LOGGER.debug("Event for %s is within 20 minutes, setting refresh rate to 5 seconds." % (team_id))
            values["private_fast_refresh"] = True
        elif values["state"] == 'STATUS_IN_PROGRESS':
            _LOGGER.debug("Event for %s is in progress, setting refresh rate to 5 seconds." % (team_id))
            values["private_fast_refresh"] = True
        elif values["state"] in ['STATUS_FINAL', 'OFF']: 
            _LOGGER.debug("Event for %s is over, setting refresh back to 20 minutes." % (team_id))
            values["private_fast_refresh"] = False
        else:
            _LOGGER.debug("Event for %s is other state, setting refresh to 20 minutes." % (team_id))
            values["private_fast_refresh"] = False


    return values

async def async_clear_states(config) -> dict:
    """Clear all state attributes"""
    
    values = {}
    # Reset values
    values = {
        "date": None,
        "attendance": None,
        "event_name": None,
        "event_short_name": None,
        "event_type": None,
        "game_notes": None,
        "series_summary": None,
        "venue_name": None,
        "venue_city": None,
        "venue_state": None,
        "venue_capacity": None,
        "venue_indoor": None,
        "inning": None,
        "inning_description": None,
        "weather_conditions": None,
        "weather_temp": None,
        "winning_pitcher": None,
        "winning_pitcher_wins": None,
        "winning_pitcher_losses": None,
        "winning_pitcher_era": None,
        "losing_pitcher": None,
        "losing_pitcher_wins": None,
        "losing_pitcher_losses": None,
        "losing_pitcher_era": None,
        "saving_pitcher": None,
        "saving_pitcher_saves": None,
        "game_status": None,
        "home_team_abbr": None,
        "home_team_id": None,
        "home_team_city": None,
        "home_team_name": None,
        "home_team_color": None,
        "home_team_alt_color": None,
        "home_team_logo": None,
        "home_team_runs": None,
        "home_team_hits": None,
        "home_team_errors": None,
        "home_team_colors": None,
        "home_team_ls_1": None,
        "home_team_ls_2": None,
        "home_team_ls_3": None,
        "home_team_ls_4": None,
        "home_team_ls_5": None,
        "home_team_ls_6": None,
        "home_team_ls_7": None,
        "home_team_ls_8": None,
        "home_team_ls_9": None,
        "home_team_record": None,
        "away_team_abbr": None,
        "away_team_id": None,
        "away_team_city": None,
        "away_team_name": None,
        "away_team_color": None,
        "away_team_alt_color": None,
        "away_team_logo": None,
        "away_team_runs": None,
        "away_team_hits": None,
        "away_team_errors": None,
        "away_team_colors": None,
        "away_team_ls_1": None,
        "away_team_ls_2": None,
        "away_team_ls_3": None,
        "away_team_ls_4": None,
        "away_team_ls_5": None,
        "away_team_ls_6": None,
        "away_team_ls_7": None,
        "away_team_ls_8": None,
        "away_team_ls_9": None,
        "away_team_record": None,
        "first_pitch_in": None,
        "tv_network": None,
        "last_play": None,
        "balls": None,
        "strikes": None,
        "outs": None,
        "runner_on_1st": None,
        "runner_on_2nd": None,
        "runner_on_3rd": None,
        "current_batter": None,
        "current_pitcher": None,
        "home_team_starting_pitcher": None,
        "away_team_starting_pitcher": None,
        "odds": None,
        "overunder": None,
        "home_team_odds_win_pct": None,
        "away_team_odds_win_pct": None,
        "headlines": None,
        "last_update": None,
        "team_id": None,
        "private_fast_refresh": False
    }

    return values
