# HYBM Under_API 模块逐行解读

## 模块概述

Under_API 模块是 HyBM 的底层 API 动态加载层，负责在运行时动态加载底层驱动库（如昇腾 ACL/HAL、英伟达 CUDA 等），提供统一的 API 访问接口。该模块通过动态加载技术实现了：

1. **多平台支持** - 同一套代码支持昇腾 NPU 和英伟达 GPU
2. **按需加载** - 只加载当前系统需要的驱动库
3. **版本兼容** - 支持不同版本的驱动 API
4. **错误隔离** - 底层库加载失败不影响上层逻辑

## 目录结构

```
under_api/
├── dl_api.h/cpp                     # 统一动态库加载入口
├── dl_acl_api.h/cpp                 # ACL (Ascend Compute Language) API 加载
├── dl_hal_api.h/cpp                 # HAL (Hardware Abstraction Layer) API 加载
├── dl_hal_api_def.h                 # HAL API 定义
├── dl_hcom_api.h/cpp                # HCOM (Host Communication) API 加载
├── hcom_service_c_define.h          # HCOM 服务 C 接口定义
├── hcom_c_define.h                  # HCOM C 接口定义
├── dl_hccp_api.h/cpp                # HCCP (Huawei Collective Comm) API 加载
├── dl_hccp_def.h                    # HCCP 定义
├── dl_cuda_api.h/cpp                # CUDA API 加载 (NVIDIA GPU)
├── dl_hybrid_api.h                  # Hybrid 统一接口定义
├── dl_hybm_copy_extend.h/cpp        # HYBM 拷贝扩展加载
```

---

## 1. dl_api.h/cpp - 统一动态库加载入口

### 文件信息
- 文件路径: `src/hybm/csrc/under_api/dl_api.h` (33 行)
- 文件路径: `src/hybm/csrc/under_api/dl_api.cpp` (71 行)
- 主要功能: 提供统一的库加载和清理接口

### 头文件解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * ...
*/

#ifndef MEM_FABRIC_HYBRID_DL_API_H
#define MEM_FABRIC_HYBRID_DL_API_H

#include <string>
#include "hybm_types.h"

namespace ock {
namespace mf {

enum class DlApiExtendLibraryType { DL_EXT_LIB_DEVICE_RDMA, DL_EXT_LIB_HOST_RDMA };
```

**逐行解读**:
- 第 1-11 行: 版权声明和许可证信息
- 第 13-14 行: 头文件保护宏
- 第 16-17 行: 引入标准库头文件
  - `<string>`: 字符串类
  - `hybm_types.h`: HyBM 类型定义
- 第 19-20 行: 定义命名空间 `ock::mf`
- 第 21 行: 定义扩展库类型枚举
  - `DL_EXT_LIB_DEVICE_RDMA`: 设备端 RDMA 库 (HCCP)
  - `DL_EXT_LIB_HOST_RDMA`: 主机端 RDMA 库 (HCOM)

```cpp
class DlApi {
public:
    static Result LoadLibrary(const std::string &libDirPath, uint32_t gvaVersion);
    static void CleanupLibrary();
    static Result LoadExtendLibrary(DlApiExtendLibraryType libraryType);
};
} // namespace mf
} // namespace ock

#endif // MEM_FABRIC_HYBRID_DL_API_H
```

**逐行解读**:
- 第 23 行: 定义 DlApi 类，所有方法都是静态的
- 第 25 行: `LoadLibrary` - 加载基础库，参数包括库目录路径和 GVA 版本
- 第 26 行: `CleanupLibrary` - 清理所有已加载的库
- 第 27 行: `LoadExtendLibrary` - 加载扩展库（按需）

### 实现文件解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * ...
*/
#include "dl_api.h"
#include "dl_hybrid_api.h"
#include "dl_hal_api.h"
#include "dl_hccp_api.h"
#include "dl_hcom_api.h"
#include "dl_hybm_copy_extend.h"
```

