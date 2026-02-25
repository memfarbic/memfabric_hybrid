# SMEM Smem_BM 模块逐行解读

## 模块概述

Smem_BM (Big Memory) 模块是 Smem 的全局内存管理 API，提供跨节点的统一内存视图。该模块基于 HyBM 的实体管理，实现了：

1. **全局内存加入** - 将本地内存暴露给远程 Rank
2. **Rank 间拓扑** - 管理节点间的内存映射关系
3. **数据拷贝** - 提供统一的数据拷贝接口
4. **配置存储同步** - 通过 ConfigStore 同步配置信息

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| smem_bm.cpp | 300+ | BM C API 实现 |
| smem_bm_entry.h/cpp | 200+ | BM 入口管理 |
| smem_bm_entry_manager.h/cpp | 100+ | BM 入口管理器 |
| smem_hybm_helper.h | - | HyBM 辅助函数 |

---

## 1. smem_bm.cpp - BM C API 实现

### 文件信息
- 文件路径: `src/smem/csrc/smem_bm/smem_bm.cpp`
- 代码行数: 300+ 行
- 主要功能: 提供 smem_bm_* C API

### 全局变量和配置初始化 (行 23-43)

```cpp
using namespace ock::smem;
using namespace ock::mf;
ReadWriteLock g_smemBmMutex_;
bool g_smemBmInited = false;

SMEM_API int32_t smem_bm_config_init(smem_bm_config_t *config)
{
    SM_VALIDATE_RETURN(config != nullptr, "Invalid config", SM_INVALID_PARAM);
    config->initTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->createTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->controlOperationTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->startConfigStoreServer = true;
    config->startConfigStoreOnly = false;
    config->dynamicWorldSize = false;
    config->unifiedAddressSpace = true;
    config->autoRanking = true;
    config->rankId = std::numeric_limits<uint16_t>::max();
    config->flags = 0;
    bzero(config->hcomUrl, sizeof(config->hcomUrl));
    bzero(&config->hcomTlsConfig, sizeof(config->hcomTlsConfig));
    bzero(&config->storeTlsConfig, sizeof(config->storeTlsConfig));
    return SM_OK;
}
```

**逐行解读**:
- 第 23 行: 引入命名空间
- 第 24 行: 全局读写锁，保护初始化状态
- 第 25 行: 全局初始化标志
- 第 26-43 行: `smem_bm_config_init` - 初始化默认配置
  - 第 29 行: `initTimeout` - 初始化超时（默认值）
  - 第 30 行: `createTimeout` - 创建超时（默认值）
  - 第 31 行: `controlOperationTimeout` - 控制操作超时
  - 第 32 行: `startConfigStoreServer` - 自动启动配置存储服务
  - 第 33 行: `startConfigStoreOnly` - 仅启动配置存储
  - 第 34 行: `dynamicWorldSize` - 动态 world size
  - 第 35 行: `unifiedAddressSpace` - 统一地址空间（必须为 true）
  - 第 36 行: `autoRanking` - 自动排序
  - 第 37 行: `rankId` - 默认最大值（需要在初始化时设置）
  - 第 41-42 行: 清零 URL 和 TLS 配置

### smem_bm_init() - 初始化 BM (行 62-93)

```cpp
SMEM_API int32_t smem_bm_init(const char *storeURL, uint32_t worldSize, uint16_t deviceId,
                              const smem_bm_config_t *config)
{
    SM_VALIDATE_RETURN(worldSize != 0, "invalid param, worldSize is 0", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(worldSize <= SMEM_WORLD_SIZE_MAX, "invalid param, worldSize is too large", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(storeURL != nullptr, "invalid param, storeURL is null", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(SmemBmConfigCheck(config) == 0, "config is invalid", SM_INVALID_PARAM);

    WriteGuard locker(g_smemBmMutex_);
    if (g_smemBmInited) {
        SM_LOG_INFO("smem bm initialized already");
        return SM_OK;
    }

    int32_t ret = SmemBmEntryManager::Instance().Initialize(storeURL, worldSize, deviceId, *config);
    if (ret != 0) {
        SM_LOG_AND_SET_LAST_ERROR("init bm entry manager failed, result: " << ret);
        return SM_ERROR;
    }

    ret = hybm_init(deviceId, config->flags);
    if (ret != 0) {
        SM_LOG_AND_SET_LAST_ERROR("init hybm failed, result: " << ret << ", flags: 0x" << std::hex << config->flags);
        SmemBmEntryManager::Instance().Destroy();
        return SM_ERROR;
    }

    g_smemBmInited = true;
    SM_LOG_INFO("smem_bm_init success. "
                << " config_ip: " << storeURL);
    return SM_OK;
}
```

