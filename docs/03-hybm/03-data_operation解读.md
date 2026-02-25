# hybm/data_operation 模块逐行解读

## 模块概述

hybm/data_operation 是 HyBM 模块的数据操作层，负责实现跨节点、跨设备的数据拷贝功能。该模块提供了多种数据传输方式（SDMA、RDMA），并支持同步/异步、批量拷贝等操作。

### 目录结构

| 文件名 | 行数 | 功能描述 |
|--------|------|----------|
| hybm_data_operator.h | 107 | 数据操作算子抽象接口 |
| hybm_data_op_factory.h | 31 | 数据操作算子工厂 |
| hybm_data_op_factory.cpp | 35 | 工厂实现 |
| hybm_compose_data_op.h | 58 | 组合数据操作算子 |
| hybm_compose_data_op.cpp | 200+ | 组合算子实现 |
| hybm_data_op_sdma.h | 75 | SDMA 数据操作算子 |
| hybm_data_op_sdma.cpp | 600+ | SDMA 算子实现 |
| hybm_data_op_device_rdma.h | 108 | Device RDMA 数据操作算子 |
| hybm_data_op_device_rdma.cpp | 960+ | Device RDMA 算子实现 |
| hybm_data_op_host_rdma.h | 93 | Host RDMA 数据操作算子 |
| hybm_data_op_host_rdma.cpp | 1020+ | Host RDMA 算子实现 |

### 设计架构

```
                    ┌─────────────────────────────────────────┐
                    │         HostComposeDataOp               │
                    │        (组合数据操作层)                   │
                    └──────────────────┬──────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
    ┌───────────────┐        ┌──────────────────┐      ┌──────────────────┐
    │HostDataOpSDMA │        │DataOpDeviceRDMA  │      │ HostDataOpRDMA   │
    │   (SDMA拷贝)  │        │  (设备端RDMA)     │      │   (主机端RDMA)    │
    └───────────────┘        └────────┬─────────┘      └────────┬─────────┘
                                       │                         │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌──────────────────────┐
                                       │  TransportManager    │
                                       │   (传输管理层)         │
                                       └──────────────────────┘
```

### 数据操作类型

| 操作类型 | 说明 | 使用场景 |
|---------|------|----------|
| SDMA | 同步直接内存访问 | 本地设备与主机间拷贝 |
| Device RDMA | 设备端 RDMA | 设备直接发起的远程内存访问 |
| Host RDMA | 主机端 RDMA | 主机发起的远程内存访问 |

---

## 1. hybm_data_operator.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/hybm_data_operator.h`
**代码行数**: 107 行

### 头文件引用 (第 1-20 行)

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * You can obtain a copy of Mulan PSL v2 at:
 *          http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
 * EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
 * MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
 * See the Mulan PSL v2 for more details.
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明，采用 Mulan PSL v2 开源许可证

```cpp
#ifndef MEM_FABRIC_HYBRID_HYBM_DATA_ACTION_H
#define MEM_FABRIC_HYBRID_HYBM_DATA_ACTION_H

#include <ostream>
#include "hybm_common_include.h"
#include "hybm_big_mem.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 12-13 行: 头文件保护宏
- 第 15 行: 引入 `std::ostream` 用于流输出
- 第 16 行: 引入公共头文件
- 第 17 行: 引入 Big Memory API 定义
- 第 19-20 行: 进入 `ock::mf` 命名空间

### 辅助结构体 (第 22-42 行)

```cpp
struct PairHash {
    std::size_t operator()(const std::pair<uint32_t, uint32_t> &p) const
    {
        return (static_cast<uint64_t>(p.first) << 32ULL) + static_cast<uint64_t>(p.second);
    }
};
```
**逐行解读**:
- 第 22-27 行: 哈希函数对象，用于 `std::unordered_map` 的 key
  - 将 pair<uint32_t, uint32_t> 组合成 64 位哈希值
  - 高 32 位存储 first，低 32 位存储 second

```cpp
struct PairEqual {
    bool operator()(const std::pair<uint32_t, uint32_t> &lhs, const std::pair<uint32_t, uint32_t> &rhs) const
    {
        return lhs.first == rhs.first && lhs.second == rhs.second;
    }
};
```
**逐行解读**:
- 第 29-34 行: 相等比较函数对象
  - 比较 pair 的两个成员是否都相等

```cpp
struct ExtOptions {
    uint32_t srcRankId;
    uint32_t destRankId;
    void *stream = nullptr;
    uint32_t flags;
    std::unordered_map<std::pair<uint32_t, uint32_t>, std::vector<uint32_t>, PairHash, PairEqual> groupMap;
};
```
**逐行解读**:
- 第 36-42 行: 扩展选项结构体
  - srcRankId: 源 Rank ID
  - destRankId: 目标 Rank ID
  - stream: 流指针（用于异步操作）
  - flags: 标志位
  - groupMap: 分组映射，key 为 (srcRankId, destRankId) pair，value 为 index 列表

### DataOperator 抽象类 (第 44-101 行)

```cpp
class DataOperator {
public:
    virtual Result Initialize() noexcept = 0;
    virtual void UnInitialize() noexcept = 0;

