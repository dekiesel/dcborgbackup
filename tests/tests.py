# pi@raspberrypi:~/backup_scripts/newscripts $ python -m unittest discover
import borg
import unittest
import cmdrunner


class TestBorg(unittest.TestCase):
    config = {
        "debug": True,
        "password": None,
        "borguser": 123,
        "borgserver": "test.com",
        "borgrepo": "testrepo",
        "borgfolder": "testfolder",
        "rootfolder": "root/folder",
        "foldername": "testfolder",
        "borg_parameters": {"create": "", "prune": "", "info": ""},
    }

    def test_get_parameters(self):
        config = {"borg_parameters": {"prune": "test"}}
        params = borg._get_parameters("prune", **config)
        self.assertTrue(params == "test")

    def test_get_parameters_exception(self):
        config = {"borg_parameters": {"prune": "test"}}
        self.assertRaises(ValueError, borg._get_parameters, "prunes", **config)

    def test_borg_create(self):
        borg.create(**TestBorg.config)

    def test_borg_prune(self):
        borg.prune(**TestBorg.config)

    def test_borg_info(self):
        borg.info(**TestBorg.config)

    fakerepo = "1234abcde"
    info_repokey = """
    Remote: Borg 0.29.0: exception in RPC call:
Remote: Traceback (most recent call last):
Remote:   File "/usr/home/kibab/borgbackup-0.29.0/borg/remote.py", line 96, in serve
Remote: TypeError: open() takes from 2 to 5 positional arguments but 7 were given
Remote: Platform: FreeBSD ch-s011.rsync.net 12.2-RELEASE FreeBSD 12.2-RELEASE rsync_12_2 amd64
Remote: Python: CPython 3.4.3
Remote: 
Please note:
If you see a TypeError complaining about the number of positional arguments
given to open(), you can ignore it if it comes from a borg version < 1.0.7.
This TypeError is a cosmetic side effect of the compatibility code borg
clients >= 1.0.7 have to support older borg servers.
This problem will go away as soon as the server has been upgraded to 1.0.7+.
Repository ID: {fakerepo}
Location: ssh://123456@ch-s011.rsync.net/./borg_repo
Encrypted: Yes (repokey)
Cache: /home/pi/.cache/borg/{fakerepo}
Security dir: /home/pi/.config/borg/security/{fakerepo}
------------------------------------------------------------------------------
                       Original size      Compressed size    Deduplicated size
All archives:                0 TB              0 TB            0 GB

                       Unique chunks         Total chunks
Chunk index:                  1              1
    """

    info_repokey_blake2b = f"""
Repository ID: {fakerepo}
Location: ssh://1234@ch-s011.rsync.net/./blaketest
Encrypted: Yes (repokey BLAKE2b)
Cache: /home/pi/.cache/borg/{fakerepo}
Security dir: /home/pi/.config/borg/security/{fakerepo}
------------------------------------------------------------------------------
                       Original size      Compressed size    Deduplicated size
All archives:                    0 B                  0 B                  0 B

                       Unique chunks         Total chunks
Chunk index:                       0                    0
"""
    info_unencrypted = """
Repository ID: {fakerepo}
Location: ssh://17963@ch-s011.rsync.net/./unencryptedtest
Encrypted: No
Cache: /home/pi/.cache/borg/{fakerepo}
Security dir: /home/pi/.config/borg/security/{fakerepo}
------------------------------------------------------------------------------
                       Original size      Compressed size    Deduplicated size
All archives:                    0 B                  0 B                  0 B

                       Unique chunks         Total chunks
Chunk index:                       0                    0
"""
    info_not_exists = """
Repository 12345@ch-s011.rsync.net:unencryptedtest2 does not exist."""

    info_wrong_pw = "passphrase supplied in BORG_PASSPHRASE, by BORG_PASSCOMMAND or via BORG_PASSPHRASE_FD is incorrect."

    def test_repo_exists(self):
        # check that no exception is thrown when the repo exists
        borg._check_repo_exists(TestBorg.info_repokey)
        self.assertRaises(
            borg.RepoDoesNotExist, borg._check_repo_exists, TestBorg.info_not_exists
        )

    def test_repo_encrypted_with_repokey(self):
        ret = borg._repo_encrypted_with_repokey(TestBorg.info_repokey)
        self.assertTrue(ret)
        ret = borg._repo_encrypted_with_repokey(TestBorg.info_repokey_blake2b)
        self.assertTrue(ret)
        ret = borg._repo_encrypted_with_repokey(TestBorg.info_unencrypted)
        self.assertFalse(ret)

    def test_check_password_correct(self):
        borg._check_password_correct(TestBorg.info_repokey)
        self.assertRaises(
            borg.WrongRepokey, borg._check_password_correct, TestBorg.info_wrong_pw
        )


class TestCMDRunner(unittest.TestCase):
    def test_cmd_run(self):
        cmd_successful = "echo"
        cmd_unsuccessful = "ls idontexist"
        cmd_doesntexist = "idontexist"
        config = {"debug": False}
        p = cmdrunner.cmd_run(cmd_successful, **config)
        self.assertTrue(p.returncode == 0)
        p = cmdrunner.cmd_run(cmd_unsuccessful, **config)
        self.assertTrue(p.returncode != 0)
        self.assertRaises(
            FileNotFoundError, cmdrunner.cmd_run, cmd_doesntexist, **config
        )


# class TestMain(unittest.TestCase):
#    def test_wrong_folder_name_throws_exception(self):
#        self.assertRaises(bu.ComposeFileNotFoundError, bu.start, "nextcloudx", "mypass")
#
#    def test_host_not_pingeable(self):
#        quatschost_de = bu.host_pingable("quatschost.de")
#        self.assertFalse(quatschost_de)
#        google_de = bu.host_pingable("www.google.de")
#        self.assertTrue(google_de)
#
#    def test_is_mountpoint(self):
#        mp1 = "/"
#        is_mp1 = hlp.is_mountpoint(mp1)
#        mp2 = "/root2"
#        is_mp2 = hlp.is_mountpoint(mp2)
#        self.assertTrue(is_mp1)
#        self.assertFalse(is_mp2)


if __name__ == "__main__":
    unittest.main()
