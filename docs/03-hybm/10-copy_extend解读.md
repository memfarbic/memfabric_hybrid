# HYBM Copy_Extend 模块逐行解读

## 模块概述

Copy_Extend 模块是 HyBM 的 AI Core 内核扩展模块，使用昇腾 AI Core 实现 GM（Global Memory）到 GM 的数据拷贝。该模块通过 Ascend C 编程模型实现：

1. **GM 到 GM 拷贝** - 通过 UB（Unified Buffer）中转实现全局内存间拷贝
2. **批量拷贝** - 支持多段内存的批量拷贝
3. **多核并行** - 使用多个 AI Core 并行处理
4. **数据缓存一致性** - 通过 DCCI 指令保证缓存一致性

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| hybm_copy_kernel.cpp | 124 | AI Core 拷贝内核实现 |

---

## 1. hybm_copy_kernel.cpp - AI Core 拷贝内核

### 文件信息
- 文件路径: `src/hybm/csrc/copy_extend/hybm_copy_kernel.cpp`
- 代码行数: 124 行
- 主要功能: 使用 AI Core 实现 GM 到 GM 的数据拷贝

### 头文件引用和常量定义 (行 1-17)

```cpp
#include "acl/acl.h"
#include "kernel_operator.h"

#define HYBM_AICORE_KERNEL __attribute__((always_inline)) __aicore__ __inline__
const uint32_t COPY_BUF_SIZE = 64 * 1024; // 最大支持192KB
const uint32_t SINGLE_COPY_SLICE = 128;
```

**逐行解读**:
- 第 12 行: `acl/acl.h` - ACL API 头文件
- 第 13 行: `kernel_operator.h` - 内核操作符头文件
- 第 15 行: 宏定义 AI Core 内核属性
  - `always_inline`: 始终内联
  - `__aicore__`: AI Core 函数
  - `__inline__`: 内联函数
- 第 16 行: 拷贝缓冲区大小（64KB）
- 第 17 行: 单次拷贝切片大小（128 字节）

### copy_ub2gm() - UB 到 GM 拷贝 (行 19-29)

```cpp
HYBM_AICORE_KERNEL void copy_ub2gm(__gm__ uint8_t* dst, __ubuf__ uint8_t* src, uint32_t size)
{
    AscendC::LocalTensor<uint8_t> ubTensor;
    AscendC::GlobalTensor<uint8_t> gmTensor;
    AscendC::DataCopyExtParams dataCopyParams(1, size, 0, 0, 0);
    ubTensor.address_.logicPos = static_cast<uint8_t>(AscendC::TPosition::VECIN);
    ubTensor.address_.bufferAddr = reinterpret_cast<uint64_t>(src);
    gmTensor.SetGlobalBuffer(reinterpret_cast<__gm__ uint8_t*>(dst));

    AscendC::DataCopyPad(gmTensor, ubTensor, dataCopyParams);
}
```

**逐行解读**:
- 第 19 行: 函数签名
  - `__gm__`: 全局内存地址空间
  - `__ubuf__`: 统一缓冲区地址空间
  - dst: 目的地址（GM）
  - src: 源地址（UB）
  - size: 拷贝大小
- 第 21-22 行: 创建本地张量和全局张量
- 第 23 行: 配置数据拷贝扩展参数
  - count: 1
  - dataSize: size
- 第 24-25 行: 配置 UB 张量
  - 逻辑位置: VECIN（向量输入）
  - 缓冲区地址: src
- 第 26 行: 配置 GM 张量
- 第 28 行: 执行带填充的数据拷贝

### copy_gm2ub() - GM 到 UB 拷贝 (行 31-42)

```cpp
HYBM_AICORE_KERNEL void copy_gm2ub(__ubuf__ uint8_t* dst, __gm__ uint8_t* src, uint32_t size)
{
    AscendC::LocalTensor<uint8_t> ubTensor;
    AscendC::GlobalTensor<uint8_t> gmTensor;
    AscendC::DataCopyExtParams dataCopyParams(1, size, 0, 0, 0);
    ubTensor.address_.logicPos = static_cast<uint8_t>(AscendC::TPosition::VECIN);
    ubTensor.address_.bufferAddr = reinterpret_cast<uint64_t>(dst);
    gmTensor.SetGlobalBuffer(reinterpret_cast<__gm__ uint8_t*>(src));

    AscendC::DataCopyPadExtParams<uint8_t> padParams;
    AscendC::DataCopyPad(ubTensor, gmTensor, dataCopyParams, padParams);
}
```

**逐行解读**:
- 第 31 行: 函数签名
  - dst: 目的地址（UB）
  - src: 源地址（GM）
- 第 33-37 行: 创建张量并配置参数
- 第 40 行: 创建填充扩展参数
- 第 41 行: 执行带填充的数据拷贝（使用扩展参数）

### copy_gm2gm() - GM 到 GM 拷贝 (行 44-66)

