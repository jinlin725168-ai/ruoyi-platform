"""Minimal HTTP client for RuoYi-Vue-Plus smoke cases (standard library only).

Cases import it with `from ruoyi_client import Client`; the executor puts this directory on
PYTHONPATH and exports SMOKE_BASE_URL / SMOKE_CLIENT_ID.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_CLIENT_ID = "e5cd7e4891bf95d1d19206ce24a7b32e"  # sys_client 'pc' row shipped with ry_vue.sql
DEFAULT_TENANT = "000000"


class ApiError(AssertionError):
    def __init__(self, status: int, body: object, path: str):
        super().__init__(f"{path} -> HTTP {status}: {json.dumps(body, ensure_ascii=False)[:500]}")
        self.status, self.body, self.path = status, body, path


class Client:
    def __init__(self, base_url: str | None = None, client_id: str | None = None):
        self.base_url = (base_url or os.environ["SMOKE_BASE_URL"]).rstrip("/")
        self.client_id = client_id or os.environ.get("SMOKE_CLIENT_ID", DEFAULT_CLIENT_ID)
        self.token: str | None = None

    def login(self, username: str = "admin", password: str = "admin123",
              tenant_id: str = DEFAULT_TENANT) -> dict:
        body = {"clientId": self.client_id, "grantType": "password", "tenantId": tenant_id,
                "username": username, "password": password}
        result = self.post("/auth/login", body)
        self.token = result["data"]["access_token"]
        return result["data"]

    def get(self, path: str, params: dict | None = None, expect: int | None = 200) -> dict:
        return self.request("GET", path, params=params, expect=expect)

    def post(self, path: str, body: object = None, expect: int | None = 200) -> dict:
        return self.request("POST", path, body=body, expect=expect)

    def put(self, path: str, body: object = None, expect: int | None = 200) -> dict:
        return self.request("PUT", path, body=body, expect=expect)

    def delete(self, path: str, expect: int | None = 200) -> dict:
        return self.request("DELETE", path, expect=expect)

    def request(self, method: str, path: str, body: object = None, params: dict | None = None,
                expect: int | None = 200) -> dict:
        """Send one request; `expect` is the RuoYi `code` field to assert (None = no check).

        RuoYi returns HTTP 200 with a JSON envelope {code, msg, data}; auth failures use code 401,
        missing permissions code 403, business failures code 500.
        """
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = None
        headers = {"Accept": "application/json", "clientid": self.client_id}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read()
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            payload = {"raw": raw[:500].decode("utf-8", "replace")}
        if status != 200:
            raise ApiError(status, payload, path)
        if expect is not None and payload.get("code") != expect:
            raise ApiError(status, payload, path)
        return payload
