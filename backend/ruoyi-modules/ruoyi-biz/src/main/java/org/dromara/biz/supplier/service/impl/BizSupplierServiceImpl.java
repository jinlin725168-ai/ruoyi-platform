package org.dromara.biz.supplier.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.RequiredArgsConstructor;
import org.dromara.biz.supplier.constant.SupplierConstants;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.biz.supplier.mapper.BizSupplierMapper;
import org.dromara.biz.supplier.service.IBizSupplierService;
import org.dromara.common.core.constant.SystemConstants;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.core.service.DictService;
import org.dromara.common.core.utils.MapstructUtils;
import org.dromara.common.core.utils.StringUtils;
import org.dromara.common.mybatis.core.page.PageQuery;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

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
    private final DictService dictService;

    /**
     * 查询供应商
     *
     * @param supplierId 主键
     * @return 供应商
     */
    @Override
    public BizSupplierVo queryById(Long supplierId) {
        BizSupplierVo vo = supplierMapper.selectVoById(supplierId);
        if (vo != null) {
            fillCategoryLabel(List.of(vo));
        }
        return vo;
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
        fillCategoryLabel(result.getRecords());
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
        List<BizSupplierVo> list = supplierMapper.selectVoList(buildQueryWrapper(bo));
        fillCategoryLabel(list);
        return list;
    }

    /**
     * 按供应商ID查询分类名称（含已逻辑删除的供应商），分类为空或已不在字典中时为『未分类』
     *
     * @param supplierIds 供应商ID集合
     * @return 供应商ID到分类名称的映射，查不到的供应商不在其中
     */
    @Override
    public Map<Long, String> queryCategoryLabels(Collection<Long> supplierIds) {
        if (supplierIds == null || supplierIds.isEmpty()) {
            return Map.of();
        }
        Map<String, String> labels = dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE);
        Map<Long, String> result = new HashMap<>(supplierIds.size());
        for (BizSupplier supplier : supplierMapper.selectCategoriesIgnoreDeleted(supplierIds)) {
            result.put(supplier.getSupplierId(), categoryLabel(labels, supplier.getSupplierCategory()));
        }
        return result;
    }

    /**
     * 查询当前分类等于给定值的供应商ID（含已逻辑删除的供应商）
     *
     * @param category 分类值
     * @return 供应商ID
     */
    @Override
    public List<Long> querySupplierIdsByCategory(String category) {
        return supplierMapper.selectIdsByCategoriesIgnoreDeleted(Set.of(category));
    }

    /**
     * 查询分类为字典中现有值的供应商ID（含已逻辑删除的供应商）
     *
     * @return 供应商ID，字典已无任何值时为空
     */
    @Override
    public List<Long> queryCategorizedSupplierIds() {
        Set<String> valid = dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE).keySet();
        if (valid.isEmpty()) {
            return List.of();
        }
        return supplierMapper.selectIdsByCategoriesIgnoreDeleted(valid);
    }

    /**
     * 把分类值翻译为字典中的分类名称，分类为空或已不在字典中时为『未分类』
     *
     * @param list 供应商列表
     */
    private void fillCategoryLabel(List<BizSupplierVo> list) {
        Map<String, String> labels = dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE);
        for (BizSupplierVo vo : list) {
            vo.setSupplierCategoryLabel(categoryLabel(labels, vo.getSupplierCategory()));
        }
    }

    /**
     * 分类值对应的字典名称，分类为空或已不在字典中时为『未分类』
     *
     * @param labels   字典值到名称的映射
     * @param category 分类值
     * @return 分类名称
     */
    private String categoryLabel(Map<String, String> labels, String category) {
        String label = StringUtils.isBlank(category) ? null : labels.get(category);
        return StringUtils.isBlank(label) ? SupplierConstants.CATEGORY_NONE_LABEL : label;
    }

    /**
     * 构建供应商查询条件：名称模糊匹配、状态精确匹配、分类精确匹配；
     * 分类为『未分类』时匹配分类为空或分类值已不在字典中的供应商
     *
     * @param bo 查询条件
     * @return 查询条件包装器
     */
    private LambdaQueryWrapper<BizSupplier> buildQueryWrapper(BizSupplierBo bo) {
        LambdaQueryWrapper<BizSupplier> lqw = Wrappers.lambdaQuery();
        lqw.like(StringUtils.isNotBlank(bo.getSupplierName()), BizSupplier::getSupplierName, bo.getSupplierName());
        lqw.eq(StringUtils.isNotBlank(bo.getStatus()), BizSupplier::getStatus, bo.getStatus());
        String category = bo.getSupplierCategory();
        if (SupplierConstants.CATEGORY_NONE.equals(category)) {
            Set<String> valid = dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE).keySet();
            // 字典已无任何值时，所有供应商都显示为『未分类』，因此不追加分类条件
            if (!valid.isEmpty()) {
                lqw.and(w -> w.isNull(BizSupplier::getSupplierCategory)
                    .or().eq(BizSupplier::getSupplierCategory, "")
                    .or().notIn(BizSupplier::getSupplierCategory, valid));
            }
        } else {
            lqw.eq(StringUtils.isNotBlank(category), BizSupplier::getSupplierCategory, category);
        }
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
     * 校验供应商分类是否为『供应商分类』字典中现有的值
     *
     * @param bo 供应商
     * @return 是否有效
     */
    @Override
    public boolean checkCategoryValid(BizSupplierBo bo) {
        String category = bo.getSupplierCategory();
        return StringUtils.isNotBlank(category)
            && dictService.getAllDictByDictType(SupplierConstants.CATEGORY_DICT_TYPE).containsKey(category);
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