```cpp
HYBM_AICORE_KERNEL void copy_gm2gm(__gm__ uint8_t *dst, __gm__ uint8_t *src, __ubuf__ uint8_t *buf,
                                   uint32_t ub_size, uint32_t elem_size)
{
    uint64_t repeat_times = elem_size / ub_size;
    uint64_t repeat_elem = ub_size;
    uint64_t remain = elem_size % ub_size;
    for (uint64_t i = 0; i < repeat_times; i++) {
        copy_gm2ub(buf, src + i * repeat_elem, ub_size);
        AscendC::SetFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        copy_ub2gm(dst + i * repeat_elem, buf, ub_size);
        AscendC::SetFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0);
    }
    if (remain > 0) {
        copy_gm2ub(buf, src + repeat_times * repeat_elem, remain);
        AscendC::SetFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        copy_ub2gm(dst + repeat_times * repeat_elem, buf, remain);
        AscendC::SetFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0);
    }
}
```

**逐行解读**:
- 第 44 行: 函数签名
  - dst: 目的地址（GM）
  - src: 源地址（GM）
  - buf: 中转缓冲区（UB）
  - ub_size: 缓冲区大小
  - elem_size: 总大小
- 第 47 行: 计算完整循环次数
- 第 48 行: 每次循环处理的大小
- 第 49 行: 剩余大小
- 第 50-57 行: 循环处理完整块
  - GM 到 UB 拷贝
  - SetFlag/WaitFlag: MTE2 到 MTE3 同步
  - UB 到 GM 拷贝
  - SetFlag/WaitFlag: MTE3 到 MTE2 同步
- 第 58-65 行: 处理剩余部分
  - GM 到 UB 拷贝
  - 同步
  - UB 到 GM 拷贝
  - 同步

### hybm_copy_kernel() - 主拷贝内核 (行 68-78)

```cpp
extern "C" __global__ __aicore__ void hybm_copy_kernel(GM_ADDR dst, GM_ADDR src, uint64_t len)
{
    KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIV_ONLY);
    uint32_t idx = AscendC::GetBlockIdx();
    uint32_t num = AscendC::GetBlockNum();
    uint64_t offset = ((len + SINGLE_COPY_SLICE - 1U) / SINGLE_COPY_SLICE + num - 1U) / num * SINGLE_COPY_SLICE;
    uint64_t size = min(offset * (idx + 1), len);
    offset = offset * idx;
    size -= offset;
    copy_gm2gm(dst + offset, src + offset, 0, COPY_BUF_SIZE, size);
}
```

**逐行解读**:
- 第 68 行: 函数签名
  - `extern "C"`: C 链接约定
  - `__global__`: 全局内核函数
  - `__aicore__`: AI Core 函数
  - dst/src: 目的/源地址
  - len: 拷贝长度
- 第 69 行: 设置内核类型为 AIV-only
- 第 70 行: 获取当前 Block 索引
- 第 71 行: 获取 Block 总数
- 第 72 行: 计算每个 Block 处理的偏移量
  - 向上取整对齐到 SINGLE_COPY_SLICE
  - 除以 Block 数量得到每个 Block 的大小
- 第 73-75 行: 计算当前 Block 的实际处理范围
- 第 76-77 行: 调用 GM 到 GM 拷贝函数

### hybm_copy_extend() - 拷贝扩展接口 (行 80-83)

```cpp
extern "C" void hybm_copy_extend(void *src, void *dst, uint64_t len, uint32_t dim, void *stream)
{
    hybm_copy_kernel<<<dim, nullptr, stream>>>((uint8_t *)dst, (uint8_t *)src, len);
}
```

**逐行解读**:
- 第 80 行: C 接口函数
  - src: 源地址
  - dst: 目的地址
  - len: 长度
  - dim: Block 数量（维度）
  - stream: ACL Stream
- 第 82 行: 启动 AI Core 内核
  - `<<<dim, nullptr, stream>>>`: CUDA 风格的启动语法
  - dim: Block 数量
  - nullptr: 共享内存（未使用）
  - stream: ACL Stream

### dcci_cacheline() - 缓存行清理失效 (行 85-95)

```cpp
HYBM_AICORE_KERNEL void dcci_cacheline(__gm__ uint8_t *addr)
{
    AscendC::GlobalTensor<uint8_t> global;
    global.SetGlobalBuffer(addr);

    // Important: add hint to avoid dcci being optimized by compiler
    __asm__ __volatile__("");
    AscendC::DataCacheCleanAndInvalid<uint8_t, AscendC::CacheLine::SINGLE_CACHE_LINE,
                                      AscendC::DcciDst::CACHELINE_OUT>(global);
    __asm__ __volatile__("");
}
```

**逐行解读**:
- 第 85 行: 函数签名
  - addr: 需要操作的缓存行地址