    virtual Result DataCopy(hybm_copy_params &params, hybm_data_copy_direction direction,
                            const ExtOptions &options) noexcept = 0;
    virtual Result BatchDataCopy(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                                 const ExtOptions &options) noexcept = 0;
    /*
     * 异步data copy
     * @return 0 if successful, > 0 is wait id, < 0 is error
     */
    virtual Result DataCopyAsync(hybm_copy_params &params, hybm_data_copy_direction direction,
                                 const ExtOptions &options) noexcept = 0;

    virtual Result Wait(int32_t waitId) noexcept = 0;

    virtual ~DataOperator() = default;
```
**逐行解读**:
- 第 44 行: 数据操作算子抽象基类
- 第 46 行: 纯虚函数，初始化算子
- 第 47 行: 纯虚函数，清理算子资源
- 第 49-50 行: 纯虚函数，单次数据拷贝
- 第 51-52 行: 纯虚函数，批量数据拷贝
- 第 53-58 行: 纯虚函数，异步数据拷贝
  - 返回值: 0=成功, >0=等待ID, <0=错误
- 第 60 行: 纯虚函数，等待异步操作完成
- 第 62 行: 虚析构函数，确保正确析构派生类

### GVA 相关方法 (第 64-89 行)

```cpp
public:
    void UpdateGvaSpace(hybm_mem_type type, uint64_t gva, uint64_t localSpaceSize, uint64_t rankCount) noexcept
    {
        if (type == HYBM_MEM_TYPE_BUTT || localSpaceSize == 0) {
            BM_LOG_ERROR("type " << type << " error, local space " << localSpaceSize);
            return;
        }
        gva_[type] = gva;
        localSpaceSize_[type] = localSpaceSize;
        rankCount_[type] = rankCount;
        BM_LOG_INFO("update type " << type << " gva: " << std::hex << gva_[type] << ", space:" << localSpaceSize_[type]
                                   << ", rankCnt:" << rankCount_[type]);
    };
```
**逐行解读**:
- 第 65-76 行: 更新 GVA 地址空间配置
  - 第 67-70 行: 参数校验，type 不能是 BUTT，localSpaceSize 不能为 0
  - 第 71-73 行: 更新静态成员数组
  - 第 74-75 行: 记录日志（十六进制输出）

```cpp
    uint32_t GetRankIdByGva(uint64_t gva) noexcept
    {
        for (auto type = 0; type < HYBM_MEM_TYPE_BUTT; ++type) {
            if (gva >= gva_[type] && gva < (gva_[type] + rankCount_[type] * localSpaceSize_[type])) {
                return (gva - gva_[type]) / localSpaceSize_[type];
            }
        }
        BM_LOG_DEBUG("failed to get rank id by gva: " << std::hex << gva <<
            ", gva of device: " << std::hex << gva_[HYBM_MEM_TYPE_DEVICE] <<
            ", gva of host: " << std::hex << gva_[HYBM_MEM_TYPE_HOST]);
        return UINT32_MAX;
    }
```
**逐行解读**:
- 第 78-89 行: 根据 GVA 地址获取对应的 Rank ID
  - 第 80 行: 遍历所有内存类型（DEVICE、HOST）
  - 第 81 行: 检查 GVA 是否在该类型的地址空间范围内
  - 第 82 行: 计算相对偏移并除以每个 Rank 的大小，得到 Rank ID
  - 第 85-88 行: 未找到时记录调试日志并返回 UINT32_MAX

### CleanUp 方法 (第 91-95 行)

```cpp
    virtual void CleanUp() noexcept
    {
        BM_LOG_INFO("DataOperator not support");
        return;
    }
```
**逐行解读**:
- 第 91-95 行: 清理方法，默认不支持（基类实现）

### 静态成员 (第 97-101 行)

```cpp
protected:
    static inline uint64_t gva_[HYBM_MEM_TYPE_BUTT] = {0};
    static inline uint64_t localSpaceSize_[HYBM_MEM_TYPE_BUTT] = {0};
    static inline uint64_t rankCount_[HYBM_MEM_TYPE_BUTT] = {0};
};
```
**逐行解读**:
- 第 97-101 行: 保护静态成员
  - gva_: 各类型内存的 GVA 起始地址
  - localSpaceSize_: 每个 Rank 的本地空间大小
  - rankCount_: Rank 数量
  - `inline static` 是 C++17 特性，允许在头文件中定义静态成员

### 类型别名 (第 103-104 行)

```cpp
using DataOperatorPtr = std::shared_ptr<DataOperator>;
} // namespace mf
} // namespace ock
```
**逐行解读**:
- 第 103 行: 定义智能指针类型别名
- 第 104-105 行: 命名空间结束

---

## 2. hybm_data_op_factory.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_data_op_factory.h`
**代码行数**: 31 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MEMFABRIC_HYBRID_HYBM_DATA_OP_FACTORY_H
#define MEMFABRIC_HYBRID_HYBM_DATA_OP_FACTORY_H