**逐行解读**:
- 第 1-11 行: 版权声明
- 第 12 行: 引入 dl_api.h 头文件
- 第 13 行: 引入 dl_hybrid_api.h - Hybrid 统一接口
- 第 14 行: 引入 dl_hal_api.h - 硬件抽象层
- 第 15 行: 引入 dl_hccp_api.h - 设备端通信
- 第 16 行: 引入 dl_hcom_api.h - 主机端通信
- 第 17 行: 引入 dl_hybm_copy_extend.h - 拷贝扩展

```cpp
namespace ock {
namespace mf {

Result DlApi::LoadLibrary(const std::string &libDirPath, const uint32_t gvaVersion)
{
    auto result = DlHybridApi::LoadLibrary(libDirPath);
    if (result != BM_OK) {
        return result;
    }
#if defined(ASCEND_NPU)
    result = DlHalApi::LoadLibrary(gvaVersion);
    if (result != BM_OK) {
        DlAclApi::CleanupLibrary();
        return result;
    }

    result = DlHccpApi::LoadLibrary();
    if (result != BM_OK) {
        DlHalApi::CleanupLibrary();
        DlAclApi::CleanupLibrary();
        return result;
    }

    (void)DlHybmExtendApi::TryLoadLibrary();
#endif

    DlHcomApi::LoadLibrary();
    return BM_OK;
}
```

**逐行解读**:
- 第 19-20 行: 进入命名空间
- 第 22 行: LoadLibrary 函数实现
- 第 23-25 行: 首先加载 Hybrid API
- 第 26 行: `ASCEND_NPU` 宏定义时加载昇腾相关库
- 第 27-31 行: 加载 HAL API，失败时清理 ACL
- 第 33-38 行: 加载 HCCP API，失败时清理 HAL 和 ACL
- 第 40 行: 尝试加载 HYBM 扩展 API（可选）
- 第 43 行: 加载 HCOM API（主机通信）
- 第 44 行: 返回成功

```cpp
void DlApi::CleanupLibrary()
{
    DlHccpApi::CleanupLibrary();
    DlAclApi::CleanupLibrary();
    DlHalApi::CleanupLibrary();
    DlHcomApi::CleanupLibrary();
    DlHybmExtendApi::CleanupLibrary();
}

Result DlApi::LoadExtendLibrary(DlApiExtendLibraryType libraryType)
{
    if (libraryType == DlApiExtendLibraryType::DL_EXT_LIB_DEVICE_RDMA) {
        return DlHccpApi::LoadLibrary();
    }

    if (libraryType == DlApiExtendLibraryType::DL_EXT_LIB_HOST_RDMA) {
        return DlHcomApi::LoadLibrary();
    }

    return BM_OK;
}
} // namespace mf
} // namespace ock
```

**逐行解读**:
- 第 49-55 行: CleanupLibrary 按相反顺序清理所有库
- 第 57-70 行: LoadExtendLibrary 按类型加载扩展库
  - 第 60-61 行: 设备 RDMA -> HCCP
  - 第 64-65 行: 主机 RDMA -> HCOM

---

## 2. dl_hal_api.h - HAL API 加载

### 文件信息
- 文件路径: `src/hybm/csrc/under_api/dl_hal_api.h` (526 行)
- 主要功能: 动态加载 HAL (Hardware Abstraction Layer) 库，封装硬件抽象层接口

### 函数指针类型定义 (行 23-72)

