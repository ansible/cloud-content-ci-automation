#!/usr/bin/env bash

repo_name=$1
branch_name=$2

cd ${repo_name}
git checkout main
git pull upstream main
# git checkout -b "edit_gha_$(date +'%Y%m%d_%H%M%S')"
git checkout -b $2
