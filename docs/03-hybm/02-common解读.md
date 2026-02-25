# hybm/common 模块逐行解读

## 模块概述

hybm/common 是 HyBM 模块的公共组件层，提供了核心的数据结构定义、工具函数、日志系统、内存分配器等基础设施。这些组件被 HyBM 模块的所有其他子模块依赖。

### 目录结构

| 文件名 | 行数 | 功能描述 |
|--------|------|----------|
| hybm_common_include.h | 30 | 公共头文件聚合声明 |
| hybm_define.h | 191 | 核心宏定义、地址空间常量、结构体 |
| hybm_functions.h | 96 | 公共工具函数类 |
| hybm_logger.h | 71 | 日志宏定义 |
| hybm_types.h | 42 | 错误码定义 |
| hybm_networks_common.h | 26 | 网络工具接口 |
| hybm_networks_common.cpp | 113 | 网络工具实现 |
| hybm_ptracer.h | 127 | 性能打点定义 |
| hybm_space_allocator.h | 100 | 空间分配器抽象接口 |
| hybm_rbtree_range_pool.h | 58 | 红黑树范围池定义 |
| hybm_rbtree_range_pool.cpp | 135 | 红黑树范围池实现 |
| hybm_version.h | 36 | 版本信息 |

---

## 1. hybm_common_include.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_common_include.h`
**代码行数**: 30 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *          http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
 * EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
 * MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
 * See the Mulan PSL v2 for more details.
*/
```
**逐行解读**:
- 第 1-11 行: 版权与许可证声明，采用 Mulan PSL v2 开源许可证

```cpp
#ifndef MEM_FABRIC_HYBRID_HYBM_COMMON_INCLUDE_H
#define MEM_FABRIC_HYBRID_HYBM_COMMON_INCLUDE_H
```
**逐行解读**:
- 第 12-13 行: 头文件保护宏，防止重复包含

```cpp
#include <map>
#include <mutex>

#include "hybm_big_mem.h"
#include "hybm_define.h"
#include "hybm_functions.h"
#include "hybm_logger.h"
#include "hybm_types.h"
#include "mf_file_util.h"
```
**逐行解读**:
- 第 15 行: 引入 `std::map` 容器
- 第 16 行: 引入 `std::mutex` 互斥锁
- 第 18 行: 引入 hybm_big_mem.h - Big Memory API 定义
- 第 19 行: 引入 hybm_define.h - 核心宏定义
- 第 20 行: 引入 hybm_functions.h - 工具函数
- 第 21 行: 引入 hybm_logger.h - 日志系统
- 第 22 行: 引入 hybm_types.h - 类型定义
- 第 23 行: 引入 mf_file_util.h - 文件操作工具（来自 util 模块）

```cpp
int32_t HybmGetInitDeviceId(void);

bool HybmHasInited(void);
```
**逐行解读**:
- 第 25 行: 声明获取初始化设备 ID 的函数，返回设备 ID
- 第 27 行: 声明检查 HyBM 是否已初始化的函数，返回是否已初始化

```cpp
#endif // MEM_FABRIC_HYBRID_HYBM_COMMON_INCLUDE_H
```
**逐行解读**:
- 第 29 行: 头文件结束保护宏

---

## 2. hybm_define.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_define.h`
**代码行数**: 191 行

### 头文件引用与命名空间

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MEM_FABRIC_HYBRID_HYBM_DEFINE_H
#define MEM_FABRIC_HYBRID_HYBM_DEFINE_H

#include <netinet/in.h>
#include <cstdint>
#include <cstddef>
#include <vector>
#include "mf_out_logger.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-13 行: 版权声明与头文件保护
- 第 15 行: 引入网络相关头文件，用于 `sockaddr_in` 等结构体
- 第 16 行: 引入 `uint64_t` 等整型定义
- 第 17 行: 引入 `size_t` 类型
- 第 18 行: 引入 `std::vector` 容器
- 第 19 行: 引入日志工具
- 第 21-22 行: 进入 `ock::mf` 命名空间

### 常量定义 (第 24-57 行)

```cpp
constexpr uint64_t KB = 1024ULL;
constexpr uint64_t MB = KB * 1024ULL;
constexpr uint64_t GB = MB * 1024ULL;
constexpr uint64_t TB = GB * 1024ULL;
```
**逐行解读**:
- 第 24 行: 定义 KB 常量 = 1024 字节
- 第 25 行: 定义 MB 常量 = KB × 1024
- 第 26 行: 定义 GB 常量 = MB × 1024
- 第 27 行: 定义 TB 常量 = GB × 1024

```cpp
constexpr uint32_t RANK_MAX = 1024UL;
constexpr uint64_t SMALL_PAGE_SIZE = 4U * KB;
```
**逐行解读**:
- 第 29 行: 最大 Rank 数量为 1024
- 第 30 行: 小页大小 = 4KB

```cpp
constexpr uint64_t HYBM_LARGE_PAGE_SIZE = 2UL * 1024UL * 1024UL; // 大页的size, 2M
constexpr uint64_t HYBM_DEVICE_VA_START = 0x100000000000UL;      // NPU上的地址空间起始: 16T
constexpr uint64_t HYBM_DEVICE_VA_SIZE = 0x80000000000UL;        // NPU上的地址空间范围: 8T
```
**逐行解读**:
- 第 32 行: 大页大小 = 2MB，用于内存对齐
- 第 33 行: NPU 设备虚拟地址空间起始 = 16TB (0x100000000000 = 2^44)
- 第 34 行: NPU 设备虚拟地址空间大小 = 8TB (0x80000000000 = 2^43)

```cpp
constexpr uint64_t SVM_END_ADDR = HYBM_DEVICE_VA_START + HYBM_DEVICE_VA_SIZE - (1UL << 30UL); // svm的结尾虚拟地址
```
**逐行解读**:
- 第 35 行: SVM (Shared Virtual Memory) 结束地址 = 16TB + 8TB - 1GB = 23TB

```cpp
constexpr uint64_t HYBM_DEVICE_PRE_META_SIZE = 128UL;                                         // 128B
constexpr uint64_t HYBM_DEVICE_GLOBAL_META_SIZE = HYBM_DEVICE_PRE_META_SIZE;                  // 128B
constexpr uint64_t HYBM_ENTITY_NUM_MAX = 511UL;                                               // entity最大数量
constexpr uint64_t HYBM_DEVICE_META_SIZE =
    HYBM_DEVICE_PRE_META_SIZE * HYBM_ENTITY_NUM_MAX + HYBM_DEVICE_GLOBAL_META_SIZE; // 64K
```
**逐行解读**:
- 第 36 行: 每个 Entity 的元数据大小 = 128B
- 第 37 行: 全局元数据大小 = 128B
- 第 38 行: Entity 最大数量 = 511
- 第 39-40 行: 设备元数据总大小 = 128B × 511 + 128B = 65408B ≈ 64KB

```cpp
constexpr uint64_t HYBM_DEVICE_USER_CONTEXT_PRE_SIZE = 64UL * 1024UL; // 64K
constexpr uint64_t HYBM_DEVICE_INFO_SIZE =
    HYBM_DEVICE_USER_CONTEXT_PRE_SIZE * HYBM_ENTITY_NUM_MAX +
    HYBM_DEVICE_META_SIZE; // 元数据+用户context,总大小32M, 对齐HYBM_LARGE_PAGE_SIZE
constexpr uint64_t HYBM_DEVICE_META_ADDR = SVM_END_ADDR - HYBM_DEVICE_INFO_SIZE;
constexpr uint64_t HYBM_DEVICE_USER_CONTEXT_ADDR = HYBM_DEVICE_META_ADDR + HYBM_DEVICE_META_SIZE;
```
**逐行解读**:
- 第 42 行: 每个 Entity 的用户上下文大小 = 64KB
- 第 43-45 行: 设备信息总大小 = 64KB × 511 + 64KB ≈ 32MB
- 第 46 行: 设备元数据地址 = SVM 结束地址 - 32MB
- 第 47 行: 用户上下文地址 = 元数据地址 + 元数据大小

