# util 模块 csrc 源文件逐行解读

## 文件清单

| 文件 | 行数 | 功能描述 |
|------|------|----------|
| mf_syntactic_sugar.h | 36 | 语法糖宏定义，提供 defer 机制 |
| mf_spinlock.h | 52 | 自旋锁实现 |
| mf_rwlock.h | 92 | 读写锁实现 |
| mf_monotonic_time.h | 168 | 单调时间获取 |
| mf_tls_util.h | 62 | 线程本地存储和动态库加载工具 |
| mf_str_util.h | 151 | 字符串处理工具 |
| mf_num_util.h | 104 | 数值处理工具 |
| mf_net.h | 95 | 网络地址结构定义 |
| mf_ipv4_validator.h | 354 | IPv4 地址和端口验证器 |
| mf_file_util.h | 403 | 文件操作工具 |
| mf_out_logger.h | 220 | 日志输出工具 |

---

## 1. mf_syntactic_sugar.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_syntactic_sugar.h](../../src/util/csrc/mf_syntactic_sugar.h)
- **代码行数**: 36 行
- **主要功能**: 提供语法糖宏定义，实现 defer 延迟执行机制

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
- 第 1-11 行: 版权和许可证声明，使用 Mulan PSL v2 许可证

```cpp
#ifndef MEMFABRIC_HYBRID_MF_SYNTACTIC_SUGAR_H
#define MEMFABRIC_HYBRID_MF_SYNTACTIC_SUGAR_H
```
**解读**:
- 第 12-13 行: 头文件保护宏，防止重复包含

```cpp
#include <utility>
```
**解读**:
- 第 14 行: 引入 `<utility>` 头文件，提供 `std::forward` 等工具

```cpp
namespace ock {
namespace mf {
```
**解读**:
- 第 16-17 行: 定义命名空间 `ock::mf`，整个项目使用此命名空间

```cpp
template<typename F>
struct Defer {
    F f;
    Defer(F &&f) : f(std::forward<F>(f)) {}
    ~Defer()
    {
        f();
    }
};
```
**解读**:
- 第 18-26 行: `Defer` 结构体模板，实现延迟执行机制
  - 第 19 行: 成员变量 `f`，存储可调用对象
  - 第 21 行: 构造函数，使用完美转发接收参数并初始化成员
  - 第 22-25 行: 析构函数，在对象销毁时调用存储的可调用对象

```cpp
template<typename F>
Defer<F> defer(F &&f)
{
    return Defer<F>(std::forward<F>(f));
}
```
**解读**:
- 第 28-32 行: `defer` 函数模板，用于创建 `Defer` 对象
  - 使用完美转发保持参数的值类别
  - 返回 `Defer<F>` 对象，当对象离开作用域时执行传入的函数

```cpp
} // namespace mf
} // namespace ock
#endif //MEMFABRIC_HYBRID_MF_SYNTACTIC_SUGAR_H
```
**解读**:
- 第 33-35 行: 命名空间结束和头文件保护结束

### 关键逻辑分析

**设计模式**: RAII (Resource Acquisition Is Initialization)
- 利用 C++ 析构函数保证在作用域结束时执行清理代码
- 类似 Go 语言中的 defer 语句

**使用示例**:
```cpp
{
    auto d = defer([&]() { fclose(fp); });  // 离开作用域时自动执行
    // 其他操作...
}  // defer 中定义的 lambda 在此处执行
```

---

## 2. mf_spinlock.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_spinlock.h](../../src/util/csrc/mf_spinlock.h)
- **代码行数**: 52 行
- **主要功能**: 基于原子操作的自旋锁实现

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
- 第 1-11 行: 版权和许可证声明

```cpp
#ifndef MEMFABRIC_HYBRID_SPINLOCK_H
#define MEMFABRIC_HYBRID_SPINLOCK_H
```
**解读**:
- 第 13-14 行: 头文件保护宏

```cpp
#include <atomic>
#include <thread>
```
**解读**:
- 第 16-17 行: 引入 `<atomic>` 和 `<thread>` 头文件

```cpp
namespace ock {
namespace mf {
```
**解读**:
- 第 19-20 行: 定义命名空间

```cpp
class SpinLock {
public:
    SpinLock() : flag_(false) {}
```
**解读**:
- 第 22-24 行: `SpinLock` 类定义和构造函数
  - 第 24 行: 使用成员初始化列表将 `flag_` 初始化为 `false`

```cpp
    void lock()
    {
        while (flag_.exchange(true, std::memory_order_acquire)) {
            while (flag_.load(std::memory_order_relaxed)) {
                std::this_thread::yield();  // 让出CPU时间片
            }
        }
    }
```
**解读**:
- 第 26-33 行: `lock()` 方法，尝试获取锁
  - 第 27 行: `exchange` 原子操作，将 `flag_` 设为 `true` 并返回旧值
  - 使用 `memory_order_acquire` 获取内存序，保证后续操作可见性
  - 第 28-31 行: 如果锁已被占用（exchange 返回 true），进入自旋等待
  - 第 29 行: 使用 `memory_order_relaxed` 轻量级检查锁状态
  - 第 30 行: 让出 CPU 时间片，避免忙等待浪费 CPU

