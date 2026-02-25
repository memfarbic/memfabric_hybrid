# SMEM Smem_SHM 模块逐行解读

## 模块概述

Smem_SHM (Shared Memory) 模块是 Smem 的共享内存管理 API，提供多进程/多节点的共享内存功能。该模块基于 HyBM 的实体管理，实现了：

1. **共享内存创建** - 创建跨节点的对称共享内存
2. **集合通信** - 提供 Barrier 和 AllGather 等集合通信原语
3. **拓扑查询** - 查询节点间的可达性和传输类型
4. **原子操作** - 提供分布式原子编号分配

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| smem_shm.cpp | 385 | SHM C API 实现 |
| smem_shm_entry.h/cpp | 319 | SHM 入口管理 |
| smem_shm_entry_manager.h/cpp | 154 | SHM 入口管理器 |

---

## 1. smem_shm.cpp - SHM C API 实现

### 文件信息
- 文件路径: `src/smem/csrc/smem_shm/smem_shm.cpp`
- 代码行数: 385 行
- 主要功能: 提供 smem_shm_* C API

### 头文件引用和全局变量 (行 1-21)

```cpp
#include <algorithm>
#include "hybm_big_mem.h"
#include "smem_logger.h"
#include "smem_shm_entry.h"
#include "smem_shm_entry_manager.h"
#include "smem_shm.h"

using namespace ock::smem;
std::mutex g_smemShmMutex_;
bool g_smemShmInited = false;
```

**逐行解读**:
- 第 12 行: `<algorithm>` - 算法库
- 第 13 行: `hybm_big_mem.h` - HyBM 大内存管理
- 第 14 行: `smem_logger.h` - 日志工具
- 第 15 行: `smem_shm_entry.h` - SHM 入口类
- 第 16 行: `smem_shm_entry_manager.h` - SHM 入口管理器
- 第 17 行: `smem_shm.h` - SHM C API 头文件
- 第 19 行: 引入 smem 命名空间
- 第 20 行: 全局互斥锁，保护初始化状态
- 第 21 行: 全局初始化标志

### smem_shm_config_init() - 配置初始化 (行 269-292)

```cpp
SMEM_API int32_t smem_shm_config_init(smem_shm_config_t *config)
{
    SM_VALIDATE_RETURN(config != nullptr, "invalid param, config is NULL", SM_INVALID_PARAM);
    config->shmInitTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->shmCreateTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->controlOperationTimeout = SMEM_DEFAUT_WAIT_TIME;
    config->startConfigStoreServer = true;
    config->flags = 0;
    return SM_OK;
}

static int32_t SmemShmConfigCheck(const smem_shm_config_t *config)
{
    SM_VALIDATE_RETURN(config != nullptr, "config is null", SM_INVALID_PARAM);

    SM_VALIDATE_RETURN(config->shmInitTimeout != 0, "initTimeout is zero", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(config->shmInitTimeout <= SMEM_SHM_TIMEOUT_MAX, "initTimeout is too large", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(config->shmCreateTimeout != 0, "createTimeout is zero", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(config->shmCreateTimeout <= SMEM_SHM_TIMEOUT_MAX, "initTimeout is too large", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(config->controlOperationTimeout != 0, "controlOperationTimeout is zero", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(config->controlOperationTimeout <= SMEM_SHM_TIMEOUT_MAX, "controlOperationTimeout is too large",
                       SM_INVALID_PARAM);
    return 0;
}
```

**逐行解读**:
- 第 270 行: 参数校验，config 不能为空
- 第 272-274 行: 设置默认超时时间
- 第 275 行: 默认启动配置存储服务器
- 第 276 行: 清零标志位
- 第 281-291 行: 配置校验函数
  - 检查超时值不为零
  - 检查超时值不超过最大值

### smem_shm_init() - 初始化 SHM (行 294-327)

