"""Base manager"""

from typing import List, Tuple, Dict, Any, Callable
from functools import cache, wraps
import logging
import json
import urllib.parse
from urllib.parse import urlencode

import requests

from single import run_once

log = logging.getLogger(__name__)


class SyncManager:
    apps_url_key: str = None
    apps_key: str = None

    field_map: List[Tuple[str, str]] = None
    field_translations: Dict[str, Callable[[Any], Any]] = {}

    def __init__(self, api_root: str, auth: Tuple[str, str], ks_filename: str = None):
        self.api_root = api_root
        self.auth = auth
        self.ks_filename = ks_filename
        self.apps_data = {}
        self.ks_data = {}

    @cache
    def get_url_map(self) -> Dict[str, str]:
        resp = requests.get(self.api_root, auth=self.auth)
        resp.raise_for_status()
        return resp.json()

    @property
    def url(self) -> str:
        return self.get_url_map()[self.apps_url_key]

    @run_once
    def load_apps_data(self):
        url = self.url
        url_parts = list(urllib.parse.urlparse(url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update({'page_size': 5000})
        url_parts[4] = urlencode(query)
        url = urllib.parse.urlunparse(url_parts)

        while url:
            log.info("Loading %s, %d records already loaded", url, len(self.apps_data))

            resp = requests.get(url, auth=self.auth).json()
            url = resp["next"]

            for record in resp["results"]:
                key = record[self.apps_key]
                self.apps_data[key] = record

        log.info("Finished loading from %s, got %d records", self.url, len(self.apps_data))

    @run_once
    def load_ks_data(self) -> Dict[str, dict]:
        with open(self.ks_filename) as f_in:
            data = json.load(f_in)

            for i, record in enumerate(data["records"]):
                try:
                    translated = self.translate(record)
                    key = translated[self.apps_key]
                    self.ks_data[key] = translated
                except InvalidRecord as exc:
                    log.error("Unable to load Keystone record %d: %s", i, exc)

    def get_url_for_key(self, key: str) -> str:
        self.load_apps_data()
        self.create()  # Make sure records are up to date

        return self.apps_data[key]["url"]

    @run_once
    def delete(self):
        self.load_apps_data()
        self.load_ks_data()

        to_delete = self.apps_data.keys() - self.ks_data.keys()

        for key in to_delete:
            record = self.apps_data[key]
            url = record["url"]

            resp = requests.delete(url, auth=self.auth)
            resp.raise_for_status()
            log.info("Deleted %s", url)

    @run_once
    def create(self):
        self.load_apps_data()
        self.load_ks_data()

        to_create = self.ks_data.keys() - self.apps_data.keys()

        log.info("Creating %d new records", len(to_create))

        for key in to_create:
            desired_record = self.ks_data[key]
            resp = requests.post(self.url, auth=self.auth, data=desired_record)
            data = resp.json()

            if resp.status_code >= 400 and resp.status_code < 500:
                log.warning("Unexpected status code when creating %s: %s", key, resp.status_code)
                for attr, errors in data.items():
                    if attr in desired_record:
                        for error in errors:
                            log.error("Error when creating %s on field %s: '%s'. Original value was '%s'",
                                      key, attr, error, desired_record[attr])

                    elif attr == 'detail':
                        log.error("Error when creating %s: %s", key, errors)

                continue

            resp.raise_for_status()
            log.info("Created %s at %s: %d", key, data["url"], resp.status_code)
            self.apps_data[key] = data

    @run_once
    def update(self):
        self.load_apps_data()
        self.load_ks_data()

        update_candidates = self.ks_data.keys() & self.apps_data.keys()

        for key in update_candidates:
            current_record = self.apps_data[key]
            desired_record = self.ks_data[key]

            if should_update(desired_record, current_record):
                url = current_record["url"]
                resp = requests.put(url, auth=self.auth, data=desired_record)
                resp.raise_for_status()
                log.info("Updated %s", url)

    def translate(self, ks_record: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a Keystone record into an apps record"""

        if not self.ks_key in ks_record:
            raise MissingKey(ks_record)
        
        if not ks_record[self.ks_key]:
            raise MissingKeyValue(ks_record)

        out = {}

        for apps_attr, ks_attr in self.field_map:
            val = ks_record[ks_attr].strip()  # DRF will strip whitespace, so this prevents a needless update
            if apps_attr in self.field_translations:
                val = self.field_translations[apps_attr](val)

            out[apps_attr] = val

        return out

    def sync(self):
        self.load_ks_data()
        self.load_apps_data()

        self.create()
        self.update()
        self.delete()


def should_update(desired: Dict[str, Any], current: Dict[str, Any]) -> bool:
    """Determine if a record for a given key should be updated"""

    for attr_name, desired_value in desired.items():
        current_value = current[attr_name]

        if current_value != desired_value:
            return True

    return False

class InvalidRecord(Exception):
    """Indicates a record is invalid"""

    def __init__(self, record: Dict[str, Any]):
        self.record = record

class MissingKey(InvalidRecord):
    """Indicates the key field is missing"""

    def __str__(self):
        return "Key field is missing"

class MissingKeyValue(InvalidRecord):
    """Indicates the key value is missing"""

    def __str__(self):
        return "Key value is missing"