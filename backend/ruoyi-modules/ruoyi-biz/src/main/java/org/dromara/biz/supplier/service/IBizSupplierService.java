package org.dromara.biz.supplier.service;

import org.dromara.biz.supplier.domain.bo.BizSupplierBo;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.common.core.domain.PageResult;
import org.dromara.common.mybatis.core.page.PageQuery;

import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * 供应商Service接口
 *
 * @author linjin
 * @date 2026-09-18
 */
public interface IBizSupplierService {

    /**
     * 查询供应商
     *
     * @param supplierId 主键
     * @return 供应商
     */
    BizSupplierVo queryById(Long supplierId);

    /**
     * 分页查询供应商列表
     *
     * @param bo        查询条件
     * @param pageQuery 分页参数
     * @return 供应商分页列表
     */
    PageResult<BizSupplierVo> queryPageList(BizSupplierBo bo, PageQuery pageQuery);

    /**
     * 查询符合条件的供应商列表
     *
     * @param bo 查询条件
     * @return 供应商列表
     */
    List<BizSupplierVo> queryList(BizSupplierBo bo);

    /**
     * 按供应商ID查询分类名称（含已逻辑删除的供应商），分类为空或已不在字典中时为『未分类』
     *
     * @param supplierIds 供应商ID集合
     * @return 供应商ID到分类名称的映射，查不到的供应商不在其中
     */
    Map<Long, String> queryCategoryLabels(Collection<Long> supplierIds);

    /**
     * 查询当前分类等于给定值的供应商ID（含已逻辑删除的供应商）
     *
     * @param category 分类值
     * @return 供应商ID
     */
    List<Long> querySupplierIdsByCategory(String category);

    /**
     * 查询分类为字典中现有值的供应商ID（含已逻辑删除的供应商），其余供应商即为『未分类』
     *
     * @return 供应商ID
     */
    List<Long> queryCategorizedSupplierIds();

    /**
     * 校验供应商编码在未删除的供应商中是否唯一
     *
     * @param bo 供应商
     * @return 是否唯一
     */
    boolean checkCodeUnique(BizSupplierBo bo);

    /**
     * 校验供应商分类是否为『供应商分类』字典中现有的值
     *
     * @param bo 供应商
     * @return 是否有效
     */
    boolean checkCategoryValid(BizSupplierBo bo);

    /**
     * 新增供应商
     *
     * @param bo 供应商
     * @return 是否新增成功
     */
    Boolean insertByBo(BizSupplierBo bo);

    /**
     * 修改供应商（编码不可修改）
     *
     * @param bo 供应商
     * @return 是否修改成功
     */
    Boolean updateByBo(BizSupplierBo bo);

    /**
     * 校验并批量删除供应商信息
     *
     * @param ids     待删除的主键集合
     * @param isValid 是否进行有效性校验
     * @return 是否删除成功
     */
    Boolean deleteWithValidByIds(Collection<Long> ids, Boolean isValid);
}
