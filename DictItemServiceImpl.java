package cn.gov.customs.ecim.sys.dict.service.impl;

import cn.gov.customs.common.cache.CpCacheService;
import cn.gov.customs.common.cache.CacheConstant;
import cn.gov.customs.common.system.base.constant.CommonConstant;
import cn.gov.customs.ecim.sys.dict.constant.DictConstant;
import cn.gov.customs.ecim.sys.dict.dao.DictItemMapper;
import cn.gov.customs.ecim.sys.dict.pojo.entity.DictItem;
import cn.gov.customs.ecim.sys.dict.pojo.query.DictItemQuery;
import cn.gov.customs.ecim.sys.dict.pojo.vo.DictItemVo;
import cn.gov.customs.ecim.sys.dict.pojo.vo.DictNodeVo;
import cn.gov.customs.ecim.sys.dict.service.DictItemService;
import cn.gov.customs.ecim.sys.dict.utils.DictTreeUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.conditions.query.LambdaQueryChainWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import java.util.*;
import java.util.stream.Collectors;

import lombok.RequiredArgsConstructor;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 系统字典参数表 服务实现类
 * @author cp
 * @since 2025/08
 */
@Service
@RequiredArgsConstructor
public class DictItemServiceImpl extends ServiceImpl<DictItemMapper, DictItem> implements DictItemService {

//    @Autowired
//    private IParaCustomsService paraCustomsService;
    private final CpCacheService baseCacheService;

    @Override
    public PageInfo getDictItemListPage(DictItemQuery query) {
        PageHelper.startPage(Math.toIntExact(query.getPageNum()), Math.toIntExact(query.getPageSize()));
        QueryWrapper<DictItem> wrapper = new QueryWrapper<>();
        wrapper.eq(StringUtils.isNotBlank(query.getDictId()), "DICT_ID", query.getDictId());
        wrapper.eq(StringUtils.isNotBlank(query.getDictCode()), "DICT_CODE", query.getDictCode());
        String itemText = StringUtils.trim(query.getItemText());
        String itemValue = StringUtils.trim(query.getItemValue());
        wrapper.like(StringUtils.isNotBlank(itemText), "ITEM_TEXT", itemText);
        wrapper.like(StringUtils.isNotBlank(itemValue), "ITEM_VALUE", itemValue);
        wrapper.eq(StringUtils.isNotBlank(query.getState()), "STATUS", query.getState());
        wrapper.orderByAsc("SORT_ORDER");
        List<DictItem> list= baseMapper.selectList(wrapper);
        return new PageInfo(list);
    }

    @Override
    public PageInfo getDictItemPage(DictItemQuery query) {
        PageHelper.startPage(Math.toIntExact(query.getPageNum()), Math.toIntExact(query.getPageSize()));
        List<DictItemVo> retList = baseMapper.getDictItemPage(
                query.getDictId(), query.getDictCode(), StringUtils.trim(query.getItemText()), StringUtils.trim(query.getItemValue()));
        // 生成 PageInfo 分页信息返回
        PageInfo<DictItemVo> retPage = new PageInfo<>(retList);
        return retPage;
    }

    @Override
    //每次更新把dict的缓存全部清掉，因更新操作较少，可以全部清除
    @CacheEvict(value = CacheConstant.SYS_DICT_CACHE, allEntries = true)
    @Transactional(rollbackFor = Exception.class)
    public boolean saveDictItem(DictItem dictItem) {
        //效验字典参数值是否重复
        boolean flag = this.save(dictItem);

        //维护父节点信息
        if(flag && (StringUtils.isNotBlank(dictItem.getParentItemId()) || !StringUtils.equals("0", dictItem.getParentItemId()))){
            //如果新增后原先父节点hasChild字段为0
            DictItem parentDictItem = baseMapper.selectOne(new LambdaQueryWrapper<DictItem>()
                    .eq(DictItem::getDictId, dictItem.getParentItemId())
                    .eq(DictItem::getIsParent, 0));
            //更新为1
            if(parentDictItem != null){
                parentDictItem.setIsParent(1);
                baseMapper.updateById(parentDictItem);
            }
        }

        clearDictCache();       // 清除缓存
        return flag;
    }

