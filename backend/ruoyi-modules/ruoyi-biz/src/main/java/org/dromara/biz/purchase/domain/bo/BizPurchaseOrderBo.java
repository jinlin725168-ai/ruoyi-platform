package org.dromara.biz.purchase.domain.bo;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.github.linpeilie.annotations.AutoMapper;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.common.core.validate.AddGroup;
import org.dromara.common.core.validate.EditGroup;
import org.springframework.format.annotation.DateTimeFormat;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 采购单业务对象 biz_purchase_order
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
@AutoMapper(target = BizPurchaseOrder.class, reverseConvertGenerate = false)
public class BizPurchaseOrderBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 采购单ID
     */
    @NotNull(message = "采购单ID不能为空", groups = {EditGroup.class})
    private Long orderId;

    /**
     * 采购单号（查询条件；新增与修改时由系统生成，提交的值被忽略）
     */
    private String orderNo;

    /**
     * 供应商ID（只能选择启用状态的供应商）
     */
    @NotNull(message = "供应商不能为空", groups = {AddGroup.class, EditGroup.class})
    private Long supplierId;

    /**
     * 供应商名称（查询条件；保存时以供应商档案为准）
     */
    private String supplierName;

    /**
     * 供应商分类（查询条件；字典 biz_supplier_category 的值，__none__ 表示未分类，按供应商档案上的当前分类匹配）
     */
    private String supplierCategory;

    /**
     * 下单日期
     */
    @NotNull(message = "下单日期不能为空", groups = {AddGroup.class, EditGroup.class})
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate orderDate;

    /**
     * 单据状态（查询条件；状态只能由新增与提交接口变更）
     */
    private String status;

    /**
     * 合计金额（由系统按明细金额之和计算，提交的值被忽略）
     */
    private BigDecimal totalAmount;

    /**
     * 备注
     */
    @Size(max = 500, message = "备注长度不能超过500个字符", groups = {AddGroup.class, EditGroup.class})
    private String remark;

    /**
     * 采购单明细
     */
    @Valid
    @NotEmpty(message = "采购单明细不能为空", groups = {AddGroup.class, EditGroup.class})
    private List<BizPurchaseOrderDetailBo> details;

    /**
     * 查询参数（下单日期范围 beginOrderDate / endOrderDate）
     */
    private Map<String, Object> params = new HashMap<>();

}
