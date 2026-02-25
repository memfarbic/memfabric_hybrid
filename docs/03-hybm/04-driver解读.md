# hybm/driver 模块逐行解读

## 模块概述

hybm/driver 模块是 HyBM 的驱动层，负责与底层设备驱动交互，提供设备内存管理和全局虚拟地址（GVA）管理功能。

### 文件清单

| 文件路径 | 代码行数 | 功能描述 |
|---------|---------|---------|
| [hybm_driver.h](../../src/hybm/csrc/driver/hybm_driver.h) | 18 行 | 驱动版本工具函数声明 |
| [hybm_cmd.h](../../src/hybm/csrc/driver/hybm_cmd.h) | 34 行 | 驱动命令接口 |
| [hybm_gva.h](../../src/hybm/csrc/driver/hybm_gva.h) | 27 行 | GVA 接口声明 |
| [hybm_gva.cpp](../../src/hybm/csrc/driver/hybm_gva.cpp) | 83 行 | GVA 初始化实现 |
| [userspace/devmm_ioctl.h](../../src/hybm/csrc/driver/userspace/devmm_ioctl.h) | 72 行 | IOCTL 命令定义 |
| [userspace/devmm_ioctl.cpp](../../src/hybm/csrc/driver/userspace/devmm_ioctl.cpp) | 144 行 | IOCTL 实现 |
| [userspace/devmm_define.h](../../src/hybm/csrc/driver/userspace/devmm_define.h) | 307 行 | 设备内存管理定义 |
| [userspace/devmm_svm_gva.h](../../src/hybm/csrc/driver/userspace/devmm_svm_gva.h) | 42 行 | SVM GVA 接口 |
| [userspace/devmm_svm_gva.cpp](../../src/hybm/csrc/driver/userspace/devmm_svm_gva.cpp) | 696 行 | SVM GVA 实现 |
| [version/hybm_gva_version.h](../../src/hybm/csrc/driver/version/hybm_gva_version.h) | 29 行 | GVA 版本管理 |
| [npu_direct_rdma/src/npu_direct_rdma.c](../../src/hybm/csrc/driver/npu_direct_rdma/src/npu_direct_rdma.c) | - | NPU Direct RDMA |

### 核心概念

1. **GVA (Global Virtual Address)**: 全局虚拟地址，统一的虚拟地址空间
2. **SVM (Shared Virtual Memory)**: 共享虚拟内存，Host 和 Device 共享同一地址空间
3. **Heap Management**: 堆管理器，使用红黑树管理分配的内存块
4. **IOCTL**: 系统调用接口，与内核驱动通信

---

## 一、hybm_cmd.h 逐行解读

### 文件信息
- 文件路径: `src/hybm/csrc/driver/hybm_cmd.h`
- 代码行数: 34 行
- 主要功能: 定义驱动命令接口

### 完整代码

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

#ifndef HYBM_HYBM_CMD_H
#define HYBM_HYBM_CMD_H

#include <string>

namespace ock {
namespace mf {
namespace drv {

void HybmInitialize(int deviceId, int fd) noexcept;

int HybmMapShareMemory(const char *name, void *expectAddr, uint64_t size, uint64_t flags) noexcept;

int HybmUnmapShareMemory(void *expectAddr, uint64_t flags) noexcept;

int HybmIoctlAllocAnddAdvice(uint64_t ptr, size_t size, uint32_t devid, uint32_t advise) noexcept;

} // namespace drv
} // namespace mf
} // namespace ock

#endif // HYBM_HYBM_CMD_H
```

### 逐行解读

**第 1-11 行**: 版权和许可证声明

**第 12-13 行**: 头文件保护宏 `HYBM_HYBM_CMD_H`

**第 15 行**: 引入 `string` 头文件

**第 17-20 行**: 命名空间定义
- `ock` - 外层命名空间
- `mf` - 中层命名空间（Memory Fabric）
- `drv` - 内层命名空间（Driver）

**第 22 行**: `HybmInitialize` 函数声明
- **功能**: 初始化 HyBM 驱动层
- **参数**:
  - `deviceId`: 设备 ID
  - `fd`: 驱动文件描述符
- **修饰**: `noexcept` - 不抛出异常

**第 24 行**: `HybmMapShareMemory` 函数声明
- **功能**: 映射共享内存到指定地址
- **参数**:
  - `name`: 共享内存名称
  - `expectAddr`: 期望映射的地址
  - `size`: 映射大小
  - `flags`: 标志位

**第 26 行**: `HybmUnmapShareMemory` 函数声明
- **功能**: 取消映射共享内存
- **参数**:
  - `expectAddr`: 要取消映射的地址
  - `flags`: 标志位

**第 28 行**: `HybmIoctlAllocAnddAdvice` 函数声明
- **功能**: 通过 IOCTL 分配内存并设置建议
- **参数**:
  - `ptr`: 内存地址
  - `size`: 内存大小
  - `devid`: 设备 ID
  - `advise`: 内存建议标志（如 HBM/DDR）

---

## 二、hybm_gva.h 和 hybm_gva.cpp 逐行解读

### 文件信息
- 文件路径: `src/hybm/csrc/driver/hybm_gva.h`
- 代码行数: 27 行
- 主要功能: GVA 初始化接口

### hybm_gva.h 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#ifndef HYBM_GVA_H
#define HYBM_GVA_H

#include <cstdint>

namespace ock {
namespace mf {

int32_t HybmGetInitedLogicDeviceId();
int32_t hybm_init_hbm_gva(uint16_t deviceId, uint64_t flags, uint64_t &baseAddress);

} // namespace mf
} // namespace ock

#endif
```

### 逐行解读

**第 21 行**: `HybmGetInitedLogicDeviceId` 函数
- **功能**: 获取已初始化的逻辑设备 ID

**第 22 行**: `hybm_init_hbm_gva` 函数
- **功能**: 初始化 HBM GVA 空间
- **参数**:
  - `deviceId`: 物理设备 ID
  - `flags`: 初始化标志
  - `baseAddress`: 输出参数，返回基地址

### hybm_gva.cpp 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#include "devmm_svm_gva.h"
#include "dl_api.h"
#include "dl_acl_api.h"
#include "dl_hal_api.h"
#include "hybm_cmd.h"
#include "hybm_functions.h"

#include "hybm_gva.h"

