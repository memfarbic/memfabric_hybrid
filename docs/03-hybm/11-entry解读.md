# HYBM Entry 模块逐行解读

## 模块概述

Entry 模块是 HyBM 的对外 API 入口层，提供 C 语言接口供外部调用。该模块负责：

1. **初始化管理** - 库的初始化和清理
2. **实体管理** - 创建和销毁内存实体
3. **数据拷贝** - 提供统一的数据拷贝接口
4. **内存操作** - 分配、注册、导出/导入内存
5. **日志配置** - 设置日志级别和外部日志函数

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| hybm_entry.cpp | 167 | 初始化、配置接口 |
| hybm_big_mem_entry.cpp | 220 | 实体和内存管理接口 |
| hybm_data_op_entry.cpp | 132 | 数据拷贝接口 |

---

## 1. hybm_entry.cpp - 初始化和配置接口

### 文件信息
- 文件路径: `src/hybm/csrc/hybm_entry.cpp`
- 代码行数: 167 行
- 主要功能: 提供初始化、反初始化和日志配置接口

### 头文件引用 (行 1-28)

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * ...
*/

#include <cstdlib>
#include <fstream>
#include <mutex>
#include <string>
#include <regex>
#include "devmm_svm_gva.h"
#include "hybm.h"
#include "hybm_ptracer.h"
#include "hybm_common_include.h"
#include "hybm_gva.h"
#include "hybm_gva_version.h"
#include "hybm_version.h"
#include "mf_file_util.h"
#include "hybm_stream_manager.h"
#include "under_api/dl_api.h"
```

**逐行解读**:
- 第 1-11 行: 版权声明
- 第 13 行: `<cstdlib>` - 通用工具函数
- 第 14 行: `<fstream>` - 文件流
- 第 15 行: `<mutex>` - 互斥锁
- 第 16 行: `<string>` - 字符串类
- 第 17 行: `<regex>` - 正则表达式
- 第 18 行: `devmm_svm_gva.h` - 设备内存管理 SVM GVA
- 第 19 行: `hybm.h` - HyBM 主接口
- 第 20 行: `hybm_ptracer.h` - 性能追踪器
- 第 21 行: `hybm_common_include.h` - 公共头文件聚合
- 第 22 行: `hybm_gva.h` - GVA 管理
- 第 23 行: `hybm_gva_version.h` - GVA 版本
- 第 24 行: `hybm_version.h` - 版本信息
- 第 25 行: `mf_file_util.h` - 文件工具
- 第 26 行: `hybm_stream_manager.h` - 流管理器
- 第 27 行: `under_api/dl_api.h` - 动态库加载

### 全局变量 (行 31-38)

```cpp
using namespace ock::mf;

namespace {

uint64_t g_baseAddr = 0ULL;
int64_t initialized = 0;
int32_t initedDeviceId = -1;

std::mutex initMutex;
} // namespace
```

**逐行解读**:
- 第 29 行: 引入 ock::mf 命名空间
- 第 31 行: 匿名命名空间，限制全局变量作用域
- 第 33 行: `g_baseAddr` - GVA 基地址，全局虚拟地址空间的起始地址
- 第 34 行: `initialized` - 初始化计数器，支持多次初始化（引用计数）
- 第 35 行: `initedDeviceId` - 已初始化的设备 ID
- 第 37 行: `initMutex` - 初始化互斥锁，保证线程安全

### 辅助函数 (行 40-48)

```cpp
int32_t HybmGetInitDeviceId()
{
    return initedDeviceId;
}

