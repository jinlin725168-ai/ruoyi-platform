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
}