namespace ock {
namespace mf {

namespace {
int32_t initedLogicDeviceId = -1;
} // namespace

int32_t HybmGetInitedLogicDeviceId()
{
    return initedLogicDeviceId;
}

int32_t hybm_init_hbm_gva(uint16_t deviceId, uint64_t flags, uint64_t &baseAddress)
{
#if !defined(ASCEND_NPU)
    return BM_OK;
#else
    initedLogicDeviceId = Func::GetLogicDeviceId(deviceId);
    if (initedLogicDeviceId < 0) {
        BM_LOG_ERROR("Failed to get logic deviceId: " << deviceId);
        return BM_ERROR;
    }
    BM_LOG_INFO("Success get deviceId: " << deviceId << ", logicDeviceId: " << initedLogicDeviceId);
    auto ret = DlAclApi::AclrtSetDevice(deviceId);
    if (ret != BM_OK) {
        BM_LOG_ERROR("set device id to be " << deviceId << " failed: " << ret);
        return BM_ERROR;
    }
    drv::HybmInitialize(initedLogicDeviceId, DlHalApi::GetFd());

    if ((flags & HYBM_FLAG_INIT_SHMEM_META) == 0) {
        BM_LOG_DEBUG("skip init shm meta space:" << flags);
        baseAddress = 0;
        return BM_OK;
    } else {
        BM_LOG_DEBUG("restore init flag");
        flags &= ~HYBM_FLAG_INIT_SHMEM_META;
    }

    void *globalMemoryBase = nullptr;
    size_t allocSize = HYBM_DEVICE_INFO_SIZE; // 申请meta空间
    ret = drv::HalGvaReserveMemory((uint64_t *)&globalMemoryBase, allocSize, initedLogicDeviceId, flags);
    if (ret != 0 || reinterpret_cast<uint64_t>(globalMemoryBase) != (SVM_END_ADDR - GB)) {
        BM_LOG_ERROR("initialize mete memory failed: " << ret << " size:0x" << std::hex << allocSize <<
                     " flag:0x" << flags << " ret_addr:" << globalMemoryBase);
        return BM_ERROR;
    }

    ret = drv::HalGvaAlloc(HYBM_DEVICE_META_ADDR, HYBM_DEVICE_INFO_SIZE, 0);
    if (ret != BM_OK) {
        (void)drv::HalGvaUnreserveMemory((uint64_t)globalMemoryBase);
        BM_LOG_ERROR("HalGvaAlloc hybm meta memory failed: " << ret);
        return BM_MALLOC_FAILED;
    }

    baseAddress = reinterpret_cast<uint64_t>(globalMemoryBase);
    return BM_OK;
#endif
}

} // namespace mf
} // namespace ock
```

### 逐行解读

**第 12-20 行**: 头文件引用
- 第 13 行: `devmm_svm_gva.h` - SVM GVA 接口
- 第 14 行: `dl_api.h` - 动态加载 API
- 第 15 行: `dl_acl_api.h` - ACL API（Ascend Computing Language）
- 第 16 行: `dl_hal_api.h` - HAL API（Hardware Abstraction Layer）

**第 25-27 行**: 匿名命名空间
- **功能**: 存储模块私有变量
- 第 26 行: `initedLogicDeviceId` - 已初始化的逻辑设备 ID，初始值为 -1

**HybmGetInitedLogicDeviceId（第 29-32 行）**:
- **功能**: 返回已初始化的逻辑设备 ID
- 第 31 行: 直接返回 `initedLogicDeviceId` 变量

**hybm_init_hbm_gva（第 34-80 行）**:
- **功能**: 初始化 HBM GVA 空间

**第 36-38 行**: 非昇腾 NPU 平台直接返回成功

**第 39 行**: 获取逻辑设备 ID
- `Func::GetLogicDeviceId` - 支持环境变量映射（ASCEND_RT_VISIBLE_DEVICES）

**第 40-43 行**: 错误处理
- 获取失败时记录错误日志并返回 `BM_ERROR`

**第 44-45 行**: 成功日志

**第 46-49 行**: 设置 ACL 设备
- `DlAclApi::AclrtSetDevice` - 设置当前使用的设备

**第 50 行**: 初始化驱动层
- `drv::HybmInitialize` - 传入逻辑设备 ID 和文件描述符

**第 52-56 行**: 检查是否需要初始化共享内存元数据
- 如果未设置 `HYBM_FLAG_INIT_SHMEM_META` 标志，跳过元数据初始化

**第 58-59 行**: 清除初始化标志位

**第 61-62 行**: 准备分配元数据空间
- `globalMemoryBase` - 存储分配的基地址
- `allocSize` - 分配大小为 `HYBM_DEVICE_INFO_SIZE`

**第 63 行**: 预留 GVA 内存
- `drv::HalGvaReserveMemory` - 从 SVM 空间末尾向前分配

**第 64-68 行**: 验证分配结果
- 检查返回值是否为 0
- 检查地址是否为 `SVM_END_ADDR - GB`（SVM 空间末尾 1GB 处）

**第 70-75 行**: 分配元数据内存
- `drv::HalGvaAlloc` - 实际分配内存
- 失败时取消预留并返回错误

**第 77 行**: 设置输出参数 `baseAddress`

**第 78 行**: 返回成功

---

## 三、devmm_define.h 逐行解读

### 文件信息
- 文件路径: `src/hybm/csrc/driver/userspace/devmm_define.h`
- 代码行数: 307 行
- 主要功能: 设备内存管理定义

### 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#ifndef MEM_FABRIC_HYBRID_DEVMM_DEFINE_H
#define MEM_FABRIC_HYBRID_DEVMM_DEFINE_H

#include <cstdint>

constexpr uint64_t DEVMM_MAP_ALIGN_SIZE = 0x200000U;
constexpr uint64_t DEVMM_HEAP_SIZE = (1UL << 30UL);
constexpr size_t DEVMM_SVM_MEM_SIZE = (1UL << 43UL);
constexpr uint64_t DEVMM_SVM_MEM_START = 0x100000000000ULL;
constexpr uint32_t DEVMM_MAX_HEAP_NUM = (DEVMM_SVM_MEM_SIZE >> 30);

constexpr uint32_t DV_ADVISE_DDR = 0x0001;
constexpr uint32_t DV_ADVISE_HBM = 0x0002;
constexpr uint32_t DV_ADVISE_HUGEPAGE = 0x0004;
constexpr uint32_t DV_ADVISE_GIANTPAGE = 0x8000;
constexpr uint32_t DV_ADVISE_POPULATE = 0x0008;
constexpr uint32_t DV_ADVISE_LOCK_DEV = 0x0080;
constexpr uint32_t DV_ADVISE_MODULE_ID_BIT = 24;
constexpr uint32_t DV_ADVISE_MODULE_ID_MASK = 0xff;
constexpr uint32_t HCCL_HAL_MODULE_ID = 3;
constexpr uint32_t APP_MODULE_ID = 33;

constexpr uint32_t DEVMM_NODE_MAPPED_BIT = 1;
constexpr uint32_t DEVMM_NODE_MEMTYPE_SHIFT = 2;
constexpr uint32_t DEVMM_NODE_MEMTYPE_WID = 4;

constexpr uint32_t DEVMM_NODE_MAPPED_FLG = (1UL << DEVMM_NODE_MAPPED_BIT);
constexpr uint32_t DEVMM_HEAP_HUGE_PAGE = 0xEFEF0002UL;
constexpr uint32_t DEVMM_HEAP_CHUNK_PAGE = 0xEFEF0003UL;

constexpr uint32_t DEVMM_MAX_PHY_DEVICE_NUM = 64;
constexpr uint32_t SVM_MAX_AGENT_NUM = 65;

#ifndef ALIGN_DOWN
#define ALIGN_DOWN(val, al) ((val) & ~((al) - 1))
#endif

#ifndef ALIGN_UP
#define ALIGN_UP(val, al) (((val) + ((al) - 1)) & ~((al) - 1))
#endif

enum MemVal {
    MEM_SVM_VAL = 0X0,
    MEM_DEV_VAL = 0X1,
    MEM_HOST_VAL = 0X2,
    MEM_DVPP_VAL = 0X3,
    MEM_HOST_AGENT_VAL = 0X4,
    MEM_RESERVE_VAL = 0X5,
    MEM_MAX_VAL = 0X6
};

enum DevHeapSubType {
    SUB_SVM_TYPE = 0x0,           /* user mode page is same as kernel page, huge or chunk. the same as MEM_SVM_VAL */
    SUB_DEVICE_TYPE = 0x1,        /* user mode page is same as kernel page, just huge. the same as MEM_DEV_VAL */
    SUB_HOST_TYPE = 0x2,          /* user mode page is same as kernel page just chunk. the same as MEM_HOST_VAL */
    SUB_DVPP_TYPE = 0x3,          /* kernel page is huge, user mode page is chunk. the same as MEM_DVPP_VAL */
    SUB_READ_ONLY_TYPE = 0x4,     /* kernel page is huge, user mode page is chunk. MEM_DEV_VAL */
    SUB_RESERVE_TYPE = 0X5,       /* For halMemAddressReserve */
    SUB_DEV_READ_ONLY_TYPE = 0x6, /* kernel page is huge, user mode page is chunk. MEM_DEV_VAL */
    SUB_MAX_TYPE
};

enum DevMemType {
    DEVMM_HBM_MEM = 0x0,
    DEVMM_DDR_MEM,
    DEVMM_P2P_HBM_MEM,
    DEVMM_P2P_DDR_MEM,
    DEVMM_TS_DDR_MEM,
    DEVMM_MEM_TYPE_MAX
};

enum DevPageType { DEVMM_NORMAL_PAGE_TYPE = 0x0, DEVMM_HUGE_PAGE_TYPE, DEVMM_PAGE_TYPE_MAX };

enum DevHeapListType {
    SVM_LIST,
    HOST_LIST,
    DEVICE_AGENT0_LIST,
    DEVICE_AGENT63_LIST = DEVICE_AGENT0_LIST + DEVMM_MAX_PHY_DEVICE_NUM - 1,
    HOST_AGENT_LIST,
    RESERVE_LIST,
    HEAP_MAX_LIST,
};

struct DevVirtHeapType {
    uint32_t heap_type;
    uint32_t heap_list_type;
    uint32_t heap_sub_type;
    uint32_t heap_mem_type; /* A heap belongs to only one physical memory type. --DevMemType */
};

struct MemStatsType {
    uint32_t mem_val;
    uint32_t page_type;
    uint32_t phy_memtype;
};

enum DMemType {
    DEVMM_MEM_NORMAL = 0,
    DEVMM_MEM_RDONLY,
    DEVMM_MEMTYPE_MAX,
};

struct DevVirtComHeap;

struct DComHeapOps {
    uint64_t (*heap_alloc)(struct DevVirtComHeap *heap, uint64_t va, size_t size, uint32_t advise);
    int32_t (*heap_free)(struct DevVirtComHeap *heap, uint64_t ptr);
};

struct DVirtListHead {
    struct DVirtListHead *next, *prev;
};

enum DMappedRbtreeType { DEVMM_MAPPED_RW_TREE = 0, DEVMM_MAPPED_RDONLY_TREE, DEVMM_MAPPED_TREE_TYPE_MAX };

struct ListNode {
    struct ListNode *next;
    struct ListNode *prev;
};

struct DevNodeData {
    uint64_t va;
    uint64_t size;
    uint64_t total;
    uint32_t flag;
};

struct RbtreeNode {
    unsigned long rbtree_parent_color;
    struct RbtreeNode *rbtree_right;
    struct RbtreeNode *rbtree_left;
};

struct RbtreeRoot {
    struct RbtreeNode *RbtreeNode;
    uint64_t rbtree_len;
};

struct RbNode {
    struct RbtreeNode RbtreeNode;
    uint64_t key;
};

struct MultiRbNode {
    struct RbNode multi_rbtree_node;
    struct ListNode list;
    uint8_t is_list_first;
};

struct DevRbtreeNode {
    struct MultiRbNode va_node;
    struct MultiRbNode size_node;
    struct MultiRbNode cache_node;
    struct DevNodeData data;
};

struct DCacheList {
    struct DevRbtreeNode cache;
    struct ListNode list;
    uint8_t is_new;
};

struct DevHeapRbtree {
    struct RbtreeRoot *alloced_tree;
    struct RbtreeRoot *idle_size_tree;
    struct RbtreeRoot *idle_va_tree;
    struct RbtreeRoot *idle_mapped_cache_tree[DEVMM_MAPPED_TREE_TYPE_MAX];
    struct DCacheList *head;
    uint32_t devmm_cache_numsize;
};

struct DevHeapList {
    int heap_cnt;
    pthread_rwlock_t list_lock;
    struct DVirtListHead heap_list;
};

struct DevVirtComHeap {
    uint32_t inited;
    uint32_t heap_type;
    uint32_t heap_sub_type;
    uint32_t heap_list_type;
    uint32_t heap_mem_type;
    uint32_t heap_idx;
    bool is_base_heap;

    uint64_t cur_cache_mem[DEVMM_MEMTYPE_MAX];        /* current cached mem */
    uint64_t cache_mem_thres[DEVMM_MEMTYPE_MAX];      /* cached mem threshold */
    uint64_t cur_alloc_cache_mem[DEVMM_MEMTYPE_MAX];  /* current alloc can cache total mem */
    uint64_t peak_alloc_cache_mem[DEVMM_MEMTYPE_MAX]; /* peak alloc can cache */
    time_t peak_alloc_cache_time[DEVMM_MEMTYPE_MAX];  /* the time peak alloc can cache */
    uint32_t need_cache_thres[DEVMM_MEMTYPE_MAX];     /* alloc size need to cache threshold */
    bool is_limited; /* true: this kind of heap is resource-limited, not allowd to be alloced another new heap.
                           The heap's cache will be shrinked forcibly, when it's not enough for nocache's allocation */
    bool is_cache;   /* true: follow the cache rule, devmm_get_free_threshold_by_type, used by normal heap.
                           false: no cache, free the heap immediately, used by specified va alloc. For example,
                                  alloc 2M success, free 2M success, alloc 2G will fail because of cache heap. */
    uint64_t start;
    uint64_t end;

    uint32_t module_id; /* used for large heap (>=512M) */
    uint32_t side;      /* used for large heap (>=512M) */
    uint32_t devid;     /* used for large heap (>=512M) */
    uint64_t mapped_size;

    uint32_t chunk_size;
    uint32_t kernel_page_size; /* get from kernel */
    uint32_t map_size;
    uint64_t heap_size;

    struct DComHeapOps *ops;
    pthread_mutex_t tree_lock;
    pthread_rwlock_t heap_rw_lock;
    uint64_t sys_mem_alloced;
    uint64_t sys_mem_freed;
    uint64_t sys_mem_alloced_num;
    uint64_t sys_mem_freed_num;

    struct DVirtListHead list; /* associated to base heap's DevHeapList */
    struct DevHeapRbtree rbtree_queue;
};

struct DHeapQueue {
    struct DevVirtComHeap base_heap; /* use for manage 32T heap, heap range 1g */
    struct DevVirtComHeap *heaps[DEVMM_MAX_HEAP_NUM];
};

struct DevVirtHeapMgmt {
    uint32_t inited;
    pid_t pid;

    uint64_t max_conti_size; /* eq heap size */

    uint64_t start; /* svm page_size aligned */
    uint64_t end;   /* svm page_size aligned */

    uint64_t dvpp_start; /* dvpp vaddr start */
    uint64_t dvpp_end;   /* dvpp vaddr end */
    uint64_t dvpp_mem_size[DEVMM_MAX_PHY_DEVICE_NUM];

    uint64_t read_only_start; /* read vaddr start */
    uint64_t read_only_end;   /* read vaddr end */

    uint32_t svm_page_size;
    uint32_t local_page_size;
    uint32_t huge_page_size;
    bool support_bar_mem[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_dev_read_only[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_dev_mem_map_host[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_bar_huge_mem[DEVMM_MAX_PHY_DEVICE_NUM];
    bool host_support_pin_user_pages_interface;
    bool support_host_rw_dev_ro;
    uint64_t double_pgtable_offset[DEVMM_MAX_PHY_DEVICE_NUM];

    struct DHeapQueue heap_queue;
    struct DevHeapList huge_list[HEAP_MAX_LIST][SUB_MAX_TYPE][DEVMM_MEM_TYPE_MAX];
    struct DevHeapList normal_list[HEAP_MAX_LIST][SUB_MAX_TYPE][DEVMM_MEM_TYPE_MAX];
};

struct DevVirtHeapMgmtV2 {
    uint32_t inited;
    pid_t pid;

    uint64_t max_conti_size; /* eq heap size */

    uint64_t start; /* svm page_size aligned */
    uint64_t end;   /* svm page_size aligned */

    uint64_t dvpp_start; /* dvpp vaddr start */
    uint64_t dvpp_end;   /* dvpp vaddr end */
    uint64_t dvpp_mem_size[DEVMM_MAX_PHY_DEVICE_NUM];

    uint64_t read_only_start; /* read vaddr start */
    uint64_t read_only_end;   /* read vaddr end */

    uint32_t svm_page_size;
    uint32_t local_page_size;
    uint32_t huge_page_size;
    bool support_bar_mem[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_dev_read_only[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_dev_mem_map_host[DEVMM_MAX_PHY_DEVICE_NUM];
    bool support_bar_huge_mem[DEVMM_MAX_PHY_DEVICE_NUM];
    bool host_support_pin_user_pages_interface;
    bool support_host_rw_dev_ro;
    uint64_t double_pgtable_offset[DEVMM_MAX_PHY_DEVICE_NUM];

    bool support_host_pin_pre_register;
    bool support_host_mem_pool;
    bool is_dev_inited[SVM_MAX_AGENT_NUM];

    struct DHeapQueue heap_queue;
    struct DevHeapList huge_list[HEAP_MAX_LIST][SUB_MAX_TYPE][DEVMM_MEM_TYPE_MAX];
    struct DevHeapList normal_list[HEAP_MAX_LIST][SUB_MAX_TYPE][DEVMM_MEM_TYPE_MAX];
};

#endif // MEM_FABRIC_HYBRID_DEVMM_DEFINE_H
```

