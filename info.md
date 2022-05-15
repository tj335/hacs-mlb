# MLB Scores

## Description

This integration retrieves scores for your favorite MLB team.

## Installation:

### Manual
Clone or download this repository and copy the "mlb" directory to your "custom_components" directory in your config directory

<config directory>/custom_components/mlb/...

### HACS
Open the HACS section of Home Assistant.
Click the "..." button in the top right corner and select "Custom Repositories."
In the window that opens paste this Github URL.
In the window that opens when you select it click om "Install This Repository in HACS"

## Configuration:

Find your team ID, which is a 2- or 3-letter acronym (eg. "NYM" for New York Mets). You can find yours at https://espn.com/mlb in the top scores UI. 

### Via the "Configuration->Integrations" section of the Home Assistant UI

Look for the integration labeled "MLB" and enter your team's acronym in the UI prompt. You can also enter a friendly name. If you keep the default, your sensor will be `sensor.mlb`, otherwise it will be `sensor.friendly_name_you_picked`. 

### Manually in your `configuration.yaml` file

To create a sensor instance add the following configuration to your sensor definitions using the team_id found above:

```
- platform: mlb
  team_id: 'NYM'
```

After you restart Home Assistant then you should have a new sensor called `sensor.mlb` in your system.

You can overide the sensor default name (`sensor.mlb`) to one of your choosing by setting the `name` option:

```
- platform: mlb
  team_id: 'NYM'
  name: New York Mets
```

Using the configuration example above the sensor will then be called "sensor.new_york_mets".