    @Override
    //每次更新把dict的缓存全部清掉，因更新操作较少，可以全部清除
    @CacheEvict(value = CacheConstant.SYS_DICT_CACHE, allEntries = true)
    @Transactional(rollbackFor = Exception.class)
    public boolean editDictItem(DictItem dictItem) {

        boolean flag = updateById(dictItem);
        clearDictCache();       // 清除缓存
        return flag;
    }

    @Override
    public String checkParams(DictItem dictItem) {
        List<DictItem> list = list(new LambdaQueryWrapper<DictItem>().eq(DictItem::getDictCode, dictItem.getDictCode())
                .eq(DictItem::getItemValue, dictItem.getItemValue()));
        if(CollectionUtils.isNotEmpty(list)&&list.size()>0){
            return "字典参数值已存在";
        }
        return null;
    }

    @Override
    //每次更新把dict的缓存全部清掉，因更新操作较少，可以全部清除
    @CacheEvict(value = CacheConstant.SYS_DICT_CACHE, allEntries = true)
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteDictItem(List<String> ids) {
        int rows = baseMapper.deleteBatchIds(ids);
        clearDictCache();       // 清除缓存
//        //维护父节点信息
//        for(String id : ids){
//            DictItem dictItem = baseMapper.selectById(id);
////            DictItem dictItem = baseMapper.selByIdDel(id);
//            if(dictItem.getState().equals("1")){
//                throw new BizException(BizExceptionCodeMessage.EXP_BIZ, "只能删除’未启用‘状态字典参数！");
//            }
//            //如果删除后父节点下没有节点了
//            if (!"0".equals(dictItem.getParentItemId())) {
//                List<DictItem> dictItemList =
//                        baseMapper.selectList(
//                                new LambdaQueryWrapper<DictItem>()
//                                        .ne(DictItem::getDictId, id)
//                                        .eq(DictItem::getParentItemId, dictItem.getParentItemId()));
//
//                // 父节点更新为0
//                if (CollectionUtils.isEmpty(dictItemList)) {
//                    DictItem parentDictItem =
//                            baseMapper.selectOne(
//                                    new LambdaQueryWrapper<DictItem>()
//                                            .eq(DictItem::getDictId, dictItem.getParentItemId()));
//                    if (parentDictItem != null) {
//                        parentDictItem.setIsParent(0);
//                        baseMapper.updateById(parentDictItem);
//                    }
//                }
//            }
//        }
        return rows > 0;
    }

    @Override
    //每次更新把dict的缓存全部清掉，因更新操作较少，可以全部清除
    @CacheEvict(value = CacheConstant.SYS_DICT_CACHE, allEntries = true)
    public boolean deleteDictItemByDictId(String dictId) {
        boolean flag = this.removeById(dictId);
//        boolean flag = baseMapper.deleteDictItemByDictId(dictId);
        clearDictCache();       // 清除缓存
        return flag;
    }

//    @CacheEvict(cacheNames = CacheConstant.SYS_DICT_CACHE, allEntries = true)
    public void clearDictCache() {
        baseCacheService.evictCache(CacheConstant.SYS_DICT_CACHE);
    }

    @Override
    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "#dictCode")
    public List<DictItem> getDictItemByCode(String dictCode) {
        LambdaQueryChainWrapper<DictItem> queryWrapper = new LambdaQueryChainWrapper<>(baseMapper);
        queryWrapper.in(StringUtils.isNotBlank(dictCode), DictItem::getDictCode, dictCode.split(","));
        queryWrapper.eq(DictItem::getState, CommonConstant.STATUS_1);
        queryWrapper.orderByAsc(DictItem::getSortOrder);
        return queryWrapper.list();
    }

    /**
    * 查询字典下最底层的叶子节点
    * @param dictCode
    * @return
    * @author hzb
    * @since 2025/6/17 下午2:31*/
    @Override
//    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "#dictCode")
    public List<DictItem> getChildrenByCode(String dictCode) {
        return baseMapper.getChildrenByCode(dictCode);
    }


    //    @Cacheable(value = {"sys:cache:dict"}, key = "#code+':'+#key" )
    @Cacheable(value = {"sys:cache:dict"}, key = "#code+':'+#key", condition = "#code != null && #key != null")
    public String queryTextByCode(String code, String key) {
        return baseMapper.queryTextByCode(code, key);
    }

    @Override