### ACL 内存拷贝方向 (第 48-52 行)

```cpp
constexpr uint32_t ACL_MEMCPY_HOST_TO_HOST = 0;
constexpr uint32_t ACL_MEMCPY_HOST_TO_DEVICE = 1;
constexpr uint32_t ACL_MEMCPY_DEVICE_TO_HOST = 2;
constexpr uint32_t ACL_MEMCPY_DEVICE_TO_DEVICE = 3;
constexpr uint32_t RT_MEMCPY_DEVICE_TO_DEVICE = 3;
```
**逐行解读**:
- 第 48 行: ACL (Ascend Computing Language) 主机到主机拷贝
- 第 49 行: 主机到设备拷贝
- 第 50 行: 设备到主机拷贝
- 第 51 行: 设备到设备拷贝
- 第 52 行: RT (Runtime) 设备到设备拷贝，方向值相同

### 地址空间范围 (第 54-57 行)

```cpp
constexpr uint64_t HYBM_HBM_START_ADDR = HYBM_DEVICE_VA_START;
constexpr uint64_t HYBM_HBM_END_ADDR = HYBM_DEVICE_VA_START + HYBM_DEVICE_VA_SIZE;
constexpr uint64_t HYBM_GVM_START_ADDR = 0x280000000000UL;      // 40T
constexpr uint64_t HYBM_GVM_END_ADDR = 0xA80000000000UL;        // 168T
```
**逐行解读**:
- 第 54 行: HBM 地址起始 = 16TB
- 第 55 行: HBM 地址结束 = 24TB
- 第 56 行: GVM (Global Virtual Memory) 起始 = 40TB
- 第 57 行: GVM 结束 = 168TB

### 导出信息 Magic 值 (第 59-64 行)

```cpp
constexpr uint64_t ENTITY_EXPORT_INFO_MAGIC = 0xAABB1234FFFFEE00UL;
constexpr uint64_t HBM_SLICE_EXPORT_INFO_MAGIC = 0xAABB1234FFFFEE01UL;
constexpr uint64_t DRAM_SLICE_EXPORT_INFO_MAGIC = 0xAABB1234FFFFEE02UL;
constexpr uint64_t VMM_BASE_HBM_SLICE_EXPORT_INFO_MAGIC = 0xAABB1234FFFFEE03UL;
constexpr uint64_t VMM_BASE_DRAM_SLICE_EXPORT_INFO_MAGIC = 0xAABB1234FFFFEE04UL;
constexpr uint64_t EXPORT_INFO_VERSION = 0x1UL;
```
**逐行解读**:
- 第 59 行: Entity 导出信息的魔数，用于验证导出数据有效性
- 第 60 行: HBM 切片导出信息魔数
- 第 61 行: DRAM 切片导出信息魔数
- 第 62 行: VMM (Virtual Memory Manager) 基础 HBM 切片魔数
- 第 63 行: VMM 基础 DRAM 切片魔数
- 第 64 行: 导出信息格式版本 = 1

### 段类型定义 (第 66-70 行)

```cpp
constexpr uint16_t SEGMENT_TYPE_VMM = 0x1U;
constexpr uint16_t SEGMENT_TYPE_USER_DEV = 0x2U;
constexpr uint16_t SEGMENT_TYPE_DEFAULT = 0x10U;
constexpr uint16_t SEGMENT_TYPE_OFFSET = 8U;
constexpr uint16_t UNIFIED_EXCHANGE_SEG_INFO_SIZE = 184U; /* all exchange info padding to same size */
```
**逐行解读**:
- 第 66 行: VMM 类型的内存段
- 第 67 行: 用户设备类型的内存段
- 第 68 行: 默认类型的内存段
- 第 69 行: 段类型在交换信息中的偏移量（8 字节）
- 第 70 行: 统一交换信息大小 = 184B，所有交换信息填充到相同大小

### 内联函数 (第 72-97 行)

```cpp
inline bool IsDramSlice(uint64_t magic)
{
    return magic == DRAM_SLICE_EXPORT_INFO_MAGIC || magic == VMM_BASE_DRAM_SLICE_EXPORT_INFO_MAGIC;
}
```
**逐行解读**:
- 第 72-75 行: 判断魔数是否为 DRAM 切片类型

```cpp
inline uint64_t Valid48BitsAddress(uint64_t address)
{
    return address & 0xffffffffffffUL;
}
```
**逐行解读**:
- 第 77-80 行: 将地址截断为 48 位有效地址，0xffffffffffff = 2^48 - 1

```cpp
inline const void *Valid48BitsAddress(const void *address)
{
    uint64_t addr = static_cast<uint64_t>(reinterpret_cast<uintptr_t>(address));
    return reinterpret_cast<const void *>(static_cast<uintptr_t>(Valid48BitsAddress(addr)));
}
```
**逐行解读**:
- 第 82-86 行: 指针版本的有效地址转换函数
  - 第 84 行: 将指针转换为 uint64_t
  - 第 85 行: 截断为 48 位后转回指针

```cpp
inline void *Valid48BitsAddress(void *address)
{
    uint64_t addr = static_cast<uint64_t>(reinterpret_cast<uintptr_t>(address));
    return reinterpret_cast<void *>(static_cast<uintptr_t>(Valid48BitsAddress(addr)));
}
```
**逐行解读**:
- 第 88-92 行: 非const 指针版本

```cpp
inline uint32_t GetExchangeInfoSegmentType(const void* data) {
    const char* bytes = static_cast<const char*>(data);
    return *reinterpret_cast<const uint32_t*>(bytes + SEGMENT_TYPE_OFFSET);
}
```
**逐行解读**:
- 第 94-97 行: 从交换信息中获取段类型
  - 第 95 行: 将 void* 转换为 char* 以便字节操作
  - 第 96 行: 读取偏移 8 字节处的 uint32_t 值作为段类型

### 枚举定义 (第 99-114 行)

```cpp
enum AscendSocType {
    ASCEND_UNKNOWN = 0,
    ASCEND_910B,
    ASCEND_910C,
};
```
**逐行解读**:
- 第 99-103 行: 昇腾 SoC 类型枚举
  - ASCEND_UNKNOWN: 未知类型
  - ASCEND_910B: 昇腾 910B 芯片
  - ASCEND_910C: 昇腾 910C 芯片

```cpp
enum DeviceSystemInfoType {
    INFO_TYPE_VERSION = 1,
    INFO_TYPE_PHY_CHIP_ID = 18,
    INFO_TYPE_PHY_DIE_ID,
    INFO_TYPE_SDID = 26,
    INFO_TYPE_SERVER_ID,
    INFO_TYPE_SCALE_TYPE,
    INFO_TYPE_SUPER_POD_ID,
    INFO_TYPE_ADDR_MODE,
};
```
**逐行解读**:
- 第 105-114 行: 设备系统信息类型枚举
  - VERSION: 版本信息
  - PHY_CHIP_ID: 物理芯片 ID
  - PHY_DIE_ID: 物理 Die ID
  - SDID: SDID (值为 26)
  - SERVER_ID: 服务器 ID
  - SCALE_TYPE: 扩展类型
  - SUPER_POD_ID: 超级 Pod ID
  - ADDR_MODE: 地址模式

### 结构体定义 (第 116-135 行)

```cpp
struct HybmDeviceGlobalMeta {
    uint64_t entityCount;
    uint64_t reserved[15]; // total 128B, equal HYBM_DEVICE_PRE_META_SIZE
};
```
**逐行解读**:
- 第 116-119 行: 设备全局元数据结构体
  - entityCount: Entity 计数
  - reserved[15]: 保留字段，15 × 8B = 120B，总计 128B

