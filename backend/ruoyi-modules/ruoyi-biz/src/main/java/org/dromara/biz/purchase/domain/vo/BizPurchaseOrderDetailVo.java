package org.dromara.biz.purchase.domain.vo;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

import org.dromara.biz.purchase.domain.BizPurchaseOrderDetail;

import io.github.linpeilie.annotations.AutoMapper;
import lombok.Data;

/**
 * 采购单明细视图对象 biz_purchase_order_detail
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@AutoMapper(target = BizPurchaseOrderDetail.class)
public class BizPurchaseOrderDetailVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 明细ID
     */
    private Long detailId;

    /**
     * 采购单ID
     */
    private Long orderId;

    /**
     * 物料名称
     */
    private String materialName;

    /**
     * 数量
     */
    private Integer quantity;

    /**
     * 单价
     */
    private BigDecimal price;

    /**
     * 金额（数量×单价）
     */
    private BigDecimal amount;

}