bool HybmHasInited()
{
    return initialized > 0;
}
```

**逐行解读**:
- 第 40-43 行: `HybmGetInitDeviceId()` - 获取已初始化的设备 ID
- 第 45-48 行: `HybmHasInited()` - 检查是否已初始化

### hybm_load_library() - 加载动态库 (行 50-74)

```cpp
static inline Result hybm_load_library()
{
    std::string libPath;
#if defined(ASCEND_NPU)
    char *path = std::getenv("ASCEND_HOME_PATH");
    BM_VALIDATE_RETURN(path != nullptr, "Environment ASCEND_HOME_PATH is not set.", BM_ERROR);
    libPath = std::string(path).append("/lib64");
    if (!ock::mf::FileUtil::Realpath(libPath) || !ock::mf::FileUtil::IsDir(libPath)) {
        BM_LOG_ERROR("Environment ASCEND_HOME_PATH check failed.");
        return BM_ERROR;
    }
#elif defined(NVIDIA_GPU)
    char *path = std::getenv("CUDA_HOME");
    BM_VALIDATE_RETURN(path != nullptr, "Environment CUDA_HOME is not set.", BM_ERROR);
    libPath = std::string(path).append("/lib64");
    if (!ock::mf::FileUtil::Realpath(libPath) || !ock::mf::FileUtil::IsDir(libPath)) {
        BM_LOG_ERROR("Environment CUDA_HOME check failed.");
        return BM_ERROR;
    }
#endif

    auto ret = DlApi::LoadLibrary(libPath, HybmGetGvaVersion());
    BM_LOG_ERROR_RETURN_IT_IF_NOT_OK(ret, "load library from path failed: " << ret << ", path:" << libPath);
    return BM_OK;
}
```

**逐行解读**:
- 第 51 行: 定义 libPath 变量存储库路径
- 第 52-60 行: 昇腾 NPU 平台处理
  - 第 53 行: 获取 `ASCEND_HOME_PATH` 环境变量
  - 第 54 行: 验证环境变量已设置
  - 第 55 行: 拼接 `/lib64` 子目录
  - 第 56-59 行: 验证路径存在且为目录
- 第 61-68 行: 英伟达 GPU 平台处理
  - 第 62 行: 获取 `CUDA_HOME` 环境变量
  - 第 63 行: 验证环境变量已设置
  - 第 64 行: 拼接 `/lib64` 子目录
  - 第 65-68 行: 验证路径存在且为目录
- 第 70 行: 调用 `DlApi::LoadLibrary` 加载所有必要库
- 第 71 行: 失败时记录错误并返回
- 第 72 行: 返回成功

### hybm_init() - 初始化 HYBM (行 76-116)

```cpp
HYBM_API int32_t hybm_init(uint16_t deviceId, uint64_t flags)
{
    std::unique_lock<std::mutex> lockGuard{initMutex};
    if (initialized > 0) {
        if (initedDeviceId != deviceId) {
            BM_LOG_ERROR("this deviceId(" << deviceId << ") is not equal to the deviceId(" << initedDeviceId
                                          << ") of other module!");
            return BM_ERROR;
        }

        /*
         * hybm_init will be accessed multiple times when bm/shm/trans init
         * incremental loading is required here.
         */
        BM_LOG_ERROR_RETURN_IT_IF_NOT_OK(hybm_load_library(), "load library failed");

        initialized++;
        return 0;
    }
```

**逐行解读**:
- 第 76 行: `HYBM_API` 宏，标记为导出的 C API
- 第 76 行: 函数签名，参数为设备 ID 和标志
- 第 77 行: 加锁保证线程安全
- 第 78-94 行: 已初始化分支处理（多次初始化支持）
  - 第 79-84 行: 检查设备 ID 是否与已初始化的一致
  - 第 86-89 行: 注释说明增量加载需求
  - 第 90 行: 再次加载库（确保所有符号可用）
  - 第 92 行: 增加初始化计数
  - 第 93 行: 返回成功

```cpp
    BM_LOG_ERROR_RETURN_IT_IF_NOT_OK(HalGvaPrecheck(), "the current version of ascend driver does not support mf!");
    BM_LOG_ERROR_RETURN_IT_IF_NOT_OK(hybm_load_library(), "load library failed");
    ptracer_config_t config{.tracerType = 1, .dumpFilePath = "/var/log/memfabric_hybrid"};
    auto ret = ptracer_init(&config);
    if (ret != BM_OK) {
        BM_LOG_WARN("init ptracer module failed, result: " << ret << ", error msg: " << ptracer_get_last_err_msg());
    }

    ret = hybm_init_hbm_gva(deviceId, flags, g_baseAddr);
    if (ret != BM_OK) {
        ptracer_uninit();
        DlApi::CleanupLibrary();
        BM_LOG_ERROR("set device id to be " << deviceId << " failed: " << ret);
        return BM_ERROR;
    }

    initedDeviceId = deviceId;
    initialized = 1L;
    BM_LOG_INFO("hybm init successfully, " << LIB_VERSION << ", deviceId: " << deviceId);
    return 0;
}
```

**逐行解读**:
- 第 96 行: 检查驱动版本兼容性
- 第 97 行: 加载动态库
- 第 98 行: 配置性能追踪器
  - `tracerType = 1`: 启用追踪
  - `dumpFilePath`: 日志输出路径
- 第 99-102 行: 初始化追踪器（失败只警告）
- 第 104 行: 初始化 HBM GVA 地址空间
- 第 105-110 行: 失败清理路径
  - 清理追踪器
  - 清理动态库
- 第 112-113 行: 保存设备 ID，设置初始化标志
- 第 114 行: 打印成功日志
- 第 115 行: 返回成功

### hybm_uninit() - 反初始化 (行 118-141)

```cpp
HYBM_API void hybm_uninit()
{
    std::unique_lock<std::mutex> lockGuard{initMutex};
    if (initialized <= 0L) {
        BM_LOG_WARN("hybm not initialized.");
        return;
    }

    if (--initialized > 0L) {
        return;
    }

    ptracer_uninit();
    if (g_baseAddr != 0) {
        drv::HalGvaFree(HYBM_DEVICE_META_ADDR, HYBM_DEVICE_INFO_SIZE);
        auto ret = drv::HalGvaUnreserveMemory(g_baseAddr);
        BM_LOG_INFO("uninitialize GVA memory return: " << ret);
        g_baseAddr = 0ULL;
    }

    HybmStreamManager::DestroyAllThreadHybmStream();
    DlApi::CleanupLibrary();
    initialized = 0;
}
```

**逐行解读**:
- 第 118 行: 导出的 C API
- 第 119 行: 加锁
- 第 120-124 行: 检查是否已初始化
- 第 126-128 行: 减少引用计数，非最后一个则直接返回
- 第 130 行: 清理性能追踪器
- 第 131-136 行: 释放 GVA 内存
  - 释放设备元数据区
  - 取消预留内存
  - 重置基址
- 第 138 行: 销毁所有线程流
- 第 139 行: 清理动态库
- 第 140 行: 重置初始化标志

### 日志配置函数 (行 143-167)

```cpp
HYBM_API void hybm_set_extern_logger(void (*logger)(int level, const char *msg))
{
    if (logger == nullptr) {
        return;
    }

    if (ock::mf::OutLogger::Instance().GetExternalLogFunction() != nullptr) {
        BM_LOG_WARN("External log function has already been set, which will be override with new log function");
    }
    ock::mf::OutLogger::Instance().SetExternalLogFunction(logger, true);
}

