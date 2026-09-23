package org.dromara.biz.supplier;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.mapper.BizSupplierMapper;
import org.dromara.biz.supplier.service.impl.BizSupplierServiceImpl;
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

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

/**
 * 供应商名称条件：去掉首尾所有空白字符、忽略英文大小写，列表与导出一致
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizSupplierNameConditionTest {

    @Mock
    private BizSupplierMapper supplierMapper;

    @Mock
    private DictService dictService;

    @InjectMocks
    private BizSupplierServiceImpl supplierService;

    @BeforeAll
    static void initTableInfo() {
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizSupplier.class);
    }

    private static BizSupplierBo bo(String name, String status) {
        BizSupplierBo bo = new BizSupplierBo();
        bo.setSupplierName(name);
        bo.setStatus(status);
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

    private List<LambdaQueryWrapper<BizSupplier>> pageAndList(String name, String status) {
        return List.of(pageWrapper(bo(name, status)), listWrapper(bo(name, status)));
    }

    private static List<Object> params(LambdaQueryWrapper<BizSupplier> lqw) {
        // 参数在生成 SQL 片段时才填充
        lqw.getSqlSegment();
        return new ArrayList<>(lqw.getParamNameValuePairs().values());
    }

    @Test
    void trimsHalfWidthSpacesAroundName() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("   Acme   ", null)) {
            assertThat(params(lqw)).contains("%acme%");
        }
    }

    @Test
    void trimsFullWidthSpacesAroundName() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("　　钢铁　", null)) {
            assertThat(params(lqw)).contains("%钢铁%");
        }
    }

    @Test
    void trimsTabsNewlinesAndMixedWhitespaceAroundName() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("　\t 钢铁\r\n", null)) {
            assertThat(params(lqw)).contains("%钢铁%");
        }
    }

    @Test
    void matchesNameIgnoringCase() {
        for (String input : new String[]{"ACME", "acme", "AcMe"}) {
            for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(input, null)) {
                assertThat(lqw.getSqlSegment()).containsIgnoringCase("lower(supplier_name) like");
                assertThat(params(lqw)).contains("%acme%");
            }
        }
    }

    @Test
    void keepsInnerWhitespaceAfterTrimAndLowerCase() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("  Acme Steel\t", null)) {
            assertThat(params(lqw)).contains("%acme steel%");
        }
    }

    @Test
    void whitespaceOnlyNameIsTreatedAsNoNameCondition() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(" 　\t\r\n ", "1")) {
            assertThat(lqw.getSqlSegment()).doesNotContain("supplier_name").contains("status =");
            assertThat(params(lqw)).containsExactly("1");
        }
    }

}
