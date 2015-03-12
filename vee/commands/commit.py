import re

from vee.cli import style, style_error, style_note
from vee.commands.main import command, argument
from vee.git import GitRepo, normalize_git_url


levels = ['major', 'minor', 'patch']

@command(
    argument('--major', action='store_const', dest='semver_level', const=0),
    argument('--minor', action='store_const', dest='semver_level', const=1),
    argument('--patch', action='store_const', dest='semver_level', const=2),
    argument('-r', '--repo'),
    argument('-m', '--message'),
)
def commit(args):

    home = args.assert_home()
    env_repo = home.get_env_repo(args.repo)

    if not env_repo.status():
        print style_error('Nothing to commit.')
        return 1

    # Pick the level of the patch.
    while args.semver_level is None:
        print '%s [%s]:' % (
            style('How severe are the changes?', 'green', bold=True),
            style('major,minor,PATCH', faint=True),
        ),
        res = raw_input().strip() or 'patch'
        args.semver_level = dict(major=0, minor=1, patch=2).get(res)

    if args.message is None:
        default_message = '%s changes' % levels[args.semver_level]
        print '%s [%s]:' % (
            style('Enter a short commit message', 'green', bold=True),
            style(default_message, faint=True),
        ),
        args.message = raw_input().strip() or default_message

    env_repo.commit(args.message, args.semver_level)