HYBM_API int32_t hybm_set_log_level(int level)
{
    BM_VALIDATE_RETURN(ock::mf::OutLogger::ValidateLevel(level),
                       "set log level failed, invalid param, level should be 0~3", -1);
    ock::mf::OutLogger::Instance().SetLogLevel(static_cast<ock::mf::LogLevel>(level));
    return 0;
}

HYBM_API const char *hybm_get_error_string(int32_t errCode)
{
    static thread_local std::string info = std::string("error(").append(std::to_string(errCode)).append(")");
    return info.c_str();
}
```

**逐行解读**:
- 第 143-153 行: 设置外部日志回调函数
  - 用于集成到上层框架的日志系统
- 第 155-161 行: 设置日志级别（0-3）
- 第 163-167 行: 获取错误字符串描述

---

## 2. hybm_big_mem_entry.cpp - 实体和内存管理接口

### 文件信息
- 文件路径: `src/hybm/csrc/hybm_big_mem_entry.cpp`
- 代码行数: 220 行
- 主要功能: 提供实体创建、内存分配、导出/导入等接口

### hybm_create_entity() - 创建实体 (行 20-40)

```cpp
HYBM_API hybm_entity_t hybm_create_entity(uint16_t id, const hybm_options *options, uint32_t flags)
{
    BM_ASSERT_RETURN(HybmHasInited(), nullptr);

    auto &factory = MemEntityFactory::Instance();
    std::shared_ptr<MemEntityDefault> entity = nullptr;
    entity =  factory.GetOrCreateEngine(id, flags);
    if (entity == nullptr) {
        BM_LOG_ERROR("create entity failed.");
        return nullptr;
    }

    auto ret = entity->Initialize(options);
    if (ret != 0) {
        MemEntityFactory::Instance().RemoveEngine(entity.get());
        BM_LOG_ERROR("initialize entity failed: " << ret);
        return nullptr;
    }

    return entity.get();
}
```

**逐行解读**:
- 第 20 行: 导出的 C API，创建内存实体
- 第 22 行: 检查是否已初始化
- 第 24 行: 获取实体工厂单例
- 第 26 行: 获取或创建实体（支持按 ID 复用）
- 第 27-30 行: 创建失败处理
- 第 32 行: 初始化实体
- 第 33-37 行: 初始化失败清理
- 第 39 行: 返回实体指针

### hybm_destroy_entity() - 销毁实体 (行 42-49)

```cpp
HYBM_API void hybm_destroy_entity(hybm_entity_t e, uint32_t flags)
{
    BM_ASSERT_RET_VOID(e != nullptr);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RET_VOID(entity != nullptr);
    entity->UnInitialize();
    MemEntityFactory::Instance().RemoveEngine(e);
}
```

**逐行解读**:
- 第 42 行: 导出的 C API，销毁内存实体
- 第 44 行: 检查实体非空
- 第 45 行: 从工厂查找实体
- 第 47 行: 反初始化实体
- 第 48 行: 从工厂移除实体

### 内存空间预留 (行 51-65)

```cpp
HYBM_API int32_t hybm_reserve_mem_space(hybm_entity_t e, uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);
    return entity->ReserveMemorySpace();
}