```cpp
struct HybmDeviceMeta {
    uint32_t entityId;
    uint32_t rankId;
    uint32_t rankSize;
    uint32_t extraContextSize;
    uint64_t symmetricSize;
    uint64_t qpInfoAddress;
    uint64_t reserved[12]; // total 128B, equal HYBM_DEVICE_PRE_META_SIZE
};
```
**逐行解读**:
- 第 121-129 行: 每个 Entity 的设备元数据结构体
  - entityId: Entity ID
  - rankId: Rank ID
  - rankSize: Rank 大小
  - extraContextSize: 额外上下文大小
  - symmetricSize: 对称大小
  - qpInfoAddress: Queue Pair 信息地址
  - reserved[12]: 保留字段，总计 96B，结构体总大小 128B

```cpp
typedef struct {
    std::vector<void *> localAddrs;
    std::vector<void *> globalAddrs;
    std::vector<uint64_t> counts;
} CopyDescriptor;
```
**逐行解读**:
- 第 131-135 行: 拷贝描述符结构体，用于批量拷贝
  - localAddrs: 本地地址列表
  - globalAddrs: 全局地址列表
  - counts: 每个地址的拷贝大小列表

### 宏定义 (第 137-184 行)

```cpp
// macro for gcc optimization for prediction of if/else
#ifndef LIKELY
#define LIKELY(x) (__builtin_expect(!!(x), 1) != 0)
#endif

#ifndef UNLIKELY
#define UNLIKELY(x) (__builtin_expect(!!(x), 0) != 0)
#endif
```
**逐行解读**:
- 第 137-144 行: GCC 分支预测优化宏
  - LIKELY(x): 告诉编译器条件很可能为真
  - UNLIKELY(x): 告诉编译器条件很可能为假
  - `__builtin_expect` 是 GCC 内置函数用于分支预测优化

```cpp
#define HYBM_API __attribute__((visibility("default")))
```
**逐行解读**:
- 第 146 行: 导出符号宏，标记函数/类在动态库中可见

```cpp
#define DL_LOAD_SYM(TARGET_FUNC_VAR, TARGET_FUNC_TYPE, FILE_HANDLE, SYMBOL_NAME)                      \
    do {                                                                                              \
        TARGET_FUNC_VAR = (TARGET_FUNC_TYPE)dlsym(FILE_HANDLE, SYMBOL_NAME);                          \
        if ((TARGET_FUNC_VAR) == nullptr) {                                                           \
            BM_LOG_ERROR("Failed to call dlsym to load " << (SYMBOL_NAME) << ", error" << dlerror()); \
            dlclose(FILE_HANDLE);                                                                     \
            FILE_HANDLE = nullptr;                                                                    \
            return BM_DL_FUNCTION_FAILED;                                                             \
        }                                                                                             \
    } while (0)
```
**逐行解读**:
- 第 148-157 行: 动态加载符号宏（必须成功）
  - 使用 `dlsym` 从动态库加载符号
  - 失败时记录错误、关闭库、返回错误码

```cpp
#define DL_LOAD_SYM_OPTIONAL(TARGET_FUNC_VAR, TARGET_FUNC_TYPE, FILE_HANDLE, SYMBOL_NAME)            \
    do {                                                                                             \
        TARGET_FUNC_VAR = (TARGET_FUNC_TYPE)dlsym(FILE_HANDLE, SYMBOL_NAME);                         \
        if ((TARGET_FUNC_VAR) == nullptr) {                                                          \
            BM_LOG_WARN("Failed to call dlsym to load " << (SYMBOL_NAME) << ", error" << dlerror()); \
        }                                                                                            \
    } while (0)
```
**逐行解读**:
- 第 159-165 行: 动态加载符号宏（可选），失败只警告不返回错误

```cpp
#define DL_LOAD_SYM_ALT(TARGET_FUNC_VAR, TARGET_FUNC_TYPE, FILE_HANDLE, SYMBOL_NAME, SYMBOL_NAME_ALT) \
    do {                                                                                              \
        TARGET_FUNC_VAR = (TARGET_FUNC_TYPE)dlsym(FILE_HANDLE, SYMBOL_NAME);                          \
        if ((TARGET_FUNC_VAR) != nullptr) {                                                           \
            BM_LOG_DEBUG("Loaded symbol " << (SYMBOL_NAME) << " successfully");                       \
            break;                                                                                    \
        }                                                                                             \
        TARGET_FUNC_VAR = (TARGET_FUNC_TYPE)dlsym(FILE_HANDLE, SYMBOL_NAME_ALT);                      \
        if ((TARGET_FUNC_VAR) != nullptr) {                                                           \
            BM_LOG_DEBUG("Loaded symbol " << (SYMBOL_NAME_ALT) << " successfully");                   \
            break;                                                                                    \
        }                                                                                             \
        BM_LOG_ERROR("Failed to call dlsym to load " << (SYMBOL_NAME) << " or " << (SYMBOL_NAME_ALT)  \
                                                     << ", error" << dlerror());                      \
        dlclose(FILE_HANDLE);                                                                         \
        FILE_HANDLE = nullptr;                                                                        \
        return BM_DL_FUNCTION_FAILED;                                                                 \
    } while (0)
```
**逐行解读**:
- 第 167-184 行: 动态加载符号宏（尝试两个备选符号名）
  - 先尝试加载 SYMBOL_NAME
  - 失败则尝试 SYMBOL_NAME_ALT
  - 两者都失败则返回错误

### GVA 版本枚举 (第 186 行)

```cpp
enum HybmGvaVersion : uint32_t { HYBM_GVA_V1 = 0, HYBM_GVA_V2 = 1, HYBM_GVA_V3 = 2, HYBM_GVA_V4 = 3, HYBM_GVA_UNKNOWN };
```
**逐行解读**:
- 第 186 行: 全局虚拟地址 (GVA) 版本枚举，支持 V1-V4

---

## 3. hybm_types.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_types.h`
**代码行数**: 42 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MEM_FABRIC_HYBRID_HYBM_TYPES_H
#define MEM_FABRIC_HYBRID_HYBM_TYPES_H

#include <cstdint>
#include <memory>

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-19 行: 版权声明、头文件保护、引入必要的头文件、进入命名空间

### 类型别名与错误码 (第 20-35 行)

```cpp
using Result = int32_t;
```
**逐行解读**:
- 第 20 行: 定义 Result 类型别名，用于函数返回值

```cpp
enum BErrorCode : int32_t {
    BM_OK = 0,
    BM_ERROR = -1,
    BM_INVALID_PARAM = -2,
    BM_MALLOC_FAILED = -3,
    BM_NEW_OBJECT_FAILED = -4,
    BM_FILE_NOT_ACCESS = -5,
    BM_DL_FUNCTION_FAILED = -6,
    BM_TIMEOUT = -7,
    BM_UNDER_API_UNLOAD = -8,
    BM_NOT_INITIALIZED = -9,
    BM_NOT_SUPPORT_FUNC = -10,
    BM_NOT_SUPPORTED = -100,
};
```
**逐行解读**:
- 第 22-35 行: 错误码枚举定义
  - BM_OK (0): 成功
  - BM_ERROR (-1): 通用错误
  - BM_INVALID_PARAM (-2): 无效参数
  - BM_MALLOC_FAILED (-3): 内存分配失败
  - BM_NEW_OBJECT_FAILED (-4): 对象创建失败
  - BM_FILE_NOT_ACCESS (-5): 文件无法访问
  - BM_DL_FUNCTION_FAILED (-6): 动态加载函数失败
  - BM_TIMEOUT (-7): 超时
  - BM_UNDER_API_UNLOAD (-8): 底层 API 已卸载
  - BM_NOT_INITIALIZED (-9): 未初始化
  - BM_NOT_SUPPORT_FUNC (-10): 不支持的函数
  - BM_NOT_SUPPORTED (-100): 不支持的操作

```cpp
constexpr uint32_t UN40 = 40;
```
**逐行解读**:
- 第 37 行: 定义常量 UN40 = 40，用于 Magic 计算

