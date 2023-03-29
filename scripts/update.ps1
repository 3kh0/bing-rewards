$branch = git rev-parse --abbrev-ref HEAD
if ($branch -ne 'master') {
    git checkout master
}

git pull
pip install -r BingRewards/requirements.txt
