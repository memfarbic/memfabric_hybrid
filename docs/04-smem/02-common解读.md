# smem/common 模块逐行解读

## 模块概述

smem/common 是 SMEM 模块的公共组件层，提供日志系统、错误处理、引用计数、类型定义等基础设施。这些组件被 SMEM 模块的所有其他子模块依赖。

### 目录结构

| 文件名 | 行数 | 功能描述 |
|--------|------|----------|
| smem_common_includes.h | 40 | 公共头文件聚合声明 |
| smem_define.h | 57 | 核心宏定义 |
| smem_logger.h | 112 | 日志宏定义 |
| smem_types.h | 61 | 类型定义和错误码 |
| smem_ref.h | 182 | 引用计数智能指针 |
| smem_timedwait.h | 150 | 超时等待机制 |
| smem_last_error.h | 74 | 错误处理类 |
| smem_last_error.cpp | 20 | 错误处理实现 |
| smem_version.h | 40+ | 版本信息 |

---

## 1. smem_define.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_define.h`
**代码行数**: 57 行

### 头文件保护与命名空间 (第 1-16 行)

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
- 第 1-11 行: 版权与许可证声明，采用 Mulan PSL v2 开源许可证

```cpp
#ifndef MEM_FABRIC_HYBRID_SMEM_DEFINE_H
#define MEM_FABRIC_HYBRID_SMEM_DEFINE_H

namespace ock {
namespace smem {
```
**逐行解读**:
- 第 12-13 行: 头文件保护宏
- 第 15-16 行: 进入 `ock::smem` 命名空间

### 分支预测优化宏 (第 17-24 行)

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
- 第 17 行: 注释说明用于 GCC 分支预测优化
- 第 18-20 行: LIKELY 宏，告诉编译器条件很可能为真
  - `__builtin_expect` 是 GCC 内置函数
  - `!!(x)` 将 x 转换为 0 或 1
- 第 22-24 行: UNLIKELY 宏，告诉编译器条件很可能为假

### 错误设置宏 (第 26-39 行)

```cpp
#define SM_SET_LAST_ERROR(msg)                     \
    do {                                           \
        std::stringstream tmpStr;                  \
        tmpStr << (msg);                           \
        ock::smem::SmLastError::Set(tmpStr.str()); \
    } while (0)
```
**逐行解读**:
- 第 26-31 行: SM_SET_LAST_ERROR 宏，设置最后一个错误信息
  - 第 28 行: 创建 stringstream 临时对象
  - 第 29 行: 将 msg 输出到流
  - 第 30 行: 调用 SmLastError::Set 设置错误信息

```cpp
#define SM_COUT_AND_SET_LAST_ERROR(msg)            \
    do {                                           \
        std::stringstream tmpStr;                  \
        tmpStr << (msg);                           \
        ock::smem::SmLastError::Set(tmpStr.str()); \
        std::cout << (msg) << std::endl;           \
    } while (0)
```
**逐行解读**:
- 第 33-39 行: SM_COUT_AND_SET_LAST_ERROR 宏，设置错误并输出到标准输出
  - 第 38 行: 使用 std::cout 输出消息
  - 第 38 行: 换行符刷新输出

### 参数校验宏 (第 41-49 行)

```cpp
// if expression is true, print error
#define SM_PARAM_VALIDATE(expression, msg, returnValue) \
    do {                                                \
        if ((expression)) {                             \
            SM_SET_LAST_ERROR(msg);                     \
            SM_LOG_ERROR(msg);                          \
            return returnValue;                         \
        }                                               \
    } while (0)
```
**逐行解读**:
- 第 42 行: 注释说明，表达式为 true 时打印错误
- 第 43-49 行: SM_PARAM_VALIDATE 宏
  - 第 44 行: 判断表达式是否为真
  - 第 45 行: 设置错误信息
  - 第 46 行: 记录错误日志
  - 第 47 行: 返回指定值

