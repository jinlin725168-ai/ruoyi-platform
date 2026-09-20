package org.dromara.biz.purchase.domain.vo;

import lombok.Data;
import org.apache.fesod.sheet.annotation.ExcelIgnoreUnannotated;
import org.apache.fesod.sheet.annotation.ExcelProperty;
import org.dromara.common.excel.annotation.ExcelDictFormat;
import org.dromara.common.excel.convert.ExcelDictConvert;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 采购单导出对象 biz_purchase_order
 * <p>
 * 导出只包含主表数据，一张采购单占一行，不含明细行。
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@ExcelIgnoreUnannotated
public class BizPurchaseOrderExportVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 采购单号
     */
    @ExcelProperty(value = "采购单号")
    private String orderNo;

    /**
     * 供应商名称
     */
    @ExcelProperty(value = "供应商")
    private String supplierName;

    /**
     * 下单日期（yyyy-MM-dd）
     */
    @ExcelProperty(value = "下单日期")
    private String orderDate;

    /**
     * 单据状态（0草稿 1已提交）
     */
    @ExcelProperty(value = "状态", converter = ExcelDictConvert.class)
    @ExcelDictFormat(dictType = "biz_purchase_order_status")
    private String status;

    /**
     * 合计金额
     */
    @ExcelProperty(value = "合计金额")
    private BigDecimal totalAmount;

    /**
     * 备注
     */
    @ExcelProperty(value = "备注")
    private String remark;

}