```cpp
    void unlock()
    {
        flag_.store(false, std::memory_order_release);
    }
```
**解读**:
- 第 35-38 行: `unlock()` 方法，释放锁
  - 使用 `memory_order_release` 释放内存序，保证之前的操作对其他线程可见

```cpp
    bool try_lock()
    {
        return !flag_.exchange(true, std::memory_order_acquire);
    }
```
**解读**:
- 第 40-43 行: `try_lock()` 方法，尝试获取锁但不阻塞
  - 返回 `true` 表示成功获取锁，`false` 表示锁已被占用

```cpp
private:
    std::atomic<bool> flag_;
};
```
**解读**:
- 第 45-47 行: 私有成员变量
  - `flag_`: 原子布尔类型，表示锁的状态

### 关键逻辑分析

**内存序说明**:
- `memory_order_acquire`: 获取操作，保证后续读写操作不会重排到此操作之前
- `memory_order_release`: 释放操作，保证之前的读写操作不会重排到此操作之后
- `memory_order_relaxed`: 松散操作，不保证顺序，仅保证原子性

---

## 3. mf_rwlock.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_rwlock.h](../../src/util/csrc/mf_rwlock.h)
- **代码行数**: 92 行
- **主要功能**: 基于 pthread 的读写锁实现

### 完整代码与逐行解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 */
```
**解读**:
- 第 1-4 行: 版权声明

```cpp
#ifndef MF_HYBRID_MF_RWLOCK_H
#define MF_HYBRID_MF_RWLOCK_H
```
**解读**:
- 第 4-5 行: 头文件保护宏

```cpp
#include <pthread.h>
```
**解读**:
- 第 7 行: 引入 pthread 头文件，使用 POSIX 读写锁

```cpp
namespace ock {
namespace mf {
class ReadWriteLock {
public:
    ReadWriteLock()
    {
        pthread_rwlock_init(&mLock, nullptr);
    }
```
**解读**:
- 第 11-16 行: `ReadWriteLock` 类和构造函数
  - 第 15 行: 使用 `pthread_rwlock_init` 初始化读写锁，第二个参数 `nullptr` 表示使用默认属性

```cpp
    ~ReadWriteLock()
    {
        pthread_rwlock_destroy(&mLock);
    }
```
**解读**:
- 第 18-21 行: 析构函数
  - 第 20 行: 销毁读写锁，释放相关资源

```cpp
    ReadWriteLock(const ReadWriteLock &) = delete;
    ReadWriteLock &operator=(const ReadWriteLock &) = delete;
    ReadWriteLock(ReadWriteLock &&) = delete;
    ReadWriteLock &operator=(ReadWriteLock &&) = delete;
```
**解读**:
- 第 23-26 行: 禁用拷贝和移动构造函数及赋值运算符
  - 防止锁对象被拷贝或移动，避免未定义行为

```cpp
    inline void LockRead()
    {
        pthread_rwlock_rdlock(&mLock);
    }
```
**解读**:
- 第 28-31 行: 获取读锁
  - `pthread_rwlock_rdlock`: 获取共享读锁，多个线程可同时持有读锁

```cpp
    inline void LockWrite()
    {
        pthread_rwlock_wrlock(&mLock);
    }
```
**解读**:
- 第 33-36 行: 获取写锁
  - `pthread_rwlock_wrlock`: 获取独占写锁，只允许一个线程持有

```cpp
    inline void UnLock()
    {
        pthread_rwlock_unlock(&mLock);
    }
```
**解读**:
- 第 38-41 行: 释放锁
  - 释放读锁或写锁

```cpp
private:
    pthread_rwlock_t mLock{};
};
```
**解读**:
- 第 43-45 行: 私有成员
  - `mLock`: pthread 读写锁对象，使用 `{}` 初始化为零

```cpp
class WriteGuard {
public:
    WriteGuard(ReadWriteLock &lock) : lock_(lock)
    {
        lock_.LockWrite();
    }

    ~WriteGuard()
    {
        lock_.UnLock();
    }
```
**解读**:
- 第 47-57 行: `WriteGuard` 写锁守卫类（RAII 模式）
  - 第 49-51 行: 构造时获取写锁
  - 第 54-57 行: 析构时自动释放锁

```cpp
    WriteGuard(const WriteGuard &) = delete;
    WriteGuard &operator=(const WriteGuard &) = delete;
    WriteGuard(WriteGuard &&) = delete;
    WriteGuard &operator=(WriteGuard &&) = delete;

private:
    ReadWriteLock &lock_;
};
```
**解读**:
- 第 59-66 行: 禁用拷贝和移动操作，存储锁的引用

```cpp
class ReadGuard {
public:
    ReadGuard(ReadWriteLock &lock) : lock_(lock)
    {
        lock_.LockRead();
    }