### API 导出宏 (第 51 行)

```cpp
#define SMEM_API __attribute__((visibility("default")))
```
**逐行解读**:
- 第 51 行: SMEM_API 宏，标记为动态库导出符号

---

## 2. smem_logger.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_logger.h`
**代码行数**: 112 行

### 头文件引用 (第 1-26 行)

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明

```cpp
#include <cstring>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <sys/syscall.h>
#include <sys/time.h>
#include <unistd.h>
#include "mf_out_logger.h"
#include "smem_last_error.h"
```
**逐行解读**:
- 第 16 行: 引入 c 字符串操作
- 第 17 行: 引入时间操作
- 第 18 行: 引入输入输出操纵器
- 第 19 行: 引入标准输入输出流
- 第 20 行: 引入互斥锁
- 第 21 行: 引入字符串流
- 第 22 行: 引入系统调用接口
- 第 23 行: 引入时间结构体
- 第 24 行: 引入 UNIX 标准函数
- 第 25 行: 引入日志工具
- 第 26 行: 引入错误处理

### 日志宏定义 (第 28-32 行)

```cpp
#define SM_LOG_DEBUG(ARGS)      MF_OUT_LOG("[SMEM ", ock::mf::DEBUG_LEVEL, ARGS)
#define SM_LOG_INFO(ARGS)       MF_OUT_LOG("[SMEM ", ock::mf::INFO_LEVEL, ARGS)
#define SM_LOG_WARN(ARGS)       MF_OUT_LOG("[SMEM ", ock::mf::WARN_LEVEL, ARGS)
#define SM_LOG_WARN_LIMIT(ARGS) MF_OUT_LOG_LIMIT("[SMEM ", ock::mf::MF_OUT_LOG_LIMIT_PREFIX "[SMEM ", ock::mf::WARN_LEVEL, ARGS)
#define SM_LOG_ERROR(ARGS)      MF_OUT_LOG("[SMEM ", ock::mf::ERROR_LEVEL, ARGS)
```
**逐行解读**:
- 第 28 行: DEBUG 级别日志宏，添加 "[SMEM" 前缀
- 第 29 行: INFO 级别日志宏
- 第 30 行: WARN 级别日志宏
- 第 31 行: 带限流的 WARN 日志宏
- 第 32 行: ERROR 级别日志宏

### 断言宏定义 (第 34-84 行)

```cpp
#define SM_CHECK_CONDITION_RET(condition, RET) \
    do {                                       \
        if (condition) {                       \
            return RET;                        \
        }                                      \
    } while (0)
```
**逐行解读**:
- 第 34-39 行: SM_CHECK_CONDITION_RET 宏
  - 第 35 行: 判断条件
  - 第 37 行: 条件为真时返回

```cpp
// if ARGS is false, print error
#define SM_ASSERT_RETURN(ARGS, RET)              \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            SM_LOG_ERROR("Assert " << #ARGS);    \
            return RET;                          \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 41 行: 注释，ARGS 为 false 时打印错误
- 第 42-47 行: SM_ASSERT_RETURN 宏
  - 第 43 行: 使用 UNLIKELY 优化分支预测
  - 第 44 行: 记录断言错误日志
  - 第 45 行: 返回指定值

```cpp
#define SM_LOG_AND_SET_LAST_ERROR(msg)             \
    do {                                           \
        std::stringstream tmpStr;                  \
        tmpStr << msg;                             \
        ock::smem::SmLastError::Set(tmpStr.str()); \
        SM_LOG_ERROR(tmpStr.str());                \
    } while (0)
```
**逐行解读**:
- 第 49-55 行: SM_LOG_AND_SET_LAST_ERROR 宏
  - 同时设置错误信息并记录日志

```cpp
#define SM_VALIDATE_RETURN(ARGS, msg, RET)       \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            SM_LOG_AND_SET_LAST_ERROR(msg);      \
            return RET;                          \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 57-63 行: SM_VALIDATE_RETURN 宏
  - 校验失败时设置错误并返回