### 逐行解读

**第 18-22 行**: 地址空间常量
- 第 18 行: `DEVMM_MAP_ALIGN_SIZE = 2MB` - 映射对齐大小
- 第 19 行: `DEVMM_HEAP_SIZE = 1GB` - 堆大小
- 第 20 行: `DEVMM_SVM_MEM_SIZE = 8TB` - SVM 地址空间大小
- 第 21 行: `DEVMM_SVM_MEM_START = 256GB` - SVM 地址空间起始
- 第 22 行: `DEVMM_MAX_HEAP_NUM = 8192` - 最大堆数量

**第 24-33 行**: 内存建议标志
- 第 24 行: `DV_ADVISE_DDR = 0x0001` - 使用 DDR 内存
- 第 25 行: `DV_ADVISE_HBM = 0x0002` - 使用 HBM 内存
- 第 26 行: `DV_ADVISE_HUGEPAGE = 0x0004` - 使用大页（2MB）
- 第 27 行: `DV_ADVISE_GIANTPAGE = 0x8000` - 使用巨页
- 第 28 行: `DV_ADVISE_POPULATE = 0x0008` - 预填充物理内存
- 第 29 行: `DV_ADVISE_LOCK_DEV = 0x0080` - 锁定到设备
- 第 30 行: `DV_ADVISE_MODULE_ID_BIT = 24` - 模块 ID 位移
- 第 31 行: `DV_ADVISE_MODULE_ID_MASK = 0xff` - 模块 ID 掩码
- 第 32 行: `HCCL_HAL_MODULE_ID = 3` - HCCL 模块 ID
- 第 33 行: `APP_MODULE_ID = 33` - 应用模块 ID