#include "hybm_transport_manager.h"
#include "hybm_data_operator.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-18 行: 版权声明、头文件保护、引入依赖头文件、进入命名空间

```cpp
class DataOperatorFactory {
public:
    static DataOperatorPtr CreateSdmaDataOperator();
    static DataOperatorPtr CreateDevRdmaDataOperator(uint32_t rankId, const transport::TransManagerPtr &tm);
    static DataOperatorPtr CreateHostRdmaDataOperator(uint32_t rankId, const transport::TransManagerPtr &tm);
};
```
**逐行解读**:
- 第 21-26 行: 数据操作算子工厂类
  - 第 23 行: 创建 SDMA 数据操作算子
  - 第 24 行: 创建 Device RDMA 数据操作算子，需要 rankId 和传输管理器
  - 第 25 行: 创建 Host RDMA 数据操作算子，需要 rankId 和传输管理器

---

## 3. hybm_data_op_factory.cpp 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_data_op_factory.cpp`
**代码行数**: 35 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#include "hybm_data_op_sdma.h"
#include "hybm_data_op_device_rdma.h"
#include "hybm_data_op_host_rdma.h"
#include "hybm_data_op_factory.h"
```
**逐行解读**:
- 第 1-11 行: 版权声明
- 第 12 行: 引入 SDMA 数据操作算子
- 第 13 行: 引入 Device RDMA 数据操作算子
- 第 14 行: 引入 Host RDMA 数据操作算子
- 第 15 行: 引入工厂头文件

```cpp
namespace ock {
namespace mf {
DataOperatorPtr DataOperatorFactory::CreateSdmaDataOperator()
{
    return std::make_shared<HostDataOpSDMA>();
}
```
**逐行解读**:
- 第 17-22 行: 创建 SDMA 数据操作算子
  - 使用 `std::make_shared` 创建 `HostDataOpSDMA` 的智能指针

```cpp
DataOperatorPtr DataOperatorFactory::CreateDevRdmaDataOperator(uint32_t rankId, const transport::TransManagerPtr &tm)
{
    return std::make_shared<DataOpDeviceRDMA>(rankId, tm);
}
```
**逐行解读**:
- 第 24-27 行: 创建 Device RDMA 数据操作算子
  - 将 rankId 和传输管理器传递给构造函数

```cpp
DataOperatorPtr DataOperatorFactory::CreateHostRdmaDataOperator(uint32_t rankId, const transport::TransManagerPtr &tm)
{
    return std::make_shared<HostDataOpRDMA>(rankId, tm);
}
} // namespace mf
} // namespace ock
```
**逐行解读**:
- 第 29-32 行: 创建 Host RDMA 数据操作算子
  - 将 rankId 和传输管理器传递给构造函数
- 第 33-34 行: 命名空间结束

---

## 4. hybm_compose_data_op.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_compose_data_op.h`
**代码行数**: 58 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MEMFABRIC_HYBRID_HYBM_COMPOSE_DATA_OP_H
#define MEMFABRIC_HYBRID_HYBM_COMPOSE_DATA_OP_H

#include <cstdint>
#include <vector>
#include "hybm_entity_tag_info.h"
#include "hybm_data_operator.h"
#include "hybm_transport_manager.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-21 行: 版权声明、头文件保护、引入依赖

