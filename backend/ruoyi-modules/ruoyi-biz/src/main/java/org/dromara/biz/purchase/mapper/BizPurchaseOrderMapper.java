package org.dromara.biz.purchase.mapper;

import org.apache.ibatis.annotations.Param;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.common.mybatis.core.mapper.BaseMapperPlus;

/**
 * 采购单Mapper接口
 *
 * @author linjin
 * @date 2026-09-20
 */
public interface BizPurchaseOrderMapper extends BaseMapperPlus<BizPurchaseOrder, BizPurchaseOrderVo> {

    /**
     * 查询指定前缀下已占用的最大采购单号（含已逻辑删除的单据，保证单号不被复用）
     *
     * @param prefix 单号前缀（PO + 下单日期）
     * @return 最大采购单号，无匹配时返回 null
     */
    String selectMaxOrderNoByPrefix(@Param("prefix") String prefix);

}
