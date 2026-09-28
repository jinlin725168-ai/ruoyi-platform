package org.dromara.biz.purchase;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.mockStatic;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Set;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;

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
import org.dromara.common.core.validate.AddGroup;
import org.dromara.common.core.validate.EditGroup;
import org.junit.jupiter.api.AfterAll;
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
 * 采购单备注：修改草稿时以本次提交的备注为准，长度按字符数限制 500（FEAT-20260928-002）
 */
@Tag("dev")
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class BizPurchaseOrderRemarkTest {

    private static final String REMARK_500 = "备注Ab1，".repeat(83) + "尾部";

    private static ValidatorFactory validatorFactory;

    private static Validator validator;

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
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    @BeforeEach
    void stubConvert() {
        mapstruct = mockStatic(MapstructUtils.class);
        mapstruct.when(() -> MapstructUtils.convert(any(BizPurchaseOrderBo.class), eq(BizPurchaseOrder.class)))
            .thenAnswer(inv -> toEntity(inv.getArgument(0)));
        BizSupplierVo supplier = new BizSupplierVo();
        supplier.setSupplierId(7L);
        supplier.setSupplierName("Acme Steel");
        supplier.setStatus(SystemConstants.NORMAL);
        when(supplierService.queryById(7L)).thenReturn(supplier);
        when(purchaseOrderMapper.updateById(any(BizPurchaseOrder.class))).thenReturn(1);
    }

    @AfterEach
    void closeConvert() {
        mapstruct.close();
    }

    private static BizPurchaseOrder toEntity(BizPurchaseOrderBo bo) {
        BizPurchaseOrder entity = new BizPurchaseOrder();
        entity.setOrderId(bo.getOrderId());
        entity.setSupplierId(bo.getSupplierId());
        entity.setOrderDate(bo.getOrderDate());
        entity.setRemark(bo.getRemark());
        return entity;
    }

    private static BizPurchaseOrder stored(String status) {
        BizPurchaseOrder order = new BizPurchaseOrder();
        order.setOrderId(5L);
        order.setOrderNo("PO202609280001");
        order.setStatus(status);
        order.setRemark("R1");
        return order;
    }

    private static BizPurchaseOrderBo editBo(String remark) {
        BizPurchaseOrderDetailBo detail = new BizPurchaseOrderDetailBo();
        detail.setMaterialName("钢板");
        detail.setQuantity(new BigDecimal("2"));
        detail.setPrice(new BigDecimal("10"));
        BizPurchaseOrderBo bo = new BizPurchaseOrderBo();
        bo.setOrderId(5L);
        bo.setSupplierId(7L);
        bo.setOrderDate(LocalDate.of(2026, 9, 28));
        bo.setRemark(remark);
        bo.setDetails(List.of(detail));
        return bo;
    }

    private BizPurchaseOrder capturedUpdate() {
        ArgumentCaptor<BizPurchaseOrder> captor = ArgumentCaptor.forClass(BizPurchaseOrder.class);
        verify(purchaseOrderMapper).updateById(captor.capture());
        return captor.getValue();
    }

    private static Set<ConstraintViolation<BizPurchaseOrderBo>> validateRemark(String remark, Class<?> group) {
        return validator.validateValue(BizPurchaseOrderBo.class, "remark", remark, group);
    }

    @Test
    void updateDraftWithoutRemarkClearsStoredRemark() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(BizPurchaseOrderServiceImpl.STATUS_DRAFT));

        assertThat(purchaseOrderService.updateByBo(editBo(null))).isTrue();

        // 空值字段不参与 updateById，必须写成空串才能覆盖原备注
        assertThat(capturedUpdate().getRemark()).isNotNull().isEmpty();
    }

    @Test
    void updateDraftWritesSubmittedRemark() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(BizPurchaseOrderServiceImpl.STATUS_DRAFT));

        purchaseOrderService.updateByBo(editBo("R2"));

        assertThat(capturedUpdate().getRemark()).isEqualTo("R2");
    }

    @Test
    void updateDraftKeeps500CharRemarkVerbatim() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(BizPurchaseOrderServiceImpl.STATUS_DRAFT));
        assertThat(REMARK_500).hasSize(500);

        purchaseOrderService.updateByBo(editBo(REMARK_500));

        assertThat(capturedUpdate().getRemark()).isEqualTo(REMARK_500);
    }

    @Test
    void updateSubmittedOrderWithNewRemarkIsRejected() {
        when(purchaseOrderMapper.selectById(5L)).thenReturn(stored(BizPurchaseOrderServiceImpl.STATUS_SUBMITTED));

        assertThatThrownBy(() -> purchaseOrderService.updateByBo(editBo(null)))
            .isInstanceOf(ServiceException.class)
            .hasMessageContaining("已提交");

        verify(purchaseOrderMapper, never()).updateById(any(BizPurchaseOrder.class));
    }

    @Test
    void remarkUpTo500CharsPassesValidation() {
        for (Class<?> group : List.of(AddGroup.class, EditGroup.class)) {
            assertThat(validateRemark(REMARK_500, group)).isEmpty();
            assertThat(validateRemark(null, group)).isEmpty();
            assertThat(validateRemark("", group)).isEmpty();
        }
    }

    @Test
    void remarkOver500CharsFailsValidationWithReadableMessage() {
        for (Class<?> group : List.of(AddGroup.class, EditGroup.class)) {
            assertThat(validateRemark(REMARK_500 + "字", group))
                .singleElement()
                .extracting(ConstraintViolation::getMessage)
                .asString()
                .contains("备注")
                .contains("500");
        }
    }

}
