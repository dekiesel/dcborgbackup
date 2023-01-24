import os
from cmdrunner import cmd_run
import logging
from shutil import which
import re

logger = logging.getLogger(__name__)


class BorgErrorGettingLock(Exception):
    pass

class BorgNotInstalled(Exception):
    pass


class WrongRepokey(Exception):
    pass


class RepoDoesNotExist(Exception):
    pass


class BorgError(Exception):
    pass


class NotRepokeyEncrypted(Exception):
    pass


def borg_installed_locally() -> bool:
    """Returns True if borg is installed locally, False otherwise

    Returns:
        bool: result of check
    """
    path = which("borg")
    logger.debug(f"borg at {path}")
    if path:
        return True
    else:
        return False


def _get_parameters(option: str, **kwargs) -> str:
    """Searches the borg_parameters part of the configuration for 'option'.

    Args:
        option (str): Has to be one of 'prune', 'create' or 'info.

    Raises:
        ValueError: raises this when 'option' isn't one of the allowed.

    Returns:
        str: A string containing parameters for "borg 'option' params ..."
    """
    params = ""
    if option not in ["create", "info", "prune"]:
        raise ValueError(f"Option {option} is unknown.")
    params = kwargs["borg_parameters"][option]
    return params


def create(**kwargs) -> None:
    """Creates a borg archive.

    Raises:
        BorgError: Raises this exception when the command didn't run successfully.
    """
    my_env = {**os.environ, "BORG_PASSPHRASE": f"{kwargs['password']}"}
    if "borg_relocated_repo_access_is_ok" in kwargs:
        my_env["BORG_RELOCATED_REPO_ACCESS_IS_OK"] = kwargs["borg_relocated_repo_access_is_ok"]
    params = _get_parameters("create", **kwargs)
    cmd = f"borg create {params} {kwargs['borguser']}@{kwargs['borgserver']}:{kwargs['borgrepo']}::{kwargs['borgarchive']}-{{now:%Y-%m-%d-%H%M%S}} {kwargs['rootfolder']}{kwargs['foldername']}"  # double {{ to escape for f-string

    result = cmd_run(cmd, env=my_env, **kwargs)
    if result.returncode != 0:
        raise BorgError(f"Error running borg: {result.stdout}")


def prune(**kwargs) -> None:
    """Prunes borg archives.

    Raises:
        BorgError: Raises this exception whent he command didn't run successfully
    """
    my_env = {**os.environ, "BORG_PASSPHRASE": f"{kwargs['password']}"}
    if "borg_relocated_repo_access_is_ok" in kwargs:
        my_env["BORG_RELOCATED_REPO_ACCESS_IS_OK"] = kwargs["borg_relocated_repo_access_is_ok"]
    params = _get_parameters("prune", **kwargs)
    cmd = f"borg prune {params} {kwargs['borguser']}@{kwargs['borgserver']}:{kwargs['borgrepo']}"

    result = cmd_run(cmd, env=my_env, **kwargs)
    if result.returncode != 0:
        raise BorgError("Error running borg prune")


def info(**kwargs) -> str:
    """Gets info on a borg repo and returns the stdout of 'borg info'.

    Raises:
        BorgError: Raised if there was an error running 'borg info ... ' that isn't a 'Repo does not exist'-error.

    Returns:
        str: stdout of 'borg 'init'
    """
    my_env = {**os.environ, "BORG_PASSPHRASE": f"{kwargs['password']}"}
    if "borg_relocated_repo_access_is_ok" in kwargs:
        my_env["BORG_RELOCATED_REPO_ACCESS_IS_OK"] = kwargs["borg_relocated_repo_access_is_ok"]
    params = _get_parameters("info", **kwargs)
    cmd = f"borg info {params} {kwargs['borguser']}@{kwargs['borgserver']}:{kwargs['borgrepo']}"

    result = cmd_run(cmd, env=my_env, **kwargs)
    contains = re.search("Failed to create/acquire the lock", result.stdout)
    if contains:
        raise BorgErrorGettingLock("Couldn't create/aquire the lock. Check if you can delete the lock.")
    if result.returncode != 0:
        _check_repo_exists(result.stdout)
        raise BorgError("Error running borg info")
    return result.stdout


def repo_checks(**kwargs) -> None:
    """Convenience function that calls all the necessary checks before creating an archive.

    Raises:
        NotRepokeyEncrypted: Raised if configuration says repo is encrypted but 'borg info' says it isn't.
    """
    if kwargs["debug"] is True:
        return
    check_ssh_login(**kwargs)
    stdout = info(**kwargs)
    _check_repo_exists(stdout)

    if kwargs["repo_encrypted"]:
        if _repo_encrypted_with_repokey(stdout):
            _check_password_correct(stdout)
        else:
            raise NotRepokeyEncrypted(
                "Config says repo is encrypted (repo_encrypted), but borg says repo isn't repokey encrypted."
            )


def _check_repo_exists(stdout: str) -> None:
    """Checks the output of info() to see whether the requested repo exists.

    Args:
        stdout (str): The output of info()

    Raises:
        RepoDoesNotExist: Raised if the repo doesn't exist.
    """
    contains = re.search("Repository .* does not exist", stdout)
    if contains:
        raise RepoDoesNotExist("Repo doesn't exist, do you need to 'init' it?")


def _repo_encrypted_with_repokey(stdout: str) -> bool:
    """Checks the output of borg() to see whether the repo is encrypted using repokey(standard or blake2)

    Args:
        stdout (str): The output of info()

    Returns:
        bool: True if the repo is encrypted using repokey, False otherwise.
    """
    contains = re.search("Encrypted: Yes [(]repokey", stdout)
    if contains:
        return True
    else:
        return False


def _check_password_correct(stdout: str) -> None:
    """Checks the output of borg() to see whether the password is correct.

    Args:
        stdout (str): The output of borg()

    Raises:
        WrongRepokey: Raised if the repo can't be decrypted with the supplied BORG_PASSPHRASE
    """
    contains = re.search("passphrase supplied in .* is incorrect.", stdout)
    if contains:
        raise WrongRepokey("The supplied password is wrong.")


def check_ssh_login(**kwargs) -> None:
    """Tries to login to the remote machine using ssh.

    Raises:
        ConnectionError: Raised if the ssh-connection fails.
    """
    cmd = f"ssh -o BatchMode=yes -o ConnectTimeout=5 {kwargs['borguser']}@{kwargs['borgserver']} echo"
    result = cmd_run(cmd, debug=kwargs["debug"])
    logger.info(result.returncode)
    if result.returncode != 0:
        raise ConnectionError("Error ssh'ing to server: {result.stdout}")


if __name__ == "__main__":
    pass