```cpp
SMEM_API int32_t smem_shm_init(const char *configStoreIpPort, uint32_t worldSize, uint32_t rankId, uint16_t deviceId,
                               smem_shm_config_t *config)
{
    SM_VALIDATE_RETURN(configStoreIpPort != nullptr, "invalid param, ipport is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(SmemShmConfigCheck(config) == 0, "config is invalid", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(!(worldSize > SMEM_WORLD_SIZE_MAX || rankId >= worldSize),
                       "invalid param, input size: " << worldSize << " limit: " << SMEM_WORLD_SIZE_MAX
                                                     << " input rank: " << rankId,
                       SM_INVALID_PARAM);

    std::lock_guard<std::mutex> guard(g_smemShmMutex_);
    if (g_smemShmInited) {
        SM_LOG_INFO("smem shm initialized already");
        return SM_OK;
    }

    int32_t ret = SmemShmEntryManager::Instance().Initialize(configStoreIpPort, worldSize, rankId, deviceId, config);
    if (ret != 0) {
        SM_LOG_AND_SET_LAST_ERROR("init shm entry manager failed, result: " << ret);
        return SM_ERROR;
    }

    uint64_t flags = static_cast<uint64_t>(config->flags) | HYBM_FLAG_INIT_SHMEM_META;
    ret = hybm_init(deviceId, flags);
    if (ret != 0) {
        SmemShmEntryManager::Instance().Destroy();
        SM_LOG_AND_SET_LAST_ERROR("init hybm failed, result: " << ret << ", flags: 0x" << std::hex << config->flags);
        return SM_ERROR;
    }

    g_smemShmInited = true;
    SM_LOG_INFO("smem_shm_init success. world_size: " << worldSize);
    return SM_OK;
}
```

**逐行解读**:
- 第 297-302 行: 参数校验
  - 检查配置存储 URL 不为空
  - 检查配置有效
  - 检查 worldSize 和 rankId 有效
- 第 304 行: 加锁保护初始化过程
- 第 305-308 行: 检查是否已初始化
- 第 310-314 行: 初始化入口管理器
- 第 316 行: 设置初始化标志，包括 SHM 元数据
- 第 317-322 行: 初始化底层 HyBM
- 第 324 行: 设置初始化标志

### smem_shm_create() - 创建 SHM 实例 (行 23-74)

```cpp
SMEM_API smem_shm_t smem_shm_create(uint32_t id, uint32_t rankSize, uint32_t rankId, uint64_t symmetricSize,
                                    smem_shm_data_op_type dataOpType, uint32_t flags, void **gva)
{
    SM_VALIDATE_RETURN(!(rankSize > SMEM_WORLD_SIZE_MAX || rankId >= rankSize),
                       "invalid param, input size: " << rankSize << " limit: " << SMEM_WORLD_SIZE_MAX
                                                     << " input rank: " << rankId,
                       nullptr);
    SM_VALIDATE_RETURN(!(id > SMEM_ID_MAX), "invalid id, id range is: [0, " << SMEM_ID_MAX << "]", nullptr);
    SM_VALIDATE_RETURN(gva != nullptr, "invalid param, gva is NULL", nullptr);
    SM_VALIDATE_RETURN(g_smemShmInited, "smem shm not initialized yet", nullptr);
    SM_VALIDATE_RETURN(symmetricSize <= SMEM_LOCAL_HBM_SIZE_MAX, "symmetric size exceeded", nullptr);

    std::lock_guard<std::mutex> guard(g_smemShmMutex_);
    SmemShmEntryPtr entry = nullptr;
    auto &manager = SmemShmEntryManager::Instance();
    auto ret = manager.CreateEntryById(id, entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("malloc entry failed, id: " << id << ", result: " << ret);
        return nullptr;
    }

    hybm_options options{};
    options.bmType = HYBM_TYPE_AI_CORE_INITIATE;
    options.memType = HYBM_MEM_TYPE_DEVICE;
    options.bmDataOpType = static_cast<hybm_data_op_type>(HYBM_DOP_TYPE_MTE | HYBM_DOP_TYPE_SDMA);
    if (dataOpType & SMEMS_DATA_OP_RDMA) {
        auto temp = static_cast<uint32_t>(options.bmDataOpType) | HYBM_DOP_TYPE_DEVICE_RDMA;
        options.bmDataOpType = static_cast<hybm_data_op_type>(temp);
    }
    options.rankCount = rankSize;
    options.rankId = rankId;
    options.maxHBMSize = symmetricSize;
    options.deviceVASpace = symmetricSize;
    options.role = HYBM_ROLE_PEER;
    options.scene = HYBM_SCENE_SHM;
    bzero(options.transUrl, sizeof(options.transUrl));
    bzero(options.tag, sizeof(options.tag));
    bzero(options.tagOpInfo, sizeof(options.tagOpInfo));
    std::string defaultNic = "tcp://127.0.0.1:10002";
    std::copy_n(defaultNic.c_str(), defaultNic.size() + 1, options.transUrl);
    options.dramShmFd = -1;

    ret = entry->Initialize(options);
    if (ret != 0) {
        SM_LOG_AND_SET_LAST_ERROR("entry init failed, result: " << ret);
        manager.RemoveEntryByPtr(reinterpret_cast<uintptr_t>(entry.Get()));
        return nullptr;
    }

    *gva = entry->GetGva();
    return reinterpret_cast<void *>(entry.Get());
}
```