---

## 4. hybm_functions.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_functions.h`
**代码行数**: 96 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MEM_FABRIC_HYBRID_HYBM_FUNCTIONS_H
#define MEM_FABRIC_HYBRID_HYBM_FUNCTIONS_H

#include "hybm_define.h"
#include "hybm_types.h"
#include "hybm_logger.h"
#include "mf_str_util.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-21 行: 版权声明、头文件保护、引入依赖、进入命名空间

### Func 工具类 (第 22-57 行)

```cpp
class Func {
public:
    static uint64_t MakeObjectMagic(uint64_t srcAddress);
    static uint64_t ValidateObjectMagic(const void *ptr, const uint64_t magic);

    static inline int32_t GetLogicDeviceId(const int &deviceId)
    {
```
**逐行解读**:
- 第 22-27 行: Func 类定义，提供静态工具函数
- 第 24 行: 声明创建对象 Magic 的函数
- 第 25 行: 声明验证对象 Magic 的函数
- 第 27 行: 定义获取逻辑设备 ID 的内联函数

```cpp
        int logicDeviceId = -1;
        auto visibleDevStr = std::getenv("ASCEND_RT_VISIBLE_DEVICES");
        if (visibleDevStr == nullptr) {
            BM_LOG_INFO("Not set rt visible env return deviceId: " << deviceId);
            return deviceId;
        } else {
```
**逐行解读**:
- 第 29 行: 初始化逻辑设备 ID 为 -1
- 第 30 行: 获取环境变量 `ASCEND_RT_VISIBLE_DEVICES`，用于指定可见设备
- 第 31-34 行: 如果环境变量未设置，直接返回传入的设备 ID

```cpp
            auto devList = StrUtil::Split(visibleDevStr, ',');
            if (devList.size() <= static_cast<uint32_t>(deviceId)) {
                BM_LOG_ERROR("Failed to get visible devSize: " << devList.size() << " deviceId: " << deviceId);
                return BM_ERROR;
            } else {
                if (!StrUtil::String2Int<int>(devList[deviceId], logicDeviceId)) {
                    BM_LOG_ERROR("Failed to get visible dev size: " << devList.size() << " deviceId: " << deviceId);
                    return BM_ERROR;
                }
            }
        }
        return logicDeviceId;
    }
```
**逐行解读**:
- 第 35 行: 使用逗号分割环境变量字符串，获取设备列表
- 第 36-38 行: 如果设备索引超出列表范围，返回错误
- 第 40-42 行: 将对应位置的设备字符串转换为整数
- 第 46 行: 返回逻辑设备 ID

```cpp
    static inline int64_t GetCurTid()
    {
        static thread_local int64_t tid = reinterpret_cast<int64_t>(syscall(SYS_gettid));
        return tid;
    }
```
**逐行解读**:
- 第 49-53 行: 获取当前线程 ID
  - 使用 `thread_local` 存储，每个线程只调用一次 `syscall`
  - `SYS_gettid` 获取线程的真实 ID

```cpp
private:
    const static uint64_t gMagicBits = 0xFFFFFFFFFF; /* get lower 40bits */
};
```
**逐行解读**:
- 第 55-57 行: 私有静态成员，Magic 掩码 = 0xFFFFFFFFFF (40 位全 1)

### 内联函数实现 (第 59-80 行)

```cpp
inline uint64_t Func::MakeObjectMagic(uint64_t srcAddress)
{
    return (srcAddress & gMagicBits) + UN40;
}
```
**逐行解读**:
- 第 59-62 行: 从地址生成 Magic 值
  - 取地址的低 40 位
  - 加上偏移量 40 (UN40)

```cpp
inline uint64_t Func::ValidateObjectMagic(const void *ptr, const uint64_t magic)
{
    auto tmp = reinterpret_cast<uint64_t>(ptr);
    return magic == ((tmp & gMagicBits) + UN40);
}
```
**逐行解读**:
- 第 64-68 行: 验证 Magic 是否匹配指针
  - 将指针转换为 uint64_t
  - 比较计算出的 Magic 是否与给定的相等

```cpp
inline std::string SafeStrError(int errNum)
{
    locale_t loc = newlocale(LC_ALL_MASK, "", static_cast<locale_t>(nullptr));
    if (loc == static_cast<locale_t>(nullptr)) {
        return "Failed to create locale";
    }
    const char *error_msg = strerror_l(errNum, loc);
    std::string result(error_msg ? error_msg : "Unknown error");
    freelocale(loc);
    return result;
}
```
**逐行解读**:
- 第 70-80 行: 线程安全的错误码转字符串函数
  - 第 72 行: 创建新的 locale 对象
  - 第 73-75 行: 创建失败时返回错误消息
  - 第 76 行: 使用 `strerror_l` 获取线程安全的错误描述
  - 第 77 行: 构造结果字符串，处理空指针情况
  - 第 78 行: 释放 locale
  - 第 79 行: 返回错误描述

### SafeCopy 模板函数 (第 82-92 行)

```cpp
template<typename II, typename OI>
Result SafeCopy(II first, II last, OI result)
{
    try {
        std::copy(first, last, result);
    } catch (...) {
        BM_LOG_ERROR("copy failed.");
        return BM_MALLOC_FAILED;
    }
    return BM_OK;
}
```
**逐行解读**:
- 第 82-92 行: 安全的拷贝函数模板
  - II: 输入迭代器类型
  - OI: 输出迭代器类型
  - 使用 try-catch 捕获可能的异常
  - 异常时记录日志并返回错误码

---

## 5. hybm_logger.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_logger.h`
**代码行数**: 71 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MEMFABRIC_HYBRID_LOGGER_H
#define MEMFABRIC_HYBRID_LOGGER_H

#include "mf_out_logger.h"
```
**逐行解读**:
- 第 1-15 行: 版权声明、头文件保护、引入日志工具

### 日志宏定义 (第 17-21 行)

```cpp
#define BM_LOG_DEBUG(ARGS)       MF_OUT_LOG("[HYBM ", ock::mf::DEBUG_LEVEL, ARGS)
#define BM_LOG_INFO(ARGS)        MF_OUT_LOG("[HYBM ", ock::mf::INFO_LEVEL, ARGS)
#define BM_LOG_WARN(ARGS)        MF_OUT_LOG("[HYBM ", ock::mf::WARN_LEVEL, ARGS)
#define BM_LOG_ERROR(ARGS)       MF_OUT_LOG("[HYBM ", ock::mf::ERROR_LEVEL, ARGS)
#define BM_LOG_ERROR_LIMIT(ARGS) MF_OUT_LOG_LIMIT("[HYBM ", ock::mf::ERROR_LEVEL, ARGS)
```
**逐行解读**:
- 第 17 行: DEBUG 级别日志宏，添加 "[HYBM" 前缀
- 第 18 行: INFO 级别日志宏
- 第 19 行: WARN 级别日志宏
- 第 20 行: ERROR 级别日志宏
- 第 21 行: 带限流的 ERROR 日志宏，防止日志刷屏

### 断言宏定义 (第 23-69 行)

```cpp
#define BM_ASSERT_RETURN(ARGS, RET)              \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            BM_LOG_ERROR("Assert " << #ARGS);    \
            return RET;                          \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 23-29 行: 断言失败返回宏
  - 使用 `__builtin_expect` 优化分支预测
  - 断言失败时记录错误日志并返回指定值
  - `#ARGS` 将条件转换为字符串

```cpp
#define BM_VALIDATE_RETURN(ARGS, msg, RET)       \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            BM_LOG_ERROR(msg);                   \
            return RET;                          \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 31-37 行: 验证返回宏，允许自定义错误消息

```cpp
#define BM_ASSERT_LOG_AND_RETURN(ARGS, MSG, RESULT) \
    do {                                            \
        if (__builtin_expect(!(ARGS), 0) != 0) {    \
            BM_LOG_ERROR(MSG);                      \
            return RESULT;                          \
        }                                           \
    } while (0)
