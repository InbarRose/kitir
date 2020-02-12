#! /usr/bin/env python

# Standard Imports
import shutil

# Lib Imports
from .exec_utils import iexec

# kitir Imports
from kitir import *

# logging
log = logging.getLogger('kitir.utils.package')

# string patterns for apt / packages
locked_apt_get_file_msg = '/var/lib/dpkg/lock'
remove_dpkg_lock = 'sudo rm /var/lib/dpkg/lock; sudo dpkg --configure -a'
fix_dpkg_interruption = 'sudo dpkg --configure -a'
apt_get_fix_broken_packages = 'apt-get -f install'
pip_commands = ['python -m pip', 'pip']
if running_on_linux:
    pip_commands.append('sudo -H pip')


def verify_pip(get_if_needed=True, raise_on_failure=True, **kwargs):
    """
    verify that pip exists on machine
    :param get_if_needed: get pip if missing
    :param raise_on_failure: raise exception if no pip at the end
    :return: returns the pip base if all is okay, or false otherwise (or raises exception)
    """
    log.trace('verifying pip exists: get_if_needed={}'.format(get_if_needed))

    kwargs.setdefault('to_console', False)
    kwargs.setdefault('trace_file', ir_artifact_dir + '/packages/pip/verify_pip.trace.out')

    def _check_for_pip():
        for pip_base in pip_commands:
            ret = iexec('{} --version'.format(pip_base), **kwargs)
            if ret.rc == 0 and ret.contains(('pip', 'python2')):
                log.trace('pip verified: base={} out={}'.format(pip_base, ret.out))
                return pip_base
        return False

    base = _check_for_pip()
    if base is False:
        if get_if_needed and running_on_linux:
            wget_base = 'wget'
            log.warning('pip was missing, trying to install')
            iexec('{} "https://bootstrap.pypa.io/get-pip.py" -O "/tmp/get-pip.py"'.format(wget_base), **kwargs)
            get_pip_cmd = 'python "/tmp/get-pip.py"'
            iexec(get_pip_cmd, **kwargs)
            base = _check_for_pip()

    if base is False:
        if get_if_needed and running_on_linux:
            log.error('pip failed even after trying to install')
        else:
            log.error('pip is missing from machine')
        if raise_on_failure:
            raise Exception('No pip found')
        return False

    return base


def pip_cmd(*packages, **kwargs):
    """
    executes pip on current machine. Using the supplied mode and packages
    :param packages: a list of packages,
    :param kwargs: kwargs for iexec and flags
    :return:
    """

    # delete pip cache dir
    shutil.rmtree('/root/.cache/pip', ignore_errors=True)

    # test for pip
    if running_on_windows:
        pip_base = 'python -m pip'
    else:
        pip_base = verify_pip(**kwargs)

    mode = kwargs.pop('mode', 'install')

    # validate
    assert mode in ['install', 'uninstall']  # todo: expand modes

    # kwargs
    kwargs.setdefault('trace_file', ir_artifact_dir + '/packages/pip/pip_iexec_trace.out')
    kwargs.setdefault('to_console', True)

    # flags  # todo: expand flags
    flags = []
    if mode == 'install' and kwargs.pop('upgrade', True):
        flags.append('--upgrade')
    if mode == 'install' and kwargs.pop('egg', True):
        flags.append('--egg')
    if mode == 'install' and kwargs.pop('force_reinstall', True):
        flags.append('--force-reinstall')
    if mode == 'uninstall' and kwargs.pop('yes', True):
        flags.append('--yes')
    if mode == 'install' and kwargs.pop('isolated', False):
        flags.append('--isolated')
    if mode == 'install' and kwargs.pop('disable_cache', False):
        flags.append('--no-cache-dir')

    # cmd
    cmd = '{} {} {} {}'.format(pip_base, mode, ' '.join(flags), ' '.join(packages))

    return iexec(cmd, **kwargs)


__all__ = [
    'pip_cmd',
]
