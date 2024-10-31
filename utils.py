"""Utils"""

import os
import re
from datetime import datetime
from functools import partial
from multiprocessing import Pool
import zipfile

import requests


def log(*args, **argv):
    """Print with time."""
    print(datetime.now().strftime("[%H:%M:%S]"), *args, **argv)


def cmdline_input(prompt: str, default: str) -> str:
    """Reac cmdline."""
    return input(f"{prompt} [{default}]: ").strip() or default


def is_local_file(url: str) -> bool:
    """True if file does not need to be downloaded."""
    return re.match(R"/|[A-Z]:\\|\.\\|./", url)


def cache_path(fname: str, ext="", cache_dir=".cache"):
    """Output filename of mesh operations."""
    if is_local_file(fname):
        basename = os.path.basename(fname)
    else:
        basename = fname.split("/")[-1]
    dst_file = os.path.join(cache_dir, basename)
    if ext:
        dst_file = os.path.splitext(dst_file)[0] + ext
    return dst_file


def url_lines(url: str) -> list[str]:
    """Read lines"""
    lines = []
    if is_local_file(url):
        with open(url, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    else:
        res = requests.get(url, timeout=1)
        lines = res.content.decode("utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def download_file(url: str, cache_dir: str) -> str:
    """Download a single file to the cache."""
    try:
        if is_local_file(url):
            return url
        dst_file = cache_path(url, cache_dir=cache_dir)
        if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
            log(f" Already here: {dst_file}.")
            return dst_file
        res = requests.get(url, timeout=1)
        with open(dst_file, "wb") as df:
            df.write(res.content)
        log(f" Downloaded {url} to {dst_file}.")
        return dst_file
    except Exception as e:
        log(e)
        return ""


def _url_to_cache_path(url: str, cache_dir: str) -> str:
    if is_local_file(url):
        return url
    return cache_path(url, cache_dir=cache_dir)


def download_and_cache(urls: list[str], cache_dir=".cache") -> list[str]:
    """Download many files to the cache."""
    urls = [url.strip() for url in urls if url.strip()]
    os.makedirs(cache_dir, exist_ok=True)
    with Pool(20 if len(urls) >= 20 else len(urls)) as pool:
        df = partial(download_file, cache_dir=cache_dir)
        pool.map(df, urls)
    return [_url_to_cache_path(url, cache_dir) for url in urls]


def zip_has_file(fname: str, pattern: str):
    """Test if the fname is a zip and contains a file with the pattern"""
    try:
        if not fname.endswith(".zip"):
            return False
        with zipfile.ZipFile(fname) as zf:
            for zfn in zf.namelist():
                if pattern in zfn:
                    return True
        return False
    except Exception as e:
        print(f"ERROR {e}")
        return False