**第 46-52 行**: 对齐宏
- 第 47-48 行: `ALIGN_DOWN` - 向下对齐
- 第 50-51 行: `ALIGN_UP` - 向上对齐

**第 54-62 行**: `MemVal` 枚举 - 内存值类型
- `MEM_SVM_VAL = 0x0` - SVM 内存
- `MEM_DEV_VAL = 0x1` - 设备内存
- `MEM_HOST_VAL = 0x2` - Host 内存
- `MEM_DVPP_VAL = 0x3` - DVPP 内存
- `MEM_HOST_AGENT_VAL = 0x4` - Host Agent 内存
- `MEM_RESERVE_VAL = 0x5` - 预留内存

**第 64-73 行**: `DevHeapSubType` 枚举 - 堆子类型
- `SUB_SVM_TYPE = 0x0` - SVM 类型
- `SUB_DEVICE_TYPE = 0x1` - 设备类型
- `SUB_HOST_TYPE = 0x2` - Host 类型
- `SUB_DVPP_TYPE = 0x3` - DVPP 类型
- `SUB_READ_ONLY_TYPE = 0x4` - 只读类型
- `SUB_RESERVE_TYPE = 0x5` - 预留类型
- `SUB_DEV_READ_ONLY_TYPE = 0x6` - 设备只读类型

**第 75-82 行**: `DevMemType` 枚举 - 设备内存类型
- `DEVMM_HBM_MEM = 0x0` - HBM 内存
- `DEVMM_DDR_MEM` - DDR 内存
- `DEVMM_P2P_HBM_MEM` - P2P HBM 内存
- `DEVMM_P2P_DDR_MEM` - P2P DDR 内存
- `DEVMM_TS_DDR_MEM` - TS DDR 内存

**第 84 行**: `DevPageType` 枚举 - 页类型
- `DEVMM_NORMAL_PAGE_TYPE = 0x0` - 普通页（4KB）
- `DEVMM_HUGE_PAGE_TYPE` - 大页（2MB）

**第 86-94 行**: `DevHeapListType` 枚举 - 堆列表类型
- `SVM_LIST` - SVM 列表
- `HOST_LIST` - Host 列表
- `DEVICE_AGENT0_LIST` - 设备 Agent 0 列表
- `DEVICE_AGENT63_LIST` - 设备 Agent 63 列表（共 64 个设备）
- `HOST_AGENT_LIST` - Host Agent 列表
- `RESERVE_LIST` - 预留列表

**第 96-101 行**: `DevVirtHeapType` 结构体
- 第 97 行: `heap_type` - 堆类型（大页/普通页）
- 第 98 行: `heap_list_type` - 堆列表类型
- 第 99 行: `heap_sub_type` - 堆子类型
- 第 100 行: `heap_mem_type` - 堆内存类型（HBM/DDR）

**第 96-101 行**: `MemStatsType` 结构体
- 第 104 行: `mem_val` - 内存值
- 第 105 行: `page_type` - 页类型
- 第 106 行: `phy_memtype` - 物理内存类型

**第 109-113 行**: `DMemType` 枚举
- `DEVMM_MEM_NORMAL = 0` - 普通内存
- `DEVMM_MEM_RDONLY` - 只读内存

**第 117-120 行**: `DComHeapOps` 结构体 - 堆操作函数指针
- 第 118 行: `heap_alloc` - 分配函数
- 第 119 行: `heap_free` - 释放函数

**第 122-124 行**: `DVirtListHead` 结构体 - 双向链表头
- 第 123 行: `next` - 下一个节点
- 第 123 行: `prev` - 前一个节点

**第 128-131 行**: `ListNode` 结构体 - 链表节点

**第 133-138 行**: `DevNodeData` 结构体 - 节点数据
- 第 134 行: `va` - 虚拟地址
- 第 135 行: `size` - 大小
- 第 136 行: `total` - 总大小
- 第 137 行: `flag` - 标志

**第 140-144 行**: `RbtreeNode` 结构体 - 红黑树节点
- 第 141 行: `rbtree_parent_color` - 父节点颜色（编码）
- 第 142 行: `rbtree_right` - 右子节点
- 第 143 行: `rbtree_left` - 左子节点

