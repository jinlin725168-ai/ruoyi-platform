package org.dromara.biz.purchase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.List;

import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderDetailMapper;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderMapper;
import org.dromara.biz.purchase.service.impl.BizPurchaseOrderServiceImpl;
import org.dromara.biz.supplier.service.IBizSupplierService;
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
 * 采购单供应商名称条件：去掉首尾所有空白字符、忽略英文大小写、模糊匹配采购单上记录的名称，列表与导出一致
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizPurchaseOrderSupplierNameConditionTest {

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
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizPurchaseOrder.class);
    }

    private static BizPurchaseOrderBo bo(String name, String status) {
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setSupplierName(name);
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

    private List<LambdaQueryWrapper<BizPurchaseOrder>> pageAndExport(String name, String status) {
        return List.of(pageWrapper(bo(name, status)), exportWrapper(bo(name, status)));
    }

    private static List<Object> params(LambdaQueryWrapper<BizPurchaseOrder> lqw) {
        // 参数在生成 SQL 片段时才填充
        lqw.getSqlSegment();
        return new ArrayList<>(lqw.getParamNameValuePairs().values());
    }

    @Test
    void trimsHalfWidthSpacesAroundName() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport("   Acme   ", null)) {
            assertThat(params(lqw)).contains("%acme%");
        }
    }

    @Test
    void trimsFullWidthSpacesAroundName() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport("　　钢铁　", null)) {
            assertThat(params(lqw)).contains("%钢铁%");
        }
    }

    @Test
    void trimsTabsNewlinesAndMixedWhitespaceAroundName() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport("　\t 钢铁\r\n", null)) {
            assertThat(params(lqw)).contains("%钢铁%");
        }
    }

    @Test
    void matchesOrderSupplierNameIgnoringCase() {
        for (String input : new String[]{"ACME", "acme", "AcMe"}) {
            for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport(input, null)) {
                assertThat(lqw.getSqlSegment()).containsIgnoringCase("lower(supplier_name) like");
                assertThat(params(lqw)).contains("%acme%");
            }
        }
        // 匹配对象是采购单上记录的名称，不查供应商档案
        verify(supplierService, never()).queryList(any());
    }

    @Test
    void keepsInnerWhitespaceAfterTrimAndLowerCase() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport("  Acme Steel\t", null)) {
            assertThat(params(lqw)).contains("%acme steel%");
        }
    }

    @Test
    void whitespaceOnlyNameIsTreatedAsNoNameCondition() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport(" 　\t\r\n ", "1")) {
            assertThat(lqw.getSqlSegment()).doesNotContain("supplier_name").contains("status =");
            assertThat(params(lqw)).containsExactly("1");
        }
    }

    @Test
    void trimmedCaseInsensitiveNameCombinesWithStatus() {
        for (LambdaQueryWrapper<BizPurchaseOrder> lqw : pageAndExport("  aCmE sTeEl　", "1")) {
            assertThat(lqw.getSqlSegment()).containsIgnoringCase("lower(supplier_name) like").contains("status =");
            assertThat(params(lqw)).containsExactlyInAnyOrder("%acme steel%", "1");
        }
    }

}
