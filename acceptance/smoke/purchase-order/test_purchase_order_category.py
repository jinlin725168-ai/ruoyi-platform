'''系统冒烟：采购单按供应商分类展示、筛选与导出（来自 FEAT-20260923-001 的核心链路）。

只保留采购单的基础查询（单号片段、状态）和供应商分类的核心口径：列表展示字典名称、空值与失效值显示『未分类』、
按分类和『未分类』筛选、分类修改后按新分类生效、供应商逻辑删除后仍按保留的分类展示与筛选、导出带供应商分类列。
展示字段和筛选参数不绑定实现：展示字段按回读的值识别（字典名称；或者是字典值，再按字典翻译），筛选参数从候选别名中识别，
『未分类』条件从前端源码和常见取值中识别。
接口不允许保存分类为空的供应商，所以通过冒烟执行器使用的 MySQL 容器（ruoyi-mysql）把供应商分类列置空，模拟历史数据；
分类失效用先新增再删除的字典值模拟；供应商逻辑删除调用供应商删除接口。
'''

from __future__ import annotations

import datetime as dt
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

ORDER_BASE = '/biz/purchaseOrder'
SUPPLIER_BASE = '/biz/supplier'
CATEGORY_DICT = 'biz_supplier_category'
STATUS_DICT = 'biz_purchase_order_status'
UNCATEGORIZED = '未分类'
LABELS = ('原材料', '服务', '设备')
BIG_PAGE = 200
XLSX_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ORDER_KEYS = {'orderId', 'orderNo', 'supplierId', 'supplierName', 'orderDate', 'status', 'totalAmount', 'remark',
              'createTime', 'updateTime', 'createBy', 'createDept', 'updateBy', 'details', 'params', 'searchValue'}
CATEGORY_PARAMS = ('supplierCategory', 'category', 'supplierCategoryCode', 'categoryCode', 'supplierCategoryValue',
                   'supplierType', 'supplierClass', 'categoryValue', 'supplierCategoryType')
UNCATEGORIZED_VALUES = (UNCATEGORIZED, '__none__', '__NONE__', 'none', 'NONE', 'null', 'NULL', '-1',
                        'uncategorized', 'UNCATEGORIZED', 'unclassified', 'UNCLASSIFIED', 'empty', '__empty__')
UNCATEGORIZED_FLAGS = ('uncategorized', 'unclassified', 'noCategory', 'categoryEmpty', 'withoutCategory',
                       'onlyUncategorized', 'supplierCategoryNone')
UNCATEGORIZED_HINTS = (UNCATEGORIZED, 'uncategor', 'unclassif', 'none', 'empty')
FRONTEND_SOURCES = ('frontend/src/views/biz/purchaseOrder', 'frontend/src/api/biz/purchaseOrder',
                    'frontend/src/views/biz/supplier', 'frontend/src/api/biz/supplier')
SUPPLIER_COLUMNS = {'supplier_id', 'supplier_code', 'supplier_name', 'contact_name', 'contact_phone', 'status',
                    'remark', 'del_flag', 'create_dept', 'create_by', 'create_time', 'update_by', 'update_time',
                    'tenant_id'}
MYSQL = ['docker', 'exec', '-i', 'ruoyi-mysql', 'mysql', '--default-character-set=utf8mb4', '-uroot', '-proot',
         '-N', '-B']
QUOTES = (chr(39), chr(34), chr(96))


def tok(size: int = 10) -> str:
    return uuid.uuid4().hex[:size]


def day(offset: int = 0) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


def sq(value: str) -> str:
    return chr(39) + value.replace(chr(39), '') + chr(39)


def call(fn, *args, **kwargs):
    '''Run a Client call without asserting the RuoYi code; return (code, msg, payload).'''
    try:
        payload = fn(*args, expect=None, **kwargs)
    except ApiError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        return body.get('code', exc.status), str(body.get('msg') or ''), body
    return payload.get('code'), str(payload.get('msg') or ''), payload


def post(client: Client, path: str, body: dict):
    '''POST, retrying when the snowflake generator reports Clock moved backwards.'''
    for attempt in range(6):
        result = call(client.post, path, body)
        if result[0] != 200 and 'Clock moved backwards' in result[1] and attempt < 5:
            time.sleep(1)
            continue
        return result


def page_of(payload: dict) -> dict:
    data = payload.get('data')
    page = data if isinstance(data, dict) and 'rows' in data else payload
    if 'rows' not in page or 'total' not in page:
        raise AssertionError(f'分页结果缺少 rows/total: {str(payload)[:300]}')
    return page


