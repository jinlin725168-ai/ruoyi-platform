package org.dromara.biz.supplier.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.domain.R;
import org.dromara.common.core.validate.AddGroup;
import org.dromara.common.core.validate.EditGroup;
import org.dromara.common.excel.utils.ExcelBuilder;
import org.dromara.common.log.annotation.Log;
import org.dromara.common.log.enums.BusinessType;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.dromara.common.redis.annotation.RepeatSubmit;
import org.dromara.common.web.core.BaseController;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 供应商管理
 *
 * @author linjin
 * @date 2026-09-18
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/biz/supplier")
public class BizSupplierController extends BaseController {

    private final IBizSupplierService supplierService;

    /**
     * 查询供应商列表
     */
    @SaCheckPermission("biz:supplier:list")
    @GetMapping("/list")
    public R<PageResult<BizSupplierVo>> list(BizSupplierBo bo, PageQuery pageQuery) {
        return R.ok(supplierService.queryPageList(bo, pageQuery));
    }

    /**
     * 导出供应商列表
     */
    @SaCheckPermission("biz:supplier:export")
    @Log(title = "供应商管理", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(BizSupplierBo bo, HttpServletResponse response) {
        List<BizSupplierVo> list = supplierService.queryList(bo);
        ExcelBuilder.of(list, BizSupplierVo.class).sheetName("供应商").toResponse(response);
    }

    /**
     * 获取供应商详细信息
     *
     * @param supplierId 主键
     */
    @SaCheckPermission("biz:supplier:query")
    @GetMapping("/{supplierId}")
    public R<BizSupplierVo> getInfo(@NotNull(message = "主键不能为空")
                                    @PathVariable Long supplierId) {
        return R.ok(supplierService.queryById(supplierId));
    }

    /**
     * 新增供应商
     */
    @SaCheckPermission("biz:supplier:add")
    @Log(title = "供应商管理", businessType = BusinessType.INSERT)
    @RepeatSubmit()
    @PostMapping()
    public R<Void> add(@Validated(AddGroup.class) @RequestBody BizSupplierBo bo) {
        if (!supplierService.checkCodeUnique(bo)) {
            return R.fail("新增供应商'" + bo.getSupplierCode() + "'失败，供应商编码已存在");
        }
        if (!supplierService.checkCategoryValid(bo)) {
            return R.fail("新增供应商'" + bo.getSupplierCode() + "'失败，供应商分类无效");
        }
        return toAjax(supplierService.insertByBo(bo));
    }

    /**
     * 修改供应商
     */
    @SaCheckPermission("biz:supplier:edit")
    @Log(title = "供应商管理", businessType = BusinessType.UPDATE)
    @RepeatSubmit()
    @PutMapping()
    public R<Void> edit(@Validated(EditGroup.class) @RequestBody BizSupplierBo bo) {
        if (!supplierService.checkCategoryValid(bo)) {
            return R.fail("修改供应商'" + bo.getSupplierName() + "'失败，供应商分类无效");
        }
        return toAjax(supplierService.updateByBo(bo));
    }

    /**
     * 删除供应商
     *
     * @param supplierIds 主键串
     */
    @SaCheckPermission("biz:supplier:remove")
    @Log(title = "供应商管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{supplierIds}")
    public R<Void> remove(@NotEmpty(message = "主键不能为空")
                          @PathVariable Long[] supplierIds) {
        return toAjax(supplierService.deleteWithValidByIds(List.of(supplierIds), true));
    }
}
