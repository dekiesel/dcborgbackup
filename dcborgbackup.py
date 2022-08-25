from modulefinder import Module
from typing import Union
import getpass
import telegram
import logging
import traceback
import os
import argparse
from importlib import import_module
import yaml
from cmdrunner import cmd_run
import borg
import pathlib


telegram_bot = None
configuration = None
secrets = None
logger = logging.getLogger(__name__)

scriptfolder = pathlib.Path(__file__).parent.resolve()
print(scriptfolder)


class UnexpectedUser(Exception):
    pass


class HostNotPingable(Exception):
    pass


class ConfigError(Exception):
    pass


class DockerComposeError(Exception):
    pass


class ComposeFileNotFoundError(FileNotFoundError):
    pass


def docker_compose(up: bool = True) -> None:
    """Calls docker-compose. Takes the stack down if up==False, otherwise it starts the stack.

    Args:
        up (bool, optional): Controls whether 'docker-compose up -d' or 'docker-compose down' is called. Defaults to True.

    Raises:
        DockerComposeError: Raised if there was an error while running docker-compose
    """
    if up:
        cmd = "docker-compose up -d"
    else:
        cmd = "docker-compose down"

    result = cmd_run(cmd, debug=configuration["debug"])
    if result.returncode != 0:
        raise DockerComposeError("Error running docker-compose")


def set_password() -> None:
    """If the repo is encrypted according to the configuration it reads the password from the secrets-dict and saves it in the global configuration-dict.

    Raises:
        KeyError: Raised if the password for the repo isn't found in the secrets-dict.
    """
    global configuration
    password = None
    if configuration["repo_encrypted"] is True:
        try:
            password = secrets["repo_passwords"][configuration["foldername"]]
        except KeyError:
            raise KeyError(
                f"Password for repo not found. The key of the repo-password must be the same as foldername {configuration['foldername']}"
            )
    configuration["password"] = password


def notify(msg: str) -> None:
    """Wrapper function to call all notifcation providers.

    Args:
        msg (str): The message to send.
    """
    if "telegram" in secrets:
        send_telegram(msg)


def send_telegram(msg: str) -> None:
    """Sends a telegram message

    Args:
        msg (str): The message to send.
    """
    for chatid in secrets["telegram"]["chatids"]:
        telegram_bot.sendMessage(chat_id=chatid, text=msg)


def host_pingable(host: str) -> bool:
    """Tests whether a host is pingable.

    Args:
        host (str): the host to test

    Returns:
        bool: True if host is pingable, False otherwise.
    """
    logger.info(f"pinging {host}")
    cmd = f"ping -c 1 {host}"
    result = cmd_run(cmd, debug=configuration["debug"])
    if result.returncode == 0:
        return True
    else:
        return False


def load_prepost_module() -> Union[None, Module]:
    """Loads prepost-modules if exist. If a prepost-module is supplied in the configuration the imported module is returned.

    Returns:
        Union[str, bool]: None if no prepost-module defined, the module otherwise.
    """
    if not configuration["prepost"]:
        return
    else:
        file = os.path.join("prepost", f"{configuration['prepost']}.py")
        logger.info(f"importing module '{configuration['prepost']}' from {file}")
        imported = import_module(f"prepost.{configuration['prepost']}")
        return imported


def execute_pre_script(imported: Module) -> None:
    """Executes the pre()-function of a prepost-module.

    Args:
        imported (Module): The module containing the pre()-function.
    """
    try:
        pre = getattr(imported, "pre")
    except AttributeError:
        logger.info(f"No pre()-function found in {imported.__name__}")
    else:
        logger.info("Executing pre-script")
        pre(**configuration)


def execute_post_script(imported: Module) -> None:
    """Executes the post()-function of a prepost-module.

    Args:
        imported (Module): The module containing the pre()-function.
    """
    try:
        post = getattr(imported, "post")
    except AttributeError:
        logger.info(f"No post()-function found in {imported.__name__}")
    else:
        logger.info("Executing post-script")
        post(**configuration)


def running_as_expected_user(expected_user: str) -> bool:
    """Tests whether this script is run as the expected user.

    Args:
        expected_user (str): The user this script should be run as, example: root

    Returns:
        bool: True if the current user equals 'expected_user', False otherwise.
    """
    # expected user check
    if configuration["debug"]:
        return True
    user = getpass.getuser()
    if user != expected_user:
        return False
    else:
        return True


def pre_start_checks() -> None:
    """Runs all the checks necessary that have to pass before creating an archive.

    Raises:
        UnexpectedUser: Raised if this script is run as another user than expected.
        HostNotPingable: Raised if borg-host isn't pingable.
        borg.BorgNotInstalled: Raised if borg isn't installed locally.
    """
    if not running_as_expected_user(configuration["expected_user"]):
        raise UnexpectedUser(
            f"This script expects to be run as {configuration['expected_user']} to back up {configuration['foldername']}."
        )

    if not host_pingable(configuration["borgserver"]):
        raise HostNotPingable(f"Host {configuration['borgserver']} not pingable!")

    if not borg.borg_installed_locally():
        raise borg.BorgNotInstalled("borg not installed locally")
    borg.repo_checks(**configuration)


def docker_compose_setup() -> None:
    """Checks whether the compose file exists and chdir's to the folder containing that file.

    Raises:
        ComposeFileNotFoundError: _description_
    """
    if not os.path.isfile(configuration["compose_file"]):
        raise ComposeFileNotFoundError(
            f"compose file {configuration['compose_file']} does not exist!"
        )
    os.chdir(f"{configuration['compose_folder']}")
    logger.debug(f"Changed dir to {configuration['compose_folder']}")