- 第 87-88 行: 创建全局张量
- 第 91 行: 内联汇编屏障，防止编译器优化
- 第 92-93 行: 执行数据缓存清理和失效操作
  - SINGLE_CACHE_LINE: 单个缓存行
  - CACHELINE_OUT: 刷新到内存
- 第 94 行: 内联汇编屏障

### hybm_batch_copy_kernel() - 批量拷贝内核 (行 97-119)

```cpp
extern "C" __global__ __aicore__ void hybm_batch_copy_kernel(GM_ADDR param, uint32_t count, GM_ADDR mask)
{
    KERNEL_TASK_TYPE_DEFAULT(KERNEL_TYPE_AIV_ONLY);
    uint32_t idx = AscendC::GetBlockIdx();
    uint32_t num = AscendC::GetBlockNum();
    uint32_t offset = (count + num - 1) / num;
    uint32_t start = offset * idx;
    uint32_t end = min(start + offset, count);

    for (uint32_t i = start; i < end; i++) {
        GM_ADDR src = reinterpret_cast<GM_ADDR>(reinterpret_cast<__gm__ uint64_t *>(param)[i * 3]);
        GM_ADDR dst = reinterpret_cast<GM_ADDR>(reinterpret_cast<__gm__ uint64_t *>(param)[i * 3 + 1]);
        uint64_t len = reinterpret_cast<__gm__ uint64_t *>(param)[i * 3 + 2];
        copy_gm2gm(dst, src, 0, COPY_BUF_SIZE, size);
    }

    __gm__ uint64_t *ptr = reinterpret_cast<__gm__ uint64_t *>(mask);
    do {
        dcci_cacheline(mask);
    } while (*ptr != idx);
    *ptr = idx + 1;
    dcci_cacheline(mask);
}
```

**逐行解读**:
- 第 97 行: 函数签名
  - param: 参数数组地址
  - count: 拷贝数量
  - mask: 同步掩码地址
- 第 99 行: 设置内核类型
- 第 100-103 行: 计算当前 Block 处理的范围
- 第 105-110 行: 循环处理每个拷贝请求
  - 参数格式: [src, dst, len, src, dst, len, ...]
  - 每次取出三个参数（源、目的、长度）
  - 调用 GM 到 GM 拷贝
- 第 112-118 行: 同步机制
  - 循环检查 mask 值是否等于当前 Block 索引
  - 每次循环前刷新缓存
  - 更新 mask 值为下一个索引
  - 刷新缓存

### hybm_batch_copy_extend() - 批量拷贝扩展接口 (行 121-124)

```cpp
extern "C" void hybm_batch_copy_extend(void *param, uint32_t count, void *mask, uint32_t dim, void *stream)
{
    hybm_batch_copy_kernel<<<dim, nullptr, stream>>>((uint8_t *)param, count, (uint8_t *)mask);
}
```

**逐行解读**:
- 第 121 行: C 接口函数
  - param: 参数数组
  - count: 拷贝数量
  - mask: 同步掩码
  - dim: Block 数量
  - stream: ACL Stream
- 第 123 行: 启动批量拷贝内核

---

## 总结

Copy_Extend 模块提供了基于 AI Core 的数据拷贝实现：

### 1. 拷贝流程

```
GM 到 GM 拷贝
    ├── 计算分块（每个 AI Core 处理一部分）
    ├── 循环处理每个块
    │   ├── GM 到 UB (copy_gm2ub)
    │   ├── 同步 (SetFlag/WaitFlag)
    │   ├── UB 到 GM (copy_ub2gm)
    │   └── 同步 (SetFlag/WaitFlag)
    └── 处理剩余部分
```

### 2. 批量拷贝

```
批量拷贝
    ├── 参数格式: [src1, dst1, len1, src2, dst2, len2, ...]
    ├── 每个 AI Core 处理一部分请求
    ├── 循环处理每个请求
    │   └── copy_gm2gm(dst, src, ...)
    └── 通过 mask 同步所有 AI Core
```

### 3. 同步机制

```
AI Core 内部同步
    ├── SetFlag<HardEvent::MTE2_MTE3>(EVENT_ID0)
    ├── WaitFlag<HardEvent::MTE2_MTE3>(EVENT_ID0)
    └── 确保 MTE 操作按顺序执行

多 AI Core 同步
    ├── 循环检查 mask 值
    ├── DCCI 缓存刷新
    └── 串行执行（通过 mask 计数）
```

### 4. 关键特性

1. **UB 中转**: GM 之间无法直接拷贝，需要通过 UB 中转
2. **事件同步**: 使用 HardEvent 确保操作顺序
3. **多核并行**: 支持多个 AI Core 并行处理
4. **缓存一致性**: 通过 DCCI 指令保证缓存一致性
5. **批量处理**: 支持多个拷贝请求的批量处理

### 5. 性能考虑

- UB 大小: 64KB（可扩展到 192KB）
- 单次拷贝切片: 128 字节
- 多核并行可提高吞吐量
- 通过事件同步避免数据冒险
