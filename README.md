# DCBorgBackup

Take your docker-compose stack down, send a backup of the folder to a borg-server, start your stack again and notify user via Telegram (optional).

## Description
To create a full backup of your stack the following folder-structure is recommended:

```
project-folder
│   docker-compose.yaml
│   README    
│
└───persistant-data
│   │   
│   │
│   |----container_1
│   |    │   
│   |    │   data.db
│   |    │   ...
│   |
    |----container_2
    |    |
    |    |  file.txt
         |  ...

```
Everything you want to back up should be in a subfolder of the folder that contains your `docker-compose.yaml`.

At runtime the script will check that the remote server is reachable, that there is a repo and check whether it is encrypted or not.

## Getting Started
1. Clone this repo
2. Create a secret.yaml file containing the keys you need (see secret.yaml).
3. Create a config.yaml (see config.yaml)
4. Optional: Create a bash script to call this script with config.yaml and secret.yaml 

## secrets.yaml
This file contains all the sensitive information the script needs to run. 

Example with explanations:

```
#Mandatory:
borguser: 12345                                 #User to connect to remote

#Optional:
repo_passwords:                                 #List of passwords per borg-repo
  nextcloud: my_pass                            #Password for repo 'nextcloud'
telegram:                                       #Telegram-specific keys
  bot_token: mybotok3nefwefwefFFRwsefDNAUuo     #Telegram bot token
  chatids:                                      #List of chats to notify
    - 9876543                                   
```
## config.yaml
This file contains all the configurations you want to pass to the script.


| Key  | Mandatory   | Note  |
|---|---|---|
|  rootfolder | Yes  | Folder containing your project folder  |
|  foldername | Yes  | The name of your project folder  |
| borgserver  |  Yes | The hostname or IP of the remote borg server  |
| expected_user  | Yes  | The user this script expects to be run as, i.e. the user that may read all files you want to back up.. If your containers run as `root` this should likely be `root`  |
|  repo_encrypted | Yes  | Is this repo encrypted (using repokey)? If `True` you need to put a password into `secrets.yaml`  |
| borgrepo  | No  | If omitted `foldername` will be used  |
| borgarchive  | No  | If omitted `foldername` will be used  |
|  prepost |  No | A pre or post script to execute  |
| debug  | No  |  If `True` the script will only print what it will do |
| docker_compose  | No  | If `True` the script will take the stack down and restart it after the backup  |
| borg_parameters  | No  |  Dict of parameters to add to borg. |


`borg_parameters` may contain the keys `info`, `create` or `prune` and the corresponding values will be added to the borg commands at runtime.

#### Example:
```
borg_parameters:
  info: "--remote-path=borg1"
```
Will add `--remote-path=borg1` to each call of `borg info...`

If `borgrepo` and `borgarchive` are not set the script will use `foldername` instead both times.

#### Example:
If both `borgrepo` and `borgarchive` are defined `borg create ... ` will be called like this:

```
borg create <borg_parameters['create']> <borguser>@<borgserver>:<borgrepo>::<borgarchive>-%Y-%m-%d-%H%M%S <rootfolder><foldername>
```
If omitted the script will use `foldername`:
```
borg create <borg_parameters['create']> <borguser>@<borgserver>:<foldername>::<foldername>-%Y-%m-%d-%H%M%S <rootfolder><foldername>
```
## Calling the script

```
dcborgbackup.py config_yaml secrets.yaml
```
## Prepost

Sometimes it is necessary to run a script before or after running the backup. If you wish to do that put a script into the folder `prepost` containing a `pre()` or `post()` function and use the option `prepost` in `config.yaml` to let the dcborgbackup know where your script is.

#### Example
Your functions are in `prepost/myprepost.py`:

config.yaml:
```
...
prepost: myprepost
...
```

### Dependencies

* Your user can ssh to the remote server
* python >= 3.6



## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

## License

This project is licensed under the linked license - see the LICENSE.md file for details

## Acknowledgments

* [BorgBackup](https://www.borgbackup.org/)