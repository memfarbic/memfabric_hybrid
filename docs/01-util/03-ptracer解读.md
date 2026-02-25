# util 模块 ptracer 逐行解读

## 概述

ptracer (performance tracer) 是 MemFabric Hybrid 项目中的性能打点工具，用于在代码中插入性能追踪点，定期收集并输出性能统计信息到文件。

### 文件清单

| 文件 | 行数 | 功能描述 |
|------|------|----------|
| [ptracer.h](../../src/util/csrc/ptracer/include/ptracer.h) | 82 | ptracer C 接口定义 |
| [ptracer.cpp](../../src/util/csrc/ptracer/ptracer.cpp) | 121 | ptracer 实现 |
| [ptracer_default.h](../../src/util/csrc/ptracer/tracers/ptracer_default.h) | 86 | 默认 tracer 实现 |
| [ptracer_default.cpp](../../src/util/csrc/ptracer/tracers/ptracer_default.cpp) | 240 | 默认 tracer 具体实现 |
| [ptracer_tracepoint.h](../../src/util/csrc/ptracer/tracers/ptracer_tracepoint.h) | 250 | 追踪点定义和集合 |
| [ptracer_utils.h](../../src/util/csrc/ptracer/tracers/ptracer_utils.h) | 210 | 工具函数 |

---

## 1. ptracer.h

### 文件信息
- **文件路径**: [src/util/csrc/ptracer/include/ptracer.h](../../src/util/csrc/ptracer/include/ptracer.h)
- **代码行数**: 82 行
- **主要功能**: ptracer C 接口定义和宏定义

