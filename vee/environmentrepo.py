import os
import re

from vee.git import GitRepo
from vee.requirements import Requirements, Header
from vee.utils import cached_property
from vee.exceptions import CliMixin
from vee.environment import Environment


class EnvironmentRepo(GitRepo):

    def __init__(self, dbrow, home):
        super(EnvironmentRepo, self).__init__(
            work_tree=dbrow['path'] or home._abs_path('repos', dbrow['name']),
            remote_name=dbrow['remote'],
            branch_name=dbrow['branch'],
        )
        self.id = dbrow['id']
        self.name = dbrow['name']
        self.home = home
        self._req_path = os.path.join(self.work_tree, 'requirements.txt')

    def fetch(self):
        return super(EnvironmentRepo, self).fetch(self.remote_name, self.branch_name)

    def checkout(self, force=False):
        super(EnvironmentRepo, self).checkout(
            revision='%s/%s' % (self.remote_name, self.branch_name), 
            branch=self.branch_name,
            force=force
        )

    def get_environment(self):
        return Environment(repo=self, home=self.home)
    
    def load_requirements(self, revision=None):
        reqs = Requirements(env_repo=self, home=self.home)
        if revision is not None:
            contents = self.show(revision, 'requirements.txt')
            if contents:
                reqs.parse_file(contents.splitlines())
        else:
            if os.path.exists(self._req_path):
                reqs.parse_file(self._req_path)
        return reqs

    def dump_requirements(self, req_set):
        tmp = self._req_path + '.tmp'
        with open(tmp, 'wb') as fh:
            for line in req_set.iter_dump():
                fh.write(line)
        os.rename(tmp, self._req_path)

    def commit(self, message, semver_level=None):

        self.git('add', self._req_path, silent=True)
        
        status = list(self.status())
        if not status:
            raise RuntimeError('nothing to commit')

        # Make sure there are no other changes.
        for idx, tree, name in status:
            if tree.strip():
                raise RuntimeError('work-tree is dirty')

        req_set = self.load_requirements()

        version_header = req_set.headers.get('Version')
        if not version_header:
            version_header = req_set.add_header('Version', '0.0.0')

        if semver_level is not None:
            version = []
            for i, x in enumerate(re.split(r'[.-]', version_header.value)):
                try:
                    version.append(int(x))
                except ValueError:
                    version.append(x)
            while len(version) <= semver_level:
                version.append(0)
            
            version[semver_level] = version[semver_level] + 1
            for i in xrange(semver_level + 1, len(version)):
                version[i] = 0

            version_header.value = '.'.join(str(x) for x in version)

        from vee import __about__ as about
        req_set.set_header('Vee-Revision', about.__version__ + '+' + about.__revision__)

        self.dump_requirements(req_set)

        self.git('add', self._req_path, silent=True)
        self.git('commit', '-m', message, silent=True)