```cpp
using halSvmModuleAllocedSizeIncFunc = void (*)(void *, uint32_t, uint32_t, uint64_t);
using halVirtAllocMemFromBaseFunc = uint64_t (*)(void *, size_t, uint32_t, uint64_t);
using halIoctlEnableHeapFunc = int32_t (*)(uint32_t, uint32_t, uint32_t, uint64_t, uint32_t);
using halGetHeapListByTypeFunc = int32_t (*)(void *, void *, void *);
using halVirtSetHeapIdleFunc = int32_t (*)(void *, void *);
using halVirtDestroyHeapV1Func = int32_t (*)(void *, void *);
using halVirtDestroyHeapV2Func = int32_t (*)(void *, void *, bool);
using halVirtGetHeapMgmtFunc = void *(*)(void);
using halIoctlFreePagesFunc = int32_t (*)(uint64_t);
using halVaToHeapIdxFunc = uint32_t (*)(const void *, uint64_t);
```

**逐行解读**:
- 第 23 行: `halSvmModuleAllocedSizeIncFunc` - SVM 模块分配大小增加回调
- 第 24 行: `halVirtAllocMemFromBaseFunc` - 从基地址分配虚拟内存
- 第 25 行: `halIoctlEnableHeapFunc` - ioctl 启用堆
- 第 26 行: `halGetHeapListByTypeFunc` - 按类型获取堆列表
- 第 27 行: `halVirtSetHeapIdleFunc` - 设置堆为空闲状态
- 第 28 行: `halVirtDestroyHeapV1Func` - 销毁堆 V1 版本
- 第 29 行: `halVirtDestroyHeapV2Func` - 销毁堆 V2 版本（带 needDec 参数）
- 第 30 行: `halVirtGetHeapMgmtFunc` - 获取堆管理结构
- 第 31 行: `halIoctlFreePagesFunc` - ioctl 释放页面
- 第 32 行: `halVaToHeapIdxFunc` - 虚拟地址转堆索引

```cpp
using halVirtGetHeapFromQueueFunc = void *(*)(void *, uint32_t, size_t);
using halVirtNormalHeapUpdateInfoFunc = void (*)(void *, void *, void *, void *, uint64_t);
using halVaToHeapFunc = void *(*)(uint64_t);

using halAssignNodeDataFunc = void (*)(uint64_t, uint64_t, uint64_t, uint32_t, void *RbtreeNode);
using halInsertIdleSizeTreeFunc = int32_t (*)(void *RbtreeNode, void *rbtree_queue);
using halInsertIdleVaTreeFunc = int32_t (*)(void *RbtreeNode, void *rbtree_queue);
using halAllocRbtreeNodeFunc = void *(*)(void *rbtree_queue);
using halEraseIdleVaTreeFunc = int32_t (*)(void *RbtreeNode, void *rbtree_queue);
using halEraseIdleSizeTreeFunc = int32_t (*)(void *RbtreeNode, void *rbtree_queue);
using halGetAllocedNodeInRangeFunc = void *(*)(uint64_t va, void *rbtree_queue);
using halGetIdleVaNodeInRangeFunc = void *(*)(uint64_t va, void *rbtree_queue);
using halInsertAllocedTreeFunc = int32_t (*)(void *RbtreeNode, void *rbtree_queue);
using halFreeRbtreeNodeFunc = void (*)(void *RbNode, void *rbtree_queue);
```

**逐行解读**:
- 第 33 行: `halVirtGetHeapFromQueueFunc` - 从队列获取堆
- 第 34 行: `halVirtNormalHeapUpdateInfoFunc` - 更新普通堆信息
- 第 35 行: `halVaToHeapFunc` - 虚拟地址转堆结构
- 第 37-47 行: 红黑树相关函数指针
  - `halAssignNodeDataFunc` - 分配节点数据
  - `halInsertIdleSizeTreeFunc` - 插入空闲大小树
  - `halInsertIdleVaTreeFunc` - 插入空闲 VA 树
  - `halAllocRbtreeNodeFunc` - 分配红黑树节点
  - `halEraseIdleVaTreeFunc` - 擦除空闲 VA 树
  - `halEraseIdleSizeTreeFunc` - 擦除空闲大小树
  - `halGetAllocedNodeInRangeFunc` - 获取范围内的已分配节点
  - `halGetIdleVaNodeInRangeFunc` - 获取范围内的空闲 VA 节点
  - `halInsertAllocedTreeFunc` - 插入已分配树
  - `halFreeRbtreeNodeFunc` - 释放红黑树节点

