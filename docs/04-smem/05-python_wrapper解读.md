# SMEM Python_Wrapper 模块逐行解读

## 模块概述

Python_Wrapper 模块提供 Python 绑定，使 Python 应用能够使用 MemFabric_Hybrid 的功能。该模块使用 pybind11 实现 C++ 到 Python 的接口绑定。

## 目录结构

```
python_wrapper/
├── memfabric_hybrid/
│   └── pymf_hybrid.cpp                    # 主模块 Python 绑定
├── mk_transfer_adapter/
│   ├── include/
│   │   ├── pytransfer.h                   # 传输适配器接口
│   │   ├── adapter_logger.h              # 适配器日志
│   │   └── transfer_util.h                 # 传输工具
│   └── csrc/
│       ├── pytransfer.cpp                   # 传输适配器实现
│       └── transfer_util.cpp               # 传输工具实现
└── python/
    ├── memfabric_hybrid/
    │   ├── __init__.py
    │   └── launch_ascend_mf_store.py     # 存储服务启动脚本
    ├── mk_transfer_adapter/
    │   ├── __init__.py
    │   └── setup.py                           # 安装脚本
```

---

## 1. pymf_hybrid.cpp - 主模块 Python 绑定

### 文件信息
- 文件路径: `src/smem/csrc/python_wrapper/memfabric_hybrid/pymf_hybrid.cpp`
- 代码行数: 200+ 行
- 主要功能: 为 ShareMemory 和 BigMemory 提供 Python 类封装

### 头文件引用和初始化 (行 1-30)

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * MemFabric_Hybrid is licensed under Mulan PSL v2.
 * ...
*/
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"

#include <iostream>
#include <Python.h>
#include <pybind11/pybind11.h>
#include <pybind11/pytypes.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <mutex>
#include <new>
#include "smem.h"
#include "smem_shm.h"
#include "smem_bm.h"
#include "smem_version.h"

namespace py = pybind11;
```

**逐行解读**:
- 第 12-13 行: 抑告 GCC 忽略 pybind11 的字段初始化警告
- 第 15-16 行: `<iostream>` - 输入输出流
- 第 16 行: `<Python.h>` - Python C API
- 第 17-20 行: pybind11 头文件
  - `pybind11/pybind11.h` - 主绑定头文件
  - `pybind11/pytypes.h` - Python 类型转换
  - `pybind11/stl.h` - STL 容器支持
- 第 21 行: `<cstdint>` - 整数类型
- 第 22 行: `<mutex>` - 互斥锁
- 第 23 行: `<new>` - new/delete 操作符
- 第 24-27 行: Smem 模块头文件
- 第 28 行: `smem_version.h` - 版本信息

### ShareMemory 类 (行 31-110)

```cpp
class ShareMemory {
public:
    explicit ShareMemory(smem_shm_t hd, void *gva) noexcept : handle_{hd}, gvaAddress_{gva} {}
    virtual ~ShareMemory() noexcept
    {
        smem_shm_destroy(handle_, 0);
    }

    int32_t SetExternContext(const void *context, uint32_t size)
    {
        return smem_shm_set_extra_context(handle_, context, size);
    }

    uint32_t LocalRank() noexcept
    {
        return smem_shm_get_global_rank(handle_);
    }

    uint32_t RankSize() noexcept
    {
        return smem_shm_get_global_rank_size(handle_);
    }

    int32_t Barrier()
    {
        return smem_shm_control_barrier(handle_);
    }

    int32_t Destroy(uint32_t flags)
    {
        return smem_shm_destroy(handle_, flags);
    }

    int32_t AllGather(const char *sendBuf, uint32_t sendSize, char *recvBuf, uint32_t recvSize)
    {
        return smem_shm_control_allgather(handle_, sendBuf, sendSize, recvBuf, recvSize);
    }

