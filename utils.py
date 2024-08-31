"""Utils"""

import os
import requests
import re
from functools import partial
from multiprocessing import Pool


def cmdline_input(prompt: str, default: str) -> str:
    """Reac cmdline."""
    return input(f"{prompt} [{default}]: ").strip() or default


def is_local_file(url: str) -> bool:
    return re.match(R"/|[A-Z]:\\|\.\\|./", url)


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


def download_file(url: str, cache_dir: str, refresh=False) -> str:
    """Download a single file to the cache."""
    try:
        if is_local_file(url):
            return url
        file_name = url.split("/")[-1]
        dst_file = os.path.join(cache_dir, file_name)
        if os.path.exists(dst_file) and os.path.getsize(dst_file) > 0:
            print(f" Already here: {dst_file}.")
            return dst_file
        res = requests.get(url, timeout=1)
        with open(dst_file, "wb") as df:
            df.write(res.content)
        print(f" Downloaded {url} to {dst_file}.")
        return dst_file
    except Exception as e:
        print(e)
        return ""


def _url_to_cache_path(url: str, cache_dir: str) -> str:
    if is_local_file(url):
        return url
    file_name = url.split("/")[-1]
    return os.path.join(cache_dir, file_name)


def download_and_cache(urls: list[str], cache_dir=".cache", refresh=False) -> list[str]:
    """Download many files to the cache."""
    urls = [url.strip() for url in urls if url.strip()]
    os.makedirs(cache_dir, exist_ok=True)
    with Pool(2) as pool:
        df = partial(download_file, cache_dir=cache_dir, refresh=refresh)
        pool.map(df, urls)
    return [_url_to_cache_path(url, cache_dir) for url in urls]