**逐行解读**:
- 第 26-33 行: 参数校验
  - 检查 rankSize 和 rankId 有效
  - 检查 ID 不超过最大值
  - 检查 gva 指针不为空
  - 检查已初始化
  - 检查对称内存大小不超过最大值
- 第 35 行: 加锁
- 第 37-42 行: 创建入口
- 第 44-61 行: 配置 HyBM 选项
  - bmType: AI Core 发起模式
  - memType: 设备内存
  - bmDataOpType: MTE + SDMA，可能加上 RDMA
  - rankCount/rankId: Rank 信息
  - maxHBMSize/deviceVASpace: 对称内存大小
  - role: PEER（对等模式）
  - scene: SHM（共享内存场景）
- 第 65-70 行: 初始化入口
- 第 72-73 行: 返回 GVA 地址和句柄

### smem_shm_control_barrier() - Barrier 同步 (行 133-147)

```cpp
SMEM_API int32_t smem_shm_control_barrier(smem_shm_t handle)
{
    SM_VALIDATE_RETURN(handle != nullptr, "invalid param, handle is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(g_smemShmInited, "smem shm not initialized yet", SM_NOT_INITIALIZED);

    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return SM_INVALID_PARAM;
    }
    auto group = entry->GetGroup();
    SM_VALIDATE_RETURN(group != nullptr, "smem shm not init group yet", SM_NOT_INITIALIZED);
    return group->GroupBarrier();
}
```

**逐行解读**:
- 第 135-136 行: 参数校验
- 第 138-143 行: 通过句柄查找入口
- 第 145 行: 获取组引擎
- 第 146 行: 调用 Barrier 同步

### smem_shm_control_allgather() - AllGather 集合通信 (行 165-185)

```cpp
SMEM_API int32_t smem_shm_control_allgather(smem_shm_t handle, const char *sendBuf, uint32_t sendSize, char *recvBuf,
                                            uint32_t recvSize)
{
    SM_VALIDATE_RETURN(handle != nullptr, "invalid param, handle is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(sendBuf != nullptr, "invalid param, sendBuf is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(recvBuf != nullptr, "invalid param, recvBuf is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(!(sendSize == 0 || sendSize > UN65536), "Invalid sendSize, sendSize must be 1~65536",
                       SM_INVALID_PARAM);

    SM_VALIDATE_RETURN(g_smemShmInited, "smem shm not initialized yet", SM_NOT_INITIALIZED);

    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return SM_INVALID_PARAM;
    }
    auto group = entry->GetGroup();
    SM_VALIDATE_RETURN(group != nullptr, "smem shm not init group yet", SM_NOT_INITIALIZED);
    return group->GroupAllGather(sendBuf, sendSize, recvBuf, recvSize);
}
```

**逐行解读**:
- 第 168-173 行: 参数校验
- 第 175 行: 检查初始化状态
- 第 177-182 行: 查找入口
- 第 184 行: 调用 AllGather

### smem_shm_topology_can_reach() - 查询拓扑可达性 (行 209-224)

```cpp
SMEM_API int32_t smem_shm_topology_can_reach(smem_shm_t handle, uint32_t remoteRank, uint32_t *reachInfo)
{
    SM_VALIDATE_RETURN(handle != nullptr, "invalid param, handle is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(reachInfo != nullptr, "invalid param, reachInfo is NULL", SM_INVALID_PARAM);

    SM_VALIDATE_RETURN(g_smemShmInited, "smem shm not initialized yet", SM_NOT_INITIALIZED);

    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return SM_INVALID_PARAM;
    }

    return entry->GetReachInfo(remoteRank, *reachInfo);
}
```

**逐行解读**:
- 第 211-216 行: 参数校验
- 第 218-223 行: 查找入口并查询可达性

### smem_shm_atomic_alloc_value() - 原子分配编号 (行 226-251)

```cpp
SMEM_API int32_t smem_shm_atomic_alloc_value(smem_shm_t handle, uint32_t limit, uint32_t *retVal)
{
    SM_VALIDATE_RETURN(handle != nullptr, "invalid param, handle is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(g_smemShmInited, "smem shm not initialized yet", SM_NOT_INITIALIZED);
    SM_VALIDATE_RETURN(retVal != nullptr, "invalid param, retVal is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(limit <= SMEM_SHM_ATOMIC_NUM_LIMIT, "invalid param, limit is too large", SM_INVALID_PARAM);

    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return SM_INVALID_PARAM;
    }
    auto group = entry->GetGroup();
    SM_VALIDATE_RETURN(group != nullptr, "smem shm not init group yet", SM_NOT_INITIALIZED);
    int32_t val = group->AllocNumber();
    if (val >= static_cast<int>(limit)) {
        group->ReleaseNumber(val);
        return SM_ERROR;
    } else if (val < 0) {
        return val;
    } else {
        *retVal = static_cast<uint32_t>(val);
        return SM_OK;
    }
}
```

