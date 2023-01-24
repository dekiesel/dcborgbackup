import logging
from subprocess import PIPE, STDOUT, Popen
import shlex

logger = logging.getLogger(__name__)


def cmd_run(cmd: str, env: dict = None, **kwargs: dict):
    """Runs a command using subprocess.Popen while writing stdout and stderr to the logger. Returns the result

    Args:
        cmd (str): Command to run
        env (dict, optional): environment variables to add to Popen. Defaults to None.

    Returns:
        _type_: _description_
    """
    my_stdout = ""
    if kwargs["debug"] is True:
        logger.info(f"env= {env}")
        cmd = "echo " + cmd
    logger.info(
        "----------------------------------------------------------------------------"
    )
    logger.info(f"Executing this command: {cmd}\n")
    with Popen(
        shlex.split(cmd),
        stdout=PIPE,
        stderr=STDOUT,
        bufsize=1,
        universal_newlines=True,
        env=env,
        text=True,
    ) as p:
        for line in p.stdout:
            my_stdout = my_stdout + line
            logger.info("subprocess: %s", line.rstrip("\r\n"))
    logger.info(
        "----------------------------------------------------------------------------"
    )
    p.stdout = my_stdout
    return p


if __name__ == "__main__":
    pass
