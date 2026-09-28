package org.dromara.biz.purchase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderExportVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderDetailMapper;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderMapper;
import org.dromara.biz.purchase.service.impl.BizPurchaseOrderServiceImpl;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.exception.ServiceException;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

/**
 * 采购单列表与导出查询条件的既有行为（供应商名称规则变更 FEAT-20260924-002 前锁定）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizPurchaseOrderServiceImplCharacterizationTest {

    private static final String ORDER_BY =
        "ORDER BY order_date DESC,create_time DESC,order_id DESC";

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

    private static BizPurchaseOrderBo bo(String orderNo, String supplierName, String status) {
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setOrderNo(orderNo);
        bo.setSupplierName(supplierName);
        bo.setStatus(status);
        return bo;
    }

    @SuppressWarnings("unchecked")
    private LambdaQueryWrapper<BizPurchaseOrder> pageWrapper(BizPurchaseOrderBo bo) {
        Page<BizPurchaseOrderVo> page = new Page<>(1, 10);
        page.setRecords(new ArrayList<>());
        ArgumentCaptor<Wrapper<BizPurchaseOrder>> captor = ArgumentCaptor.forClass(Wrapper.class);
        when(purchaseOrderMapper.selectVoPage(any(), captor.capture())).thenReturn(page);
        purchaseOrderService.queryPageList(bo, new PageQuery());
        return (LambdaQueryWrapper<BizPurchaseOrder>) captor.getValue();
    }

    @SuppressWarnings("unchecked")
    private LambdaQueryWrapper<BizPurchaseOrder> exportWrapper(BizPurchaseOrderBo bo) {
        ArgumentCaptor<Wrapper<BizPurchaseOrder>> captor = ArgumentCaptor.forClass(Wrapper.class);
        when(purchaseOrderMapper.selectVoList(captor.capture())).thenReturn(new ArrayList<>());
        purchaseOrderService.queryExportList(bo);
        return (LambdaQueryWrapper<BizPurchaseOrder>) captor.getValue();
    }

    private static boolean anyParamContains(LambdaQueryWrapper<BizPurchaseOrder> lqw, String text) {
        // 参数在生成 SQL 片段时才填充
        lqw.getSqlSegment();
        return lqw.getParamNameValuePairs().values().stream()
            .anyMatch(v -> v instanceof String s && s.contains(text));
    }

    @Test
    void noConditionQueriesAllWithDefaultOrder() {
        LambdaQueryWrapper<BizPurchaseOrder> page = pageWrapper(new BizPurchaseOrderBo());
        LambdaQueryWrapper<BizPurchaseOrder> export = exportWrapper(new BizPurchaseOrderBo());

        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : List.of(page, export)) {
            assertThat(lqw.getSqlSegment())
                .doesNotContain("order_no")
                .doesNotContain("supplier_name")
                .doesNotContain("supplier_id =")
                .doesNotContain("status")
                .doesNotContain("order_date >=")
                .doesNotContain("order_date <=")
                .contains(ORDER_BY);
        }
        verifyNoInteractions(supplierService);
    }

    @Test
    void nullOrEmptyOrSpacesOnlySupplierNameAddsNoNameCondition() {
        for (String name : new String[]{null, "", "   "}) {
            LambdaQueryWrapper<BizPurchaseOrder> page = pageWrapper(bo(null, name, null));
            LambdaQueryWrapper<BizPurchaseOrder> export = exportWrapper(bo(null, name, null));
            for (LambdaQueryWrapper<BizPurchaseOrder> lqw : List.of(page, export)) {
                assertThat(lqw.getSqlSegment()).doesNotContain("supplier_name").contains(ORDER_BY);
            }
        }
    }

    @Test
    void supplierNameIsFuzzyMatchOnOrderColumnInPageAndExport() {
        LambdaQueryWrapper<BizPurchaseOrder> page = pageWrapper(bo(null, "钢铁", null));
        LambdaQueryWrapper<BizPurchaseOrder> export = exportWrapper(bo(null, "钢铁", null));

        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : List.of(page, export)) {
            assertThat(lqw.getSqlSegment()).contains("supplier_name").containsIgnoringCase("like");
            assertThat(anyParamContains(lqw, "%钢铁%")).isTrue();
        }
        // 匹配对象是采购单上记录的名称，不查供应商档案
        verifyNoInteractions(supplierService);
    }

    @Test
    void supplierNameKeepsInnerWhitespace() {
        LambdaQueryWrapper<BizPurchaseOrder> lqw = pageWrapper(bo(null, "钢 铁", null));

        assertThat(anyParamContains(lqw, "钢 铁")).isTrue();
    }

    @Test
    void orderNoIsFuzzyAndUntrimmedLikeBefore() {
        LambdaQueryWrapper<BizPurchaseOrder> lqw = pageWrapper(bo("X9", null, null));

        assertThat(lqw.getSqlSegment()).contains("order_no LIKE").doesNotContain("supplier_name");
        assertThat(anyParamContains(lqw, "%X9%")).isTrue();
    }

    @Test
    void allConditionsCombineWithSupplierNameInPageAndExport() {
        BizPurchaseOrderBo pageBo = bo("X9", "钢铁", "1");
        pageBo.setSupplierId(5L);
        pageBo.getParams().put("beginOrderDate", "2026-09-01");
        pageBo.getParams().put("endOrderDate", "2026-09-30");
        BizPurchaseOrderBo exportBo = bo("X9", "钢铁", "1");
        exportBo.setSupplierId(5L);
        exportBo.getParams().put("beginOrderDate", "2026-09-01");
        exportBo.getParams().put("endOrderDate", "2026-09-30");

        LambdaQueryWrapper<BizPurchaseOrder> page = pageWrapper(pageBo);
        LambdaQueryWrapper<BizPurchaseOrder> export = exportWrapper(exportBo);

        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : List.of(page, export)) {
            assertThat(lqw.getSqlSegment())
                .contains("order_no LIKE")
                .contains("supplier_id =")
                .contains("supplier_name")
                .contains("status =")
                .contains("order_date >=")
                .contains("order_date <=")
                .endsWith(ORDER_BY);
            assertThat(lqw.getParamNameValuePairs().values())
                .contains(5L, "1", "2026-09-01", "2026-09-30");
            assertThat(anyParamContains(lqw, "%X9%")).isTrue();
            assertThat(anyParamContains(lqw, "%钢铁%")).isTrue();
        }
        // 列表与导出使用同一套筛选条件
        assertThat(export.getSqlSegment()).isEqualTo(page.getSqlSegment());
    }

    @Test
    void blankDateParamsAreIgnored() {
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.getParams().put("beginOrderDate", " ");
        bo.getParams().put("endOrderDate", "");

        LambdaQueryWrapper<BizPurchaseOrder> lqw = pageWrapper(bo);

        assertThat(lqw.getSqlSegment()).doesNotContain("order_date >=").doesNotContain("order_date <=");
    }

    @Test
    void supplierNameCombinesWithCategoryFilter() {
        when(supplierService.querySupplierIdsByCategory("2")).thenReturn(List.of(21L));
        BizPurchaseOrderBo bo = bo(null, "钢铁", "1");
        bo.setSupplierCategory("2");

        LambdaQueryWrapper<BizPurchaseOrder> lqw = pageWrapper(bo);

        assertThat(lqw.getSqlSegment()).contains("supplier_name").contains("supplier_id IN").contains("status =");
        assertThat(lqw.getParamNameValuePairs().values()).contains(21L, "1");
        verify(supplierService, never()).queryCategorizedSupplierIds();
    }

    @Test
    void pageReturnsRowsAndTotalWithDisplayedSupplierName() {
        BizPurchaseOrderVo vo = new BizPurchaseOrderVo();
        vo.setOrderId(1L);
        vo.setSupplierId(11L);
        vo.setSupplierName("Acme Steel");
        Page<BizPurchaseOrderVo> page = new Page<>(1, 10);
        page.setRecords(List.of(vo));
        page.setTotal(7);
        when(purchaseOrderMapper.selectVoPage(any(), any())).thenReturn(page);
        when(supplierService.queryCategoryLabels(any())).thenReturn(Map.of(11L, "原材料"));

        PageResult<BizPurchaseOrderVo> result = purchaseOrderService.queryPageList(bo(null, "acme", null), new PageQuery());

        assertThat(result.getTotal()).isEqualTo(7);
        assertThat(result.getRows()).extracting(BizPurchaseOrderVo::getSupplierName).containsExactly("Acme Steel");
    }

    @Test
    void exportRowsCopyMainTableFields() {
        BizPurchaseOrderVo vo = new BizPurchaseOrderVo();
        vo.setOrderId(1L);
        vo.setOrderNo("PO202609240001");
        vo.setSupplierId(11L);
        vo.setSupplierName("Acme Steel");
        vo.setOrderDate(LocalDate.of(2026, 9, 24));
        vo.setStatus("1");
        vo.setTotalAmount(new BigDecimal("12.50"));
        vo.setRemark("备注");
        when(purchaseOrderMapper.selectVoList(any())).thenReturn(List.of(vo));
        when(supplierService.queryCategoryLabels(any())).thenReturn(Map.of(11L, "原材料"));

        List<BizPurchaseOrderExportVo> rows = purchaseOrderService.queryExportList(new BizPurchaseOrderBo());

        assertThat(rows).hasSize(1);
        BizPurchaseOrderExportVo row = rows.get(0);
        assertThat(row.getOrderNo()).isEqualTo("PO202609240001");
        assertThat(row.getSupplierName()).isEqualTo("Acme Steel");
        assertThat(row.getSupplierCategoryLabel()).isEqualTo("原材料");
        assertThat(row.getOrderDate()).isEqualTo("2026-09-24");
        assertThat(row.getStatus()).isEqualTo("1");
        assertThat(row.getTotalAmount()).isEqualByComparingTo("12.50");
        assertThat(row.getRemark()).isEqualTo("备注");
    }

    @Test
    void submittedOrderCannotBeDeleted() {
        BizPurchaseOrder order = new BizPurchaseOrder();
        order.setOrderId(1L);
        order.setOrderNo("PO202609240001");
        order.setStatus(BizPurchaseOrderServiceImpl.STATUS_SUBMITTED);
        when(purchaseOrderMapper.selectByIds(any())).thenReturn(List.of(order));

        assertThatThrownBy(() -> purchaseOrderService.deleteWithValidByIds(List.of(1L), true))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("已提交，不能删除");
    }

}
