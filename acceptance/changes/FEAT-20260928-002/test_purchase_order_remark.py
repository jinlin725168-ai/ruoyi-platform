'''FEAT-20260928-002 采购单备注：后端接口验收冒烟（独立外部验收）。

核心链路：新增和修改草稿采购单时备注选填，最多 500 个字符（按字符计）；超长时拒绝保存，返回提到备注长度的可读提示，
新增不产生单据，修改不改变单据内容；已提交的单据拒绝修改，备注不变；列表、详情和导出 Excel 的『备注』列返回单据备注，
备注为空时为空白。
数据准备沿用已验收的采购单用例：每张采购单使用独立的新供应商，按采购单上记录的供应商名称定位单据（不依赖备注本身）；
雪花 ID 偶发 Clock moved backwards 时稍等后重试。
'''

from __future__ import annotations

import datetime as dt
import io
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

from ruoyi_client import ApiError, Client

ORDER_BASE = '/biz/purchaseOrder'
SUPPLIER_BASE = '/biz/supplier'
CATEGORY_DICT = 'biz_supplier_category'
STATUS_DICT = 'biz_purchase_order_status'
BIG_PAGE = 200
XLSX_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
MISSING = object()
# 汉字、英文字母和数字混合组成的恰好 500 个字符
MIXED_500 = ('采购备注AbC123xyz交期' * 60)[:500]
TOO_LONG = MIXED_500 + '超'


def tok(size: int = 10) -> str:
    return uuid.uuid4().hex[:size]


def day(offset: int = 0) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


def call(fn, *args, **kwargs):
    '''Run a Client call without asserting the RuoYi code; return (code, msg, payload).'''
    try:
        payload = fn(*args, expect=None, **kwargs)
    except ApiError as exc:
        body = exc.body if isinstance(exc.body, dict) else {}
        return body.get('code', exc.status), str(body.get('msg') or ''), body
    return payload.get('code'), str(payload.get('msg') or ''), payload


def send(fn, *args):
    '''Write call, retrying when the snowflake generator reports Clock moved backwards.'''
    for attempt in range(6):
        result = call(fn, *args)
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


def column(header: list[str], label: str) -> int:
    index = next((i for i, text in enumerate(header) if label in text), None)
    if index is None:
        raise AssertionError(f'导出表头缺少『{label}』列: {header}')
    return index


def remark_column(header: list[str]) -> int:
    index = next((i for i, text in enumerate(header) if text.strip() == '备注'), None)
    if index is None:
        raise AssertionError(f'导出表头没有列标题为『备注』的列: {header}')
    return index