```
**逐行解读**:
- 第 39-45 行: 带日志的断言返回宏，与 BM_VALIDATE_RETURN 功能相同

```cpp
#define BM_ASSERT_RET_VOID(ARGS)                 \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            BM_LOG_ERROR("Assert " << #ARGS);    \
            return;                              \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 47-53 行: 断言失败返回空宏，用于 void 返回类型的函数

```cpp
#define BM_LOG_ERROR_RETURN_IT_IF_NOT_OK(result, msg) \
    do {                                              \
        auto innerResult = (result);                  \
        if (UNLIKELY(innerResult != 0)) {             \
            BM_LOG_ERROR(msg);                        \
            return innerResult;                       \
        }                                             \
    } while (0)
```
**逐行解读**:
- 第 55-62 行: 检查结果并返回宏
  - 先执行表达式保存结果
  - 如果结果非 0（表示错误），记录日志并返回

```cpp
#define BM_ASSERT(ARGS)                          \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            BM_LOG_ERROR("Assert " << #ARGS);    \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 64-69 行: 纯断言宏，只记录日志不返回

---

## 6. hybm_networks_common.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_networks_common.h`
**代码行数**: 26 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MEM_FABRIC_HYBRID_HYBM_NETWORKS_COMMON_H
#define MEM_FABRIC_HYBRID_HYBM_NETWORKS_COMMON_H

#include <cstdint>
#include <vector>

namespace ock {
namespace mf {
std::vector<uint32_t> NetworkGetIpAddresses() noexcept;
}
} // namespace ock

#endif // MEM_FABRIC_HYBRID_HYBM_NETWORKS_COMMON_H
```
**逐行解读**:
- 第 1-22 行: 版权声明、头文件保护
- 第 16-17 行: 引入必要头文件
- 第 19-21 行: 进入命名空间，声明获取本机 IP 地址列表的函数
  - 返回 uint32_t 格式的 IP 地址列表（网络字节序转换后）
  - noexcept 表示不抛出异常

---

## 7. hybm_networks_common.cpp 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_networks_common.cpp`
**代码行数**: 113 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <net/if.h>
#include <ifaddrs.h>

#include <fstream>
#include <sstream>
#include <algorithm>
#include <cerrno>
#include <cstring>
#include "hybm_functions.h"
#include "hybm_logger.h"
#include "hybm_networks_common.h"
```
**逐行解读**:
- 第 1-11 行: 版权声明
- 第 12 行: 引入系统类型定义
- 第 13 行: 引入网络地址转换函数
- 第 14 行: 引入 sockaddr_in 结构体
- 第 15 行: 引入网络接口标志
- 第 16 行: 引入 getifaddrs 函数
- 第 18 行: 引入文件流
- 第 19 行: 引入字符串流
- 第 20 行: 引入算法库（排序用）
- 第 21 行: 引入 errno 错误码
- 第 22 行: 引入字符串操作
- 第 23-25 行: 引入项目头文件

### GetDefaultRouteNetwork 内部函数 (第 27-62 行)

```cpp
namespace ock {
namespace mf {
namespace {
std::string GetDefaultRouteNetwork()
{
    std::string routeFileName{"/proc/net/route"};
    std::ifstream input(routeFileName);
    if (!input.is_open()) {
        BM_LOG_ERROR("open route file failed: " << strerror(errno));
        return "";
    }
```
**逐行解读**:
- 第 27-29 行: 进入 ock::mf 命名空间，使用匿名命名空间限制函数可见性
- 第 30-37 行: 定义获取默认路由网络接口名称的函数
  - 第 31 行: 路由文件路径（Linux 内核路由表）
  - 第 32 行: 打开文件
  - 第 34-37 行: 打开失败时记录错误并返回空字符串

```cpp
    std::string ifname;
    uint32_t destination;
    uint32_t temp;
    uint32_t mask;
    std::string line;
    std::getline(input, line); // skip header line
    while (std::getline(input, line)) {
        std::stringstream ss{line};
        ss >> ifname >> std::hex; // Iface
        ss >> destination;        // Destination
        ss >> temp;               // Gateway
        ss >> temp;               // Flags
        ss >> temp;               // RefCnt
        ss >> temp;               // Use
        ss >> temp;               // Metric
        ss >> mask;               // Mask
```
**逐行解读**:
- 第 39-43 行: 定义变量
  - ifname: 接口名称
  - destination: 目标地址
  - temp: 临时变量（用于跳过不需要的字段）
  - mask: 子网掩码
  - line: 每行文本
- 第 44 行: 跳过第一行（表头）
- 第 45 行: 逐行读取路由表
- 第 46 行: 创建字符串流解析行
- 第 47 行: 读取接口名称，设置十六进制模式
- 第 48 行: 读取目标地址
- 第 49-54 行: 跳过 Gateway、Flags、RefCnt、Use、Metric 字段
- 第 54 行: 读取掩码

```cpp
        if (destination == 0U && mask == 0U) {
            BM_LOG_INFO("default route network : " << ifname);
            return ifname;
        }
    }
    return "";
}
} // namespace
```
**逐行解读**:
- 第 55-58 行: 如果目标地址和掩码都为 0，表示默认路由，返回接口名
- 第 59-61 行: 没找到默认路由返回空字符串

### NetworkGetIpAddresses 主函数 (第 63-111 行)

```cpp
std::vector<uint32_t> NetworkGetIpAddresses() noexcept
{
    std::vector<uint32_t> addresses;
    struct ifaddrs *ifa;
    struct ifaddrs *p;
    if (getifaddrs(&ifa) < 0) {
        BM_LOG_ERROR("getifaddrs() failed: " << errno << " : " << SafeStrError(errno));
        return addresses;
    }
```
**逐行解读**:
- 第 63-71 行: 获取本机 IP 地址列表函数
  - 第 64 行: 结果向量
  - 第 65-66 行: ifaddrs 结构体指针
  - 第 68 行: 获取所有网络接口地址
  - 第 69-71 行: 失败时记录错误并返回空列表

```cpp
    uint32_t routeIp = 0;
    auto routeName = GetDefaultRouteNetwork();
    for (p = ifa; p != nullptr; p = p->ifa_next) {
        if (p->ifa_addr == nullptr) {
            continue;
        }

        if (p->ifa_addr->sa_family != AF_INET) {
            continue;
        }

        if ((p->ifa_flags & IFF_LOOPBACK) != 0) {
            continue;
        }

        if ((p->ifa_flags & IFF_UP) == 0 || (p->ifa_flags & IFF_RUNNING) == 0) {
            continue;
        }
```
**逐行解读**:
- 第 73 行: 路由 IP，初始化为 0
- 第 74 行: 获取默认路由接口名称
- 第 75 行: 遍历所有接口
- 第 76-78 行: 跳过空地址
- 第 80-82 行: 只处理 IPv4 地址
- 第 84-86 行: 跳过回环地址 (127.0.0.1)
- 第 88-90 行: 跳过未启动或未运行的接口

```cpp
        std::string ifname{p->ifa_name};
        auto sin = reinterpret_cast<struct sockaddr_in *>(p->ifa_addr);
        char ip_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &sin->sin_addr, ip_str, sizeof(ip_str));
        if (routeName == ifname) {
            routeIp = ntohl(sin->sin_addr.s_addr);
            BM_LOG_INFO("find route ip address: " << p->ifa_name << " -> " << ip_str);
        } else {
            addresses.emplace_back(ntohl(sin->sin_addr.s_addr));
            BM_LOG_INFO("find ip address: " << p->ifa_name << " -> " << ip_str);
        }
    }
```
**逐行解读**:
- 第 92 行: 获取接口名称
- 第 93 行: 转换为 sockaddr_in 指针
- 第 94 行: IP 地址字符串缓冲区
- 第 95 行: 将二进制 IP 转换为字符串
- 第 96-99 行: 如果是默认路由接口，保存到 routeIp
- 第 100-102 行: 否则添加到 addresses 列表

```cpp
    freeifaddrs(ifa);
    std::sort(addresses.begin(), addresses.end(), std::less<uint32_t>());
    if (routeIp != 0) {
        addresses.insert(addresses.begin(), routeIp);
    }
    return addresses;
}
} // namespace mf
} // namespace ock
```
**逐行解读**:
- 第 105 行: 释放 ifaddrs 内存
- 第 106 行: 对地址列表排序（从小到大）
- 第 107-109 行: 如果有路由 IP，插入到列表最前面
- 第 110 行: 返回地址列表
- 第 112-113 行: 命名空间结束

---

## 8. hybm_ptracer.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_ptracer.h`
**代码行数**: 127 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#ifndef MF_HYBRID_HYBM_PTRACER_H
#define MF_HYBRID_HYBM_PTRACER_H

