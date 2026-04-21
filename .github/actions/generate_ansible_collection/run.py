# Copyright 2026 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import os

import pbr.version
from ruamel.yaml import YAML


def generate_version_info(path):
    version_info = pbr.version.VersionInfo('random')
    semantic_version = version_info.semantic_version()
    print(f"Semantic version: {semantic_version}")

    yaml = YAML()
    yaml.explicit_start = True
    yaml.indent(sequence=4, offset=2)

    galaxy_path = os.path.join(os.path.expanduser(path), 'galaxy.yml')
    config = yaml.load(open(galaxy_path))
    try:
        galaxy_version = str(config.get('version')).replace("-", ".")
        galaxy_version = pbr.version.SemanticVersion.from_pip_string(galaxy_version)
    except (ValueError, TypeError):
        raise KeyError(f"Galaxy version error for collection path {path!r}")

    config['version'] = galaxy_version._long_version('-')
    with open(galaxy_path, 'w') as fp:
        yaml.dump(config, fp)
    return f"{config['namespace']}-{config['name']}-{config['version']}.tar.gz"


def main():
    result = generate_version_info(sys.argv[1])
    print(f"Collection tarball: {result}")


if __name__ == "__main__":
    main()
