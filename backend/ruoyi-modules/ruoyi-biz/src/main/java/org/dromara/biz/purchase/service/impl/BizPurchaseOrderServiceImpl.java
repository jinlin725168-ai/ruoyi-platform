package org.dromara.biz.purchase.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.dromara.biz.purchase.domain.BizPurchaseOrder;
import org.dromara.biz.purchase.domain.BizPurchaseOrderDetail;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderBo;
import org.dromara.biz.purchase.domain.bo.BizPurchaseOrderDetailBo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderDetailVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderExportVo;
import org.dromara.biz.purchase.domain.vo.BizPurchaseOrderVo;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderDetailMapper;
import org.dromara.biz.purchase.mapper.BizPurchaseOrderMapper;
import org.dromara.biz.purchase.service.IBizPurchaseOrderService;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.constant.SystemConstants;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.exception.ServiceException;
import org.dromara.common.core.utils.MapstructUtils;
import org.dromara.common.core.utils.StringUtils;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * 采购单Service业务层处理
 *
 * @author linjin
 * @date 2026-09-20
 */
@RequiredArgsConstructor
@Service
public class BizPurchaseOrderServiceImpl implements IBizPurchaseOrderService {

    /**
     * 草稿状态
     */
    public static final String STATUS_DRAFT = "0";

    /**
     * 已提交状态
     */
    public static final String STATUS_SUBMITTED = "1";

    /**
     * 单号前缀
     */
    private static final String ORDER_NO_PREFIX = "PO";

    /**
     * 单号流水号位数
     */
    private static final int ORDER_NO_SEQ_WIDTH = 4;

    /**
     * 单号中的日期格式
     */
    private static final DateTimeFormatter ORDER_NO_DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * 可解析的流水号最大位数，超出视为非法单号
     */
    private static final int MAX_SEQ_DIGITS = 18;

    /**
     * 单号冲突时的最大取号次数
     */
    private static final int ORDER_NO_MAX_ATTEMPTS = 5;

    /**
     * 金额小数位数
     */
    private static final int AMOUNT_SCALE = 2;

    private final BizPurchaseOrderMapper purchaseOrderMapper;

    private final BizPurchaseOrderDetailMapper purchaseOrderDetailMapper;

    private final IBizSupplierService supplierService;

    /**
     * 查询采购单详情（含全部明细）
     *
     * @param orderId 主键
     * @return 采购单详情
     */
    @Override
    public BizPurchaseOrderVo queryById(Long orderId) {
        BizPurchaseOrderVo vo = purchaseOrderMapper.selectVoById(orderId);
        if (vo == null) {
            throw new ServiceException("采购单不存在或已被删除");
        }
        vo.setDetails(queryDetails(orderId));
        return vo;
    }

    /**
     * 分页查询采购单列表
     *
     * @param bo        查询条件
     * @param pageQuery 分页参数
     * @return 采购单分页列表
     */
    @Override
    public PageResult<BizPurchaseOrderVo> queryPageList(BizPurchaseOrderBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<BizPurchaseOrder> lqw = buildQueryWrapper(bo);
        Page<BizPurchaseOrderVo> result = purchaseOrderMapper.selectVoPage(pageQuery.build(), lqw);
        return PageResult.build(result.getRecords(), result.getTotal());
    }

    /**
     * 查询符合条件的采购单导出列表（仅主表数据，一张采购单一行）
     *
     * @param bo 查询条件
     * @return 采购单导出列表
     */
    @Override
    public List<BizPurchaseOrderExportVo> queryExportList(BizPurchaseOrderBo bo) {
        List<BizPurchaseOrderVo> list = purchaseOrderMapper.selectVoList(buildQueryWrapper(bo));
        List<BizPurchaseOrderExportVo> exportList = new ArrayList<>(list.size());
        for (BizPurchaseOrderVo vo : list) {
            BizPurchaseOrderExportVo export = new BizPurchaseOrderExportVo();
            export.setOrderNo(vo.getOrderNo());
            export.setSupplierName(vo.getSupplierName());
            export.setOrderDate(vo.getOrderDate() == null ? null : vo.getOrderDate().toString());
            export.setStatus(vo.getStatus());
            export.setTotalAmount(vo.getTotalAmount());
            export.setRemark(vo.getRemark());
            exportList.add(export);
        }
        return exportList;
    }

