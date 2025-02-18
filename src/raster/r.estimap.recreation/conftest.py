import functools
import py
import pytest
from ruamel.yaml import YAML

# from .runner import estimap_test_runner

import hashlib
import os
import pathlib
import shlex
import subprocess
import tempfile
import uuid


def exec_grass(mapset, cmd, **kwargs):
    cmd = f"grass {mapset} --exec {cmd}"
    process = subprocess.run(shlex.split(cmd), check=True, **kwargs)
    return process


def construct_r_estimap_command(test_case):
    flags = " ".join(test_case["flags"])
    inputs = " ".join([f"{k}={','.join(v)}" for (k, v) in test_case["inputs"].items()])
    output_maps = " ".join(
        [f"{k}={v['name']}" for (k, v) in test_case["outputs"]["maps"].items()]
    )
    output_csvs = " ".join(
        [f"{k}={v['name']}" for (k, v) in test_case["outputs"]["csvs"].items()]
    )
    cmd = f"r.estimap.recreation {flags} {inputs} {output_maps} {output_csvs}"
    return cmd


def generate_univar_md5sum(mapset, map_name):
    txt = pathlib.Path("/tmp") / f"{uuid.uuid4().hex}.txt"
    exec_grass(mapset, f"r.univar --o -e {map_name} output={txt.as_posix()}")
    m = hashlib.md5()
    m.update(txt.read_bytes())
    return m.hexdigest()


def generate_csv_md5sum(mapset, csv_file):
    m = hashlib.md5()
    m.update(pathlib.Path(csv_file).read_bytes())
    return m.hexdigest()


import subprocess
import shlex
import shutil

# from .utilities import (
#     exec_grass,
#     construct_r_estimap_command,
#     generate_univar_md5sum,
#     generate_csv_md5sum,
# )
# from . import GRASSDB

import pathlib
import shlex
import shutil
import subprocess

from ruamel.yaml import YAML

yaml = YAML(typ="safe", pure=True)

# TEST_DIR = pathlib.Path(__file__).parent.resolve()
TEST_DIR = pathlib.Path(__file__).parent.resolve() / "tests"
DATA_DIR = TEST_DIR / "data"
ROOT_DIR = TEST_DIR.parent
GRASSDB = DATA_DIR / "grassdb_estimap_recreation"
GRASSDB_TAR = DATA_DIR / "example_grassdb_epsg_3035.tar.gz"


def check_wget_availability():
    if not shutil.which("wget"):
        raise ValueError("wget is missing, please install it and re-run")


def download_data():
    cmd = "wget https://gitlab.com/natcapes/r.estimap.recreation.data/raw/master/example_grassdb_epsg_3035.tar.gz"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)


def extract_data():
    # cleanup (needed in case data files have changed and we have manually updated the tar)
    print("Cleaning up existing data fixtures")
    cmd = f"rm -rf {GRASSDB.as_posix()}"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)
    # extract
    print("Extracting data fixtures")
    cmd = "tar xf example_grassdb_epsg_3035.tar.gz"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)


def ensure_data_availability():
    if not GRASSDB.exists():
        check_wget_availability()
        print("Downloading data")
        download_data()
        extract_data()


ensure_data_availability()


def estimap_test_runner(test_case):
    mapset = f"{GRASSDB}/{test_case['mapset']}"

    # check if the mapset already exists
    cmd = f"grass {GRASSDB}/PERMANENT --exec g.mapset -l"
    proc = subprocess.run(
        shlex.split(cmd), check=True, universal_newlines=True, stdout=subprocess.PIPE
    )
    if test_case["mapset"] in proc.stdout:
        # The mapset already exists. Cleanup maps and remove it.
        # Cleaning up the maps is necessary due to GRASS linking maps
        exec_grass(mapset, "g.remove -f type=all pattern=*")
        shutil.rmtree(mapset, ignore_errors=True)

    # create temporary mapset
    cmd = f"grass -c -e {mapset}"
    proc = subprocess.run(shlex.split(cmd), check=True)

    # add the 'sample_data' Mapset to the current Mapset's search path
    exec_grass(mapset, "g.mapsets sample_data operation=add")

    # set region
    exec_grass(mapset, "g.region raster=input_area_of_interest")

    # run the test
    estimap_cmd = construct_r_estimap_command(test_case)
    exec_grass(mapset, f"{estimap_cmd}")

    # check map hashes
    for i, (key, data) in enumerate(test_case["outputs"]["maps"].items()):
        map_name = data["name"]
        expected_hash = data["hash"]
        generated_hash = generate_univar_md5sum(mapset, map_name)
        assert expected_hash == generated_hash, f"map hash mismatch: {map_name}"

    # check csv hashes
    for i, (key, data) in enumerate(test_case["outputs"]["csvs"].items()):
        csv_name = data["name"]
        expected_hash = data["hash"]
        generated_hash = generate_csv_md5sum(mapset, csv_name)
        assert expected_hash == generated_hash, f"csv hash mismatch: {csv_name}"


yaml = YAML(typ="safe", pure=True)


def pytest_collect_file(file_path: pathlib.Path, parent):
    if file_path.suffix in (".yml", ".yaml") and file_path.name.startswith("test"):
        return YamlFile.from_parent(parent=parent, path=file_path)


class YamlFile(pytest.File):
    def collect(self):
        test_cases = yaml.load(self.fspath.open())
        for case in test_cases:
            module = pathlib.Path(str(self.path).replace(".yml", ".py"))
            yield pytest.Function.from_parent(
                name=case["mapset"],
                # parent=pytest.Module(fspath=os.path.abspath(__file__), parent=self),
                parent=pytest.Module.from_parent(parent=self, path=module),
                # parent=pytest.Module(fspath=module, parent=self),
                callobj=functools.partial(estimap_test_runner, case),
            )