```cpp
/**
 * @brief Combine multiple data operators into a single external interface, with the diversity of data operators
 * not exposed to the Entity.
 */
class HostComposeDataOp : public DataOperator {
public:
    HostComposeDataOp(hybm_options options, transport::TransManagerPtr tm, HybmEntityTagInfoPtr tag) noexcept;
    ~HostComposeDataOp() noexcept override;

    Result Initialize() noexcept override;
    void UnInitialize() noexcept override;
    Result DataCopy(hybm_copy_params &params, hybm_data_copy_direction direction,
                    const ExtOptions &options) noexcept override;
    Result BatchDataCopy(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result DataCopyAsync(hybm_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result Wait(int32_t waitId) noexcept override;
```
**逐行解读**:
- 第 24-27 行: 类注释说明，将多个数据操作算子组合成单一接口
- 第 28 行: 继承 DataOperator
- 第 30 行: 构造函数，接收配置选项、传输管理器、Entity 标签信息
- 第 31 行: 析构函数
- 第 33-41 行: 实现 DataOperator 接口方法

```cpp
private:
    using DataOperators = std::vector<std::pair<hybm_data_op_type, DataOperatorPtr>>;
    DataOperators GetPrioritedDataOperators(const ExtOptions &options) noexcept;
```
**逐行解读**:
- 第 43-45 行: 私有类型定义和方法
  - DataOperators: 数据操作算子列表，包含类型和指针的 pair
  - GetPrioritedDataOperators: 根据选项获取优先级排序的数据操作算子

```cpp
private:
    const hybm_options options_;
    const transport::TransManagerPtr transport_;
    HybmEntityTagInfoPtr entityTagInfo_;
    DataOperatorPtr sdmaDataOperator_;
    DataOperatorPtr devRdmaDataOperator_;
    DataOperatorPtr hostRdmaDataOperator_;
};
```
**逐行解读**:
- 第 47-54 行: 私有成员
  - options_: 配置选项
  - transport_: 传输管理器
  - entityTagInfo_: Entity 标签信息
  - sdmaDataOperator_: SDMA 数据操作算子
  - devRdmaDataOperator_: Device RDMA 数据操作算子
  - hostRdmaDataOperator_: Host RDMA 数据操作算子

**设计模式**: 组合模式 + 策略模式
- 将多种数据操作算子组合成一个统一接口
- 根据场景动态选择最优的数据传输方式

---

## 5. hybm_data_op_sdma.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_data_op_sdma.h`
**代码行数**: 75 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MEM_FABRIC_HYBRID_HYBM_DATA_OPERATOR_SDMA_H
#define MEM_FABRIC_HYBRID_HYBM_DATA_OPERATOR_SDMA_H

#include <unordered_map>
#include "mf_rwlock.h"
#include "hybm_data_operator.h"
#include "hybm_stream.h"
#include "hybm_rbtree_range_pool.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-22 行: 版权声明、头文件保护、引入依赖
  - mf_rwlock.h: 读写锁
  - hybm_stream.h: 流管理

```cpp
class HostDataOpSDMA : public DataOperator {
public:
    explicit HostDataOpSDMA() noexcept;
    ~HostDataOpSDMA() override;

    Result Initialize() noexcept override;
    void UnInitialize() noexcept override;

    Result DataCopy(hybm_copy_params &params, hybm_data_copy_direction direction,
                    const ExtOptions &options) noexcept override;
    Result DataCopyAsync(hybm_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result BatchDataCopy(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result Wait(int32_t waitId) noexcept override;

    void CleanUp() noexcept override;
```
**逐行解读**:
- 第 23 行: SDMA 数据操作算子类
- 第 25 行: explicit 构造函数，防止隐式转换
- 第 26 行: 析构函数
- 第 28-37 行: 实现 DataOperator 接口方法
- 第 39 行: 重写 CleanUp 方法

```cpp
private:
    Result CopyLH2GD(void *gvaAddr, const void *hostAddr, size_t count, void *stream) noexcept;
    Result CopyGD2LH(void *hostAddr, const void *gvaAddr, size_t count, void *stream) noexcept;
    Result CopyLH2GH(void *destVA, const void *srcVA, uint64_t length, void *stream) noexcept;
    Result CopyGH2LH(void *destVA, const void *srcVA, uint64_t length, void *stream) noexcept;
```
**逐行解读**:
- 第 42-45 行: 各种拷贝方向的私有方法
  - LH2GD: Local Host → Global Device
  - GD2LH: Global Device → Local Host
  - LH2GH: Local Host → Global Host
  - GH2LH: Global Host → Local Host

