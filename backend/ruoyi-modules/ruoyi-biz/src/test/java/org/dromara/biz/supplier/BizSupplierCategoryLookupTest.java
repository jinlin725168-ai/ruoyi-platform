package org.dromara.biz.supplier;

import org.dromara.biz.supplier.constant.SupplierConstants;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.mapper.BizSupplierMapper;
import org.dromara.biz.supplier.service.impl.BizSupplierServiceImpl;
import org.dromara.common.core.service.DictService;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 供应商分类查询（供采购单按供应商分类展示与筛选，含已逻辑删除的供应商）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
class BizSupplierCategoryLookupTest {

    @Mock
    private BizSupplierMapper supplierMapper;

    @Mock
    private DictService dictService;

    @InjectMocks
    private BizSupplierServiceImpl supplierService;

    private static BizSupplier supplier(Long id, String category) {
        BizSupplier supplier = new BizSupplier();
        supplier.setSupplierId(id);
        supplier.setSupplierCategory(category);
        return supplier;
    }

    @Test
    void queryCategoryLabelsTranslatesValidAndFallsBackToUncategorized() {
        when(supplierMapper.selectCategoriesIgnoreDeleted(List.of(1L, 2L, 3L, 4L))).thenReturn(List.of(
            supplier(1L, "1"), supplier(2L, null), supplier(3L, ""), supplier(4L, "stale")));
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE)).thenReturn(Map.of("1", "原材料"));

        Map<Long, String> labels = supplierService.queryCategoryLabels(List.of(1L, 2L, 3L, 4L));

        assertThat(labels).containsExactlyInAnyOrderEntriesOf(Map.of(
            1L, "原材料", 2L, "未分类", 3L, "未分类", 4L, "未分类"));
    }

    @Test
    void queryCategoryLabelsSkipsQueryWhenNoSupplier() {
        assertThat(supplierService.queryCategoryLabels(List.of())).isEmpty();
        verify(supplierMapper, never()).selectCategoriesIgnoreDeleted(any());
    }

    @Test
    void querySupplierIdsByCategoryIncludesDeletedSuppliers() {
        when(supplierMapper.selectIdsByCategoriesIgnoreDeleted(Set.of("2"))).thenReturn(List.of(7L, 8L));

        assertThat(supplierService.querySupplierIdsByCategory("2")).containsExactly(7L, 8L);
    }

    @Test
    void queryCategorizedSupplierIdsUsesCurrentDictValues() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE))
            .thenReturn(Map.of("1", "原材料", "2", "服务"));
        when(supplierMapper.selectIdsByCategoriesIgnoreDeleted(Set.of("1", "2"))).thenReturn(List.of(5L));

        assertThat(supplierService.queryCategorizedSupplierIds()).containsExactly(5L);
    }

    @Test
    void queryCategorizedSupplierIdsIsEmptyWhenDictIsEmpty() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE)).thenReturn(Map.of());

        assertThat(supplierService.queryCategorizedSupplierIds()).isEmpty();
        verify(supplierMapper, never()).selectIdsByCategoriesIgnoreDeleted(any());
    }

}