```cpp
using halSqTaskSendFunc = int (*)(uint32_t, halTaskSendInfo *);
using halCqReportRecvFunc = int (*)(uint32_t, halReportRecvInfo *);
using halSqCqAllocateFunc = int (*)(uint32_t, halSqCqInputInfo *, halSqCqOutputInfo *);
using halSqCqFreeFunc = int (*)(uint32_t, halSqCqFreeInfo *);
using halResourceIdAllocFunc = int (*)(uint32_t, struct halResourceIdInputInfo *, struct halResourceIdOutputInfo *);
using halResourceIdFreeFunc = int (*)(uint32_t, struct halResourceIdInputInfo *);
using halResourceConfigFunc = int (*)(uint32_t, struct halResourceIdInputInfo *, struct halResourceConfigInfo *);
using halSqCqQueryFunc = int (*)(uint32_t devId, struct halSqCqQueryInfo *info);
using halHostRegisterFunc = int (*)(void *, uint64_t, uint32_t, uint32_t, void **);
using halHostUnregisterExFunc = int (*)(void *, uint32_t, uint32_t);
using drvNotifyIdAddrOffsetFunc = int (*)(uint32_t, struct drvNotifyInfo *);
```

**逐行解读**:
- 第 48 行: `halSqTaskSendFunc` - SQ (Send Queue) 任务发送
- 第 49 行: `halCqReportRecvFunc` - CQ (Completion Queue) 报告接收
- 第 50 行: `halSqCqAllocateFunc` - SQ/CQ 分配
- 第 51 行: `halSqCqFreeFunc` - SQ/CQ 释放
- 第 52 行: `halResourceIdAllocFunc` - 资源 ID 分配
- 第 53 行: `halResourceIdFreeFunc` - 资源 ID 释放
- 第 54 行: `halResourceConfigFunc` - 资源配置
- 第 55 行: `halSqCqQueryFunc` - SQ/CQ 查询
- 第 56 行: `halHostRegisterFunc` - 主机内存注册
- 第 57 行: `halHostUnregisterExFunc` - 主机内存注销
- 第 58 行: `drvNotifyIdAddrOffsetFunc` - 驱动通知 ID 地址偏移

```cpp
using halMemAddressReserveFunc = int (*)(void **, size_t, size_t, void *, uint64_t);
using halMemAddressFreeFunc = int (*)(void *);
using halMemCreateFunc = int (*)(drv_mem_handle_t **, size_t, const struct drv_mem_prop *, uint64_t);
using halMemReleaseFunc = int (*)(drv_mem_handle_t *);
using halMemMapFunc = int (*)(void *, size_t, size_t, drv_mem_handle_t *, uint64_t);
using halMemUnmapFunc = int (*)(void *);
using halMemSetAccessFunc = int (*)(void *, size_t, struct drv_mem_access_desc *, size_t);
using halMemExportFunc = int (*)(drv_mem_handle_t *, drv_mem_handle_type, uint64_t, struct MemShareHandle *);
using halMemImportFunc = int (*)(drv_mem_handle_type, struct MemShareHandle *, uint32_t, drv_mem_handle_t **);
using halMemShareHandleSetAttributeFunc = int (*)(uint64_t, enum ShareHandleAttrType, struct ShareHandleAttr);
using halMemTransShareableHandleFunc = int (*)(drv_mem_handle_type, struct MemShareHandle *, uint32_t *, uint64_t *);
using halMemGetAllocationGranularityFunc = int (*)(const struct drv_mem_prop *, drv_mem_granularity_options, size_t *);
```