HYBM_API int32_t hybm_unreserve_mem_space(hybm_entity_t e, uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);
    return entity->UnReserveMemorySpace();
}
```

**逐行解读**:
- 第 51-57 行: 预留内存空间
- 第 59-65 行: 取消预留内存空间

### 内存分配和释放 (行 82-104)

```cpp
HYBM_API hybm_mem_slice_t hybm_alloc_local_memory(hybm_entity_t e, hybm_mem_type mType, uint64_t size, uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, nullptr);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, nullptr);
    hybm_mem_slice_t slice;
    auto ret = entity->AllocLocalMemory(size, mType, flags, slice);
    if (ret != 0) {
        BM_LOG_ERROR("allocate slice with size: " << size << ", mType: " << mType << " failed: " << ret);
        return nullptr;
    }

    return slice;
}

HYBM_API int32_t hybm_free_local_memory(hybm_entity_t e, hybm_mem_slice_t slice, uint32_t count, uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(slice != nullptr, BM_INVALID_PARAM);
    return entity->FreeLocalMemory(slice, flags);
}
```

**逐行解读**:
- 第 82-95 行: 分配本地内存
  - `mType`: 内存类型（HBM 或 DRAM）
  - `size`: 分配大小
  - 返回内存切片句柄
- 第 97-104 行: 释放本地内存

### 导出和导入 (行 122-175)

```cpp
HYBM_API int32_t hybm_export(hybm_entity_t e, hybm_mem_slice_t slice, uint32_t flags, hybm_exchange_info *exInfo)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(exInfo != nullptr, BM_INVALID_PARAM);

    ExchangeInfoWriter writer(exInfo);
    if ((flags & HYBM_FLAG_EXPORT_ENTITY) != 0) {
        auto ret = entity->ExportExchangeInfo(writer, 0);
        if (ret != 0) {
            BM_LOG_ERROR("export entity data failed: " << ret);
            return ret;
        }
    } else {
        auto ret = entity->ExportExchangeInfo(slice, writer, flags);
        if (ret != 0) {
            BM_LOG_ERROR("export slices: " << slice << " failed: " << ret);
            return ret;
        }
    }

    return BM_OK;
}

