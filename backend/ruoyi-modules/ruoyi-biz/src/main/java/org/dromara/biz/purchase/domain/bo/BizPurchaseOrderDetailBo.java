package org.dromara.biz.purchase.domain.bo;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;
import org.dromara.common.core.validate.AddGroup;
import org.dromara.common.core.validate.EditGroup;

import java.io.Serial;
import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 采购单明细业务对象 biz_purchase_order_detail
 *
 * @author linjin
 * @date 2026-09-20
 */
@Data
public class BizPurchaseOrderDetailBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 明细ID（修改时以本次提交的明细集合为准，不要求回传）
     */
    private Long detailId;

    /**
     * 物料名称
     */
    @NotBlank(message = "物料名称不能为空", groups = {AddGroup.class, EditGroup.class})
    @Size(max = 200, message = "物料名称长度不能超过200个字符", groups = {AddGroup.class, EditGroup.class})
    private String materialName;

    /**
     * 数量（必须是大于 0 的正整数）
     */
    @NotNull(message = "数量不能为空", groups = {AddGroup.class, EditGroup.class})
    @DecimalMin(value = "0", inclusive = false, message = "数量必须大于0", groups = {AddGroup.class, EditGroup.class})
    @Digits(integer = 9, fraction = 0, message = "数量必须是正整数", groups = {AddGroup.class, EditGroup.class})
    private BigDecimal quantity;

    /**
     * 单价（必须大于 0，最多 2 位小数）
     */
    @NotNull(message = "单价不能为空", groups = {AddGroup.class, EditGroup.class})
    @DecimalMin(value = "0", inclusive = false, message = "单价必须大于0", groups = {AddGroup.class, EditGroup.class})
    @Digits(integer = 10, fraction = 2, message = "单价最多保留2位小数", groups = {AddGroup.class, EditGroup.class})
    private BigDecimal price;

    /**
     * 金额（由系统按数量×单价计算，提交的值被忽略）
     */
    private BigDecimal amount;

}
