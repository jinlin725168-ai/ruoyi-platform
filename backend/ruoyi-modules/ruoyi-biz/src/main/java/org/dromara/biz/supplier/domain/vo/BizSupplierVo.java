package org.dromara.biz.supplier.domain.vo;

import io.github.linpeilie.annotations.AutoMapper;
import lombok.Data;
import org.apache.fesod.sheet.annotation.ExcelIgnoreUnannotated;
import org.apache.fesod.sheet.annotation.ExcelProperty;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.common.excel.annotation.ExcelDictFormat;
import org.dromara.common.excel.convert.ExcelDictConvert;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 供应商视图对象 biz_supplier
 *
 * @author linjin
 * @date 2026-09-18
 */
@Data
@ExcelIgnoreUnannotated
@AutoMapper(target = BizSupplier.class)
public class BizSupplierVo implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    /**
     * 供应商ID
     */
    private Long supplierId;

    /**
     * 供应商编码
     */
    @ExcelProperty(value = "供应商编码")
    private String supplierCode;

    /**
     * 供应商名称
     */
    @ExcelProperty(value = "供应商名称")
    private String supplierName;

    /**
     * 供应商分类（字典值）
     */
    private String supplierCategory;

    /**
     * 供应商分类名称（分类为空或已不在字典中时为『未分类』）
     */
    @ExcelProperty(value = "供应商分类")
    private String supplierCategoryLabel;

    /**
     * 联系人
     */
    @ExcelProperty(value = "联系人")
    private String contactName;

    /**
     * 联系电话
     */
    @ExcelProperty(value = "联系电话")
    private String contactPhone;

    /**
     * 状态（0正常 1停用）
     */
    @ExcelProperty(value = "状态", converter = ExcelDictConvert.class)
    @ExcelDictFormat(dictType = "sys_normal_disable")
    private String status;

    /**
     * 备注
     */
    @ExcelProperty(value = "备注")
    private String remark;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

}