### 完整代码与逐行解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 */
```
**解读**:
- 第 1-3 行: 版权声明

```cpp
#ifndef MEM_FABRIC_PTRACER_H
#define MEM_FABRIC_PTRACER_H
```
**解读**:
- 第 4-5 行: 头文件保护宏

```cpp
#include <stdint.h>
```
**解读**:
- 第 7 行: 引入标准整数类型头文件

```cpp
#ifdef __cplusplus
extern "C" {
#endif
```
**解读**:
- 第 9-11 行: C++ 兼容性支持
  - 如果是 C++ 编译器，使用 `extern "C"` 使符号按 C 方式命名
  - 允许 C 代码链接此头文件

```cpp
/**
 * @brief ptracer (i.e. performance tracer) interface for extension
 */
typedef struct {
    bool enabled;                                                                /* if the tracer enabled  */
    void (*trace_begin)(uint32_t traceId, const char *traceName);                /* function hook to start recording */
    void (*trace_end)(uint32_t traceId, const uint64_t diff, int32_t goodOrBad); /* function hook to stop recording */
    uint64_t (*current_time_ns)();                                               /* function hook to get time in ns */
} ptracer;
```
**解读**:
- 第 12-20 行: `ptracer` 结构体定义
  - 第 16 行: `enabled` - 是否启用追踪
  - 第 17 行: `trace_begin` - 开始追踪的函数指针，参数为追踪 ID 和追踪名称
  - 第 18 行: `trace_end` - 结束追踪的函数指针，参数为追踪 ID、时间差、执行结果
  - 第 19 行: `current_time_ns` - 获取当前时间（纳秒）的函数指针

```cpp
extern ptracer g_tracer;
```
**解读**:
- 第 22 行: 全局 tracer 变量声明

```cpp
typedef struct {
    int32_t tracerType;       /* 1 default tracer with file dumper */
    const char *dumpFilePath; /* dir path of dump file */
} ptracer_config_t;
```
**解读**:
- 第 24-27 行: tracer 配置结构体
  - `tracerType`: tracer 类型，目前仅支持类型 1（带文件转储的默认 tracer）
  - `dumpFilePath`: 转储文件目录路径

```cpp
int32_t ptracer_init(ptracer_config_t *config);
void ptracer_uninit(void);
const char *ptracer_get_last_err_msg(void);
const char *ptracer_get_all_tp_string(void);
```
**解读**:
- 第 29-32 行: ptracer API 函数声明
  - `ptracer_init`: 初始化 ptracer
  - `ptracer_uninit`: 清理 ptracer 资源
  - `ptracer_get_last_err_msg`: 获取最后一条错误消息
  - `ptracer_get_all_tp_string`: 获取所有追踪点的字符串表示

```cpp
/**
 * @brief Start to trace
 * @param TP_ID            [in] trace id defined with macro PTRACER_ID
 */
#define TP_TRACE_BEGIN(TP_ID)                        \
    uint64_t tpBegin##TP_ID = 0;                     \
    if (g_tracer.enabled) {                          \
        g_tracer.trace_begin(TP_ID, #TP_ID);         \
        tpBegin##TP_ID = g_tracer.current_time_ns(); \
    }
```
**解读**:
- 第 34-43 行: 开始追踪宏
  - 第 39 行: 使用 `##` 操作符将 `tpBegin` 和 `TP_ID` 连接成唯一的变量名
  - 第 40-42 行: 如果 tracer 启用，调用 `trace_begin` 并记录开始时间
  - `#TP_ID`: 将宏参数转换为字符串

```cpp
/**
 * @brief End to trace, this should be in the same thread with PTRACER_ID
 * @param TP_ID            [in] trace id defined with macro PTRACER_ID
 * @param GOOD_BAD         [in] good or bad result to be record, used to counting function
 *                              execution result beside the time cost, 0 means good, other
 *                              value means bad, bad execution will be not record into
 *                              performance counting
 */
#define TP_TRACE_END(TP_ID, GOOD_BAD)                                                     \
    if (g_tracer.enabled) {                                                               \
        g_tracer.trace_end(TP_ID, g_tracer.current_time_ns() - tpBegin##TP_ID, GOOD_BAD); \
    }
```
**解读**:
- 第 45-56 行: 结束追踪宏
  - 计算时间差并调用 `trace_end`
  - `GOOD_BAD`: 0 表示执行成功，非 0 表示执行失败

```cpp
#define TP_TRACE_TRACE_BEGIN(TP_ID, P_U64_TIME_NS)       \
    if (g_tracer.enabled) {                              \
        g_tracer.trace_begin(TP_ID, #TP_ID);             \
        (*(P_U64_TIME_NS)) = g_tracer.current_time_ns(); \
    }

#define TP_TRACE_TRACE_END(TP_ID, U64_TIME_NS, GOOD_BAD)                                   \
    if (g_tracer.enabled) {                                                                \
        g_tracer.trace_end(TP_ID, (g_tracer.current_time_ns() - (U64_TIME_NS)), GOOD_BAD); \
    }
```
**解读**:
- 第 58-67 行: 带自定义时间变量的追踪宏
  - 允许使用指定的变量存储时间值

```cpp
#define TP_TRACE_RECORD(TP_ID, U64_DIFF_TIME_NS, GOOD_BAD)       \
    if (g_tracer.enabled) {                                      \
        g_tracer.trace_begin(TP_ID, #TP_ID);                     \
        g_tracer.trace_end(TP_ID, (U64_DIFF_TIME_NS), GOOD_BAD); \
    }

#define TP_CURRENT_TIME_NS (g_tracer.current_time_ns ? g_tracer.current_time_ns() : 0)
```
**解读**:
- 第 69-75 行: 直接记录时间差的宏和获取当前时间的宏

```cpp
#define PTRACER_ID(MODULE_ID_, traceId_) ((MODULE_ID_) << 16 | ((traceId_) & 0xFFFF))
```
**解读**:
- 第 77 行: 生成追踪点 ID 的宏
  - 高 16 位：模块 ID
  - 低 16 位：追踪点 ID
  - 可以支持 65536 个模块，每个模块 65536 个追踪点

```cpp
#ifdef __cplusplus
}
#endif
#endif // MEM_FABRIC_PTRACER_H
```
**解读**:
- 第 79-82 行: 结束 C 兼容块和头文件保护

---

## 2. ptracer.cpp

### 文件信息
- **文件路径**: [src/util/csrc/ptracer/ptracer.cpp](../../src/util/csrc/ptracer/ptracer.cpp)
- **代码行数**: 121 行
- **主要功能**: ptracer C 接口实现

### 完整代码与逐行解读

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
**解读**:
- 第 1-11 行: 版权声明

```cpp
#include "ptracer.h"
#include "ptracer_default.h"
```
**解读**:
- 第 12-13 行: 引入头文件

```cpp
#define PTRACER_API __attribute__((visibility("default")))
#define PTRACER_VALIDATE_RETURN(CONDITION, MSG, RETURN_VALUE) \
    do {                                                      \
        if (!(CONDITION)) {                                   \
            LastError::Set(MSG);                              \
            return RETURN_VALUE;                              \
        }                                                     \
    } while (0)
```
**解读**:
- 第 15-22 行: 宏定义
  - `PTRACER_API`: 将函数标记为默认可见，使动态库导出此符号
  - `PTRACER_VALIDATE_RETURN`: 参数验证宏，如果条件失败则设置错误并返回

```cpp
static std::mutex g_mutex;
static bool g_inited = false;
static int32_t g_tracerType = 0;
ptracer g_tracer = {};
```
**解读**:
- 第 24-27 行: 全局静态变量
  - `g_mutex`: 保护初始化过程的互斥锁
  - `g_inited`: 是否已初始化
  - `g_tracerType`: tracer 类型
  - `g_tracer`: 全局 tracer 实例

```cpp
namespace ock {
namespace mf {
namespace tracer {
```
**解读**:
- 第 29-31 行: 定义命名空间

```cpp
int32_t InitDefaultTracer(const std::string &dumpDir, ptracer &tracer)
{
#ifdef ENABLE_PTRACER
    auto &service = DefaultTracer::GetInstance();
    if (service.StartUp(dumpDir) != 0) {
        return -1;
    }

    tracer.trace_begin = DefaultTracer::TraceBegin;
    tracer.trace_end = DefaultTracer::TraceEnd;
    tracer.current_time_ns = DefaultTracer::TimeNs;
    tracer.enabled = true;
    return 0;
#else
    tracer.enabled = false;
    return 0;
#endif
}
```
**解读**:
- 第 33-50 行: 初始化默认 tracer
  - 第 34 行: 条件编译，只有在定义了 `ENABLE_PTRACER` 时才编译
  - 第 36 行: 获取 DefaultTracer 单例
  - 第 37-39 行: 启动服务，失败则返回 -1
  - 第 41-44 行: 设置函数指针
  - 第 47-49 行: 如果未启用 ptracer，将 enabled 设为 false

```cpp
void UnInitDefaultTracer(ptracer &tracer)
{
#ifdef ENABLE_PTRACER
    DefaultTracer::GetInstance().ShutDown();
    tracer.enabled = false;
    tracer.trace_begin = nullptr;
    tracer.trace_end = nullptr;
    tracer.current_time_ns = nullptr;
#endif
}
```
**解读**:
- 第 52-61 行: 清理默认 tracer
  - 关闭服务，重置所有函数指针

```cpp
} // namespace tracer
} // namespace mf
} // namespace ock
```
**解读**:
- 第 63-65 行: 命名空间结束

```cpp
PTRACER_API int32_t ptracer_init(ptracer_config_t *config)
{
    std::lock_guard<std::mutex> guard(g_mutex);
    if (g_inited) {
        return 0;
    }

    using namespace ock::mf::tracer;
    PTRACER_VALIDATE_RETURN(config != nullptr, "invalid config, which is null", -1);
    PTRACER_VALIDATE_RETURN(config->tracerType == 1, "invalid config.dumpType, only 1 is supported", -1);
    PTRACER_VALIDATE_RETURN(config->dumpFilePath != nullptr, "invalid param config.dumpFilePath is null", -1);

    int32_t result = 0;
    if (config->tracerType == 1) {
        result = InitDefaultTracer(config->dumpFilePath, g_tracer);
    }

    if (result == 0) {
        g_tracerType = config->tracerType;
        g_inited = true;
    }

    return result;
}
```
**解读**:
- 第 67-90 行: `ptracer_init` 实现
  - 第 68 行: 加锁保护初始化
  - 第 69-71 行: 如果已经初始化，直接返回
  - 第 75-77 行: 验证配置参数
  - 第 80-82 行: 根据类型初始化对应的 tracer
  - 第 84-87 行: 记录类型并标记已初始化

```cpp
PTRACER_API void ptracer_uninit(void)
{
    std::lock_guard<std::mutex> guard(g_mutex);
    if (!g_inited) {
        return;
    }

    if (g_tracerType) {
        ock::mf::tracer::UnInitDefaultTracer(g_tracer);
    }
    g_inited = false;
}
```
**解读**:
- 第 92-103 行: `ptracer_uninit` 实现
  - 清理 tracer 并重置初始化标志

```cpp
PTRACER_API const char *ptracer_get_last_err_msg(void)
{
    return ock::mf::tracer::LastError::Get();
}

PTRACER_API const char *ptracer_get_all_tp_string(void)
{
#ifdef ENABLE_PTRACER
    thread_local static std::string allTpString;
    std::stringstream ss;
    ock::mf::tracer::DefaultTracer::GetInstance().GenerateAllTpString(ss, true);
    allTpString = ss.str();
    return allTpString.c_str();
#else
    return "";
#endif
}
```
**解读**:
- 第 105-121 行: 错误消息获取和追踪点字符串获取
  - 第 113 行: 使用 `thread_local` 存储线程局部的字符串
  - 第 115-116 行: 生成所有追踪点的字符串表示

---

## 3. ptracer_default.h

### 文件信息
- **文件路径**: [src/util/csrc/ptracer/tracers/ptracer_default.h](../../src/util/csrc/ptracer/tracers/ptracer_default.h)
- **代码行数**: 86 行
- **主要功能**: 默认 tracer 类定义

### 主要类和方法

```cpp
class DefaultTracer {
public:
    static void TraceBegin(uint32_t tpId, const char *tpName);
    static void TraceEnd(uint32_t tpId, uint64_t ns, int32_t goodBad);
    static uint64_t TimeNs();

    static DefaultTracer &GetInstance();
    int32_t StartUp(const std::string &dumpDir);
    void ShutDown();
    int GenerateAllTpString(std::stringstream &ss, bool needTotal = false);

private:
    int PrepareDumpFile(const std::string &dumpDir);
    void StartDumpThread();
    void RunInThread();
    void DumpTracepoints();

    // 成员变量
    off_t writePos_{0};                          // 写入位置
    std::string dumpFilePath_{};                 // 转储文件路径
    std::string headline_{};                     // 标题行
    std::mutex dumpLock_{};                      // 转储锁
    bool running_{false};                        // 线程运行标志
    std::thread dumpThread_{};                   // 转储线程
    std::condition_variable dumpCond_{};         // 条件变量

    int32_t DUMP_PERIOD_SECOND = 10;             // 转储周期：10秒
    size_t MAX_DUMP_SIZE = 10 * 1024 * 1024;     // 最大文件大小：10MB
};
```

---

## 4. ptracer_tracepoint.h

### 文件信息
- **文件路径**: [src/util/csrc/ptracer/tracers/ptracer_tracepoint.h](../../src/util/csrc/ptracer/tracers/ptracer_tracepoint.h)
- **代码行数**: 250 行
- **主要功能**: 追踪点定义和集合

### Tracepoint 类

```cpp
class Tracepoint {
public:
    __always_inline void TraceBegin(const std::string &tpName)
    {
        bool expectVal = false;
        if (nameValid_.compare_exchange_weak(expectVal, true)) {
            name_ = tpName;
        }
        begin_.fetch_add(1u, std::memory_order_relaxed);
    }

    __always_inline void TraceEnd(uint64_t diff, int32_t goodBadExecution)
    {
        if (goodBadExecution != 0) {
            badEnd_.fetch_add(1u, std::memory_order_relaxed);
            return;
        }

        if (diff < min_) {
            min_.store(diff, std::memory_order_relaxed);
        }
        // ... 更新统计数据
        total_.fetch_add(diff, std::memory_order_relaxed);
        goodEnd_.fetch_add(1u, std::memory_order_relaxed);
    }

private:
    std::string name_;                          // 追踪点名称
    std::atomic<bool> nameValid_{false};       // 名称是否有效
    std::atomic_uint_fast64_t begin_{0};       // 开始次数
    std::atomic_uint_fast64_t goodEnd_{0};     // 成功结束次数
    std::atomic_uint_fast64_t badEnd_{0};      // 失败结束次数
    std::atomic_uint_fast64_t min_{UINT64_MAX}; // 最小耗时
    std::atomic_uint_fast64_t max_{0};         // 最大耗时
    std::atomic_uint_fast64_t total_{0};       // 总耗时
    // ... 之前周期的数据
};
```

**解读**:
- 使用原子操作保证线程安全
- 记录最小/最大/总耗时，支持周期性统计

### TracepointCollection 类

```cpp
class TracepointCollection {
public:
    static constexpr int32_t MAX_MODULE_COUNT = 64;      // 最大模块数
    static constexpr int32_t MAX_TRACE_ID_COUNT = 1024;  // 每个模块最大追踪点数

    static __always_inline Tracepoint *GetTracepoint(uint32_t tpId);
    static __always_inline void TraceBegin(uint32_t tpId, const std::string &tpName);
    static __always_inline void TraceEnd(uint32_t tpId, const uint64_t &diff, int32_t goodBadExecution);

private:
    static __always_inline uint32_t GetModuleId(uint32_t tpId)
    {
        return ((tpId >> 16) & 0xFFFF);
    }

    static __always_inline uint32_t GetTraceId(uint32_t tpId)
    {
        return (tpId & 0xFFFF);
    }
};
```

**解读**:
- 从 32 位追踪点 ID 中提取模块 ID（高 16 位）和追踪点 ID（低 16 位）
- 追踪点以二维数组组织：`tracepoints[module_id][trace_id]`

---

## 5. ptracer_default.cpp

### 文件信息
- **文件路径**: [src/util/csrc/ptracer/tracers/ptracer_default.cpp](../../src/util/csrc/ptracer/tracers/ptracer_default.cpp)
- **代码行数**: 240 行
- **主要功能**: 默认 tracer 具体实现

### 关键方法解读

#### StartUp - 初始化

```cpp
int32_t DefaultTracer::StartUp(const std::string &dumpDir)
{
    auto tracePoints = TracepointCollection::GetTracepoints();
    if (tracePoints == nullptr) {
        LastError::Set("get tracepoints collection failed");
        return -1;
    }
    if (PrepareDumpFile(dumpDir) != 0) {
        return -1;
    }
    StartDumpThread();
    return 0;
}
```

#### PrepareDumpFile - 准备转储文件

```cpp
int32_t DefaultTracer::PrepareDumpFile(const std::string &dumpDir)
{
    if (dumpDir.empty()) {
        LastError::Set("create dump file failed as dumpDir is empty");
        return -1;
    }

    std::string dumpFileDir = dumpDir;
    if (dumpFileDir.back() != '/') {
        dumpFileDir += "/";
    }

    int32_t ret = Func::MakeDir(dumpFileDir);
    if (ret != 0) {
        LastError::Set("create dir @" + dumpFileDir + " failed, errno " + std::to_string(errno));
        return -1;
    }

    dumpFilePath_ = dumpFileDir + "ptracer_" + std::to_string(getpid()) + ".dat";
    int32_t fd = open(dumpFilePath_.c_str(), O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR | S_IRGRP);
    if (fd < 0) {
        LastError::Set("create or open file @" + dumpFilePath_ + " failed, errno " + std::to_string(errno));
        return -1;
    }
    close(fd);
    return 0;
}
```

**解读**:
- 文件名格式：`ptracer_<pid>.dat`
- 使用进程 ID 区分不同进程的文件

#### StartDumpThread 和 RunInThread - 后台转储线程

```cpp
void DefaultTracer::StartDumpThread()
{
    std::unique_lock<std::mutex> lock(dumpLock_);
    if (running_) {
        return;
    }

    running_ = true;
    dumpThread_ = std::thread(&DefaultTracer::RunInThread, this);
    pthread_setname_np(dumpThread_.native_handle(), "ptracer_dump");
}

void DefaultTracer::RunInThread()
{
    std::unique_lock<std::mutex> lock(dumpLock_);
    while (running_) {
        dumpCond_.wait_for(lock, std::chrono::seconds(DUMP_PERIOD_SECOND));
        DumpTracepoints();
    }
}
```

**解读**:
- 每 10 秒（`DUMP_PERIOD_SECOND`）自动转储一次追踪点数据
- 使用条件变量实现定时等待

---

## 使用示例

```cpp
// 定义追踪点 ID
#define MY_MODULE_ID 1
#define TP_MY_FUNCTION PTRACER_ID(MY_MODULE_ID, 1)

// 在代码中使用
void MyFunction() {
    TP_TRACE_BEGIN(TP_MY_FUNCTION);

    // 执行一些操作...
    int result = DoSomething();

    // 0 表示成功，非 0 表示失败
    TP_TRACE_END(TP_MY_FUNCTION, result);
}

// 初始化 ptracer
ptracer_config_t config = {
    .tracerType = 1,
    .dumpFilePath = "/var/log/memfabric_hybrid"
};
ptracer_init(&config);

// 使用完毕后清理
ptracer_uninit();
```

---

## 总结

ptracer 模块提供了：

1. **低开销的性能追踪**：使用原子操作和内联函数，最小化性能影响
2. **自动转储**：后台线程定期将数据写入文件
3. **统计功能**：记录最小/最大/平均耗时，成功/失败次数
4. **线程安全**：所有操作都是线程安全的
5. **灵活的 ID 编码**：支持多模块、多追踪点

转储文件示例格式：
```
2025-02-24 10:30:00 | TP_NAME | 1000 | 950 | 50 | 1000 | 5000 | 4750000
```
- 时间戳 | 追踪点名称 | 开始次数 | 成功次数 | 失败次数 | 最小耗时(ns) | 最大耗时(ns) | 总耗时(ns)