**第 146-149 行**: `RbtreeRoot` 结构体 - 红黑树根
- 第 147 行: `RbtreeNode` - 根节点
- 第 148 行: `rbtree_len` - 树长度

**第 151-154 行**: `RbNode` 结构体 - 带键的红黑树节点
- 第 152 行: `RbtreeNode` - 嵌入的红黑树节点
- 第 153 行: `key` - 键值

**第 156-160 行**: `MultiRbNode` 结构体 - 多红黑树节点
- 同时在多个红黑树中（按地址、按大小）
- 第 157 行: `multi_rbtree_node` - 红黑树节点
- 第 158 行: `list` - 链表节点
- 第 159 行: `is_list_first` - 是否是链表首节点

**第 162-167 行**: `DevRbtreeNode` 结构体 - 设备红黑树节点
- 第 163 行: `va_node` - 按地址索引
- 第 164 行: `size_node` - 按大小索引
- 第 165 行: `cache_node` - 缓存索引
- 第 166 行: `data` - 节点数据

**第 169-173 行**: `DCacheList` 结构体 - 缓存列表
- 第 170 行: `cache` - 缓存节点
- 第 171 行: `list` - 链表
- 第 172 行: `is_new` - 是否新建

**第 175-182 行**: `DevHeapRbtree` 结构体 - 堆红黑树
- 第 176 行: `alloced_tree` - 已分配树
- 第 177 行: `idle_size_tree` - 空闲大小树
- 第 178 行: `idle_va_tree` - 空闲地址树
- 第 179 行: `idle_mapped_cache_tree` - 空闲映射缓存树数组
- 第 180 行: `head` - 缓存头
- 第 181 行: `devmm_cache_numsize` - 缓存数量大小

**第 184-188 行**: `DevHeapList` 结构体 - 堆列表
- 第 185 行: `heap_cnt` - 堆计数
- 第 186 行: `list_lock` - 读写锁
- 第 187 行: `heap_list` - 堆链表头

**第 190-233 行**: `DevVirtComHeap` 结构体 - 公共虚拟堆
- **初始化和类型**（第 191-197 行）:
  - `inited` - 初始化标志
  - `heap_type` - 堆类型
  - `heap_sub_type` - 堆子类型
  - `heap_list_type` - 堆列表类型
  - `heap_mem_type` - 堆内存类型
  - `heap_idx` - 堆索引
  - `is_base_heap` - 是否基础堆

- **缓存管理**（第 199-209 行）:
  - `cur_cache_mem` - 当前缓存内存
  - `cache_mem_thres` - 缓存阈值
  - `cur_alloc_cache_mem` - 当前分配缓存内存
  - `peak_alloc_cache_mem` - 峰值分配缓存内存
  - `peak_alloc_cache_time` - 峰值时间
  - `need_cache_thres` - 需要缓存的阈值
  - `is_limited` - 是否资源受限
  - `is_cache` - 是否启用缓存

- **地址范围**（第 210-211 行）:
  - `start` - 起始地址
  - `end` - 结束地址

- **大堆属性**（第 213-215 行）:
  - `module_id` - 模块 ID
  - `side` - 侧
  - `devid` - 设备 ID

- **映射和大小**（第 216-221 行）:
  - `mapped_size` - 映射大小
  - `chunk_size` - 块大小
  - `kernel_page_size` - 内核页大小
  - `map_size` - 映射大小
  - `heap_size` - 堆大小

- **操作和锁**（第 223-225 行）:
  - `ops` - 操作函数指针
  - `tree_lock` - 树锁
  - `heap_rw_lock` - 读写锁

- **统计**（第 226-229 行）:
  - `sys_mem_alloced` - 系统内存已分配
  - `sys_mem_freed` - 系统内存已释放
  - `sys_mem_alloced_num` - 分配次数
  - `sys_mem_freed_num` - 释放次数

- **关联**（第 231-232 行）:
  - `list` - 链表节点
  - `rbtree_queue` - 红黑树队列

**第 235-238 行**: `DHeapQueue` 结构体 - 堆队列
- 第 236 行: `base_heap` - 基础堆（管理 32TB，范围 1GB）
- 第 237 行: `heaps` - 堆指针数组

**第 240-270 行**: `DevVirtHeapMgmt` 结构体 - V1 虚拟堆管理
- **基本信息**（第 241-247 行）:
  - `inited` - 初始化标志
  - `pid` - 进程 ID
  - `max_conti_size` - 最大连续大小
  - `start/end` - SVM 地址范围

- **DVPP 区域**（第 249-251 行）:
  - `dvpp_start/dvpp_end` - DVPP 地址范围
  - `dvpp_mem_size` - 各设备 DVPP 内存大小

- **只读区域**（第 253-254 行）:
  - `read_only_start/read_only_end` - 只读地址范围

- **页大小**（第 256-258 行）:
  - `svm_page_size` - SVM 页大小
  - `local_page_size` - 本地页大小
  - `huge_page_size` - 大页大小

- **能力支持**（第 259-265 行）:
  - `support_bar_mem` - 支持 BAR 内存
  - `support_dev_read_only` - 支持设备只读
  - `support_dev_mem_map_host` - 支持设备内存映射到 Host
  - `support_bar_huge_mem` - 支持 BAR 大页内存
  - `host_support_pin_user_pages_interface` - Host 支持 pin 用户页接口
  - `support_host_rw_dev_ro` - 支持 Host 读写设备只读内存
  - `double_pgtable_offset` - 双页表偏移

- **堆管理**（第 267-269 行）:
  - `heap_queue` - 堆队列
  - `huge_list` - 大页堆列表三维数组
  - `normal_list` - 普通堆列表三维数组

**第 272-306 行**: `DevVirtHeapMgmtV2` 结构体 - V2 虚拟堆管理
- 新增字段（第 299-301 行）:
  - `support_host_pin_pre_register` - 支持 Host 预注册
  - `support_host_mem_pool` - 支持 Host 内存池
  - `is_dev_inited` - 设备初始化状态数组

---

## 四、devmm_ioctl.h 和 devmm_ioctl.cpp 逐行解读

### 文件信息
- 文件路径: `src/hybm/csrc/driver/userspace/devmm_ioctl.h`
- 代码行数: 72 行
- 主要功能: IOCTL 命令定义

### devmm_ioctl.h 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#ifndef MEM_FABRIC_HYBRID_DEVMM_IOCTL_H
#define MEM_FABRIC_HYBRID_DEVMM_IOCTL_H

#include <cstdint>

constexpr auto DEVMM_MAX_NAME_SIZE = 65U;

struct DevmmCommandHead {
    uint32_t logicDevId;
    uint32_t devId;
    uint32_t vFid;
};

struct DevmmCommandOpenParam {
    uint64_t vptr;
    char name[DEVMM_MAX_NAME_SIZE];
};

struct DevmmMemTranslateParam {
    uint64_t vptr;
    uint64_t pptr;
    uint32_t addrInDevice;
};

struct DevmmMemAdvisePara {
    uint64_t ptr;
    size_t count;
    uint32_t advise;
};

struct DevmmMemQuerySizePara {
    char name[DEVMM_MAX_NAME_SIZE];
    int32_t isHuge;
    size_t len;
};

struct DevmmMemAllocPara {
    uint64_t p;
    size_t size;
};

struct DevmmFreePagesPara {
    uint64_t va;
};

struct DevmmCommandMessage {
    DevmmCommandHead head;
    union {
        DevmmCommandOpenParam openParam;
        DevmmMemTranslateParam translateParam;
        DevmmMemAdvisePara prefetchParam;
        DevmmMemQuerySizePara queryParam;
        DevmmMemAllocPara allocSvmPara;
        DevmmMemAdvisePara advisePara;
        DevmmFreePagesPara freePagesPara;
    } data;
};

