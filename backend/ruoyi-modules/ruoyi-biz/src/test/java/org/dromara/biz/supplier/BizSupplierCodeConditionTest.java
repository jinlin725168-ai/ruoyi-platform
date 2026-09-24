package org.dromara.biz.supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.List;

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

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

/**
 * 供应商编码条件：模糊匹配、去掉首尾所有空白字符、忽略英文大小写，列表与导出一致
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizSupplierCodeConditionTest {

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

    private static BizSupplierBo bo(String code, String name, String status) {
        BizSupplierBo bo = new BizSupplierBo();
        bo.setSupplierCode(code);
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

    private List<LambdaQueryWrapper<BizSupplier>> pageAndList(String code, String name, String status) {
        return List.of(pageWrapper(bo(code, name, status)), listWrapper(bo(code, name, status)));
    }

    private List<LambdaQueryWrapper<BizSupplier>> pageAndList(String code) {
        return pageAndList(code, null, null);
    }

    private static List<Object> params(LambdaQueryWrapper<BizSupplier> lqw) {
        // 参数在生成 SQL 片段时才填充
        lqw.getSqlSegment();
        return new ArrayList<>(lqw.getParamNameValuePairs().values());
    }

    @Test
    void matchesCodeFragmentAsContains() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("b0")) {
            assertThat(lqw.getSqlSegment()).containsIgnoringCase("lower(supplier_code) like");
            assertThat(params(lqw)).contains("%b0%");
        }
    }

    @Test
    void trimsHalfWidthSpacesAroundCode() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("   AB01  ")) {
            assertThat(params(lqw)).contains("%ab01%");
        }
    }

    @Test
    void trimsFullWidthSpaceTabAndNewlineAroundCode() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList("　\tAB01\r\n")) {
            assertThat(params(lqw)).contains("%ab01%");
        }
    }

    @Test
    void matchesCodeIgnoringCase() {
        for (String input : new String[]{"SUP-AB", "sup-ab", "Sup-aB"}) {
            for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(input)) {
                assertThat(lqw.getSqlSegment()).containsIgnoringCase("lower(supplier_code) like");
                assertThat(params(lqw)).contains("%sup-ab%");
            }
        }
    }

    @Test
    void keepsInnerWhitespaceInCode() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(" Ab 01 ")) {
            assertThat(params(lqw)).contains("%ab 01%");
        }
    }

    @Test
    void blankOrWhitespaceOnlyCodeIsTreatedAsNoCodeCondition() {
        for (String input : new String[]{null, "", " 　\t\r\n "}) {
            for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(input, null, "1")) {
                assertThat(lqw.getSqlSegment()).doesNotContain("supplier_code").contains("status =");
                assertThat(params(lqw)).containsExactly("1");
            }
        }
    }

    @Test
    void combinesCodeWithNameAndStatus() {
        for (LambdaQueryWrapper<BizSupplier> lqw : pageAndList(" AB01 ", "Acme", "0")) {
            assertThat(lqw.getSqlSegment())
                .containsIgnoringCase("lower(supplier_code) like")
                .containsIgnoringCase("lower(supplier_name) like")
                .contains("status =");
            assertThat(params(lqw)).contains("%ab01%", "%acme%", "0");
        }
    }

}
