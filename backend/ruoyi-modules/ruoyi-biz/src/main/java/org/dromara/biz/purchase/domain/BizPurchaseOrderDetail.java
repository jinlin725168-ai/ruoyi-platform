package org.dromara.biz.purchase.domain;

import java.io.Serial;
import java.math.BigDecimal;

import org.dromara.common.mybatis.core.domain.BaseEntity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 采购单明细对象 biz_purchase_order_detail
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("biz_purchase_order_detail")
public class BizPurchaseOrderDetail extends BaseEntity {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 明细ID
     */
    @TableId(value = "detail_id")
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
     * 数量（正整数）
     */
    private Integer quantity;

    /**
     * 单价
     */
    private BigDecimal price;

    /**
     * 金额（数量×单价，由系统计算）
     */
    private BigDecimal amount;

    /**
     * 删除标志（0代表存在 1代表删除）
     */
    @TableLogic
    private String delFlag;

}