//  @Cacheable(value = CacheConstant.SYS_DICT_CACHE, key = "'DictItemId' +'_'+ #id")
    @Cacheable(value = CacheConstant.SYS_DICT_CACHE, key = "'DictItemId' +'_'+ #id", condition = "#id != null")
    public DictItem getDictItemById(String id) {
        return getById(id);
    }

    @Override
//  @Cacheable(value = CacheConstant.SYS_DICT_CACHE, key = "'dictTree' +'_'+ #dictCode")
    @Cacheable(value = CacheConstant.SYS_DICT_CACHE, key = "'dictTree' +'_'+ #dictCode", condition = "#dictCode")
    public List<DictNodeVo> dictTree(String dictCode, String dictId) {
        List<DictNodeVo> dictNodeVos = baseMapper.selectDictByCodeOrId(dictCode, dictId);
        DictTreeUtil treeUtil = new DictTreeUtil(dictNodeVos);
        return treeUtil.buildTree();
    }

    @Override
    public List<String> findChildrenItemValue(List<DictNodeVo> dictTree, String itemValue, boolean isParentFound) {
        List<String> itemValueList = new ArrayList<>();
        List<DictNodeVo> childrenList =  findChildrenNode(dictTree, itemValue, isParentFound);
        for (DictNodeVo dictNodeVo : childrenList) {
            itemValueList.add(dictNodeVo.getItemValue());
        }
        return itemValueList;
    }

    @Override
    public List<DictNodeVo> findChildrenNode(List<DictNodeVo> dictTree, String itemValue, boolean isParentFound) {
        List<DictNodeVo> childrenList = new ArrayList<>();
        for (DictNodeVo dictNodeVo : dictTree) {
            if (StringUtils.equals(dictNodeVo.getItemValue(), itemValue)) {
                childrenList.add(dictNodeVo);
                List<DictNodeVo> subList = findChildrenNode(dictNodeVo.getChildren(), itemValue, true);
                childrenList.addAll(subList);
                return childrenList;
            } else {
                if (isParentFound) {                // 已找到其父节点, 直接添加其子节点
                    childrenList.add(dictNodeVo);
                    List<DictNodeVo> subList = findChildrenNode(dictNodeVo.getChildren(), itemValue, isParentFound);
                    childrenList.addAll(subList);
                } else {                            // 还没找到其父节点, 则继续从树的其他节点中寻找
                    List<DictNodeVo> childrenNodes = dictNodeVo.getChildren();
                    if(ObjectUtils.isNotEmpty(childrenNodes)){
                        for (DictNodeVo child : childrenNodes) {
                            if (isParentFound) {
                                childrenList.add(child);
                            }
                            List<DictNodeVo> subList = findChildrenNode(child.getChildren(), itemValue, isParentFound);
                            childrenList.addAll(subList);
                        }
                    }
                }
            }
        }
        return childrenList;
    }

    @Override
    public Map<String, String> getDictItemMap(List<String> codeList, String type) {
        Map<String, String> dictMap = new HashMap<>();
        List<DictItem> dictItemList = getDictItemByCode(codeList.stream().collect(Collectors.joining(",")));
        if (DictConstant.ITEM_TO_TEXT.equals(type)) {
            dictMap = dictItemList.stream().collect(Collectors.toMap(k -> k.getItemValue(), DictItem::getItemText));
        } else if (DictConstant.ITEM_TO_VALUE.equals(type)) {
            dictMap = dictItemList.stream().collect(Collectors.toMap(k -> k.getItemText(), DictItem::getItemValue));
        }
        return dictMap;
    }

    @Override
    public Map<String,Map<String,String>> getDictItemNestedMap(List<String> codeList, String type) {
        Map<String,Map<String,String>> dictMap = new HashMap<>();
        List<DictItem> dictItemList = getDictItemByCode(codeList.stream().collect(Collectors.joining(",")));
        if (DictConstant.ITEM_TO_TEXT.equals(type)) {
            dictMap = dictItemList.stream()
                    .collect(Collectors.groupingBy(
                            DictItem::getDictCode,
                            Collectors.toMap(DictItem::getItemValue,dictItem -> dictItem.getItemText())
                    ));
        } else if (DictConstant.ITEM_TO_VALUE.equals(type)) {
            dictMap = dictItemList.stream()
                    .collect(Collectors.groupingBy(
                            DictItem::getDictCode,
                            Collectors.toMap(DictItem::getItemText,dictItem -> dictItem.getItemValue())
                    ));
        }
        return dictMap;
    }

    @Override
    public List<Object> getDictItemValueByCode(String dictCode) {
        LambdaQueryWrapper<DictItem> wrapper = new LambdaQueryWrapper<>();
        wrapper.select(DictItem::getItemValue);
        wrapper.eq(DictItem::getDictCode, dictCode);
        wrapper.orderByAsc(DictItem::getSortOrder);
        List list = this.listObjs(wrapper);
//        List retlist =
        return (List<Object>) list.stream().map(obj -> obj == null ? "" : obj.toString()).collect(Collectors.toList());
//        return baseMapper.getDictItemValueCode(dictCode);
    }

    @Override
    public List<DictItem> getAllChildItem(String dictCode, String parentItemValue) {
        return baseMapper.getChildrenByCodeValue(dictCode, parentItemValue);
    }