**逐行解读**:
- 第 60 行: `halMemAddressReserveFunc` - 内存地址预留
- 第 61 行: `halMemAddressFreeFunc` - 内存地址释放
- 第 62 行: `halMemCreateFunc` - 内存句柄创建
- 第 63 行: `halMemReleaseFunc` - 内存句柄释放
- 第 64 行: `halMemMapFunc` - 内存映射
- 第 65 行: `halMemUnmapFunc` - 内存解映射
- 第 66 行: `halMemSetAccessFunc` - 设置内存访问权限
- 第 67 行: `halMemExportFunc` - 导出内存共享句柄
- 第 68 行: `halMemImportFunc` - 导入内存共享句柄
- 第 69 行: `halMemShareHandleSetAttributeFunc` - 设置共享句柄属性
- 第 70 行: `halMemTransShareableHandleFunc` - 转换可共享句柄
- 第 71 行: `halMemGetAllocationGranularityFunc` - 获取分配粒度

### DlHalApi 类定义 (行 73-459)

```cpp
class DlHalApi {
public:
    static Result LoadLibrary(uint32_t gvaVersion);
    static void CleanupLibrary();
    static void CleanupHalApi();

    static inline void HalSvmModuleAllocedSizeInc(void *type, uint32_t devid, uint32_t moduleId, uint64_t size)
    {
        if (pSvmModuleAllocedSizeInc == nullptr) {
            return;
        }
        return pSvmModuleAllocedSizeInc(type, devid, moduleId, size);
    }
```

**逐行解读**:
- 第 73 行: DlHalApi 类定义
- 第 75 行: `LoadLibrary` - 加载 HAL 库
- 第 76 行: `CleanupLibrary` - 清理 HAL 库
- 第 77 行: `CleanupHalApi` - 清理 HAL API
- 第 79-85 行: 内联函数封装，调用函数指针
  - 检查函数指针是否为空
  - 为空则直接返回
  - 非空则调用底层函数

```cpp
    static inline uint64_t HalVirtAllocMemFromBase(void *mgmt, size_t size, uint32_t advise, uint64_t allocPtr)
    {
        if (pVirtAllocMemFromBase == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pVirtAllocMemFromBase(mgmt, size, advise, allocPtr);
    }

    static inline Result HalIoctlEnableHeap(uint32_t heapIdx, uint32_t heapType, uint32_t subType, uint64_t heapSize,
                                            uint32_t heapListType)
    {
        if (pIoctlEnableHeap == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pIoctlEnableHeap(heapIdx, heapType, subType, heapSize, heapListType);
    }
```

**逐行解读**:
- 第 87-93 行: 虚拟内存分配封装
- 第 95-102 行: ioctl 启用堆封装
  - 函数指针为空时返回 `BM_UNDER_API_UNLOAD` 错误码

```cpp
    static inline int HalHostRegister(void *srcPtr, uint64_t size, uint32_t flag, uint32_t devid, void **dstPtr)
    {
        if (pHalHostRegister == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pHalHostRegister(srcPtr, size, flag, devid, dstPtr);
    }

    static inline int HalHostUnregisterEx(void *srcPtr, uint32_t devid, uint32_t flag)
    {
        if (pHalHostUnregisterEx == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pHalHostUnregisterEx(srcPtr, devid, flag);
    }
```

**逐行解读**:
- 第 335-341 行: 主机内存注册封装
  - `srcPtr`: 源指针（主机内存）
  - `size`: 大小
  - `flag`: 标志（如 HOST_MEM_MAP_DEV）
  - `devid`: 设备 ID
  - `dstPtr`: 输出的目标指针（设备可访问的地址）
- 第 343-349 行: 主机内存注销封装

```cpp
    static inline int HalMemExport(drv_mem_handle_t *handle, drv_mem_handle_type type, uint64_t flags,
                                   struct MemShareHandle *sHandle)
    {
        if (pHalMemExport == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pHalMemExport(handle, type, flags, sHandle);
    }

    static inline int HalMemImport(drv_mem_handle_type type, struct MemShareHandle *sHandle, uint32_t devid,
                                   drv_mem_handle_t **handle)
    {
        if (pHalMemImport == nullptr) {
            return BM_UNDER_API_UNLOAD;
        }
        return pHalMemImport(type, sHandle, devid, handle);
    }
```

