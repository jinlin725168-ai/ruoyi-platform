-- FEAT-20260921-001 供应商分类：biz_supplier 增加分类列 + 『供应商分类』字典（原材料、服务、设备）
-- 可重复执行：列按 information_schema 判断后再加，字典先删后插
-- 依赖 FEAT-20260918-001 创建的 biz_supplier 表；历史供应商的分类保持为空，不做迁移

-- ----------------------------
-- 供应商表：分类列（存字典值，历史数据为空）
-- ----------------------------
set @biz_supplier_category_exists := (
    select count(*) from information_schema.columns
    where table_schema = database() and table_name = 'biz_supplier' and column_name = 'supplier_category'
);
set @biz_supplier_category_ddl := if(@biz_supplier_category_exists = 0,
    'alter table biz_supplier add column supplier_category varchar(100) default null comment ''供应商分类（字典 biz_supplier_category）'' after supplier_name',
    'select 1');
prepare biz_supplier_category_stmt from @biz_supplier_category_ddl;
execute biz_supplier_category_stmt;
deallocate prepare biz_supplier_category_stmt;

-- ----------------------------
-- 字典：供应商分类
-- ----------------------------
delete from sys_dict_data where dict_type = 'biz_supplier_category';
delete from sys_dict_type where dict_type = 'biz_supplier_category';

insert into sys_dict_type (dict_id, dict_name, dict_type, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770500000000000002, '供应商分类', 'biz_supplier_category', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '供应商分类列表');

insert into sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770600000000000003, 1, '原材料', 'raw_material', 'biz_supplier_category', '', 'primary', 'N', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '原材料供应商');

insert into sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770600000000000004, 2, '服务', 'service', 'biz_supplier_category', '', 'success', 'N', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '服务供应商');

insert into sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770600000000000005, 3, '设备', 'equipment', 'biz_supplier_category', '', 'warning', 'N', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '设备供应商');
