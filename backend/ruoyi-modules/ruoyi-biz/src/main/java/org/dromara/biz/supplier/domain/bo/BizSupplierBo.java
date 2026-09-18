package org.dromara.biz.supplier.domain.bo;

import io.github.linpeilie.annotations.AutoMapper;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.common.core.validate.AddGroup;
import org.dromara.common.core.validate.EditGroup;

import java.io.Serial;
import java.io.Serializable;

/**
 * 供应商业务对象 biz_supplier
 *
 * @author linjin
 * @date 2026-09-18
 */
@Data
@AutoMapper(target = BizSupplier.class, reverseConvertGenerate = false)
public class BizSupplierBo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 供应商ID
     */
    @NotNull(message = "供应商ID不能为空", groups = {EditGroup.class})
    private Long supplierId;

    /**
     * 供应商编码（创建后不可修改）
     */
    @NotBlank(message = "供应商编码不能为空", groups = {AddGroup.class})
    @Size(max = 64, message = "供应商编码长度不能超过64个字符", groups = {AddGroup.class})
    private String supplierCode;

    /**
     * 供应商名称
     */
    @NotBlank(message = "供应商名称不能为空", groups = {AddGroup.class, EditGroup.class})
    @Size(max = 100, message = "供应商名称长度不能超过100个字符", groups = {AddGroup.class, EditGroup.class})
    private String supplierName;

    /**
     * 联系人
     */
    @Size(max = 50, message = "联系人长度不能超过50个字符", groups = {AddGroup.class, EditGroup.class})
    private String contactName;

    /**
     * 联系电话（不校验格式）
     */
    @Size(max = 50, message = "联系电话长度不能超过50个字符", groups = {AddGroup.class, EditGroup.class})
    private String contactPhone;

    /**
     * 状态（0正常 1停用）
     */
    @Pattern(regexp = "^[01]?$", message = "状态只能为0或1", groups = {AddGroup.class, EditGroup.class})
    private String status;

    /**
     * 备注
     */
    @Size(max = 500, message = "备注长度不能超过500个字符", groups = {AddGroup.class, EditGroup.class})
    private String remark;

}