```cpp
    void InitG2GStreamTask(StreamTask &task) noexcept;
    Result CopyG2G(void *destVA, const void *srcVA, size_t count, uint32_t flags, void *stream) noexcept;
    Result BatchCopyG2G(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;

    Result CopyG2GAsync(void *destVA, const void *srcVA, size_t count, uint32_t flags, void *stream) noexcept;
```
**逐行解读**:
- 第 47-51 行: G2G (Global to Global) 相关方法
  - InitG2GStreamTask: 初始化 G2G 流任务
  - CopyG2G: 同步 G2G 拷贝
  - BatchCopyG2G: 批量 G2G 拷贝
  - CopyG2GAsync: 异步 G2G 拷贝

```cpp
    Result BatchCopyLH2GD(void *gvaAddrs[], void *hostAddrs[], const uint64_t counts[], uint32_t batchSize,
                          void *stream) noexcept;
    Result BatchCopyGD2LH(void *hostAddrs[], void *gvaAddrs[], const uint64_t counts[], uint32_t batchSize,
                          void *stream) noexcept;
    Result BatchCopyLH2GH(void *gvaAddrs[], void *hostAddrs[], const uint64_t counts[], uint32_t batchSize,
                          void *stream) noexcept;
    Result BatchCopyGH2LH(void *hostAddrs[], void *gvaAddrs[], const uint64_t counts[], uint32_t batchSize,
                          void *stream) noexcept;

    Result BatchCopyExtend(hybm_batch_copy_params &params, void *stream, uint32_t flags) noexcept;
    uint32_t TryGetOneParamSpace(void **ptr) noexcept;
```
**逐行解读**:
- 第 53-60 行: 各种方向的批量拷贝方法
- 第 62 行: 扩展批量拷贝
- 第 63 行: 尝试获取一个参数空间

```cpp
private:
    bool inited_ = false;

    void *paramSpace_ = nullptr;
    uint64_t paramOffset_ = 0;
    uint32_t paramSpaceIdx_ = 0;
};
```
**逐行解读**:
- 第 65-71 行: 私有成员
  - inited_: 初始化标志
  - paramSpace_: 参数空间基地址
  - paramOffset_: 当前参数偏移
  - paramSpaceIdx_: 参数空间索引

---

## 6. hybm_data_op_device_rdma.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_data_op_device_rdma.h`
**代码行数**: 108 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MF_HYBRID_HYBM_DATA_OP_DEVICE_RDMA_H
#define MF_HYBRID_HYBM_DATA_OP_DEVICE_RDMA_H

#include <cstdint>
#include <unordered_map>

#include "hybm_data_operator.h"
#include "hybm_transport_manager.h"
#include "hybm_rbtree_range_pool.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-24 行: 版权声明、头文件保护、引入依赖

```cpp
class DataOpDeviceRDMA : public DataOperator {
public:
    DataOpDeviceRDMA(uint32_t rankId, std::shared_ptr<transport::TransportManager> tm) noexcept;
    ~DataOpDeviceRDMA() override;
    Result Initialize() noexcept override;
    void UnInitialize() noexcept override;
    Result DataCopy(hybm_copy_params &params, hybm_data_copy_direction direction,
                    const ExtOptions &options) noexcept override;
    Result DataCopyAsync(hybm_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result BatchDataCopy(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result Wait(int32_t waitId) noexcept override;
```
**逐行解读**:
- 第 25 行: Device RDMA 数据操作算子类
- 第 27 行: 构造函数，接收 rankId 和传输管理器
- 第 28 行: 析构函数
- 第 29-37 行: 实现 DataOperator 接口方法

```cpp
private:
    Result CopyLH2GH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLH2GD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLD2GH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLD2GD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGH2LH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGD2LH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGH2LD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGD2LD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGH2GH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGD2GH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGH2GD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyGD2GD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLH2LH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLD2LD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLH2LD(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyLD2LH(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
    Result CopyRDMA(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options) noexcept;
```
**逐行解读**:
- 第 40-56 行: 各种拷贝方向的私有方法
  - LH: Local Host, LD: Local Device
  - GH: Global Host, GD: Global Device
  - CopyRDMA: RDMA 拷贝的核心实现

