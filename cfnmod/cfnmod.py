import contextlib
import datetime
import glob
import hashlib
import io
import os
import stat
import sys
import zipfile

# from invoke import run
import boto3
import click
import yaml

ARTIFACT_BUCKET = os.environ["ARTIFACT_BUCKET"]

# load configuration
with open("module.yml", "r") as f:
    conf = yaml.load(f, Loader=yaml.FullLoader)

module_name = conf["module"]["name"]
now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
build_number = os.environ.get(
    conf["module"]["build_number_environment_variable"], f"dev{now}"
)
version = f'{conf["module"]["version"]}.{build_number}'
entrypoint = conf["module"]["entrypoint"]


@click.group()
def cli():
    pass


@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def add_file(zip_file, path):
    print(f"Adding path = {path}")
    permission = 0o555 if os.access(path, os.X_OK) else 0o444
    zip_info = zipfile.ZipInfo.from_file(path)
    zip_info.date_time = (2020, 1, 1, 0, 0, 0)
    zip_info.external_attr = (stat.S_IFREG | permission) << 16
    with open(path, "rb") as fp:
        zip_file.writestr(zip_info, fp.read())


def create_zip(files):
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zip_file:
        for folder, files in files:
            with pushd(folder):
                for path in files:
                    if os.path.isfile(path):
                        add_file(zip_file, path)
        zip_bytes.seek(0)
        return zip_bytes


def calc_md5(md5_files):
    zip_bytes = create_zip(md5_files)
    md5hash = hashlib.md5(zip_bytes.getvalue())
    return md5hash.hexdigest()


def get_latest_details(module_name):
    s3 = boto3.client("s3")
    try:
        response = s3.get_object(
            Bucket=ARTIFACT_BUCKET, Key=f"modules/{module_name}-latest.yml"
        )
        latest = yaml.load(response["Body"], Loader=yaml.FullLoader)
        return latest["version"], latest["md5sum"]
    except Exception as exc:
        if exc.response.get("Error", {}).get("Code"):
            return None, None
        else:
            raise


def collect_files(artifacts):
    md5 = {}
    full = {}
    for artifact_item in conf["module"]["artifacts"]:
        folder = artifact_item.get("folder", ".")
        with pushd(folder):
            for pattern in artifact_item.get("pattern", ["*"]):
                recursive = artifact_item.get("recursive", False)
                print(
                    f"Collecting Folder = {folder}, Pattern = {pattern}, Recursive = {recursive}"
                )
                files = sorted(glob.glob(pattern, recursive=recursive))
                full.setdefault(folder, []).extend(files)
                if artifact_item.get("include_in_md5", False):
                    print("Including in md5sum-able artifacts")
                    md5.setdefault(folder, []).extend(files)
        full[folder] = sorted(list(set(full.get(folder, []))))
        md5[folder] = sorted(list(set(md5.get(folder, []))))
    return sorted(full.items()), sorted(md5.items())


@cli.command()
def publish():
    latest_version, latest_md5sum = get_latest_details(module_name)
    all_files, md5_files = collect_files(conf["module"]["artifacts"])
    print("# Calculating md5 sum")
    new_md5sum = calc_md5(md5_files)
    if version == latest_version and new_md5sum == latest_md5sum:
        print(f"Version {version} and md5 sum {latest_md5sum} MATCH. Quitting.")
        sys.exit(0)
    elif version == latest_version and new_md5sum != latest_md5sum:
        print(
            f"Building version {version}, but version matches latest published"
            " and the md5 sums DO NOT match.  Quitting."
        )
        sys.exit(1)
    elif new_md5sum == latest_md5sum:
        print(f"Artifacts match existing latest version {latest_version}. Quitting.")
        sys.exit(0)
    key = (
        f"modules/dev/{module_name}-{version}.zip"
        if "dev" in version
        else f"modules/{module_name}-{version}.zip"
    )
    print("# Creating zip file")
    artifact_zip = create_zip(all_files)
    s3 = boto3.client("s3")
    print("# Writing artifact")
    s3.put_object(Body=artifact_zip.getvalue(), Bucket=ARTIFACT_BUCKET, Key=key)
    print(f"# Artifact written to s3://{ARTIFACT_BUCKET}/{key}")
    if "dev" not in version:
        print("# Updating {module_name} module latest details")
        latest = {"version": version, "md5sum": new_md5sum}
        key = f"modules/{module_name}-latest.yml"
        s3.put_object(
            Body=yaml.dump(latest).encode("utf-8"), Bucket=ARTIFACT_BUCKET, Key=key
        )


if __name__ == "__main__":
    cli()
