package org.dromara.biz.supplier.constant;

/**
 * 供应商常量
 *
 * @author linjin
 * @date 2026-09-21
 */
public interface SupplierConstants {

    /**
     * 供应商分类字典类型
     */
    String CATEGORY_DICT_TYPE = "biz_supplier_category";

    /**
     * 『未分类』查询条件值：匹配分类为空或分类值已不在字典中的供应商
     */
    String CATEGORY_NONE = "__none__";

    /**
     * 分类为空或分类值已不在字典中时显示的名称
     */
    String CATEGORY_NONE_LABEL = "未分类";

}