**逐行解读**:
- 第 415-422 行: 内存导出封装
  - `handle`: 内存句柄
  - `type`: 句柄类型
  - `flags`: 导出标志
  - `sHandle`: 输出的共享句柄（可跨进程传递）
- 第 424-431 行: 内存导入封装
  - `type`: 句柄类型
  - `sHandle`: 共享句柄（从其他进程接收）
  - `devid`: 设备 ID
  - `handle`: 输出的内存句柄

### 静态成员变量 (行 460-520)

```cpp
private:
    static Result LoadHybmVmmLibrary(uint32_t gvaVersion);
    static Result LoadHybmV1V2Library(uint32_t gvaVersion);

private:
    static std::mutex gMutex;
    static bool gLoaded;
    static void *halHandle;
    static const char *gAscendHalLibName;

    static halSvmModuleAllocedSizeIncFunc pSvmModuleAllocedSizeInc;
    static halVirtAllocMemFromBaseFunc pVirtAllocMemFromBase;
    static halIoctlEnableHeapFunc pIoctlEnableHeap;
    // ... 更多函数指针
};
```

**逐行解读**:
- 第 461-462 行: 私有辅助方法
  - `LoadHybmVmmLibrary` - 加载 VMM 版本 HAL 库
  - `LoadHybmV1V2Library` - 加载 V1/V2 版本 HAL 库
- 第 464 行: `gMutex` - 加载互斥锁
- 第 465 行: `gLoaded` - 加载状态标志
- 第 466 行: `halHandle` - 动态库句柄
- 第 467 行: `gAscendHalLibName` - 库名称
- 第 469-519 行: 所有函数指针成员

---

## 3. dl_hcom_api.h - HCOM API 加载

### 文件信息
- 文件路径: `src/hybm/csrc/under_api/dl_hcom_api.h` (478 行)
- 主要功能: 动态加载 HCOM (Host Communication) 库，封装主机端通信接口

### 函数指针类型定义 (行 21-76)

```cpp
using serviceCreateFunc = int (*)(Service_Type, const char *, Service_Options, Hcom_Service *);
using serviceBindFunc = int (*)(Hcom_Service, const char *, Service_ChannelHandler);
using serviceStartFunc = int (*)(Hcom_Service);
using serviceDestroyFunc = int (*)(Hcom_Service, const char *);
using serviceConnectFunc = int (*)(Hcom_Service, const char *, Hcom_Channel *, Service_ConnectOptions);
using serviceDisConnectFunc = int (*)(Hcom_Service, Hcom_Channel);
```

**逐行解读**:
- 第 21 行: `serviceCreateFunc` - 创建 HCOM 服务
- 第 22 行: `serviceBindFunc` - 绑定服务到地址
- 第 23 行: `serviceStartFunc` - 启动服务
- 第 24 行: `serviceDestroyFunc` - 销毁服务
- 第 25 行: `serviceConnectFunc` - 连接到远程服务
- 第 26 行: `serviceDisConnectFunc` - 断开连接

```cpp
using serviceRegisterMemoryRegionFunc = int (*)(Hcom_Service, uint64_t, Service_MemoryRegion *);
using serviceGetMemoryRegionInfoFunc = int (*)(Service_MemoryRegion, Service_MemoryRegionInfo *);
using serviceRegisterAssignMemoryRegionFunc = int (*)(Hcom_Service, uintptr_t, uint64_t, Service_MemoryRegion *);
using serviceDestroyMemoryRegionFunc = int (*)(Hcom_Service, Service_MemoryRegion);
```

