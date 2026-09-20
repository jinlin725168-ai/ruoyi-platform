package org.dromara.biz.purchase.controller;

import cn.dev33.satoken.annotation.SaCheckPermission;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderExportVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.purchase.service.IBizPurchaseOrderService;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
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
 * 采购单管理
 *
 * @author linjin
 * @date 2026-09-20
 */
@Validated
@RequiredArgsConstructor
@RestController
@RequestMapping("/biz/purchaseOrder")
public class BizPurchaseOrderController extends BaseController {

    private final IBizPurchaseOrderService purchaseOrderService;

    /**
     * 查询采购单列表
     */
    @SaCheckPermission("biz:purchaseOrder:list")
    @GetMapping("/list")
    public R<PageResult<BizPurchaseOrderVo>> list(BizPurchaseOrderBo bo, PageQuery pageQuery) {
        return R.ok(purchaseOrderService.queryPageList(bo, pageQuery));
    }

    /**
     * 查询可选供应商列表（仅启用状态）
     */
    @SaCheckPermission("biz:purchaseOrder:list")
    @GetMapping("/supplierOptions")
    public R<List<BizSupplierVo>> supplierOptions() {
        return R.ok(purchaseOrderService.queryEnabledSuppliers());
    }

    /**
     * 导出采购单列表（仅主表数据）
     */
    @SaCheckPermission("biz:purchaseOrder:export")
    @Log(title = "采购单管理", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(BizPurchaseOrderBo bo, HttpServletResponse response) {
        List<BizPurchaseOrderExportVo> list = purchaseOrderService.queryExportList(bo);
        ExcelBuilder.of(list, BizPurchaseOrderExportVo.class).sheetName("采购单").toResponse(response);
    }

    /**
     * 获取采购单详细信息（含全部明细）
     *
     * @param orderId 主键
     */
    @SaCheckPermission("biz:purchaseOrder:query")
    @GetMapping("/{orderId}")
    public R<BizPurchaseOrderVo> getInfo(@NotNull(message = "主键不能为空")
                                         @PathVariable Long orderId) {
        return R.ok(purchaseOrderService.queryById(orderId));
    }

    /**
     * 新增采购单
     */
    @SaCheckPermission("biz:purchaseOrder:add")
    @Log(title = "采购单管理", businessType = BusinessType.INSERT)
    @RepeatSubmit()
    @PostMapping()
    public R<Void> add(@Validated(AddGroup.class) @RequestBody BizPurchaseOrderBo bo) {
        return toAjax(purchaseOrderService.insertByBo(bo));
    }

    /**
     * 修改采购单（仅草稿）
     */
    @SaCheckPermission("biz:purchaseOrder:edit")
    @Log(title = "采购单管理", businessType = BusinessType.UPDATE)
    @RepeatSubmit()
    @PutMapping()
    public R<Void> edit(@Validated(EditGroup.class) @RequestBody BizPurchaseOrderBo bo) {
        return toAjax(purchaseOrderService.updateByBo(bo));
    }

    /**
     * 提交采购单（草稿变已提交）
     *
     * @param orderId 主键
     */
    @SaCheckPermission("biz:purchaseOrder:submit")
    @Log(title = "采购单管理", businessType = BusinessType.UPDATE)
    @RepeatSubmit()
    @PutMapping("/submit/{orderId}")
    public R<Void> submit(@NotNull(message = "主键不能为空")
                          @PathVariable Long orderId) {
        return toAjax(purchaseOrderService.submitById(orderId));
    }

    /**
     * 删除采购单（仅草稿）
     *
     * @param orderIds 主键串
     */
    @SaCheckPermission("biz:purchaseOrder:remove")
    @Log(title = "采购单管理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{orderIds}")
    public R<Void> remove(@NotEmpty(message = "主键不能为空")
                          @PathVariable Long[] orderIds) {
        return toAjax(purchaseOrderService.deleteWithValidByIds(List.of(orderIds), true));
    }
}
