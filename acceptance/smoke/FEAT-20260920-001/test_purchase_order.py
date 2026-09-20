"""FEAT-20260920-001 采购单管理（主子表）：后端接口验收冒烟（独立外部验收）。

接口前缀按 AGENT_GUIDE 约定从『业务管理/采购单管理』菜单的权限串推导为 /biz/<feature>；
字段名与提交路由都不绑定实现：先用常见命名的候选别名新增一张探针单据，再按回读的值识别主表与
明细的 JSON 键，并在候选路由里识别提交接口。菜单、接口、字段或行为缺失时用例失败。
"""

from __future__ import annotations

import datetime as dt
import decimal
import io
import json
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

from ruoyi_client import ApiError, Client

DIR_NAME = "业务管理"
MENU_NAME = "采购单管理"
SUPPLIER_MENU_NAME = "供应商管理"
OTHER_DEPT_ID = "1761000000000000105"  # 测试部门；admin 属于研发部门（...103）
BIG_PAGE = 200
MISSING_ID = 9223372036854775000
REPEAT_WINDOW = 6  # @RepeatSubmit 默认 5 秒内拒绝完全相同的写请求
STANDARD_ACTIONS = {"list", "query", "add", "edit", "remove", "export", "import"}
BASE_ID_KEYS = {"createDept", "createBy", "updateBy", "tenantId", "deptId", "userId", "supplierId"}
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

MAIN_ALIASES = {
    "orderNo": ("orderNo", "orderCode", "purchaseNo", "purchaseOrderNo", "poNo", "billNo", "orderNumber"),
    "supplierId": ("supplierId",),
    "supplierName": ("supplierName",),
    "orderDate": ("orderDate", "purchaseDate", "billDate", "orderTime", "orderDay"),
    "status": ("status", "orderStatus", "billStatus"),
    "remark": ("remark",),
    "totalAmount": ("totalAmount", "totalMoney", "totalPrice", "sumAmount", "amountTotal", "amount"),
}
DETAIL_LIST_KEYS = ("details", "detailList", "orderDetails", "orderDetailList", "purchaseOrderDetails",
                    "purchaseOrderDetailList", "items", "itemList", "orderItems", "detailBoList",
                    "detailVoList", "lines", "lineList", "subList", "children")
DETAIL_ALIASES = {
    "materialName": ("materialName", "materialsName", "itemName", "goodsName", "productName", "material", "name"),
    "quantity": ("quantity", "qty", "num", "number", "count"),
    "price": ("price", "unitPrice", "itemPrice"),
    "amount": ("amount", "itemAmount", "lineAmount", "detailAmount", "money", "subtotal", "totalAmount"),
}
SUBMIT_ROUTES = (
    ("PUT", "{base}/submit/{id}", "path"),
    ("POST", "{base}/submit/{id}", "path"),
    ("PUT", "{base}/{id}/submit", "path"),
    ("POST", "{base}/{id}/submit", "path"),
    ("PUT", "{base}/submit", "params"),
    ("POST", "{base}/submit", "params"),
    ("PUT", "{base}/submit", "body"),
    ("POST", "{base}/submit", "body"),
)


def tok(size: int = 10) -> str:
    return uuid.uuid4().hex[:size]


def call(fn, *args, **kwargs):
    """Run a Client call without asserting the RuoYi code; return (code, msg, payload)."""
    try:
        payload = fn(*args, expect=None, **kwargs)
    except ApiError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        return body.get("code", exc.status), str(body.get("msg") or ""), body
    return payload.get("code"), str(payload.get("msg") or ""), payload


def page_of(payload: dict) -> dict:
    data = payload.get("data")
    page = data if isinstance(data, dict) and "rows" in data else payload
    if "rows" not in page or "total" not in page:
        raise AssertionError(f"分页结果缺少 rows/total: {str(payload)[:300]}")
    return page


def num(value):
    """Numeric value of a JSON field (BigDecimal 会被序列化成字符串)，无法解析时返回 None。"""
    if value is None or isinstance(value, (bool, dict, list)):
        return None
    try:
        return decimal.Decimal(str(value))
    except (ArithmeticError, ValueError):
        return None


def same(value, expected) -> bool:
    got = num(value)
    return got is not None and got == decimal.Decimal(str(expected))