    void *Address() const noexcept
    {
        return gvaAddress_;
    }
```

**逐行解读**:
- 第 32-33 行: 构造函数，接收 SHM 句柄和 GVA 地址
- 第 34-37 行: 析构函数，自动销毁 SHM 句柄
- 第 39-42 行: 设置外部上下文
- 第 44-47 行: 获取本地 Rank ID
- 第 49-52 行: 获取 Rank 总数
- 第 54-57 行: Barrier 同步
- 第 59-62 行: 销毁句柄
- 第 64-67 行: AllGather 集合通信
- 第 69-72 行: 获取 GVA 地址

```cpp
    static int Initialize(const std::string &storeURL, uint32_t worldSize, uint32_t rankId, uint16_t deviceId,
                          smem_shm_config_t &config) noexcept
    {
        return smem_shm_init(storeURL.c_str(), worldSize, rankId, deviceId, &config);
    }

    static void UnInitialize(uint32_t flags) noexcept
    {
        smem_shm_uninit(flags);
    }

    static ShareMemory *Create(uint32_t id, uint32_t rankSize, uint32_t rankId, uint64_t symmetricSize,
                               smem_shm_data_op_type dataOpType, uint32_t flags)
    {
        void *gva;
        auto handle = smem_shm_create(id, rankSize, rankId, symmetricSize, dataOpType, flags, &gva);
        if (handle == nullptr) {
            throw std::runtime_error("create shm failed!");
        }

        return new (std::nothrow) ShareMemory(handle, gva);
    }

    uint32_t QuerySupportDataOp() noexcept
    {
        return smem_shm_query_support_data_operation();
    }

    uint32_t TopologyCanReach(uint32_t remoteRank, uint32_t *reachInfo)
    {
        return smem_shm_topology_can_reach(handle_, remoteRank, reachInfo);
    }

private:
    smem_shm_t handle_;
    void *gvaAddress_;
};
```

**逐行解读**:
- 第 74-78 行: `Initialize` - 初始化 SHM
- 第 80-83 行: `UnInitialize` - 反初始化
- 第 85-95 行: `Create` - 创建 SHM 实例
  - 失败时抛出 `runtime_error` 异常
- 第 97-100 行: `QuerySupportDataOp` - 查询支持的数据操作
- 第 102-105 行: `TopologyCanReach` - 查询拓扑可达性
- 第 107-109 行: 私有成员

### BigMemory 类 (行 112-200+)

```cpp
class BigMemory {
public:
    explicit BigMemory(smem_bm_t hd) noexcept : handle_{hd} {}
    virtual ~BigMemory() noexcept
    {
        smem_bm_destroy(handle_);
    }

    int32_t Join(uint32_t flags)
    {
        return smem_bm_join(handle_, flags);
    }

    int32_t Leave(uint32_t flags)
    {
        return smem_bm_leave(handle_, flags);
    }

    uint64_t LocalMemSize(smem_bm_mem_type memType)
    {
        return smem_bm_get_local_mem_size_by_mem_type(handle_, memType);
    }

    void *GetPtrByRank(uint32_t rankId, smem_bm_mem_type memType)
    {
        auto ptr = smem_bm_ptr_by_mem_type(handle_, memType, rankId);
        if (ptr == nullptr) {
            return 0;
        }

        return (uint64_t)(ptrdiff_t)ptr;
    }

    void Destroy()
    {
        smem_bm_destroy(handle_);
        handle_ = nullptr;
    }

