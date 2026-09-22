"""FEAT-20260921-001 供应商分类：后端接口验收冒烟（独立外部验收）。

供应商接口和已有字段沿用 FEAT-20260918-001 已验收的 /biz/supplier 契约；分类字段名不绑定实现：
先用候选别名提交字典中的有效值新增一条探针记录，再按回读的值识别分类的 JSON 键。
『未分类』查询条件同样不绑定实现：从前端源码和常见取值中找出能筛出历史供应商、且排除分类有效的
供应商的那个条件，再用它验证其余规则。
接口要求分类必填，无法产生分类为空的历史供应商，因此经冒烟执行器使用的 MySQL 容器（ruoyi-mysql）
把刚新增的供应商的分类列置空来模拟历史数据。
"""

from __future__ import annotations

import io
import subprocess
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ruoyi_client import ApiError, Client

BASE = "/biz/supplier"
DICT_NAME = "供应商分类"
UNCATEGORIZED = "未分类"
INITIAL_LABELS = ("原材料", "服务", "设备")
KEYS = {"id": "supplierId", "code": "supplierCode", "name": "supplierName", "contact": "contactName",
        "phone": "contactPhone", "status": "status", "remark": "remark"}
FIELDS = ("code", "name", "category", "contact", "phone", "status", "remark")
CATEGORY_ALIASES = ("supplierCategory", "category", "supplierType", "categoryCode", "supplierCategoryCode",
                    "categoryValue", "supplierClass", "supplierClassify", "classify")
UNCATEGORIZED_VALUES = (UNCATEGORIZED, "__none__", "__NONE__", "none", "NONE", "null", "NULL", "-1",
                        "uncategorized", "UNCATEGORIZED", "unclassified", "UNCLASSIFIED", "empty", "__empty__")
UNCATEGORIZED_FLAGS = ("uncategorized", "unclassified", "noCategory", "categoryEmpty", "withoutCategory",
                       "onlyUncategorized")
UNCATEGORIZED_HINTS = (UNCATEGORIZED, "uncategor", "unclassif", "none", "empty")
FRONTEND_SOURCES = ("frontend/src/views/biz/supplier", "frontend/src/api/biz/supplier")
BASE_COLUMNS = {"supplier_id", "supplier_code", "supplier_name", "contact_name", "contact_phone", "status",
                "remark", "del_flag", "create_dept", "create_by", "create_time", "update_by", "update_time",
                "tenant_id"}
MYSQL = ["docker", "exec", "-i", "ruoyi-mysql", "mysql", "--default-character-set=utf8mb4", "-uroot", "-proot",
         "-N", "-B"]
BIG_PAGE = 200
DEFAULT_PAGE = 10
XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADER_LABELS = ("编码", "名称", "分类", "联系人", "电话", "状态", "备注")


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


def column(header: list[str], label: str) -> int:
    index = next((i for i, text in enumerate(header) if label in text), None)
    if index is None:
        raise AssertionError(f"导出表头缺少『{label}』列: {header}")
    return index