**逐行解读**:
- 第 228-231 行: 参数校验
- 第 233-240 行: 查找入口
- 第 241 行: 原子分配一个编号
- 第 242-244 行: 超过限制则释放并返回错误
- 第 245-246 行: 负数表示错误
- 第 247-249 行: 成功返回分配的编号

### smem_shm_register_exit() - 注册退出回调 (行 347-366)

```cpp
SMEM_API int32_t smem_shm_register_exit(smem_shm_t handle, void (*exit)(int))
{
    SM_VALIDATE_RETURN(exit != nullptr, "set exit function failed, invalid func which is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(handle != nullptr, "invalid param, handle is NULL", SM_INVALID_PARAM);

    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return SM_INVALID_PARAM;
    }

    SM_VALIDATE_RETURN(entry->GetGroup() != nullptr, "invalid param, Group is NULL", SM_INVALID_PARAM);
    ret = entry->GetGroup()->RegisterExit(exit);
    if (ret != SM_OK) {
        SM_LOG_AND_SET_LAST_ERROR("RegisterExit failed, result: " << ret);
        return SM_ERROR;
    }
    return SM_OK;
}
```

**逐行解读**:
- 第 349-350 行: 参数校验
- 第 352-357 行: 查找入口
- 第 359 行: 获取组引擎
- 第 360-364 行: 注册退出回调

### smem_shm_global_exit() - 全局退出广播 (行 368-385)

```cpp
SMEM_API void smem_shm_global_exit(smem_shm_t handle, int status)
{
    if (handle == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("invalid param, handle is NULL");
        return;
    }
    SmemShmEntryPtr entry = nullptr;
    auto ret = SmemShmEntryManager::Instance().GetEntryByPtr(reinterpret_cast<uintptr_t>(handle), entry);
    if (ret != SM_OK || entry == nullptr) {
        SM_LOG_AND_SET_LAST_ERROR("input handle is invalid, result: " << ret);
        return;
    }
    if (entry->GetGroup() == nullptr) {
        SM_LOG_ERROR("Group is NULL");
        return;
    }
    entry->GetGroup()->GroupBroadcastExit(status);
}
```

**逐行解读**:
- 第 370-373 行: 句柄校验
- 第 375-379 行: 查找入口
- 第 380-383 行: 组引擎检查
- 第 384 行: 广播退出状态

---

## 2. smem_shm_entry.h/cpp - SHM 入口管理

### 文件信息
- 文件路径: `src/smem/csrc/smem_shm/smem_shm_entry.h/cpp`
- 代码行数: 319 行
- 主要功能: SHM 入口类实现

### 类定义 (行 27-92)

```cpp
struct ShmEntryInitStep {
    std::string name;
    std::function<int32_t()> processor;
    std::function<void()> rollback;
    ShmEntryInitStep(std::string nm, std::function<int32_t()> p, std::function<void()> r)
        : name{std::move(nm)}, processor{std::move(p)}, rollback{std::move(r)}
    {}
};

class SmemShmEntry : public SmReferable {
public:
    explicit SmemShmEntry(uint32_t id);
    ~SmemShmEntry() override;

    int32_t Initialize(hybm_options &options);
    void SetConfig(const smem_shm_config_t &config);
    Result SetExtraContext(const void *context, uint32_t size);
    void *GetGva() const;
    SmemGroupEnginePtr GetGroup() const;
    uint32_t Id() const;
    Result GetReachInfo(uint32_t remoteRank, uint32_t &reachInfo) const;

private:
    Result CreateGlobalTeam(uint32_t rankSize, uint32_t rankId);
    int32_t InitStepCreateEntity();
    void InitStepDestroyEntity();
    int32_t InitStepReserveMemory();
    void InitStepUnreserveMemory();
    int32_t InitStepAllocSlice();
    void InitStepFreeSlice();
    int32_t InitStepExchangeSlice();
    int32_t InitStepExchangeEntity();
    int32_t InitStepMap();

private:
    hybm_options options_{};
    std::vector<ShmEntryInitStep> initSteps_;
    SmemGroupEnginePtr globalGroup_ = nullptr;
    smem_shm_config_t extraConfig_;

    bool inited_ = false;
    const uint32_t id_;
    uint32_t localRank_ = UINT32_MAX;
    hybm_entity_t entity_ = nullptr;
    void *gva_ = nullptr;
    hybm_mem_slice_t slice_ = nullptr;

    std::mutex entryMutex_;
};
```