#include "ptracer.h"
```
**逐行解读**:
- 第 1-16 行: 版权声明、头文件保护、引入 ptracer（来自 util 模块）

### 性能打点 ID 定义 (第 17-125 行)

```cpp
enum MF_HYBM_MOD {
    TP_HYBM_START = PTRACER_ID(0, 0U),
```
**逐行解读**:
- 第 18 行: 定义起始 ID，使用 PTRACER_ID 宏生成唯一 ID

#### SDMA 相关打点 (第 19-61 行)

```cpp
    TP_HYBM_SDMA_LH_TO_GH,
    TP_HYBM_SDMA_LH_TO_GD,
    TP_HYBM_SDMA_LD_TO_GH,
    TP_HYBM_SDMA_LD_TO_GD,
```
**逐行解读**:
- Local Host 到 Global Host/Device 的 SDMA 拷贝打点
- Local Device 到 Global Host/Device 的 SDMA 拷贝打点

```cpp
    TP_HYBM_SDMA_GH_TO_LD,
    TP_HYBM_SDMA_GH_TO_LH,
    TP_HYBM_SDMA_GD_TO_LD,
    TP_HYBM_SDMA_GD_TO_LH,
```
**逐行解读**:
- Global Host/Device 到 Local Device/Host 的 SDMA 拷贝打点

```cpp
    TP_HYBM_SDMA_BATCH_GH_TO_LD,
    TP_HYBM_SDMA_BATCH_LD_TO_GH,
    ...
    TP_HYBM_SDMA_BATCH_G_TO_G,
```
**逐行解读**:
- 批量 SDMA 拷贝打点（各种方向组合）

```cpp
    TP_HYBM_SDMA_WAIT,
    TP_HYBM_SDMA_PUT_WAIT,
```
**逐行解读**:
- SDMA 等待操作打点

#### Extend Copy 打点 (第 61-62 行)

```cpp
    TP_HYBM_EXTEND_COPY,
    TP_HYBM_EXTEND_BATCH_COPY,
```
**逐行解读**:
- 扩展拷贝功能打点

#### Host RDMA 打点 (第 64-85 行)

```cpp
    TP_HYBM_HOST_RDMA_LH_TO_GH,
    TP_HYBM_HOST_RDMA_LH_TO_GD,
    ...
    TP_HYBM_HOST_RDMA_BATCH_LOCAL_COPY,
```
**逐行解读**:
- Host 端 RDMA 操作打点，包括各种方向的拷贝和批量操作

#### Device RDMA 打点 (第 87-121 行)

```cpp
    TP_HYBM_RDMA_LH_TO_GH,
    TP_HYBM_RDMA_LH_TO_GD,
    ...
    TP_HYBM_DEV_SUBMIT_TASK,
    TP_HYBM_RDMA_BATCH_LOCAL,
```
**逐行解读**:
- Device 端 RDMA 操作打点，包括各种方向的拷贝、批量操作、任务提交

#### ACL 打点 (第 123-124 行)

```cpp
    TP_HYBM_ACL_BATCH_LD_TO_LH,
    TP_HYBM_ACL_BATCH_LH_TO_LD,
};
```
**逐行解读**:
- ACL (Ascend Computing Language) 批量本地设备间拷贝打点

---

## 9. hybm_space_allocator.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_space_allocator.h`
**代码行数**: 100 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MF_HYBM_SPACE_ALLOCATOR_H
#define MF_HYBM_SPACE_ALLOCATOR_H

#include <cstdint>
#include <memory>

namespace ock::mf {
```
**逐行解读**:
- 第 1-19 行: 版权声明、头文件保护、引入必要头文件、进入命名空间

### SpaceAllocator 抽象类 (第 20-32 行)

```cpp
class AllocatedElement;
class SpaceAllocator {
public:
    virtual ~SpaceAllocator() = default;

public:
    virtual bool CanAllocate(uint64_t size) const noexcept = 0;
    virtual AllocatedElement Allocate(uint64_t size) noexcept = 0;
    virtual bool Release(const AllocatedElement &element) noexcept = 0;
};

using SpaceAllocatorPtr = std::shared_ptr<SpaceAllocator>;
```
**逐行解读**:
- 第 21 行: 前向声明 AllocatedElement
- 第 22-30 行: 空间分配器抽象基类
  - 第 24 行: 虚析构函数，确保正确析构派生类
  - 第 27 行: 纯虚函数，检查是否可以分配指定大小
  - 第 28 行: 纯虚函数，分配空间
  - 第 29 行: 纯虚函数，释放已分配的空间
- 第 32 行: 定义智能指针类型别名

### AllocatedElement 类 (第 34-95 行)

```cpp
class AllocatedElement {
public:
    AllocatedElement() noexcept : startAddress{nullptr}, size{0}, allocator(nullptr) {}

    explicit AllocatedElement(uint8_t *p, uint64_t s, SpaceAllocator *allocator) noexcept
        : startAddress{p}, size{s}, allocator(allocator)
    {}
```
**逐行解读**:
- 第 34-40 行: 已分配元素类，RAII 风格的资源管理
  - 第 36 行: 默认构造函数，初始化为空状态
  - 第 38-40 行: 带参数的构造函数，explicit 防止隐式转换

```cpp
    virtual ~AllocatedElement()
    {
        if (allocator != nullptr) {
            allocator->Release(*this);
            Reset();
        }
    }
```
**逐行解读**:
- 第 42-48 行: 析构函数，自动释放资源
  - 如果有分配器，调用其 Release 方法
  - 然后重置自身状态

```cpp
    AllocatedElement(AllocatedElement &&another)
        : startAddress(another.startAddress), size(another.size), allocator(another.allocator)
    {
        another.Reset();
    };

    AllocatedElement &operator=(AllocatedElement &&another)
    {
        startAddress = another.startAddress;
        size = another.size;
        allocator = another.allocator;
        another.Reset();
        return *this;
    };
```
**逐行解读**:
- 第 50-54 行: 移动构造函数，窃取另一个对象的资源
- 第 56-63 行: 移动赋值运算符

```cpp
    // if need to copy, use shared_ptr to wrap AllocatedElement
    AllocatedElement(const AllocatedElement &) = delete;
    AllocatedElement &operator=(const AllocatedElement &) = delete;
```
**逐行解读**:
- 第 65-67 行: 禁用拷贝构造和拷贝赋值，防止资源重复释放

```cpp
    uint8_t *Address() noexcept
    {
        return startAddress;
    }

    const uint8_t *Address() const noexcept
    {
        return startAddress;
    }