    /**
     * 查询可选的供应商（仅启用状态）
     *
     * @return 启用状态的供应商列表
     */
    @Override
    public List<BizSupplierVo> queryEnabledSuppliers() {
        BizSupplierBo query = new BizSupplierBo();
        query.setStatus(SystemConstants.NORMAL);
        return supplierService.queryList(query);
    }

    /**
     * 构建采购单查询条件：单号模糊匹配，供应商、状态精确匹配，下单日期按区间过滤
     *
     * @param bo 查询条件
     * @return 查询条件包装器
     */
    private LambdaQueryWrapper<BizPurchaseOrder> buildQueryWrapper(BizPurchaseOrderBo bo) {
        Map<String, Object> params = bo.getParams();
        Object beginOrderDate = dateParam(params, "beginOrderDate");
        Object endOrderDate = dateParam(params, "endOrderDate");
        LambdaQueryWrapper<BizPurchaseOrder> lqw = Wrappers.lambdaQuery();
        lqw.like(StringUtils.isNotBlank(bo.getOrderNo()), BizPurchaseOrder::getOrderNo, bo.getOrderNo());
        lqw.eq(bo.getSupplierId() != null, BizPurchaseOrder::getSupplierId, bo.getSupplierId());
        lqw.like(StringUtils.isNotBlank(bo.getSupplierName()), BizPurchaseOrder::getSupplierName, bo.getSupplierName());
        lqw.eq(StringUtils.isNotBlank(bo.getStatus()), BizPurchaseOrder::getStatus, bo.getStatus());
        lqw.ge(beginOrderDate != null, BizPurchaseOrder::getOrderDate, beginOrderDate);
        lqw.le(endOrderDate != null, BizPurchaseOrder::getOrderDate, endOrderDate);
        lqw.orderByDesc(BizPurchaseOrder::getOrderDate);
        lqw.orderByDesc(BizPurchaseOrder::getCreateTime);
        lqw.orderByDesc(BizPurchaseOrder::getOrderId);
        return lqw;
    }

    /**
     * 读取查询参数中的日期条件，空白值视为未填写
     *
     * @param params 查询参数
     * @param key    参数名
     * @return 日期条件
     */
    private Object dateParam(Map<String, Object> params, String key) {
        Object value = params == null ? null : params.get(key);
        if (value == null || StringUtils.isBlank(value.toString())) {
            return null;
        }
        return value;
    }

    /**
     * 新增采购单及其明细：单号与金额由系统生成，状态固定为草稿
     *
     * @param bo 采购单
     * @return 是否新增成功
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean insertByBo(BizPurchaseOrderBo bo) {
        BizSupplierVo supplier = loadEnabledSupplier(bo.getSupplierId());
        List<BizPurchaseOrderDetail> details = buildDetails(bo.getDetails());
        BizPurchaseOrder add = MapstructUtils.convert(bo, BizPurchaseOrder.class);
        add.setOrderId(null);
        add.setSupplierName(supplier.getSupplierName());
        add.setStatus(STATUS_DRAFT);
        add.setTotalAmount(sumAmount(details));
        boolean flag = insertWithGeneratedOrderNo(add, bo.getOrderDate());
        if (flag) {
            bo.setOrderId(add.getOrderId());
            saveDetails(add.getOrderId(), details);
        }
        return flag;
    }

    /**
     * 生成单号并落库。单号由库中该日期已占用的最大流水号加一得到，
     * 并发下两个请求可能算出同一个流水号，此时唯一索引会拒绝其中一个，
     * 这里重新取号重试，重试用尽才抛出可读提示，避免把数据库异常暴露给使用者。
     *
     * @param add       待新增的采购单
     * @param orderDate 下单日期
     * @return 是否新增成功
     */
    private boolean insertWithGeneratedOrderNo(BizPurchaseOrder add, LocalDate orderDate) {
        for (int attempt = 1; attempt <= ORDER_NO_MAX_ATTEMPTS; attempt++) {
            add.setOrderNo(generateOrderNo(orderDate));
            try {
                return purchaseOrderMapper.insert(add) > 0;
            } catch (DuplicateKeyException e) {
                if (attempt == ORDER_NO_MAX_ATTEMPTS) {
                    throw new ServiceException("采购单号生成冲突，请稍后重试");
                }
            }
        }
        return false;
    }