**逐行解读**:
- 第 27-34 行: `ShmEntryInitStep` - 初始化步骤结构体
  - `name`: 步骤名称
  - `processor`: 处理函数
  - `rollback`: 回滚函数
- 第 36-91 行: `SmemShmEntry` 类
  - 继承自 `SmReferable`（引用计数）
  - 公有方法：初始化、配置设置、上下文设置等
  - 私有方法：各初始化步骤
  - 成员变量：选项、步骤列表、组引擎、配置、实体、GVA、切片等

### 构造函数 (行 23-39)

```cpp
SmemShmEntry::SmemShmEntry(uint32_t id) : id_{id}, entity_{nullptr}, gva_{nullptr}
{
    (void)smem_shm_config_init(&extraConfig_);

    auto emptyRollback = []() {};
    initSteps_.emplace_back(ShmEntryInitStep{"01_create_entity", [this]() { return InitStepCreateEntity(); },
                                             [this]() { InitStepDestroyEntity(); }});
    initSteps_.emplace_back(ShmEntryInitStep{"02_reserve_memory", [this]() { return InitStepReserveMemory(); },
                                             [this]() { InitStepUnreserveMemory(); }});
    initSteps_.emplace_back(ShmEntryInitStep{"03_alloc_slice", [this]() { return InitStepAllocSlice(); },
                                             [this]() { InitStepFreeSlice(); }});
    initSteps_.emplace_back(
        ShmEntryInitStep{"04_exchange_slice", [this]() { return InitStepExchangeSlice(); }, emptyRollback});
    initSteps_.emplace_back(
        ShmEntryInitStep{"05_exchange_entity", [this]() { return InitStepExchangeEntity(); }, emptyRollback});
    initSteps_.emplace_back(ShmEntryInitStep{"05_map_memory", [this]() { return InitStepMap(); }, emptyRollback});
}
```

**逐行解读**:
- 第 23 行: 初始化 ID 和指针成员
- 第 25 行: 初始化配置
- 第 27 行: 空回滚函数
- 第 28-38 行: 添加初始化步骤
  - 创建实体 -> 销毁实体
  - 预留内存 -> 取消预留
  - 分配切片 -> 释放切片
  - 交换切片信息（无回滚）
  - 交换实体信息（无回滚）
  - 内存映射（无回滚）

### 初始化流程 (行 79-119)

```cpp
Result SmemShmEntry::CreateGlobalTeam(uint32_t rankSize, uint32_t rankId)
{
    auto client = SmemShmEntryManager::Instance().GetStoreClient();
    SM_ASSERT_RETURN(client != nullptr, SM_INVALID_PARAM);

    std::string prefix = "SHM_(" + std::to_string(id_) + ")_";
    StorePtr store = StoreFactory::PrefixStore(client, prefix);
    SM_ASSERT_RETURN(store != nullptr, SM_ERROR);

    SmemGroupOption opt = {rankSize, rankId,  extraConfig_.controlOperationTimeout * SECOND_TO_MILLSEC,
                           false,    nullptr, nullptr};
    SmemGroupEnginePtr group = SmemNetGroupEngine::Create(store, opt);
    SM_ASSERT_RETURN(group != nullptr, SM_ERROR);

    globalGroup_ = group;
    return globalGroup_->GroupBarrier(); // 保证所有rank都初始化了
}

Result SmemShmEntry::Initialize(hybm_options &options)
{
    localRank_ = options.rankId;
    SM_LOG_ERROR_RETURN_IT_IF_NOT_OK(CreateGlobalTeam(options.rankCount, options.rankId), "create global team failed");

    options_ = options;
    for (auto it = initSteps_.begin(); it != initSteps_.end(); ++it) {
        SM_LOG_DEBUG("process init step : " << it->name);
        auto stepRet = it->processor();
        if (stepRet != 0) {
            SM_LOG_ERROR("init step(" << it->name << ") process failed: " << stepRet);
            auto fit = it;
            while (fit != initSteps_.begin()) {
                --fit;
                fit->rollback();
            }
            return stepRet;
        }
    }

    inited_ = true;
    return SM_OK;
}
```