```cpp
    Result BatchCopyLH2GD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGD2LH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyLD2GD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyLD2GH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGH2LD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGD2LD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyLH2GH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGH2GH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGH2GD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGH2LH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGD2GH(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;
    Result BatchCopyGD2GD(hybm_batch_copy_params &params, const ExtOptions &options) noexcept;

    Result BatchDataCopyDefault(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                                const ExtOptions &options) noexcept;
    Result BatchDataCopyLocal(hybm_batch_copy_params &params, int32_t direction, const ExtOptions &options) noexcept;
    Result BatchDataCopyLocalSync(hybm_batch_copy_params &params, int32_t direction,
                                  const ExtOptions &options) noexcept;
    Result BatchDataCopyLocalAsync(hybm_batch_copy_params &params, int32_t direction,
                                   const ExtOptions &options) noexcept;
    Result BatchDataCopyLocalBatch(hybm_batch_copy_params &params, int32_t direction,
                                   const ExtOptions &options) noexcept;
```
**逐行解读**:
- 第 58-79 行: 各种方向的批量拷贝方法
  - BatchCopy*: 各方向批量拷贝
  - BatchDataCopy*: 批量拷贝的内部实现
    - Default: 默认实现
    - Local: 本地拷贝
    - LocalSync: 同步本地拷贝
    - LocalAsync: 异步本地拷贝
    - LocalBatch: 批量本地拷贝

```cpp
    Result AllocSwapMemory();
    void FreeSwapMemory();

    void ClassifyDataAddr(void **globalAddrs, void **localAddrs, const uint64_t *counts, uint32_t batchSize,
                          std::unordered_map<uint32_t, CopyDescriptor> &registered,
                          std::unordered_map<uint32_t, CopyDescriptor> &localed,
                          std::unordered_map<uint32_t, CopyDescriptor> &notRegistered, uint32_t globalRankId) noexcept;
    Result BatchCopyWrite(hybm_batch_copy_params &params, const ExtOptions &options,
                          hybm_data_copy_direction direction) noexcept;
    Result BatchCopyRead(hybm_batch_copy_params &params, const ExtOptions &options,
                         hybm_data_copy_direction direction) noexcept;
    Result BatchCopyG2G(hybm_batch_copy_params &params, const ExtOptions &options,
                        hybm_data_copy_direction direction) noexcept;
    Result SafePut(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options, bool isLocalHost);
    Result SafeGet(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options, bool isLocalHost);
```
**逐行解读**:
- 第 81-82 行: RDMA Swap 内存管理
- 第 84-87 行: 地址分类方法，将地址按注册状态分类
  - registered: 已注册的远程地址
  - localed: 本地地址
  - notRegistered: 未注册的地址
- 第 88-93 行: 批量拷贝的内部实现
  - BatchCopyWrite: 写操作
  - BatchCopyRead: 读操作
  - BatchCopyG2G: G2G 拷贝
  - SafePut: 安全的 Put 操作
  - SafeGet: 安全的 Get 操作

```cpp
private:
    bool inited_{false};
    uint32_t rankId_{0};
    std::shared_ptr<transport::TransportManager> transportManager_;
    void *rdmaSwapBaseAddr_{nullptr};
    std::shared_ptr<RbtreeRangePool> rdmaSwapMemoryAllocator_;
};
```
**逐行解读**:
- 第 97-103 行: 私有成员
  - inited_: 初始化标志
  - rankId_: 当前 Rank ID
  - transportManager_: 传输管理器
  - rdmaSwapBaseAddr_: RDMA 交换内存基地址
  - rdmaSwapMemoryAllocator_: RDMA 交换内存分配器

---

## 7. hybm_data_op_host_rdma.h 逐行解读

**文件路径**: `src/hybm/csrc/data_operation/host/hybm_data_op_host_rdma.h`
**代码行数**: 93 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MF_HYBRID_HYBM_DATA_OP_HOST_RDMA_H
#define MF_HYBRID_HYBM_DATA_OP_HOST_RDMA_H

#include <unordered_map>
#include "hybm_data_operator.h"
#include "hybm_mem_segment.h"
#include "hybm_transport_manager.h"
#include "hybm_rbtree_range_pool.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-22 行: 版权声明、头文件保护、引入依赖

