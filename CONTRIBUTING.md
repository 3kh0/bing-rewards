# Contributing

There are still many things to be done, just have a look at that issue log. If you feel like contributing to the project, please do! 

If you want to implement something big, please start a discussion about that in the issues! Maybe I've already had something similar in mind and we can make it happen together. However, keep in mind that the general roadmap is to make the existing features stable and get them tested.

* When making additions to the project, consider if the majority of users will benefit from your change. If not, you're probably better off forking the project.
* Also consider if your change will get in the way of other users. A good change is a change that enhances the experience of some users who want that change and does not affect users who do not care about the change.

## Branches

`Master` always reflects the latest release. Apart from changes to the documentation or hot-fixes, there should be no functional changes on this branch in between releases.

`dev` contains all changes that will be part of the next release. Use this branch to start making your changes.

`Feature-X` branches are for experimental features that will eventually be merged into dev, and then released as part of the next release.

## Pull Requests Guidelines

1. Commits are squashed into fewer, logically organized commits
2. PR to `dev` NOT master
3. Commits are rebased on top of `dev` allowing for fast forward merges and avoiding the extra merge commit

## Python version support
Will support non-deprecated versions, list [here](https://endoflife.date/python)
As of 2/8/2022, that would be python 3.7+

## Style guide
[PEP-8](https://www.python.org/dev/peps/pep-0008/) is the ideal.

## Acknowledgment
This CONTRIBUTING.md copied from [here](https://github.com/jonaswinkler/paperless-ng/blob/master/CONTRIBUTING.md)