#endif // MEM_FABRIC_HYBRID_DEVMM_IOCTL_H
```

### 逐行解读

**第 18 行**: `DEVMM_MAX_NAME_SIZE = 65` - 最大名称长度

**第 20-24 行**: `DevmmCommandHead` 结构体 - 命令头
- 第 21 行: `logicDevId` - 逻辑设备 ID
- 第 22 行: `devId` - 物理设备 ID
- 第 23 行: `vFid` - 虚拟函数 ID

**第 26-29 行**: `DevmmCommandOpenParam` 结构体 - 打开参数
- 第 27 行: `vptr` - 虚拟指针
- 第 28 行: `name` - 共享内存名称

**第 31-35 行**: `DevmmMemTranslateParam` 结构体 - 地址转换参数
- 第 32 行: `vptr` - 虚拟地址
- 第 33 行: `pptr` - 物理地址
- 第 34 行: `addrInDevice` - 设备内地址

**第 37-41 行**: `DevmmMemAdvisePara` 结构体 - 内存建议参数
- 第 38 行: `ptr` - 地址
- 第 39 行: `count` - 大小
- 第 40 行: `advise` - 建议标志

**第 43-47 行**: `DevmmMemQuerySizePara` 结构体 - 查询大小参数
- 第 44 行: `name` - 共享内存名称
- 第 45 行: `isHuge` - 是否大页
- 第 46 行: `len` - 大小

**第 49-52 行**: `DevmmMemAllocPara` 结构体 - 分配参数
- 第 50 行: `p` - 指针
- 第 51 行: `size` - 大小

**第 54-56 行**: `DevmmFreePagesPara` 结构体 - 释放页参数
- 第 55 行: `va` - 虚拟地址

**第 58-69 行**: `DevmmCommandMessage` 结构体 - 命令消息
- 第 59 行: `head` - 命令头
- 第 60-68 行: `data` 联合体 - 不同命令的参数
  - `openParam` - 打开参数
  - `translateParam` - 转换参数
  - `prefetchParam` - 预取参数
  - `queryParam` - 查询参数
  - `allocSvmPara` - SVM 分配参数
  - `advisePara` - 建议参数
  - `freePagesPara` - 释放参数

### devmm_ioctl.cpp 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <algorithm>
#include <cerrno>
#include <cstring>

#include "hybm_logger.h"
#include "hybm_cmd.h"
#include "hybm_functions.h"
#include "devmm_ioctl.h"

namespace ock {
namespace mf {
namespace drv {

namespace {
const char DEVMM_SVM_MAGIC = 'M';
#define DEVMM_SVM_IPC_MEM_OPEN  _IOW(DEVMM_SVM_MAGIC, 21, DevmmCommandMessage)
#define DEVMM_SVM_PREFETCH      _IOW(DEVMM_SVM_MAGIC, 14, DevmmMemAdvisePara)
#define DEVMM_SVM_IPC_MEM_QUERY _IOWR(DEVMM_SVM_MAGIC, 29, DevmmMemQuerySizePara)
#define DEVMM_SVM_ALLOC         _IOW(DEVMM_SVM_MAGIC, 3, DevmmCommandMessage)
#define DEVMM_SVM_ADVISE        _IOW(DEVMM_SVM_MAGIC, 13, DevmmCommandMessage)
#define DEVMM_SVM_FREE_PAGES    _IOW(DEVMM_SVM_MAGIC, 4, DevmmCommandMessage)
#define DEVMM_SVM_IPC_MEM_CLOSE _IOW(DEVMM_SVM_MAGIC, 22, DevmmCommandMessage)

int gDeviceId = -1;
int gDeviceFd = -1;
} // namespace

void HybmInitialize(int deviceId, int fd) noexcept
{
    gDeviceId = deviceId;
    gDeviceFd = fd;
}

int HybmMapShareMemory(const char *name, void *expectAddr, uint64_t size, uint64_t flags) noexcept
{
    if (gDeviceId == -1 || gDeviceFd == -1) {
        BM_LOG_ERROR("deviceId or fd not set! id:" << gDeviceId << " fd:" << gDeviceFd);
        return -1;
    }

    DevmmCommandMessage arg{};
    arg.head.devId = static_cast<uint32_t>(gDeviceId);
    if (strlen(name) > DEVMM_MAX_NAME_SIZE) {
        BM_LOG_ERROR("name is too long:" << strlen(name) << ", max is " << DEVMM_MAX_NAME_SIZE);
        return -1;
    }
    std::copy_n(name, strlen(name), arg.data.queryParam.name);

    auto ret = ioctl(gDeviceFd, DEVMM_SVM_IPC_MEM_QUERY, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("query for name: (" << name << ") failed = " << ret);
        return -1;
    }

    BM_LOG_INFO("shm(" << name << ") size=" << arg.data.queryParam.len << ", isHuge=" << arg.data.queryParam.isHuge);

    std::fill_n(reinterpret_cast<char *>(&arg.data), sizeof(arg.data), 0);
    arg.data.openParam.vptr = reinterpret_cast<uint64_t>(expectAddr);
    BM_LOG_DEBUG("before map share memory: " << name);

    std::copy_n(name, strlen(name), arg.data.openParam.name);
    ret = ioctl(gDeviceFd, DEVMM_SVM_IPC_MEM_OPEN, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("open share memory failed:" << ret << " : " << errno << " : " << SafeStrError(errno)
                                                 << ", name = " << arg.data.openParam.name);
        return -1;
    }

    std::fill_n(reinterpret_cast<char *>(&arg.data), sizeof(arg.data), 0);
    arg.data.prefetchParam.ptr = reinterpret_cast<uint64_t>(expectAddr);
    arg.data.prefetchParam.count = size;
    ret = ioctl(gDeviceFd, DEVMM_SVM_PREFETCH, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("prefetch share memory failed:" << ret << " : " << errno << " : " << SafeStrError(errno)
                                                     << ", name = " << arg.data.openParam.name);
        return -1;
    }

    return 0;
}

int HybmUnmapShareMemory(void *expectAddr, uint64_t flags) noexcept
{
    DevmmCommandMessage arg{};
    int32_t ret;

    arg.data.freePagesPara.va = reinterpret_cast<uint64_t>(expectAddr);
    ret = ioctl(gDeviceFd, DEVMM_SVM_IPC_MEM_CLOSE, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("gva close error.\n");
        return ret;
    }
    return 0;
}

int HybmIoctlAllocAnddAdvice(uint64_t ptr, size_t size, uint32_t devid, uint32_t advise) noexcept
{
    DevmmCommandMessage arg{};
    int32_t ret;

    arg.data.allocSvmPara.p = ptr;
    arg.data.allocSvmPara.size = size;

    ret = ioctl(gDeviceFd, DEVMM_SVM_ALLOC, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("svm alloc failed:" << ret << " : " << errno << " : " << SafeStrError(errno));
        return -1;
    }

    arg.head.devId = devid;
    arg.data.advisePara.ptr = ptr;
    arg.data.advisePara.count = size;
    arg.data.advisePara.advise = advise;

    ret = ioctl(gDeviceFd, DEVMM_SVM_ADVISE, &arg);
    if (ret != 0) {
        BM_LOG_ERROR("svm advise failed:" << ret << " : " << errno << " : " << SafeStrError(errno));

        arg.data.freePagesPara.va = ptr;
        (void)ioctl(gDeviceFd, DEVMM_SVM_FREE_PAGES, &arg);
        return -1;
    }

    return 0;
}

} // namespace drv
} // namespace mf
} // namespace ock
```