**逐行解读**:
- 第 62-67 行: 参数校验
- 第 70-74 行: 检查是否已初始化
- 第 76-80 行: 初始化 BM 入口管理器
- 第 82-87 行: 初始化底层 HyBM
- 第 89-92 行: 设置初始化标志

### smem_bm_create() - 创建 BM 实例 (行 107-143)

```cpp
SMEM_API smem_bm_t smem_bm_create(uint32_t id, uint64_t localDRAMSize, uint64_t localHBMSize,
                                smem_bm_mem_type *memTypes, uint32_t rankSize, uint32_t rankId, uint64_t symmetricSize,
                                smem_shm_data_op_type dataOpType, uint32_t flags)
{
    SM_VALIDATE_RETURN(HybmHasInited(), "hybm not initialized", SM_ERROR);
    SM_LOG_DEBUG("smem_bm_create: " << " id: " << id << ", localDRAMSize: 0x" << std::hex << localDRAMSize
                                  << ", localHBMSize: 0x" << localHBMSize
                                  << ", rankSize: " << rankSize);

    if (symmetricSize == 0) {
        symmetricSize = localDRAMSize + localHBMSize;
    }

    smem_bm_t handle = SmemBmEntryManager::Instance().CreateEntry(id, localDRAMSize, localHBMSize, memTypes, rankSize,
                                                                       rankId, symmetricSize, dataOpType, flags);
    BM_LOG_INFO("smem_bm_create success, handle: " << handle);
    return handle;
}
```

**逐行解读**:
- 第 107-114 行: 函数签名参数
  - `id`: BM 实例 ID
  - `localDRAMSize`: 本地 DRAM 大小
  - `localHBMSize`: 本地 HBM 大小
  - `memTypes`: 内存类型数组
  - `rankSize`: Rank 数量
  - `rankId`: 本地 Rank ID
  - `symmetricSize`: 对称大小
  - `dataOpType`: 数据操作类型
  - `flags`: 标志位
- 第 116-118 行: 默认对称大小为本地内存总和
- 第 120-122 行: 调用入口管理器创建实体
- 第 123-124 行: 打印成功日志并返回句柄

### smem_bm_copy() - 数据拷贝 (行 168-175)

```cpp
SMEM_API int32_t smem_bm_copy(smem_bm_t handle, const smem_copy_params *params, smem_bm_copy_type type, uint32_t flags)
{
    SM_VALIDATE_RETURN(HybmHasInited(), "hybm not initialized", SM_ERROR);
    SM_VALIDATE_RETURN(handle != nullptr, "invalid handle", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params != nullptr, "invalid params", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->src != nullptr, "invalid src ptr", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->dest != nullptr, "invalid dest ptr", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->dataSize > 0, "invalid data size", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(type < SMEM_BM_COPY_BUTT, "invalid copy type", SM_INVALID_PARAM);

    auto entity = MemEntityFactory::Instance().FindEngineByPtr(handle);
    SM_VALIDATE_RETURN(entity != nullptr, "find entity by ptr failed", SM_INVALID_PARAM);

    smem_copy_params newParams = *params;
    auto ret = entity->CopyData(newParams, type, nullptr, flags);
    if (ret != SM_OK) {
        SM_LOG_ERROR("smem_bm_copy failed, result: " << ret);
        return ret;
    }

    SM_LOG_DEBUG("smem_bm_copy success, handle: " << handle);
    return SM_OK;
}
```

**逐行解读**:
- 第 168 行: 函数签名
  - `handle`: BM 句柄
  - `params`: 拷贝参数（源地址、目标地址、大小）
  - `type`: 拷贝类型
  - `flags`: 标志位
- 第 169-175 行: 参数校验
- 第 176-178 行: 通过句柄查找实体
- 第 180-181 行: 准备拷贝参数
- 第 182-187 行: 调用实体的 CopyData 方法

### smem_bm_copy_batch() - 批量数据拷贝 (行 189-222)

