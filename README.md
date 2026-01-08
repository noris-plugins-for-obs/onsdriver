# ONS Driver

This is a python library to start OBS Studio and control it.

## Using the toolchain

### Basic workflow

#### Preparing OBS Studio

We provide a script to download the latest OBS Studio.

```sh
onsdriver-obsinstall
```

This script will
- download the latest OBS Studio from GitHub,
- and extract it on a directory `./obs-studio`.

#### Run the first-time wizard

At first, we recommend to backup your configuration file.

Then, run the script to invoke the first-time wizard and configure for the following steps.
```sh
onsdriver-firsttime --save ./saved-config
```

This script will
- remove the existing configuration of OBS Studio,
- install necessary plugins to control OBS Studio,
- run OBS Studio (under `./obs-studio`) and proceed the first-time wizard,
- enable obs-websocket,
- and copy the configuration into `./saved-config`.

#### Run your tests


### Environment variables

| Name | Purpose |
| ---- | ------- |
| `HOME` | Home directory to set the configuration directory for Linux and macOS. |
| `AppData` | AppData directory to set the configuration directory for Windows. |
| `ProgramData` | ProgramData directory to extract plugins for Windows. |
| `XDG_CONFIG_HOME` | Optionally overwrites the configuration directory derived from `HOME` directory for Linux. |
| `OBS_EXEC` | Optionally configures path to the OBS Studio executable file. |
| `GITHUB_TOKEN` | Optionally uses this token to download plugin from GitHub. |
| `ONSDRIVER_LOGS` | Optionally sets location to move log files to. |