**逐行解读**:
- 第 81 行: 获取存储客户端
- 第 83-85 行: 创建带前缀的存储
- 第 87-89 行: 配置组选项
- 第 90 行: 创建组引擎
- 第 93-94 行: Barrier 等待所有 Rank
- 第 99 行: 保存本地 Rank
- 第 100 行: 创建全局组
- 第 102 行: 保存选项
- 第 103-114 行: 执行初始化步骤
  - 调用处理器函数
  - 失败则回滚之前的步骤
- 第 117 行: 设置初始化标志

### InitStepCreateEntity() - 创建实体 (行 142-152)

```cpp
int32_t SmemShmEntry::InitStepCreateEntity()
{
    auto entity = hybm_create_entity(id_ << 1, &options_, 0);
    if (entity == nullptr) {
        SM_LOG_ERROR("create entity failed");
        return SM_ERROR;
    }

    entity_ = entity;
    return SM_OK;
}
```

**逐行解读**:
- 第 144 行: 创建 HyBM 实体（ID 左移 1 位）
- 第 145-148 行: 失败处理
- 第 150 行: 保存实体

### InitStepReserveMemory() - 预留内存 (行 160-170)

```cpp
int32_t SmemShmEntry::InitStepReserveMemory()
{
    auto ret = hybm_reserve_mem_space(entity_, 0);
    if (ret != 0) {
        SM_LOG_ERROR("reserve mem failed, result: " << ret);
        return SM_ERROR;
    }

    gva_ = hybm_get_memory_ptr(entity_, HYBM_MEM_TYPE_DEVICE);
    return SM_OK;
}
```

**逐行解读**:
- 第 162 行: 预留内存空间
- 第 163-166 行: 失败处理
- 第 168 行: 获取 GVA 指针

### InitStepAllocSlice() - 分配切片 (行 181-191)

```cpp
int32_t SmemShmEntry::InitStepAllocSlice()
{
    auto slice = hybm_alloc_local_memory(entity_, HYBM_MEM_TYPE_DEVICE, options_.deviceVASpace, 0);
    if (slice == nullptr) {
        SM_LOG_ERROR("alloc local mem failed, size: " << options_.deviceVASpace);
        return SM_ERROR;
    }

    slice_ = slice;
    return SM_OK;
}
```

**逐行解读**:
- 第 183 行: 分配本地设备内存
- 第 184-187 行: 失败处理
- 第 189 行: 保存切片

### InitStepExchangeSlice() - 交换切片信息 (行 203-237)

```cpp
int32_t SmemShmEntry::InitStepExchangeSlice()
{
    hybm_exchange_info exInfo;
    bzero(&exInfo, sizeof(exInfo));
    auto ret = hybm_export(entity_, slice_, 0, &exInfo);
    if (ret != 0) {
        SM_LOG_ERROR("hybm export slice failed, result: " << ret);
        return ret;
    }

    hybm_exchange_info *allExInfo = new hybm_exchange_info[options_.rankCount];
    SM_ASSERT_RETURN(allExInfo != nullptr, SM_MALLOC_FAILED);
    ret = globalGroup_->GroupAllGather((char *)&exInfo, sizeof(hybm_exchange_info), (char *)allExInfo,
                                       sizeof(hybm_exchange_info) * options_.rankCount);
    if (ret != 0) {
        SM_LOG_ERROR("hybm gather export slice failed, result: " << ret);
        delete[] allExInfo;
        return ret;
    }

    ret = hybm_import(entity_, allExInfo, options_.rankCount, nullptr, 0);
    if (ret != 0) {
        SM_LOG_ERROR("hybm import failed, result: " << ret);
        delete[] allExInfo;
        return ret;
    }

    ret = globalGroup_->GroupBarrier();
    if (ret != 0) {
        SM_LOG_ERROR("hybm barrier for slice failed, result: " << ret);
    }

    delete[] allExInfo;
    return ret;
}
```

**逐行解读**:
- 第 205-207 行: 导出本地切片信息
- 第 208-211 行: 导出失败处理
- 第 213 行: 分配存储所有 Rank 信息的数组
- 第 214-221 行: AllGather 收集所有 Rank 的切片信息
- 第 223-228 行: 导入所有 Rank 的切片信息
- 第 230-234 行: Barrier 同步
- 第 235 行: 释放数组

### GetReachInfo() - 获取可达性信息 (行 288-316)

