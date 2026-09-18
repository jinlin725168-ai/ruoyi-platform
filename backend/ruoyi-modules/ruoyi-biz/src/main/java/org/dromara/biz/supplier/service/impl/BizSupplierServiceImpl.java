package org.dromara.biz.supplier.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.mapper.BizSupplierMapper;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.constant.SystemConstants;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.utils.MapstructUtils;
import org.dromara.common.core.utils.StringUtils;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.List;

/**
 * 供应商Service业务层处理
 *
 * @author linjin
 * @date 2026-09-18
 */
@RequiredArgsConstructor
@Service
public class BizSupplierServiceImpl implements IBizSupplierService {

    private final BizSupplierMapper supplierMapper;

    /**
     * 查询供应商
     *
     * @param supplierId 主键
     * @return 供应商
     */
    @Override
    public BizSupplierVo queryById(Long supplierId) {
        return supplierMapper.selectVoById(supplierId);
    }

    /**
     * 分页查询供应商列表
     *
     * @param bo        查询条件
     * @param pageQuery 分页参数
     * @return 供应商分页列表
     */
    @Override
    public PageResult<BizSupplierVo> queryPageList(BizSupplierBo bo, PageQuery pageQuery) {
        LambdaQueryWrapper<BizSupplier> lqw = buildQueryWrapper(bo);
        Page<BizSupplierVo> result = supplierMapper.selectVoPage(pageQuery.build(), lqw);
        return PageResult.build(result.getRecords(), result.getTotal());
    }

    /**
     * 查询符合条件的供应商列表
     *
     * @param bo 查询条件
     * @return 供应商列表
     */
    @Override
    public List<BizSupplierVo> queryList(BizSupplierBo bo) {
        return supplierMapper.selectVoList(buildQueryWrapper(bo));
    }

    /**
     * 构建供应商查询条件：名称模糊匹配、状态精确匹配
     *
     * @param bo 查询条件
     * @return 查询条件包装器
     */
    private LambdaQueryWrapper<BizSupplier> buildQueryWrapper(BizSupplierBo bo) {
        LambdaQueryWrapper<BizSupplier> lqw = Wrappers.lambdaQuery();
        lqw.like(StringUtils.isNotBlank(bo.getSupplierName()), BizSupplier::getSupplierName, bo.getSupplierName());
        lqw.eq(StringUtils.isNotBlank(bo.getStatus()), BizSupplier::getStatus, bo.getStatus());
        lqw.orderByDesc(BizSupplier::getSupplierId);
        return lqw;
    }

    /**
     * 校验供应商编码在未删除的供应商中是否唯一（逻辑删除条件由 MyBatis-Plus 自动追加）
     *
     * @param bo 供应商
     * @return 是否唯一
     */
    @Override
    public boolean checkCodeUnique(BizSupplierBo bo) {
        if (StringUtils.isBlank(bo.getSupplierCode())) {
            return true;
        }
        return !supplierMapper.exists(Wrappers.<BizSupplier>lambdaQuery()
            .eq(BizSupplier::getSupplierCode, bo.getSupplierCode())
            .ne(bo.getSupplierId() != null, BizSupplier::getSupplierId, bo.getSupplierId()));
    }

    /**
     * 新增供应商，未填写状态时默认启用
     *
     * @param bo 供应商
     * @return 是否新增成功
     */
    @Override
    public Boolean insertByBo(BizSupplierBo bo) {
        BizSupplier add = MapstructUtils.convert(bo, BizSupplier.class);
        if (StringUtils.isBlank(add.getStatus())) {
            add.setStatus(SystemConstants.NORMAL);
        }
        boolean flag = supplierMapper.insert(add) > 0;
        if (flag) {
            bo.setSupplierId(add.getSupplierId());
        }
        return flag;
    }

    /**
     * 修改供应商，编码创建后不可修改，提交的编码被忽略
     *
     * @param bo 供应商
     * @return 是否修改成功
     */
    @Override
    public Boolean updateByBo(BizSupplierBo bo) {
        BizSupplier update = MapstructUtils.convert(bo, BizSupplier.class);
        update.setSupplierCode(null);
        if (StringUtils.isBlank(update.getStatus())) {
            update.setStatus(null);
        }
        return supplierMapper.updateById(update) > 0;
    }

    /**
     * 校验并批量删除供应商信息（逻辑删除）
     *
     * @param ids     待删除的主键集合
     * @param isValid 是否进行有效性校验
     * @return 是否删除成功
     */
    @Override
    public Boolean deleteWithValidByIds(Collection<Long> ids, Boolean isValid) {
        return supplierMapper.deleteByIds(ids) > 0;
    }

}
