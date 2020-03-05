import sys
import os
import ctypes
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from moltspider.utils import str_md5
from moltspider.settings.active import IMAGES_STORE, FILES_STORE, BASE_DIR

ASADMIN = 'asadmin'


def create_symbol_links_to_replace_site_to_hash(src, tgt):
    """Create symbol links for "site" with hash of "site" in medias folders.
        The purpose is to hide real "site" from go live.
        Basically need to only run once when deploy.
    """
    os.makedirs(tgt, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(src):
        for d in dirnames:
            h = str_md5(d)
            s = os.path.join(src, d)
            t = os.path.join(tgt, h)
            if not os.path.exists(t):
                try:
                    os.symlink(s, t, target_is_directory=True)
                    sys.stdout.write('Created symbol link: %s ==> %s\n' % (s, t))
                except OSError as err:
                    sys.stderr.writelines(['Error: You may need admin (win: run as administrator | *nix: sudo).\n'])
                    raise
        break


def is_win():
    return sys.platform.startswith('win')


def is_admin():
    if is_win():
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False
    else:
        return os.geteuid() == 0


if __name__ == '__main__':
    if is_admin():
        if len(sys.argv) > 1:
            base_path = sys.argv[1]
        else:
            base_path = os.path.join(BASE_DIR, 'temp', 'static')
            sys.stderr.write('Warning: No base path specified.\n')
            sys.stderr.write('         Using default %s.\n' % base_path)

        images_store_symbol_link = os.path.join(base_path, 'album')
        files_store_symbol_link = os.path.join(base_path, 'media')

        create_symbol_links_to_replace_site_to_hash(IMAGES_STORE, images_store_symbol_link)
        create_symbol_links_to_replace_site_to_hash(FILES_STORE, files_store_symbol_link)
    else:
        if is_win():
            params = subprocess.list2cmdline([os.path.abspath(sys.argv[0])] + sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
