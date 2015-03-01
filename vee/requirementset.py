import re

from vee.requirement import Requirement
from vee.utils import guess_name


class Envvar(tuple):

    def __new__(cls, name, value):
        return super(Envvar, cls).__new__(cls, (name, value))

    @property
    def name(self):
        return self[0]

    @property
    def value(self):
        return self[1]

    def __str__(self):
        return '%s=%s' % self


class Header(tuple):

    def __new__(cls, name, value):
        name = '-'.join(x.title() for x in name.split('-'))
        return super(Header, cls).__new__(cls, (name, value))

    @property
    def name(self):
        return self[0]

    @property
    def value(self):
        return self[1]

    def __str__(self):
        return '%s: %s' % self


class RequirementSet(object):

    def __init__(self, source=None):
        self.elements = []
        if source:
            self.parse(source)

    def parse(self, source, home=None):
        
        environ = {}

        if isinstance(source, basestring):
            source = open(source, 'r')

        line_iter = iter(source)
        for line in line_iter:

            line = line.rstrip()
            while line.endswith('\\'):
                line = line[:-1] + next(line_iter).rstrip()

            m = re.match(r'^(\s*)([^#]*?)(\s*#.*)?$', line)
            before, spec, after = m.groups()
            before = before or ''
            after = after or ''

            if not spec:
                self.elements.append((before, '', after))
                continue

            m = re.match(r'^(\w+)=(\S.*)$', spec)
            if m:
                name, value = m.groups()
                environ[name] = value
                self.elements.append((before, Envvar(name, value), after))
                continue

            m = re.match(r'^([\w-]+): (\S.*)$', spec)
            if m:
                self.elements.append((before, Header(*m.groups()), after))
                continue

            req = Requirement(spec, home=home)
            for k, v in environ.iteritems():
                req.environ.setdefault(k, v)

            self.elements.append((before, req, after))

    def iter_requirements(self):
        for _, element, _ in self.elements:
            if isinstance(element, Requirement):
                yield element

    def guess_names(self, strict=True):
        """Guess names for every requirement which does not already have one.

        This mutates the requirements as it goes; if it fails then some
        requirements will have already had their name set.

        """

        names = set()
        to_guess = []

        # First pass: the explicitly named.
        for req in self.iter_requirements():

            if not req.name:
                to_guess.append(req)
                continue

            if req.name.lower() in names:
                raise ValueError('name collision; please rename one of the %rs' % name)
            names.add(req.name.lower())

        # Second pass; the rest.
        for req in to_guess:
            name = guess_name(req.url)
            if name.lower() in names:
                if strict:
                    raise ValueError('name collision; please set name for one of the %rs' % name)
            else:
                names.add(name.lower())
                req.name = name



    def iter_dump(self, freeze=False):

        # We track the state of the environment as we progress, and don't
        # include envvars in each requirement if they exactly match those
        # in the current state.
        environ = {}

        for before, element, after in self.elements:

            if isinstance(element, Envvar):
                environ[element.name] = element.value

            if isinstance(element, Requirement):
                if freeze:
                    req = element = element.package.freeze(environ=False)
                else:
                    req = element
                for k, v in environ.iteritems():
                    if req.environ.get(k) == v:
                        del req.environ[k]

            yield '%s%s%s\n' % (before, element, after)



if __name__ == '__main__':

    import sys

    from vee.home import Home

    home = Home('/usr/local/vee')
    rs = RequirementSet()
    rs.parse(sys.stdin, home=home)

    rs.guess_names()
    
    print ''.join(rs.iter_dump())


