"""FEAT-20260923-002 供应商名称搜索忽略首尾空白字符和英文大小写：后端接口验收冒烟（独立外部验收）。

核心链路：名称条件先去掉首尾空白字符（半角空格、全角空格、制表符、换行），忽略英文字母大小写，
中间的空白字符按原样参与匹配；去掉首尾空白后为空时视同没有填写名称条件。列表查询和按条件导出遵守同一规则。
不能坏的基础功能沿用 FEAT-20260921-001 已验收的供应商列表、分类筛选、『未分类』和导出用例，以及它们的数据准备方式：
分类字段名和『未分类』查询条件不绑定实现，按候选探测；分类为空的历史供应商无法通过接口产生，
因此经冒烟执行器使用的 MySQL 容器（ruoyi-mysql）把刚新增的供应商的分类列置空来模拟。
"""

from __future__ import annotations

import io
import subprocess
import time
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

# 名称条件里的空白字符：半角空格、全角空格（U+3000）、制表符、换行
SPACE, FULL, TAB, LF = " ", chr(0x3000), chr(9), chr(10)
BLANK_MIX = SPACE + FULL + TAB + LF + SPACE * 2 + FULL + LF + TAB


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
    return [line.split(TAB) for line in result.stdout.decode("utf-8").splitlines() if line]


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
        # 雪花 ID 偶发 Clock moved backwards 属于环境时钟抖动，稍等后重试
        for _ in range(5):
            result = call(self.admin.post, BASE, self.body(**fields))
            if result[0] == 200 or "Clock moved backwards" not in result[1]:
                return result
            time.sleep(1)
        return call(self.admin.post, BASE, self.body(**fields))

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

    def historical(self, **fields) -> dict:
        """A supplier whose category is empty, as if created before categories existed."""
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


class SupplierCase(unittest.TestCase):
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

    def mixed(self, prefix: str = "") -> str:
        """A unique supplier name containing mixed-case English letters."""
        name = prefix + "Acme" + tok(8).upper() + "Steel"
        self.assertNotEqual(name, name.lower())
        self.assertNotEqual(name, name.upper())
        return name

    def export_row(self, header, data, code) -> list[str]:
        index = column(header, "编码")
        matches = [r for r in data if cell_of(r, index) == code]
        self.assertEqual(len(matches), 1, f"导出文件中编码 {code} 的行数不为 1")
        return matches[0]


class QueryTest(SupplierCase):
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


class NameRuleTest(SupplierCase):
    def assert_name_hits(self, query, wanted, other=None, fragment=None):
        """List by `query`: `wanted` is found, `other` is not, every row's name contains `fragment` ignoring case."""
        s = self.s
        rows, _ = s.rows(name=query)
        codes = s.codes(rows)
        self.assertIn(s.value(wanted, "code"), codes, f"名称条件 {query!r} 没有查到 {s.value(wanted, 'name')}: {rows}")
        if other is not None:
            self.assertNotIn(s.value(other, "code"), codes, f"名称条件 {query!r} 查到了不匹配的 {s.value(other, 'name')}")
        if fragment is not None:
            for row in rows:
                self.assertIn(fragment.lower(), str(s.value(row, "name")).lower(), row)

    def pair(self, prefix: str):
        name = self.mixed(prefix)
        return name, self.new(name=name), self.new(name=prefix + "对照" + tok())

    def test_A61_leading_trailing_half_width_spaces_ignored(self):
        name, wanted, other = self.pair("半角")
        self.assert_name_hits(SPACE * 3 + name + SPACE * 2, wanted, other, name)

    def test_A69_leading_trailing_full_width_spaces_ignored(self):
        name, wanted, other = self.pair("全角")
        self.assert_name_hits(FULL * 2 + name + FULL * 3, wanted, other, name)

    def test_A70_leading_tab_trailing_newline_ignored(self):
        name, wanted, other = self.pair("制表换行")
        self.assert_name_hits(TAB + name + LF, wanted, other, name)

    def test_A62_lower_case_condition_matches(self):
        name = self.mixed("小写")
        wanted = self.new(name=name)
        self.assert_name_hits(name.lower(), wanted, fragment=name)

    def test_A63_upper_case_condition_matches(self):
        name = self.mixed("大写")
        wanted = self.new(name=name)
        self.assert_name_hits(name.upper(), wanted, fragment=name)

    def test_A64_fragment_with_changed_case_and_spaces(self):
        fragment = "Acme" + tok(8).upper() + "Steel"
        wanted = self.new(name="华北" + fragment + "机械")
        other = self.new(name="华南" + tok() + "机械")
        query = SPACE * 2 + fragment.swapcase() + SPACE * 2
        self.assertNotIn(query.strip(), fragment)
        self.assert_name_hits(query, wanted, other, fragment)

    def test_A65_inner_space_is_kept(self):
        t = tok(6)
        spaced = self.new(name="Acme Steel" + t)
        joined = self.new(name="AcmeSteel" + t)
        self.assert_name_hits("acme steel", spaced, joined, "acme steel")

    def assert_blank_is_no_condition(self, blank: str):
        s = self.s
        self.new(status="0")
        self.new(status="1", category=self.cat("服务"))
        _, total = s.rows(size=DEFAULT_PAGE)
        rows, blank_total = s.rows(name=blank, size=DEFAULT_PAGE)
        self.assertGreaterEqual(total, 2)
        self.assertEqual(blank_total, total, f"名称条件 {blank!r} 的总条数与不带条件不同")
        self.assertTrue(rows)

    def test_A66_only_half_width_spaces_is_no_condition(self):
        self.assert_blank_is_no_condition(SPACE * 4)

    def test_A71_only_mixed_whitespace_is_no_condition(self):
        self.assert_blank_is_no_condition(BLANK_MIX)


class ExportTest(SupplierCase):
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
            code, msg, _ = s.add(code=f"X{t}{i:02d}", name=f"导出停用{t}-{i}", status="1", category=self.cat("服务"))
            self.assertEqual(code, 200, msg)
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

    def assert_export_matches_list(self, query: str, wanted: dict):
        """Export by name `query`: it contains `wanted` and has as many rows as the list total for `query`."""
        s = self.s
        _, total = s.rows(name=query, size=DEFAULT_PAGE)
        header, data = s.export(name=query)
        self.export_row(header, data, s.value(wanted, "code"))
        self.assertEqual(len(data), total, f"名称条件 {query!r} 的导出行数与列表总条数不同")

    def test_A67_export_name_with_changed_case_and_spaces(self):
        name = self.mixed("导出大小写")
        wanted = self.new(name=name)
        self.assert_export_matches_list(SPACE * 2 + name.swapcase() + SPACE * 3, wanted)

    def test_A72_export_name_with_full_width_space_tab_newline(self):
        name = self.mixed("导出空白")
        wanted = self.new(name=name)
        self.assert_export_matches_list(FULL + TAB + name + LF, wanted)

    def test_A68_export_blank_name_with_disabled_status(self):
        s = self.s
        self.new(status="0")
        self.new(status="1")
        _, total = s.rows(status="1", size=DEFAULT_PAGE)
        self.assertGreaterEqual(total, 1)
        header, data = s.export(name=BLANK_MIX, status="1")
        index = column(header, "状态")
        self.assertEqual(len(data), total)
        for row in data:
            self.assertEqual(cell_of(row, index), "停用", row)


if __name__ == "__main__":
    unittest.main()
