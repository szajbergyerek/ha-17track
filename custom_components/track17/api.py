"""API client for the 17TRACK REST API (v2.4), used by the 17TRACK Home Assistant integration."""

from datetime import datetime

import requests

from .const import DEFAULT_BASE_URL


class Track17ApiError(Exception):
    """Raised when the 17TRACK API returns an error response (bad API key, rejected tracking number, etc.)."""


class Track17ConnectionError(Track17ApiError):
    """Raised when the 17TRACK API could not be reached at all (network/timeout failure)."""


class Track17Api:

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL) -> None:
        """
        Initialize the 17TRACK API client.

        param api_key: The 17TRACK API key (17token) used to authenticate requests.
        param base_url: Base URL of the 17TRACK tracking API.

        :return: None
        """
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self) -> dict:
        """
        Build the HTTP headers required by the 17TRACK API.

        :return: A dictionary of HTTP headers including the API key.
        """
        return {
            "17token": self.api_key,
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload) -> dict:
        """
        POST a request to the given 17TRACK API path and return its decoded result.

        param path: The API path to call, relative to the base url (e.g. "/register").
        param payload: The JSON-serializable request body.

        :return: The "result" object from the API response, once its top-level code has been checked.
        """
        try:
            response = requests.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as error:
            raise Track17ConnectionError(f"Error communicating with the 17TRACK API: {error}") from error

        if result["code"] != 0:
            raise Track17ApiError(result.get("message", "Unknown 17TRACK API error"))

        return result

    def get_all_packages(self) -> list:
        """
        Fetch every package currently registered with 17TRACK, across all result pages.

        :return: A list of raw package dictionaries as returned by the gettracklist endpoint.
        """
        packages = []
        page_no = 1

        while True:
            result = self._post("/gettracklist", {"page_no": page_no})
            packages.extend(result["data"]["accepted"])

            if not result["page"]["has_next"]:
                break
            page_no += 1

        return packages

    def delete_packages(self, packages: list) -> None:
        """
        Delete the given packages from 17TRACK so they are no longer tracked.

        param packages: A list of dictionaries with "number" and "carrier" keys identifying the packages to delete.

        :return: None
        """
        chunk_size = 40
        for start in range(0, len(packages), chunk_size):
            chunk = packages[start : start + chunk_size]
            self._post(
                "/deletetrack",
                [{"number": package["number"], "carrier": package["carrier"]} for package in chunk],
            )

    def register_package(self, tracking_number: str, tag: str | None = None) -> None:
        """
        Register a new tracking number with 17TRACK so it starts being tracked.

        param tracking_number: The tracking number to register for tracking.
        param tag: Optional user-facing label for the package, shown instead of the tracking number.

        :return: None
        """
        item = {"number": tracking_number}
        if tag:
            item["tag"] = tag

        result = self._post("/register", [item])

        rejected = result["data"].get("rejected") or []
        if rejected:
            reason = rejected[0].get("error", {}).get("message", "Unknown reason")
            raise Track17ApiError(f'17TRACK rejected tracking number "{tracking_number}": {reason}')


def get_package_description(package: dict) -> str:
    """
    Extract the latest event description from a raw package entry, without the trailing tracking number.

    param package: One package dictionary as returned by the 17TRACK gettracklist endpoint.

    :return: The cleaned latest event description.
    """
    return (package.get("latest_event_info") or "").split("Tracking number:")[0].strip()


def format_package_status(package: dict) -> str:
    """
    Format one raw package entry as 'On <date> package "<name>": <message>'.

    param package: One package dictionary as returned by the 17TRACK gettracklist endpoint.

    :return: The formatted status sentence for this package.
    """
    package_name = package.get("tag") or package["number"]
    time_iso = package.get("latest_event_time")
    formatted_date = datetime.fromisoformat(time_iso).strftime("%Y.%m.%d %H:%M") if time_iso else "unknown date"
    return f'On {formatted_date} package "{package_name}": {get_package_description(package)}'
