"""FEAT-20260918-001 供应商管理：后端接口验收冒烟（独立外部验收）。

接口前缀按 AGENT_GUIDE 约定从『业务管理/供应商管理』菜单的权限串推导为 /biz/<feature>；
字段名不绑定具体实现：先用常见命名的候选别名新增一条探针记录，再按回读的值识别各字段的 JSON 键。
菜单、接口或字段缺失时用例失败。
"""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

from ruoyi_client import ApiError, Client

DIR_NAME = "业务管理"
MENU_NAME = "供应商管理"
OTHER_DEPT_ID = "1761000000000000105"  # 测试部门；admin 属于研发部门（...103）
BIG_PAGE = 200
DEFAULT_PAGE = 10
FIELDS = ("code", "name", "contact", "phone", "status", "remark")
ALIASES = {
    "code": ("supplierCode", "code", "supplierNo"),
    "name": ("supplierName", "name"),
    "contact": ("contactName", "contactPerson", "contacts", "contact", "linkman", "linkMan", "contactUser"),
    "phone": ("contactPhone", "phone", "telephone", "contactTel", "contactNumber", "tel", "mobile"),
    "status": ("status",),
    "remark": ("remark",),
}
BASE_ID_KEYS = {"createDept", "createBy", "updateBy", "tenantId", "deptId", "userId"}
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADER_LABELS = ("编码", "名称", "联系人", "电话", "状态", "备注")


def tok(size: int = 10) -> str:
    return uuid.uuid4().hex[:size]


def call(fn, *args):
    """Run a Client call without asserting the RuoYi code; return (code, msg, payload)."""
    try:
        payload = fn(*args, expect=None)
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


def col_index(ref: str) -> int:
    number = 0
    for ch in ref:
        if not ch.isalpha():
            break
        number = number * 26 + (ord(ch.upper()) - 64)
    return number - 1


def read_xlsx(content: bytes) -> list[list[str]]:
    """Non-empty rows of the first worksheet as lists of cell texts."""
    if not content.startswith(b"PK"):
        raise AssertionError(f"不是 Excel 文件: {content[:200]!r}")
    with zipfile.ZipFile(io.BytesIO(content)) as book:
        names = book.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            for item in ET.fromstring(book.read("xl/sharedStrings.xml")).iter(XLSX_NS + "si"):
                shared.append("".join(t.text or "" for t in item.iter(XLSX_NS + "t")))
        sheets = sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        if not sheets:
            raise AssertionError("Excel 文件中没有工作表")
        root = ET.fromstring(book.read(sheets[0]))
    rows = []
    for row in root.iter(XLSX_NS + "row"):
        cells = {}
        for cell in row.findall(XLSX_NS + "c"):
            ref = cell.get("r")
            index = col_index(ref) if ref else len(cells)
            kind = cell.get("t")
            value = cell.find(XLSX_NS + "v")
            if kind == "s":
                text = shared[int(value.text)] if value is not None and value.text else ""
            elif kind == "inlineStr":
                text = "".join(t.text or "" for t in cell.iter(XLSX_NS + "t"))
            else:
                text = value.text if value is not None and value.text else ""
            cells[index] = text
        if any(text.strip() for text in cells.values()):
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    if not rows:
        raise AssertionError("Excel 文件为空")
    return rows


