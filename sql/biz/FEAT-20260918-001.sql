-- FEAT-20260918-001 供应商管理：建表 + 『业务管理』目录 + 『供应商管理』菜单与按钮
-- 可重复执行：表用 if not exists，菜单先删后插

-- ----------------------------
-- 供应商表
-- ----------------------------
create table if not exists biz_supplier (
    supplier_id       bigint(20)      not null                   comment '供应商ID',
    supplier_code     varchar(64)     not null                   comment '供应商编码',
    supplier_name     varchar(100)    not null                   comment '供应商名称',
    contact_name      varchar(50)     default null               comment '联系人',
    contact_phone     varchar(50)     default null               comment '联系电话',
    status            char(1)         default '0'                comment '状态（0正常 1停用）',
    remark            varchar(500)    default null               comment '备注',
    del_flag          char(1)         default '0'                comment '删除标志（0代表存在 1代表删除）',
    create_dept       bigint(20)      default null               comment '创建部门',
    create_by         bigint(20)      default null               comment '创建者',
    create_time       datetime                                   comment '创建时间',
    update_by         bigint(20)      default null               comment '更新者',
    update_time       datetime                                   comment '更新时间',
    primary key (supplier_id),
    key idx_biz_supplier_code (supplier_code),
    key idx_biz_supplier_name (supplier_name)
) engine=innodb comment = '供应商表';

-- ----------------------------
-- 菜单：业务管理（目录，由第一个业务变更创建）
-- ----------------------------
delete from sys_menu where menu_id in (
    1770000000000000000,
    1770000000000000001, 1770000000000000002, 1770000000000000003,
    1770000000000000004, 1770000000000000005, 1770000000000000006
);

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000000, '业务管理', 0, 10, 'biz', null, '', 'N', 'Y', 'M', '0', '0', '', 'guide', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '业务管理目录');

-- ----------------------------
-- 菜单：供应商管理
-- ----------------------------
insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000001, '供应商管理', 1770000000000000000, 1, 'supplier', 'biz/supplier/index', '', 'N', 'Y', 'C', '0', '0', 'biz:supplier:list', 'shopping', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '供应商管理菜单');

-- ----------------------------
-- 按钮：查询/新增/修改/删除/导出
-- ----------------------------
insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000002, '供应商查询', 1770000000000000001, 1, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:supplier:query',  '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000003, '供应商新增', 1770000000000000001, 2, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:supplier:add',    '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000004, '供应商修改', 1770000000000000001, 3, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:supplier:edit',   '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000005, '供应商删除', 1770000000000000001, 4, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:supplier:remove', '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');

insert into sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query_param, is_frame, is_cache, menu_type, visible, status, perms, icon, active_menu, ext, create_dept, create_by, create_time, update_by, update_time, remark)
values(1770000000000000006, '供应商导出', 1770000000000000001, 5, '#', '', '', 'N', 'Y', 'F', '0', '0', 'biz:supplier:export', '#', '', '', 1761000000000000103, 1761100000000000001, sysdate(), null, null, '');