**逐行解读**:
- 第 27 行: `serviceRegisterMemoryRegionFunc` - 注册内存区域（分配大小）
- 第 28 行: `serviceGetMemoryRegionInfoFunc` - 获取内存区域信息
- 第 29 行: `serviceRegisterAssignMemoryRegionFunc` - 注册指定地址的内存区域
- 第 30 行: `serviceDestroyMemoryRegionFunc` - 销毁内存区域

```cpp
using channelSendFunc = int (*)(Hcom_Channel, Channel_Request, Channel_Callback *);
using channelCallFunc = int (*)(Hcom_Channel, Channel_Request, Channel_Response *, Channel_Callback *);
using channelReplyFunc = int (*)(Hcom_Channel, Channel_Request, Channel_ReplyContext, Channel_Callback *);
using channelPutFunc = int (*)(Hcom_Channel, Channel_OneSideRequest, Channel_Callback *);
using channelBatchPutFunc = int (*)(Hcom_Channel, Channel_OneSideRequestSgl, Channel_Callback *);
using channelGetFunc = int (*)(Hcom_Channel, Channel_OneSideRequest, Channel_Callback *);
using channelBatchGetFunc = int (*)(Hcom_Channel, Channel_OneSideRequestSgl, Channel_Callback *);
```

**逐行解读**:
- 第 57 行: `channelSendFunc` - 发送请求（双向通信）
- 第 58 行: `channelCallFunc` - 调用请求（带响应）
- 第 59 行: `channelReplyFunc` - 回复请求
- 第 60 行: `channelPutFunc` - 单边写（RDMA WRITE）
- 第 61 行: `channelBatchPutFunc` - 批量单边写（散列写）
- 第 62 行: `channelGetFunc` - 单边读（RDMA READ）
- 第 63 行: `channelBatchGetFunc` - 批量单边读（散列读）

### DlHcomApi 类定义 (行 77-475)

```cpp
class DlHcomApi {
public:
    static Result LoadLibrary();
    static void CleanupLibrary();

    static inline int ServiceCreate(Service_Type t, const char *name, Service_Options options, Hcom_Service *service)
    {
        BM_ASSERT_RETURN(gServiceCreate != nullptr, BM_UNDER_API_UNLOAD);
        return gServiceCreate(t, name, options, service);
    }

    static inline int ServiceBind(Hcom_Service service, const char *listenerUrl, Service_ChannelHandler h)
    {
        BM_ASSERT_RETURN(gServiceBind != nullptr, BM_UNDER_API_UNLOAD);
        return gServiceBind(service, listenerUrl, h);
    }

    static inline int ServiceStart(Hcom_Service service)
    {
        BM_ASSERT_RETURN(gServiceStart != nullptr, BM_UNDER_API_UNLOAD);
        return gServiceStart(service);
    }
```

**逐行解读**:
- 第 77-78 行: 加载和清理库方法
- 第 80-86 行: ServiceCreate 封装
  - `t`: 服务类型（TCP/RoCE/UB/UBC）
  - `name`: 服务名称
  - `options`: 服务选项（线程优先级、队列大小等）
  - `service`: 输出的服务句柄
- 第 88-92 行: ServiceBind 封装
  - `listenerUrl`: 监听地址（如 "ip:port"）
  - `h`: 新连接回调
- 第 94-98 行: ServiceStart 封装

```cpp
    static inline int ChannelPut(Hcom_Channel channel, Channel_OneSideRequest req, Channel_Callback *cb)
    {
        BM_ASSERT_RETURN(gChannelPut != nullptr, BM_UNDER_API_UNLOAD);
        return gChannelPut(channel, req, cb);
    }

    static inline int ChannelPutV(Hcom_Channel channel, Channel_OneSideRequestSgl req, Channel_Callback *cb)
    {
        BM_ASSERT_RETURN(gChannelBatchPut != nullptr, BM_UNDER_API_UNLOAD);
        return gChannelBatchPut(channel, req, cb);
    }

    static inline int ChannelGet(Hcom_Channel channel, Channel_OneSideRequest req, Channel_Callback *cb)
    {
        BM_ASSERT_RETURN(gChannelGet != nullptr, BM_UNDER_API_UNLOAD);
        return gChannelGet(channel, req, cb);
    }
```