```cpp
Result SmemShmEntry::GetReachInfo(uint32_t remoteRank, uint32_t &reachInfo) const
{
    if (entity_ == nullptr) {
        SM_LOG_ERROR("entity_ is null, cannot get reach info.");
        return SM_NOT_STARTED;
    }

    hybm_data_op_type reachesTypes;
    auto ret = hybm_entity_reach_types(entity_, remoteRank, reachesTypes, 0);
    if (ret != 0) {
        SM_LOG_ERROR("hybm_entity_reach_types() failed: " << ret);
        return SM_ERROR;
    }

    reachInfo = 0U;
    if (reachesTypes & HYBM_DOP_TYPE_MTE) {
        reachInfo |= SMEMS_DATA_OP_MTE;
    }

    if (reachesTypes & HYBM_DOP_TYPE_SDMA) {
        reachInfo |= SMEMS_DATA_OP_SDMA;
    }

    if (reachesTypes & HYBM_DOP_TYPE_DEVICE_RDMA) {
        reachInfo |= SMEMS_DATA_OP_RDMA;
    }

    return SM_OK;
}
```

**逐行解读**:
- 第 290-293 行: 实体检查
- 第 295-300 行: 查询可达类型
- 第 302-313 行: 转换类型标志
  - MTE -> SMEMS_DATA_OP_MTE
  - SDMA -> SMEMS_DATA_OP_SDMA
  - DEVICE_RDMA -> SMEMS_DATA_OP_RDMA

---

## 3. smem_shm_entry_manager.h/cpp - SHM 入口管理器

### 文件信息
- 文件路径: `src/smem/csrc/smem_shm/smem_shm_entry_manager.h/cpp`
- 代码行数: 154 行
- 主要功能: 管理 SHM 入口的生命周期

### 类定义 (行 21-58)

```cpp
class SmemShmEntryManager {
public:
    static SmemShmEntryManager &Instance();

public:
    SmemShmEntryManager() = default;
    ~SmemShmEntryManager() = default;

    SmemShmEntryManager(const SmemShmEntryManager &) = delete;
    SmemShmEntryManager(SmemShmEntryManager &&) = delete;
    SmemShmEntryManager &operator=(const SmemShmEntryManager &) = delete;
    SmemShmEntryManager &operator=(SmemShmEntryManager &&) = delete;

    Result Initialize(const char *configStoreIpPort, uint32_t worldSize, uint32_t rankId, uint16_t deviceId,
                      smem_shm_config_t *config);
    Result CreateEntryById(uint32_t id, SmemShmEntryPtr &entry);
    Result GetEntryByPtr(uintptr_t ptr, SmemShmEntryPtr &entry);
    Result GetEntryById(uint32_t id, SmemShmEntryPtr &entry);
    Result RemoveEntryByPtr(uintptr_t ptr);

    uint16_t GetDeviceId() const;
    StorePtr GetStoreClient() const;

    void Destroy();

private:
    std::mutex entryMutex_;
    std::map<uintptr_t, SmemShmEntryPtr> ptr2EntryMap_; /* lookup entry by ptr */
    std::map<uint32_t, SmemShmEntryPtr> entryIdMap_;    /* deduplicate entry by id */
    smem_shm_config_t config_{};
    uint16_t deviceId_ = 0;
    bool inited_ = false;
    std::string ip_;
    uint16_t port_ = 9980L;

    StorePtr store_ = nullptr;
};
```

**逐行解读**:
- 第 22 行: 单例获取方法
- 第 24-32 行: 禁止拷贝和移动
- 第 34-42 行: 公有接口
  - 初始化
  - 创建/获取/删除入口
  - 获取设备 ID 和存储客户端
  - 销毁
- 第 44-57 行: 私有成员
  - 互斥锁
  - 指针到入口的映射
  - ID 到入口的映射（去重）
  - 配置、设备 ID、初始化标志
  - IP、端口、存储客户端

### Initialize() - 初始化管理器 (行 24-56)

```cpp
Result SmemShmEntryManager::Initialize(const char *configStoreIpPort, uint32_t worldSize, uint32_t rankId,
                                       uint16_t deviceId, smem_shm_config_t *config)
{
    std::lock_guard<std::mutex> guard(entryMutex_);
    if (inited_) {
        SM_LOG_WARN("smem shm manager has already initialized");
        return SM_OK;
    }

    SM_VALIDATE_RETURN(config != nullptr, "invalid param, config is NULL", SM_INVALID_PARAM);
    SM_VALIDATE_RETURN(configStoreIpPort != nullptr, "invalid param, ipPort is NULL", SM_INVALID_PARAM);

    UrlExtraction option;
    std::string url(configStoreIpPort);
    SM_ASSERT_RETURN(option.ExtractIpPortFromUrl(url) == SM_OK, SM_INVALID_PARAM);

    if (rankId == 0 && config->startConfigStoreServer) {
        store_ = ock::smem::StoreFactory::CreateStore(option.ip, option.port, true, 0);
        ip_ = option.ip;
        port_ = option.port;
    } else {
        store_ = ock::smem::StoreFactory::CreateStore(option.ip, option.port, false, static_cast<int32_t>(rankId),
                                                      static_cast<int32_t>(config->shmInitTimeout));
        ip_ = option.ip;
        port_ = option.port;
    }
    SM_ASSERT_RETURN(store_ != nullptr, SM_ERROR);

    config_ = *config;
    deviceId_ = deviceId;
    inited_ = true;
    return SM_OK;
}
```

