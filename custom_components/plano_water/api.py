"""API client for Plano Water portal."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from .const import (
    ACCOUNT_SUMMARY_URL,
    BASE_URL,
    DEFAULT_TIMEOUT,
    LOGIN_URL,
    METER_READS_URL,
)

_LOGGER = logging.getLogger(__name__)


class PlanoWaterAPI:
    """API client for Plano Water portal."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the API client."""
        self.username = username
        self.password = password
        self.session: aiohttp.ClientSession | None = None
        self.account_info: dict[str, Any] = {}
        self.meter_info: dict[str, Any] = {}

    async def async_login(self) -> bool:
        """Login to the Plano Water portal."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            )

        try:
            # Get login page to extract viewstate and other form data
            async with self.session.get(LOGIN_URL) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get login page: %s", response.status)
                    return False
                
                login_html = await response.text()
                soup = BeautifulSoup(login_html, "html.parser")
                
                # Extract form data
                viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
                viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
                event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
                
                # Find antiforgery token
                antiforgery_input = soup.find("input", {"name": "ctl00$MainContent$antiforgery"})
                antiforgery_token = antiforgery_input["value"] if antiforgery_input else ""

            # Prepare login form data
            form_data = {
                "__LASTFOCUS": "",
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "", 
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstate_generator,
                "__EVENTVALIDATION": event_validation,
                "ctl00$MainContent$Login1$UserName": self.username,
                "ctl00$MainContent$Login1$Password": self.password,
                "ctl00$MainContent$Login1$test": "Log in",
                "ctl00$MainContent$antiforgery": antiforgery_token,
            }

            # Perform login
            async with self.session.post(
                LOGIN_URL + "?ReturnUrl=%2fAccountSummary",
                data=form_data,
                allow_redirects=True,
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Login failed with status: %s", response.status)
                    return False
                
                # Check if login was successful by looking for account info
                content = await response.text()
                if "Welcome," in content and "Account Number:" in content:
                    _LOGGER.info("Successfully logged into Plano Water portal")
                    return True
                else:
                    _LOGGER.error("Login failed - invalid credentials or page structure changed")
                    return False

        except Exception as exc:
            _LOGGER.exception("Error during login: %s", exc)
            return False

    async def async_get_account_info(self) -> dict[str, Any]:
        """Get account information from the portal."""
        if not self.session:
            if not await self.async_login():
                return {}

        try:
            async with self.session.get(ACCOUNT_SUMMARY_URL) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get account summary: %s", response.status)
                    return {}

                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")

                # Extract account information
                account_summary = soup.find("span", {"id": "MainContent_lblAccountSummary"})
                if not account_summary:
                    return {}

                account_text = account_summary.get_text()
                
                # Parse account number
                account_match = re.search(r"Account Number:\s*(\d+)", account_text)
                account_number = account_match.group(1) if account_match else ""

                # Parse name
                name_match = re.search(r"Name:\s*([^\n]+)", account_text)
                name = name_match.group(1).strip() if name_match else ""

                # Parse address
                address_match = re.search(r"Address:\s*([^\n]+)", account_text)
                address = address_match.group(1).strip() if address_match else ""

                # Extract meter information
                meter_select = soup.find("select", {"id": "MainContent_ddMeters"})
                meter_id = ""
                meter_number = ""
                if meter_select:
                    selected_option = meter_select.find("option", {"selected": "selected"})
                    if selected_option:
                        meter_id = selected_option.get("value", "")
                        meter_number = selected_option.get_text().strip()

                self.account_info = {
                    "account_number": account_number,
                    "name": name,
                    "address": address,
                    "meter_id": meter_id,
                    "meter_number": meter_number,
                }

                return self.account_info

        except Exception as exc:
            _LOGGER.exception("Error getting account info: %s", exc)
            return {}

    async def async_get_usage_data(self, days: int = 30) -> dict[str, Any]:
        """Get water usage data from the portal."""
        if not self.session or not self.account_info:
            if not await self.async_login():
                return {}
            await self.async_get_account_info()

        if not self.account_info.get("meter_id"):
            _LOGGER.error("No meter ID available")
            return {}

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates as expected by the API
            start_str = start_date.strftime("%m/%d/%Y")
            end_str = end_date.strftime("%m/%d/%Y")

            # Prepare API request
            api_data = {
                "mtuID": self.account_info["meter_id"],
                "sStart": start_str,
                "sEnd": end_str,
            }

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "X-Requested-With": "XMLHttpRequest",
            }

            async with self.session.post(
                METER_READS_URL,
                data=json.dumps(api_data),
                headers=headers,
            ) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get usage data: %s", response.status)
                    return {}

                result = await response.json()
                
                # Parse the response
                if isinstance(result, dict) and "d" in result:
                    data = json.loads(result["d"])
                    if data.get("status") and "list" in data:
                        return self._parse_usage_data(data["list"])
                
                _LOGGER.warning("Unexpected API response format")
                return {}

        except Exception as exc:
            _LOGGER.exception("Error getting usage data: %s", exc)
            return {}

    def _parse_usage_data(self, usage_list: list) -> dict[str, Any]:
        """Parse usage data from API response."""
        if not usage_list:
            return {}

        current_usage = 0
        daily_usage = 0
        last_reading = None

        try:
            # Sort by date (most recent first)
            sorted_usage = sorted(
                usage_list,
                key=lambda x: datetime.strptime(x.get("billDate", ""), "%m/%d/%Y"),
                reverse=True,
            )

            if sorted_usage:
                # Get most recent reading
                latest = sorted_usage[0]
                current_usage = float(latest.get("totalGallonsUsed", 0))
                last_reading = latest.get("billDate", "")

                # Calculate daily usage (sum of today's readings)
                today = datetime.now().strftime("%m/%d/%Y")
                daily_usage = sum(
                    float(reading.get("totalGallonsUsed", 0))
                    for reading in usage_list
                    if reading.get("billDate", "").startswith(today.split("/")[0] + "/" + today.split("/")[1])
                )

        except Exception as exc:
            _LOGGER.exception("Error parsing usage data: %s", exc)

        return {
            "current_usage": current_usage,
            "daily_usage": daily_usage,
            "last_reading": last_reading,
            "raw_data": usage_list,
        }

    async def async_close(self) -> None:
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None