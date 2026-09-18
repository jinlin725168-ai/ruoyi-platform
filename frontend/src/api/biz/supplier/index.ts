import type { SupplierForm, SupplierQuery, SupplierVO } from '@/api/biz/supplier/types';
import type { PageResult } from '@/api/types';
import type { AxiosPromise } from '@/utils/api-types';
import request from '@/utils/request';

/**
 * 查询供应商列表
 * @param query
 */
export const listSupplier = (query?: SupplierQuery): AxiosPromise<PageResult<SupplierVO>> => {
  return request({
    url: '/biz/supplier/list',
    method: 'get',
    params: query
  });
};

/**
 * 查询供应商详细
 * @param supplierId
 */
export const getSupplier = (supplierId: string | number): AxiosPromise<SupplierVO> => {
  return request({
    url: '/biz/supplier/' + supplierId,
    method: 'get'
  });
};

/**
 * 新增供应商
 * @param data
 */
export const addSupplier = (data: SupplierForm) => {
  return request({
    url: '/biz/supplier',
    method: 'post',
    data: data
  });
};

/**
 * 修改供应商
 * @param data
 */
export const updateSupplier = (data: SupplierForm) => {
  return request({
    url: '/biz/supplier',
    method: 'put',
    data: data
  });
};

/**
 * 删除供应商
 * @param supplierId
 */
export const delSupplier = (supplierId: string | number | Array<string | number>) => {
  return request({
    url: '/biz/supplier/' + supplierId,
    method: 'delete'
  });
};
