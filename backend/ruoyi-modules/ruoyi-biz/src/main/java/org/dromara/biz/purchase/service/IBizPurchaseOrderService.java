package org.dromara.biz.purchase.service;

import java.util.Collection;
import java.util.List;

import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderExportVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.mybatis.core.page.PageQuery;

/**
 * 采购单Service接口
 *
 * @author linjin
 * @date 2026-09-20
 */
public interface IBizPurchaseOrderService {

    /**
     * 查询采购单详情（含全部明细）
     *
     * @param orderId 主键
     * @return 采购单详情
     */
    BizPurchaseOrderVo queryById(Long orderId);

    /**
     * 分页查询采购单列表
     *
     * @param bo        查询条件
     * @param pageQuery 分页参数
     * @return 采购单分页列表
     */
    PageResult<BizPurchaseOrderVo> queryPageList(BizPurchaseOrderBo bo, PageQuery pageQuery);

    /**
     * 查询符合条件的采购单导出列表（仅主表数据）
     *
     * @param bo 查询条件
     * @return 采购单导出列表
     */
    List<BizPurchaseOrderExportVo> queryExportList(BizPurchaseOrderBo bo);

    /**
     * 查询可选的供应商（仅启用状态）
     *
     * @return 启用状态的供应商列表
     */
    List<BizSupplierVo> queryEnabledSuppliers();

    /**
     * 新增采购单及其明细，保存后状态为草稿
     *
     * @param bo 采购单
     * @return 是否新增成功
     */
    Boolean insertByBo(BizPurchaseOrderBo bo);

    /**
     * 修改草稿采购单及其明细
     *
     * @param bo 采购单
     * @return 是否修改成功
     */
    Boolean updateByBo(BizPurchaseOrderBo bo);

    /**
     * 提交采购单（草稿变已提交）
     *
     * @param orderId 主键
     * @return 是否提交成功
     */
    Boolean submitById(Long orderId);

    /**
     * 校验并批量删除采购单及其明细
     *
     * @param ids     待删除的主键集合
     * @param isValid 是否进行有效性校验
     * @return 是否删除成功
     */
    Boolean deleteWithValidByIds(Collection<Long> ids, Boolean isValid);
}