```cpp
class HostDataOpRDMA : public DataOperator {
public:
    HostDataOpRDMA(uint32_t rankId, transport::TransManagerPtr transportManager) noexcept
        : rankId_(rankId), transportManager_{std::move(transportManager)} {};

    ~HostDataOpRDMA() override;

    Result Initialize() noexcept override;
    void UnInitialize() noexcept override;

    Result DataCopy(hybm_copy_params &params, hybm_data_copy_direction direction,
                    const ExtOptions &options) noexcept override;
    Result DataCopyAsync(hybm_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result BatchDataCopy(hybm_batch_copy_params &params, hybm_data_copy_direction direction,
                         const ExtOptions &options) noexcept override;
    Result Wait(int32_t waitId) noexcept override;
```
**逐行解读**:
- 第 24 行: Host RDMA 数据操作算子类
- 第 26-27 行: 构造函数，使用初始化列表和 std::move
- 第 29 行: 析构函数
- 第 31-40 行: 实现 DataOperator 接口方法

```cpp
private:
    Result CopyHost2Gva(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options);
    Result CopyGva2Host(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options);
    Result CopyDevice2Gva(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options);
    Result CopyGva2Device(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options);
    Result CopyGva2Gva(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options);
    Result SafePut(const void *srcVA, void *destVA, uint64_t length,
        const ExtOptions &options, bool isLocalHost);
    Result SafeGet(const void *srcVA, void *destVA, uint64_t length, const ExtOptions &options, bool isLocalHost);
```
**逐行解读**:
- 第 42-50 行: 各种拷贝方向的私有方法
  - CopyHost2Gva: 主机到 GVA
  - CopyGva2Host: GVA 到主机
  - CopyDevice2Gva: 设备到 GVA
  - CopyGva2Device: GVA 到设备
  - CopyGva2Gva: GVA 到 GVA
  - SafePut/SafeGet: 安全的 Put/Get 操作

```cpp
    Result BatchCopyLH2LH(void *gvaAddrs[], void *hostAddrs[], const uint64_t counts[], uint32_t batchSize) noexcept;
    Result BatchCopyLD2LH(void *hostAddrs[], void *deviceAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyLH2LD(void *deviceAddrs[], void *hostAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyLD2GH(void *gvaAddrs[], void *deviceAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyGH2LD(void *deviceAddrs[], void *gvaAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyLH2GH(void *gvaAddrs[], void *hostAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyGH2LH(void *hostAddrs[], void *gvaAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
    Result BatchCopyGH2GH(void *destAddrs[], void *srcAddrs[], const uint64_t counts[], uint32_t batchSize,
                          const ExtOptions &options) noexcept;
```
**逐行解读**:
- 第 51-66 行: 各种方向的批量拷贝方法

```cpp
    void ClassifyDataAddr(void **globalAddrs, void **localAddrs, const uint64_t *counts, uint32_t batchSize,
                          std::unordered_map<uint32_t, CopyDescriptor> &rmtRankMap,
                          std::unordered_map<uint32_t, CopyDescriptor> &localRankMap, const uint32_t rankId) noexcept;
    Result BatchWriteLD2RH(uint32_t rmtRankId, CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options) noexcept;
    Result BatchReadRH2LD(uint32_t rmtRankId, CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options) noexcept;

    Result BatchReadRH2LH(CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options) noexcept;
    Result BatchWriteLH2RH(CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options) noexcept;
```
**逐行解读**:
- 第 67-74 行: 批量拷贝辅助方法
  - ClassifyDataAddr: 地址分类
  - BatchWriteLD2RH: 本地设备写到远程主机
  - BatchReadRH2LD: 远程主机读到本地设备
  - BatchReadRH2LH: 远程主机读到本地主机
  - BatchWriteLH2RH: 本地主机写到远程主机

```cpp
private:
    Result InnerBatchReadRH2LH(const CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options, uint64_t batchOffset,
                               size_t batchEnd, void *tmpRdmaAddrs[]) const;
    Result InnerBatchWriteLH2RH(const CopyDescriptor &rmtCopyDescriptor, const ExtOptions &options,
        uint64_t batchOffset, size_t batchEnd, void *tmpRdmaAddrs[]) const;
    void *GetLocalMrAddr(hybm_copy_params &params, hybm_data_copy_direction direction) noexcept;
    void PreRegisterLocalMr(hybm_copy_params &params, hybm_data_copy_direction direction) noexcept;
    void BatchPreRegisterLocalMr(hybm_batch_copy_params &params, hybm_data_copy_direction direction) noexcept;
    void BatchUnRegisterLocalMr(hybm_batch_copy_params &params, hybm_data_copy_direction direction) noexcept;
```
**逐行解读**:
- 第 75-83 行: 内部辅助方法
  - InnerBatchReadRH2LH/InnerBatchWriteLH2RH: 批量读写的内部实现
  - GetLocalMrAddr: 获取本地内存区域地址
  - PreRegisterLocalMr: 预注册本地内存区域
  - BatchPreRegisterLocalMr: 批量预注册本地内存区域
  - BatchUnRegisterLocalMr: 批量注销本地内存区域

