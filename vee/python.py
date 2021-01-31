import os
import re
import subprocess
import sys

from vee.utils import cached_property


class Python(object):

    def __init__(self, executable, version):
        self.executable = executable
        self.version = version

    def __repr__(self):
        return 'Python({!r}, {!r})'.format(self.executable, self.version)

    @cached_property
    def major(self):
        return self.version[0]

    @cached_property
    def minor(self):
        return self.version[1]

    @cached_property
    def rel_site_packages(self):
        return os.path.join('lib', 'python{}.{}'.format(self.major, self.minor), 'site-packages')


def get_python(selector=None):

    selector = selector or os.environ.get('VEE_PYTHON')
    if not selector:
        return Python(sys.executable, sys.version_info)

    version = executable = None

    if isinstance(selector, str):

        m = re.match(r'(?:python)?(\d)(?:\.(\d+)(?:\.(\d+))?)?', selector)
        if m:
            major, minor, patch = m.groups()
            if minor:
                version = (int(major), int(minor))
                executable = 'python{}.{}'.format(*version)
            else:
                executable = 'python{}'.format(major)

    elif isinstance(selector, int):
        executable = 'python{}'.format(selector)

    elif isinstance(selector, (list, tuple)):
        version = tuple(selector)
        if len(version) < 2:
            raise ValueError("version sequence must have 2 elements")
        if not (isinstance(version[0], int) and isinstance(version[1], int)):
            raise ValueError("version sequence must contain ints")

    if not version:
        
        if not executable:
            executable = selector
        
        proc = subprocess.Popen([executable, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        out = (out + err).decode().strip()

        m = re.match(r'Python (\d)\.(\d+)\.(\d+)', out)
        if not m:
            raise ValueError("could not parse output of `{} --version`".format(executable))
        version = tuple(map(int, m.groups()))

    if version and not executable:
        executable = 'python{}.{}'.format(*version)

    return Python(executable, version)


_default_python = None

def get_default_python():
    global _default_python
    if _default_python is None:
        _default_python = get_python()
    return _default_python


def get_base_site_packages():
    return os.path.join(
        sys.base_prefix,
        'lib',
        'python{}.{}'.format(*sys.version_info[:2]),
        'site-packages',
    )


def get_base_python():
    
    # Look for pyenv path.
    m = re.match(r'versions/(\d\.\d+\.\d+)/?$', sys.base_prefix)
    if m:
        version = map(int, m.group(1).split('.'))
        return Python(os.path.join(sys.base_prefix, 'bin', 'python'), version)
    
    # Fall back onto the default.
    return get_default_python()


if __name__ == '__main__':
    print(get_default_python())
    print(get_base_python())

