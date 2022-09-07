# DCBorgBackup

Take your docker-compose stack down, send a backup of the folder to a borg-server, start your stack again and notify user via Telegram (optional).

## Description
To create a full backup of your stack the following folder-structure is recommended:

```
project
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
|  adscwc | vwwev  | wev  |
|   |   |   |
|   |   |   |
|   |   |   |
|   |   |   |
|   |   |   |
|   |   |   |
|   |   |   |



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

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)
