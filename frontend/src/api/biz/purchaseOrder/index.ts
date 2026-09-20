import type { PurchaseOrderForm, PurchaseOrderQuery, PurchaseOrderVO } from '@/api/biz/purchaseOrder/types';
import type { SupplierVO } from '@/api/biz/supplier/types';
import type { PageResult } from '@/api/types';
import type { AxiosPromise } from '@/utils/api-types';
import request from '@/utils/request';

/**
 * 查询采购单列表
 * @param query
 */
export const listPurchaseOrder = (query?: PurchaseOrderQuery): AxiosPromise<PageResult<PurchaseOrderVO>> => {
  return request({
    url: '/biz/purchaseOrder/list',
    method: 'get',
    params: query
  });
};

/**
 * 查询可选供应商列表（仅启用状态）
 */
export const listPurchaseOrderSuppliers = (): AxiosPromise<SupplierVO[]> => {
  return request({
    url: '/biz/purchaseOrder/supplierOptions',
    method: 'get'
  });
};

/**
 * 查询采购单详细（含明细）
 * @param orderId
 */
export const getPurchaseOrder = (orderId: string | number): AxiosPromise<PurchaseOrderVO> => {
  return request({
    url: '/biz/purchaseOrder/' + orderId,
    method: 'get'
  });
};

/**
 * 新增采购单
 * @param data
 */
export const addPurchaseOrder = (data: PurchaseOrderForm) => {
  return request({
    url: '/biz/purchaseOrder',
    method: 'post',
    data: data
  });
};

/**
 * 修改采购单
 * @param data
 */
export const updatePurchaseOrder = (data: PurchaseOrderForm) => {
  return request({
    url: '/biz/purchaseOrder',
    method: 'put',
    data: data
  });
};

/**
 * 提交采购单
 * @param orderId
 */
export const submitPurchaseOrder = (orderId: string | number) => {
  return request({
    url: '/biz/purchaseOrder/submit/' + orderId,
    method: 'put'
  });
};

/**
 * 删除采购单
 * @param orderId
 */
export const delPurchaseOrder = (orderId: string | number | Array<string | number>) => {
  return request({
    url: '/biz/purchaseOrder/' + orderId,
    method: 'delete'
  });
};
