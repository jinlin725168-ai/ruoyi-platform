package org.dromara.biz.purchase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collection;
import java.util.List;

import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.BizPurchaseOrderDetail;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderDetailBo;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderDetailMapper;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderMapper;
import org.dromara.biz.purchase.service.impl.BizPurchaseOrderServiceImpl;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.constant.SystemConstants;
import org.dromara.common.core.exception.ServiceException;
import org.dromara.common.core.utils.MapstructUtils;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.beans.factory.support.DefaultListableBeanFactory;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;

import cn.hutool.extra.spring.SpringUtil;
import io.github.linpeilie.Converter;

/**
 * 采购单新增、修改、提交的既有行为（备注变更 FEAT-20260928-002 前锁定）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizPurchaseOrderSaveCharacterizationTest {

    @Mock
    private BizPurchaseOrderMapper purchaseOrderMapper;

    @Mock
    private BizPurchaseOrderDetailMapper purchaseOrderDetailMapper;

    @Mock
    private IBizSupplierService supplierService;

    @InjectMocks
    private BizPurchaseOrderServiceImpl purchaseOrderService;

    private MockedStatic<MapstructUtils> mapstruct;

    @BeforeAll
    static void initStatics() {
        // LambdaQueryWrapper 解析列名依赖表信息缓存，纯单元测试里手动初始化
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizPurchaseOrder.class);
        TableInfoHelper.initTableInfo(new MapperBuilderAssistant(new MybatisConfiguration(), ""), BizPurchaseOrderDetail.class);
        // MapstructUtils 类初始化时从 Spring 取 Converter，没有容器时手动提供一个
        try {
            SpringUtil.getBeanFactory();
        } catch (RuntimeException e) {
            DefaultListableBeanFactory factory = new DefaultListableBeanFactory();
            factory.registerSingleton("converter", mock(Converter.class));
            new SpringUtil().postProcessBeanFactory(factory);
        }
    }

    @BeforeEach
    void stubConvert() {
        mapstruct = mockStatic(MapstructUtils.class);
        mapstruct.when(() -> MapstructUtils.convert(any(BizPurchaseOrderBo.class), eq(BizPurchaseOrder.class)))
            .thenAnswer(inv -> toEntity(inv.getArgument(0)));
        when(supplierService.queryById(7L)).thenReturn(supplier(7L, "Acme Steel", SystemConstants.NORMAL));
    }

    @AfterEach
    void closeConvert() {
        mapstruct.close();
    }

    private static BizPurchaseOrder toEntity(BizPurchaseOrderBo bo) {
        BizPurchaseOrder entity = new BizPurchaseOrder();
        entity.setOrderId(bo.getOrderId());
        entity.setOrderNo(bo.getOrderNo());
        entity.setSupplierId(bo.getSupplierId());
        entity.setSupplierName(bo.getSupplierName());
        entity.setOrderDate(bo.getOrderDate());
        entity.setStatus(bo.getStatus());
        entity.setTotalAmount(bo.getTotalAmount());
        entity.setRemark(bo.getRemark());
        return entity;
    }

    private static BizSupplierVo supplier(Long id, String name, String status) {
        BizSupplierVo vo = new BizSupplierVo();
        vo.setSupplierId(id);
        vo.setSupplierName(name);
        vo.setStatus(status);
        return vo;
    }

    private static BizPurchaseOrderDetailBo detail(String name, String quantity, String price) {
        BizPurchaseOrderDetailBo detail = new BizPurchaseOrderDetailBo();
        detail.setMaterialName(name);
        detail.setQuantity(new BigDecimal(quantity));
        detail.setPrice(new BigDecimal(price));
        detail.setAmount(new BigDecimal("999"));
        return detail;
    }

    private static BizPurchaseOrderBo saveBo(Long orderId, String remark) {
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setOrderId(orderId);
        bo.setOrderNo("HACKED");
        bo.setSupplierId(7L);
        bo.setSupplierName("随便填的名称");
        bo.setOrderDate(LocalDate.of(2026, 9, 28));
        bo.setStatus(BizPurchaseOrderServiceImpl.STATUS_SUBMITTED);
        bo.setTotalAmount(new BigDecimal("1"));
        bo.setRemark(remark);
        bo.setDetails(List.of(detail("钢板", "2", "10.005"), detail("螺丝", "3", "1.5")));
        return bo;
    }

    private static BizPurchaseOrder stored(Long orderId, String status, String remark) {
        BizPurchaseOrder order = new BizPurchaseOrder();
        order.setOrderId(orderId);
        order.setOrderNo("PO202609280001");
        order.setStatus(status);
        order.setRemark(remark);
        return order;
    }

    private BizPurchaseOrder capturedUpdate() {
        ArgumentCaptor<BizPurchaseOrder> captor = ArgumentCaptor.forClass(BizPurchaseOrder.class);
        verify(purchaseOrderMapper).updateById(captor.capture());
        return captor.getValue();
    }

    @SuppressWarnings("unchecked")
    private List<BizPurchaseOrderDetail> capturedDetails() {
        ArgumentCaptor<Collection<BizPurchaseOrderDetail>> captor = ArgumentCaptor.forClass(Collection.class);
        verify(purchaseOrderDetailMapper).insertBatch(captor.capture());
        return List.copyOf(captor.getValue());
    }

    @Test
    void insertKeepsRemarkAndGeneratesNoStatusAndAmount() {
        when(purchaseOrderMapper.selectMaxOrderNoByPrefix("PO20260928")).thenReturn("PO202609280004");
        when(purchaseOrderMapper.insert(any(BizPurchaseOrder.class))).thenAnswer(inv -> {
            inv.<BizPurchaseOrder>getArgument(0).setOrderId(100L);
            return 1;
        });
        BizPurchaseOrderBo bo = saveBo(null, "请于月底前送达，外包装需防潮");

        assertThat(purchaseOrderService.insertByBo(bo)).isTrue();

        ArgumentCaptor<BizPurchaseOrder> captor = ArgumentCaptor.forClass(BizPurchaseOrder.class);
        verify(purchaseOrderMapper).insert(captor.capture());
        BizPurchaseOrder add = captor.getValue();
        assertThat(add.getOrderNo()).isEqualTo("PO202609280005");
        assertThat(add.getStatus()).isEqualTo(BizPurchaseOrderServiceImpl.STATUS_DRAFT);
        assertThat(add.getSupplierName()).isEqualTo("Acme Steel");
        assertThat(add.getTotalAmount()).isEqualByComparingTo("24.52");
        assertThat(add.getRemark()).isEqualTo("请于月底前送达，外包装需防潮");
        assertThat(bo.getOrderId()).isEqualTo(100L);
        assertThat(capturedDetails()).extracting(BizPurchaseOrderDetail::getOrderId).containsOnly(100L);
    }

    @Test
    void insertWithoutRemarkStillSaves() {
        when(purchaseOrderMapper.insert(any(BizPurchaseOrder.class))).thenReturn(1);

        assertThat(purchaseOrderService.insertByBo(saveBo(null, null))).isTrue();

        ArgumentCaptor<BizPurchaseOrder> captor = ArgumentCaptor.forClass(BizPurchaseOrder.class);
        verify(purchaseOrderMapper).insert(captor.capture());
        assertThat(captor.getValue().getOrderNo()).isEqualTo("PO202609280001");
        assertThat(captor.getValue().getRemark()).isNull();
    }

    @Test
    void updateDraftOverwritesWithSubmittedRemarkAndKeepsSystemFields() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        when(purchaseOrderMapper.updateById(any(BizPurchaseOrder.class))).thenReturn(1);

        assertThat(purchaseOrderService.updateByBo(saveBo(5L, "R2"))).isTrue();

        BizPurchaseOrder update = capturedUpdate();
        assertThat(update.getOrderId()).isEqualTo(5L);
        assertThat(update.getOrderNo()).isNull();
        assertThat(update.getStatus()).isNull();
        assertThat(update.getSupplierId()).isEqualTo(7L);
        assertThat(update.getSupplierName()).isEqualTo("Acme Steel");
        assertThat(update.getOrderDate()).isEqualTo(LocalDate.of(2026, 9, 28));
        assertThat(update.getTotalAmount()).isEqualByComparingTo("24.52");
        assertThat(update.getRemark()).isEqualTo("R2");
        verify(purchaseOrderDetailMapper).delete(any());
        List<BizPurchaseOrderDetail> details = capturedDetails();
        assertThat(details).extracting(BizPurchaseOrderDetail::getOrderId).containsOnly(5L);
        assertThat(details).extracting(BizPurchaseOrderDetail::getAmount)
            .usingElementComparator(BigDecimal::compareTo)
            .containsExactly(new BigDecimal("20.02"), new BigDecimal("4.50"));
    }

    @Test
    void updateDraftKeepsRemarkVerbatimIncluding500Chars() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        when(purchaseOrderMapper.updateById(any(BizPurchaseOrder.class))).thenReturn(1);
        String remark = " 备注Ab1，".repeat(71) + "尾部三";
        assertThat(remark).hasSize(500);

        purchaseOrderService.updateByBo(saveBo(5L, remark));

        assertThat(capturedUpdate().getRemark()).isEqualTo(remark);
    }

    @Test
    void updateDraftWithEmptyRemarkWritesEmpty() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        when(purchaseOrderMapper.updateById(any(BizPurchaseOrder.class))).thenReturn(1);

        purchaseOrderService.updateByBo(saveBo(5L, ""));

        assertThat(capturedUpdate().getRemark()).isEmpty();
    }

    @Test
    void updateSubmittedOrderIsRejectedWithoutWriting() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_SUBMITTED, "R1"));

        assertThatThrownBy(() -> purchaseOrderService.updateByBo(saveBo(5L, "R2")))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("PO202609280001")
            .hasMessageContaining("已提交，不能修改");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
        verify(purchaseOrderDetailMapper, never()).delete(any());
        verify(purchaseOrderDetailMapper, never()).insertBatch(any());
    }

    @Test
    void updateMissingOrderIsRejected() {
        assertThatThrownBy(() -> purchaseOrderService.updateByBo(saveBo(5L, "R2")))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("不存在");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
    }

    @Test
    void updateWithDisabledSupplierIsRejectedWithoutWriting() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        when(supplierService.queryById(7L)).thenReturn(supplier(7L, "Acme Steel", "1"));

        assertThatThrownBy(() -> purchaseOrderService.updateByBo(saveBo(5L, "R2")))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("已停用");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
    }

    @Test
    void updateWithoutDetailsIsRejectedWithoutWriting() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        BizPurchaseOrderBo bo = saveBo(5L, "R2");
        bo.setDetails(List.of());

        assertThatThrownBy(() -> purchaseOrderService.updateByBo(bo))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("明细不能为空");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
    }

    @Test
    void submitOnlyWritesStatusAndLeavesRemarkUntouched() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_DRAFT, "R1"));
        when(purchaseOrderDetailMapper.selectCount(any())).thenReturn(1L);
        when(purchaseOrderMapper.updateById(any(BizPurchaseOrder.class))).thenReturn(1);

        assertThat(purchaseOrderService.submitById(5L)).isTrue();

        BizPurchaseOrder update = capturedUpdate();
        assertThat(update.getOrderId()).isEqualTo(5L);
        assertThat(update.getStatus()).isEqualTo(BizPurchaseOrderServiceImpl.STATUS_SUBMITTED);
        // 未设置的字段不参与更新，提交不会改动备注
        assertThat(update.getRemark()).isNull();
        assertThat(update.getOrderNo()).isNull();
        assertThat(update.getTotalAmount()).isNull();
    }

    @Test
    void submitSubmittedOrderIsRejected() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(5L, BizPurchaseOrderServiceImpl.STATUS_SUBMITTED, "R1"));

        assertThatThrownBy(() -> purchaseOrderService.submitById(5L))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("已提交，不能提交");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
        verify(purchaseOrderMapper, never()).selectMaxOrderNoByPrefix(anyString());
    }

}