    ~ReadGuard()
    {
        lock_.UnLock();
    }
```
**解读**:
- 第 68-78 行: `ReadGuard` 读锁守卫类，与 `WriteGuard` 类似，但使用读锁

### 关键逻辑分析

**RAII 模式**: `WriteGuard` 和 `ReadGuard` 使用 RAII 模式自动管理锁的生命周期

**使用示例**:
```cpp
ReadWriteLock rwLock;

// 读锁
{
    ReadGuard guard(rwLock);  // 构造时获取读锁
    // 读取数据...
}  // 离开作用域，自动释放锁

// 写锁
{
    WriteGuard guard(rwLock);  // 构造时获取写锁
    // 修改数据...
}  // 离开作用域，自动释放锁
```

---

## 4. mf_monotonic_time.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_monotonic_time.h](../../src/util/csrc/mf_monotonic_time.h)
- **代码行数**: 168 行
- **主要功能**: 提供单调时间获取，避免系统时间调整影响

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
#ifndef MEMFABRIC_HYBRID_MONOTONIC_H
#define MEMFABRIC_HYBRID_MONOTONIC_H
```
**解读**:
- 第 12-13 行: 头文件保护宏

```cpp
#include <cstdio>
#include <cstdint>
#include <ctime>
```
**解读**:
- 第 15-17 行: 引入标准库头文件

```cpp
namespace ock {
namespace mf {
class MonotonicTime {
public:
    /**
     * @brief Get monotonic time in us, is not absolution time
     */
    static inline uint64_t TimeUs();

    /**
     * @brief Get monotonic time in ns, is not absolution time
     */
    static inline uint64_t TimeNs();

private:
    /* only ENABLE_CPU_MONOTONIC */
    template<int32_t FAILURE_RET>
    static int32_t InitTickUs();
};
```
**解读**:
- 第 19-37 行: `MonotonicTime` 类定义
  - 第 26 行: 获取微秒级单调时间
  - 第 31 行: 获取纳秒级单调时间
  - 第 36 行: 初始化 CPU tick 频率的模板函数

```cpp
class MonoPerfTrace {
public:
    MonoPerfTrace();

    ~MonoPerfTrace() = default;

    /**
     * @brief Record start time
     */
    void RecordStart() noexcept;

    /**
     * @brief Record end time
     */
    void RecordEnd() noexcept;

    /**
     * @brief Get period in ns
     */
    uint64_t PeriodNs() const noexcept;

    /**
     * @brief Get period in us
     */
    uint64_t PeriodUs() const noexcept;

    /**
     * @brief Get period in ms
     */
    uint64_t PeriodMs() const noexcept;

public:
    uint64_t start = 0; /* start time in ns */
    uint64_t end = 0;   /* end time in ns */
};
```
**解读**:
- 第 39-73 行: `MonoPerfTrace` 性能追踪类
  - 用于测量代码段的执行时间
  - `start`: 记录开始时间（纳秒）
  - `end`: 记录结束时间（纳秒）

```cpp
#if defined(ENABLE_CPU_MONOTONIC) && defined(__aarch64__)
```
**解读**:
- 第 75 行: 条件编译，仅在启用 CPU 单调时间且为 ARM64 架构时编译以下代码

```cpp
template<int32_t FAILURE_RET>
inline int32_t MonotonicTime::InitTickUs()
{
    /* get frequ */
    uint64_t tmpFreq = 0;
    __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(tmpFreq));
```
**解读**:
- 第 77-82 行: 读取 ARM64 系统计数器频率
  - `mrs`: 指令从系统寄存器读取到通用寄存器
  - `cntfrq_el0`: ARM64 系统计数器频率寄存器

```cpp
    auto freq = static_cast<uint32_t>(tmpFreq);

    /* calculate */
    freq = freq / 1000L / 1000L;
    if (freq == 0) {
        printf("Failed to get tick as freq is %d\n", freq);
        return FAILURE_RET;
    }

    return freq;
}
```
**解读**:
- 第 83-93 行: 计算每微秒的 tick 数
  - 将频率从 Hz 转换为 MHz（除以 1000000）
  - 如果计算结果为 0，返回失败值

```cpp
inline uint64_t MonotonicTime::TimeUs()
{
    const static int32_t TICK_PER_US = InitTickUs<1>();
    uint64_t timeValue = 0;
    __asm__ volatile("mrs %0, cntvct_el0" : "=r"(timeValue));
    return timeValue / TICK_PER_US;
}
```
**解读**:
- 第 95-101 行: 使用 ARM64 CPU 指令获取微秒级单调时间
  - `cntvct_el0`: ARM64 虚拟计数器寄存器，单调递增
  - 将 tick 值转换为微秒

```cpp
inline uint64_t MonotonicTime::TimeNs()
{
    const static int32_t TICK_PER_US = InitTickUs<1>();
    uint64_t timeValue = 0;
    __asm__ volatile("mrs %0, cntvct_el0" : "=r"(timeValue));
    return timeValue * 1000L / TICK_PER_US;
}
```
**解读**:
- 第 103-109 行: 获取纳秒级单调时间
  - 先乘以 1000 转换为纳秒单位，再除以每微秒的 tick 数

```cpp
#else  /* defined(ENABLE_CPU_MONOTONIC) && defined(__aarch64__) */
```
**解读**:
- 第 111 行: 条件编译的 else 分支

```cpp
template<int32_t FAILURE_RET>
int32_t MonotonicTime::InitTickUs()
{
    return 0;
}
```
**解读**:
- 第 113-117 行: 非 ARM64 平台的空实现

```cpp
inline uint64_t MonotonicTime::TimeUs()
{
    struct timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<uint64_t>(ts.tv_sec * 1000000L + ts.tv_nsec / 1000L);
}
```
**解读**:
- 第 119-124 行: 使用 POSIX `clock_gettime` 获取单调时间
  - `CLOCK_MONOTONIC`: 单调递增的时钟，不受系统时间调整影响
  - 将秒和纳秒转换为微秒

```cpp
inline uint64_t MonotonicTime::TimeNs()
{
    struct timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<uint64_t>(ts.tv_sec * 1000000000L + ts.tv_nsec);
}
```
**解读**:
- 第 126-131 行: 获取纳秒级单调时间
  - 将秒和纳秒转换为纳秒

```cpp
#endif /* ENABLE_CPU_MONOTONIC */
```
**解读**:
- 第 132 行: 条件编译结束

```cpp
/* functions of MonoPerfTrace */
inline MonoPerfTrace::MonoPerfTrace()
{
    RecordStart();
}

inline void MonoPerfTrace::RecordStart() noexcept
{
    start = MonotonicTime::TimeNs();
}

inline void MonoPerfTrace::RecordEnd() noexcept
{
    end = MonotonicTime::TimeNs();
}

inline uint64_t MonoPerfTrace::PeriodNs() const noexcept
{
    return end - start;
}

inline uint64_t MonoPerfTrace::PeriodUs() const noexcept
{
    return (end - start) / 1000L;
}

inline uint64_t MonoPerfTrace::PeriodMs() const noexcept
{
    return (end - start) / 1000000L;
}
```
**解读**:
- 第 134-163 行: `MonoPerfTrace` 类的方法实现
  - 构造函数自动记录开始时间
  - 提供纳秒、微秒、毫秒三种时间单位获取

### 关键逻辑分析

**两种实现方式**:
1. **ARM64 CPU 指令方式**（性能更高）:
   - 直接读取硬件计数器寄存器
   - 无需系统调用，开销小

2. **POSIX 系统调用方式**（通用）:
   - 使用 `clock_gettime`
   - 可移植性更好

**使用示例**:
```cpp
MonoPerfTrace trace;
// 执行一些操作...
trace.RecordEnd();
std::cout << "耗时: " << trace.PeriodUs() << " 微秒" << std::endl;
```

---

## 5. mf_tls_util.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_tls_util.h](../../src/util/csrc/mf_tls_util.h)
- **代码行数**: 62 行
- **主要功能**: 线程本地存储和动态库加载工具

### 完整代码与逐行解读

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 */
```
**解读**:
- 第 1-4 行: 版权声明

```cpp
#ifndef MEMFABRIC_HYBRID_TLS_UTIL_H
#define MEMFABRIC_HYBRID_TLS_UTIL_H
```
**解读**:
- 第 5-6 行: 头文件保护宏

```cpp
#include <algorithm>
#include <cstdint>
#include <dlfcn.h>
```
**解读**:
- 第 8-10 行: 引入头文件，`dlfcn.h` 用于动态库加载

```cpp
namespace ock {
namespace mf {

using DecryptFunc = int (*)(const char *cipherText, const size_t cipherTextLen, char *plainText, size_t plainTextLen);
```
**解读**:
- 第 15 行: 定义解密函数指针类型
  - 参数：密文、密文长度、明文缓冲区、明文长度
  - 返回值：int，0 表示成功

```cpp
class MfTlsUtil {
public:
    static inline int32_t DefaultDecrypter(const char *cipherText, const size_t cipherTextLen, char *plainText,
                                           const size_t plainTextLen)
    {
        std::copy_n(cipherText, plainTextLen, plainText);
        return 0;
    }
```
**解读**:
- 第 17-24 行: 默认解密器实现
  - 实际上不做解密，直接拷贝数据
  - 用于不需要解密的场景

```cpp
    static inline void **GetTlsLibHandler()
    {
        static void *decryptLibHandle = nullptr;
        return &decryptLibHandle;
    }
```
**解读**:
- 第 26-30 行: 获取线程本地库句柄指针
  - 使用 `static` 变量，但这里是函数静态变量，不是线程本地存储
  - 返回指向指针的指针，允许修改句柄值

```cpp
    static inline DecryptFunc LoadDecryptFunction(const char *decrypterLibPath)
    {
        void **decryptLibHandlePtr = GetTlsLibHandler();
        if (*decryptLibHandlePtr == nullptr) {
            *decryptLibHandlePtr = dlopen(decrypterLibPath, RTLD_LAZY);
        }
```
**解读**:
- 第 32-48 行: 加载解密函数
  - 第 33 行: 获取库句柄指针
  - 第 34-36 行: 如果句柄为空，使用 `dlopen` 加载动态库
  - `RTLD_LAZY`: 延迟绑定，只在需要时解析符号

```cpp
        if (*decryptLibHandlePtr != nullptr) {
            const auto decryptFunc = (DecryptFunc)dlsym(*decryptLibHandlePtr, "DecryptPassword");
            if (decryptFunc != nullptr) {
                return decryptFunc;
            } else {
                CloseTlsLib();
                return nullptr;
            }
        }
        return nullptr;
    }
```
**解读**:
- 第 38-48 行: 查找解密函数
  - `dlsym`: 在动态库中查找符号
  - 如果找到函数 `DecryptPassword`，返回函数指针
  - 如果未找到，关闭库并返回空指针

```cpp
    static inline void CloseTlsLib()
    {
        void **decryptLibHandlePtr = GetTlsLibHandler();
        if (*decryptLibHandlePtr != nullptr) {
            dlclose(*decryptLibHandlePtr);
            decryptLibHandlePtr = nullptr;
        }
    }
};
```
**解读**:
- 第 50-57 行: 关闭动态库
  - 注意：第 55 行有 bug，应该设置为 `*decryptLibHandlePtr = nullptr;`

### 关键逻辑分析

**Bug 分析**: 第 55 行 `decryptLibHandlePtr = nullptr` 只是让局部指针变量指向空，没有修改实际的句柄。应该改为 `*decryptLibHandlePtr = nullptr;`。

---

## 6. mf_str_util.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_str_util.h](../../src/util/csrc/mf_str_util.h)
- **代码行数**: 151 行
- **主要功能**: 字符串处理工具函数

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
#ifndef MEMFABRIC_HYBRID_STR_UTIL_H
#define MEMFABRIC_HYBRID_STR_UTIL_H
```
**解读**:
- 第 12-13 行: 头文件保护宏

```cpp
#include <string>
#include <vector>
#include <sstream>
#include <limits>
#include <chrono>
```
**解读**:
- 第 15-19 行: 引入标准库头文件

```cpp
namespace ock {
namespace mf {
static const std::string ipv6_common_core = R"((?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7})|)"
                                            R"((?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){0,6})?::)"
                                            R"((?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){0,6})?)";
```
**解读**:
- 第 21-25 行: IPv6 地址正则表达式模式（原始字符串字面量）
  - 使用 `R"(...)"` 语法避免转义字符
  - 匹配标准 IPv6 地址格式

```cpp
class StrUtil {
public:
    static std::string StrTrim(const std::string &str);
    static inline std::vector<std::string> Split(const std::string &str, char delimiter);
    static inline bool StartWith(const std::string &str, const std::string &prefix);
    template<typename UIntType>
    static inline bool String2Uint(const std::string &str, UIntType &val);
    template<typename IntType>
    static inline bool String2Int(const std::string &str, IntType &val);
    static inline int64_t GetNowTime();
};
```
**解读**:
- 第 26-36 行: `StrUtil` 类声明，包含静态工具方法

```cpp
inline std::string StrUtil::StrTrim(const std::string &input)
{
    if (input.empty()) {
        return "";
    }
    auto start = input.begin();
    while (start != input.end() && std::isspace(*start)) {
        start++;
    }
```
**解读**:
- 第 38-46 行: `StrTrim` 方法实现（去除首尾空格）
  - 第 40-42 行: 如果输入为空，返回空字符串
  - 第 44-46 行: 找到第一个非空格字符

```cpp
    auto end = input.end();
    do {
        end--;
    } while (std::distance(start, end) > 0 && std::isspace(*end));

    return std::string(start, end + 1);
}
```
**解读**:
- 第 48-54 行: 找到最后一个非空格字符并返回子串

```cpp
inline std::vector<std::string> StrUtil::Split(const std::string &str, char delimiter)
{
    std::vector<std::string> result;
    std::stringstream ss(str);
    std::string item;

    while (std::getline(ss, item, delimiter)) {
        result.push_back(item);
    }

    return result;
}
```
**解读**:
- 第 56-67 行: 字符串分割方法
  - 使用 `std::getline` 按分隔符分割字符串

```cpp
inline bool StrUtil::StartWith(const std::string &str, const std::string &prefix)
{
    return str.length() >= prefix.length() && str.compare(0, prefix.length(), prefix) == 0;
}
```
**解读**:
- 第 69-72 行: 检查字符串是否以指定前缀开头

```cpp
template<typename UIntType>
inline bool StrUtil::String2Uint(const std::string &str, UIntType &val)
{
    if (str.empty()) {
        return false;
    }

    if (str[0] == '-') {
        return false;
    }

    char *end = nullptr;
    errno = 0;

    unsigned long long result = std::strtoull(str.c_str(), &end, 10);
```
**解读**:
- 第 74-88 行: 字符串转无符号整数模板函数
  - 第 76-78 行: 检查空字符串
  - 第 80-82 行: 检查负号（无符号数不能为负）
  - 第 84-86 行: 设置 errno 并使用 `strtoull` 转换

```cpp
    if (end == str.c_str()) {
        return false;
    }

    while (*end != '\0' && std::isspace(*end)) {
        ++end;
    }
    if (*end != '\0') {
        return false;
    }

    if (errno == ERANGE || result > static_cast<unsigned long long>(std::numeric_limits<UIntType>::max())) {
        return false;
    }

    val = static_cast<UIntType>(result);
    return true;
}
```
**解读**:
- 第 90-107 行: 检查转换结果的合法性
  - 检查是否有无效字符
  - 检查是否溢出
  - 转换成功则设置输出值并返回 true

```cpp
template<typename IntType>
inline bool StrUtil::String2Int(const std::string &str, IntType &val)
{
    if (str.empty()) {
        return false;
    }

    char *end = nullptr;
    errno = 0;

    int64_t result = std::strtoll(str.c_str(), &end, 10);

    if (end == str.c_str()) {
        return false;
    }

    while (*end != '\0' && std::isspace(*end)) {
        ++end;
    }
    if (*end != '\0') {
        return false;
    }

    if (errno == ERANGE || result > static_cast<int64_t>(std::numeric_limits<IntType>::max())) {
        return false;
    }

    val = static_cast<IntType>(result);
    return true;
}
```
**解读**:
- 第 109-138 行: 字符串转有符号整数模板函数，逻辑与无符号版本类似

```cpp
inline int64_t StrUtil::GetNowTime()
{
    auto now = std::chrono::system_clock::now();
    auto now_ms = std::chrono::time_point_cast<std::chrono::milliseconds>(now);
    auto value = now_ms.time_since_epoch().count();
    return static_cast<int64_t>(value);
}
```
**解读**:
- 第 140-146 行: 获取当前时间戳（毫秒）
  - 使用 C++11 chrono 库

---

## 7. mf_num_util.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_num_util.h](../../src/util/csrc/mf_num_util.h)
- **代码行数**: 104 行
- **主要功能**: 数值处理工具函数

### 完整代码与逐行解读

```cpp
/*
Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 */
```
**解读**:
- 第 1-4 行: 版权声明

```cpp
#ifndef MEMFABRIC_NUM_UTIL_H
#define MEMFABRIC_NUM_UTIL_H
```
**解读**:
- 第 4-5 行: 头文件保护宏

```cpp
#include <type_traits>
#include <limits>
#include <string>
#include <cctype>
#include <cstdint>
```
**解读**:
- 第 7-11 行: 引入标准库头文件

```cpp
namespace ock {
namespace mf {
template<typename T>
struct IsUnsignedNumber {
    static constexpr bool value = std::is_same<T, unsigned short>::value || std::is_same<T, unsigned int>::value ||
                                  std::is_same<T, unsigned long>::value || std::is_same<T, unsigned long long>::value;
};
```
**解读**:
- 第 13-19 行: 类型特征模板，判断类型是否为无符号整数类型

```cpp
class NumUtil {
public:
    /**
     * @brief Check whether an arithmetic operation will overflow
     *
     * checks potential overflow in addition and multiplication
     *
     * @tparam T      Numeric type (integral)
     * @param a       [in] first operand
     * @param b       [in] second operand
     * @param calc    [in] operation type: '+' for addition, '*' for multiplication
     * @return true if the operation overflow, false otherwise
     */
    template<typename T>
    static bool IsOverflowCheck(T a, T b, T max, char calc);
```
**解读**:
- 第 21-35 行: 溢出检查方法声明

```cpp
    /**
     * @brief Check whether the input string is all digits
     *
     * @param str input string
     * @return true if the input is all digits else false
     */
    static bool IsDigit(const std::string &str);
```
**解读**:
- 第 36-43 行: 检查字符串是否全是数字

```cpp
    /**
    * Extracts a bit field from the given flag value.
    *
    * @param flag        The 32-bit source value.
    * @param startBit    The starting bit position (0-based, 0 = least significant bit).
    * @param bitLength   The number of bits to extract (1 to 32).
    * @return            extraction flags value
    */
    static uint32_t ExtractBits(uint32_t flag, uint8_t startBit, uint8_t bitLength)
    {
        if (startBit >= UINT32_WIDTH) {
            return UINT32_MAX;
        }
        if (bitLength == 0 || bitLength >= UINT32_WIDTH) {
            return UINT32_MAX;
        }
        if (startBit + bitLength > UINT32_WIDTH) {
            return UINT32_MAX;
        }

        return (flag >> startBit) & ((1U << bitLength) - 1);
    }
};
```
**解读**:
- 第 45-67 行: `ExtractBits` 方法，从标志值中提取位域
  - 第 51-52 行: 检查起始位是否越界
  - 第 53-55 行: 检查位长度是否有效
  - 第 56-58 行: 检查起始位+长度是否越界
  - 第 59 行: 执行位提取：先右移 startBit 位，再与掩码进行与操作

```cpp
template<typename T>
inline bool NumUtil::IsOverflowCheck(T a, T b, T max, char calc)
{
    if (!(IsUnsignedNumber<T>::value)) {
        return false;
    }
    switch (calc) {
        case '+':
            return (a > max - b);
        case '*':
            return ((b != 0) && (a > max / b));
        default:
            return true;
    }
}
```
**解读**:
- 第 69-83 行: 溢出检查模板函数实现
  - 第 72-73 行: 只支持无符号数
  - 第 76 行: 加法溢出检查：如果 `a > max - b`，则 `a + b` 会溢出
  - 第 78 行: 乘法溢出检查：如果 `a > max / b`，则 `a * b` 会溢出

```cpp
inline bool NumUtil::IsDigit(const std::string &str)
{
    if (str.empty()) {
        return false;
    }
    size_t start = str.find_first_not_of(" \t");
    if (start == std::string::npos) {
        return false;
    }

    for (size_t i = start; i < str.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(str[i]))) {
            return false;
        }
    }
    return true;
}
```
**解读**:
- 第 85-101 行: 检查字符串是否全是数字
  - 跳过前导空格和制表符
  - 逐个字符检查是否为数字

---

## 8. mf_net.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_net.h](../../src/util/csrc/mf_net.h)
- **代码行数**: 95 行
- **主要功能**: 网络地址结构定义和哈希函数

### 完整代码与逐行解读

```cpp
/*
Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 */

#ifndef MF_NET_H
#define MF_NET_H
```
**解读**:
- 第 1-6 行: 版权声明和头文件保护

```cpp
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstring>
#include <functional>
#include <cstdint>
```
**解读**:
- 第 8-13 行: 引入网络相关头文件

```cpp
namespace ock {
namespace mf {
enum IpType {
    IpV4,
    IpV6,
    IPNONE,
};
```
**解读**:
- 第 15-21 行: IP 地址类型枚举

```cpp
struct net_addr_t {
    union {
        struct in_addr ipv4;
        struct in6_addr ipv6;
    } ip{};
    IpType type{IPNONE};
```
**解读**:
- 第 23-30 行: 网络地址结构体
  - 使用 union 存储 IPv4 或 IPv6 地址
  - 类型字段标识地址类型

```cpp
    net_addr_t() : type(IPNONE) {}

    static net_addr_t from_ipv4(const struct in_addr &addr)
    {
        net_addr_t result;
        result.type = IpV4;
        result.ip.ipv4 = addr;
        return result;
    }

    static net_addr_t from_ipv6(const struct in6_addr &addr)
    {
        net_addr_t result;
        result.type = IpV6;
        result.ip.ipv6 = addr;
        return result;
    }
```
**解读**:
- 第 30-47 行: 构造函数和静态工厂方法
  - `from_ipv4`: 从 IPv4 地址创建结构体
  - `from_ipv6`: 从 IPv6 地址创建结构体

```cpp
    bool operator==(const net_addr_t &other) const
    {
        if (type != other.type)
            return false;

        if (type == IpV4) {
            return ip.ipv4.s_addr == other.ip.ipv4.s_addr;
        } else if (type == IpV6) {
            return std::memcmp(&ip.ipv6, &other.ip.ipv6, sizeof(struct in6_addr)) == 0;
        }

        return true;
    }
};
```
**解读**:
- 第 48-61 行: 相等运算符重载

```cpp
} // namespace mf
} // namespace ock
namespace std {
template<>
struct hash<ock::mf::net_addr_t> {
    size_t operator()(const ock::mf::net_addr_t &addr) const
    {
        size_t result = 0;

        hash_combine(result, static_cast<int>(addr.type));

        if (addr.type == ock::mf::IpV4) {
            hash_combine(result, addr.ip.ipv4.s_addr);
        } else if (addr.type == ock::mf::IpV6) {
            const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&addr.ip.ipv6);
            for (size_t i = 0; i < sizeof(struct in6_addr); ++i) {
                hash_combine(result, bytes[i]);
            }
        }

        return result;
    }

private:
    static void hash_combine(size_t &seed, size_t value)
    {
        constexpr size_t SHIFT_LEFT = 6;
        constexpr size_t SHIFT_RIGHT = 2;
        seed ^= value + 0x9e3779b9 + (seed << SHIFT_LEFT) + (seed >> SHIFT_RIGHT);
    }
};
} // namespace std
```
**解读**:
- 第 64-93 行: 为 `net_addr_t` 特化 `std::hash`，使其可用于哈希容器
  - `hash_combine`: 哈希组合函数，使用 Boost 风格的哈希组合算法
  - 0x9e3779b9: 黄金比例分数相关的常数

---

## 9. mf_ipv4_validator.h

由于此文件较长（354 行），这里只解读核心部分：

### 文件信息
- **文件路径**: [src/util/csrc/mf_ipv4_validator.h](../../src/util/csrc/mf_ipv4_validator.h)
- **代码行数**: 354 行
- **主要功能**: IPv4 地址和端口验证、Socket 地址解析

### 主要类

1. **Ipv4PortValidator**: 验证 IPv4:Port 格式字符串
2. **SocketAddressParser**: 解析 TCP URL（如 `tcp://192.168.1.1:8080`）
3. **SocketAddressParserMgr**: 管理多个地址解析器的单例

---

## 10. mf_file_util.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_file_util.h](../../src/util/csrc/mf_file_util.h)
- **代码行数**: 403 行
- **主要功能**: 文件操作工具函数

### 主要方法

| 方法 | 功能 |
|------|------|
| `Exist()` | 检查文件或目录是否存在 |
| `Readable()` | 检查是否可读 |
| `Writable()` | 检查是否可写 |
| `ReadAndWritable()` | 检查是否可读可写 |
| `MakeDir()` | 创建目录 |
| `MakeDirRecursive()` | 递归创建目录 |
| `Remove()` | 删除文件或空目录 |
| `RemoveDirRecursive()` | 递归删除目录 |
| `Realpath()` | 获取真实路径（规范化） |
| `GetFileSize()` | 获取文件大小 |
| `IsFile()` | 检查是否为普通文件 |
| `IsDir()` | 检查是否为目录 |

### 关键代码解读

```cpp
inline bool FileUtil::Realpath(std::string &path)
{
    if (path.empty() || path.size() > PATH_MAX_LIMIT) {
        return false;
    }

    /* It will allocate memory to store path */
    char *tmp = new (std::nothrow) char[ock::mf::FileUtil::GetSafePathMax() + 1];
    if (tmp == nullptr) {
        return false;
    }
    char *realPath = realpath(path.c_str(), tmp);
    if (realPath == nullptr) {
        delete[] tmp;
        return false;
    }

    path = realPath;
    realPath = nullptr;
    delete[] tmp;
    return true;
}
```
**解读**:
- 使用 `realpath` 系统调用获取规范化的绝对路径
- `realpath` 会解析符号链接、处理 `.` 和 `..`
- 返回的路径不含冗余的 `/`，是绝对路径

---

## 11. mf_out_logger.h

### 文件信息
- **文件路径**: [src/util/csrc/mf_out_logger.h](../../src/util/csrc/mf_out_logger.h)
- **代码行数**: 220 行
- **主要功能**: 日志输出工具

### 主要组件

#### 日志级别枚举
```cpp
enum LogLevel : int {
    DEBUG_LEVEL = 0,
    INFO_LEVEL,
    WARN_LEVEL,
    ERROR_LEVEL,
    FATAL_LEVEL,
    BUTT_LEVEL // no use
};
```

#### OutLogger 类
- 单例模式
- 支持外部日志函数注入
- 支持日志级别控制
- 自动添加时间戳、进程ID、线程ID

#### 日志宏
```cpp
#define MF_OUT_LOG(TAG, LEVEL, ARGS)                                                  \
    do {                                                                              \
        if (static_cast<int>(LEVEL) < ock::mf::OutLogger::Instance().GetLogLevel()) { \
            break;                                                                    \
        }                                                                             \
        std::ostringstream oss;                                                       \
        oss << (TAG) << MF_LOG_FORMAT << ARGS;                                        \
        ock::mf::OutLogger::Instance().Log(static_cast<int>(LEVEL), oss.str());       \
    } while (0)
```

**解读**:
- 使用 `do { ... } while(0)` 包装宏，确保宏展开后作为语句使用时安全
- 检查日志级别，只输出高于当前级别的日志
- 使用 `std::ostringstream` 构建日志消息
- `MF_LOG_FORMAT`: 包含文件名、行号、函数名的格式化字符串

### 使用示例
```cpp
// 设置日志级别
ock::mf::OutLogger::Instance().SetLogLevel(ock::mf::DEBUG_LEVEL);

// 输出日志
MF_OUT_LOG("[TAG]", ock::mf::DEBUG_LEVEL, "This is a debug message: " << value);
```

---

## 总结

util 模块提供了项目的基础设施，包括：

1. **同步原语**: 自旋锁、读写锁
2. **时间工具**: 单调时间获取、性能追踪
3. **字符串工具**: trim、split、类型转换
4. **数值工具**: 溢出检查、位提取
5. **网络工具**: 地址解析、验证
6. **文件工具**: 路径操作、文件检查
7. **日志工具**: 统一日志输出

这些工具被项目中的所有其他模块使用。
