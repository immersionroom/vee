import os
import re

from vee import log
from vee.cli import style, style_note
from vee.pipeline.base import PipelineStep
from vee.subproc import call
from vee.utils import cached_property
from vee.exceptions import AlreadyInstalled, PipelineError


_installed_packages = set()

class RPMChecker(PipelineStep):

    factory_priority = 1000

    @cached_property
    def installed_packages(self):
        
        if _installed_packages:
            return _installed_packages

        packages = _installed_packages

        out = call(['rpm', '-qa'], stdout=True)
        for line in out.splitlines():
            line = line.strip().lower()
            if not line:
                continue
            packages.add(line)

            chunks = line.split('-')
            for i in range(1, len(chunks)):
                packages.add('-'.join(chunks[:i]))

            chunks = line.split('.')
            for i in range(1, len(chunks)):
                packages.add('.'.join(chunks[:i]))

        return packages

    @classmethod
    def factory(cls, step, pkg):
        if step == 'init' and re.match(r'^rpm:', pkg.url):
            return cls()

    def get_next(self, step, pkg):
        return self

    def init(self, pkg):
        # Signal that we should not be persisted to the database.
        pkg.virtual = True

    def fetch(self, pkg):
        if pkg.name.lower() not in self.installed_packages:
            raise PipelineError('rpm package "%s" is not installed.' % pkg.name)
        raise AlreadyInstalled()

    def inspect(self, pkg):
        pass
        
    def extract(self, pkg):
        pass

    def build(self, pkg):
        pass

    def install(self, pkg):
        pass

    def optlink(self, pkg):
        pass

    def relocate(self, pkg):
        pass