**逐行解读**:
- 第 304-308 行: ChannelPut - 单边写（RDMA WRITE）
- 第 310-314 行: ChannelPutV - 批量单边写（散列写）
- 第 316-320 行: ChannelGet - 单边读（RDMA READ）

---

## 4. dl_acl_api - ACL API 加载

### 主要功能

ACL (Ascend Compute Language) 是昇腾 NPU 的计算语言 API，类似于 NVIDIA 的 CUDA API。

### 关键函数类型

**内存管理**:
- `aclrtMalloc` - 分配设备内存
- `aclrtFree` - 释放设备内存
- `aclrtMallocHost` - 分配主机内存（可被设备 DMA 访问）
- `aclrtMemcpy` - 内存拷贝
- `aclrtMemcpyAsync` - 异步内存拷贝

**设备管理**:
- `aclrtSetDevice` - 设置当前设备
- `aclrtGetDevice` - 获取当前设备
- `aclrtDeviceEnablePeerAccess` - 启用 P2P 访问

**流管理**:
- `aclrtCreateStream` - 创建流
- `aclrtDestroyStream` - 销毁流
- `aclrtSynchronizeStream` - 同步流

**IPC 内存**:
- `RtIpcSetMemoryName` - 设置 IPC 内存名称
- `RtIpcOpenMemory` - 打开 IPC 内存

---

## 总结

Under_API 模块实现了完整的底层 API 动态加载抽象：

### 1. 设计模式

**外观模式 (Facade)**: DlApi 类提供统一的加载入口，隐藏各个子库的加载细节

**策略模式**: 根据编译宏（ASCEND_NPU/NO_XPU）和运行时配置选择加载不同的库

**单例模式**: 各个 DlApi 类使用静态方法管理全局唯一的函数指针表

### 2. 动态加载流程

```
DlApi::LoadLibrary()
    ├── DlHybridApi::LoadLibrary()      // 加载 Hybrid 基础库
    ├── DlHalApi::LoadLibrary()         // 加载 HAL 库 (昇腾)
    │   ├── LoadHybmVmmLibrary()       // VMM 版本
    │   └── LoadHybmV1V2Library()      // V1/V2 版本
    ├── DlHccpApi::LoadLibrary()        // 加载 HCCP (设备 RDMA)
    ├── DlHcomApi::LoadLibrary()        // 加载 HCOM (主机 RDMA)
    └── DlHybmExtendApi::TryLoadLibrary() // 加载拷贝扩展 (可选)
```

### 3. 错误处理

所有内联函数在调用前检查函数指针：
- 为空时返回 `BM_UNDER_API_UNLOAD` 错误码
- 非空时调用底层函数

### 4. 内存操作封装

| 操作 | HAL API | ACL API | 用途 |
|------|---------|---------|------|
| 虚拟地址分配 | HalVirtAllocMemFromBase | AclrtMalloc | 设备内存分配 |
| 堆管理 | HalVirtSetHeapIdle | - | 堆空闲管理 |
| 红黑树 | HalInsertIdleSizeTree | - | 空闲块管理 |
| SQ/CQ | HalSqCqAllocate | - | 队列对管理 |
| 主机注册 | HalHostRegister | - | DMA 可访问主机内存 |
| 内存导出 | HalMemExport | RtIpcSetMemoryName | 跨进程共享 |
| 内存导入 | HalMemImport | RtIpcOpenMemory | 跨进程导入 |

### 5. 通信 API

| API | 类型 | 函数 |
|-----|------|------|
| HCOM | 主机 RDMA | ChannelPut/Get (单边) |
| HCCP | 设备 RDMA | RaSendWrV2 (工作请求发送) |