def as_date(value):
    """yyyy-MM-dd of a date field, whether it comes back as text or as epoch millis."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < 10 ** 11:
            return None
        moment = dt.datetime.fromtimestamp(value / 1000, dt.timezone(dt.timedelta(hours=8)))
        return moment.date().isoformat()
    text = str(value or "")
    head = text[:10]
    try:
        dt.date.fromisoformat(head)
    except ValueError:
        return None
    return head


def day(offset: int = 0) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


def excel_rows(content: bytes) -> int:
    """Row count of the first worksheet; raises when the bytes are not a workbook."""
    if not content.startswith(b"PK"):
        raise AssertionError(f"不是 Excel 文件: {content[:200]!r}")
    with zipfile.ZipFile(io.BytesIO(content)) as book:
        sheets = sorted(n for n in book.namelist()
                        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        if not sheets:
            raise AssertionError("Excel 文件中没有工作表")
        root = ET.fromstring(book.read(sheets[0]))
    return len(list(root.iter(XLSX_NS + "row")))


class Suppliers:
    """已交付的供应商档案接口：用来准备启用/停用状态的供应商。"""

    NAME_ALIASES = ("supplierName", "name")
    CODE_ALIASES = ("supplierCode", "code", "supplierNo")

    def __init__(self, admin: Client, base: str):
        self.admin, self.base = admin, base
        self.name_key = None
        self.id_key = None

    def create(self, status: str = "0", label: str = "") -> dict:
        t = tok()
        name = f"采购冒烟供应商{label}{t}"
        body = {"status": status}
        for alias in self.CODE_ALIASES:
            body[alias] = "PS" + t
        for alias in self.NAME_ALIASES:
            body[alias] = name
        code, msg, _ = call(self.admin.post, self.base, body)
        if code != 200:
            raise AssertionError(f"准备供应商失败（POST {self.base}）: {code} {msg}")
        row = self.find(name)
        if self.name_key is None:
            self.name_key = next((k for k, v in row.items() if str(v) == name), None)
            self.id_key = (next((k for k in ("supplierId", "id") if row.get(k) not in (None, "")), None)
                           or next((k for k in row if k.endswith("Id") and row.get(k) not in (None, "")), None))
        if not self.name_key or not self.id_key:
            raise AssertionError(f"供应商记录缺少名称或主键字段: {row}")
        return {"id": row[self.id_key], "name": name, "row": row}

    def find(self, name: str) -> dict:
        params = {"pageNum": 1, "pageSize": BIG_PAGE}
        for alias in self.NAME_ALIASES:
            params[alias] = name
        page = page_of(self.admin.get(self.base + "/list", params))
        matches = [r for r in (page["rows"] or []) if any(str(v) == name for v in r.values())]
        if len(matches) != 1:
            raise AssertionError(f"按名称 {name} 查到 {len(matches)} 条供应商")
        return matches[0]

    def disable(self, supplier: dict) -> None:
        body = dict(supplier["row"])
        body["status"] = "1"
        code, msg, _ = call(self.admin.put, self.base, body)
        if code != 200:
            raise AssertionError(f"停用供应商失败: {code} {msg}")
        row = self.find(supplier["name"])
        if str(row.get("status")) != "1":
            raise AssertionError(f"供应商没有变成停用状态: {row}")
        supplier["row"] = row


class Orders:
    """Discovered purchase-order API: base path, JSON keys, submit route, helper clients."""

    def __init__(self):
        self.admin = Client()
        self.admin.login()
        menus = self.admin.get("/system/menu/list")["data"] or []
        tops = [m for m in menus if m.get("menuName") == DIR_NAME and str(m.get("parentId")) == "0"]
        if not tops:
            raise AssertionError("菜单中没有顶级目录『业务管理』")
        self.top_menu = tops[0]
        pages = [m for m in menus if m.get("menuName") == MENU_NAME
                 and str(m.get("parentId")) == str(self.top_menu["menuId"])]
        if not pages:
            raise AssertionError("『业务管理』下没有『采购单管理』菜单")
        self.page_menu = pages[0]
        self.buttons = [m for m in menus if str(m.get("parentId")) == str(self.page_menu["menuId"])]
        self.feature = self._feature([self.page_menu] + self.buttons)
        if not self.feature:
            raise AssertionError("采购单管理菜单及按钮没有 biz:<feature>:* 权限串")
        self.base = "/biz/" + self.feature
        self.actions = {str(m.get("perms") or "").split(":")[-1] for m in self.buttons
                        if str(m.get("perms") or "").count(":") == 2}
        self.submit_action = next((a for a in sorted(self.actions) if a not in STANDARD_ACTIONS), None)
        supplier_pages = [m for m in menus if m.get("menuName") == SUPPLIER_MENU_NAME]
        supplier_feature = None
        if supplier_pages:
            children = [m for m in menus if str(m.get("parentId")) == str(supplier_pages[0]["menuId"])]
            supplier_feature = self._feature([supplier_pages[0]] + children)
        self.suppliers = Suppliers(self.admin, "/biz/" + (supplier_feature or "supplier"))
        self.keys: dict = {}
        self.detail_keys: dict = {}
        self.detail_list_key = None
        self.id_key = None
        self.submit_route = None
        self.date_suffix = ""
        self.draft = None
        self.submitted = None
        self.status_labels: dict = {}
        self._probe()

    @staticmethod
    def _feature(menus) -> str | None:
        for menu in menus:
            parts = str(menu.get("perms") or "").split(":")
            if len(parts) == 3 and parts[0] == "biz" and parts[1]:
                return parts[1]
        return None

    # ---- 请求封装 ---------------------------------------------------------

    def date_value(self, value: str) -> str:
        return value + self.date_suffix

    def _detail_body(self, detail: dict) -> dict:
        item = {}
        for logical, value in detail.items():
            if value is None:
                continue
            if self.detail_keys:
                item[self.detail_keys[logical]] = value
            else:
                for alias in DETAIL_ALIASES[logical]:
                    item[alias] = value
        return item

    def body(self, supplier=None, order_date=None, details=None, remark=None,
             order_no=None, total_amount=None, order_id=None) -> dict:
        out: dict = {}

        def put(logical, value):
            if value is None:
                return
            if self.keys:
                out[self.keys[logical]] = value
            else:
                for alias in MAIN_ALIASES[logical]:
                    out[alias] = value

        if supplier is not None:
            put("supplierId", supplier["id"])
            put("supplierName", supplier["name"])
        if order_date is not None:
            put("orderDate", self.date_value(order_date))
        put("remark", remark)
        put("orderNo", order_no)
        put("totalAmount", total_amount)
        if order_id is not None:
            out[self.id_key or "id"] = order_id
        if details is not None:
            items = [self._detail_body(d) for d in details]
            if self.detail_list_key:
                out[self.detail_list_key] = items
            else:
                for key in DETAIL_LIST_KEYS:
                    out[key] = items
        return out

    def add(self, client=None, **fields):
        return call((client or self.admin).post, self.base, self.body(**fields))

    def edit(self, client=None, **fields):
        return call((client or self.admin).put, self.base, self.body(**fields))

    def remove(self, ids, client=None):
        joined = ",".join(str(i) for i in ids)
        return call((client or self.admin).delete, f"{self.base}/{joined}")

    def detail(self, order_id, client=None):
        return call((client or self.admin).get, f"{self.base}/{order_id}")

    def detail_of(self, order_id, client=None):
        code, msg, payload = self.detail(order_id, client)
        if code != 200:
            raise AssertionError(f"查询采购单 {order_id} 详情失败: {code} {msg}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise AssertionError(f"采购单详情没有返回主表数据: {str(payload)[:300]}")
        items = data.get(self.detail_list_key)
        if not isinstance(items, list):
            raise AssertionError(f"采购单详情没有返回明细 {self.detail_list_key}: {list(data)}")
        return data, items

    def _submit_with(self, route, order_id, client=None):
        method, template, style = route
        client = client or self.admin
        path = template.format(base=self.base, id=order_id)
        key = self.id_key or "id"
        payload = {key: order_id, "id": order_id}
        if style == "params":
            return call(client.request, method, path, params=payload)
        if style == "body":
            return call(client.request, method, path, payload)
        return call(client.request, method, path)

    def submit(self, order_id, client=None):
        if self.submit_route is None:
            raise AssertionError("没有可用的采购单提交接口")
        return self._submit_with(self.submit_route, order_id, client)

    def query(self, client=None, page=1, size=BIG_PAGE, order_no=None, supplier=None,
              status=None, begin=None, end=None) -> dict:
        params = {"pageNum": page, "pageSize": size}
        if order_no is not None:
            params[self.keys["orderNo"]] = order_no
        if status is not None:
            params[self.keys["status"]] = status
        if supplier is not None:
            params[self.keys["supplierId"]] = supplier["id"]
            params[self.keys["supplierName"]] = supplier["name"]
        if begin is not None or end is not None:
            key = self.keys["orderDate"]
            cap = key[0].upper() + key[1:]
            if begin is not None:
                params["params[begin" + cap + "]"] = self.date_value(begin)
                params["begin" + cap] = self.date_value(begin)
            if end is not None:
                params["params[end" + cap + "]"] = self.date_value(end)
                params["end" + cap] = self.date_value(end)
        return page_of((client or self.admin).get(self.base + "/list", params))

    def all_rows(self, client=None, **filters):
        collected, total = [], 0
        for page_num in range(1, 11):
            result = self.query(client=client, page=page_num, **filters)
            rows = list(result["rows"] or [])
            total = int(result["total"])
            collected += rows
            if not rows or len(collected) >= total:
                break
        return collected, total

    def export(self, client=None, status=None):
        """POST the export form like the frontend does; return (content type, raw bytes)."""
        client = client or self.admin
        fields = {}
        if status is not None:
            fields[self.keys["status"]] = status
        data = urllib.parse.urlencode(fields).encode("utf-8")
        headers = {"clientid": client.client_id, "Authorization": "Bearer " + (client.token or ""),
                   "Content-Type": "application/x-www-form-urlencoded"}
        request = urllib.request.Request(client.base_url + self.base + "/export", data=data,
                                         headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.headers.get("Content-Type", ""), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.headers.get("Content-Type", ""), exc.read()

    # ---- 数据查找 ---------------------------------------------------------

    def value(self, row: dict, logical: str):
        return row.get(self.keys[logical])

    def find(self, remark: str) -> dict:
        rows, _ = self.all_rows()
        matches = [r for r in rows if str(r.get(self.keys["remark"]) or "") == remark]
        if len(matches) != 1:
            raise AssertionError(f"按备注 {remark} 查到 {len(matches)} 张采购单")
        return matches[0]

    def exists(self, remark: str) -> bool:
        rows, _ = self.all_rows()
        return any(str(r.get(self.keys["remark"]) or "") == remark for r in rows)

    # ---- 探针 -------------------------------------------------------------

    def _probe(self) -> None:
        supplier = self.suppliers.create(label="探针")
        marker = tok()
        remark = "探针备注" + marker
        date = day()
        details = [{"materialName": "探针物料甲" + marker, "quantity": 2, "price": 10, "amount": 999},
                   {"materialName": "探针物料乙" + marker, "quantity": 3, "price": 5, "amount": 888}]
        code, msg, _ = self.add(supplier=supplier, order_date=date, details=details, remark=remark)
        if code != 200:
            self.date_suffix = " 00:00:00"  # 下单日期可能按 yyyy-MM-dd HH:mm:ss 反序列化
            retry_code, retry_msg, _ = self.add(supplier=supplier, order_date=date,
                                                details=details, remark=remark)
            if retry_code != 200:
                self.date_suffix = ""
                raise AssertionError(f"新增采购单接口 POST {self.base} 失败: {code} {msg}")
        rows, _ = self.all_rows()
        matches = [r for r in rows if any(str(v) == remark for v in r.values())]
        if len(matches) != 1:
            raise AssertionError(f"新增后列表里没有唯一的探针采购单（{len(matches)} 条）")
        row = matches[0]
        keys: dict = {}
        taken: set = set()

        def pick(logical, pred=None, names_first=False, skip=()):
            by_name = [k for k in MAIN_ALIASES[logical] if k in row and k not in taken]
            key = by_name[0] if (names_first and by_name) else None
            if key is None and pred is not None:
                key = next((k for k, v in row.items()
                            if k not in taken and k not in skip and pred(v)), None)
            if key is None and by_name:
                key = by_name[0]
            if key:
                taken.add(key)
            keys[logical] = key

        pick("remark", lambda v: str(v) == remark)
        pick("supplierName", lambda v: str(v) == supplier["name"])
        pick("supplierId", lambda v: str(v) == str(supplier["id"]))
        pick("totalAmount", lambda v: same(v, 35))
        pick("status", names_first=True)
        if not keys["status"]:
            fallback = next((k for k in row if "status" in k.lower() and k not in taken), None)
            keys["status"] = fallback
            if fallback:
                taken.add(fallback)
        pick("orderDate", lambda v: as_date(v) == date, names_first=True,
             skip=("createTime", "updateTime"))
        pick("orderNo", lambda v: isinstance(v, str) and v.startswith("PO"))
        missing = [logical for logical, key in keys.items() if not key]
        if missing:
            raise AssertionError(f"采购单列表记录缺少字段 {missing}: {row}")
        shown = row[keys["orderDate"]]
        if as_date(shown) != date:
            raise AssertionError(f"列表返回的下单日期 {shown} 与提交的 {date} 不一致")
        candidates = [self.feature + "Id", "orderId", "purchaseOrderId", "id"]
        candidates += [k for k in row if k.endswith("Id") and k not in BASE_ID_KEYS]
        self.id_key = next((k for k in candidates if row.get(k) not in (None, "")), None)
        if not self.id_key:
            raise AssertionError(f"采购单列表记录没有主键字段: {row}")
        self.keys = keys
        order_id = row[self.id_key]

        code, msg, payload = self.detail(order_id)
        if code != 200 or not isinstance(payload.get("data"), dict):
            raise AssertionError(f"采购单详情接口 GET {self.base}/<id> 失败: {code} {msg}")
        data = payload["data"]
        names = {d["materialName"] for d in details}
        list_key = None
        for key, value in data.items():
            if (isinstance(value, list) and len(value) == 2
                    and all(isinstance(i, dict) for i in value)
                    and any(str(v) in names for item in value for v in item.values())):
                list_key = key
                break
        if list_key is None:
            raise AssertionError(f"采购单详情里没有带两条明细的子表字段: {list(data)}")
        self.detail_list_key = list_key
        items = list(data[list_key])
        if not any(str(v) == details[0]["materialName"] for v in items[0].values()):
            items.reverse()
        first, second = items[0], items[1]
        dkeys: dict = {}
        dkeys["materialName"] = next((k for k, v in first.items()
                                      if str(v) == details[0]["materialName"]), None)
        used = {dkeys["materialName"]}

        def pair(logical, left, right):
            key = next((k for k in first
                        if k not in used and same(first.get(k), left) and same(second.get(k), right)), None)
            if key is None:
                key = next((k for k in DETAIL_ALIASES[logical] if k in first and k not in used), None)
            if key:
                used.add(key)
            dkeys[logical] = key

        pair("quantity", 2, 3)
        pair("price", 10, 5)
        pair("amount", 20, 15)
        missing = [logical for logical, key in dkeys.items() if not key]
        if missing:
            raise AssertionError(f"采购单明细缺少字段 {missing}: {first}")
        self.detail_keys = dkeys
        self.draft = str(row[keys["status"]])
        self._discover_submit(order_id)
        data, _ = self.detail_of(order_id)
        after = str(data.get(keys["status"]))
        if after == self.draft:
            raise AssertionError(f"提交后状态没有变化（{self.draft} -> {after}）")
        self.submitted = after
        self.status_labels = self._status_labels()

    def _discover_submit(self, order_id) -> None:
        tried = []
        for route in SUBMIT_ROUTES:
            code, msg, _ = self._submit_with(route, order_id)
            tried.append(f"{route[0]} {route[1]} -> {code} {msg}".strip())
            if code == 200:
                self.submit_route = route
                return
        raise AssertionError("没有找到采购单提交接口: " + "; ".join(tried))

    def _status_labels(self) -> dict:
        """字典里 草稿/已提交 的取值，用于校验状态码值的业务含义；查不到时返回空表。"""
        try:
            page = page_of(self.admin.get("/system/dict/data/list", {"pageNum": 1, "pageSize": 500}))
        except (ApiError, AssertionError, KeyError):
            return {}
        labels = {}
        for item in page["rows"] or []:
            label = str(item.get("dictLabel") or "")
            if label in ("草稿", "已提交"):
                labels.setdefault(str(item.get("dictValue")), label)
        return labels

    # ---- 受限用户 ---------------------------------------------------------

    def user(self, allow: set, tag: str) -> Client:
        """另一个部门里只被授予 `allow` 这些按钮权限的登录用户。"""
        t = tok(8)
        role_key = f"po_{tag}_{t}"
        menu_ids = [self.top_menu["menuId"], self.page_menu["menuId"]]
        menu_ids += [b["menuId"] for b in self.buttons
                     if str(b.get("perms") or "").split(":")[-1] in allow]
        self.admin.post("/system/role", {
            "roleName": "采购单" + tag + t, "roleKey": role_key, "roleSort": 99, "status": "0",
            "dataScope": "3", "menuCheckStrictly": True, "deptCheckStrictly": True, "menuIds": menu_ids})
        rows = page_of(self.admin.get("/system/role/list",
                                      {"roleKey": role_key, "pageNum": 1, "pageSize": 10}))["rows"]
        role_id = next((r["roleId"] for r in rows if r.get("roleKey") == role_key), None)
        if role_id is None:
            raise AssertionError(f"创建的测试角色 {role_key} 查询不到")
        username, password = "po" + tag[:4] + t, "Smoke#" + t
        self.admin.post("/system/user", {
            "userName": username, "nickName": "采购单" + tag + t, "password": password,
            "deptId": OTHER_DEPT_ID, "roleIds": [role_id], "status": "0"})
        client = Client()
        client.login(username, password)
        return client


_STATE: dict = {}


def orders() -> Orders:
    if "error" in _STATE:
        raise AssertionError(_STATE["error"])
    if "value" not in _STATE:
        try:
            _STATE["value"] = Orders()
        except AssertionError as exc:
            _STATE["error"] = str(exc)
            raise
    return _STATE["value"]


class OrderCase(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.o = orders()

    def supplier(self, status: str = "0") -> dict:
        return self.o.suppliers.create(status=status)

    def assert_code(self, result, expected):
        self.assertEqual(result[0], expected, f"code={result[0]} msg={result[1]}")

    def assert_failed(self, result, keyword=None):
        self.assertNotEqual(result[0], 200, f"期望失败却成功: {str(result[2])[:300]}")
        self.assertTrue(result[1].strip(), f"失败时没有可读提示: {str(result[2])[:300]}")
        if keyword:
            self.assertIn(keyword, result[1])

    def create(self, supplier=None, details=None, order_date=None, **extra) -> dict:
        """新增一张草稿采购单并回读列表记录。"""
        o = self.o
        supplier = supplier or self.supplier()
        marker = tok()
        remark = "冒烟单据" + marker
        details = details or [{"materialName": "物料" + marker, "quantity": 2, "price": 10}]
        result = o.add(supplier=supplier, order_date=order_date or day(), details=details,
                       remark=remark, **extra)
        self.assert_code(result, 200)
        row = o.find(remark)
        return {"row": row, "id": row[o.id_key], "remark": remark,
                "supplier": supplier, "details": details}

    def amounts(self, items) -> dict:
        o = self.o
        return {str(i[o.detail_keys["materialName"]]): num(i[o.detail_keys["amount"]]) for i in items}


class QueryTest(OrderCase):
    def test_A1_filter_by_order_no_fragment(self):
        o = self.o
        wanted = self.create()
        other = self.create()
        number = str(o.value(wanted["row"], "orderNo"))
        fragment = number[2:]
        self.assertGreaterEqual(len(fragment), 8, f"单号 {number} 不像 PO+日期+流水号")
        page = o.query(order_no=fragment)
        rows = list(page["rows"] or [])
        self.assertEqual(int(page["total"]), 1, rows)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual(str(o.value(rows[0], "orderNo")), number)
        self.assertNotEqual(number, str(o.value(other["row"], "orderNo")))

    def test_A2_filter_by_order_date_range(self):
        o = self.o
        supplier = self.supplier()
        inside = self.create(supplier=supplier, order_date=day())
        outside = self.create(supplier=supplier, order_date=day(-10))
        begin, end = day(-3), day()
        rows, _ = o.all_rows(supplier=supplier, begin=begin, end=end)
        ids = {str(r.get(o.id_key)) for r in rows}
        self.assertIn(str(inside["id"]), ids, "范围内（边界当天）的单据没有返回")
        self.assertNotIn(str(outside["id"]), ids, "范围外的单据也被返回了")
        for row in rows:
            got = as_date(o.value(row, "orderDate"))
            self.assertIsNotNone(got, row)
            self.assertTrue(begin <= got <= end, f"超出查询范围的下单日期 {got}")

    def test_A3_filter_by_draft_status(self):
        o = self.o
        supplier = self.supplier()
        draft = self.create(supplier=supplier)
        submitted = self.create(supplier=supplier)
        self.assert_code(o.submit(submitted["id"]), 200)
        rows, _ = o.all_rows(supplier=supplier, status=o.draft)
        ids = {str(r.get(o.id_key)) for r in rows}
        self.assertIn(str(draft["id"]), ids, rows)
        self.assertNotIn(str(submitted["id"]), ids, rows)
        for row in rows:
            self.assertEqual(str(o.value(row, "status")), o.draft, row)


class CreateTest(OrderCase):
    def test_A5_create_master_with_two_details(self):
        o = self.o
        marker = tok()
        details = [{"materialName": "螺栓" + marker, "quantity": 2, "price": 10},
                   {"materialName": "螺母" + marker, "quantity": 3, "price": 5}]
        order = self.create(details=details)
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 2, items)
        self.assertEqual({str(i[o.detail_keys["materialName"]]) for i in items},
                         {d["materialName"] for d in details})
        self.assertEqual(str(data.get(o.keys["status"])), o.draft)
        if o.status_labels:
            self.assertEqual(o.status_labels.get(o.draft), "草稿")

    def test_A6_amounts_are_recalculated(self):
        o = self.o
        marker = tok()
        details = [{"materialName": "甲" + marker, "quantity": 2, "price": 10, "amount": 999},
                   {"materialName": "乙" + marker, "quantity": 3, "price": 5, "amount": 888}]
        order = self.create(details=details, total_amount=12345)
        data, items = o.detail_of(order["id"])
        self.assertEqual(self.amounts(items),
                         {details[0]["materialName"]: decimal.Decimal("20"),
                          details[1]["materialName"]: decimal.Decimal("15")})
        total = data.get(o.keys["totalAmount"])
        self.assertTrue(same(total, 35), f"合计金额应为 35，实际 {total}")

    def test_A7_disabled_supplier_rejected(self):
        o = self.o
        supplier = self.supplier(status="1")
        marker = tok()
        remark = "停用供应商" + marker
        result = o.add(supplier=supplier, order_date=day(), remark=remark,
                       details=[{"materialName": "物料" + marker, "quantity": 1, "price": 1}])
        self.assert_failed(result, "供应商")
        self.assertFalse(o.exists(remark), "停用供应商的采购单不应落库")

    def test_A8_details_required(self):
        o = self.o
        marker = tok()
        remark = "无明细" + marker
        result = o.add(supplier=self.supplier(), order_date=day(), remark=remark, details=[])
        self.assert_failed(result, "明细")
        self.assertFalse(o.exists(remark), "没有明细的采购单不应落库")

    def test_A32_order_no_is_generated_and_request_value_ignored(self):
        o = self.o
        marker = tok()
        remark = "自带单号" + marker
        custom = "MANUAL-" + marker
        date = day()
        result = o.add(supplier=self.supplier(), order_date=date, remark=remark, order_no=custom,
                       details=[{"materialName": "物料" + marker, "quantity": 1, "price": 7}])
        self.assert_code(result, 200)
        row = o.find(remark)
        number = str(o.value(row, "orderNo"))
        self.assertNotEqual(number, custom)
        self.assertNotIn(marker, number)
        self.assertRegex(number, "^PO" + date.replace("-", "") + "[-_]?[0-9]+$")
        data, _ = o.detail_of(row[o.id_key])
        self.assertEqual(str(data.get(o.keys["orderNo"])), number)

    def test_A33_invalid_quantity_or_price_rejected(self):
        o = self.o
        supplier = self.supplier()
        cases = [({"quantity": 0, "price": 10}, "数量"),
                 ({"quantity": 1.5, "price": 10}, None),
                 ({"quantity": 1, "price": 0}, "单价")]
        for changes, keyword in cases:
            with self.subTest(detail=changes):
                marker = tok()
                remark = "非法明细" + marker
                detail = {"materialName": "物料" + marker}
                detail.update(changes)
                result = o.add(supplier=supplier, order_date=day(), remark=remark, details=[detail])
                self.assert_failed(result, keyword)
                self.assertFalse(o.exists(remark), f"校验应失败却落库: {changes}")


class DetailTest(OrderCase):
    def test_A15_detail_returns_master_and_all_details(self):
        o = self.o
        marker = tok()
        details = [{"materialName": "甲" + marker, "quantity": 1, "price": 10},
                   {"materialName": "乙" + marker, "quantity": 2, "price": 20},
                   {"materialName": "丙" + marker, "quantity": 3, "price": 5}]
        order = self.create(details=details)
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 3, items)
        self.assertEqual(self.amounts(items),
                         {details[0]["materialName"]: decimal.Decimal("10"),
                          details[1]["materialName"]: decimal.Decimal("40"),
                          details[2]["materialName"]: decimal.Decimal("15")})
        self.assertTrue(str(data.get(o.keys["orderNo"]) or "").strip(), data)
        self.assertEqual(str(data.get(o.keys["supplierName"])), order["supplier"]["name"])
        self.assertEqual(str(data.get(o.keys["status"])), o.draft)
        self.assertEqual(str(data.get(o.keys["remark"])), order["remark"])
        self.assertTrue(same(data.get(o.keys["totalAmount"]), 65),
                        f"合计金额应为 65，实际 {data.get(o.keys['totalAmount'])}")

    def test_A16_missing_order_detail_fails(self):
        result = self.o.detail(MISSING_ID)
        self.assert_failed(result)
        self.assertFalse(result[2].get("data"), "不存在的单据不应返回空壳数据")


class UpdateTest(OrderCase):
    def test_A11_edit_details_and_recalculate(self):
        o = self.o
        marker = tok()
        keep = {"materialName": "保留" + marker, "quantity": 2, "price": 20}
        drop = {"materialName": "删除" + marker, "quantity": 1, "price": 10}
        order = self.create(details=[keep, drop])
        changed = dict(keep)
        changed["quantity"] = 3
        added = {"materialName": "新增" + marker, "quantity": 4, "price": 2.5}
        result = o.edit(order_id=order["id"], supplier=order["supplier"], order_date=day(),
                        remark=order["remark"], details=[changed, added])
        self.assert_code(result, 200)
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 2, items)
        self.assertEqual(self.amounts(items),
                         {changed["materialName"]: decimal.Decimal("60"),
                          added["materialName"]: decimal.Decimal("10")})
        self.assertTrue(same(data.get(o.keys["totalAmount"]), 70),
                        f"合计金额应为 70，实际 {data.get(o.keys['totalAmount'])}")

    def test_A12_submitted_order_cannot_be_edited(self):
        o = self.o
        marker = tok()
        detail = {"materialName": "原始" + marker, "quantity": 2, "price": 10}
        order = self.create(details=[detail])
        self.assert_code(o.submit(order["id"]), 200)
        result = o.edit(order_id=order["id"], supplier=order["supplier"], order_date=day(),
                        remark="已改" + marker,
                        details=[{"materialName": "改后" + marker, "quantity": 9, "price": 9}])
        self.assert_failed(result, "提交")
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 1, items)
        self.assertEqual(str(items[0][o.detail_keys["materialName"]]), detail["materialName"])
        self.assertEqual(str(data.get(o.keys["remark"])), order["remark"])
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)

    def test_A34_edit_requires_enabled_supplier(self):
        o = self.o
        supplier = self.supplier()
        marker = tok()
        detail = {"materialName": "原始" + marker, "quantity": 2, "price": 10}
        order = self.create(supplier=supplier, details=[detail])
        o.suppliers.disable(supplier)
        result = o.edit(order_id=order["id"], supplier=supplier, order_date=day(),
                        remark=order["remark"],
                        details=[{"materialName": "改后" + marker, "quantity": 5, "price": 10}])
        self.assert_failed(result, "供应商")
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 1, items)
        self.assertEqual(str(items[0][o.detail_keys["materialName"]]), detail["materialName"])
        self.assertTrue(same(data.get(o.keys["totalAmount"]), 20), data.get(o.keys["totalAmount"]))
        self.assertEqual(str(data.get(o.keys["status"])), o.draft)


class DeleteTest(OrderCase):
    def test_A17_delete_draft_order(self):
        o = self.o
        marker = tok()
        order = self.create(details=[{"materialName": "待删" + marker, "quantity": 1, "price": 3}])
        self.assert_code(o.remove([order["id"]]), 200)
        self.assertFalse(o.exists(order["remark"]), "删除后列表里仍能查到")
        code, _, payload = o.detail(order["id"])
        self.assertTrue(code != 200 or not payload.get("data"), payload)

    def test_A18_submitted_order_cannot_be_deleted(self):
        o = self.o
        order = self.create()
        self.assert_code(o.submit(order["id"]), 200)
        self.assert_failed(o.remove([order["id"]]), "提交")
        self.assertTrue(o.exists(order["remark"]), "删除失败后单据应仍然存在")
        data, items = o.detail_of(order["id"])
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)
        self.assertEqual(len(items), len(order["details"]))


class SubmitTest(OrderCase):
    def test_A20_submit_draft_order(self):
        o = self.o
        order = self.create()
        self.assert_code(o.submit(order["id"]), 200)
        data, _ = o.detail_of(order["id"])
        self.assertNotEqual(o.submitted, o.draft)
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)
        if o.status_labels:
            self.assertEqual(o.status_labels.get(o.submitted), "已提交")

    def test_A21_submit_twice_rejected(self):
        o = self.o
        order = self.create()
        self.assert_code(o.submit(order["id"]), 200)
        time.sleep(REPEAT_WINDOW)  # 避开防重复提交窗口，确保拿到的是业务校验结果
        result = o.submit(order["id"])
        self.assert_failed(result)
        self.assertNotIn("重复提交", result[1], "第二次提交被防重复提交拦截，没有验证到状态校验")
        data, _ = o.detail_of(order["id"])
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)

    def test_A22_submitted_order_is_frozen(self):
        o = self.o
        marker = tok()
        detail = {"materialName": "冻结" + marker, "quantity": 2, "price": 10}
        order = self.create(details=[detail])
        self.assert_code(o.submit(order["id"]), 200)
        self.assert_failed(o.edit(order_id=order["id"], supplier=order["supplier"], order_date=day(),
                                  remark=order["remark"],
                                  details=[{"materialName": "改后" + marker, "quantity": 1, "price": 1}]),
                           "提交")
        self.assert_failed(o.remove([order["id"]]), "提交")
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 1, items)
        self.assertEqual(str(items[0][o.detail_keys["materialName"]]), detail["materialName"])
        self.assertTrue(same(data.get(o.keys["totalAmount"]), 20), data.get(o.keys["totalAmount"]))
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)

    def test_A24_submit_requires_its_own_permission(self):
        o = self.o
        self.assertTrue(o.submit_action,
                        f"采购单没有独立的提交按钮权限（现有按钮：{sorted(o.actions)}）")
        user = o.user(o.actions - {o.submit_action}, "nosubmit")
        order = self.create()
        self.assert_code(o.submit(order["id"], client=user), 403)
        data, _ = o.detail_of(order["id"])
        self.assertEqual(str(data.get(o.keys["status"])), o.draft)

    def test_A35_disabled_supplier_does_not_block_detail_or_submit(self):
        o = self.o
        supplier = self.supplier()
        marker = tok()
        details = [{"materialName": "甲" + marker, "quantity": 2, "price": 10},
                   {"materialName": "乙" + marker, "quantity": 1, "price": 5}]
        order = self.create(supplier=supplier, details=details)
        o.suppliers.disable(supplier)
        data, items = o.detail_of(order["id"])
        self.assertEqual(len(items), 2, items)
        self.assertEqual(str(data.get(o.keys["supplierName"])), supplier["name"])
        self.assertTrue(str(data.get(o.keys["orderNo"]) or "").strip(), data)
        self.assertTrue(same(data.get(o.keys["totalAmount"]), 25), data.get(o.keys["totalAmount"]))
        self.assert_code(o.submit(order["id"]), 200)
        data, _ = o.detail_of(order["id"])
        self.assertEqual(str(data.get(o.keys["status"])), o.submitted)


class ExportTest(OrderCase):
    def test_A25_export_returns_excel(self):
        o = self.o
        order = self.create()
        self.assert_code(o.submit(order["id"]), 200)
        self.create()  # 同时存在草稿单据
        ctype, content = o.export(status=o.submitted)
        self.assertTrue(content, "导出内容为空")
        self.assertTrue(content.startswith(b"PK"), f"导出的不是 Excel: {ctype} {content[:200]!r}")
        self.assertGreaterEqual(excel_rows(content), 2, "导出文件没有数据行")

    def test_A26_export_requires_permission(self):
        o = self.o
        user = o.user(o.actions - {"export"}, "noexport")
        ctype, content = o.export(client=user)
        self.assertFalse(content.startswith(b"PK"), "无导出权限却拿到了 Excel")
        self.assertEqual(json.loads(content.decode("utf-8")).get("code"), 403, ctype)


class PermissionTest(OrderCase):
    def test_A29_list_requires_login(self):
        o = self.o
        self.assertEqual(o.admin.get(o.base + "/list", {"pageNum": 1, "pageSize": 1})["code"], 200)
        code, msg, payload = call(Client().get, o.base + "/list", {"pageNum": 1, "pageSize": 10})
        self.assertEqual(code, 401, msg)
        self.assertFalse(payload.get("data"), payload)

    def test_A30_query_only_user_cannot_write(self):
        o = self.o
        user = o.user({"list", "query"}, "readonly")
        order = self.create()
        rows, _ = o.all_rows(client=user, supplier=order["supplier"])
        self.assertIn(str(order["id"]), {str(r.get(o.id_key)) for r in rows},
                      "有查询权限的用户看不到管理员创建的采购单")
        marker = tok()
        self.assert_code(o.add(client=user, supplier=order["supplier"], order_date=day(),
                               remark="越权新增" + marker,
                               details=[{"materialName": "物料" + marker, "quantity": 1, "price": 1}]), 403)
        self.assert_code(o.edit(client=user, order_id=order["id"], supplier=order["supplier"],
                                order_date=day(), remark="越权修改" + marker,
                                details=order["details"]), 403)
        self.assert_code(o.remove([order["id"]], client=user), 403)
        self.assertFalse(o.exists("越权新增" + marker))
        self.assertTrue(o.exists(order["remark"]))


if __name__ == "__main__":
    unittest.main()
