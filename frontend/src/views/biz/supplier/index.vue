<template>
  <div class="p-2 app-container biz-supplier-page">
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
          <el-form-item label="供应商编码" prop="supplierCode">
            <el-input
              v-model="queryParams.supplierCode"
              placeholder="请输入供应商编码"
              clearable
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="供应商名称" prop="supplierName">
            <el-input
              v-model="queryParams.supplierName"
              placeholder="请输入供应商名称"
              clearable
              @keyup.enter="handleQuery"
            />
          </el-form-item>
          <el-form-item label="状态" prop="status">
            <el-select v-model="queryParams.status" placeholder="供应商状态" clearable>
              <el-option v-for="dict in sys_normal_disable" :key="dict.value" :label="dict.label" :value="dict.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="供应商分类" prop="supplierCategory">
            <el-select v-model="queryParams.supplierCategory" placeholder="供应商分类" clearable>
              <el-option v-for="dict in biz_supplier_category" :key="dict.value" :label="dict.label" :value="dict.value" />
              <el-option label="未分类" :value="SUPPLIER_CATEGORY_NONE" />
            </el-select>
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
            <span class="panel-kicker">Supplier Dataset</span>
            <h3>供应商列表</h3>
            <p>共 {{ total }} 条记录，支持供应商档案维护和导出。</p>
          </div>
          <div class="toolbar-actions">
            <el-button v-hasPermi="['biz:supplier:add']" type="primary" plain icon="Plus" @click="handleAdd">新增</el-button>
            <el-button
              v-hasPermi="['biz:supplier:edit']"
              type="success"
              plain
              icon="Edit"
              :disabled="single"
              @click="handleUpdate()"
            >
              修改
            </el-button>
            <el-button
              v-hasPermi="['biz:supplier:remove']"
              type="danger"
              plain
              icon="Delete"
              :disabled="multiple"
              @click="handleDelete()"
            >
              删除
            </el-button>
            <el-button v-hasPermi="['biz:supplier:export']" type="warning" plain icon="Download" @click="handleExport">
              导出
            </el-button>
            <right-toolbar v-model:show-search="showSearch" :search="false" @query-table="getList"></right-toolbar>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" border class="data-table" :data="supplierList" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="供应商编码" align="center" prop="supplierCode" />
        <el-table-column label="供应商名称" align="center" prop="supplierName" :show-overflow-tooltip="true" />
        <el-table-column label="供应商分类" align="center" prop="supplierCategoryLabel" />
        <el-table-column label="联系人" align="center" prop="contactName" />
        <el-table-column label="联系电话" align="center" prop="contactPhone" />
        <el-table-column label="状态" align="center" prop="status">
          <template #default="scope">
            <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
          </template>
        </el-table-column>
        <el-table-column label="备注" align="center" prop="remark" :show-overflow-tooltip="true" />
        <el-table-column label="操作" width="140" align="center" class-name="small-padding fixed-width">
          <template #default="scope">
            <el-tooltip content="修改" placement="top">
              <el-button
                v-hasPermi="['biz:supplier:edit']"
                link
                type="primary"
                icon="Edit"
                @click="handleUpdate(scope.row)"
              ></el-button>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button
                v-hasPermi="['biz:supplier:remove']"
                link
                type="primary"
                icon="Delete"
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

    <!-- 添加或修改供应商对话框 -->
    <el-dialog v-model="dialog.visible" :title="dialog.title" width="500px" append-to-body>
      <el-form ref="supplierFormRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="供应商编码" prop="supplierCode">
          <el-input
            v-model="form.supplierCode"
            placeholder="请输入供应商编码"
            maxlength="64"
            :disabled="!!form.supplierId"
          />
        </el-form-item>
        <el-form-item label="供应商名称" prop="supplierName">
          <el-input v-model="form.supplierName" placeholder="请输入供应商名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="供应商分类" prop="supplierCategory">
          <el-select v-model="form.supplierCategory" placeholder="请选择供应商分类">
            <el-option v-for="dict in biz_supplier_category" :key="dict.value" :label="dict.label" :value="dict.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人" prop="contactName">
          <el-input v-model="form.contactName" placeholder="请输入联系人" maxlength="50" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contactPhone">
          <el-input v-model="form.contactPhone" placeholder="请输入联系电话" maxlength="50" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio v-for="dict in sys_normal_disable" :key="dict.value" :value="dict.value">
              {{ dict.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button :loading="buttonLoading" type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="Supplier" lang="ts">
import { addSupplier, delSupplier, getSupplier, listSupplier, updateSupplier } from '@/api/biz/supplier';
import { SUPPLIER_CATEGORY_NONE, SupplierForm, SupplierQuery, SupplierVO } from '@/api/biz/supplier/types';
import { useLoading } from '@/hooks/async/useLoading';
import { useFormDialog } from '@/hooks/dialog/useFormDialog';
import { useSearchReset } from '@/hooks/form/useSearchReset';
import { useSearchToggle } from '@/hooks/form/useSearchToggle';
import { useTableSelection } from '@/hooks/table/useTableSelection';
import modal from '@/plugins/modal';
import { useDict } from '@/utils/dict';
import { download as requestDownload } from '@/utils/request';

const { sys_normal_disable, biz_supplier_category } = toRefs<any>(useDict('sys_normal_disable', 'biz_supplier_category'));

const supplierList = ref<SupplierVO[]>([]);
const buttonLoading = ref(false);
const { loading, withLoading } = useLoading(true);
const { showSearch } = useSearchToggle();
const { ids, single, multiple, handleSelectionChange } = useTableSelection<SupplierVO>((item) => item.supplierId);
const total = ref(0);

const queryFormRef = ref<ElFormInstance>();
const supplierFormRef = ref<ElFormInstance>();

const initFormData: SupplierForm = {
  supplierId: undefined,
  supplierCode: '',
  supplierName: '',
  supplierCategory: undefined,
  contactName: '',
  contactPhone: '',
  status: '0',
  remark: ''
};

const data = reactive<PageData<SupplierForm, SupplierQuery>>({
  form: { ...initFormData },
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    supplierCode: undefined,
    supplierName: undefined,
    status: undefined,
    supplierCategory: undefined
  },
  rules: {
    supplierCode: [{ required: true, message: '供应商编码不能为空', trigger: 'blur' }],
    supplierName: [{ required: true, message: '供应商名称不能为空', trigger: 'blur' }],
    supplierCategory: [{ required: true, message: '供应商分类不能为空', trigger: 'change' }]
  }
});

const { queryParams, form, rules } = toRefs<PageData<SupplierForm, SupplierQuery>>(data);
const { dialog, resetForm, openDialog, showDialog, closeDialog } = useFormDialog({
  form,
  formRef: supplierFormRef,
  initialFormData: initFormData
});

/** 查询供应商列表 */
const getList = async () => {
  await withLoading(async () => {
    const res = await listSupplier(queryParams.value);
    supplierList.value = res.data?.rows;
    total.value = res.data?.total;
  });
};

/** 取消按钮 */
const cancel = () => {
  resetForm();
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
  afterReset: () => {
    handleQuery();
  }
});