### 逐行解读

**第 12-17 行**: 头文件引用
- 第 12 行: `unistd.h` - POSIX 操作系统 API
- 第 13 行: `fcntl.h` - 文件控制
- 第 14 行: `sys/ioctl.h` - IOCTL 系统调用
- 第 15 行: `algorithm` - 算法
- 第 16 行: `cerrno` - 错误码
- 第 17 行: `cstring` - 字符串操作

**第 28-35 行**: IOCTL 命令定义
- 第 29 行: 魔数 `'M'`
- 第 30 行: `DEVMM_SVM_IPC_MEM_OPEN` - 打开共享内存
- 第 31 行: `DEVMM_SVM_PREFETCH` - 预取
- 第 32 行: `DEVMM_SVM_IPC_MEM_QUERY` - 查询共享内存
- 第 33 行: `DEVMM_SVM_ALLOC` - 分配 SVM 内存
- 第 34 行: `DEVMM_SVM_ADVISE` - 设置内存建议
- 第 35 行: `DEVMM_SVM_FREE_PAGES` - 释放页
- 第 36 行: `DEVMM_SVM_IPC_MEM_CLOSE` - 关闭共享内存

**第 38-39 行**: 全局变量
- `gDeviceId` - 设备 ID
- `gDeviceFd` - 设备文件描述符

**HybmInitialize（第 42-46 行）**:
- **功能**: 初始化驱动层，保存设备 ID 和文件描述符
- 第 44 行: 保存设备 ID
- 第 45 行: 保存文件描述符

**HybmMapShareMemory（第 48-94 行）**:
- **功能**: 映射共享内存到指定地址
- 第 50-53 行: 检查设备是否已初始化
- 第 55-60 行: 准备查询参数
- 第 62-67 行: 调用 IOCTL 查询共享内存信息
- 第 69 行: 记录日志
- 第 71-73 行: 准备打开参数
- 第 75-76 行: 调用 IOCTL 打开共享内存
- 第 77-81 行: 错误处理
- 第 83-85 行: 准备预取参数
- 第 86-91 行: 调用 IOCTL 预取内存
- 第 93 行: 返回成功

**HybmUnmapShareMemory（第 96-108 行）**:
- **功能**: 取消映射共享内存
- 第 101-102 行: 设置虚拟地址
- 第 103 行: 调用 IOCTL 关闭共享内存
- 第 104-106 行: 错误处理

**HybmIoctlAllocAnddAdvice（第 110-139 行）**:
- **功能**: 分配内存并设置建议
- 第 113-116 行: 准备分配参数
- 第 118-122 行: 调用 IOCTL 分配内存
- 第 124-127 行: 准备建议参数
- 第 129-136 行: 调用 IOCTL 设置建议，失败时释放内存
- 第 138 行: 返回成功

---

## 五、devmm_svm_gva.h 和 devmm_svm_gva.cpp 逐行解读

### 文件信息
- 文件路径: `src/hybm/csrc/driver/userspace/devmm_svm_gva.cpp`
- 代码行数: 696 行
- 主要功能: SVM GVA 实现

### devmm_svm_gva.h 完整代码

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ... (许可证同上)
*/

#ifndef MEM_FABRIC_HYBRID_DEVMM_SVM_GVA_H
#define MEM_FABRIC_HYBRID_DEVMM_SVM_GVA_H

#include <cstddef>
#include <cstdint>

namespace ock {
namespace mf {
namespace drv {

const uint64_t GVA_GIANT_FLAG = (1ULL << 0);

int32_t HalGvaReserveMemory(uint64_t *address, size_t size, int32_t deviceId, uint64_t flags);

int32_t HalGvaUnreserveMemory(uint64_t address);

int32_t HalGvaAlloc(uint64_t address, size_t size, uint64_t flags);

int32_t HalGvaFree(uint64_t address, size_t size);

int32_t HalGvaOpen(uint64_t address, const char *name, size_t size, uint64_t flags);

int32_t HalGvaClose(uint64_t address, uint64_t flags);

} // namespace drv
} // namespace mf
} // namespace ock

#endif // MEM_FABRIC_HYBRID_DEVMM_SVM_GVA_H
```

### 逐行解读

**第 23 行**: `GVA_GIANT_FLAG` - GVA 巨页标志

**第 25-38 行**: GVA 操作函数声明
- `HalGvaReserveMemory` - 预留 GVA 内存
- `HalGvaUnreserveMemory` - 取消预留
- `HalGvaAlloc` - 分配 GVA 内存
- `HalGvaFree` - 释放 GVA 内存
- `HalGvaOpen` - 打开共享 GVA
- `HalGvaClose` - 关闭共享 GVA

### devmm_svm_gva.cpp 关键代码解读

#### GvaHeap 结构体（第 28-39 行）

```cpp
struct GvaHeap {
    uint32_t inited = false;
    int32_t deviceId = -1;

    uint64_t start = 0;
    uint64_t end = 0;

