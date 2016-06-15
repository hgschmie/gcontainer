# gcontainer - G Container Management

Container management tool for deploying and running containerized applications.

## Installation

Unless you plan to do development on the gcontainer program itself,
installation through the release RPMs is the preferred way. For each
release tag, an RPM is available from the internal repositories.

## Usage

gcontainer abstracts away the handling of containerized applications
on a host.

gcontainer must be executed with root privileges.

The following container formats are currently supported (the
respective container software must be installed and is required as a
dependency when gcontainer is installed as an RPM):

* docker (https://docker.com) -- default

gcontainer manages software deployment and configuration assignment.

The following commands are available:

```
create           Create a new service.
list             List all installed services.
deploy           Deploy an existing service.
status           Display status of an installed service.
remove           Remove an existing service.
start            Start a deployed service.
stop             Stop a deployed service.
restart          Restart a deployed service if it is running.
disable          Disable a deployed service for autostart.
enable           Enable a deployed service for autostart.
config create    Create a new service config.
config list      List all available service configs.
config activate  Activate an existing service config.
config remove    Remove an existing service config.
```

The following global flags exist:

```
--version      Show the version and exit.
--json         Output is formatted as JSON.
--verbose      Verbose output.
--config PATH  Configuration file to use.
```

Note that verbose output and json do not go well together. Verbose
should only be used for troubleshooting.

### `create` - create a new service

This command takes one mandatory parameter, the name of the new
service.

A service name must be unique on the host.

```bash
% gcontainer create new-service
name:              new-service
config-location:   /data/gcontainer/config/new-service/initial
log-location:      /data/gcontainer/log/new-service
script-location:   /data/gcontainer/script/new-service
running:           False
enabled:           False
container-running: False
deployment:        -
config:            initial
```

JSON output:

```json
{
    "script_location": "/data/gcontainer/script/new-service",
    "log_location": "/data/gcontainer/log/new-service",
    "error_code": 0,
    "running": false,
    "config_location": "/data/gcontainer/config/new-service/initial",
    "name": "new-service",
    "deployment": "-",
    "enabled": false,
    "container_status": {},
    "config": "initial"
}
```

Config, Log and Script location are folders that can be used to place
scripts and files to affect the deployed service.

### `list` - show configured services and their status

This command takes no parameters.

```bash
% gcontainer list
ID          FLAGS DEPLOY CONFIG
new-service SD--  -      initial
```

JSON output:

```json
{
  "deploys": {
    "new-service": {
      "config": "initial",
      "deployment": "-",
      "running": false,
      "container_status": {},
      "enabled": false,
      "name": "new-service"
    }
  },
  "error_code": 0
}
```

The gcontainer output contains the following flags (left to right):

* gcontainer service status: `S` for stopped, `R` for running. The
  status that gcontainer has registered for the service. It is
  controlled by issuing `start` and `stop` commands. The corresponding
  JSON attribute is `running`.
* gcontainer enable status: `D` for disabled, `E` for enabled. The
  enable information that gcontainer has registered for the
  service. It is controlled by issuing `enable` and `disable`
  commands. The corresponding JSON attribute is `enabled`.
* actual service status: `-` for unset, `s` for stopped, `r` for
  running. This status is only available if the service has been
  started at least once. This flag returns the status from the
  underlying container infrastructure. The corresponding JSON
  attribute is `running` nested inside `container_status`.
* callback uri present: `-` for not present, `C` for present. This
  flag is controlled by the `--callback-uri` option of the `deploy`
  command. The corresponding JSON attribute is `callback_uri`.


### `deploy` - Deploy software to an existing service

This command takes two mandatory parameters

* the name of the service. The service must have been created before.
* a container specific identifier for the software to deploy. For
  docker, this is a full docker image specification including a
  version tag. gcontainer does not allow deploy of images without
  version or using the 'latest' tag.

This command has additional options:

* `--callback-uri=<text>` - defines a callback URI for container events

The `deploy` command associates as service with software that should
be executed. The command downloads the necessary image to the host.

```bash
% gcontainer deploy new-service docker.example.com/g/httpd-centos:3.0
```

This command has no output.

### `status` - Display status of a service

This command takes one mandatory parameter, the name of the service to
display. The service must exist.

```bash
% gcontainer status new-service
name:              new-service
config-location:   /data/gcontainer/config/new-service/initial
log-location:      /data/gcontainer/log/new-service
script-location:   /data/gcontainer/script/new-service
running:           False
enabled:           False
container-running: False
deployment:        docker.example.com/g/httpd-centos:3.0
config:            initial
```

```json
{
  "script_location": "/data/gcontainer/script/new-service",
  "log_location": "/data/gcontainer/log/new-service",
  "error_code": 0,
  "running": false,
  "config_location": "/data/gcontainer/config/new-service/initial",
  "name": "new-service",
  "deployment": "docker.example.com/g/httpd-centos:3.0",
  "enabled": false,
  "container_status": {},
  "config": "initial"
}
```

If the service is running, the `container_status` section contains
additional parameters returned from the underlying container
infrastructure:

```json
{
  "script_location": "/data/gcontainer/script/new-service",
  "log_location": "/data/gcontainer/log/new-service",
  "error_code": 0,
  "running": true,
  "config_location": "/data/gcontainer/config/new-service/initial",
  "name": "new-service",
  "deployment": "docker.example.com/g/httpd-centos:3.0",
  "enabled": false,
  "container_status": {
    "id": "9eb90f8f5d35cb770bb3b3f3c67ac30a27e185b1f857768c957504bd715a1f80",
    "running": true,
    "environment": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "container=docker"
    ],
    "image": "docker.example.com/g/httpd-centos:3.0",
    "started": "2015-05-06T23:23:24.778114269Z",
    "created": "2015-05-06T23:23:24.410447546Z"
  },
  "config": "initial"
}
```

### `remove` - Remove a service

This command takes one mandatory parameter, the name of the service to
remove. The service must exist and must not be running.

```bash
% gcontainer remove new-service
```

This command has no output.

### `start` - Start a service

This command takes one mandatory parameter, the name of the service to
start. The service must exist and must not be running.

This command has additional options:

* `--block` If this option is given, the gcontainer command will block
  until the service instance exits.

* `--ignore-started` If this option is given, `gcontainer start` will
  not return an error if the service is already started.

Combining the two options is possible, it will make the `gcontainer
start` command block either on a newly started instance of the service
or until an already running instance exists.

```bash
% gcontainer start new-service
```

This command has no output.

### `stop` - Stop a service

This command takes one mandatory parameter, the name of the service to
stop. The service must exist and must be running.

This command has additional options:

* `--ignore-stopped` If this option is given, `gcontainer stop` will
  not return an error if the service is already stopped.

```bash
% gcontainer stop new-service
```

This command has no output.

### `restart` - Restart a deployed service if it is running

This command takes one mandatory parameter, the name of the service to
restart. The service must exist.

```bash
% gcontainer restart new-service
```

This command has no output.

### `enable` - Enable a service for autostart

This command takes one mandatory parameter, the name of the service to
enable. The service must exist.

Enabling a service will auto-start it when the host is restarted. No
attempt is made to keep the service alive beyond this. Especially, if
a service crashes, it will not be restarted.

Enabling a service is not starting it. A service can be enable while
it is running.


```bash
% gcontainer enable new-service
```

This command has no output.

### `disable` - Disable a service for autostart

This command takes one mandatory parameter, the name of the service to
disable. The service must exist.

After issuing this command, a service will no longer be started when
the host is restarted.

Disabling a service will not stop it. A service can be disabled while
it is running.

```bash
% gcontainer disable new-service
```

This command has no output.

### Configuration management

gcontainer manages different configurations for a service. For each
service, one configuration is active.

When a service is created, a default configuration, `initial` is
created.


#### `config create` - Create a new configuration

This command takes two mandatory parameters, the name of the service
and the name of the configuration. The service must exist prior to
this command. The command name must be unique for this service.

```bash
% gcontainer config create new-service new-config
/data/gcontainer/config/new-service/new-config
```

```json
{
  "error_code": 0,
  "path": "/data/gcontainer/config/new-service/new-config"
}
```

#### `config list` - List all available configurations for a service

This command takes one mandatory parameter, the name of the service to
disable. The service must exist.

```bash
#  gcontainer config list new-service
* initial
  new-config
  ```

The `*` in the first column designates which is the currently active configuration.

```json
{
  "error_code": 0,
  "configs": [
    {
      "mtime": "2015-05-07T11:08:34.607451Z",
      "name": "initial",
      "current": true
    },
    {
      "mtime": "2015-05-07T11:50:39.601219Z",
      "name": "new-config",
      "current": false
    }
  ]
}
```

#### `config activate` - Activate an existing configuration

This command takes two mandatory parameters, the name of the service
and the name of the configuration. The service and configuration must
exist prior to this command.

```bash
% gcontainer config activate new-service new-config
```

This command has no output.


#### `config remove` - Remove an existing configuration

This command takes two mandatory parameters, the name of the service
and the name of the configuration. The service and configuration must
exist prior to this command.

The configuration can not be the currently active configuration.

```bash
% gcontainer config remove new-service new-config
```

This command has no output.

## exit codes

gcontainer can exit with three different exit codes:

* 0 - command executed successfully. With JSON output, the
  `error_code` field will be 0 if the exit code is 0.
* 1 - command failed. With JSON output, the `error_code` field will be
  != 0 and `msg` will describe the error.
* 2 - illegal command given. gcontainer failed to parse the command
  line. In JSON mode, the returned data must be discarded.

## JSON output

When the global `--json` flag is given, any command output is
formatted as JSON as long as the exit code is 0 or 1.

The output is always a JSON object which contains at least one
attribute: `error_code` with a numeric value.

If the error code is != 0 (unsuccessful execution), it will also
contain a second attribute, `msg` which is a human readable message
describing the error. No attempt should be made to parse or interpret
the error message. The format of the message is not part of the
gcontainer API and its form and text may change even between minor
releases.

The list of error codes is available from
[the gcontainer source code](gcontainer/error.py).

## gcontainer configuration

gcontainer will pick up configuration files from

* `~/.gcontainer.conf`
* `/usr/local/etc/gcontainer.conf`
* `/etc/gcontainer.conf`

An alternate config file can be given with the `--config` global
command line option.

It should almost never necessary to change settings in the
configuration file. Especially the settings under `[layout]` should
never need to be changed in normal operation.

The config file is structured as an ini file with sections marked as
`[section]` and `key = value` pairs. If no configuration file is given
or present, the following default values are used:

```ini
[general]
require_root = true    # gcontainer must be run as the root user [1]

[layout]
root = /data/gcontainer  # file system location for the gcontainer files
config_dir = config      # location of the configuration folder [2]
log_dir = log            # location of the logging folder [2]
script_dir = script      # location of the scripts folder [2]
archive_dir = archive    # location of the archive folder [2]

[docker]
socket = unix://var/run/docker.sock  # docker socket location
disable_latest_tag = true            # disable "latest" tag deploys
allow_insecure_registry = false      # require https for registry

[systemd]
config_dir = /etc/systemd/system  # Location for systemd files [3]
systemctl = /usr/bin/systemctl    # systemctl program location [3]
gcontainer = /usr/bin/gcontainer  # install location of gcontainer [4]
timeout = 30s                     # timeout for command execution [4]

[callback]
connect_timeout = 1   # Timeout to connect to callback url in seconds
read_timeout = 5      # TImeout to send data in seconds
ignore_callbacks = false # Turn callbacks off globally
```

* [1] Setting this flag will not make gcontainer work as
  "non-root". This setting is useful for debugging and development,
  however some operations such as `enable` or `disable` will not work
  as non-root. The file system folders for gcontainer must be
  accessible as non-root for basic commands to work. Additional
  restrictions may apply when executing container infrastructure
  commands (e.g. accessing the docker socket).
* [2] If a relative path is given, it is relative to the `root` path,
  absolute paths are used "as-is".
* [3] These paths are specific to the OS. The defaults are for CentOS.
* [4] Used for templating the startup script placed in the systemd folder.


## gcontainer file system layout

gcontainer manages a file system location (default:
`/data/gcontainer`) to store service and configuration
information.

For each services, the following folders are created.

* configuration location (default: `/data/gcontainer/config/<service-name>/<config-name>`)
* log location (default: `/data/gcontainer/log/<service-name>`)

Files placed in these folders are accessible inside a container:

* `/data/config` maps to the active configuration at startup
  time. This folder is mounted read-only and will not change while the
  container is active, even if another `config activate` command is
  executed while the container is active.
* `/data/log` maps to the log location. This folder is mounted
  read-write. A service running in a container should write their log
  files into this location.

## gcontainer startup environment

A file `.startup-env.conf` can be placed in a configuration
folder. This file should contain lines with `key = value` pairs, for
example:

```
PORT=12345
INFO="hello, world"
```

When a service is started, this file is read line-by-line and passed
to the container as environment variables. The status of the
environment can be inspected with the `--json` version of the
`gcontainer status` command.

Keys must be alphanumeric. Any white space around key or value is
stripped. Empty lines or lines starting with `#` are ignored. Key and
value can be surrounded with `'` or `"` characters if they
e.g. contain white space. Any value after the first `=` on a line is
considered the value.

Multi-line values and line-continuation is not supported. This is a
feature: if a service requires this, it should pick up its
configuration through a configuration file.

## Development

gcontainer is installed in a single location (Python virtual
environment) and then linked into the search path. For development
purposes, run

```
% virtualenv ~/.virtualenv/gcontainer
% source ~/.virtualenv/gcontainer/bin/activate
(gcontainer) % pip install --editable .
```

and then link `~/.virtualenv/gcontainer/bin/gcontainer` into the
search path.

As an alternative, you can use the
[pipsi tool](https://github.com/mitsuhiko/pipsi#readme).

### RPM packaging (for gcontainer maintainers)

Unless you are maintaining gcontainer, there should never be a need to
build an RPM yourself. If you experiment with it, use the development
instructions above; if you need to install gcontainer on multiple
machines, use one of the released versions.

gcontainer packs itself as a self-contained RPM and does not require
any additional python packages to be installed on the target host.

An RPM can be packaged with the `build_rpm.sh` script in the `rpm`
folder:

```bash
% ./bin/build_rpm.sh <tag or sha> [<revision>]
```

will build an installable and source RPM in the rpm/dist folder.

The first parameter `tag or sha` can either be a release tag or a sha
value from a commit on the gcontainer main repository at $LINKY

Any changes must have been pushed to this repository. Creating an RPM
from the current working directory is not supported (that is
intentional and a feature).

The second, optional parameter is a revision number in case that
multiple versions of a given tag or sha need to be built. This should
never be necessary unless an RPM that was not intended for consumption
was accidentally leaked out.