/** 新增按钮操作 */
const handleAdd = () => {
  openDialog('添加供应商');
};

/** 修改按钮操作 */
const handleUpdate = async (row?: Partial<SupplierVO>) => {
  resetForm();
  const supplierId = row?.supplierId || ids.value[0];
  const res = await getSupplier(supplierId);
  Object.assign(form.value, res.data);
  // 分类为空或已不在字典中（显示为『未分类』）时清空，要求重新选择
  if (!biz_supplier_category.value.some((dict: DictDataOption) => dict.value === form.value.supplierCategory)) {
    form.value.supplierCategory = undefined;
  }
  showDialog('修改供应商');
};

/** 提交按钮 */
const submitForm = () => {
  supplierFormRef.value?.validate(async (valid: boolean) => {
    if (valid) {
      buttonLoading.value = true;
      if (form.value.supplierId) {
        await updateSupplier(form.value).finally(() => (buttonLoading.value = false));
      } else {
        await addSupplier(form.value).finally(() => (buttonLoading.value = false));
      }
      modal.msgSuccess('操作成功');
      closeDialog();
      await getList();
    }
  });
};

/** 删除按钮操作 */
const handleDelete = async (row?: Partial<SupplierVO>) => {
  const supplierIds = row?.supplierId || ids.value;
  const label = row?.supplierCode || supplierIds;
  await modal.confirm('是否确认删除供应商"' + label + '"的数据项？');
  await delSupplier(supplierIds);
  await getList();
  modal.msgSuccess('删除成功');
};

/** 导出按钮操作 */
const handleExport = () => {
  requestDownload(
    'biz/supplier/export',
    {
      ...queryParams.value
    },
    `supplier_${new Date().getTime()}.xlsx`
  );
};

onMounted(() => {
  getList();
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/components/page-shell' as pageShell;

@include pageShell.table-crud-page;
</style>
