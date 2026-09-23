package org.dromara.biz.supplier.mapper;

import org.apache.ibatis.annotations.Param;
import org.dromara.biz.supplier.domain.BizSupplier;
import org.dromara.biz.supplier.domain.vo.BizSupplierVo;
import org.dromara.common.mybatis.core.mapper.BaseMapperPlus;

import java.util.Collection;
import java.util.List;

/**
 * 供应商Mapper接口
 *
 * @author linjin
 * @date 2026-09-18
 */
public interface BizSupplierMapper extends BaseMapperPlus<BizSupplier, BizSupplierVo> {

    /**
     * 查询供应商的分类（含已逻辑删除的供应商，只返回 supplierId 与 supplierCategory）
     *
     * @param supplierIds 供应商ID集合
     * @return 供应商分类
     */
    List<BizSupplier> selectCategoriesIgnoreDeleted(@Param("supplierIds") Collection<Long> supplierIds);

    /**
     * 查询分类属于给定值的供应商ID（含已逻辑删除的供应商）
     *
     * @param categories 分类值集合
     * @return 供应商ID
     */
    List<Long> selectIdsByCategoriesIgnoreDeleted(@Param("categories") Collection<String> categories);

}