    pthread_mutex_t treeLock;
    std::map<uint64_t, uint64_t> tree;
    std::map<uint64_t, uint64_t> reserved;
};
GvaHeap g_gvaHeapMgr;
```

**解读**: GVA 堆管理器
- `inited` - 初始化标志
- `deviceId` - 设备 ID
- `start/end` - 地址范围
- `treeLock` - 线程锁
- `tree` - 已分配的地址范围映射（起始地址 -> 结束地址）
- `reserved` - 预留的地址范围映射

#### InitGvaHeapMgmt（第 58-84 行）

```cpp
static int32_t InitGvaHeapMgmt(uint64_t st, uint64_t ed, int32_t deviceId)
{
    if (g_gvaHeapMgr.inited) {
        if (ed != g_gvaHeapMgr.start) {
            BM_LOG_ERROR("init gva mgr error. input_ed:0x" << std::hex << ed << " pre_st:0x" << g_gvaHeapMgr.start);
            return -1;
        }
        if (deviceId != g_gvaHeapMgr.deviceId) {
            BM_LOG_ERROR("init gva mgr error. input_device:" << deviceId << " pre_device:" << g_gvaHeapMgr.deviceId);
            return -1;
        }
        g_gvaHeapMgr.start = st;
        g_gvaHeapMgr.reserved[st] = ed;
        return 0;
    }

    g_gvaHeapMgr.tree.clear();
    g_gvaHeapMgr.reserved.clear();
    g_gvaHeapMgr.start = st;
    g_gvaHeapMgr.end = ed;
    g_gvaHeapMgr.deviceId = deviceId;
    g_gvaHeapMgr.reserved[st] = ed;
    (void)pthread_mutex_init(&g_gvaHeapMgr.treeLock, nullptr);
    g_gvaHeapMgr.inited = true;

    return 0;
}
```

**解读**: 初始化 GVA 堆管理器
- 第 60-71 行: 如果已初始化，检查连续性并扩展范围
- 第 73-81 行: 首次初始化，清空映射并设置初始值

#### TryUpdateGvaHeap（第 123-147 行）

```cpp
static bool TryUpdateGvaHeap(uint64_t va, size_t len)
{
    if (!g_gvaHeapMgr.inited) {
        BM_LOG_ERROR("update gva heap failed, gva heap not init.");
        return false;
    }

    if (va < g_gvaHeapMgr.start || va + len > g_gvaHeapMgr.end) {
        BM_LOG_ERROR("update gva heap failed, out of range. (key=0x" << std::hex << va << " len=0x" << len << " st=0x"
                                                                     << g_gvaHeapMgr.start << " ed=0x"
                                                                     << g_gvaHeapMgr.end << ")");
        return false;
    }

    (void)pthread_mutex_lock(&g_gvaHeapMgr.treeLock);
    if (GvaHeapCheckInRange(va, len)) {
        (void)pthread_mutex_unlock(&g_gvaHeapMgr.treeLock);
        BM_LOG_ERROR("update gva heap failed, has some alloced memory in range.");
        return false;
    }

    g_gvaHeapMgr.tree[va] = va + len;
    (void)pthread_mutex_unlock(&g_gvaHeapMgr.treeLock);
    return true;
}
```

**解读**: 尝试更新 GVA 堆
- 检查是否已初始化
- 检查地址是否在范围内
- 检查是否与已分配区域重叠
- 添加到已分配映射

#### HalGvaReserveMemory（第 535-586 行）

```cpp
int32_t HalGvaReserveMemory(uint64_t *address, size_t size, int32_t deviceId, uint64_t flags)
{
#ifdef UT_ENABLED
    *address = SVM_END_ADDR - GB;
    return BM_OK;
#endif
    uint32_t advise = 0;
    struct DevVirtHeapType heap_type;
    size_t allocSize = ALIGN_UP(size, DEVMM_HEAP_SIZE);
    if (allocSize == 0 || allocSize > (DEVMM_SVM_MEM_SIZE >> 1) || address == nullptr) { // init size <= 4T
        BM_LOG_ERROR("gva init failed, (size must > 0 && <= 4T) or address is null. (flag=" << flags << " size=0x"
                                                                                            << std::hex << size << ")");
        return -1;
    }

    advise |= DV_ADVISE_HUGEPAGE;
    advise |= (flags & GVA_GIANT_FLAG) ? (DV_ADVISE_GIANTPAGE | DV_ADVISE_DDR) : (DV_ADVISE_HBM);
    SetModuleId2Advise(HCCL_HAL_MODULE_ID, &advise);
    FillSvmHeapType(advise, &heap_type);

    void *mgmt = nullptr;
    mgmt = DlHalApi::HalVirtGetHeapMgmt();
    if (mgmt == nullptr) {
        BM_LOG_ERROR("HalGvaInitMemory get heap mgmt is nullptr.");
        return -1;
    }

    uint64_t va = (DEVMM_SVM_MEM_START + DEVMM_SVM_MEM_SIZE - DEVMM_HEAP_SIZE) - allocSize;
    if (g_gvaHeapMgr.inited) {
        if (allocSize > g_gvaHeapMgr.start) {
            BM_LOG_ERROR("invalid allocSize or g_gvaHeapMgr.start");
            return -1;
        }
        va = g_gvaHeapMgr.start - allocSize;
    }

    uint64_t retVa = VirtAllocGvaMem(mgmt, va, allocSize, &heap_type, advise);
    if (retVa != va) {
        BM_LOG_ERROR("HalGvaInitMemory alloc mem failed. (flag=" << flags << " size=0x" << std::hex << size << ")");
        return -1;
    }

    int32_t ret = InitGvaHeapMgmt(va, va + allocSize, deviceId);
    if (ret != 0) {
        BM_LOG_ERROR("HalGvaInitMemory init gva heap failed.");
        FreeManagedNomal(va);
        return -1;
    }

    *address = va;
    return BM_OK;
}
```

**解读**: 预留 GVA 内存
- 第 543-548 行: 大小检查（最大 4TB）
- 第 550-553 行: 设置分配建议（HBM/DDR，大页）
- 第 562-569 行: 计算分配地址（从 SVM 空间末尾向前）
- 第 571-575 行: 调用虚拟分配函数
- 第 577-582 行: 初始化堆管理器
- 第 584 行: 返回基地址

#### HalGvaAlloc（第 597-624 行）

```cpp
int32_t HalGvaAlloc(uint64_t address, size_t size, uint64_t flags)
{
#ifdef UT_ENABLED
    return BM_OK;
#endif
    uint64_t va = address;
    if ((va % DEVMM_MAP_ALIGN_SIZE != 0) || (size % DEVMM_MAP_ALIGN_SIZE != 0)) {
        BM_LOG_ERROR("open gva va check failed, size must the align of 2M. (size=0x" << std::hex << size << ")");
        return -1;
    }

    if (!TryUpdateGvaHeap(va, size)) {
        return -1;
    }

    uint32_t advise = DV_ADVISE_HUGEPAGE | DV_ADVISE_POPULATE | DV_ADVISE_LOCK_DEV;
    advise |= (flags & GVA_GIANT_FLAG) ? (DV_ADVISE_GIANTPAGE | DV_ADVISE_DDR) : (DV_ADVISE_HBM);
    SetModuleId2Advise(APP_MODULE_ID, &advise);
    int32_t ret = HybmIoctlAllocAnddAdvice(va, size, g_gvaHeapMgr.deviceId, advise);
    if (ret != 0) {
        BM_LOG_ERROR("Alloc gva local mem error. (ret=" << ret << " size=0x" << std::hex << size << "advise=0x"
                                                        << advise << ")");
        (void)RemoveInGvaHeap(va);
        return -1;
    }

    return 0;
}
```

**解读**: 分配 GVA 内存
- 第 603-606 行: 检查 2MB 对齐
- 第 608-610 行: 更新堆管理器
- 第 612 行: 设置分配建议（大页、预填充、锁定）
- 第 615 行: 调用 IOCTL 分配

#### HalGvaOpen（第 663-678 行）

```cpp
int32_t HalGvaOpen(uint64_t address, const char *name, size_t size, uint64_t flags)
{
#ifdef UT_ENABLED
    return BM_OK;
#endif
    if (OpenGvaMalloc(address, size, flags) != 0) {
        BM_LOG_ERROR("HalGvaOpen malloc gva error. (size=0x" << std::hex << size << ")");
        return -1;
    }

    auto ret = HybmMapShareMemory(name, reinterpret_cast<void *>(address), size, flags);
    if (ret != 0) {
        HalGvaFree(address, 0);
    }
    return ret;
}
```

**解读**: 打开共享 GVA
- 第 668 行: 先分配 GVA 内存
- 第 673 行: 映射共享内存
- 第 674-676 行: 失败时释放内存

---

## 总结

### Driver 模块核心功能

1. **GVA 管理**:
   - 预留 SVM 地址空间末尾区域用于元数据管理
   - 从高地址向低地址分配（SVM_END_ADDR 向前）
   - 支持 2MB 对齐的内存分配

2. **堆管理**:
   - 使用 `std::map` 管理已分配的地址范围
   - 线程安全设计（pthread_mutex）
   - 支持地址范围检查和重叠检测

3. **IOCTL 通信**:
   - 通过 IOCTL 与内核驱动通信
   - 支持共享内存查询、打开、关闭
   - 支持内存分配和设置建议

4. **内存类型**:
   - HBM: 高带宽内存
   - DDR: 双倍速率同步动态随机存储器
   - 支持大页（2MB）和巨页

### 地址空间布局

```
SVM 地址空间:
+------------------+ 0x100000000000 (256GB)
|                  |
|     可用区域      |
|                  |
+------------------+
|   元数据区域      | <- SVM_END_ADDR - 1GB
+------------------+
|   保留区域        |
+------------------+ SVM_END_ADDR (8TB + 256GB)
```

### 关键常量

| 常量 | 值 | 说明 |
|-----|---|------|
| DEVMM_MAP_ALIGN_SIZE | 2MB | 映射对齐大小 |
| DEVMM_HEAP_SIZE | 1GB | 堆大小 |
| DEVMM_SVM_MEM_SIZE | 8TB | SVM 地址空间大小 |
| DEVMM_SVM_MEM_START | 256GB | SVM 起始地址 |
