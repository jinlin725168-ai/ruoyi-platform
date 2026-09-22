export interface SupplierVO {
  /**
   * 供应商ID
   */
  supplierId: string | number;
  /**
   * 供应商编码
   */
  supplierCode: string;
  /**
   * 供应商名称
   */
  supplierName: string;
  /**
   * 供应商分类（字典 biz_supplier_category 的值）
   */
  supplierCategory: string;
  /**
   * 供应商分类名称（分类为空或已不在字典中时为『未分类』）
   */
  supplierCategoryLabel: string;
  /**
   * 联系人
   */
  contactName: string;
  /**
   * 联系电话
   */
  contactPhone: string;
  /**
   * 状态（0正常 1停用）
   */
  status: string;
  /**
   * 备注
   */
  remark: string;
  /**
   * 创建时间
   */
  createTime: string;
}

export interface SupplierForm extends BaseEntity {
  /**
   * 供应商ID
   */
  supplierId?: string | number;
  /**
   * 供应商编码（创建后不可修改）
   */
  supplierCode?: string;
  /**
   * 供应商名称
   */
  supplierName?: string;
  /**
   * 供应商分类（字典 biz_supplier_category 的值）
   */
  supplierCategory?: string;
  /**
   * 联系人
   */
  contactName?: string;
  /**
   * 联系电话
   */
  contactPhone?: string;
  /**
   * 状态（0正常 1停用）
   */
  status?: string;
  /**
   * 备注
   */
  remark?: string;
}

export interface SupplierQuery extends PageQuery {
  /**
   * 供应商名称（模糊匹配）
   */
  supplierName?: string;
  /**
   * 状态
   */
  status?: string;
  /**
   * 供应商分类（字典值；SUPPLIER_CATEGORY_NONE 表示未分类）
   */
  supplierCategory?: string;
}

/**
 * 『未分类』查询条件值：匹配分类为空或分类值已不在字典中的供应商
 */
export const SUPPLIER_CATEGORY_NONE = '__none__';