**逐行解读**:
- 第 27 行: 加锁
- 第 28-31 行: 检查是否已初始化
- 第 33-35 行: 参数校验
- 第 37-38 行: 提取 IP 和端口
- 第 40-48 行: 创建存储
  - Rank 0 且启动服务器时创建服务器端存储
  - 否则创建客户端存储
- 第 52-54 行: 保存配置并设置初始化标志

### CreateEntryById() - 创建入口 (行 58-83)

```cpp
Result SmemShmEntryManager::CreateEntryById(uint32_t id, SmemShmEntryPtr &entry)
{
    std::lock_guard<std::mutex> guard(entryMutex_);
    /* look up the shm entry exists or not with lock */
    SM_ASSERT_RETURN(inited_, SM_NOT_STARTED);
    auto iter = entryIdMap_.find(id);
    if (iter != entryIdMap_.end()) {
        SM_LOG_WARN("create shm entry failed as already exists, id: " << id);
        return SM_DUPLICATED_OBJECT;
    }

    /* create new shm entry */
    auto tmpEntry = SmMakeRef<SmemShmEntry>(id);
    SM_ASSERT_RETURN(tmpEntry != nullptr, SM_NEW_OBJECT_FAILED);

    /* add into set and map */
    entryIdMap_.emplace(id, tmpEntry);
    ptr2EntryMap_.emplace(reinterpret_cast<uintptr_t>(tmpEntry.Get()), tmpEntry);

    /* assign out object ptr */
    entry = tmpEntry;
    entry->SetConfig(config_);

    SM_LOG_DEBUG("create new shm entry success, id: " << id);
    return SM_OK;
}
```

**逐行解读**:
- 第 60 行: 加锁
- 第 62 行: 检查初始化状态
- 第 63-67 行: 检查 ID 是否已存在
- 第 70 行: 创建新的入口
- 第 74-75 行: 添加到映射表
- 第 78-79 行: 设置输出和配置

---

## 总结

Smem_SHM 模块提供了共享内存管理的上层 API：

### 1. 初始化流程

```
smem_shm_init()
    ├── SmemShmEntryManager::Initialize()
    │   ├── 创建 ConfigStore 连接
    │   ├── Rank 0 启动 Server
    │   └── 保存配置
    ├── hybm_init() - 初始化底层 HyBM
    └── 设置初始化标志
```

### 2. SHM 实例创建

```
smem_shm_create()
    ├── SmemShmEntryManager::CreateEntryById()
    │   ├── 创建 SmemShmEntry
    │   └── 添加到映射表
    ├── entry->Initialize()
    │   ├── CreateGlobalTeam() - 创建全局组
    │   ├── InitStepCreateEntity() - 创建实体
    │   ├── InitStepReserveMemory() - 预留内存
    │   ├── InitStepAllocSlice() - 分配切片
    │   ├── InitStepExchangeSlice() - 交换切片信息
    │   ├── InitStepExchangeEntity() - 交换实体信息
    │   └── InitStepMap() - 内存映射
    └── 返回 GVA 和句柄
```

### 3. 集合通信

```
smem_shm_control_barrier()
    ├── 查找入口
    ├── 获取组引擎
    └── GroupBarrier()

smem_shm_control_allgather()
    ├── 查找入口
    ├── 获取组引擎
    └── GroupAllGather()
```

### 4. 拓扑查询

```
smem_shm_topology_can_reach()
    ├── 查找入口
    ├── hybm_entity_reach_types()
    └── 转换类型标志
```

### 5. 关键特性

1. **对称内存**: 每个 Rank 分配相同大小的 HBM
2. **集合通信**: 支持 Barrier 和 AllGather
3. **原子操作**: 分布式原子编号分配
4. **拓扑感知**: 查询可达传输类型
5. **容错**: 支持退出回调广播