    /**
     * 修改草稿采购单：单号与状态不可修改，明细以本次提交的集合为准
     *
     * @param bo 采购单
     * @return 是否修改成功
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean updateByBo(BizPurchaseOrderBo bo) {
        BizPurchaseOrder exists = loadDraft(bo.getOrderId(), "修改");
        BizSupplierVo supplier = loadEnabledSupplier(bo.getSupplierId());
        List<BizPurchaseOrderDetail> details = buildDetails(bo.getDetails());
        BizPurchaseOrder update = MapstructUtils.convert(bo, BizPurchaseOrder.class);
        update.setOrderId(exists.getOrderId());
        update.setOrderNo(null);
        update.setStatus(null);
        update.setSupplierName(supplier.getSupplierName());
        update.setTotalAmount(sumAmount(details));
        boolean flag = purchaseOrderMapper.updateById(update) > 0;
        if (flag) {
            removeDetails(List.of(exists.getOrderId()));
            saveDetails(exists.getOrderId(), details);
        }
        return flag;
    }

    /**
     * 提交采购单：草稿变已提交，已提交是终态
     *
     * @param orderId 主键
     * @return 是否提交成功
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean submitById(Long orderId) {
        BizPurchaseOrder exists = loadDraft(orderId, "提交");
        long details = purchaseOrderDetailMapper.selectCount(Wrappers.<BizPurchaseOrderDetail>lambdaQuery()
            .eq(BizPurchaseOrderDetail::getOrderId, orderId));
        if (details <= 0) {
            throw new ServiceException("采购单【" + exists.getOrderNo() + "】没有明细，不能提交");
        }
        BizPurchaseOrder update = new BizPurchaseOrder();
        update.setOrderId(orderId);
        update.setStatus(STATUS_SUBMITTED);
        return purchaseOrderMapper.updateById(update) > 0;
    }

    /**
     * 校验并批量删除采购单及其明细（已提交的单据不可删除）
     *
     * @param ids     待删除的主键集合
     * @param isValid 是否进行有效性校验
     * @return 是否删除成功
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean deleteWithValidByIds(Collection<Long> ids, Boolean isValid) {
        if (isValid) {
            List<BizPurchaseOrder> orders = purchaseOrderMapper.selectByIds(ids);
            if (orders.size() != ids.size()) {
                throw new ServiceException("采购单不存在或已被删除");
            }
            for (BizPurchaseOrder order : orders) {
                if (!STATUS_DRAFT.equals(order.getStatus())) {
                    throw new ServiceException("采购单【" + order.getOrderNo() + "】已提交，不能删除");
                }
            }
        }
        boolean flag = purchaseOrderMapper.deleteByIds(ids) > 0;
        if (flag) {
            removeDetails(ids);
        }
        return flag;
    }

    /**
     * 查询采购单的全部明细
     *
     * @param orderId 采购单ID
     * @return 明细列表
     */
    private List<BizPurchaseOrderDetailVo> queryDetails(Long orderId) {
        return purchaseOrderDetailMapper.selectVoList(Wrappers.<BizPurchaseOrderDetail>lambdaQuery()
            .eq(BizPurchaseOrderDetail::getOrderId, orderId)
            .orderByAsc(BizPurchaseOrderDetail::getDetailId));
    }

    /**
     * 读取草稿状态的采购单，不存在或已提交时抛出可读提示
     *
     * @param orderId 采购单ID
     * @param action  操作名称
     * @return 采购单
     */
    private BizPurchaseOrder loadDraft(Long orderId, String action) {
        BizPurchaseOrder exists = purchaseOrderMapper.selectById(orderId);
        if (exists == null) {
            throw new ServiceException("采购单不存在或已被删除");
        }
        if (!STATUS_DRAFT.equals(exists.getStatus())) {
            throw new ServiceException("采购单【" + exists.getOrderNo() + "】已提交，不能" + action);
        }
        return exists;
    }

    /**
     * 读取启用状态的供应商，停用或不存在时抛出可读提示
     *
     * @param supplierId 供应商ID
     * @return 供应商
     */
    private BizSupplierVo loadEnabledSupplier(Long supplierId) {
        BizSupplierVo supplier = supplierService.queryById(supplierId);
        if (supplier == null) {
            throw new ServiceException("供应商不存在，请重新选择供应商");
        }
        if (!SystemConstants.NORMAL.equals(supplier.getStatus())) {
            throw new ServiceException("供应商【" + supplier.getSupplierName() + "】已停用，请改选启用状态的供应商");
        }
        return supplier;
    }

