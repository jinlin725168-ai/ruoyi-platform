package org.dromara.biz.purchase.domain;

import java.io.Serial;
import java.math.BigDecimal;
import java.time.LocalDate;

import org.dromara.common.mybatis.core.domain.BaseEntity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 采购单对象 biz_purchase_order
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("biz_purchase_order")
public class BizPurchaseOrder extends BaseEntity {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 采购单ID
     */
    @TableId(value = "order_id")
    private Long orderId;

    /**
     * 采购单号（系统生成，PO + 下单日期 + 当日流水号）
     */
    private String orderNo;

    /**
     * 供应商ID
     */
    private Long supplierId;

    /**
     * 供应商名称（下单时从供应商档案冗余）
     */
    private String supplierName;

    /**
     * 下单日期
     */
    private LocalDate orderDate;

    /**
     * 单据状态（0草稿 1已提交）
     */
    private String status;

    /**
     * 合计金额（明细金额之和）
     */
    private BigDecimal totalAmount;

    /**
     * 备注
     */
    private String remark;

    /**
     * 删除标志（0代表存在 1代表删除）
     */
    @TableLogic
    private String delFlag;

}
