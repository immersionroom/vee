import os
import sys


# Add our vendor-ed packages to the path.
vendor_path = os.path.abspath(os.path.join(__file__, '..', '_vendor'))
if vendor_path not in sys.path:
    sys.path.append(vendor_path)

import pkg_resources

# Make sure our vendor-ed packages are added to the working_set (for)
# entry points, etc..
if vendor_path not in pkg_resources.working_set.entries:
    pkg_resources.working_set.add_entry(vendor_path)


def _bootstrap_pkg_resources():

    # See if we are already registered.
    req = pkg_resources.Requirement.parse('vee')
    dist = pkg_resources.working_set.find(req)
    if dist is not None:
        return

    # Make a dummy metadata provider (which looks in our package for metadata),
    # and a dummy distribution (which lives wherever it does on dist).
    class Provider(pkg_resources.DefaultProvider):
        egg_info = os.path.abspath(os.path.join(__file__, '..'))
    dummy = pkg_resources.Distribution(
        project_name='vee',
        version='bootstrapped',
        metadata=Provider('vee'),
        location=os.path.abspath(os.path.join(__file__, '..', '..')),
    )
    pkg_resources.working_set.add(dummy)


_bootstrap_pkg_resources()
