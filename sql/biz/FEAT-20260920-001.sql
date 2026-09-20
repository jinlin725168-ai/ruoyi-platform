-- FEAT-20260920-001 采购单管理（主子表）：建表 + 单据状态字典 + 『采购单管理』菜单与按钮
-- 可重复执行：表用 if not exists，字典与菜单先删后插
-- 依赖 FEAT-20260918-001 创建的『业务管理』目录（menu_id = 1770000000000000000）与供应商档案

-- ----------------------------
-- 采购单主表
-- ----------------------------
create table if not exists biz_purchase_order (
    order_id          bigint(20)      not null                   comment '采购单ID',
    order_no          varchar(64)     not null                   comment '采购单号（PO+下单日期+当日流水号）',
    supplier_id       bigint(20)      not null                   comment '供应商ID',
    supplier_name     varchar(100)    default null               comment '供应商名称',
    order_date        date            not null                   comment '下单日期',
    status            char(1)         default '0'                comment '单据状态（0草稿 1已提交）',
    total_amount      decimal(16,2)   default 0.00               comment '合计金额（明细金额之和）',
    remark            varchar(500)    default null               comment '备注',
    del_flag          char(1)         default '0'                comment '删除标志（0代表存在 1代表删除）',
    create_dept       bigint(20)      default null               comment '创建部门',
    create_by         bigint(20)      default null               comment '创建者',
    create_time       datetime                                   comment '创建时间',
    update_by         bigint(20)      default null               comment '更新者',
    update_time       datetime                                   comment '更新时间',
    primary key (order_id),
    unique key uk_biz_purchase_order_no (order_no),
    key idx_biz_purchase_order_supplier (supplier_id),
    key idx_biz_purchase_order_date (order_date)
) engine=innodb comment = '采购单表';

-- ----------------------------
-- 采购单明细子表
-- ----------------------------
create table if not exists biz_purchase_order_detail (
    detail_id         bigint(20)      not null                   comment '明细ID',
    order_id          bigint(20)      not null                   comment '采购单ID',
    material_name     varchar(200)    not null                   comment '物料名称',
    quantity          int(11)         not null                   comment '数量（正整数）',
    price             decimal(14,2)   not null                   comment '单价',
    amount            decimal(16,2)   not null                   comment '金额（数量×单价）',
    del_flag          char(1)         default '0'                comment '删除标志（0代表存在 1代表删除）',
    create_dept       bigint(20)      default null               comment '创建部门',
    create_by         bigint(20)      default null               comment '创建者',
    create_time       datetime                                   comment '创建时间',
    update_by         bigint(20)      default null               comment '更新者',
    update_time       datetime                                   comment '更新时间',
    primary key (detail_id),
    key idx_biz_purchase_order_detail_order (order_id)
) engine=innodb comment = '采购单明细表';

-- ----------------------------
-- 字典：采购单状态
-- ----------------------------
delete from sys_dict_data where dict_type = 'biz_purchase_order_status';
delete from sys_dict_type where dict_type = 'biz_purchase_order_status';

insert into sys_dict_type (dict_id, dict_name, dict_type, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770500000000000001, '采购单状态', 'biz_purchase_order_status', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '采购单状态列表');

insert into sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770600000000000001, 1, '草稿', '0', 'biz_purchase_order_status', '', 'info', 'Y', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '草稿');

insert into sys_dict_data (dict_code, dict_sort, dict_label, dict_value, dict_type, css_class, list_class, is_default, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770600000000000002, 2, '已提交', '1', 'biz_purchase_order_status', '', 'success', 'N', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '已提交');

-- ----------------------------
-- 菜单：采购单管理（挂在『业务管理』目录下）
-- ----------------------------
delete from sys_menu where menu_id in (
    1770000000000000010,
    1770000000000000011, 1770000000000000012, 1770000000000000013,
    1770000000000000014, 1770000000000000015, 1770000000000000016
);

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000010, '采购单管理', 1770000000000000000, 2, 'purchaseOrder', 'biz/purchaseOrder/index', '', 'N', 'Y', 'C', '0', '0', 'biz:purchaseOrder:list', 'documentation', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '采购单管理菜单');

-- ----------------------------
-- 按钮：查询/新增/修改/删除/提交/导出
-- ----------------------------
insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000011, '采购单查询', 1770000000000000010, 1, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:query',  '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000012, '采购单新增', 1770000000000000010, 2, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:add',    '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000013, '采购单修改', 1770000000000000010, 3, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:edit',   '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000014, '采购单删除', 1770000000000000010, 4, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:remove', '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000015, '采购单提交', 1770000000000000010, 5, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:submit', '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000016, '采购单导出', 1770000000000000010, 6, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:purchaseOrder:export', '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');