```cpp
SMEM_API int32_t smem_bm_copy_batch(smem_bm_t handle, const smem_batch_copy_params *params,
                                     smem_bm_copy_type type, uint32_t flags)
{
    SM_VALIDATE_RETURN(HybmHasInited(), "hybm not initialized", SM_ERROR);
    SM_VALIDATE_RETURN(handle != nullptr, "invalid handle", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params != nullptr, "invalid params", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->sources != nullptr, "invalid sources ptr", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->destinations != nullptr, "invalid destinations ptr", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->dataSizes != nullptr, "invalid sizes ptr", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(params->batchSize != 0, "invalid batch size", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(type < SMEM_BM_COPY_BUTT, "invalid copy type", SM_INVALID_PARAM);

    auto entity = MemEntityFactory::Instance().FindEngineByPtr(handle);
    SM_VALIDATE_RETURN(entity != nullptr, "find entity by ptr failed", SM_INVALID_PARAM);

    smem_batch_copy_params newParams = *params;
    auto ret = entity->BatchCopyData(newParams, type, nullptr, flags);
    if (ret != SM_OK) {
        SM_LOG_ERROR("smem_bm_copy_batch failed, result: " << ret);
        return ret;
    }

    SM_LOG_DEBUG("smem_bm_copy_batch success, handle: " << handle);
    return SM_OK;
}
```

**逐行解读**:
- 第 189 行: 函数签名
  - `handle`: BM 句柄
  - `params`: 批量拷贝参数（源数组、目标数组、大小数组）
  - `type`: 拷贝类型
  - `flags`: 标志位
- 第 190-197 行: 参数校验
- 第 198-199 行: 查找实体
- 第 200-201 行: 准备批量拷贝参数
- 第 202-207 行: 调用实体的 BatchCopyData 方法

---

## 2. smem_bm_entry_manager - BM 入口管理器

### 主要功能

SmemBmEntryManager 是 BM 实体管理器，负责：

1. **实例生命周期管理** - 创建和销毁 BM 实体
2. **配置存储同步** - 通过 ConfigStore 同步 Rank 信息
3. **HyBM 实体集成** - 与底层 HyBM 模块交互
4. **多实例支持** - 支持创建多个 BM 实例

### 关键流程

```
smem_bm_init()
    ├── SmemBmEntryManager::Initialize()
    │   ├── 初始化 ConfigStore
    │   ├── 创建本地 Server
    │   └── hybm_init()
    └── 注册到全局管理器

smem_bm_create()
    └── SmemBmEntryManager::CreateEntry()
        ├── 创建 HyBM 实体
        ├── 分配本地内存
        ├── 注册内存
        ├── 导出内存信息
        └── 同步到 ConfigStore
```

---

## 总结

Smem_BM 模块提供了全局内存管理的上层 API：

### 1. 初始化流程

```
smem_bm_config_init() - 设置默认配置
smem_bm_init() - 初始化
    ├── SmemBmEntryManager::Initialize()
    │   ├── 创建 ConfigStore 连接
    │   ├── 注册到 ConfigStore
    │   └── 同步 Rank 信息
    ├── hybm_init() - 初始化底层 HyBM
    └── 准备建立连接
```

### 2. BM 实例创建

```
smem_bm_create()
    ├── SmemBmEntryManager::CreateEntry()
    │   ├── hybm_create_entity()
    │   ├── 分配本地内存 (DRAM/HBM)
    │   ├── hybm_alloc_local_memory()
    │   ├── hybm_register_local_memory()
    │   ├── hybm_export()
    │   └── 同步 Export 信息到 ConfigStore
    └── 注册到本地 map
```

### 3. 数据拷贝流程

```
smem_bm_copy()
    ├── 根据 handle 查找实体
    ├── 调用 entity->CopyData()
    │   ├── 解析源/目标地址类型
    │   ├── 选择最优传输路径
    │   └── 调用传输层接口
    └── 返回结果
```

### 4. 与底层模块的关系

```
smem_bm (C API)
    ├── smem_shm (共享内存管理)
    ├── smem_trans (传输管理)
    ├── hybm (内存管理)
    │   ├── entity (实体管理)
    │   ├── mm (内存段管理)
    │   ├── transport (传输管理)
    │   └── data_operation (数据操作)
    └── config_store (配置同步)
```

### 5. 关键特性

1. **自动配置**: 默认配置开箱即用
2. **统一地址空间**: UVA (Unified Virtual Address)
3. **自动拓扑**: 自动发现 Rank 拓扑
4. **多传输**: 支持 Device RDMA / Host RDMA / TCP
5. **容错**: 自动重连、断链恢复