//
//    /**
//     * 获取单层的设备类型列表
//     * @param query
//     * @return
//     * @since 2025/7/9 上午10:56
//     */
//    @Override
//    public PageInfo getDeviceTypePage(DictItemQuery query) {
//        if(StringUtils.isBlank(query.getParentItemId())){
//            query.setParentItemId("0");
//        }
//        if (query.getIsPage()) {
//            PageHelper.startPage(query);
//        }
//        LambdaQueryWrapper<DictItem> lqw = new LambdaQueryWrapper<DictItem>()
//                .eq(DictItem::getParentItemId, query.getParentItemId())
//                .eq(DictItem::getDictCode, DictCodeEnum.DEVICE_TYPE.getCode())
//                .orderByAsc(DictItem::getSortOrder);
//        return new PageInfo(baseMapper.selectList(lqw));
//
//    }
//
//    @Override
////    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "'dictEqCatTree' +'_'+ #dictCode ")
//    public List<DictEqCatNodeVO> dictEqCatTree(String dictCode) {
//        List<DictEqCatNodeVO> dictEqCatNodeVOS = new ArrayList<>();
//        List<DictNodeVo> dictNodeVos = dictTree(dictCode, "");
//        for (DictNodeVo dictNode : dictNodeVos) {
//            DictTreeUtil treeUtil = new DictTreeUtil(dictNode);
//            List<String> itemValues = treeUtil.extractLeafItemValues();
//            Map<String, List<EquipmentCatalog>> catalogMap = iEquipmentCatalogService.findEqCatGroupByItemValues(itemValues);
//            DictEqCatNodeVO dictEqCatNodeVO = buildCompositeTree(dictNode, catalogMap);
//            dictEqCatNodeVOS.add(dictEqCatNodeVO);
//        }
//        return dictEqCatNodeVOS;
//    }
//
//    @Override
//    public List<DictItem> getResearchUnits() {
//        List<DictItem> result = new ArrayList<>();
//        //研发单位列表  数据来源 直属关 + 字典配置
//        List<ParaCustoms> paraCustomsList = paraCustomsService.getDirectCustoms();
//        //构造成字典的形式
//        if(CollectionUtils.isNotEmpty(paraCustomsList)){
//            for (ParaCustoms item : paraCustomsList) {
//                DictItem dictItem = new DictItem();
//                dictItem.setId(item.getCustomsId());
//                dictItem.setDictCode("IRESEARCH_MANAGE_CUSTOM");
//                dictItem.setItemText(item.getCustomsName());
//                dictItem.setItemValue(item.getCustomsCode());
//                result.add(dictItem);
//            }
//        }
//        //查询字典数据
//        List<DictItem> dictItems = this.list(new LambdaQueryWrapper<DictItem>()
//                .eq(DictItem::getDictCode, "RESEARCH_UNIT")
//                .eq(DictItem::getStatus, CommonConstant.STATUS_1)
//                .orderByAsc(DictItem::getSortOrder));
//        if(CollectionUtils.isNotEmpty(dictItems)){
//            result.addAll(dictItems);
//        }
//        //按照关区号从小到大排序
////        result=result.stream()
////                .sorted(Comparator.comparing(DictItem::getItemValue))
////                .collect(Collectors.toList());
//
//        return result;
//    }
//
//    /**
//     * @param researchUnit 研发单位(下拉框)的自定义参数
//     * @return fullPathName 机构全路径
//     * @since 2025/5/26
//     */
//    @Override
//    public String getResearchUnitFullPathName(String researchUnit) {
//        DictItem dictItem = this.getOne(new LambdaQueryWrapper<DictItem>()
//                .eq(DictItem::getDictCode, "RESEARCH_UNIT")
//                .eq(DictItem::getStatus, CommonConstant.STATUS_1)
//                .eq(DictItem::getItemValue, researchUnit)
//                .orderByAsc(DictItem::getSortOrder));
//        String fullPathName = dictItem == null ? researchUnit : dictItem.getItemText();
//        return fullPathName;
//    }
//
//    @Override
//    @CachePut(value = CacheConstant.SYS_DICT_CACHE,key = "'customs_direct'")
//    public List<DictItem> getDirectCustoms() {
//        //获取直属关
//        List<ParaCustoms> paraCustomsList = paraCustomsService.getDirectCustoms();
//
//        //构造成字典的形式
//        List<DictItem> result = new ArrayList<>();
//        if(CollectionUtils.isNotEmpty(paraCustomsList)){
//            for (ParaCustoms item : paraCustomsList) {
//                DictItem dictItem = new DictItem();
//                dictItem.setId(item.getCustomsId());
//                dictItem.setDictCode("DIRECT_CUSTOMS");
//                dictItem.setItemText(item.getCustomsName());
//                dictItem.setItemValue(item.getCustomsCode());
//                result.add(dictItem);
//            }
//        }
//        //按照关区号从小到大排序 查询时按照排序号排序
////        result=result.stream()
////                .sorted(Comparator.comparing(DictItem::getItemValue))
////                .collect(Collectors.toList());
//        return result;
//    }
//
//    @Override
//    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "'customs_direct_all'")
//    public List<DictItem> getDirectCustomsAll() {
//        //获取直属关
//        List<ParaCustoms> paraCustomsList = paraCustomsService.list();
//
//        //构造成字典的形式
//        List<DictItem> result = new ArrayList<>();
//        if(CollectionUtils.isNotEmpty(paraCustomsList)){
//            for (ParaCustoms item : paraCustomsList) {
//                DictItem dictItem = new DictItem();
//                dictItem.setId(item.getCustomsId());
//                dictItem.setDictCode("DIRECT_CUSTOMS");
//                dictItem.setItemText(item.getCustomsName());
//                dictItem.setItemValue(item.getCustomsCode());
//                result.add(dictItem);
//            }
//        }
//        //按照关区号从小到大排序 查询时按照排序号排序
////        result=result.stream()
////                .sorted(Comparator.comparing(DictItem::getItemValue))
////                .collect(Collectors.toList());
//        return result;
//    }
//
//
//    @Override
//    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "'customs_sub' +'_'+ #customsCode ")
//    public List<DictItem> getSubordinateCustoms(String customsCode) {
//
//        //通过直属关获取隶属关
//        List<ParaCustoms> paraCustomsList = paraCustomsService.getSubordinateCustoms(customsCode);
//
//        //构造成字典的形式
//        List<DictItem> result = new ArrayList<>();
//        if(CollectionUtils.isNotEmpty(paraCustomsList)){
//            for (ParaCustoms item : paraCustomsList) {
//                String itemValue=item.getCustomsCode();
//                if (itemValue!=null && itemValue.length()==4){
//                    DictItem dictItem = new DictItem();
//                    dictItem.setId(item.getCustomsId());
//                    dictItem.setDictCode("REGIONAL_CUSTOMS");
//                    dictItem.setItemText(item.getCustomsName());
//                    dictItem.setItemValue(item.getCustomsCode());
//                    result.add(dictItem);
//                }
//            }
//        }
//        //按照关区号从小到大排序 查询时按照排序号排序
////        result=result.stream()
////                .sorted(Comparator.comparing(DictItem::getItemValue))
////                .collect(Collectors.toList());
//        return result;
//    }
//
//    @Override
//    @Cacheable(value = CacheConstant.SYS_DICT_CACHE,key = "'customsChild' +'_'+ #customsCode ")
//    public List<DictItem> getChildCustoms(String customsCode) {
//
//        //通过上级ID获取下级列表信息
//        List<ParaCustoms> paraCustomsList = paraCustomsService.getChildCustoms(customsCode);
//
//        //构造成字典的形式
//        List<DictItem> result = new ArrayList<>();
//        if(CollectionUtils.isNotEmpty(paraCustomsList)){
//            for (ParaCustoms item : paraCustomsList) {
//                DictItem dictItem = new DictItem();
//                dictItem.setId(item.getCustomsId());
//                dictItem.setDictCode("USED_PLACE");
//                dictItem.setItemText(item.getCustomsName());
//                dictItem.setItemValue(item.getCustomsCode());
//                result.add(dictItem);
//            }
//        }
//        return result;
//    }
//
//    /**
//     * 构建组合设备目录树
//     *
//     * @param dictNode
//     * @param catalogMap
//     * @return
//     */
//    public DictEqCatNodeVO buildCompositeTree(DictNodeVo dictNode, Map<String, List<EquipmentCatalog>> catalogMap) {
//        DictEqCatNodeVO outputNode = new DictEqCatNodeVO();
//        outputNode.setItemText(dictNode.getItemText());
//        outputNode.setItemValue(dictNode.getItemValue());
//        outputNode.setId(dictNode.getId());
//        outputNode.setParentItemId(dictNode.getParentItemId());
//        outputNode.setType(false);
//        List<DictEqCatNodeVO> children = new ArrayList<>();
//        //递归处理子节点
//        for (DictNodeVo child : dictNode.getChildren()) {
//            children.add(buildCompositeTree(child, catalogMap));
//        }
//        //如果是叶子节点，挂载设备目录数据
//        if (dictNode.getChildren().isEmpty()) {
//            List<EquipmentCatalog> equipmentCatalogs = catalogMap.get(dictNode.getItemValue());
//            if (equipmentCatalogs != null) {
//                for (EquipmentCatalog equipmentCatalog : equipmentCatalogs) {
//                    LocalDate now = LocalDate.now(Clock.systemDefaultZone());
//                    String deviceName = equipmentCatalog.getDeviceName();
//                    if (StringUtils.isNotBlank(deviceName)) {
//                        boolean isRepeal = false;
//                        //废止时间
//                        LocalDate abolishDate = equipmentCatalog.getAbolishDate();
//                        //发布时间
//                        LocalDate publishDate = equipmentCatalog.getPublishDate();
//
//                        //根据发布日期、废止日期自动识别状态：
//                        //1）未发布：没填写“发布日期”时；
//                        //2）发布：填写“发布日期”时且到达发布日期未到达废止日期时；
//                        //3）废止：已到达填写的“废止日期”时。
//
//                        //已废止添加“（废止）”尾缀，未发布添加“（未发布）”尾缀，已发布不添加尾缀；
//                        if (ObjectUtils.isNotEmpty(abolishDate)) {
//                            if (abolishDate.isBefore(now) || abolishDate.isEqual(now)) {
//                                deviceName = deviceName + "（废止）";
//                                isRepeal = true;
//                            }
//                        }
//                        //判断是否废止
//                        if (!isRepeal) {
//                            if (ObjectUtils.isEmpty(publishDate) || publishDate.isAfter(now)) {
//                                deviceName = deviceName + "（未发布）";
//                            }
//                        }
//                    }
//                    //创建设备节点，无子节点
//                    DictEqCatNodeVO dictEqCatNodeVO = new DictEqCatNodeVO(equipmentCatalog.getId(), outputNode.getId(), equipmentCatalog.getId(), deviceName, true);
//                    children.add(dictEqCatNodeVO);
//                }
//            }
//        }
//        outputNode.setChildren(children);
//        return outputNode;
//    }
//
}