```cpp
    bool inited_{false};
    uint32_t rankId_{0};
    void *rdmaSwapBaseAddr_{nullptr};
    transport::TransManagerPtr transportManager_;
    std::shared_ptr<RbtreeRangePool> rdmaSwapMemoryAllocator_;
};
```
**逐行解读**:
- 第 85-90 行: 私有成员
  - inited_: 初始化标志
  - rankId_: 当前 Rank ID
  - rdmaSwapBaseAddr_: RDMA 交换内存基地址
  - transportManager_: 传输管理器
  - rdmaSwapMemoryAllocator_: RDMA 交换内存分配器

---

## 数据拷贝方向说明

hybm 模块支持多种数据拷贝方向，通过 `hybm_data_copy_direction` 枚举定义：

| 方向枚举值 | 说明 |
|-----------|------|
| HYBM_LOCAL_HOST_TO_GLOBAL_HOST | 本地主机 → 全局主机 |
| HYBM_LOCAL_HOST_TO_GLOBAL_DEVICE | 本地主机 → 全局设备 |
| HYBM_LOCAL_DEVICE_TO_GLOBAL_HOST | 本地设备 → 全局主机 |
| HYBM_LOCAL_DEVICE_TO_GLOBAL_DEVICE | 本地设备 → 全局设备 |
| HYBM_GLOBAL_HOST_TO_GLOBAL_HOST | 全局主机 → 全局主机 |
| HYBM_GLOBAL_HOST_TO_GLOBAL_DEVICE | 全局主机 → 全局设备 |
| HYBM_GLOBAL_HOST_TO_LOCAL_HOST | 全局主机 → 本地主机 |
| HYBM_GLOBAL_HOST_TO_LOCAL_DEVICE | 全局主机 → 本地设备 |
| HYBM_GLOBAL_DEVICE_TO_GLOBAL_HOST | 全局设备 → 全局主机 |
| HYBM_GLOBAL_DEVICE_TO_GLOBAL_DEVICE | 全局设备 → 全局设备 |
| HYBM_GLOBAL_DEVICE_TO_LOCAL_HOST | 全局设备 → 本地主机 |
| HYBM_GLOBAL_DEVICE_TO_LOCAL_DEVICE | 全局设备 → 本地设备 |

**命名规则**:
- LH (Local Host): 本地主机的内存
- LD (Local Device): 本地设备（NPU）的内存
- GH (Global Host): 远程主机的内存
- GD (Global Device): 远程设备（NPU）的内存

---

## 总结

hybm/data_operation 模块实现了跨节点、跨设备的数据拷贝功能：

1. **DataOperator 抽象接口** ([hybm_data_operator.h](../src/hybm/csrc/data_operation/hybm_data_operator.h)): 定义了数据操作的统一接口
2. **工厂模式** ([hybm_data_op_factory.h/cpp](../src/hybm/csrc/data_operation/host/hybm_data_op_factory.h)): 根据类型创建不同的数据操作算子
3. **组合模式** ([hybm_compose_data_op.h/cpp](../src/hybm/csrc/data_operation/host/hybm_compose_data_op.h)): 将多种数据操作算子组合成统一接口
4. **SDMA 数据操作** ([hybm_data_op_sdma.h/cpp](../src/hybm/csrc/data_operation/host/hybm_data_op_sdma.h)): 基于流的数据拷贝
5. **Device RDMA** ([hybm_data_op_device_rdma.h/cpp](../src/hybm/csrc/data_operation/host/hybm_data_op_device_rdma.h)): 设备端发起的 RDMA 操作
6. **Host RDMA** ([hybm_data_op_host_rdma.h/cpp](../src/hybm/csrc/data_operation/host/hybm_data_op_host_rdma.h)): 主机端发起的 RDMA 操作

**设计亮点**:
- 抽象接口支持多种数据传输方式
- GVA (Global Virtual Address) 实现统一寻址
- 批量操作减少传输次数，提高效率
- 内存预注册和 RDMA Swap 内存优化性能
