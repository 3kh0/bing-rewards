# Contributing

There are still many things to be done, as can be seen by the [feature request](https://discord.com/channels/1075059328681267240/1075078886678863922) section in Discord. If you feel like contributing to the project, please do! 

If you want to implement something big, please start a discussion about that in the issues! Maybe I've already had something similar in mind and we can make it happen together. However, keep in mind that the general roadmap is to make the existing features stable and get them tested.

* When making additions to the project, consider if the majority of users will benefit from your change. If not, you're probably better off forking the project.
* Also consider if your change will get in the way of other users. A good change is a change that enhances the experience of some users who want that change and does not affect users who do not care about the change.

## Branches

`Master` always reflects the latest release. Apart from changes to the documentation or hot-fixes, there should be no functional changes on this branch.

`Feature-X` branches are for new features that will be merged to master.

`dev` branch is no longer used as of 3/19/2023, use 'feature' branches instead.

## Pull Requests Guidelines

1. Formatting
	- run `black`, i.e `black BingRewards/BingRewards.py`
	- run `flake8`, i.e `flake8 BingRewards/BingRewards.py`
1. Commit guidelines
	1. Commits are squashed into fewer, logically organized commits
	1. Commits are rebased on top of `master` allowing for [fast forward merges](https://docs.gitlab.com/ee/user/project/merge_requests/methods/#fast-forward-merge) and avoiding the extra [merge commit](https://docs.gitlab.com/ee/user/project/merge_requests/methods/#merge-commit).
1. Update `CHANGELOG.md` if change is significant
1. Pass all pipeline checks
1. After merge:
	- consider tagging the change to auto-push to [DockerHub](https://hub.docker.com/repository/docker/jwong235/bing-rewards/general)

## Python version support
Will support non-deprecated versions, list [here](https://endoflife.date/python)
As of 2/8/2022, that would be python 3.7+

## Style guide
- [PEP-8](https://www.python.org/dev/peps/pep-0008/) is the ideal.
- Changes are expected to pass [flake8](https://pypi.org/project/flake8/)
- Changes are expected to conform to [black](https://pypi.org/project/black/) code formatting

## Acknowledgment
This CONTRIBUTING.md copied from [here](https://github.com/jonaswinkler/paperless-ng/blob/master/CONTRIBUTING.md)
