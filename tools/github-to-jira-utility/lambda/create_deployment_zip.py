#!/usr/bin/env python3
"""
Create Lambda deployment zip package.
Packages all dependencies from the 'package' directory and handler.py into deploy.zip.
"""
import zipfile
import os
import sys


def create_deployment_zip(output_file="deploy.zip", package_dir="package", handler_file="handler.py"):
    """
    Create a deployment zip file for Lambda.

    Args:
        output_file: Name of the output zip file
        package_dir: Directory containing installed dependencies
        handler_file: Lambda handler Python file
    """
    try:
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add all files from the package directory
            if os.path.exists(package_dir):
                for root, _, files in os.walk(package_dir):
                    for f in files:
                        path = os.path.join(root, f)
                        arcname = os.path.relpath(path, package_dir)
                        zf.write(path, arcname)

            # Add the handler file
            if os.path.exists(handler_file):
                zf.write(handler_file, handler_file)
            else:
                print(f"Warning: {handler_file} not found", file=sys.stderr)
                return 1

        print(f"Successfully created {output_file}")
        return 0

    except Exception as e:
        print(f"Error creating deployment zip: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(create_deployment_zip())
