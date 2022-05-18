# MLB game data in Home Assistant

This integration fetches data for an MLB team's current/future game, and creates a sensor with attributes for the details of the game. 

The integration is a shameless fork of the excellent [NFL](https://github.com/zacs/ha-nfl) custom component by @zacs.

## Sensor Data

### State
The sensor is pretty simple: the main state is `STATUS_SCHEDULED`, `STATUS_IN_PROGRESS`, `STATUS_FINAL`, `STATUS_POSTPONED`, `STATUS_RAIN_DELAY` or `NOT_FOUND`, but there are attributes for pretty much all aspects of the game, when available. State definitions are as you'd expect:
- `STATUS_SCHEDULED`: The game is in pre-game state. 
- `STATUS_IN_PROGRESS`: The game is in progress.
- `STATUS_FINAL`: The game has completed. 
- `STATUS_POSTPONED`: The game has been postponed.
- `STATUS_RAIN_DELAY`: The game is in a rain delay.
- `NOT_FOUND`: There is no game found for your team. This should only happen at the end of the season, and once your team is eliminated from postseason play. 

### Attributes
The attributes available will change based on the sensor's state, a small number are always available (team abbreviation, team name, and logo), but otherwise the attributes only populate when in the current state. The table below lists which attributes are available in which states. 

| Name | Value | Relevant States |
| --- | --- | --- |
| `game_length` | Length of the game | `STATUS_FINAL` |
| `date` | Date and time that the game starts (or started) | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `game_end_time` | Date and time that the game ended | `STATUS_FINAL` |
| `attendance` | Number of fans in attendance | `STATUS_FINAL` |
| `event_name` | Description of the event (eg. "St. Louis Cardinals at New York Mets") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `event_short_name` | Shorter description of the event (eg. "STL @ NYM") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `event_type` | Code indicating the type of event (eg. "STD", "RD16" or "QTR") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `game_notes` | Notes about the game (eg. "East 1st Round - Game 7") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `series_summary` | Current status of the series (eg. "Series Tied 3-3") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `venue_name` | The name of the stadium where the game is being played (eg. "Citi Field") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `venue_city` | The city where the stadium is located (eg. "Queens") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `venue_state` | The state where the stadium is located (eg. "NY") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `venue_capacity` | The capacity of the venue (eg. "41,922") | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `venue_indoor` | An indicator if the venue is indoors (true) or not (false)  | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `inning` | The current inning of the game formatted as an integer (eg. "3") | `STATUS_IN_PROGRESS` |
| `inning_description` | The current inning of the game (eg. "Top 3rd") | `STATUS_IN_PROGRESS` |
| `weather_conditions` | Description of the expected weather conditions | `STATUS_IN_PROGRESS` |
| `weather_temp` | Expected game-time temperature | `STATUS_IN_PROGRESS` |
| `winning_pitcher` | Name of the winning pitcher | `STATUS_FINAL` |
| `winning_pitcher_wins` | An integer representing the number of wins for the winning pitcher | `STATUS_FINAL` |
| `winning_pitcher_losses` | An integer representing the number of losses for the winning pitcher | `STATUS_FINAL` |
| `winning_pitcher_era` | A float representing the ERA for the winning pitcher | `STATUS_FINAL` |
| `losing_pitcher` | Name of the losing pitcher | `STATUS_FINAL` |
| `losing_pitcher_wins` | An integer representing the number of wins for the losing pitcher | `STATUS_FINAL` |
| `losing_pitcher_losses` | An integer representing the number of losses for the losing pitcher | `STATUS_FINAL` |
| `losing_pitcher_era` | A float representing the ERA for the losing pitcher | `STATUS_FINAL` |
| `saving_pitcher` | Name of the saving pitcher | `STATUS_FINAL` |
| `saving_pitcher_saves` | An integer representing the number of saves for the saving pitcher | `STATUS_FINAL` |
| `game_status` | Status of the current game | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_abbr` | The abbreviation of the home team (ie. `NYM` for the New York Mets). | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_id` | A numeric ID for the home team. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_city` | The home team's city (eg. "New York"). Note this does not include the team name. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_name` | The home team's name (eg. "Mets"). Note this does not include the city name. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_logo` | A URL for a 500px wide PNG logo for the home team. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_runs` | The home team's number of runs scored. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_hits` | The home team's number of hits. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_errors` | The home team's number of errors. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_colors` | An array with two hex colors. The first is the home team's primary color, and the second is their secondary color. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_1` | The home team's line score for the 1st inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_2` | The home team's line score for the 2nd inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_3` | The home team's line score for the 3rd inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_4` | The home team's line score for the 4th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_5` | The home team's line score for the 5th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_6` | The home team's line score for the 6th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_7` | The home team's line score for the 7th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_8` | The home team's line score for the 8th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_ls_9` | The home team's line score for the 9th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `home_team_record` | The home team's current record (eg. "24-14"). | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_abbr` | The abbreviation of the away team (ie. `STL` for the St. Louis Cardinals). | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_id` | A numeric ID for the away team. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_city` | The away team's city (eg. "St. Louis"). Note this does not include the team name. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_name` | The away team's name (eg. "Cardinals"). Note this does not include the city name. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_logo` | A URL for a 500px wide PNG logo for the away team. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_runs` | The away team's number of runs scored. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_hits` | The away team's number of hits. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_errors` | The away team's number of errors. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_colors` | An array with two hex colors. The first is the away team's primary color, and the second is their secondary color. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_1` | The away team's line score for the 1st inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_2` | The away team's line score for the 2nd inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_3` | The away team's line score for the 3rd inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_4` | The away team's line score for the 4th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_5` | The away team's line score for the 5th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_6` | The away team's line score for the 6th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_7` | The away team's line score for the 7th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_8` | The away team's line score for the 8th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_ls_9` | The away team's line score for the 9th inning. An integer. | `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `away_team_record` | The away team's current record (eg. "20-16"). | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `first_pitch_in` | Human-readable string for how far away the game is (eg. "in 30 minutes" or "tomorrow") |  `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `tv_network` | The TV network where you can watch the game (eg. "NBC" or "NFL"). Note that if there is a national feed, it will be listed here, otherwise the local affiliate will be listed. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |
| `last_play` | Sentence describing the most recent play. Note this can be null between innings. | `STATUS_IN_PROGRESS` |
| `balls` | Current number of balls | `STATUS_IN_PROGRESS` |
| `strikes` | Current number of strikes | `STATUS_IN_PROGRESS` |
| `outs` | Current number of outs | `STATUS_IN_PROGRESS` |
| `runner_on_1st` | true/false indicator if a runner is on 1st base | `STATUS_IN_PROGRESS` |
| `runner_on_2nd` | true/false indicator if a runner is on 2nd base | `STATUS_IN_PROGRESS` |
| `runner_on_3rd` | true/false indicator if a runner is on 3rd base | `STATUS_IN_PROGRESS` |
| `current_batter` | Name of the current batter. | `STATUS_IN_PROGRESS` |
| `current_pitcher` | Name of the current pitcher. | `STATUS_IN_PROGRESS` |
| `home_team_starting_pitcher` | The probable starting pitcher for the home team | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` |
| `away_team_starting_pitcher` | The probable starting pitcher for the away team | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` |
| `odds` | The betting odds for the game (eg. "PIT -5.0") | `STATUS_SCHEDULED` |
| `overunder` | The over/under betting line for the total runs scored in the game (eg. "42.5"). | `STATUS_SCHEDULED` |
| `home_team_odds_win_pct` | The pre-game chance the home team has to win, according to ESPN.  A percentage, but presented as a float. | `STATUS_SCHEDULED` |
| `away_team_odds_win_pct` | The pre-game chance the away team has to win, according to ESPN.  A percentage, but presented as a float. | `STATUS_SCHEDULED` |
| `headlines` | A one sentence headline provided by ESPN. | `STATUS_SCHEDULED` `STATUS_FINAL` |
| `win_or_loss` | Shows either `win` or `loss` for your team. | `STATUS_FINAL` |
| `last_update` | A timestamp for the last time data was fetched for the game. If you watch this in real-time, you should notice it updating every 10 minutes, except for during the game (and for the ~20 minutes pre-game) when it updates every 5 seconds. | `STATUS_SCHEDULED` `STATUS_IN_PROGRESS` `STATUS_FINAL` |

## Installation

### Manually

Clone or download this repository and copy the "mlb" directory to your "custom_components" directory in your config directory

```<config directory>/custom_components/mlb/...```
  
### HACS

1. Open the HACS section of Home Assistant.
2. Click the "..." button in the top right corner and select "Custom Repositories."
3. In the window that opens paste this Github URL.
4. In the window that opens when you select it click om "Install This Repository in HACS"
  
## Configuration

You'll need to know your team ID, which is a 2- or 3-letter acronym (eg. "SEA" for Seattle or "MIA" for Miama). You can find yours at https://espn.com/mlb in the top scores UI. 

### Via the "Configuration->Integrations" section of the Home Assistant UI

Look for the integration labeled "MLB" and enter your team's acronym in the UI prompt. You can also enter a friendly name. If you keep the default, your sensor will be `sensor.mlb`, otherwise it will be `sensor.friendly_name_you_picked`. 

### Manually in your `configuration.yaml` file

To create a sensor instance add the following configuration to your sensor definitions using the team_id found above:

```
- platform: mlb
  team_id: 'SEA'
```

After you restart Home Assistant then you should have a new sensor called `sensor.mlb` in your system.

You can overide the sensor default name (`sensor.mlb`) to one of your choosing by setting the `name` option:

```
- platform: mlb
  team_id: 'SEA'
  name: Mariners
```

Using the configuration example above the sensor will then be called "sensor.mariners".