def cell_of(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def mysql(statement: str, database: str | None = None) -> list[list[str]]:
    result = subprocess.run(MYSQL + ([database] if database else []) + ["-e", statement], capture_output=True)
    if result.returncode != 0:
        raise AssertionError("准备历史供应商时 MySQL 命令失败: " + result.stderr.decode("utf-8", "replace")[-500:])
    return [line.split("\t") for line in result.stdout.decode("utf-8").splitlines() if line]


def clear_category(code: str) -> None:
    """Simulate a supplier created before categories existed: empty its category column."""
    schemas = [r[0] for r in mysql("select table_schema from information_schema.tables "
                                   "where table_name = 'biz_supplier' and table_schema like 'ry_smoke_%'")]
    database = next((s for s in schemas
                     if mysql(f"select count(*) from biz_supplier where supplier_code = '{code}'", s) == [["1"]]),
                    None)
    if database is None:
        raise AssertionError(f"冒烟数据库中找不到编码为 {code} 的供应商")
    columns = [r[0].lower() for r in mysql("select column_name from information_schema.columns "
                                           f"where table_schema = '{database}' and table_name = 'biz_supplier'")]
    extra = [c for c in columns if c not in BASE_COLUMNS]
    name = next((c for word in ("categ", "class", "type") for c in extra if word in c),
                extra[0] if len(extra) == 1 else None)
    if name is None:
        raise AssertionError(f"biz_supplier 中找不到分类列: {columns}")
    try:
        mysql(f"update biz_supplier set `{name}` = null where supplier_code = '{code}'", database)
    except AssertionError:
        mysql(f"update biz_supplier set `{name}` = '' where supplier_code = '{code}'", database)


def source_candidates() -> list[str]:
    """Quoted literals on supplier frontend lines that mention 未分类 (the option value the page submits)."""
    found = []
    for folder in FRONTEND_SOURCES:
        root = Path(folder)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix not in (".vue", ".ts"):
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not any(hint in line.lower() for hint in UNCATEGORIZED_HINTS):
                    continue
                for quote in ("'", '"', "`"):
                    found += [p for p in line.split(quote)[1::2] if p and len(p) <= 40 and " " not in p]
    return found


def find_dict_type(client: Client) -> str:
    params = {"dictName": DICT_NAME, "pageNum": 1, "pageSize": 50}
    rows = page_of(client.get("/system/dict/type/list", params))["rows"] or []
    types = [r.get("dictType") for r in rows if r.get("dictName") == DICT_NAME]
    if not types:
        raise AssertionError(f"系统字典中没有名为『{DICT_NAME}』的字典")
    return types[0]


class Supplier:
    """Supplier API with the discovered category key, the category dictionary and shared fixtures."""

    def __init__(self):
        self.admin = Client()
        self.admin.login()
        self.dict_type = find_dict_type(self.admin)
        self.values: dict[str, str] = {}
        for item in self.dict_items():
            self.values.setdefault(item.get("dictLabel"), item.get("dictValue"))
        missing = [label for label in INITIAL_LABELS if label not in self.values]
        if missing:
            raise AssertionError(f"『{DICT_NAME}』字典缺少初始值 {missing}: {self.values}")
        self.cat_key = None
        self._fixture = None
        self._uncategorized = None
        self._probe()

    def dict_items(self) -> list[dict]:
        params = {"dictType": self.dict_type, "pageNum": 1, "pageSize": BIG_PAGE}
        return list(page_of(self.admin.get("/system/dict/data/list", params))["rows"] or [])

    def add_category(self) -> tuple[str, object]:
        """Add a value to the category dictionary; return (value, dictCode)."""
        t = tok(8)
        value = "smk" + t
        self.admin.post("/system/dict/data", {"dictType": self.dict_type, "dictLabel": "临时分类" + t,
                                              "dictValue": value, "dictSort": 99, "listClass": "default",
                                              "isDefault": "N"})
        item = next((i for i in self.dict_items() if i.get("dictValue") == value), None)
        if item is None:
            raise AssertionError(f"新增的分类值 {value} 在字典中查询不到")
        return value, item["dictCode"]

    def remove_category(self, dict_code) -> None:
        self.admin.delete(f"/system/dict/data/{dict_code}")

    def _probe(self):
        t = tok()
        raw = self.values["原材料"]
        fields = {"code": "P" + t, "name": "分类探针" + t, "contact": "探针联系人" + t, "phone": "TEL-" + t,
                  "status": "1" if raw != "1" else "0", "remark": "探针备注" + t, "category": raw}
        code, msg, _ = self.add(**fields)
        if code != 200:
            raise AssertionError(f"带分类新增供应商失败（分类字段候选 {CATEGORY_ALIASES}）: {code} {msg}")
        row = self.find(fields["code"], fields["name"])
        known = set(KEYS.values())
        self.cat_key = next((k for k, v in row.items() if k not in known and v == raw), None)
        if self.cat_key is None:
            raise AssertionError(f"列表记录中没有分类字段（提交值 {raw}）: {row}")

    def body(self, **fields) -> dict:
        out = {}
        for logical, value in fields.items():
            if value is None:
                continue
            if logical == "category":
                out.update({self.cat_key: value} if self.cat_key else dict.fromkeys(CATEGORY_ALIASES, value))
            else:
                out[KEYS[logical]] = value
        return out

    def value(self, row: dict, logical: str):
        return row.get(self.cat_key if logical == "category" else KEYS[logical])

    def codes(self, rows: list[dict]) -> set:
        return {self.value(r, "code") for r in rows}

    def add(self, **fields):
        return call(self.admin.post, BASE, self.body(**fields))

    def update(self, **fields):
        return call(self.admin.put, BASE, self.body(**fields))

    def detail(self, supplier_id):
        return call(self.admin.get, f"{BASE}/{supplier_id}")

    def rows(self, client=None, size=BIG_PAGE, extra=None, **filters):
        params = {"pageNum": 1, "pageSize": size}
        params.update(self.body(**filters))
        params.update(extra or {})
        page = page_of((client or self.admin).get(BASE + "/list", params))
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
        fields["id"] = row[KEYS["id"]]
        return fields

    def historical(self, **fields) -> dict:
        """A supplier whose category is empty, as if created before this change."""
        row = self.create(category=self.values["原材料"], **fields)
        clear_category(fields["code"])
        row = self.find(fields["code"], fields["name"])
        if self.value(row, "category") not in (None, ""):
            raise AssertionError(f"置空分类后回读仍有分类: {row}")
        return row

    def deleted(self, **fields) -> dict:
        """A supplier whose category value has since been deleted from the dictionary."""
        value, dict_code = self.add_category()
        row = self.create(category=value, **fields)
        self.remove_category(dict_code)
        return row

    def fixture(self) -> dict:
        if self._fixture is None:
            token, t = "分类夹具" + tok(8), tok(6)
            self._fixture = {
                "token": token,
                "hist": self.historical(code="FH" + t, name=token + "历史"),
                "deleted": self.deleted(code="FD" + t, name=token + "已删分类"),
                "raw": self.create(code="FR" + t, name=token + "原材料", category=self.values["原材料"]),
                "service": self.create(code="FS" + t, name=token + "服务", category=self.values["服务"]),
            }
        return self._fixture

    def uncategorized(self) -> dict:
        """Query parameters of the 未分类 filter: the candidate that returns the historical supplier only."""
        if self._uncategorized is None:
            fx = self.fixture()
            code = lambda key: self.value(fx[key], "code")
            known = set(self.values.values())
            values = [v for v in dict.fromkeys(source_candidates() + list(UNCATEGORIZED_VALUES)) if v not in known]
            options = [{self.cat_key: v} for v in values]
            options += [{flag: v} for flag in UNCATEGORIZED_FLAGS for v in ("true", "1")]
            for params in options:
                try:
                    rows, _ = self.rows(name=fx["token"], extra=params)
                except (ApiError, AssertionError):
                    continue
                codes = self.codes(rows)
                if code("hist") in codes and code("raw") not in codes and code("service") not in codes:
                    self._uncategorized = params
                    break
            else:
                raise AssertionError("没有能筛出分类为空的供应商、且排除分类有效供应商的『未分类』查询条件")
        return self._uncategorized

    def export(self, extra=None, **filters) -> tuple[list[str], list[list[str]]]:
        """POST the export form like the frontend does; return (header, data rows)."""
        fields = self.body(**filters)
        fields.update(extra or {})
        data = urllib.parse.urlencode(fields).encode("utf-8")
        headers = {"clientid": self.admin.client_id, "Authorization": "Bearer " + self.admin.token,
                   "Content-Type": "application/x-www-form-urlencoded"}
        request = urllib.request.Request(self.admin.base_url + BASE + "/export", data=data, headers=headers,
                                         method="POST")
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                content = resp.read()
        except urllib.error.HTTPError as exc:
            content = exc.read()
        rows = read_xlsx(content)
        return rows[0], rows[1:]


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


class CategoryCase(unittest.TestCase):
    def setUp(self):
        self.s = supplier()

    def cat(self, label: str) -> str:
        return self.s.values[label]

    def new(self, **fields) -> dict:
        t = tok()
        data = {"code": "S" + t, "name": "供应商" + t, "contact": "联系人" + t[:4], "phone": "0755-" + t[:6],
                "remark": "备注" + t, "category": self.cat("原材料")}
        data.update(fields)
        return self.s.create(**data)

    def assert_code(self, result, expected):
        self.assertEqual(result[0], expected, f"code={result[0]} msg={result[1]}")

    def assert_rejected(self, result, word):
        self.assertNotEqual(result[0], 200, f"应当失败却成功: {result[2]}")
        self.assertIn(word, result[1])

    def detail_data(self, row: dict) -> dict:
        result = self.s.detail(row[KEYS["id"]])
        self.assert_code(result, 200)
        data = result[2].get("data")
        self.assertTrue(data, result[2])
        return data

    def export_row(self, header, data, code) -> list[str]:
        index = column(header, "编码")
        matches = [r for r in data if cell_of(r, index) == code]
        self.assertEqual(len(matches), 1, f"导出文件中编码 {code} 的行数不为 1")
        return matches[0]


class DictTest(CategoryCase):
    def test_A36_category_dictionary_has_initial_values(self):
        s = self.s
        self.assertEqual(find_dict_type(s.admin), s.dict_type)
        labels = {item.get("dictLabel") for item in s.dict_items()}
        for label in INITIAL_LABELS:
            self.assertIn(label, labels)

    def test_A37_new_dictionary_value_can_be_used(self):
        s = self.s
        value, _ = s.add_category()
        row = self.new(category=value)
        self.assertEqual(s.value(row, "category"), value)
        self.assertEqual(s.value(self.detail_data(row), "category"), value)

    def test_A55_deleted_dictionary_value_is_rejected(self):
        s = self.s
        value, dict_code = s.add_category()
        s.remove_category(dict_code)
        t = tok()
        code_x, name = "V" + t, "已删分类新增" + t
        self.assert_rejected(s.add(code=code_x, name=name, category=value), "分类")
        self.assertNotIn(code_x, s.codes(s.rows(name=name)[0]))


class CreateTest(CategoryCase):
    def test_A9_create_with_category_then_query_by_name(self):
        s = self.s
        t = tok()
        data = {"code": "C" + t, "name": "新增供应商" + t, "category": self.cat("原材料"),
                "contact": "王五" + t[:4], "phone": "13800138000", "status": "0", "remark": "备注" + t}
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
        self.assert_rejected(s.add(code=code_x, name="重复编码乙" + t, category=self.cat("服务")), "编码")
        rows, _ = s.rows(name=t)
        self.assertEqual(sum(1 for r in rows if s.value(r, "code") == code_x), 1, rows)

    def test_A11_name_required(self):
        self.assert_rejected(self.s.add(code="N" + tok(), category=self.cat("服务"), contact="无名称"), "名称")

    def test_A26_code_required(self):
        s = self.s
        name = "无编码供应商" + tok()
        self.assert_rejected(s.add(name=name, category=self.cat("服务")), "编码")
        self.assertEqual(s.rows(name=name)[0], [])

    def test_A27_name_not_unique(self):
        s = self.s
        name = "同名供应商" + tok()
        self.new(name=name)
        self.assert_code(s.add(code="E" + tok(), name=name, category=self.cat("设备")), 200)
        rows, _ = s.rows(name=name)
        self.assertEqual(len([r for r in rows if s.value(r, "name") == name]), 2, rows)

    def test_A28_only_code_name_category_defaults_to_enabled(self):
        s = self.s
        t = tok()
        code_x, name, category = "M" + t, "最少字段" + t, self.cat("设备")
        self.assert_code(s.add(code=code_x, name=name, category=category), 200)
        row = s.find(code_x, name)
        for data in (row, self.detail_data(row)):
            self.assertIn(s.value(data, "contact"), (None, ""))
            self.assertIn(s.value(data, "phone"), (None, ""))
            self.assertEqual(str(s.value(data, "status")), "0")
            self.assertEqual(s.value(data, "category"), category)

    def test_A29_phone_not_format_checked(self):
        s = self.s
        phone = "请找前台转分机 #12（非号码）"
        row = self.new(phone=phone, category=self.cat("服务"))
        self.assertEqual(s.value(row, "phone"), phone)
        self.assertEqual(s.value(self.detail_data(row), "phone"), phone)

    def test_A38_category_required_on_create(self):
        s = self.s
        t = tok()
        code_x, name = "K" + t, "无分类供应商" + t
        self.assert_rejected(s.add(code=code_x, name=name, contact="无分类"), "分类")
        self.assertNotIn(code_x, s.codes(s.rows(name=name)[0]))

    def test_A50_unknown_category_rejected_on_create(self):
        s = self.s
        t = tok()
        code_x, name, bogus = "Z" + t, "无效分类供应商" + t, "zz" + t
        self.assertNotIn(bogus, s.values.values())
        self.assert_rejected(s.add(code=code_x, name=name, category=bogus), "分类")
        self.assertNotIn(code_x, s.codes(s.rows(name=name)[0]))


class QueryTest(CategoryCase):
    def test_A4_first_page_without_conditions(self):
        s = self.s
        t = tok()
        self.new(name="首页甲" + t)
        self.new(name="首页乙" + t, category=self.cat("服务"))
        page = page_of(s.admin.get(BASE + "/list", {"pageNum": 1, "pageSize": DEFAULT_PAGE}))
        rows = list(page["rows"] or [])
        self.assertGreaterEqual(int(page["total"]), 2)
        self.assertTrue(rows)
        self.assertLessEqual(len(rows), DEFAULT_PAGE)
        for row in rows:
            self.assertIn(KEYS["code"], row)
            self.assertIn(KEYS["name"], row)
        created, _ = s.rows(name=t)
        self.assertEqual(len(created), 2, created)
        for row in created:
            for logical in FIELDS:
                key = s.cat_key if logical == "category" else KEYS[logical]
                self.assertIn(key, row, f"记录缺少 {logical}: {row}")

    def test_A5_filter_by_disabled_status(self):
        s = self.s
        t = tok()
        enabled = self.new(name="状态启用" + t, status="0")
        disabled = self.new(name="状态停用" + t, status="1")
        rows, _ = s.rows(status="1")
        codes = s.codes(rows)
        self.assertIn(s.value(disabled, "code"), codes)
        self.assertNotIn(s.value(enabled, "code"), codes)
        self.assertTrue(all(str(s.value(r, "status")) == "1" for r in rows), rows)

    def test_A6_filter_by_full_name(self):
        s = self.s
        t = tok()
        wanted = self.new(name="甲供应商" + t)
        other = self.new(name="乙供应商" + t)
        name = s.value(wanted, "name")
        codes = s.codes(s.rows(name=name)[0])
        self.assertIn(s.value(wanted, "code"), codes)
        self.assertNotIn(s.value(other, "code"), codes)

    def test_A25_filter_by_name_fragment(self):
        s = self.s
        middle = tok()
        wanted = self.new(name="华东" + middle + "精密")
        other = self.new(name="华南" + tok() + "机械")
        rows, _ = s.rows(name=middle)
        codes = s.codes(rows)
        self.assertIn(s.value(wanted, "code"), codes)
        self.assertNotIn(s.value(other, "code"), codes)
        self.assertTrue(all(middle in str(s.value(r, "name")) for r in rows), rows)

    def test_A41_filter_by_category(self):
        s = self.s
        t = tok()
        raw, service = self.cat("原材料"), self.cat("服务")
        wanted = self.new(name="按分类原材料" + t, category=raw)
        other = self.new(name="按分类服务" + t, category=service)
        rows, _ = s.rows(category=raw)
        self.assertTrue(rows)
        self.assertTrue(all(s.value(r, "category") == raw for r in rows), rows)
        codes = s.codes(s.rows(category=raw, name=t)[0])
        self.assertIn(s.value(wanted, "code"), codes)
        self.assertNotIn(s.value(other, "code"), codes)

    def test_A42_filter_by_name_and_category(self):
        s = self.s
        name = "同名分类组合" + tok()
        equipment = self.new(name=name, category=self.cat("设备"))
        self.new(name=name, category=self.cat("服务"))
        rows, _ = s.rows(name=name, category=self.cat("设备"))
        self.assertEqual(s.codes(rows), {s.value(equipment, "code")}, rows)

    def test_A51_uncategorized_filter_returns_empty_category(self):
        s = self.s
        fx = s.fixture()
        rows, _ = s.rows(extra=s.uncategorized())
        codes = s.codes(rows)
        self.assertIn(s.value(fx["hist"], "code"), codes)
        self.assertNotIn(s.value(fx["raw"], "code"), codes)
        valid = set(s.values.values())
        for row in rows:
            self.assertNotIn(s.value(row, "category"), valid, row)

    def test_A58_uncategorized_filter_returns_deleted_category(self):
        s = self.s
        fx = s.fixture()
        codes = s.codes(s.rows(extra=s.uncategorized())[0])
        self.assertIn(s.value(fx["deleted"], "code"), codes)
        self.assertNotIn(s.value(fx["service"], "code"), codes)

    def test_A7_list_requires_login(self):
        code, msg, _ = call(Client().get, BASE + "/list", {"pageNum": 1, "pageSize": DEFAULT_PAGE})
        self.assertEqual(code, 401, msg)


class UpdateTest(CategoryCase):
    def test_A13_change_contact_and_disable(self):
        s = self.s
        row = self.new(status="0")
        contact = "新联系人" + tok(4)
        self.assert_code(s.update(**s.full(row, contact=contact, status="1")), 200)
        data = self.detail_data(row)
        self.assertEqual(s.value(data, "contact"), contact)
        self.assertEqual(str(s.value(data, "status")), "1")

    def test_A14_detail_returns_full_record_with_category(self):
        s = self.s
        row = self.new(status="1", category=self.cat("设备"))
        data = self.detail_data(row)
        self.assertEqual(str(data.get(KEYS["id"])), str(row[KEYS["id"]]))
        for logical in FIELDS:
            self.assertEqual(str(s.value(data, logical)), str(s.value(row, logical)), logical)
        self.assertEqual(s.value(data, "category"), self.cat("设备"))

    def test_A30_code_cannot_be_changed(self):
        s = self.s
        row = self.new()
        old_code, new_code = s.value(row, "code"), "Y" + tok()
        s.update(**s.full(row, code=new_code))  # 拒绝或忽略编码都可以，结果由下面的断言检查
        self.assertEqual(s.value(self.detail_data(row), "code"), old_code)
        self.assertNotIn(new_code, s.codes(s.rows()[0]))

    def test_A31_name_cannot_be_cleared(self):
        s = self.s
        row = self.new()
        self.assert_rejected(s.update(**s.full(row, name="")), "名称")
        self.assertEqual(s.value(self.detail_data(row), "name"), s.value(row, "name"))

    def test_A45_change_category(self):
        s = self.s
        row = self.new(category=self.cat("原材料"))
        self.assert_code(s.update(**s.full(row, category=self.cat("设备"))), 200)
        self.assertEqual(s.value(self.detail_data(row), "category"), self.cat("设备"))

    def test_A46_category_cannot_be_cleared(self):
        s = self.s
        row = self.new(category=self.cat("服务"))
        self.assert_rejected(s.update(**s.full(row, category="")), "分类")
        self.assertEqual(s.value(self.detail_data(row), "category"), self.cat("服务"))

    def test_A53_unknown_category_rejected_on_update(self):
        s = self.s
        row = self.new(category=self.cat("服务"))
        bogus = "zz" + tok()
        self.assertNotIn(bogus, s.values.values())
        self.assert_rejected(s.update(**s.full(row, category=bogus)), "分类")
        self.assertEqual(s.value(self.detail_data(row), "category"), self.cat("服务"))

    def test_A47_historical_supplier_needs_category_to_save(self):
        s = self.s
        t = tok()
        row = s.historical(code="HU" + t, name="历史待补" + t, contact="原联系人" + t[:4])
        self.assert_rejected(s.update(**s.full(row, contact="新联系人" + t[:4])), "分类")
        self.assertEqual(s.value(self.detail_data(row), "contact"), "原联系人" + t[:4])


class ExportTest(CategoryCase):
    def test_A19_export_excel_with_category_header(self):
        self.new()
        header, data = self.s.export()
        for label in HEADER_LABELS:
            self.assertTrue(any(label in text for text in header), f"表头缺少 {label}: {header}")
        self.assertTrue(data, "导出文件没有数据行")

    def test_A34_export_all_matching_rows_not_paged(self):
        s = self.s
        t = tok(6)
        for i in range(DEFAULT_PAGE + 1):
            self.assert_code(s.add(code=f"X{t}{i:02d}", name=f"导出停用{t}-{i}", status="1",
                                   category=self.cat("服务")), 200)
        _, total = s.rows(status="1", size=DEFAULT_PAGE)
        self.assertGreater(total, DEFAULT_PAGE)
        header, data = s.export(status="1")
        index = column(header, "状态")
        self.assertEqual(len(data), total)
        for row in data:
            self.assertEqual(cell_of(row, index), "停用", row)

    def test_A49_export_by_category(self):
        s = self.s
        raw = self.cat("原材料")
        self.new(category=raw)
        self.new(category=self.cat("设备"))
        _, total = s.rows(category=raw, size=DEFAULT_PAGE)
        header, data = s.export(category=raw)
        index = column(header, "分类")
        self.assertEqual(len(data), total)
        for row in data:
            self.assertEqual(cell_of(row, index), "原材料", row)

    def test_A54_export_empty_category_as_uncategorized(self):
        s = self.s
        hist = s.fixture()["hist"]
        header, data = s.export(name=s.value(hist, "name"))
        row = self.export_row(header, data, s.value(hist, "code"))
        self.assertEqual(cell_of(row, column(header, "分类")), UNCATEGORIZED)

    def test_A57_export_deleted_category_as_uncategorized(self):
        s = self.s
        deleted = s.fixture()["deleted"]
        header, data = s.export(name=s.value(deleted, "name"))
        row = self.export_row(header, data, s.value(deleted, "code"))
        self.assertEqual(cell_of(row, column(header, "分类")), UNCATEGORIZED)

    def test_A60_export_uncategorized_filter(self):
        s = self.s
        fx = s.fixture()
        params = s.uncategorized()
        _, total = s.rows(extra=params, size=DEFAULT_PAGE)
        header, data = s.export(extra=params)
        code_index, cat_index = column(header, "编码"), column(header, "分类")
        codes = {cell_of(r, code_index) for r in data}
        self.assertIn(s.value(fx["hist"], "code"), codes)
        self.assertIn(s.value(fx["deleted"], "code"), codes)
        self.assertNotIn(s.value(fx["service"], "code"), codes)
        self.assertEqual(len(data), total)
        for row in data:
            self.assertEqual(cell_of(row, cat_index), UNCATEGORIZED, row)


if __name__ == "__main__":
    unittest.main()