def cell_of(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ''


class World:
    '''Shared context: admin client, the supplier category used for fixtures and the order statuses.'''

    def __init__(self):
        self.admin = Client()
        self.admin.login()
        categories = self.dict_values(CATEGORY_DICT)
        if not categories:
            raise AssertionError('供应商分类字典为空')
        self.category = categories.get('原材料') or next(iter(categories.values()))
        statuses = self.dict_values(STATUS_DICT)
        if '草稿' not in statuses or '已提交' not in statuses:
            raise AssertionError(f'采购单状态字典缺少 草稿/已提交: {statuses}')
        self.draft, self.submitted = str(statuses['草稿']), str(statuses['已提交'])

    def dict_values(self, dict_type: str) -> dict:
        params = {'dictType': dict_type, 'pageNum': 1, 'pageSize': BIG_PAGE}
        values = {}
        for item in page_of(self.admin.get('/system/dict/data/list', params))['rows'] or []:
            values.setdefault(item.get('dictLabel'), item.get('dictValue'))
        return values

    # ---- 供应商 -----------------------------------------------------------

    def supplier(self) -> dict:
        t = tok()
        code, name = 'RM' + t, '备注冒烟' + t
        result = send(self.admin.post, SUPPLIER_BASE, {
            'supplierCode': code, 'supplierName': name, 'status': '0', 'supplierCategory': self.category})
        if result[0] != 200:
            raise AssertionError(f'准备供应商失败: {result[0]} {result[1]}')
        params = {'supplierName': name, 'pageNum': 1, 'pageSize': BIG_PAGE}
        rows = [r for r in page_of(self.admin.get(SUPPLIER_BASE + '/list', params))['rows'] or []
                if r.get('supplierCode') == code]
        if len(rows) != 1:
            raise AssertionError(f'按名称 {name} 查到编码 {code} 的供应商 {len(rows)} 条')
        return rows[0]

    # ---- 采购单 -----------------------------------------------------------

    def rows(self, **filters) -> list[dict]:
        params = dict(filters, pageNum=1, pageSize=BIG_PAGE)
        return list(page_of(self.admin.get(ORDER_BASE + '/list', params))['rows'] or [])

    def orders_of(self, supplier: dict) -> list[dict]:
        return self.rows(supplierName=supplier['supplierName'])

    def create(self, supplier: dict, remark=MISSING):
        body = {'supplierId': supplier['supplierId'], 'orderDate': day(),
                'details': [{'materialName': '备注物料' + tok(6), 'quantity': 2, 'price': 10}]}
        if remark is not MISSING:
            body['remark'] = remark
        return send(self.admin.post, ORDER_BASE, body)

    def placed(self, remark=MISSING, submit: bool = False) -> dict:
        '''A new draft order (optionally submitted) for a brand-new supplier; returns its list row.'''
        supplier = self.supplier()
        code, msg, _ = self.create(supplier, remark)
        if code != 200:
            raise AssertionError(f'新增采购单失败: {code} {msg}')
        rows = self.orders_of(supplier)
        if len(rows) != 1:
            raise AssertionError(f'新增后按供应商 {supplier[chr(115) + "upplierName"] if False else supplier.get("supplierName")} 查到 {len(rows)} 张采购单')
        row = rows[0]
        if submit:
            self.submit(row)
        return row

    def detail(self, order_id) -> dict:
        data = self.admin.get(ORDER_BASE + '/' + str(order_id)).get('data')
        if not isinstance(data, dict):
            raise AssertionError(f'采购单 {order_id} 详情为空')
        return data

    def update(self, order_id, remark=MISSING, price=None):
        '''PUT the order as the edit form does: current header and details, with the given remark.'''
        current = self.detail(order_id)
        details = [{'materialName': d.get('materialName'), 'quantity': d.get('quantity'),
                    'price': price if price is not None else d.get('price')}
                   for d in current.get('details') or []]
        if not details:
            raise AssertionError(f'采购单 {order_id} 详情中没有明细')
        body = {'orderId': current['orderId'], 'supplierId': current['supplierId'],
                'orderDate': str(current.get('orderDate'))[:10], 'details': details}
        if remark is not MISSING:
            body['remark'] = remark
        return send(self.admin.put, ORDER_BASE, body)

    def submit(self, row: dict) -> None:
        result = send(self.admin.put, ORDER_BASE + '/submit/' + str(row['orderId']))
        if result[0] != 200:
            raise AssertionError(f'提交采购单失败: {result[0]} {result[1]}')

    def export(self, fields: dict) -> bytes:
        '''POST the export form like the frontend does; return the raw bytes.'''
        data = urllib.parse.urlencode(fields).encode('utf-8')
        headers = {'clientid': self.admin.client_id, 'Authorization': 'Bearer ' + (self.admin.token or ''),
                   'Content-Type': 'application/x-www-form-urlencoded'}
        request = urllib.request.Request(self.admin.base_url + ORDER_BASE + '/export', data=data,
                                         headers=headers, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            return exc.read()

    def export_row(self, order_no: str):
        '''The exported rows for `order_no` and the index of the 备注 column.'''
        rows = read_xlsx(self.export({'orderNo': order_no}))
        header, data = rows[0], rows[1:]
        number, remark = column(header, '单号'), remark_column(header)
        return [r for r in data if cell_of(r, number) == order_no], remark


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

    def assert_blank(self, value, message: str) -> None:
        self.assertIn(value, (None, ''), message)

    def assert_length_hint(self, msg: str) -> None:
        self.assertIn('备注', msg, f'超长备注的失败提示没有提到备注: {msg!r}')
        self.assertTrue('500' in msg or '长度' in msg or '字符' in msg, f'失败提示没有说明备注长度: {msg!r}')


class RemarkEntryTest(Case):
    def test_A98_add_with_remark_keeps_it(self):
        w = self.w
        remark = '请于月底前送达，外包装需防潮'
        row = w.placed(remark)
        data = w.detail(row['orderId'])
        self.assertEqual(data.get('remark'), remark, data)
        self.assertEqual(str(data.get('status')), w.draft, data)
        self.assertEqual(float(str(data.get('totalAmount'))), 20.0, data)

    def test_A99_add_without_remark(self):
        w = self.w
        row = w.placed()
        data = w.detail(row['orderId'])
        self.assert_blank(data.get('remark'), f'不带备注新增后详情中的备注不为空: {data}')

    def test_A100_add_with_exactly_500_characters(self):
        w = self.w
        self.assertEqual(len(MIXED_500), 500)
        self.assertTrue(any('一' <= ch <= '龥' for ch in MIXED_500))
        self.assertTrue(any(ch.isascii() and ch.isalpha() for ch in MIXED_500))
        self.assertTrue(any(ch.isdigit() for ch in MIXED_500))
        row = w.placed(MIXED_500)
        data = w.detail(row['orderId'])
        self.assertEqual(data.get('remark'), MIXED_500, '恰好 500 个字符的备注没有原样保存')

    def test_A101_add_with_501_characters_rejected(self):
        w = self.w
        self.assertEqual(len(TOO_LONG), 501)
        supplier = w.supplier()
        code, msg, _ = w.create(supplier, TOO_LONG)
        self.assertNotEqual(code, 200, '501 个字符的备注也保存成功了')
        self.assert_length_hint(msg)
        self.assertEqual(w.orders_of(supplier), [], '备注超长被拒绝后系统中仍产生了采购单')

    def test_A102_update_draft_replaces_remark(self):
        w = self.w
        r1, r2 = '原备注' + tok(), '新备注' + tok()
        row = w.placed(r1)
        code, msg, _ = w.update(row['orderId'], r2)
        self.assertEqual(code, 200, msg)
        self.assertEqual(w.detail(row['orderId']).get('remark'), r2)

    def test_A103_update_draft_with_empty_remark_clears_it(self):
        w = self.w
        for label, empty in (('空字符串', ''), ('null', None)):
            with self.subTest(remark=label):
                row = w.placed('待清空备注' + tok())
                code, msg, _ = w.update(row['orderId'], empty)
                self.assertEqual(code, 200, msg)
                data = w.detail(row['orderId'])
                self.assert_blank(data.get('remark'), f'以{label}备注修改后详情中的备注仍不为空: {data}')

    def test_A104_update_draft_with_501_characters_rejected(self):
        w = self.w
        r1 = '保持备注' + tok()
        row = w.placed(r1)
        before = w.detail(row['orderId'])
        code, msg, _ = w.update(row['orderId'], TOO_LONG, price=99)
        self.assertNotEqual(code, 200, '501 个字符的备注修改也保存成功了')
        self.assert_length_hint(msg)
        after = w.detail(row['orderId'])
        self.assertEqual(after.get('remark'), r1, '备注超长被拒绝后单据备注变了')
        self.assertEqual(str(after.get('totalAmount')), str(before.get('totalAmount')), '备注超长被拒绝后合计金额变了')
        self.assertEqual([str(d.get('price')) for d in after.get('details') or []],
                         [str(d.get('price')) for d in before.get('details') or []], '备注超长被拒绝后明细变了')

    def test_A105_submitted_order_remark_cannot_change(self):
        w = self.w
        r1, r2 = '已提交备注' + tok(), '改后备注' + tok()
        row = w.placed(r1, submit=True)
        code, msg, _ = w.update(row['orderId'], r2)
        self.assertNotEqual(code, 200, '已提交的采购单备注被修改成功了')
        self.assertIn('已提交', msg, f'失败提示没有说明单据已提交: {msg!r}')
        data = w.detail(row['orderId'])
        self.assertEqual(data.get('remark'), r1)
        self.assertEqual(str(data.get('status')), w.submitted, data)


class RemarkDisplayTest(Case):
    def test_A107_list_row_returns_remark(self):
        w = self.w
        remark = '列表备注' + tok()
        row = w.placed(remark)
        rows = [r for r in w.rows(orderNo=row['orderNo']) if str(r.get('orderId')) == str(row['orderId'])]
        self.assertEqual(len(rows), 1, f'按单号 {row["orderNo"] if False else row.get("orderNo")} 查询不到该单据')
        self.assertEqual(rows[0].get('remark'), remark, rows[0])

    def test_A108_submitted_detail_returns_remark(self):
        w = self.w
        remark = '详情备注' + tok()
        row = w.placed(remark, submit=True)
        data = w.detail(row['orderId'])
        self.assertEqual(str(data.get('status')), w.submitted, data)
        self.assertEqual(data.get('remark'), remark, data)

    def test_A109_export_has_remark_column(self):
        w = self.w
        remark = '导出备注' + tok()
        row = w.placed(remark)
        matches, index = w.export_row(str(row['orderNo']))
        self.assertEqual(len(matches), 1, f'导出文件中该单号的行数不为 1: {matches}')
        self.assertEqual(cell_of(matches[0], index), remark, matches[0])

    def test_A110_export_empty_remark_cell(self):
        w = self.w
        row = w.placed()
        matches, index = w.export_row(str(row['orderNo']))
        self.assertEqual(len(matches), 1, f'导出文件中该单号的行数不为 1: {matches}')
        self.assertEqual(cell_of(matches[0], index), '', f'无备注单据的备注单元格不为空: {matches[0]}')


if __name__ == '__main__':
    unittest.main()