    /**
     * 按数量×单价计算每条明细的金额
     *
     * @param details 明细业务对象
     * @return 明细实体
     */
    private List<BizPurchaseOrderDetail> buildDetails(List<BizPurchaseOrderDetailBo> details) {
        if (details == null || details.isEmpty()) {
            throw new ServiceException("采购单明细不能为空");
        }
        List<BizPurchaseOrderDetail> list = new ArrayList<>(details.size());
        for (BizPurchaseOrderDetailBo detailBo : details) {
            BizPurchaseOrderDetail detail = new BizPurchaseOrderDetail();
            detail.setMaterialName(detailBo.getMaterialName());
            detail.setQuantity(toQuantity(detailBo.getQuantity()));
            detail.setPrice(detailBo.getPrice().setScale(AMOUNT_SCALE, RoundingMode.HALF_UP));
            detail.setAmount(detail.getPrice()
                .multiply(BigDecimal.valueOf(detail.getQuantity()))
                .setScale(AMOUNT_SCALE, RoundingMode.HALF_UP));
            list.add(detail);
        }
        return list;
    }

    /**
     * 明细数量转正整数
     *
     * @param quantity 数量
     * @return 正整数数量
     */
    private int toQuantity(BigDecimal quantity) {
        try {
            int value = quantity.intValueExact();
            if (value <= 0) {
                throw new ServiceException("数量必须是大于0的正整数");
            }
            return value;
        } catch (ArithmeticException e) {
            throw new ServiceException("数量必须是大于0的正整数");
        }
    }

    /**
     * 合计金额为明细金额之和
     *
     * @param details 明细
     * @return 合计金额
     */
    private BigDecimal sumAmount(List<BizPurchaseOrderDetail> details) {
        BigDecimal total = BigDecimal.ZERO;
        for (BizPurchaseOrderDetail detail : details) {
            total = total.add(detail.getAmount());
        }
        return total.setScale(AMOUNT_SCALE, RoundingMode.HALF_UP);
    }

    /**
     * 保存采购单明细
     *
     * @param orderId 采购单ID
     * @param details 明细
     */
    private void saveDetails(Long orderId, List<BizPurchaseOrderDetail> details) {
        for (BizPurchaseOrderDetail detail : details) {
            detail.setDetailId(null);
            detail.setOrderId(orderId);
        }
        purchaseOrderDetailMapper.insertBatch(details);
    }

    /**
     * 删除采购单下的全部明细
     *
     * @param orderIds 采购单ID集合
     */
    private void removeDetails(Collection<Long> orderIds) {
        purchaseOrderDetailMapper.delete(Wrappers.<BizPurchaseOrderDetail>lambdaQuery()
            .in(BizPurchaseOrderDetail::getOrderId, orderIds));
    }

    /**
     * 生成采购单号：PO + 下单日期(yyyyMMdd) + 当日流水号。
     * 流水号取自库中该日期已占用的最大单号（含已逻辑删除的单据）加一，
     * 因此回填历史日期或预填未来日期的单据也不会重号；
     * 并发下的取号冲突由唯一索引兜底，并在 {@link #insertWithGeneratedOrderNo} 中重新取号。
     *
     * @param orderDate 下单日期
     * @return 采购单号
     */
    private String generateOrderNo(LocalDate orderDate) {
        String datePrefix = ORDER_NO_PREFIX + ORDER_NO_DATE_FORMATTER.format(orderDate);
        String maxOrderNo = purchaseOrderMapper.selectMaxOrderNoByPrefix(datePrefix);
        long nextSeq = parseSeq(maxOrderNo, datePrefix) + 1;
        return datePrefix + StringUtils.leftPad(Long.toString(nextSeq), ORDER_NO_SEQ_WIDTH, '0');
    }

    /**
     * 解析单号中的流水号，非法或为空时视为 0
     *
     * @param orderNo    采购单号
     * @param datePrefix 单号中的前缀部分
     * @return 流水号
     */
    private long parseSeq(String orderNo, String datePrefix) {
        if (StringUtils.isBlank(orderNo) || orderNo.length() <= datePrefix.length()) {
            return 0L;
        }
        String seq = orderNo.substring(datePrefix.length());
        if (!StringUtils.isNumeric(seq) || seq.length() > MAX_SEQ_DIGITS) {
            return 0L;
        }
        return Long.parseLong(seq);
    }

}