HYBM_API int32_t hybm_import(hybm_entity_t e, const hybm_exchange_info allExInfo[], uint32_t count, void *addresses[],
                             uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(allExInfo != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(count > 0, BM_INVALID_PARAM);

    std::vector<ExchangeInfoReader> readers(count);
    for (auto i = 0U; i < count; i++) {
        readers[i].Reset(allExInfo + i);
    }
    if ((flags & HYBM_FLAG_EXPORT_ENTITY) != 0) {
        return entity->ImportEntityExchangeInfo(readers.data(), count, flags);
    }
    return entity->ImportExchangeInfo(readers.data(), count, addresses, flags);
}
```

**逐行解读**:
- 第 122-145 行: 导出内存信息
  - `HYBM_FLAG_EXPORT_ENTITY`: 导出整个实体而非单个切片
  - 使用 ExchangeInfoWriter 序列化信息
- 第 158-175 行: 导入内存信息
  - 支持批量导入多个 Rank 的信息
  - 使用 ExchangeInfoReader 反序列化信息

---

## 3. hybm_data_op_entry.cpp - 数据拷贝接口

### 文件信息
- 文件路径: `src/hybm/csrc/hybm_data_op_entry.cpp`
- 代码行数: 132 行
- 主要功能: 提供数据拷贝和批量拷贝接口

### 拷贝方向检查表 (行 22-30)

```cpp
using hybm_check_enum = enum { OP_CHECK_IDX = 0U, OP_CHECK_SRC, OP_CHECK_DEST, OP_CHECK_BUTT };

static uint32_t g_checkMap[HYBM_DATA_COPY_DIRECTION_BUTT][OP_CHECK_BUTT] = {
    {HYBM_LOCAL_HOST_TO_GLOBAL_HOST, false, true},   {HYBM_LOCAL_HOST_TO_GLOBAL_DEVICE, false, true},
    {HYBM_LOCAL_DEVICE_TO_GLOBAL_HOST, false, true}, {HYBM_LOCAL_DEVICE_TO_GLOBAL_DEVICE, false, true},
    {HYBM_GLOBAL_HOST_TO_GLOBAL_HOST, true, true},   {HYBM_GLOBAL_HOST_TO_GLOBAL_DEVICE, true, true},
    {HYBM_GLOBAL_HOST_TO_LOCAL_HOST, true, false},   {HYBM_GLOBAL_HOST_TO_LOCAL_DEVICE, true, false},
    {HYBM_GLOBAL_DEVICE_TO_GLOBAL_HOST, true, true}, {HYBM_GLOBAL_DEVICE_TO_GLOBAL_DEVICE, true, true},
    {HYBM_GLOBAL_DEVICE_TO_LOCAL_HOST, true, false}, {HYBM_GLOBAL_DEVICE_TO_LOCAL_DEVICE, true, false}};
```

**逐行解读**:
- 第 22 行: 检查类型枚举
  - `OP_CHECK_IDX`: 索引
  - `OP_CHECK_SRC`: 检查源地址
  - `OP_CHECK_DEST`: 检查目标地址
- 第 24-30 行: 二维检查表
  - 第一维: 拷贝方向
  - 第二维: 检查类型
  - 值含义: `{方向枚举值, 是否检查源, 是否检查目标}`

### hybm_data_copy() - 数据拷贝 (行 32-73)

```cpp
HYBM_API int32_t hybm_data_copy(hybm_entity_t e, hybm_copy_params *params, hybm_data_copy_direction direction,
                                void *stream, uint32_t flags)
{
    BM_LOG_DEBUG("Src: " << VaToInfo(params->src) << ", dest: " << VaToInfo(params->dest));
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->src != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->dest != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->dataSize != 0, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(direction < HYBM_DATA_COPY_DIRECTION_BUTT, BM_INVALID_PARAM);

    if (direction == HYBM_DATA_COPY_DIRECTION_AUTO) {
        auto& vaMgr = ock::mf::HybmVaManager::GetInstance();
        direction = vaMgr.InferCopyDirection(reinterpret_cast<uint64_t>(params->src),
                                             reinterpret_cast<uint64_t>(params->dest));
        if (direction == HYBM_DATA_COPY_DIRECTION_BUTT) {
            BM_LOG_ERROR("Failed to auto infer copy direction, src=0x"
                         << std::hex << reinterpret_cast<uint64_t>(params->src) <<
                         ", dest=0x" << reinterpret_cast<uint64_t>(params->dest));
            return BM_INVALID_PARAM;
        }
    }
```

**逐行解读**:
- 第 32 行: 导出的 C API，数据拷贝
- 第 33-34 行: 打印调试日志
- 第 35-40 行: 参数校验
- 第 43-53 行: 自动推断拷贝方向
  - 当 direction 为 AUTO 时，根据源/目标地址类型推断

```cpp
    auto entity = MemEntityFactory::Instance().FindEngineByPtr(e);
    BM_ASSERT_RETURN(entity != nullptr, BM_INVALID_PARAM);

    bool addressValid = true;
    if (g_checkMap[direction][OP_CHECK_DEST]) {
        addressValid = entity->CheckAddressInEntity(params->dest, params->dataSize);
    }
    if (g_checkMap[direction][OP_CHECK_SRC]) {
        addressValid = (addressValid && entity->CheckAddressInEntity(params->src, params->dataSize));
    }

    if (!addressValid) {
        BM_LOG_ERROR("input copy address out of entity range, size: " << std::oct << params->dataSize
                                                                      << ", direction: " << direction);
        return BM_INVALID_PARAM;
    }

    return entity->CopyData(*params, direction, stream, flags);
}
```

**逐行解读**:
- 第 55-56 行: 获取实体
- 第 58-64 行: 地址范围校验
  - 根据检查表决定是否检查源/目标地址
- 第 66-70 行: 地址无效处理
- 第 72 行: 调用实体的 CopyData 方法

### hybm_data_batch_copy() - 批量数据拷贝 (行 85-132)

```cpp
HYBM_API int32_t hybm_data_batch_copy(hybm_entity_t e, hybm_batch_copy_params *params,
                                      hybm_data_copy_direction direction, void *stream, uint32_t flags)
{
    BM_ASSERT_RETURN(e != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->sources != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->destinations != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->dataSizes != nullptr, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(params->batchSize != 0, BM_INVALID_PARAM);
    BM_ASSERT_RETURN(direction < HYBM_DATA_COPY_DIRECTION_BUTT, BM_INVALID_PARAM);
    BM_LOG_DEBUG("Src[0]: " << VaToInfo(params->sources[0]) << ", dest[0]: " << VaToInfo(params->destinations[0]));
```

**逐行解读**:
- 第 85 行: 导出的 C API，批量数据拷贝
- 第 87-95 行: 参数校验
- 第 96 行: 打印第一个元素的调试日志

```cpp
    if (direction == HYBM_DATA_COPY_DIRECTION_AUTO) {
        auto &vaMgr = ock::mf::HybmVaManager::GetInstance();
        direction = vaMgr.InferCopyDirection(reinterpret_cast<uint64_t>(params->sources[0]),
                                             reinterpret_cast<uint64_t>(params->destinations[0]));
        if (UNLIKELY(direction == HYBM_DATA_COPY_DIRECTION_BUTT)) {
            BM_LOG_ERROR("Failed to auto infer copy direction, src=0x"
                         << std::hex << reinterpret_cast<uint64_t>(params->sources[0]) << ", dest=0x" <<
                         std::hex << reinterpret_cast<uint64_t>(params->destinations[0]));
            return BM_INVALID_PARAM;
        }
    }

    bool addressValid = true;
    auto entity = (MemEntity *)e;
    bool check_dst = g_checkMap[direction][OP_CHECK_DEST];
    bool check_src = g_checkMap[direction][OP_CHECK_SRC];
    for (uint32_t i = 0; i < params->batchSize; i++) {
        if (params->sources[i] == nullptr || params->destinations[i] == nullptr) {
            BM_LOG_ERROR("input copy address is invalid, source or dest is nullptr, index:" << i);
            return BM_INVALID_PARAM;
        }
        if (check_dst) {
            addressValid = entity->CheckAddressInEntity(params->destinations[i], params->dataSizes[i]);
        }
        if (check_src) {
            addressValid = (addressValid && entity->CheckAddressInEntity(params->sources[i], params->dataSizes[i]));
        }

        if (!addressValid) {
            BM_LOG_ERROR("input copy address out of entity range, size: " << std::oct << params->dataSizes[i]
                                                                          << ", direction: " << direction);
            return BM_INVALID_PARAM;
        }
    }
    return entity->BatchCopyData(*params, direction, stream, flags);
}
```

**逐行解读**:
- 第 97-107 行: 自动推断拷贝方向
- 第 109-130 行: 循环检查每个批量元素的地址有效性
- 第 131 行: 调用实体的 BatchCopyData 方法

### hybm_wait() - 等待完成 (行 75-83)

```cpp
HYBM_API int32_t hybm_wait(hybm_entity_t e)
{
    if (e == nullptr) {
        BM_LOG_ERROR("input parameter invalid, e: 0x" << std::hex << e);
        return BM_INVALID_PARAM;
    }
    auto entity = static_cast<MemEntity *>(e);
    return entity->Wait();
}
```

**逐行解读**:
- 第 75 行: 导出的 C API，等待所有异步操作完成
- 第 76-80 行: 参数校验
- 第 81 行: 转换为实体指针
- 第 82 行: 调用实体的 Wait 方法

---

## 总结

Entry 模块提供了完整的 C API 接口：

### 1. 初始化流程

```
hybm_init()
    ├── HalGvaPrecheck()           // 检查驱动版本
    ├── DlApi::LoadLibrary()        // 加载驱动库
    ├── ptracer_init()              // 初始化性能追踪
    └── hybm_init_hbm_gva()         // 初始化 HBM GVA
```

### 2. 实体生命周期

```
hybm_create_entity()               // 创建实体
    ├── MemEntityFactory::GetOrCreateEngine()
    └── entity->Initialize()

hybm_destroy_entity()              // 销毁实体
    ├── entity->UnInitialize()
    └── MemEntityFactory::RemoveEngine()
```

### 3. 内存操作

| API | 功能 |
|-----|------|
| hybm_reserve_mem_space | 预留内存空间 |
| hybm_unreserve_mem_space | 取消预留 |
| hybm_alloc_local_memory | 分配本地内存 |
| hybm_free_local_memory | 释放本地内存 |
| hybm_register_local_memory | 注册外部内存 |
| hybm_export | 导出内存信息 |
| hybm_import | 导入内存信息 |
| hybm_mmap | 映射内存 |
| hybm_unmap | 解映射内存 |

### 4. 数据拷贝

| API | 功能 |
|-----|------|
| hybm_data_copy | 单次数据拷贝 |
| hybm_data_batch_copy | 批量数据拷贝 |
| hybm_wait | 等待异步操作完成 |

### 5. 拷贝方向

HYBM 支持 10 种拷贝方向：

| 方向 | 说明 |
|------|------|
| LOCAL_HOST_TO_GLOBAL_HOST | 本地主机 → 全局主机 |
| LOCAL_HOST_TO_GLOBAL_DEVICE | 本地主机 → 全局设备 |
| LOCAL_DEVICE_TO_GLOBAL_HOST | 本地设备 → 全局主机 |
| LOCAL_DEVICE_TO_GLOBAL_DEVICE | 本地设备 → 全局设备 |
| GLOBAL_HOST_TO_GLOBAL_HOST | 全局主机 → 全局主机 |
| GLOBAL_HOST_TO_GLOBAL_DEVICE | 全局主机 → 全局设备 |
| GLOBAL_HOST_TO_LOCAL_HOST | 全局主机 → 本地主机 |
| GLOBAL_HOST_TO_LOCAL_DEVICE | 全局主机 → 本地设备 |
| GLOBAL_DEVICE_TO_GLOBAL_HOST | 全局设备 → 全局主机 |
| GLOBAL_DEVICE_TO_GLOBAL_DEVICE | 全局设备 → 全局设备 |
| GLOBAL_DEVICE_TO_LOCAL_HOST | 全局设备 → 本地主机 |
| GLOBAL_DEVICE_TO_LOCAL_DEVICE | 全局设备 → 本地设备 |
| AUTO | 自动推断 |

### 6. 引用计数

hybm_init/hybm_uninit 支持引用计数：
- 第一次 init 初始化所有资源
- 后续 init 只增加计数
- 最后一次 uninit 才真正清理资源
- 允许不同模块（BM/SHM/Trans）独立初始化
