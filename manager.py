"""Base manager"""

import time
from typing import Any, List, Tuple, Dict, Iterable, Hashable, Callable, Optional
from functools import cache
import logging
import json
import urllib.parse

import requests
from tqdm import tqdm

from single import run_once

log = logging.getLogger(__name__)


class AppsManager:
    url_key: str = None
    key_name: str = None
    
    def __init__(self, api_root: str, auth: Tuple[str, str]):
        self.api_root = api_root
        self.apps_data = {}
        self.session = requests.session()
        self.session.auth = auth
    
    def get_url_for_key(self, key: str) -> Optional[str]:
        """Get the URL for a given key"""

        if not key:
            return None

        self.load_apps_data()

        if not key in self.apps_data:
            return None

        return self.apps_data[key]["url"]

    def get_key_value(self, record: Dict[str, Any]) -> Hashable:
        """Get the key to use for a given record"""

        if not self.key_name in record:
            raise MissingKey(record)
        
        if not record[self.key_name]:
            raise MissingKeyValue(record)
        
        return record[self.key_name]

    @cache
    def get_url_map(self) -> Dict[str, str]:
        for i in range(10):
            try:
                resp = self.session.get(self.api_root)
                resp.raise_for_status()
                return resp.json()
            except requests.ConnectionError:
                log.error("Connection error when getting URL map")
                time.sleep(5)

    @run_once
    def load_apps_data(self):
        url = self.url

        log.info("Beginning apps data load from %s", url)

        url_parts = list(urllib.parse.urlparse(url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update({'page_size': 5000})
        url_parts[4] = urllib.parse.urlencode(query)
        url = urllib.parse.urlunparse(url_parts)

        while url:
            log.debug("Loading %s, %d records already loaded", url, len(self.apps_data))

            resp = self.session.get(url)
            data = resp.json()
            url = data["next"]

            for record in data["results"]:
                key = self.get_key_value(record)
                
                # We're only storing the URLs here
                self.apps_data[key] = record

        log.info("Finished loading from %s, got %d records", self.url, len(self.apps_data))
    
    @property
    def url(self) -> str:
        return self.get_url_map()[self.url_key]

class SyncManager(AppsManager):
    field_map: List[Tuple[str, str]] = None
    field_translations: Dict[str, Callable[[Any], Any]] = {}
    required_fields: List[str] = []
    

    def __init__(self, api_root: str, auth: Tuple[str, str], ks_filename: str = None):
        super().__init__(api_root=api_root, auth=auth)
        self.ks_filename = ks_filename
        self.ks_data = {}

    def get_url_for_key(self, key: str) -> str:
        self.create()

        return super().get_url_for_key(key)

    @run_once
    def load_ks_data(self) -> Dict[str, dict]:
        log.info("Beginning Keystone data load from %s", self.ks_filename)

        with open(self.ks_filename) as f_in:
            data = json.load(f_in)

            for i, record in enumerate(data["records"]):
                try:
                    for j, translated in enumerate(self.split(record)):
                        try:
                            key = self.get_key_value(translated)
                        
                            self.ks_data[key] = translated
                        except InvalidRecord as exc:
                            log.error("Unable to load Keystone record %d subrecord %d: %s (%s)", i, j, exc, exc.record)
                except InvalidRecord as exc:
                    log.error("Unable to load Keystone record %d: %s (%s)", i, exc, exc.record)

    

    @run_once
    def delete(self):
        self.load_apps_data()
        self.load_ks_data()

        to_delete = self.apps_data.keys() - self.ks_data.keys()
        
        if not to_delete:
            log.info("No records to delete")
            return

        log.info("Deleting %d records under %s", len(to_delete), self.url_key)

        for key in tqdm(to_delete):
            record = self.apps_data[key]
            url = record["url"]

            resp = self.session.delete(url)
            resp.raise_for_status()
            log.info("Deleted %s", url)

    @run_once
    def create(self):
        self.load_apps_data()
        self.load_ks_data()

        to_create = self.ks_data.keys() - self.apps_data.keys()

        if not to_create:
            log.info("No records to create")
            return

        log.info("Creating %d new records under %s", len(to_create), self.url_key)

        for key in tqdm(to_create):
            desired_record = self.ks_data[key]
            resp = self.session.post(self.url, json=desired_record)
            data = resp.json()

            if resp.status_code >= 400 and resp.status_code < 500:
                log.warning("Unexpected status code when creating %s: %s", key, resp.status_code)
                for attr, errors in data.items():
                    if attr == 'detail' and isinstance(errors, str):
                        log.error("Error when creating %s: %s", key, errors)
                    else:                        
                        for error in errors:
                            log.error("Error when creating %s on field %s: '%s'. Original value was '%s'",
                                    key, attr, error, desired_record[attr])

                continue

            resp.raise_for_status()
            log.debug("Created %s at %s: %d", key, data["url"], resp.status_code)
            self.apps_data[key] = data
        
        log.info("Record creation finished")

    @run_once
    def update(self):
        self.load_apps_data()
        self.load_ks_data()

        update_candidates = self.ks_data.keys() & self.apps_data.keys()

        to_update = set()

        for key in update_candidates:
            current_record = self.apps_data[key]
            desired_record = self.ks_data[key]

            if should_update(desired_record, current_record):
                to_update.add(key)
        
        if not to_update:
            log.info("No records to update")
            return

        log.info("Updating %d records under %s", len(to_update), self.url_key)

        for key in tqdm(to_update):
            desired_record = self.ks_data[key]
            current_record = self.apps_data[key]
            url = current_record["url"]
            resp = self.session.put(url, json=desired_record)
            resp.raise_for_status()
            log.debug("Updated %s", url)

        log.info("Updated %d records", len(to_update))

    def split(self, ks_record: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        """Split a single incoming record into one or more translated outgoing records"""

        yield self.translate(ks_record)


    def translate(self, ks_record: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a Keystone record into an apps record"""

        out = {}

        for apps_attr, ks_attr in self.field_map:
            val = ks_record[ks_attr]
            
            if isinstance(val, str):
                val = val.strip()  # DRF will strip whitespace, so this prevents a needless update

            if apps_attr in self.field_translations:
                val = self.field_translations[apps_attr](val)

            out[apps_attr] = val

        for key in self.required_fields:
            if not key in out:
                raise MissingRequiredValue(out, key)
            
            if not out[key]:
                raise MissingRequiredValue(out, key)

        return out

    def sync(self):
        self.load_ks_data()
        self.load_apps_data()

        self.delete()
        self.create()
        self.update()
        


class GetOrCreateManager(AppsManager):
    """Get or create manager gets URLS for various IDs and such"""

    def get_url_for_key(self, key) -> Optional[str]:
        self.load_apps_data()

        if not key:
            return None

        if key in self.apps_data:
            return self.apps_data[key]["url"]
        
        # We didn't have it - create the record
        resp = self.session.post(self.url, json={self.key_name: key})
        resp.raise_for_status()
        data = resp.json()

        self.apps_data[key] = data

        return data["url"]


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

class MissingRequiredValue(InvalidRecord):
    def __init__(self, record: Dict[str, Any], key: str):
        super().__init__(record)
        self.key = key
    
    def __str__(self):
        return f"Missing key '{self.key}'"