def _start() -> None:
    """Orchestrates the necessary steps to create an archive."""
    pre_start_checks()
    if configuration["prepost"]:
        imported = load_prepost_module()
        execute_pre_script(imported)
    if configuration["docker_compose"]:
        docker_compose_setup()
        docker_compose(up=False)
    borg.create(**configuration)
    if configuration["docker_compose"]:
        docker_compose()
    borg.prune(**configuration)
    if configuration["prepost"]:
        execute_post_script(imported)
    notify(f"borg-backup of {configuration['foldername']} finished successfully.")


def read_secrets(secretsfile: str) -> None:
    """Reads secrets.yaml

    Args:
        secretsfile (str): secrets.yaml

    Raises:
        KeyError: Raised if a mandatory key doesn't exist.
    """
    with open(secretsfile, "r") as f:
        s = yaml.safe_load(f)
    mandatory = ["borguser"]
    for key in mandatory:
        if key not in s:
            raise KeyError(
                f"Mandatory key {key} not found in secrets file {secretsfile}"
            )
    global secrets
    secrets = s


def read_config(configfile: str) -> None:
    """Parses the config file

    Args:
        configfile (str): The config file

    Raises:
        KeyError: Raised if a mandatory config item doesn't exist or telegram is requested but not all parameters exist in the config.
        ConfigError: Raised if the rootfolder doesn't end in /
        ValueError: Raised if telegram parameters are of the wrong type.
    """
    with open(configfile, "r") as f:
        config = yaml.safe_load(f)
    mandatory = [
        "foldername",
        "borgserver",
        "rootfolder",
        "expected_user",
        "repo_encrypted",
    ]
    for key in mandatory:
        if key not in config:
            raise KeyError(f"Mandatory key {key} not found in config file {configfile}")
    if not config["rootfolder"].endswith("/"):
        raise ConfigError("rootfolder needs to end with '/'")
    # Optional keys:
    if "borgrepo" not in config:
        config["borgrepo"] = config["foldername"]
    if "borgarchive" not in config:
        config["borgarchive"] = config["foldername"]
    if "debug" not in config:
        config["debug"] = False
    if "telegram" not in config:
        config["telegram"] = False
    if "docker_compose" not in config:
        config["docker_compose"] = True
    if "prepost" not in config:
        config["prepost"] = False

    if "borg_parameters" not in config:
        params = {
            "prune:": "-v --list --keep-within=1d --keep-daily=7 --keep-weekly=4 --keep-monthly=12",
            "create": "",
            "info": "",
        }
        config["borg_parameters"]: params
    else:
        if "create" not in config["borg_parameters"]:
            config["borg_parameters"]["create"] = ""
        if "info" not in config["borg_parameters"]:
            config["borg_parameters"]["info"] = ""
        if "prune" not in config["borg_parameters"]:
            config["borg_parameters"]["prune"] = ""

    if config["docker_compose"]:
        config["compose_folder"] = f"{config['rootfolder']}{config['foldername']}"
        config["compose_file"] = f"{config['compose_folder']}/docker-compose.yaml"

    if "telegram" in secrets:
        if (
            "bot_token" not in secrets["telegram"]
            or "chatids" not in secrets["telegram"]
        ):
            raise KeyError(
                "config_parser: bot_token and chatids are mandatory keys in secrets.yaml when using telegram"
            )
        elif not isinstance(secrets["telegram"]["bot_token"], str) or not isinstance(
            secrets["telegram"]["chatids"], list
        ):
            raise ValueError(
                "config parser: bot_token needs to be a string and chatids needs to be a list"
            )
        global telegram_bot
        telegram_bot = telegram.Bot(token=secrets["telegram"]["bot_token"])

    config["borguser"] = secrets["borguser"]
    global configuration
    configuration = config


def logger_setup() -> None:
    """Logging setup."""
    format = "%(asctime)s-%(levelname)s: %(message)s"
    datefmt = "%d-%b-%y_%H:%M:%S"
    if configuration["debug"]:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format=format, datefmt=datefmt, level=level)


def start(configfile: str, secretsfile: str) -> None:
    """Runs initial checks and starts parsing the config and secrets files.

    Args:
        configfile (str): The file containing the configuration
        secretsfile (str): The file containing the secrets

    Raises:
        FileNotFoundError: Raised if configfile not found.
        FileNotFoundError: Raised if secrets file not found
        FileNotFoundError: Raised if prepost requested but no prepost file found.
        e: Catch-all to notify user via requested methods.
    """
    try:
        if not os.path.isfile(configfile):
            raise FileNotFoundError(f"Configuration yaml {configfile} not found.")
        if not os.path.isfile(secretsfile):
            raise FileNotFoundError(f"Secrets yaml {secretsfile} not found.")
        read_secrets(secretsfile)
        read_config(configfile)
        if configuration["prepost"]:
            if configuration["prepost"].endswith(".py"):
                configuration["prepost"] = configuration["prepost"][0:-3]
            file = os.path.join(
                scriptfolder, "prepost", f"{configuration['prepost']}.py"
            )
            if not os.path.isfile(file):
                raise FileNotFoundError(f"Prepostfile {file} not found.")
        set_password()
        logger_setup()
        _start()
    except Exception as e:
        tb = traceback.format_exc()
        message = (
            f"ERROR: borg-backup for {configuration['foldername']} failed with reason:"
        )
        notify(message)
        notify(tb)
        if configuration["docker_compose"]:
            docker_compose()
        logger.error(message)
        logger.error(tb)
        raise e


def main():
    parser = argparse.ArgumentParser(
        description="Backup data (from docker-volumes) with borg"
    )
    parser.add_argument("config", help="The config.yaml file")
    parser.add_argument("secrets", help="The secrets.yaml file")
    args = parser.parse_args()
    start(args.config, args.secrets)


if __name__ == "__main__":
    main()