class Supplier:
    """Discovered supplier API: base path, JSON keys, admin and list-only clients."""

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
            raise AssertionError("『业务管理』下没有『供应商管理』菜单")
        self.page_menu = pages[0]
        self.buttons = [m for m in menus if str(m.get("parentId")) == str(self.page_menu["menuId"])]
        self.feature = None
        for menu in [self.page_menu] + self.buttons:
            parts = str(menu.get("perms") or "").split(":")
            if len(parts) == 3 and parts[0] == "biz" and parts[1]:
                self.feature = parts[1]
                break
        if not self.feature:
            raise AssertionError("供应商管理菜单及按钮没有 biz:<feature>:* 权限串")
        self.base = "/biz/" + self.feature
        self.keys: dict[str, str] = {}
        self.id_key = None
        self._limited = None
        self._probe()

    def _probe(self):
        t = tok()
        probe = {"code": "P" + t, "name": "探针供应商" + t, "contact": "探针联系人" + t,
                 "phone": "TEL-" + t, "status": "0", "remark": "探针备注" + t}
        code, msg, _ = self.add(**probe)
        if code != 200:
            raise AssertionError(f"新增供应商接口 POST {self.base} 失败: {code} {msg}")
        rows, _ = self.rows(name=probe["name"])
        matches = [r for r in rows if probe["name"] in r.values()]
        if len(matches) != 1:
            raise AssertionError(f"按名称查询不到刚新增的供应商: {rows}")
        row = matches[0]
        keys = {}
        for logical, value in probe.items():
            if logical == "status":
                key = "status" if "status" in row else next((k for k in row if "status" in k.lower()), None)
            else:
                key = next((k for k, v in row.items() if v == value), None)
            if key is None:
                raise AssertionError(f"列表记录缺少字段 {logical}（提交值 {value}）: {row}")
            keys[logical] = key
        candidates = [self.feature + "Id", "id"] + [k for k in row if k.endswith("Id") and k not in BASE_ID_KEYS]
        self.id_key = next((k for k in candidates if row.get(k) not in (None, "")), None)
        if self.id_key is None:
            raise AssertionError(f"列表记录没有主键字段: {row}")
        self.keys = keys

    def body(self, **fields) -> dict:
        out = {}
        for logical, value in fields.items():
            if value is None:
                continue
            if logical == "id":
                out[self.id_key] = value
            elif self.keys:
                out[self.keys[logical]] = value
            else:
                out.update(dict.fromkeys(ALIASES[logical], value))
        return out

    def value(self, row: dict, logical: str):
        return row.get(self.keys[logical])

    def add(self, client=None, **fields):
        return call((client or self.admin).post, self.base, self.body(**fields))

    def update(self, client=None, **fields):
        return call((client or self.admin).put, self.base, self.body(**fields))

    def remove(self, ids, client=None):
        joined = ",".join(str(i) for i in ids)
        return call((client or self.admin).delete, f"{self.base}/{joined}")

    def detail(self, supplier_id, client=None):
        return call((client or self.admin).get, f"{self.base}/{supplier_id}")

    def rows(self, client=None, name=None, status=None, size=BIG_PAGE):
        params = {"pageNum": 1, "pageSize": size}
        params.update(self.body(name=name, status=status))
        page = page_of((client or self.admin).get(self.base + "/list", params))
        return list(page["rows"] or []), int(page["total"])

    def find(self, code, name) -> dict:
        rows, _ = self.rows(name=name)
        matches = [r for r in rows if self.value(r, "code") == code]
        if len(matches) != 1:
            raise AssertionError(f"按名称 {name} 查询到编码 {code} 的记录 {len(matches)} 条: {rows}")
        return matches[0]

    def create(self, **fields) -> dict:
        code, msg, _ = self.add(**fields)
        if code != 200:
            raise AssertionError(f"新增供应商失败: {code} {msg} {fields}")
        return self.find(fields["code"], fields["name"])

    def full(self, row: dict, **changes) -> dict:
        """Edit fields: the row's own values with `changes` applied."""
        fields = {logical: self.value(row, logical) for logical in FIELDS}
        fields.update(changes)
        fields["id"] = row[self.id_key]
        return fields

    def export(self, client=None, **filters):
        """POST the export form like the frontend does; return (content type, raw bytes)."""
        client = client or self.admin
        data = urllib.parse.urlencode(self.body(**filters)).encode("utf-8")
        headers = {"clientid": client.client_id, "Authorization": "Bearer " + client.token,
                   "Content-Type": "application/x-www-form-urlencoded"}
        request = urllib.request.Request(client.base_url + self.base + "/export", data=data,
                                         headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.headers.get("Content-Type", ""), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.headers.get("Content-Type", ""), exc.read()

    def limited(self) -> Client:
        """A logged-in user of another department whose role only has the supplier list permission."""
        if self._limited is None:
            self._limited = self._make_limited_user()
        return self._limited

    def _make_limited_user(self) -> Client:
        t = tok(8)
        role_key = "sup_list_" + t
        menu_ids = [self.top_menu["menuId"], self.page_menu["menuId"]] + [
            b["menuId"] for b in self.buttons if str(b.get("perms") or "").endswith(":list")]
        self.admin.post("/system/role", {
            "roleName": "供应商只读" + t, "roleKey": role_key, "roleSort": 99, "status": "0",
            "dataScope": "3", "menuCheckStrictly": True, "deptCheckStrictly": True, "menuIds": menu_ids})
        roles = page_of(self.admin.get("/system/role/list", {"roleKey": role_key, "pageNum": 1, "pageSize": 10}))["rows"]
        role_id = next((r["roleId"] for r in roles if r.get("roleKey") == role_key), None)
        if role_id is None:
            raise AssertionError(f"创建的测试角色 {role_key} 查询不到")
        username, password = "sup" + t, "Smoke#" + t
        self.admin.post("/system/user", {
            "userName": username, "nickName": "供应商只读" + t, "password": password,
            "deptId": OTHER_DEPT_ID, "roleIds": [role_id], "status": "0"})
        client = Client()
        client.login(username, password)
        return client


_STATE: dict = {}


def supplier() -> Supplier:
    if "error" in _STATE:
        raise AssertionError(_STATE["error"])
    if "value" not in _STATE:
        try:
            _STATE["value"] = Supplier()
        except AssertionError as exc:
            _STATE["error"] = str(exc)
            raise
    return _STATE["value"]


class SupplierCase(unittest.TestCase):
    def setUp(self):
        self.s = supplier()

    def new(self, **fields) -> dict:
        t = tok()
        data = {"code": "S" + t, "name": "供应商" + t, "contact": "联系人" + t[:4],
                "phone": "0755-" + t[:6], "remark": "备注" + t}
        data.update(fields)
        return self.s.create(**data)

    def assert_code(self, result, expected):
        self.assertEqual(result[0], expected, f"code={result[0]} msg={result[1]}")

    def detail_data(self, row: dict) -> dict:
        result = self.s.detail(row[self.s.id_key])
        self.assert_code(result, 200)
        data = result[2].get("data")
        self.assertTrue(data, result[2])
        return data


class MenuTest(SupplierCase):
    def test_A1_business_directory_supplier_menu_and_five_buttons(self):
        s = self.s
        self.assertEqual(s.top_menu.get("menuType"), "M")
        self.assertEqual(s.page_menu.get("menuType"), "C")
        perms = {b.get("perms") for b in s.buttons if b.get("menuType") == "F"}
        for action in ("query", "add", "edit", "remove", "export"):
            self.assertIn(f"biz:{s.feature}:{action}", perms)


class QueryTest(SupplierCase):
    def test_A4_first_page_without_conditions(self):
        s = self.s
        self.new()
        self.new()
        page = page_of(s.admin.get(s.base + "/list", {"pageNum": 1, "pageSize": DEFAULT_PAGE}))
        rows = list(page["rows"] or [])
        self.assertGreaterEqual(int(page["total"]), 2)
        self.assertTrue(rows)
        self.assertLessEqual(len(rows), DEFAULT_PAGE)
        for row in rows:
            for logical in FIELDS:
                self.assertIn(s.keys[logical], row, f"记录缺少 {logical}: {row}")

    def test_A5_filter_by_disabled_status(self):
        s = self.s
        t = tok()
        enabled = self.new(name="状态启用" + t, status="0")
        disabled = self.new(name="状态停用" + t, status="1")
        rows, _ = s.rows(status="1")
        codes = {s.value(r, "code") for r in rows}
        self.assertIn(s.value(disabled, "code"), codes)
        self.assertNotIn(s.value(enabled, "code"), codes)
        self.assertTrue(all(str(s.value(r, "status")) == "1" for r in rows), rows)

    def test_A6_filter_by_full_name(self):
        s = self.s
        t = tok()
        wanted = self.new(name="甲供应商" + t)
        other = self.new(name="乙供应商" + t)
        name = s.value(wanted, "name")
        rows, _ = s.rows(name=name)
        codes = {s.value(r, "code") for r in rows}
        self.assertIn(s.value(wanted, "code"), codes)
        self.assertNotIn(s.value(other, "code"), codes)
        self.assertTrue(all(name in str(s.value(r, "name")) for r in rows), rows)

    def test_A25_filter_by_name_fragment(self):
        s = self.s
        middle = tok()
        wanted = self.new(name="华东" + middle + "精密")
        other = self.new(name="华南" + tok() + "机械")
        rows, _ = s.rows(name=middle)
        codes = {s.value(r, "code") for r in rows}
        self.assertIn(s.value(wanted, "code"), codes)
        self.assertNotIn(s.value(other, "code"), codes)
        self.assertTrue(all(middle in str(s.value(r, "name")) for r in rows), rows)

    def test_A7_list_requires_login(self):
        s = self.s
        self.assertEqual(s.admin.get(s.base + "/list", {"pageNum": 1, "pageSize": 1})["code"], 200)
        code, msg, _ = call(Client().get, s.base + "/list", {"pageNum": 1, "pageSize": DEFAULT_PAGE})
        self.assertEqual(code, 401, msg)


class CreateTest(SupplierCase):
    def test_A9_create_then_query_by_name(self):
        s = self.s
        t = tok()
        data = {"code": "C" + t, "name": "新增供应商" + t, "contact": "王五" + t[:4],
                "phone": "13800138000", "status": "0", "remark": "备注" + t}
        self.assert_code(s.add(**data), 200)
        rows, _ = s.rows(name=data["name"])
        self.assertEqual(len(rows), 1, rows)
        for logical, value in data.items():
            self.assertEqual(str(s.value(rows[0], logical)), value, logical)

    def test_A10_duplicate_code_rejected(self):
        s = self.s
        t = tok()
        code_x = "D" + t
        self.new(code=code_x, name="重复编码甲" + t)
        code, msg, _ = s.add(code=code_x, name="重复编码乙" + t)
        self.assertNotEqual(code, 200, msg)
        self.assertIn("编码", msg)
        rows, _ = s.rows(name=t)
        self.assertEqual(sum(1 for r in rows if s.value(r, "code") == code_x), 1, rows)

    def test_A11_name_required(self):
        code, msg, _ = self.s.add(code="N" + tok(), contact="无名称")
        self.assertNotEqual(code, 200, msg)
        self.assertIn("名称", msg)

    def test_A26_code_required(self):
        s = self.s
        name = "无编码供应商" + tok()
        code, msg, _ = s.add(name=name)
        self.assertNotEqual(code, 200, msg)
        self.assertIn("编码", msg)
        self.assertEqual(s.rows(name=name)[0], [])

    def test_A27_name_not_unique(self):
        s = self.s
        name = "同名供应商" + tok()
        self.new(name=name)
        self.assert_code(s.add(code="E" + tok(), name=name), 200)
        rows, _ = s.rows(name=name)
        self.assertEqual(len([r for r in rows if s.value(r, "name") == name]), 2, rows)

    def test_A28_only_code_and_name_defaults_to_enabled(self):
        s = self.s
        t = tok()
        code_x, name = "M" + t, "最少字段" + t
        self.assert_code(s.add(code=code_x, name=name), 200)
        row = s.find(code_x, name)
        for data in (row, self.detail_data(row)):
            self.assertIn(s.value(data, "contact"), (None, ""))
            self.assertIn(s.value(data, "phone"), (None, ""))
            self.assertEqual(str(s.value(data, "status")), "0")

    def test_A29_phone_not_format_checked(self):
        s = self.s
        phone = "请找前台转分机 #12（非号码）"
        row = self.new(phone=phone)
        self.assertEqual(s.value(row, "phone"), phone)
        self.assertEqual(s.value(self.detail_data(row), "phone"), phone)


class UpdateTest(SupplierCase):
    def test_A13_change_contact_and_disable(self):
        s = self.s
        row = self.new(status="0")
        contact = "新联系人" + tok(4)
        self.assert_code(s.update(**s.full(row, contact=contact, status="1")), 200)
        data = self.detail_data(row)
        self.assertEqual(s.value(data, "contact"), contact)
        self.assertEqual(str(s.value(data, "status")), "1")

    def test_A14_detail_returns_full_record(self):
        s = self.s
        row = self.new(status="1")
        data = self.detail_data(row)
        self.assertEqual(str(data.get(s.id_key)), str(row[s.id_key]))
        for logical in FIELDS:
            self.assertEqual(str(s.value(data, logical)), str(s.value(row, logical)), logical)

    def test_A30_code_cannot_be_changed(self):
        s = self.s
        row = self.new()
        old_code, new_code = s.value(row, "code"), "Y" + tok()
        s.update(**s.full(row, code=new_code))  # 拒绝或忽略编码都可以，结果由下面的断言检查
        self.assertEqual(s.value(self.detail_data(row), "code"), old_code)
        rows, _ = s.rows()
        self.assertNotIn(new_code, {s.value(r, "code") for r in rows})

    def test_A31_name_cannot_be_cleared(self):
        s = self.s
        row = self.new()
        code, msg, _ = s.update(**s.full(row, name=""))
        self.assertNotEqual(code, 200, msg)
        self.assertIn("名称", msg)
        self.assertEqual(s.value(self.detail_data(row), "name"), s.value(row, "name"))


class DeleteTest(SupplierCase):
    def test_A16_A32_delete_enabled_supplier(self):
        s = self.s
        row = self.new(status="0")
        self.assertEqual(str(s.value(row, "status")), "0")
        self.assert_code(s.remove([row[s.id_key]]), 200)
        self.assertEqual(s.rows(name=s.value(row, "name"))[0], [])
        rows, _ = s.rows()
        self.assertNotIn(str(row[s.id_key]), {str(r.get(s.id_key)) for r in rows})

    def test_A17_batch_delete(self):
        s = self.s
        t = tok()
        first = self.new(name="批删甲" + t)
        second = self.new(name="批删乙" + t)
        self.assert_code(s.remove([first[s.id_key], second[s.id_key]]), 200)
        self.assertEqual(s.rows(name=t)[0], [])

    def test_A33_deleted_supplier_has_no_detail(self):
        s = self.s
        row = self.new()
        self.assert_code(s.remove([row[s.id_key]]), 200)
        code, msg, payload = s.detail(row[s.id_key])
        self.assertTrue(code != 200 or not payload.get("data"), payload)


class ExportTest(SupplierCase):
    def test_A19_export_excel_with_headers(self):
        s = self.s
        self.new()
        ctype, content = s.export()
        rows = read_xlsx(content)
        header = rows[0]
        for label in HEADER_LABELS:
            self.assertTrue(any(label in cell for cell in header), f"表头缺少 {label}: {header} ({ctype})")
        self.assertGreaterEqual(len(rows), 2, "导出文件没有数据行")

    def test_A34_export_all_matching_rows_not_paged(self):
        s = self.s
        t = tok(6)
        for i in range(DEFAULT_PAGE + 1):
            self.assert_code(s.add(code=f"X{t}{i:02d}", name=f"导出停用{t}-{i}", status="1"), 200)
        _, total = s.rows(status="1", size=DEFAULT_PAGE)
        self.assertGreater(total, DEFAULT_PAGE)
        rows = read_xlsx(s.export(status="1")[1])
        header, data = rows[0], rows[1:]
        index = next((i for i, cell in enumerate(header) if "状态" in cell), None)
        self.assertIsNotNone(index, f"表头缺少状态列: {header}")
        self.assertEqual(len(data), total)
        for row in data:
            self.assertEqual(row[index] if index < len(row) else "", "停用", row)


class PermissionTest(SupplierCase):
    def test_A22_list_only_user_cannot_write_or_export(self):
        s = self.s
        user = s.limited()
        row = self.new()
        t = tok()
        self.assert_code(s.add(client=user, code="R" + t, name="越权新增" + t), 403)
        self.assert_code(s.update(client=user, **s.full(row, name="越权修改" + t)), 403)
        self.assert_code(s.remove([row[s.id_key]], client=user), 403)
        ctype, content = s.export(client=user)
        self.assertFalse(content.startswith(b"PK"), "无导出权限却拿到了 Excel")
        self.assertEqual(json.loads(content.decode("utf-8")).get("code"), 403, ctype)
        data = self.detail_data(row)
        for logical in FIELDS:
            self.assertEqual(str(s.value(data, logical)), str(s.value(row, logical)), logical)
        self.assertEqual(s.rows(name="越权新增" + t)[0], [])

    def test_A35_list_user_in_other_dept_sees_admin_supplier(self):
        s = self.s
        row = self.new(name="管理员新增" + tok())
        rows, _ = s.rows(client=s.limited(), name=s.value(row, "name"))
        self.assertIn(str(row[s.id_key]), {str(r.get(s.id_key)) for r in rows})

    def test_A24_admin_query_add_edit_delete_export(self):
        s = self.s
        t = tok()
        self.assertEqual(s.admin.get(s.base + "/list", {"pageNum": 1, "pageSize": DEFAULT_PAGE})["code"], 200)
        self.assert_code(s.add(code="F" + t, name="全流程" + t), 200)
        row = s.find("F" + t, "全流程" + t)
        self.assert_code(s.update(**s.full(row, remark="已修改" + t)), 200)
        self.assert_code(s.remove([row[s.id_key]]), 200)
        self.assertTrue(read_xlsx(s.export()[1]))


if __name__ == "__main__":
    unittest.main()
