def is_mountpoint(mp):
    """Checks whether mp is a mountpoint. Can be used to make sure that we are not reading from an unmounted disk where there are no data.

    Args:
        mp (str): A mountpoint, f.ex: /home/pi/docker/nextcloud/persistant-data/nc_data

    Returns:
        bool: whether mp is a mountpoint
    """
    is_mountpoint = False
    with open("/etc/mtab", "r") as fp:
        Lines = fp.readlines()
        for line in Lines:
            mountpoint = line.split()[1]
            if mountpoint == mp:
                is_mountpoint = True
    return is_mountpoint
