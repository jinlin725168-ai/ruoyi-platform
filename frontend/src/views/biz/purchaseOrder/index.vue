<template>
  <div class="p-2 app-container biz-purchase-order-page">
    <div class="search-wrap">
      <el-card shadow="hover" class="search-panel" :class="{ 'is-collapsed': !showSearch }">
        <template #header>
          <div class="panel-heading search-panel-toggle" @click.stop="showSearch = !showSearch">
            <div>
              <span class="panel-kicker">Search Filters</span>
              <h3>筛选条件</h3>
            </div>
          </div>
        </template>
        <el-form ref="queryFormRef" :model="queryParams" :inline="true" class="query-form">
          <el-form-item label="采购单号" prop="orderNo">
            <el-input v-model="queryParams.orderNo" placeholder="请输入采购单号" clearable @keyup.enter="handleQuery" />
          </el-form-item>
          <el-form-item label="供应商" prop="supplierName">
            <el-input
              v-model="queryParams.supplierName"
              placeholder="请输入供应商名称"
              clearable
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="状态" prop="status">
            <el-select v-model="queryParams.status" placeholder="单据状态" clearable>
              <el-option
                v-for="dict in biz_purchase_order_status"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="下单日期">
            <el-date-picker
              v-model="dateRange"
              value-format="YYYY-MM-DD"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
            <el-button icon="Refresh" @click="resetQuery">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <el-card shadow="hover" class="table-panel">
      <template #header>
        <div class="toolbar-shell">
          <div class="table-heading">
            <span class="panel-kicker">Purchase Order Dataset</span>
            <h3>采购单列表</h3>
            <p>共 {{ total }} 条记录，草稿单据可修改、删除并提交，提交后不可再变更。</p>
          </div>
          <div class="toolbar-actions">
            <el-button v-hasPermi="['biz:purchaseOrder:add']" type="primary" plain icon="Plus" @click="handleAdd">
              新增
            </el-button>
            <el-button
              v-hasPermi="['biz:purchaseOrder:edit']"
              type="success"
              plain
              icon="Edit"
              :disabled="single || !selectedAllDraft"
              @click="handleUpdate()"
            >
              修改
            </el-button>
            <el-button
              v-hasPermi="['biz:purchaseOrder:remove']"
              type="danger"
              plain
              icon="Delete"
              :disabled="multiple || !selectedAllDraft"
              @click="handleDelete()"
            >
              删除
            </el-button>
            <el-button v-hasPermi="['biz:purchaseOrder:export']" type="warning" plain icon="Download" @click="handleExport">
              导出
            </el-button>
            <right-toolbar v-model:show-search="showSearch" :search="false" @query-table="getList"></right-toolbar>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        border
        class="data-table"
        :data="purchaseOrderList"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="采购单号" align="center" prop="orderNo" width="180" />
        <el-table-column label="供应商" align="center" prop="supplierName" :show-overflow-tooltip="true" />
        <el-table-column label="下单日期" align="center" prop="orderDate" width="120" />
        <el-table-column label="状态" align="center" prop="status" width="100">
          <template #default="scope">
            <dict-tag :options="biz_purchase_order_status" :value="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column label="合计金额" align="right" prop="totalAmount" width="120">
          <template #default="scope">{{ formatAmount(scope.row.totalAmount) }}</template>
        </el-table-column>
        <el-table-column label="备注" align="center" prop="remark" :show-overflow-tooltip="true" />
        <el-table-column label="创建时间" align="center" prop="createTime" width="170" />
        <el-table-column label="操作" width="200" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="详情" placement="top">
              <el-button
                v-hasPermi="['biz:purchaseOrder:query']"
                link
                type="primary"
                icon="View"
                @click="handleView(scope.row)"
              ></el-button>
            </el-tooltip>
            <el-tooltip content="修改" placement="top">
              <el-button
                v-hasPermi="['biz:purchaseOrder:edit']"
                link
                type="primary"
                icon="Edit"
                :disabled="!isDraft(scope.row)"
                @click="handleUpdate(scope.row)"
              ></el-button>
            </el-tooltip>
            <el-tooltip content="提交" placement="top">
              <el-button
                v-hasPermi="['biz:purchaseOrder:submit']"
                link
                type="primary"
                icon="Promotion"
                :disabled="!isDraft(scope.row)"
                @click="handleSubmit(scope.row)"
              ></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button
                v-hasPermi="['biz:purchaseOrder:remove']"
                link
                type="primary"
                icon="Delete"
                :disabled="!isDraft(scope.row)"
                @click="handleDelete(scope.row)"
              ></el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        v-model:page="queryParams.pageNum"
        v-model:limit="queryParams.pageSize"
        :total="total"
        @pagination="getList"
      />
    </el-card>

    <!-- 添加或修改采购单对话框 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="900px" append-to-body>
      <el-form ref="purchaseOrderFormRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="16">
          <el-col v-if="form.orderId" :span="12">
            <el-form-item label="采购单号">
              <el-input v-model="form.orderNo" readonly placeholder="由系统自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplierId">
              <div class="supplier-picker">
                <el-input
                  v-model="supplierKeyword"
                  class="supplier-keyword"
                  placeholder="供应商名称"
                  maxlength="100"
                  clearable
                />
                <el-select
                  v-model="form.supplierId"
                  class="supplier-select"
                  placeholder="请选择"
                  @change="handleSupplierChange"
                >
                  <el-option
                    v-for="item in formSupplierOptions"
                    :key="item.supplierId"
                    :label="item.label"
                    :value="item.supplierId"
                    :disabled="item.disabled"
                  />
                </el-select>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="下单日期" prop="orderDate">
              <el-date-picker
                v-model="form.orderDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="请选择下单日期"
                class="w-full"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" maxlength="500" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">采购明细</el-divider>
        <el-row class="mb-2">
          <el-col :span="24">
            <el-button type="primary" plain icon="Plus" @click="handleAddDetail">添加明细</el-button>
          </el-col>
        </el-row>
        <el-table border :data="form.details" class="detail-table">
          <el-table-column label="序号" type="index" width="60" align="center" />
          <el-table-column label="物料名称" prop="materialName">
            <template #default="scope">
              <el-input v-model="scope.row.materialName" placeholder="请输入物料名称" maxlength="200" />
            </template>
          </el-table-column>
          <el-table-column label="数量" prop="quantity" width="160" align="center">
            <template #default="scope">
              <el-input v-model="scope.row.quantity" placeholder="正整数" maxlength="9" />
            </template>
          </el-table-column>
          <el-table-column label="单价" prop="price" width="170" align="center">
            <template #default="scope">
              <el-input v-model="scope.row.price" placeholder="大于0，最多2位小数" maxlength="14" />
            </template>
          </el-table-column>
          <el-table-column label="金额" prop="amount" width="120" align="right">
            <template #default="scope">
              <span class="detail-amount">{{ formatAmount(rowAmount(scope.row)) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="scope">
              <el-button link type="danger" icon="Delete" @click="handleRemoveDetail(scope.$index)"></el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="detail-total">合计金额：<span class="detail-total-value">{{ formatAmount(formTotalAmount) }}</span></div>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button :loading="buttonLoading" type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 采购单详情对话框 -->
    <el-dialog v-model="viewDialog.visible" title="采购单详情" width="900px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="采购单号">{{ viewOrder?.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="供应商">{{ viewOrder?.supplierName }}</el-descriptions-item>
        <el-descriptions-item label="下单日期">{{ viewOrder?.orderDate }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <dict-tag :options="biz_purchase_order_status" :value="viewOrder?.status" />
        </el-descriptions-item>
        <el-descriptions-item label="合计金额">{{ formatAmount(viewOrder?.totalAmount) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ viewOrder?.createTime }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ viewOrder?.remark }}</el-descriptions-item>
      </el-descriptions>
      <el-divider content-position="left">采购明细</el-divider>
      <el-table border :data="viewOrder?.details ?? []">
        <el-table-column label="序号" type="index" width="60" align="center" />
        <el-table-column label="物料名称" prop="materialName" :show-overflow-tooltip="true" />
        <el-table-column label="数量" prop="quantity" width="120" align="center" />
        <el-table-column label="单价" prop="price" width="140" align="right">
          <template #default="scope">{{ formatAmount(scope.row.price) }}</template>
        </el-table-column>
        <el-table-column label="金额" prop="amount" width="140" align="right">
          <template #default="scope">{{ formatAmount(scope.row.amount) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="viewDialog.visible = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="PurchaseOrder" lang="ts">
import {
  addPurchaseOrder,
  delPurchaseOrder,
  getPurchaseOrder,
  listPurchaseOrder,
  listPurchaseOrderSuppliers,
  submitPurchaseOrder,
  updatePurchaseOrder
} from '@/api/biz/purchaseOrder';
import { PurchaseOrderDetailForm, PurchaseOrderForm, PurchaseOrderQuery, PurchaseOrderVO } from '@/api/biz/purchaseOrder/types';
import { SupplierVO } from '@/api/biz/supplier/types';
import { useLoading } from '@/hooks/async/useLoading';
import { useDialogState } from '@/hooks/dialog/useDialogState';
import { useFormDialog } from '@/hooks/dialog/useFormDialog';
import { useDateRangeQuery } from '@/hooks/form/useDateRangeQuery';
import { useSearchReset } from '@/hooks/form/useSearchReset';
import { useSearchToggle } from '@/hooks/form/useSearchToggle';
import { useTableSelection } from '@/hooks/table/useTableSelection';
import modal from '@/plugins/modal';
import { useDict } from '@/utils/dict';
import { download as requestDownload } from '@/utils/request';

/** 草稿状态码值，与后端 biz_purchase_order_status 字典一致 */
const STATUS_DRAFT = '0';

const { biz_purchase_order_status } = toRefs<any>(useDict('biz_purchase_order_status'));

const purchaseOrderList = ref<PurchaseOrderVO[]>([]);
const buttonLoading = ref(false);
const { loading, withLoading } = useLoading(true);
const { showSearch } = useSearchToggle();
const { ids, single, multiple, selectedRows, handleSelectionChange } = useTableSelection<PurchaseOrderVO>((item) => item.orderId);
const total = ref(0);
const { dateRange, applyDateRange, resetDateRange } = useDateRangeQuery('OrderDate');

const queryFormRef = ref<ElFormInstance>();
const purchaseOrderFormRef = ref<ElFormInstance>();

/** 启用状态的供应商候选项 */
const supplierOptions = ref<SupplierVO[]>([]);
/** 编辑时单据自身的供应商已停用，保留一个只读候选项用于回显 */
const staleSupplier = ref<{ supplierId: string | number; supplierName: string } | null>(null);
/** 供应商搜索词：展示当前已选供应商，输入后按名称筛选候选项 */
const supplierKeyword = ref('');

const { dialog: viewDialog, openDialog: openViewDialog } = useDialogState();
const viewOrder = ref<PurchaseOrderVO | null>(null);

const initFormData: PurchaseOrderForm = {
  orderId: undefined,
  orderNo: '',
  supplierId: undefined,
  orderDate: undefined,
  remark: '',
  details: []
};

const data = reactive<PageData<PurchaseOrderForm, PurchaseOrderQuery>>({
  form: { ...initFormData, details: [] },
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    orderNo: undefined,
    supplierName: undefined,
    status: undefined
  },
  rules: {
    supplierId: [{ required: true, message: '供应商不能为空', trigger: 'change' }],
    orderDate: [{ required: true, message: '下单日期不能为空', trigger: 'change' }]
  }
});

const { queryParams, form, rules } = toRefs<PageData<PurchaseOrderForm, PurchaseOrderQuery>>(data);
const { dialog, resetForm, openDialog, showDialog, closeDialog } = useFormDialog({
  form,
  formRef: purchaseOrderFormRef,
  initialFormData: initFormData
});

/** 供应商下拉候选：只列启用供应商，修改时补一个已停用的只读项用于回显 */
const supplierCandidates = computed(() => {
  const options = supplierOptions.value.map((item) => ({
    supplierId: item.supplierId,
    label: item.supplierName,
    disabled: false
  }));
  if (staleSupplier.value) {
    options.unshift({
      supplierId: staleSupplier.value.supplierId,
      label: `${staleSupplier.value.supplierName}（已停用）`,
      disabled: true
    });
  }
  return options;
});

/** 按搜索词筛选候选项，已选中的供应商始终保留，避免下拉回显成原始 ID */
const formSupplierOptions = computed(() => {
  const keyword = supplierKeyword.value.trim();
  if (!keyword) {
    return supplierCandidates.value;
  }
  return supplierCandidates.value.filter(
    (item) => item.label.includes(keyword) || String(item.supplierId) === String(form.value.supplierId)
  );
});

/** 选中供应商后把名称同步到搜索框，作为当前选择的展示 */
const handleSupplierChange = (supplierId?: string | number) => {
  const picked = supplierCandidates.value.find((item) => String(item.supplierId) === String(supplierId));
  supplierKeyword.value = picked?.label ?? '';
};

/** 金额统一展示为 2 位小数 */
const formatAmount = (value?: string | number | null) => {
  const amount = Number(value ?? 0);
  return Number.isNaN(amount) ? '0.00' : amount.toFixed(2);
};

/** 行金额 = 数量 × 单价，与后端计算口径一致 */
const rowAmount = (row: PurchaseOrderDetailForm) => Number(row.quantity ?? 0) * Number(row.price ?? 0);

/** 表单合计金额 = 各行金额之和 */
const formTotalAmount = computed(() =>
  (form.value.details ?? []).reduce((sum, row) => sum + rowAmount(row), 0)
);

/** 是否草稿：只有草稿可以修改、删除和提交 */
const isDraft = (row: Partial<PurchaseOrderVO>) => row?.status === STATUS_DRAFT;

/** 勾选的单据是否全是草稿：已提交的单据不能再修改和删除 */
const selectedAllDraft = computed(
  () => selectedRows.value.length > 0 && selectedRows.value.every((row) => isDraft(row as PurchaseOrderVO))
);

/** 查询采购单列表 */
const getList = async () => {
  await withLoading(async () => {
    const res = await listPurchaseOrder(applyDateRange(queryParams.value));
    purchaseOrderList.value = res.data?.rows;
    total.value = res.data?.total;
  });
};

/** 加载启用状态的供应商候选项 */
const loadSupplierOptions = async () => {
  const res = await listPurchaseOrderSuppliers();
  supplierOptions.value = res.data ?? [];
};

/** 取消按钮 */
const cancel = () => {
  resetForm();
  form.value.details = [];
  supplierKeyword.value = '';
  staleSupplier.value = null;
  closeDialog();
};

/** 搜索按钮操作 */
const handleQuery = () => {
  queryParams.value.pageNum = 1;
  getList();
};

const { resetQuery } = useSearchReset({
  queryFormRef,
  queryParams,
  pageNumKey: 'pageNum',
  pageSizeKey: 'pageSize',
  initialPageSize: 10,
  resetExtras: () => {
    resetDateRange();
  },
  afterReset: () => {
    handleQuery();
  }
});

/** 新增按钮操作 */
const handleAdd = async () => {
  staleSupplier.value = null;
  supplierKeyword.value = '';
  await loadSupplierOptions();
  openDialog('添加采购单');
  form.value.details = [];
  handleAddDetail();
};

/** 修改按钮操作 */
const handleUpdate = async (row?: Partial<PurchaseOrderVO>) => {
  resetForm();
  form.value.details = [];
  staleSupplier.value = null;
  supplierKeyword.value = '';
  const orderId = row?.orderId || ids.value[0];
  const [res] = await Promise.all([getPurchaseOrder(orderId), loadSupplierOptions()]);
  const order = res.data;
  form.value.orderId = order.orderId;
  form.value.orderNo = order.orderNo;
  form.value.supplierId = order.supplierId;
  form.value.orderDate = order.orderDate;
  form.value.remark = order.remark;
  form.value.details = (order.details ?? []).map((detail) => ({
    materialName: detail.materialName,
    quantity: Number(detail.quantity),
    price: Number(detail.price)
  }));
  const enabled = supplierOptions.value.some((item) => String(item.supplierId) === String(order.supplierId));
  if (!enabled && order.supplierId) {
    staleSupplier.value = { supplierId: order.supplierId, supplierName: order.supplierName };
  }
  // 供应商搜索框同时用于回显当前已选供应商
  handleSupplierChange(order.supplierId);
  showDialog('修改采购单');
};

/** 查看详情操作 */
const handleView = async (row: Partial<PurchaseOrderVO>) => {
  const res = await getPurchaseOrder(row.orderId as string | number);
  viewOrder.value = res.data;
  openViewDialog('采购单详情');
};

/** 添加一行明细 */
const handleAddDetail = () => {
  form.value.details.push({ materialName: '', quantity: 1, price: 0 });
};

/** 删除一行明细 */
const handleRemoveDetail = (index: number) => {
  form.value.details.splice(index, 1);
};

/** 明细校验：至少一行，且物料名称、数量、单价均合法 */
const validateDetails = () => {
  const details = form.value.details ?? [];
  if (details.length === 0) {
    modal.msgError('采购单明细不能为空');
    return false;
  }
  for (let i = 0; i < details.length; i++) {
    const detail = details[i];
    const rowNo = i + 1;
    if (!detail.materialName || !detail.materialName.trim()) {
      modal.msgError(`第 ${rowNo} 行物料名称不能为空`);
      return false;
    }
    const quantity = Number(detail.quantity);
    if (!Number.isInteger(quantity) || quantity <= 0) {
      modal.msgError(`第 ${rowNo} 行数量必须是大于 0 的正整数`);
      return false;
    }
    const price = Number(detail.price);
    if (!(price > 0)) {
      modal.msgError(`第 ${rowNo} 行单价必须大于 0`);
      return false;
    }
    if (!/^\d+(\.\d{1,2})?$/.test(String(detail.price).trim())) {
      modal.msgError(`第 ${rowNo} 行单价最多保留 2 位小数`);
      return false;
    }
  }
  return true;
};

/** 提交按钮：单号与金额由后端生成，这里只回传主表字段与明细 */
const submitForm = () => {
  purchaseOrderFormRef.value?.validate(async (valid: boolean) => {
    if (!valid || !validateDetails()) {
      return;
    }
    buttonLoading.value = true;
    const payload: PurchaseOrderForm = {
      orderId: form.value.orderId,
      supplierId: form.value.supplierId,
      orderDate: form.value.orderDate,
      remark: form.value.remark,
      details: form.value.details.map((detail) => ({
        materialName: detail.materialName,
        quantity: Number(detail.quantity),
        price: Number(detail.price)
      }))
    };
    if (payload.orderId) {
      await updatePurchaseOrder(payload).finally(() => (buttonLoading.value = false));
    } else {
      await addPurchaseOrder(payload).finally(() => (buttonLoading.value = false));
    }
    modal.msgSuccess('操作成功');
    closeDialog();
    await getList();
  });
};

/** 提交采购单：草稿变已提交，提交后不可再修改和删除 */
const handleSubmit = async (row: Partial<PurchaseOrderVO>) => {
  await modal.confirm('是否确认提交采购单"' + row.orderNo + '"？提交后将不能再修改和删除。');
  await submitPurchaseOrder(row.orderId as string | number);
  await getList();
  modal.msgSuccess('提交成功');
};

/** 删除按钮操作 */
const handleDelete = async (row?: Partial<PurchaseOrderVO>) => {
  const orderIds = row?.orderId || ids.value;
  const label = row?.orderNo || orderIds;
  await modal.confirm('是否确认删除采购单"' + label + '"的数据项？');
  await delPurchaseOrder(orderIds);
  await getList();
  modal.msgSuccess('删除成功');
};

/** 导出按钮操作：沿用当前查询条件，导出全部匹配的主表数据 */
const handleExport = () => {
  requestDownload(
    'biz/purchaseOrder/export',
    {
      ...applyDateRange(queryParams.value)
    },
    `purchaseOrder_${new Date().getTime()}.xlsx`
  );
};

onMounted(() => {
  getList();
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/components/page-shell' as pageShell;

@include pageShell.table-crud-page;

.detail-total {
  margin-top: 12px;
  text-align: right;
  font-weight: 600;
}

.detail-total-value {
  font-size: 16px;
}
</style>
