package org.dromara.biz.supplier;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.supplier.constant.SupplierConstants;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.mapper.BizSupplierMapper;
import org.dromara.biz.supplier.service.impl.BizSupplierServiceImpl;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.service.DictService;
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

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * 供应商列表与导出查询条件的既有行为（名称规则变更前锁定）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizSupplierServiceImplCharacterizationTest {

    @Mock
    private BizSupplierMapper supplierMapper;

    @Mock
    private DictService dictService;

    @InjectMocks
    private BizSupplierServiceImpl supplierService;

    @BeforeAll
    static void initTableInfo() {
        // LambdaQueryWrapper 解析列名依赖表信息缓存，纯单元测试里手动初始化
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizSupplier.class);
    }

    private static BizSupplierVo supplier(Long id, String category) {
        BizSupplierVo vo = new BizSupplierVo();
        vo.setSupplierId(id);
        vo.setSupplierCategory(category);
        return vo;
    }

    private static BizSupplierBo bo(String name, String status, String category) {
        BizSupplierBo bo = new BizSupplierBo();
        bo.setSupplierName(name);
        bo.setStatus(status);
        bo.setSupplierCategory(category);
        return bo;
    }

    @SuppressWarnings("unchecked")
    private LambdaQueryWrapper<BizSupplier> pageWrapper(BizSupplierBo bo) {
        Page<BizSupplierVo> page = new Page<>(1, 10);
        page.setRecords(new ArrayList<>());
        ArgumentCaptor<Wrapper<BizSupplier>> captor = ArgumentCaptor.forClass(Wrapper.class);
        when(supplierMapper.selectVoPage(any(), captor.capture())).thenReturn(page);
        supplierService.queryPageList(bo, new PageQuery());
        return (LambdaQueryWrapper<BizSupplier>) captor.getValue();
    }

    @SuppressWarnings("unchecked")
    private LambdaQueryWrapper<BizSupplier> listWrapper(BizSupplierBo bo) {
        ArgumentCaptor<Wrapper<BizSupplier>> captor = ArgumentCaptor.forClass(Wrapper.class);
        when(supplierMapper.selectVoList(captor.capture())).thenReturn(new ArrayList<>());
        supplierService.queryList(bo);
        return (LambdaQueryWrapper<BizSupplier>) captor.getValue();
    }

    private static boolean anyParamContains(LambdaQueryWrapper<BizSupplier> lqw, String text) {
        // 参数在生成 SQL 片段时才填充
        lqw.getSqlSegment();
        return lqw.getParamNameValuePairs().values().stream()
            .anyMatch(v -> v instanceof String s && s.contains(text));
    }

    @Test
    void noConditionQueriesAllOrderedByIdDesc() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE)).thenReturn(Map.of());

        LambdaQueryWrapper<BizSupplier> lqw = pageWrapper(new BizSupplierBo());

        assertThat(lqw.getSqlSegment())
            .doesNotContain("supplier_name")
            .doesNotContain("status")
            .doesNotContain("supplier_category")
            .contains("ORDER BY supplier_id DESC");
    }

    @Test
    void nullOrEmptyOrSpacesOnlyNameAddsNoNameCondition() {
        for (String name : new String[]{null, "", "   "}) {
            LambdaQueryWrapper<BizSupplier> page = pageWrapper(bo(name, null, null));
            LambdaQueryWrapper<BizSupplier> list = listWrapper(bo(name, null, null));
            assertThat(page.getSqlSegment()).doesNotContain("supplier_name");
            assertThat(list.getSqlSegment()).doesNotContain("supplier_name");
        }
    }

    @Test
    void nameConditionIsFuzzyOnSupplierNameInPageAndExport() {
        LambdaQueryWrapper<BizSupplier> page = pageWrapper(bo("钢铁", null, null));
        LambdaQueryWrapper<BizSupplier> list = listWrapper(bo("钢铁", null, null));

        for (LambdaQueryWrapper<BizSupplier> lqw : List.of(page, list)) {
            assertThat(lqw.getSqlSegment()).contains("supplier_name").containsIgnoringCase("like");
            assertThat(anyParamContains(lqw, "%钢铁%")).isTrue();
        }
    }

    @Test
    void nameConditionKeepsInnerWhitespace() {
        LambdaQueryWrapper<BizSupplier> lqw = pageWrapper(bo("钢 铁", null, null));

        assertThat(anyParamContains(lqw, "钢 铁")).isTrue();
    }

    @Test
    void statusAndCategoryAreExactMatchesCombinedWithName() {
        LambdaQueryWrapper<BizSupplier> page = pageWrapper(bo("钢铁", "1", "2"));
        LambdaQueryWrapper<BizSupplier> list = listWrapper(bo("钢铁", "1", "2"));

        for (LambdaQueryWrapper<BizSupplier> lqw : List.of(page, list)) {
            assertThat(lqw.getSqlSegment())
                .contains("supplier_name")
                .contains("status =")
                .contains("supplier_category =")
                .contains("ORDER BY supplier_id DESC");
            assertThat(lqw.getParamNameValuePairs().values()).contains("1", "2");
        }
    }

    @Test
    void uncategorizedMatchesEmptyOrStaleCategory() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE))
            .thenReturn(Map.of("1", "原材料", "2", "服务"));

        LambdaQueryWrapper<BizSupplier> lqw = pageWrapper(bo(null, null, SupplierConstants.CATEGORY_NONE));

        assertThat(lqw.getSqlSegment())
            .contains("supplier_category IS NULL")
            .contains("supplier_category NOT IN")
            .doesNotContain("supplier_category = " + SupplierConstants.CATEGORY_NONE);
        assertThat(lqw.getParamNameValuePairs().values()).contains("", "1", "2")
            .doesNotContain(SupplierConstants.CATEGORY_NONE);
    }

    @Test
    void uncategorizedWithEmptyDictAddsNoCategoryCondition() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE)).thenReturn(Map.of());

        LambdaQueryWrapper<BizSupplier> lqw = listWrapper(bo(null, null, SupplierConstants.CATEGORY_NONE));

        assertThat(lqw.getSqlSegment()).doesNotContain("supplier_category");
    }

    @Test
    void pageAndListFillCategoryLabelOrUncategorized() {
        when(dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE)).thenReturn(Map.of("1", "原材料"));
        Page<BizSupplierVo> page = new Page<>(1, 10);
        page.setRecords(List.of(supplier(1L, "1"), supplier(2L, null), supplier(3L, "stale")));
        page.setTotal(3);
        when(supplierMapper.selectVoPage(any(), any())).thenReturn(page);
        when(supplierMapper.selectVoList(any(Wrapper.class)))
            .thenReturn(List.of(supplier(4L, "1"), supplier(5L, ""), supplier(6L, "stale")));

        PageResult<BizSupplierVo> result = supplierService.queryPageList(new BizSupplierBo(), new PageQuery());
        List<BizSupplierVo> list = supplierService.queryList(new BizSupplierBo());

        assertThat(result.getTotal()).isEqualTo(3);
        assertThat(result.getRows()).extracting(BizSupplierVo::getSupplierCategoryLabel)
            .containsExactly("原材料", "未分类", "未分类");
        assertThat(list).extracting(BizSupplierVo::getSupplierCategoryLabel)
            .containsExactly("原材料", "未分类", "未分类");
    }

}