```cpp
#define SM_ASSERT_RET_VOID(ARGS)                 \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            SM_LOG_ERROR("Assert " << #ARGS);    \
            return;                              \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 65-71 行: SM_ASSERT_RET_VOID 宏
  - void 版本的断言返回宏

```cpp
#define SM_ASSERT_RETURN_NOLOG(ARGS, RET)        \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            return RET;                          \
        }                                        \
    } while (0)
```
****:
- 第 73-78 行: SM_ASSERT_RETURN_NOLOG 宏
  - 不记录日志的断言返回宏

```cpp
#define SM_ASSERT(ARGS)                          \
    do {                                         \
        if (__builtin_expect(!(ARGS), 0) != 0) { \
            SM_LOG_ERROR("Assert " << #ARGS);    \
        }                                        \
    } while (0)
```
**逐行解读**:
- 第 80-85 行: SM_ASSERT 宏
  - 纯日志断言，不返回

```cpp
#define SM_LOG_ERROR_RETURN_IT_IF_NOT_OK(result, msg) \
    do {                                              \
        auto innerResult = (result);                  \
        if (UNLIKELY(innerResult != 0)) {             \
            SM_LOG_ERROR(msg);                        \
            return innerResult;                       \
        }                                             \
    } while (0)
```
**逐行解读**:
- 第 87-94 行: SM_LOG_ERROR_RETURN_IT_IF_NOT_OK 宏
  - 检查结果并返回错误码

```cpp
#define SM_RETURN_IT_IF_NOT_OK(result)    \
    do {                                  \
        auto innerResult = (result);      \
        if (UNLIKELY(innerResult != 0)) { \
            return innerResult;           \
        }                                 \
    } while (0)
```
**逐行解读**:
- 第 96-102 行: SM_RETURN_IT_IF_NOT_OK 宏
  - 不记录日志的结果检查宏

```cpp
#define SM_LOG_LIMIT_WARN(limit, msg) \
    do {                              \
        static uint32_t printCnt = 0; \
        if (printCnt++ == (limit)) {  \
            SM_LOG_WARN(msg);         \
            printCnt -= limit;        \
        }                             \
    } while (0)
```
**逐行解读**:
- 第 104-111 行: SM_LOG_LIMIT_WARN 限流警告宏
  - 第 106 行: 静态计数器
  - 第 107 行: 每第 limit 次打印一次
  - 第 109 行: 重置计数器

---

## 3. smem_last_error.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_last_error.h`
**代码行数**: 74 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明

```cpp
#ifndef MEMFABRIC_HYBRID_SMEM_LAST_ERROR_H
#define MEMFABRIC_HYBRID_SMEM_LAST_ERROR_H

#include <string>

namespace ock {
namespace smem {
```
**逐行解读**:
- 第 12-14 行: 头文件保护
- 第 15 行: 引入 string 头文件
- 第 17-19 行: 进入命名空间

### SmLastError 类定义 (第 19-71 行)

```cpp
class SmLastError {
public:
    /**
     * @brief Set last error string
     *
     * @param msg          [in] last error message
     */
    static void Set(const std::string &msg);

    /**
     * @brief Set last error string
     *
     * @param msg          [in] last error message
     */
    static void Set(const char *msg);

    /**
     * @brief Get and clear last error messaged
     *
     * @return err string if there is, and clear it
     */
    static const char *GetAndClear(bool clear);
```
**逐行解读**:
- 第 19-45 行: SmLastError 类声明
  - 第 26 行: Set 方法重载（std::string 版本）
  - 第 33 行: Set 方法重载（const char* 版本）
  - 第 40 行: GetAndClear 方法，返回错误信息并可选择清除

```cpp
private:
    static thread_local bool have_;
    static thread_local std::string msg_;
};
```
**逐行解读**:
- 第 43-44 行: 私有静态成员
  - have_: 是否有错误标志
  - msg_: 错误消息内容
  - 使用 thread_local 确保线程安全

### 内联函数实现 (第 47-71 行)

```cpp
inline void SmLastError::Set(const std::string &msg)
{
    msg_ = msg;
    have_ = true;
}
```
**逐行解读**:
- 第 47-51 行: Set 方法实现（std::string 版本）
  - 第 49 行: 赋值错误消息
  - 第 50 行: 设置有错误标志

```cpp
inline void SmLastError::Set(const char *msg)
{
    msg_ = msg;
    have_ = true;
}
```
**逐行行读**:
- 第 53-57 行: Set 方法实现（const char* 版本）
  - 第 55 行: 赋值错误消息
  - 第 56 行: 设置有错误标志

```cpp
inline const char *SmLastError::GetAndClear(bool clear)
{
    /* have last error, just set the flag to false */
    if (have_) {
        have_ = !clear;
        return msg_.c_str();
    }

    /* empty string */
    static std::string emptyString;

    return emptyString.c_str();
}
```
**逐行解读**:
- 第 59-71 行: GetAndClear 方法实现
  - 第 62 行: 检查是否有错误
  - 第 63 行: 根据参数决定是否清除标志
  - 第 64 行: 返回错误消息的 C 字符串指针
  - 第 68-70 行: 无错误时返回空字符串

---

## 4. smem_types.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_types.h`
**代码行数**: 61 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明

```cpp
#ifndef MEMFABRIC_HYBRID_SMEM_TYPES_H
#define MEMFABRIC_HYBRID_SMEM_TYPES_H

#include <cstdint>

namespace ock {
namespace smem {
using Result = int32_t;
```
**逐行解读**:
- 第 13-14 行: 头文件保护
- 第 16 行: 引入整型头文件
- 第 19-20 行: 进入命名空间，定义 Result 类型别名

### 错误码枚举 (第 22-37 行)

```cpp
enum SMErrorCode : int32_t {
    SM_OK = 0,
    SM_ERROR = -1,
    SM_INVALID_PARAM = -2000,
    SM_MALLOC_FAILED = -2001,
    SM_NEW_OBJECT_FAILED = -2002,
    SM_NOT_STARTED = -2003,
    SM_TIMEOUT = -2004,
    SM_REPEAT_CALL = -2005,
    SM_DUPLICATED_OBJECT = -2006,
    SM_OBJECT_NOT_EXISTS = -2007,
    SM_NOT_INITIALIZED = -2008,
    SM_RESOURCE_IN_USE = -2009,
    SM_RECONNECT = -2010,
    SM_GET_OBJIECT = -2011,
};
```
**逐行解读**:
- 第 22-37 行: 错误码枚举定义
  - SM_OK (0): 成功
  - SM_ERROR (-1): 通用错误
  - SM_INVALID_PARAM (-2000): 无效参数
  - SM_MALLOC_FAILED (-2001): 内存分配失败
  - SM_NEW_OBJECT_FAILED (-2002): 对象创建失败
  - SM_NOT_STARTED (-2003): 未启动
  - SM_TIMEOUT (-2004): 超时
  - SM_REPEAT_CALL (-2005): 重复调用
  - SM_DUPLICATED_OBJECT (-2006): 对象重复
  - SM_OBJECT_NOT_EXISTS (-2007): 对象不存在
  - SM_NOT_INITIALIZED (-2008): 未初始化
  - SM_RESOURCE_IN_USE (-2009): 资源占用中
  - SM_RECONNECT (-2010): 需要重连
  - SM_GET_OBJIECT (-2011): 获取对象错误

### 常量定义 (第 39-56 行)

```cpp
constexpr int32_t N16 = 16;
constexpr int32_t N64 = 64;
constexpr int32_t N256 = 256;
constexpr int32_t N1024 = 1024;
constexpr int32_t N8192 = 8192;
const uint32_t REGISTER_WAIT_TIME = 8;

constexpr uint32_t UN2 = 2;
constexpr uint32_t UN32 = 32;
constexpr uint32_t UN58 = 58;
constexpr uint32_t UN128 = 128;
constexpr uint32_t UN65536 = 65536;
constexpr uint32_t UN16777216 = 16777216;

constexpr uint32_t SMEM_DEFAUT_WAIT_TIME = 120; // 120s
constexpr uint32_t SMEM_ID_MAX = 63;
constexpr uint64_t SMEM_LOCAL_HBM_SIZE_MAX = 64ULL << 30; // 64G
constexpr uint64_t SMEM_LOCAL_DRAM_SIZE_MAX = 2ULL << 40; // 2T
```
**逐行解读**:
- 第 39-44 行: 常用数字常量
- 第 45 行: 注册等待时间 8 (单位未明确)
- 第 47-51 行: 未命名的常量值
- 第 53 行: 默认超时时间 120 秒
- 第 54 行: 最大 ID 值 63
- 第 55 行: 本地 HBM 最大 64GB (64 << 30)
- 第 56 行: 本地 DRAM 最大 2TB (2 << 40)

---

## 5. smem_ref.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_ref.h`
**代码行数**: 182 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明

```cpp
#ifndef MEMFABRIC_HYBRID_SMEM_REF_H
#define MEMFABRIC_HYBRID_SMEM_REF_H

#include <cstdint>

namespace ock {
namespace smem {
```
**逐行解读**:
- 第 13-14 行: 头文件保护
- 第 16 行: 引入整型头文件
- 第 18-19 行: 进入命名空间

### SmReferable 基类 (第 21-41 行)

```cpp
class SmReferable {
public:
    SmReferable() = default;
    virtual ~SmReferable() = default;

    inline void IncreaseRef()
    {
        __sync_fetch_and_add(&mRefCount, 1);
    }

    inline void DecreaseRef()
    {
        // delete itself if reference count equal to 0
        if (__sync_sub_and_fetch(&mRefCount, 1) == 0) {
            delete this;
        }
    }

protected:
    int32_t mRefCount = 0;
};
```
**逐行解读**:
- 第 21-41 行: SmReferable 引用计数基类
  - 第 23 行: 默认构造函数
  - 第 24 行: 虚析构函数
  - 第 26-29 行: IncreaseRef 方法，原子增加引用计数
    - `__sync_fetch_and_add` 是 GCC 原子操作内置函数
  - 第 31-37 行: DecreaseRef 方法，原子减少引用计数，计数为 0 时自删除
  - 第 40 行: 保护成员，引用计数

### SmRef 智能指针模板 (第 43-162 行)

```cpp
template<typename T>
class SmRef {
public:
    // constructor
    SmRef() noexcept = default;
```
**逐行解读**:
- 第 43-47 行: SmRef 智能指针模板类
  - 第 46 行: 默认构造函数

```cpp
    // fix: can't be explicit
    SmRef(T *newObj) noexcept
    {
        // if new obj is not null, increase reference count and assign to mObj
        // else nothing need to do as mObj is nullptr by default
        if (newObj != nullptr) {
            newObj->IncreaseRef();
            mObj = newObj;
        }
    }
```
**逐行解读**:
- 第 49-58 行: 指针构造函数
  - 第 50 行: 注释说明不能是 explicit（允许隐式转换）
  - 第 54 行: 如果新对象非空，增加引用计数
  - 第 55 行: 赋值给成员变量

```cpp
    SmRef(const SmRef<T> &other) noexcept
    {
        // if other's obj is not null, increase reference count and assign to mObj
        // else nothing need to do as mObj is nullptr by default
        if (other.mObj != nullptr) {
            other.mObj->IncreaseRef();
            mObj = other.mObj;
        }
    }
```
**逐行解读**:
- 第 60-68 行: 拷贝构造函数
  - 增加原对象的引用计数并赋值

```cpp
    SmRef(SmRef<T> &&other) noexcept : mObj(std::__exchange(other.mObj, nullptr))
    {
        // move constructor
        // since this mObj is null, just exchange
    }
```
**逐行解读**:
- 第 70-74 行: 移动构造函数
  - 使用 `std::__exchange` 交换指针，原对象的 mObj 变为 nullptr

```cpp
    // de-constructor
    ~SmRef()
    {
        if (mObj != nullptr) {
            mObj->DecreaseRef();
        }
    }
```
**逐行解读**:
- 第 76-82 行: 析构函数
  - 如果有对象，减少引用计数

```cpp
    // operator =
    inline SmRef<T> &operator=(T *newObj)
    {
        this->Set(newObj);
        return *this;
    }

    inline SmRef<T> &operator=(const SmRef<T> &other)
    {
        if (this != &other) {
            this->Set(other.mObj);
        }
        return *this;
    }

    SmRef<T> &operator=(SmRef<T> &&other) noexcept
    {
        if (this != &other) {
            auto tmp = mObj;
            mObj = std::__exchange(other.mObj, nullptr);
            if (tmp != nullptr) {
                tmp->DecreaseRef();
            }
        }
        return *this;
    }
```
**逐行解读**:
- 第 84-109 行: 赋值运算符重载
  - 第 85-89 行: 指针赋值运算符
  - 第 91-97 行: 拷贝赋值运算符
  - 第 99-109 行: 移动赋值运算符

```cpp
    // equal operator
    inline bool operator==(const SmRef<T> &other) const
    {
        return mObj == other.mObj;
    }

    inline bool operator==(T *other) const
    {
        return mObj == other;
    }

    inline bool operator!=(const SmRef<T> &other) const
    {
        return mObj != other.mObj;
    }

    inline bool operator!=(T *other) const
    {
        return mObj != other;
    }
```
**逐行解读**:
- 第 111-130 行: 相等与不等比较运算符

```cpp
    // get operator and set
    inline T *operator->() const
    {
        return mObj;
    }

    inline T *Get() const
    {
        return mObj;
    }

    inline void Set(T *newObj)
    {
        if (newObj == mObj) {
            return;
        }

        if (newObj != nullptr) {
            newObj->IncreaseRef();
        }

        if (mObj != nullptr) {
            mObj->DecreaseRef();
        }

        mObj = newObj;
    }

private:
    T *mObj = nullptr;
};
```
**逐行解读**:
- 第 132-158 行: 箭头运算符、Get 方法、Set 方法
  - 第 133-136 行: 箭头运算符，返回对象指针
  - 第 138-141 行: Get 方法，返回对象指针
  - 第 143-158 行: Set 方法，线程安全的指针设置

### 辅助函数 (第 164-178 行)

```cpp
template<class Src, class Des>
SmRef<Des> inline Convert(const SmRef<Src> &child)
{
    Des *converted = dynamic_cast<Des *>(child.Get());
    if (converted) {
        return SmRef<Des>(converted);
    }
    return nullptr;
}

template<typename C, typename... ARGS>
inline SmRef<C> SmMakeRef(ARGS... args)
{
    return new (std::nothrow) C(args...);
}
```
**逐行解读**:
- 第 164-172 行: Convert 类型转换函数模板
  - 使用 dynamic_cast 进行向下转型
- 第 174-178 行: SmMakeRef 工厂函数模板
  - 使用 placement new 创建对象

---

## 6. smem_timedwait.h 逐行解读

**文件路径**: `src/smem/csrc/common/smem_timedwait.h`
**代码行数**: 150 行

```cpp
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.
 * ...
*/
```
**逐行解读**:
- 第 1-11 行: 版权声明

```cpp
#ifndef MEM_FABRIC_HYBRID_SMEM_TIMEDWAIT_H
#define MEM_FABRIC_HYBRID_SMEM_TIMEDWAIT_H

#include <mutex>
#include <functional>
#include "smem_types.h"

constexpr uint64_t SECOND_TO_MILLSEC = 1000U;
constexpr uint64_t MILLSEC_TO_NANOSEC = 1000000U;
constexpr uint64_t SECOND_TO_NANOSEC = 1000000000U;
```
**逐行解读**:
- 第 13-22 行: 头文件保护和引入
- 第 20 行: 1秒 = 1000毫秒
- 第 21 行: 1毫秒 = 1000000纳秒
- 第 22 行: 1秒 = 1000000000纳秒

```cpp
namespace ock {
namespace smem {
class SmemTimedwait { // wait signal or overtime, instead of sem_timedwait
public:
    SmemTimedwait() = default;
    ~SmemTimedwait()
    {
        if (inited_) {
            pthread_condattr_destroy(&cattr_);
            pthread_cond_destroy(&condTimeChecker_);
            pthread_mutex_destroy(&timeCheckerMutex_);
        }
    }
```
**逐行解读**:
- 第 26-36 行: SmemTimedwait 类
  - 第 26 行: 注释说明，替代 sem_timedwait
  - 第 27 行: 默认构造函数
  - 第 28-36 行: 析构函数，销毁 pthread 资源

```cpp
    Result Initialize()
    {
        if (inited_) {
            return SM_OK;
        }
        signalFlag = false;
        int32_t attrInitRet = pthread_condattr_init(&cattr_);
        if (attrInitRet != 0) {
            return SM_ERROR;
        }

        int32_t setClockRet = pthread_condattr_setclock(&cattr_, CLOCK_MONOTONIC);
        if (setClockRet != 0) {
            pthread_condattr_destroy(&cattr_);
            return SM_ERROR;
        }

        int32_t condInitRet = pthread_cond_init(&condTimeChecker_, &cattr_);
        if (condInitRet != 0) {
            pthread_condattr_destroy(&cattr_);
            return SM_ERROR;
        }

        int32_t mutexInitRet = pthread_mutex_init(&timeCheckerMutex_, nullptr);
        if (mutexInitRet != 0) {
            pthread_cond_destroy(&condTimeChecker_);
            pthread_condattr_destroy(&cattr_);
            return SM_ERROR;
        }
        inited_ = true;
        return SM_OK;
    }
```
**逐行解读**:
- 第 38-69 行: Initialize 方法
  - 第 40-42 行: 如果已初始化直接返回
  - 第 43 行: 重置信号标志
  - 第 44-47 行: 初始化条件变量属性
  - 第 49-53 行: 设置时钟为 MONOTONIC（单调时钟）
  - 第 55-59 行: 初始化条件变量
  - 第 61-66 行: 初始化互斥锁
  - 第 68 行: 设置初始化标志
  - 第 69 行: 返回成功

```cpp
    int32_t TimedwaitMillsecs(long msecs, const std::function<void()> &wakeupOp = nullptr)
    {
        struct timespec ts{0, 0};
        int32_t ret = 0;

        pthread_mutex_lock(&this->timeCheckerMutex_);
        if (this->signalFlag && wakeupOp != nullptr) {
            wakeupOp();
            this->signalFlag = false;
            pthread_mutex_unlock(&this->timeCheckerMutex_);
            return SM_OK;
        }

        clock_gettime(CLOCK_MONOTONIC, &ts);

        // avoid ts.tv_nsec overflow
        long secs = msecs / SECOND_TO_MILLSEC;
        msecs = (msecs % SECOND_TO_MILLSEC) * SECOND_TO_MILLSEC * SECOND_TO_MILLSEC + ts.tv_nsec;
        long add = msecs / (SECOND_TO_MILLSEC * SECOND_TO_MILLSEC * SECOND_TO_MILLSEC);
        ts.tv_sec += (add + secs);
        ts.tv_nsec = msecs % (SECOND_TO_MILLSEC * SECOND_TO_MILLSEC * SECOND_TO_MILLSEC);
        while (!this->signalFlag) { // avoid spurious wakeup
            ret = pthread_cond_timedwait(&this->condTimeChecker_, &this->timeCheckerMutex_, &ts);
            if (ret == ETIMEDOUT) { // avoid infinite loop
                ret = SM_OK;
                break;
            }
        }
        this->signalFlag = false;
        if (wakeupOp != nullptr) {
            wakeupOp();
        }
        pthread_mutex_unlock(&this->timeCheckerMutex_);

        return ret;
    }
```
**逐行解读**:
- 第 71-106 行: TimedwaitMillsecs 超时等待方法
  - 第 73-79 行: 检查是否已有信号，有信号则执行回调后返回
  - 第 84 行: 获取当前单调时钟
  - 第 87-91 行: 计算超时时刻，防止纳秒溢出
  - 第 92-98 行: 循环等待信号或超时
  - 第 94-97 行: 超时后跳出循环
  - 第 99-102 行: 执行唤醒回调

```cpp
    void OperateInLock(const std::function<void()> &op, bool notify = false)
    {
        pthread_mutex_lock(&this->timeCheckerMutex_);
        if (op != nullptr) {
            op();
        }
        if (notify) {
            signalFlag = true;
        }
        pthread_mutex_unlock(&this->timeCheckerMutex_);
        if (notify) {
            pthread_cond_signal(&this->condTimeChecker_);
        }
    }
```
**逐行解读**:
- 第 108-121 行: OperateInLock 方法
  - 在锁保护下执行操作
  - 可选通知等待者

```cpp
    // signal will NOT lost when call PthreadSignal before PthreadTimedwaitMillsecs, so we can proactive cleanup
    void SignalClean()
    {
        signalFlag = false;
    }

    int32_t PthreadSignal()
    {
        int32_t signalRet = 0;
        pthread_mutex_lock(&this->timeCheckerMutex_);
        signalFlag = true;
        signalRet = pthread_cond_signal(&this->condTimeChecker_);
        pthread_mutex_unlock(&this->timeCheckerMutex_);
        return signalRet;
    }
```
**逐行解读**:
- 第 123-137 行: 信号相关方法
  - SignalClean: 清除信号标志
  - PthreadSignal: 发送唤醒信号

```cpp
private:
    bool inited_{false};
    pthread_condattr_t cattr_;
    pthread_cond_t condTimeChecker_;
    pthread_mutex_t timeCheckerMutex_;
    bool signalFlag{false}; // signal will NOT lost when call PthreadSignal before PthreadTimedwaitMillsecs
};
```
**逐行解读**:
- 第 139-145 行: 私有成员
  - inited_: 初始化标志
  - cattr_: 条件变量属性
  - condTimeChecker_: 条件变量
  - timeCheckerMutex_: 互斥锁
  - signalFlag: 信号标志

---

## 总结

smem/common 模块为 SMEM 提供了：

1. **错误处理** ([smem_last_error.h/cpp](../../src/smem/csrc/common/smem_last_error.h)): 线程安全的错误信息存储
2. **引用计数** ([smem_ref.h](../../src/smem/csrc/common/smem_ref.h)): SmReferable 基类和 SmRef 智能指针
3. **日志系统** ([smem_logger.h](../../src/smem/csrc/common/smem_logger.h)): 统一的日志宏定义
4. **超时机制** ([smem_timedwait.h](../../src/smem/csrc/common/smem_timedwait.h)): SmemTimedwait 可靠的超时等待
5. **类型定义** ([smem_types.h](../../src/smem/csrc/common/smem_types.h)): 错误码、常量定义
6. **宏工具** ([smem_define.h](../../src/smem/csrc/common/smem_define.h)): 断言、校验、错误设置等便捷宏

**设计亮点**:
- thread_local 实现线程安全的错误存储
- 原子操作的引用计数，无需锁
- CLOCK_MONOTONIC 避免系统时间调整影响
- 信号标志防止信号丢失