def col_index(ref: str) -> int:
    number = 0
    for ch in ref:
        if not ch.isalpha():
            break
        number = number * 26 + (ord(ch.upper()) - 64)
    return number - 1


def read_xlsx(content: bytes) -> list[list[str]]:
    '''Non-empty rows of the first worksheet as lists of cell texts.'''
    if not content.startswith(b'PK'):
        raise AssertionError(f'不是 Excel 文件: {content[:200]!r}')
    with zipfile.ZipFile(io.BytesIO(content)) as book:
        names = book.namelist()
        shared = []
        if 'xl/sharedStrings.xml' in names:
            for item in ET.fromstring(book.read('xl/sharedStrings.xml')).iter(XLSX_NS + 'si'):
                shared.append(''.join(t.text or '' for t in item.iter(XLSX_NS + 't')))
        sheets = sorted(n for n in names if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'))
        if not sheets:
            raise AssertionError('Excel 文件中没有工作表')
        root = ET.fromstring(book.read(sheets[0]))
    rows = []
    for row in root.iter(XLSX_NS + 'row'):
        cells = {}
        for cell in row.findall(XLSX_NS + 'c'):
            ref = cell.get('r')
            index = col_index(ref) if ref else len(cells)
            kind = cell.get('t')
            value = cell.find(XLSX_NS + 'v')
            if kind == 's':
                text = shared[int(value.text)] if value is not None and value.text else ''
            elif kind == 'inlineStr':
                text = ''.join(t.text or '' for t in cell.iter(XLSX_NS + 't'))
            else:
                text = value.text if value is not None and value.text else ''
            cells[index] = text
        if any(text.strip() for text in cells.values()):
            rows.append([cells.get(i, '') for i in range(max(cells) + 1)])
    if not rows:
        raise AssertionError('Excel 文件为空')
    return rows


def read_export(result) -> tuple[list[str], list[list[str]]]:
    _, content = result
    rows = read_xlsx(content)
    return rows[0], rows[1:]


def column(header: list[str], label: str) -> int:
    index = next((i for i, text in enumerate(header) if label in text), None)
    if index is None:
        raise AssertionError(f'导出表头缺少『{label}』列: {header}')
    return index


def cell_of(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ''


def mysql(statement: str, database: str | None = None) -> list[list[str]]:
    result = subprocess.run(MYSQL + ([database] if database else []) + ['-e', statement], capture_output=True)
    if result.returncode != 0:
        raise AssertionError('准备分类为空的供应商时 MySQL 命令失败: '
                             + result.stderr.decode('utf-8', 'replace')[-500:])
    return [line.split(chr(9)) for line in result.stdout.decode('utf-8').splitlines() if line]


def clear_category(code: str) -> None:
    '''Simulate a supplier saved before categories existed: empty its category column.'''
    schemas = [r[0] for r in mysql('select table_schema from information_schema.tables where table_name = '
                                   + sq('biz_supplier') + ' and table_schema like ' + sq('ry_smoke_%'))]
    database = next((s for s in schemas
                     if mysql('select count(*) from biz_supplier where supplier_code = ' + sq(code), s) == [['1']]),
                    None)
    if database is None:
        raise AssertionError(f'冒烟数据库中找不到编码为 {code} 的供应商')
    columns = [r[0].lower() for r in mysql('select column_name from information_schema.columns where table_schema = '
                                           + sq(database) + ' and table_name = ' + sq('biz_supplier'))]
    extra = [c for c in columns if c not in SUPPLIER_COLUMNS]
    name = next((c for word in ('categ', 'class', 'type') for c in extra if word in c),
                extra[0] if len(extra) == 1 else None)
    if name is None:
        raise AssertionError(f'biz_supplier 中找不到分类列: {columns}')
    target = chr(96) + name + chr(96)
    try:
        mysql('update biz_supplier set ' + target + ' = null where supplier_code = ' + sq(code), database)
    except AssertionError:
        mysql('update biz_supplier set ' + target + ' = ' + sq('') + ' where supplier_code = ' + sq(code), database)


def source_candidates() -> list[str]:
    '''Quoted literals on frontend lines that mention 未分类 (the option value the page submits).'''
    found = []
    for folder in FRONTEND_SOURCES:
        root = Path(folder)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob('*')):
            if path.suffix not in ('.vue', '.ts'):
                continue
            for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
                if not any(hint in line.lower() for hint in UNCATEGORIZED_HINTS):
                    continue
                for quote in QUOTES:
                    found += [p for p in line.split(quote)[1::2] if p and len(p) <= 40 and ' ' not in p]
    return found


class World:
    '''Shared fixture: suppliers in every category state, each with purchase orders.'''

    def __init__(self):
        self.admin = Client()
        self.admin.login()
        self.categories = self.dict_values(CATEGORY_DICT)
        missing = [label for label in LABELS if label not in self.categories]
        if missing:
            raise AssertionError(f'供应商分类字典缺少 {missing}: {self.categories}')
        self.labels = {value: label for label, value in self.categories.items()}
        statuses = self.dict_values(STATUS_DICT)
        if '草稿' not in statuses or '已提交' not in statuses:
            raise AssertionError(f'采购单状态字典缺少 草稿/已提交: {statuses}')
        self.draft, self.submitted = str(statuses['草稿']), str(statuses['已提交'])
        self.prefix = '分类采购' + tok(8)
        self._display = None
        self._cat_param = None
        self._uncategorized = None
        self._build()

    # ---- 字典 -------------------------------------------------------------

    def dict_items(self, dict_type: str) -> list[dict]:
        params = {'dictType': dict_type, 'pageNum': 1, 'pageSize': BIG_PAGE}
        return list(page_of(self.admin.get('/system/dict/data/list', params))['rows'] or [])

    def dict_values(self, dict_type: str) -> dict:
        values = {}
        for item in self.dict_items(dict_type):
            values.setdefault(item.get('dictLabel'), item.get('dictValue'))
        return values

    def temp_category(self):
        t = tok(8)
        value = 'smk' + t
        result = post(self.admin, '/system/dict/data', {
            'dictType': CATEGORY_DICT, 'dictLabel': '临时分类' + t, 'dictValue': value, 'dictSort': 99,
            'listClass': 'default', 'isDefault': 'N'})
        if result[0] != 200:
            raise AssertionError(f'新增临时分类失败: {result[0]} {result[1]}')
        item = next((i for i in self.dict_items(CATEGORY_DICT) if i.get('dictValue') == value), None)
        if item is None:
            raise AssertionError(f'新增的临时分类 {value} 在字典中查询不到')
        return value, item['dictCode']

    def remove_category(self, dict_code) -> None:
        self.admin.delete('/system/dict/data/' + str(dict_code))
        if any(str(i.get('dictCode')) == str(dict_code) for i in self.dict_items(CATEGORY_DICT)):
            raise AssertionError('临时分类删除后仍在字典中')

    # ---- 供应商 -----------------------------------------------------------

    def supplier(self, label: str = '原材料', value=None, name: str | None = None) -> dict:
        t = tok()
        code = 'FC' + t
        name = name or self.prefix + '-' + t
        body = {'supplierCode': code, 'supplierName': name, 'status': '0',
                'supplierCategory': value if value is not None else self.categories[label]}
        result = post(self.admin, SUPPLIER_BASE, body)
        if result[0] != 200:
            raise AssertionError(f'准备供应商失败: {result[0]} {result[1]}')
        return self.find_supplier(code, name)

    def supplier_rows(self, name: str) -> list[dict]:
        params = {'supplierName': name, 'pageNum': 1, 'pageSize': BIG_PAGE}
        return list(page_of(self.admin.get(SUPPLIER_BASE + '/list', params))['rows'] or [])

    def find_supplier(self, code: str, name: str) -> dict:
        matches = [r for r in self.supplier_rows(name) if r.get('supplierCode') == code]
        if len(matches) != 1:
            raise AssertionError(f'按名称 {name} 查到编码 {code} 的供应商 {len(matches)} 条')
        return matches[0]

    def supplier_detail(self, row: dict) -> dict:
        return self.admin.get(SUPPLIER_BASE + '/' + str(row['supplierId'])).get('data') or {}

    def change_category(self, row: dict, label: str) -> None:
        body = dict(row)
        body['supplierCategory'] = self.categories[label]
        result = call(self.admin.put, SUPPLIER_BASE, body)
        if result[0] != 200:
            raise AssertionError(f'修改供应商分类失败: {result[0]} {result[1]}')
        if self.supplier_detail(row).get('supplierCategory') != self.categories[label]:
            raise AssertionError('修改后供应商档案上的分类没有变化')

    def delete_supplier(self, row: dict) -> None:
        result = call(self.admin.delete, SUPPLIER_BASE + '/' + str(row['supplierId']))
        if result[0] != 200:
            raise AssertionError(f'删除供应商失败: {result[0]} {result[1]}')
        if any(r.get('supplierCode') == row['supplierCode'] for r in self.supplier_rows(row['supplierName'])):
            raise AssertionError('删除后供应商仍出现在供应商列表中')

    # ---- 采购单 -----------------------------------------------------------

    def rows(self, client=None, extra=None, **filters):
        params = {k: v for k, v in filters.items() if v is not None}
        params.update(extra or {})
        collected, total = [], 0
        for page_num in range(1, 21):
            query = dict(params, pageNum=page_num, pageSize=BIG_PAGE)
            page = page_of((client or self.admin).get(ORDER_BASE + '/list', query))
            batch = list(page['rows'] or [])
            total = int(page['total'])
            collected += batch
            if not batch or len(collected) >= total:
                break
        return collected, total

    def fixture_rows(self, extra=None, **filters):
        rows, total = self.rows(extra=extra, supplierName=self.prefix, **filters)
        return {str(r.get('orderId')): r for r in rows}, total

    def order(self, supplier: dict, order_date: str | None = None) -> dict:
        marker = tok()
        remark = '分类冒烟' + marker
        body = {'supplierId': supplier['supplierId'], 'orderDate': order_date or day(), 'remark': remark,
                'details': [{'materialName': '物料' + marker, 'quantity': 2, 'price': 10}]}
        result = post(self.admin, ORDER_BASE, body)
        if result[0] != 200:
            raise AssertionError(f'准备采购单失败: {result[0]} {result[1]}')
        rows, _ = self.rows(supplierName=supplier['supplierName'])
        matches = [r for r in rows if r.get('remark') == remark]
        if len(matches) != 1:
            raise AssertionError(f'新增后按供应商查到备注为 {remark} 的采购单 {len(matches)} 张')
        return matches[0]

    def submit(self, row: dict) -> None:
        result = call(self.admin.put, ORDER_BASE + '/submit/' + str(row['orderId']))
        if result[0] != 200:
            raise AssertionError(f'提交采购单失败: {result[0]} {result[1]}')

    def export(self, fields=None, client=None):
        '''POST the export form like the frontend does; return (content type, raw bytes).'''
        client = client or self.admin
        data = urllib.parse.urlencode(fields or {}).encode('utf-8')
        headers = {'clientid': client.client_id, 'Authorization': 'Bearer ' + (client.token or ''),
                   'Content-Type': 'application/x-www-form-urlencoded'}
        request = urllib.request.Request(client.base_url + ORDER_BASE + '/export', data=data, headers=headers,
                                         method='POST')
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.headers.get('Content-Type', ''), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.headers.get('Content-Type', ''), exc.read()

    def _build(self) -> None:
        s = {key: self.supplier(label) for key, label in (
            ('raw', '原材料'), ('service', '服务'), ('equip', '设备'),
            ('empty', '原材料'), ('deleted', '原材料'), ('change', '原材料'))}
        value, dict_code = self.temp_category()
        s['invalid'] = self.supplier(value=value)
        o = {key: self.order(s[key]) for key in ('raw', 'equip', 'empty', 'invalid', 'deleted', 'change')}
        o['service_draft'] = self.order(s['service'])
        o['service_submitted'] = self.order(s['service'])
        self.submit(o['service_submitted'])
        clear_category(s['empty']['supplierCode'])
        if self.supplier_detail(s['empty']).get('supplierCategory') not in (None, ''):
            raise AssertionError('置空后供应商档案上仍有分类')
        self.remove_category(dict_code)
        self.delete_supplier(s['deleted'])
        self.change_category(s['change'], '设备')
        self.suppliers, self.orders = s, o
        self.ids = {key: str(row['orderId']) for key, row in o.items()}

    # ---- 供应商分类的展示与筛选（不绑定实现） ------------------------------

    def display(self, row: dict) -> str:
        '''The supplier category a list row shows: the label field, or the dict value translated.'''
        if self._display is None:
            self._display = self._discover_display()
        kind, key = self._display
        value = row.get(key)
        if kind == 'label':
            return str(value or '')
        if value in (None, ''):
            return UNCATEGORIZED
        return self.labels.get(str(value), UNCATEGORIZED)

    def _discover_display(self):
        rows, _ = self.fixture_rows()
        row = rows.get(self.ids['raw'])
        if row is None:
            raise AssertionError('按供应商名称查询不到供应商分类为原材料的采购单')
        extra = {k: v for k, v in row.items() if k not in ORDER_KEYS}
        key = next((k for k, v in extra.items() if v == '原材料'), None)
        if key:
            return 'label', key
        key = next((k for k, v in extra.items() if v == self.categories['原材料']), None)
        if key:
            return 'value', key
        raise AssertionError(f'采购单列表记录中没有供应商分类字段（该单据的供应商分类为原材料）: {row}')

    def cat_param(self) -> str:
        if self._cat_param is None:
            value = self.categories['服务']
            wanted = {self.ids['service_draft'], self.ids['service_submitted']}
            unwanted = {self.ids['raw'], self.ids['equip']}
            for alias in CATEGORY_PARAMS:
                try:
                    rows, _ = self.fixture_rows(extra={alias: value})
                except (ApiError, AssertionError):
                    continue
                if wanted <= set(rows) and not unwanted & set(rows):
                    self._cat_param = alias
                    break
            else:
                raise AssertionError(f'按供应商分类=服务查询时，候选参数 {CATEGORY_PARAMS} 都没有只返回服务类采购单')
        return self._cat_param

    def by_category(self, label: str) -> dict:
        return {self.cat_param(): self.categories[label]}

    def uncategorized(self) -> dict:
        if self._uncategorized is None:
            known = set(self.categories.values())
            values = [v for v in dict.fromkeys(source_candidates() + list(UNCATEGORIZED_VALUES)) if v not in known]
            options = [{self.cat_param(): v} for v in values]
            options += [{flag: v} for flag in UNCATEGORIZED_FLAGS for v in ('true', '1')]
            for params in options:
                try:
                    rows, _ = self.fixture_rows(extra=params)
                except (ApiError, AssertionError):
                    continue
                ids = set(rows)
                if (self.ids['empty'] in ids and self.ids['raw'] not in ids
                        and self.ids['service_draft'] not in ids):
                    self._uncategorized = params
                    break
            else:
                raise AssertionError('没有能筛出供应商分类为空的采购单、且排除分类有效单据的『未分类』查询条件')
        return self._uncategorized


_STATE: dict = {}


def world() -> World:
    if 'error' in _STATE:
        raise AssertionError(_STATE['error'])
    if 'value' not in _STATE:
        try:
            _STATE['value'] = World()
        except AssertionError as exc:
            _STATE['error'] = str(exc)
            raise
    return _STATE['value']


class Case(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.w = world()

    def assert_category(self, rows: dict, key: str, label: str) -> None:
        row = rows.get(self.w.ids[key])
        self.assertIsNotNone(row, f'列表中没有 {key} 采购单')
        self.assertEqual(self.w.display(row), label, row)


class QueryBasicsTest(Case):
    def test_filter_by_order_no_fragment(self):
        w = self.w
        supplier = w.supplier('服务', name='冒烟采购单号' + tok())
        wanted = w.order(supplier)
        other = w.order(supplier)
        number = str(wanted['orderNo'])
        fragment = number[2:]
        self.assertGreaterEqual(len(fragment), 8, f'单号 {number} 不像 PO+日期+流水号')
        rows, total = w.rows(orderNo=fragment)
        self.assertEqual(total, 1, rows)
        self.assertEqual([str(r.get('orderNo')) for r in rows], [number])
        self.assertNotEqual(number, str(other['orderNo']))

    def test_filter_by_draft_status(self):
        w = self.w
        supplier = w.supplier('服务', name='冒烟采购状态' + tok())
        draft = w.order(supplier)
        submitted = w.order(supplier)
        w.submit(submitted)
        rows, _ = w.rows(supplierName=supplier['supplierName'], status=w.draft)
        ids = {str(r.get('orderId')) for r in rows}
        self.assertIn(str(draft['orderId']), ids, rows)
        self.assertNotIn(str(submitted['orderId']), ids, rows)
        for row in rows:
            self.assertEqual(str(row.get('status')), w.draft, row)


class CategoryDisplayTest(Case):
    def test_row_shows_supplier_category_label(self):
        rows, _ = self.w.fixture_rows()
        self.assert_category(rows, 'raw', '原材料')
        self.assert_category(rows, 'service_draft', '服务')
        self.assert_category(rows, 'equip', '设备')

    def test_empty_supplier_category_shows_uncategorized(self):
        rows, _ = self.w.fixture_rows()
        self.assert_category(rows, 'empty', UNCATEGORIZED)

    def test_invalid_supplier_category_shows_uncategorized(self):
        rows, _ = self.w.fixture_rows()
        self.assert_category(rows, 'invalid', UNCATEGORIZED)

    def test_deleted_supplier_keeps_category(self):
        rows, _ = self.w.fixture_rows()
        self.assertIn(self.w.ids['deleted'], rows, '供应商被逻辑删除后采购单不在列表中')
        self.assert_category(rows, 'deleted', '原材料')


class CategoryFilterTest(Case):
    def test_filter_by_service_category(self):
        w = self.w
        params = w.by_category('服务')
        rows, total = w.fixture_rows(extra=params)
        self.assertEqual(set(rows), {w.ids['service_draft'], w.ids['service_submitted']}, rows)
        self.assertEqual(total, 2)
        for row in rows.values():
            self.assertEqual(w.display(row), '服务', row)
        all_rows, all_total = w.rows(extra=params)
        self.assertEqual(len(all_rows), all_total)
        for row in all_rows:
            self.assertEqual(w.display(row), '服务', row)

    def test_filter_uncategorized_excludes_valid_and_deleted_supplier(self):
        w = self.w
        params = w.uncategorized()
        rows, _ = w.fixture_rows(extra=params)
        self.assertIn(w.ids['empty'], rows, '分类为空的单据没有返回')
        self.assertIn(w.ids['invalid'], rows, '分类已失效的单据没有返回')
        self.assertNotIn(w.ids['raw'], rows, '分类为原材料的单据也被返回了')
        self.assertNotIn(w.ids['deleted'], rows, '供应商逻辑删除后其采购单被当成未分类')
        self.assertEqual(set(rows), {w.ids['empty'], w.ids['invalid']}, rows)
        all_rows, _ = w.rows(extra=params)
        for row in all_rows:
            self.assertEqual(w.display(row), UNCATEGORIZED, row)

    def test_changed_supplier_category_is_used(self):
        w = self.w
        rows, _ = w.fixture_rows(extra=w.by_category('设备'))
        self.assertIn(w.ids['change'], rows, '供应商分类改为设备后按设备查询不到其采购单')
        self.assertIn(w.ids['equip'], rows)
        self.assert_category(rows, 'change', '设备')
        raw_rows, _ = w.fixture_rows(extra=w.by_category('原材料'))
        self.assertNotIn(w.ids['change'], raw_rows, '供应商分类修改后仍按原分类筛出')

    def test_deleted_supplier_order_matches_its_category(self):
        w = self.w
        rows, _ = w.fixture_rows(extra=w.by_category('原材料'))
        self.assertIn(w.ids['deleted'], rows, '供应商逻辑删除后按原材料查询不到其采购单')
        self.assertIn(w.ids['raw'], rows)
        for row in rows.values():
            self.assertEqual(w.display(row), '原材料', row)


class ExportTest(Case):
    def test_export_returns_excel(self):
        w = self.w
        ctype, content = w.export({'status': w.submitted})
        self.assertTrue(content, '导出内容为空')
        self.assertTrue(content.startswith(b'PK'), f'导出的不是 Excel: {ctype} {content[:200]!r}')
        rows = read_xlsx(content)
        self.assertGreaterEqual(len(rows), 2, '导出文件没有数据行')

    def test_export_by_service_category(self):
        w = self.w
        params = w.by_category('服务')
        _, total = w.rows(extra=params)
        header, data = read_export(w.export(params))
        cat, number = column(header, '供应商分类'), column(header, '单号')
        self.assertEqual(len(data), total, '导出行数与同条件列表总条数不一致')
        for row in data:
            self.assertEqual(cell_of(row, cat), '服务', row)
        numbers = {cell_of(r, number) for r in data}
        self.assertIn(str(w.orders['service_draft']['orderNo']), numbers)
        self.assertIn(str(w.orders['service_submitted']['orderNo']), numbers)

    def test_export_empty_category_as_uncategorized(self):
        w = self.w
        order_no = str(w.orders['empty']['orderNo'])
        header, data = read_export(w.export({'orderNo': order_no}))
        number, cat = column(header, '单号'), column(header, '供应商分类')
        matches = [r for r in data if cell_of(r, number) == order_no]
        self.assertEqual(len(matches), 1, f'导出文件中单号 {order_no} 的行数不为 1: {data}')
        self.assertEqual(cell_of(matches[0], cat), UNCATEGORIZED)


if __name__ == '__main__':
    unittest.main()
