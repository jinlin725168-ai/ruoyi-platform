package org.dromara.biz.purchase;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderExportVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderDetailMapper;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderMapper;
import org.dromara.biz.purchase.service.impl.BizPurchaseOrderServiceImpl;
import org.dromara.biz.supplier.constant.SupplierConstants;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 采购单按供应商分类展示与筛选（列表与导出）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
class BizPurchaseOrderSupplierCategoryTest {

    @Mock
    private BizPurchaseOrderMapper purchaseOrderMapper;

    @Mock
    private BizPurchaseOrderDetailMapper purchaseOrderDetailMapper;

    @Mock
    private IBizSupplierService supplierService;

    @InjectMocks
    private BizPurchaseOrderServiceImpl purchaseOrderService;

    @BeforeAll
    static void initTableInfo() {
        // LambdaQueryWrapper 解析列名依赖表信息缓存，纯单元测试里手动初始化
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizPurchaseOrder.class);
    }

    private static BizPurchaseOrderVo order(Long orderId, Long supplierId) {
        BizPurchaseOrderVo vo = new BizPurchaseOrderVo();
        vo.setOrderId(orderId);
        vo.setOrderNo("PO202609230000" + orderId);
        vo.setSupplierId(supplierId);
        vo.setStatus("0");
        return vo;
    }

    @SuppressWarnings("unchecked")
    private LambdaQueryWrapper<BizPurchaseOrder> queryPage(BizPurchaseOrderBo bo, List<BizPurchaseOrderVo> rows) {
        Page<BizPurchaseOrderVo> page = new Page<>(1, 10);
        page.setRecords(rows);
        page.setTotal(rows.size());
        ArgumentCaptor<Wrapper<BizPurchaseOrder>> captor = ArgumentCaptor.forClass(Wrapper.class);
        when(purchaseOrderMapper.selectVoPage(any(), captor.capture())).thenReturn(page);
        purchaseOrderService.queryPageList(bo, new PageQuery());
        return (LambdaQueryWrapper<BizPurchaseOrder>) captor.getValue();
    }

    @Test
    void pageRowsShowSupplierCategoryLabelOrUncategorized() {
        BizPurchaseOrderVo raw = order(1L, 11L);
        BizPurchaseOrderVo empty = order(2L, 12L);
        BizPurchaseOrderVo missing = order(3L, 13L);
        when(supplierService.queryCategoryLabels(any())).thenReturn(Map.of(11L, "原材料", 12L, "未分类"));
        Page<BizPurchaseOrderVo> page = new Page<>(1, 10);
        page.setRecords(List.of(raw, empty, missing));
        page.setTotal(3);
        when(purchaseOrderMapper.selectVoPage(any(), any())).thenReturn(page);

        PageResult<BizPurchaseOrderVo> result = purchaseOrderService.queryPageList(new BizPurchaseOrderBo(), new PageQuery());

        assertThat(result.getRows()).extracting(BizPurchaseOrderVo::getSupplierCategoryLabel)
            .containsExactly("原材料", "未分类", "未分类");
    }

    @Test
    void filterBySpecificCategoryKeepsOnlyOrdersOfMatchingSuppliers() {
        when(supplierService.querySupplierIdsByCategory("2")).thenReturn(List.of(21L, 22L));
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierCategory("2");
        bo.setStatus("1");

        LambdaQueryWrapper<BizPurchaseOrder> lqw = queryPage(bo, List.of());

        assertThat(lqw.getSqlSegment()).contains("supplier_id IN").contains("status =");
        assertThat(lqw.getParamNameValuePairs().values()).contains(21L, 22L, "1");
    }

    @Test
    void filterByCategoryWithoutMatchingSupplierReturnsNothing() {
        when(supplierService.querySupplierIdsByCategory("3")).thenReturn(List.of());
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierCategory("3");

        LambdaQueryWrapper<BizPurchaseOrder> lqw = queryPage(bo, List.of());

        assertThat(lqw.getSqlSegment()).contains("1 = 0");
    }

    @Test
    void filterUncategorizedExcludesOrdersOfCategorizedSuppliers() {
        when(supplierService.queryCategorizedSupplierIds()).thenReturn(List.of(31L, 32L));
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierCategory(SupplierConstants.CATEGORY_NONE);

        LambdaQueryWrapper<BizPurchaseOrder> lqw = queryPage(bo, List.of());

        assertThat(lqw.getSqlSegment()).contains("supplier_id NOT IN");
        assertThat(lqw.getParamNameValuePairs().values()).contains(31L, 32L);
        verify(supplierService, never()).querySupplierIdsByCategory(any());
    }

    @Test
    void filterUncategorizedWithoutCategorizedSupplierKeepsAllOrders() {
        when(supplierService.queryCategorizedSupplierIds()).thenReturn(List.of());
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierCategory(SupplierConstants.CATEGORY_NONE);

        LambdaQueryWrapper<BizPurchaseOrder> lqw = queryPage(bo, List.of());

        assertThat(lqw.getSqlSegment()).doesNotContain("supplier_id").doesNotContain("1 = 0");
    }

    @Test
    void noCategoryConditionDoesNotLookUpSuppliers() {
        LambdaQueryWrapper<BizPurchaseOrder> lqw = queryPage(new BizPurchaseOrderBo(), List.of());

        assertThat(lqw.getSqlSegment()).doesNotContain("supplier_id");
        verify(supplierService, never()).querySupplierIdsByCategory(any());
        verify(supplierService, never()).queryCategorizedSupplierIds();
    }

    @Test
    void exportRowsCarrySupplierCategoryLabelUnderSameFilter() {
        when(supplierService.querySupplierIdsByCategory("2")).thenReturn(List.of(41L));
        when(supplierService.queryCategoryLabels(any())).thenReturn(Map.of(41L, "服务"));
        when(purchaseOrderMapper.selectVoList(any())).thenReturn(List.of(order(5L, 41L), order(6L, 42L)));
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierCategory("2");

        List<BizPurchaseOrderExportVo> rows = purchaseOrderService.queryExportList(bo);

        assertThat(rows).extracting(BizPurchaseOrderExportVo::getSupplierCategoryLabel).containsExactly("服务", "未分类");
    }

}
