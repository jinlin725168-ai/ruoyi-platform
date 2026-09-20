export interface PurchaseOrderDetailVO {
  /**
   * 明细ID
   */
  detailId: string | number;
  /**
   * 采购单ID
   */
  orderId: string | number;
  /**
   * 物料名称
   */
  materialName: string;
  /**
   * 数量
   */
  quantity: number;
  /**
   * 单价
   */
  price: string | number;
  /**
   * 金额（数量×单价）
   */
  amount: string | number;
}

export interface PurchaseOrderVO {
  /**
   * 采购单ID
   */
  orderId: string | number;
  /**
   * 采购单号
   */
  orderNo: string;
  /**
   * 供应商ID
   */
  supplierId: string | number;
  /**
   * 供应商名称
   */
  supplierName: string;
  /**
   * 下单日期
   */
  orderDate: string;
  /**
   * 单据状态（0草稿 1已提交）
   */
  status: string;
  /**
   * 合计金额
   */
  totalAmount: string | number;
  /**
   * 备注
   */
  remark: string;
  /**
   * 创建时间
   */
  createTime: string;
  /**
   * 采购单明细（详情接口返回）
   */
  details?: PurchaseOrderDetailVO[];
}

export interface PurchaseOrderDetailForm {
  /**
   * 物料名称
   */
  materialName?: string;
  /**
   * 数量（大于 0 的正整数）
   */
  quantity?: string | number;
  /**
   * 单价（大于 0，最多 2 位小数）
   */
  price?: string | number;
}

export interface PurchaseOrderForm extends BaseEntity {
  /**
   * 采购单ID
   */
  orderId?: string | number;
  /**
   * 采购单号（系统生成，只读）
   */
  orderNo?: string;
  /**
   * 供应商ID
   */
  supplierId?: string | number;
  /**
   * 下单日期
   */
  orderDate?: string;
  /**
   * 单据状态（0草稿 1已提交）
   */
  status?: string;
  /**
   * 备注
   */
  remark?: string;
  /**
   * 采购单明细
   */
  details: PurchaseOrderDetailForm[];
}

export interface PurchaseOrderQuery extends PageQuery {
  /**
   * 采购单号（模糊匹配）
   */
  orderNo?: string;
  /**
   * 供应商ID
   */
  supplierId?: string | number;
  /**
   * 供应商名称（模糊匹配）
   */
  supplierName?: string;
  /**
   * 单据状态
   */
  status?: string;
  /**
   * 下单日期范围
   */
  params?: Record<string, any>;
}