    uint64_t Size() const noexcept
    {
        return size;
    }
```
**逐行解读**:
- 第 69-82 行: 获取地址和大小的访问器方法
  - 第 69-72 行: 可变地址访问器
  - 第 74-77 行: 常量地址访问器
  - 第 79-82 行: 大小访问器

```cpp
    void Reset() noexcept
    {
        startAddress = nullptr;
        size = 0;
        allocator = nullptr;
    }

private:
    uint8_t *startAddress;
    uint64_t size;
    SpaceAllocator *allocator;
};
```
**逐行解读**:
- 第 84-89 行: 重置函数，清空所有成员
- 第 91-95 行: 私有成员变量
  - startAddress: 分配的起始地址
  - size: 分配的大小
  - allocator: 所属的分配器指针（不负责释放）

---

## 10. hybm_rbtree_range_pool.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_rbtree_range_pool.h`
**代码行数**: 58 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MF_HYBM_RBTREE_RANGEALLOC_H
#define MF_HYBM_RBTREE_RANGEALLOC_H

#include <pthread.h>
#include <map>
#include <set>
#include "hybm_space_allocator.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-22 行: 版权声明、头文件保护、引入必要的头文件、进入命名空间

### SpaceRange 结构体 (第 23-28 行)

```cpp
struct SpaceRange {
    const uint64_t offset;
    const uint64_t size;

    SpaceRange(uint64_t o, uint64_t s) noexcept : offset{o}, size{s} {}
};
```
**逐行解读**:
- 第 23-28 行: 空间范围结构体，表示一段可用空间
  - offset: 偏移量
  - size: 大小
  - 两者都是 const，构造后不可修改

### RangeSizeFirst 比较器 (第 30-32 行)

```cpp
struct RangeSizeFirst {
    bool operator()(const SpaceRange &sr1, const SpaceRange &sr2) const noexcept;
};
```
**逐行解读**:
- 第 30-32 行: 自定义比较器，用于按大小优先排序空间范围

### RbtreeRangePool 类 (第 34-54 行)

```cpp
class RbtreeRangePool : public SpaceAllocator {
public:
    RbtreeRangePool(uint8_t *address, uint64_t size) noexcept;
    ~RbtreeRangePool() noexcept override;

public:
    bool CanAllocate(uint64_t size) const noexcept override;
    AllocatedElement Allocate(uint64_t size) noexcept override;
    bool Release(const AllocatedElement &element) noexcept override;

private:
    static uint64_t AllocateSizeAlignUp(uint64_t inputSize) noexcept;

private:
    uint8_t *const baseAddress;
    const uint64_t totalSize;
    mutable pthread_spinlock_t lock{};
    std::map<uint64_t, uint64_t> addressTree;    // 按地址索引的空闲空间
    std::set<SpaceRange, RangeSizeFirst> sizeTree; // 按大小索引的空闲空间
};
```
**逐行解读**:
- 第 34 行: 继承 SpaceAllocator，实现红黑树范围池
- 第 36-37 行: 构造函数，接收基地址和总大小
- 第 38 行: 析构函数
- 第 40-42 行: 实现接口方法
- 第 44 行: 私有静态方法，对齐分配大小
- 第 47-53 行: 私有成员
  - baseAddress: 基地址
  - totalSize: 总大小
  - lock: 自旋锁，保护内部数据结构
  - addressTree: 按地址索引的红黑树，key=偏移, value=大小
  - sizeTree: 按大小索引的红黑树，使用 RangeSizeFirst 比较器

**设计要点**: 使用两个红黑树实现高效的范围分配
- `addressTree`: 支持快速地址查找和相邻范围合并
- `sizeTree`: 支持最佳匹配分配（Best-Fit）

---

## 11. hybm_rbtree_range_pool.cpp 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_rbtree_range_pool.cpp`
**代码行数**: 135 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
#include "hybm_logger.h"
#include "hybm_rbtree_range_pool.h"

namespace ock {
namespace mf {
```
**逐行解读**:
- 第 1-15 行: 版权声明、引入头文件、进入命名空间

### RangeSizeFirst::operator() 实现 (第 17-24 行)

```cpp
bool RangeSizeFirst::operator()(const ock::mf::SpaceRange &sr1, const ock::mf::SpaceRange &sr2) const noexcept
{
    if (sr1.size != sr2.size) {
        return sr1.size < sr2.size;
    }

    return sr1.offset < sr2.offset;
}
```
**逐行解读**:
- 第 17-24 行: 比较函数实现
  - 第 18 行: 如果大小不同，按大小升序排序（小的在前）
  - 第 23 行: 如果大小相同，按偏移量升序排序

**设计目的**: 实现 Best-Fit 分配策略，同时保证唯一性

### 构造与析构函数 (第 26-36 行)

```cpp
RbtreeRangePool::RbtreeRangePool(uint8_t *address, uint64_t size) noexcept : baseAddress{address}, totalSize{size}
{
    pthread_spin_init(&lock, 0);
    addressTree[0] = size;
    sizeTree.insert({0, size});
}
```
**逐行解读**:
- 第 26-31 行: 构造函数
  - 初始化基类成员
  - 第 28 行: 初始化自旋锁
  - 第 29 行: 初始时整个空间都是空闲的，从偏移 0 开始
  - 第 30 行: 向 sizeTree 插入初始范围

```cpp
RbtreeRangePool::~RbtreeRangePool() noexcept
{
    pthread_spin_destroy(&lock);
}
```
**逐行解读**:
- 第 33-36 行: 析构函数，销毁自旋锁

### CanAllocate 实现 (第 38-47 行)

```cpp
bool RbtreeRangePool::CanAllocate(uint64_t size) const noexcept
{
    SpaceRange anchor{0, AllocateSizeAlignUp(size)};

    pthread_spin_lock(&lock);
    bool exists = (sizeTree.lower_bound(anchor) != sizeTree.end());
    pthread_spin_unlock(&lock);

    return exists;
}
```
**逐行解读**:
- 第 38-47 行: 检查是否可以分配指定大小
  - 第 40 行: 创建锚点范围，用于查找
  - 第 42 行: 加锁
  - 第 43 行: 使用 lower_bound 查找第一个 >= 锚点的范围
  - 第 44 行: 解锁
  - 第 46 行: 返回是否存在足够大的空闲块

### Allocate 实现 (第 49-83 行)

```cpp
AllocatedElement RbtreeRangePool::Allocate(uint64_t size) noexcept
{
    auto alignedSize = AllocateSizeAlignUp(size);
    SpaceRange anchor{0, alignedSize};
    pthread_spin_lock(&lock);
    auto sizePos = sizeTree.lower_bound(anchor);
    if (sizePos == sizeTree.end()) {
        pthread_spin_unlock(&lock);
        BM_LOG_ERROR("cannot allocate with size: " << size);
        return AllocatedElement{};
    }
```
**逐行解读**:
- 第 49-59 行: 分配函数实现
  - 第 51 行: 对齐分配大小
  - 第 52 行: 创建锚点用于查找
  - 第 53 行: 加锁
  - 第 54 行: 查找第一个足够大的空闲块
  - 第 55-59 行: 如果没找到，解锁、记录错误、返回空元素

```cpp
    if (baseAddress == nullptr) {
        pthread_spin_unlock(&lock);
        BM_LOG_ERROR("base is a null pointer.");
        return AllocatedElement{};
    }
    auto targetOffset = sizePos->offset;
    auto targetSize = sizePos->size;
    auto addrPos = addressTree.find(targetOffset);
    if (addrPos == addressTree.end()) {
        pthread_spin_unlock(&lock);
        BM_LOG_ERROR("offset: " << targetOffset << "size: " << targetSize << "in size tree, not in address tree.");
        return AllocatedElement{};
    }
```
**逐行解读**:
- 第 60-72 行: 参数校验
  - 检查 baseAddress 是否为空
  - 获取目标偏移和大小
  - 在 addressTree 中查找对应的条目
  - 如果找不到说明数据结构不一致，返回错误

```cpp
    sizeTree.erase(sizePos);
    addressTree.erase(addrPos);
    if (targetSize > alignedSize) {
        SpaceRange left{targetOffset + alignedSize, targetSize - alignedSize};
        addressTree.emplace(left.offset, left.size);
        sizeTree.emplace(left);
    }
    pthread_spin_unlock(&lock);
    return AllocatedElement{baseAddress + targetOffset, size, this};
}
```
**逐行解读**:
- 第 74-83 行: 执行分配
  - 第 74 行: 从 sizeTree 删除
  - 第 75 行: 从 addressTree 删除
  - 第 76-80 行: 如果分配后还有剩余空间，创建新的空闲块
  - 第 81 行: 解锁
  - 第 82 行: 返回分配的元素（注意返回原始请求的大小，不是对齐后的大小）

**分配算法**: Best-Fit + 剩余块处理

### Release 实现 (第 85-126 行)

```cpp
bool RbtreeRangePool::Release(const AllocatedElement &element) noexcept
{
    auto alignedSize = AllocateSizeAlignUp(element.Size());
    auto elemAddr = element.Address();
    if (baseAddress == nullptr || elemAddr == nullptr) {
        BM_LOG_ERROR("The addr is a null pointer.");
        return false;
    }
    if (elemAddr < baseAddress || elemAddr >= baseAddress + totalSize) {
        BM_LOG_ERROR("element address not in this range pool.");
        return false;
    }
```
**逐行解读**:
- 第 85-96 行: 释放函数实现
  - 第 87 行: 获取对齐后的大小
  - 第 88 行: 获取元素地址
  - 第 89-92 行: 检查空指针
  - 第 93-96 行: 检查地址是否在有效范围内

```cpp
    auto offset = static_cast<uint64_t>(elemAddr - baseAddress);
    uint64_t finalOffset = offset;
    uint64_t finalSize = alignedSize;

    pthread_spin_lock(&lock);
```
**逐行解读**:
- 第 98-102 行: 计算偏移量，初始化最终合并后的偏移和大小，加锁

```cpp
    auto prevAddrPos = addressTree.lower_bound(offset);
    if (prevAddrPos != addressTree.begin()) {
        --prevAddrPos;
        if (prevAddrPos != addressTree.end() && prevAddrPos->first + prevAddrPos->second == offset) { // 合并前一个range
            finalOffset = prevAddrPos->first;
            finalSize += prevAddrPos->second;
            sizeTree.erase(SpaceRange{prevAddrPos->first, prevAddrPos->second});
            addressTree.erase(prevAddrPos);
        }
    }
```
**逐行解读**:
- 第 103-112 行: 尝试与前一个空闲块合并
  - 第 103 行: 找到第一个 >= offset 的位置
  - 第 104 行: 回退到前一个元素
  - 第 105 行: 如果前一个块的结束地址正好等于当前块的起始
  - 第 107-111 行: 合并：更新偏移和大小，从两个树中删除前一个块

```cpp
    auto nextAddrPos = addressTree.find(offset + alignedSize);
    if (nextAddrPos != addressTree.end()) { // 合并后一个range
        finalSize += nextAddrPos->second;
        sizeTree.erase(SpaceRange{nextAddrPos->first, nextAddrPos->second});
        addressTree.erase(nextAddrPos);
    }
```
**逐行解读**:
- 第 114-119 行: 尝试与后一个空闲块合并
  - 第 114 行: 查找紧随其后的空闲块
  - 第 115-119 行: 如果存在，合并大小并删除

```cpp
    addressTree.emplace(finalOffset, finalSize);
    sizeTree.emplace(SpaceRange{finalOffset, finalSize});

    pthread_spin_unlock(&lock);
    return true;
}
```
**逐行解读**:
- 第 121-122 行: 将合并后的空闲块插入两个树
- 第 124 行: 解锁
- 第 125 行: 返回成功

**释放算法**: Coalescing（合并相邻空闲块）

### AllocateSizeAlignUp 实现 (第 128-133 行)

```cpp
uint64_t RbtreeRangePool::AllocateSizeAlignUp(uint64_t inputSize) noexcept
{
    constexpr uint64_t alignSize = 4096UL;
    constexpr uint64_t alignSizeMask = ~(alignSize - 1UL);
    return (inputSize + alignSize - 1UL) & alignSizeMask;
}
```
**逐行解读**:
- 第 128-133 行: 对齐到 4KB 边界
  - alignSize = 4096 (4KB)
  - alignSizeMask = ~0xFFF = 0xFFFFF1000
  - 公式: `(size + 4095) & ~0xFFF` 实现向上对齐

---

## 12. hybm_version.h 逐行解读

**文件路径**: `src/hybm/csrc/common/hybm_version.h`
**代码行数**: 36 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/

#ifndef MEM_FABRIC_HYBRID_HYBM_VERSION_H
#define MEM_FABRIC_HYBRID_HYBM_VERSION_H

/* second level marco define 'CON' to get string */
#define CONCAT(x, y, z)  x.##y.##z
#define STR(x)           #x
#define CONCAT2(x, y, z) CONCAT(x, y, z)
#define STR2(x)          STR(x)
```
**逐行解读**:
- 第 1-20 行: 版权声明、头文件保护
- 第 17 行: CONCAT 宏，使用 `##` 标记连接符连接三个 token
- 第 18 行: STR 宏，使用 `#` 将 token 转换为字符串
- 第 19 行: CONCAT2 宏，调用 CONCAT
- 第 20 行: STR2 宏，调用 STR

```cpp
/* get cancat version string */
#define SM_VERSION STR2(CONCAT2(VERSION_MAJOR, VERSION_MINOR, VERSION_FIX))
```
**逐行解读**:
- 第 23 行: SM_VERSION 宏，展开过程：
  1. `CONCAT2(1, 0, 0)` → `1.0.0` (假设版本是 1.0.0)
  2. `STR2(1.0.0)` → `"1.0.0"`

```cpp
#ifndef GIT_LAST_COMMIT
#define GIT_LAST_COMMIT empty
#endif

/*
 * global lib version string with build time
 */
static const char *LIB_VERSION =
    "library version: " SM_VERSION ", build time: " __DATE__ " " __TIME__ ", commit: " STR2(GIT_LAST_COMMIT);
```
**逐行解读**:
- 第 25-27 行: 如果没有定义 GIT_LAST_COMMIT，定义为 "empty"
- 第 32-33 行: 定义全局版本字符串，包含：
  - 库版本号
  - 编译日期 (__DATE__)
  - 编译时间 (__TIME__)
  - Git 提交 hash

**示例输出**: `"library version: 1.0.0, build time: Feb 24 2026 10:30:00, commit: abc1234"`

---

## 总结

hybm/common 模块是 HyBM 的基础设施层，提供：

1. **核心定义** ([hybm_define.h](../src/hybm/csrc/common/hybm_define.h)): 地址空间布局、常量、Magic 值
2. **类型系统** ([hybm_types.h](../src/hybm/csrc/common/hybm_types.h)): 错误码定义
3. **工具函数** ([hybm_functions.h](../src/hybm/csrc/common/hybm_functions.h)): Magic 生成/验证、设备 ID 获取、线程 ID 获取
4. **日志系统** ([hybm_logger.h](../src/hybm/csrc/common/hybm_logger.h)): 日志宏、断言宏
5. **网络工具** ([hybm_networks_common.cpp](../src/hybm/csrc/common/hybm_networks_common.cpp)): 获取本机 IP 地址
6. **性能打点** ([hybm_ptracer.h](../src/hybm/csrc/common/hybm_ptracer.h)): 各种操作的性能打点 ID
7. **内存分配器** ([hybm_space_allocator.h](../src/hybm/csrc/common/hybm_space_allocator.h), [hybm_rbtree_range_pool.cpp](../src/hybm/csrc/common/hybm_rbtree_range_pool.cpp)): 基于 Best-Fit 算法的范围池
8. **版本信息** ([hybm_version.h](../src/hybm/csrc/common/hybm_version.h)): 编译版本字符串

**设计亮点**:
- 红黑树范围池使用两个树实现 O(log n) 的分配和释放
- Coalescing 算法减少内存碎片
- RAII 风格的 AllocatedElement 自动资源管理
