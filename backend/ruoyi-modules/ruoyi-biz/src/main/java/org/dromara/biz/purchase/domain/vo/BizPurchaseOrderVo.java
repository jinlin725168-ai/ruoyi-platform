package org.dromara.biz.purchase.domain.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.github.linpeilie.annotations.AutoMapper;
import lombok.Data;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 采购单视图对象 biz_purchase_order
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@AutoMapper(target = BizPurchaseOrder.class)
public class BizPurchaseOrderVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 采购单ID
     */
    private Long orderId;

    /**
     * 采购单号
     */
    private String orderNo;

    /**
     * 供应商ID
     */
    private Long supplierId;

    /**
     * 供应商名称
     */
    private String supplierName;

    /**
     * 下单日期
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate orderDate;

    /**
     * 单据状态（0草稿 1已提交）
     */
    private String status;

    /**
     * 合计金额
     */
    private BigDecimal totalAmount;

    /**
     * 备注
     */
    private String remark;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 采购单明细（仅详情接口返回）
     */
    private List<BizPurchaseOrderDetailVo> details;

}