    int32_t CopyData(uint64_t src, uint64_t dest, uint64_t size, smem_bm_copy_type type, uint32_t flags)
    {
        smem_copy_params params = {(const void *)(ptrdiff_t)src, (void *)(ptrdiff_t)dest, size};
        return smem_bm_copy(handle_, &params, type, flags);
    }
```

**逐行解读**:
- 第 112-114 行: 构造函数，接收 BM 句柄
- 第 115-118 行: 析造函数，自动销毁句柄
- 第 120-123 行: `Join` - 加入 BM 全局内存
- 第 125-128 行: `Leave` - 离开 BM 全局内存
- 第 130-133 行: `LocalMemSize` - 获取本地内存大小
- 第 135-143 行: `GetPtrByRank` - 获取指定 Rank 的内存指针
- 第 145-149 行: `Destroy` - 销毁句柄
- 第 151-155 行: `CopyData` - 单次数据拷贝

```cpp
    int32_t CopyDataBatch(std::vector<uintptr_t> srcs, std::vector<uintptr_t> dsts, std::vector<size_t> sizes,
                          uint32_t count, smem_bm_copy_type type, uint32_t flags)
    {
        void **ptr = new void *[count + count];
        if (ptr == nullptr) {
            throw std::runtime_error(std::string("alloc mem failed."));
        }

        void **sources = ptr;
        void **destinations = ptr + count;
        for (uint64_t i = 0; i < count; ++i) {
            sources[i] = reinterpret_cast<void *>(srcs[i]);
            destinations[i] = reinterpret_cast<void *>(dsts[i]);
        }
        smem_batch_copy_params batch_params = {sources, destinations, sizes.data(), count};
        auto ret = smem_bm_copy_batch(handle_, &batch_params, type, flags);
        delete[] ptr;
        return ret;
    }
```

**逐行解读**:
- 第 157-159 行: 函数签名，批量拷贝
- 第 160-163 行: 分配指针数组（源和目标各 count 个）
- 第 164-166 行: 分配失败抛出异常
- 第 168-170 行: 设置源指针数组起始位置
- 第 171 行: 设置目标指针数组起始位置
- 第 172-174 行: 转换 uintptr_t 到 void*
- 第 175 行: 构造批量拷贝参数
- 第 176 行: 调用底层批量拷贝 API
- 第 177 行: 释放指针数组

### PYBIND11 模块定义

```cpp
PYBIND11_MODULE(pymf_hybrid, m) {
    m.doc() = "MemFabric Hybrid Python bindings";

    py::class_<ShareMemory>(m, "ShareMemory")
        .def(py::init<>(&ShareMemory::Create))
        .def("set_extern_context", &ShareMemory::SetExternContext)
        .def("local_rank", &ShareMemory::LocalRank)
        .def("rank_size", &ShareMemory::RankSize)
        .def("barrier", &ShareMemory::Barrier)
        .def("destroy", &ShareMemory::Destroy)
        .def("allgather", &ShareMemory::AllGather)
        .def_property("address", &ShareMemory::Address)
        .def_static("initialize", &ShareMemory::Initialize)
        .def_static("uninitialize", &ShareMemory::UnInitialize);

    py::class_<BigMemory>(m, "BigMemory")
        .def(py::init<>(&BigMemory::Create))
        .def("join", &BigMemory::Join)
        .def("leave", &BigMemory::Leave)
        .def("local_mem_size", &BigMemory::LocalMemSize)
        .def("get_ptr_by_rank", &BigMemory::GetPtrByRank)
        .def("destroy", &BigMemory::Destroy)
        .def("copy_data", &BigMemory::CopyData)
        .def("copy_data_batch", &BigMemory::CopyDataBatch)
        .def_static("initialize", &BigMemory::Initialize)
        .def_static("uninitialize", &BigMemory::UnInitialize)
        .def_static("get_rank_id", &BigMemory::GetRankId)
        .def("get_rank_id_by_gva", &BigMemory::GetRankIdByGva);

    m.def("get_version", []() {
        auto version = smem_get_version();
        return std::string(version);
    });
}
```

**逐行解读**:
- 模块名称: `pymf_hybrid`
- ShareMemory 类绑定:
  - `py::init<>` - 绑定静态 Create 方法作为构造函数
  - `set_extern_context` - 设置外部上下文
  - `local_rank` - 本地 Rank ID
  - `rank_size` - Rank 总数
  - `barrier` - Barrier 同步
  - `destroy` - 销毁
  - `allgather` - 集合通信
  - `address` - GVA 地址属性
  - `initialize` - 静态初始化方法
  - `uninitialize` - 静态反初始化方法
- BigMemory 类绑定:
  - `join`/`leave` - 加入/离开全局内存
  - `local_mem_size` - 本地内存大小
  - `get_ptr_by_rank` - 获取指定 Rank 的内存指针
  - `destroy` - 销毁
  - `copy_data` - 单次拷贝
  - `copy_data_batch` - 批量拷贝
  - `get_rank_id` - 静态方法获取 Rank ID
  - `get_rank_id_by_gva` - 通过 GVA 获取 Rank ID
- `get_version` - 获取版本号

---

## 2. pytransfer.cpp - 传输适配器

### 文件路径
- `src/smem/csrc/python_wrapper/mk_transfer_adapter/csrc/pytransfer.cpp`

### 主要功能

pytransfer 模块提供 Python 传输接口，封装了 smem_trans API，支持：
- 数据传输（发送/接收）
- 链接管理（连接/断开）
- 批量传输

### 关键接口

```python
class PyTransfer:
    def send(self, data: bytes, dest_rank: int) -> None
    def send_batch(self, data_list: List[bytes], dest_rank: int) -> None
    def recv(self, size: int, src_rank: int) -> bytes
    def connect(self, rank_id: int) -> None
    def disconnect(self, rank_id: int) -> None
```

---

## 总结

Python_Wrapper 模块提供了 Python 对 MemFabric_Hybrid 的完整访问：

### 1. Python 类映射

| C++ | Python | 说明 |
|-----|--------|------|
| ShareMemory | `memfabric_hybrid.ShareMemory` | 共享内存管理 |
| BigMemory | `memfabric_hybrid.BigMemory` | 大内存管理 |

### 2. ShareMemory API

| Python 方法 | C API | 功能 |
|-----------|--------|------|
| `initialize()` | `smem_shm_init` | 初始化 |
| `uninitialize()` | `smem_shm_uninit` | 反初始化 |
| `create()` | `smem_shm_create` | 创建实例 |
| `barrier()` | `smem_shm_control_barrier` | Barrier |
| `allgather()` | `smem_shm_control_allgather` | 集合通信 |
| `destroy()` | `smem_shm_destroy` | 销毁 |
| `address` | GVA 地址 | 只读属性 |

### 3. BigMemory API

| Python 方法 | C API | 功能 |
|-----------|--------|------|
| `initialize()` | `smem_bm_init` | 初始化 |
| `uninitialize()` | `smem_bm_uninit` | 反初始化 |
| `create()` | `smem_bm_create` | 创建实例 |
| `join()` | `smem_bm_join` | 加入全局内存 |
| `leave()` | `smem_bm_leave` | 离开全局内存 |
| `local_mem_size()` | `smem_bm_get_local_mem_size_by_mem_type` | 本地内存大小 |
| `get_ptr_by_rank()` | `smem_bm_ptr_by_mem_type` | 获取远程内存指针 |
| `copy_data()` | `smem_bm_copy` | 数据拷贝 |
| `copy_data_batch()` | `smem_bm_copy_batch` | 批量数据拷贝 |

### 4. 使用示例

```python
import memfabric_hybrid as mfh

# 初始化
mfh.ShareMemory.initialize("tcp://127.0.0.1:8888", 4, 0, 0)

# 创建共享内存
shm = mfh.ShareMemory.create(id=0, rankSize=4, rankId=0, symmetricSize=1024*1024*1024,
                             dataOpType=mfh.DATALINK_HCOM, flags=0)

# Barrier 同步
shm.barrier()

# 获取地址
addr = shm.address()

# 销毁
shm.destroy()

# 反初始化
mfh.ShareMemory.uninitialize(0)
```

### 5. 传输适配器

`mk_transfer_adapter` 子模块提供独立的 Python 传输接口：
- `pytransfer.cpp` - 传输适配器实现
- `transfer_util.cpp` - 传输工具函数
- 支持 Python 到 C++ 的数据传输
- 用于 PyTorch 等框架的集成
