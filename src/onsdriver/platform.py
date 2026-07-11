'Detect OS, architecture, etc.'

import platform
import os
import sys

OS_LINUX = 'linux'
OS_MACOS = 'darwin'
OS_WINDOWS = 'win32'
MACOS_ARCH_ARM64 = 'arm64'
MACOS_ARCH_X86_64 = 'x86_64'
WIN_ARCH_ARM64 = 'ARM64'
WIN_ARCH_X64 = 'AMD64'

def _from_env(env_name, accepted_values):
    if env_name not in os.environ:
        return None
    v = os.environ[env_name]
    if v not in accepted_values:
        raise ValueError(f'Invalid {env_name} value: {v}')
    return v

def os_name():
    '''Detect OS

    :return:  OS type
    '''
    env_os = _from_env('ONSDRIVER_OS', (OS_LINUX, OS_MACOS, OS_WINDOWS))
    if env_os:
        return env_os
    return sys.platform

def os_is_linux():
    '''Check current OS is Linux'''
    return os_name() == OS_LINUX

def os_is_macos():
    '''Check current OS is macOS'''
    return os_name() == OS_MACOS

def os_is_windows():
    '''Check current OS is Windows'''
    return os_name() == OS_WINDOWS

def arch():
    '''Detect machine architecture

    :return:  Architecture type
    '''
    if os_is_macos():
        env_arch = _from_env('ONSDRIVER_ARCH', (MACOS_ARCH_ARM64, MACOS_ARCH_X86_64))
    elif os_is_windows():
        env_arch = _from_env('ONSDRIVER_ARCH', (WIN_ARCH_X64, WIN_ARCH_ARM64))
    else:
        env_arch = None
    if env_arch:
        return env_arch
    return platform.machine()
