# ACC_Links Common 模块逐行解读

## 模块概述

Common 模块是 ACC_Links 的公共工具模块，提供 IPv4 验证、SSL 关闭助手、环境变量解析、TLS 选项验证等通用功能。

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| acc_common_util.h/cpp | 168 | 公共工具函数 |
| acc_includes.h | - | 公共头文件聚合 |
| acc_file_validator.h/cpp | - | 文件验证器 |
| acc_out_logger.h | - | 日志输出 |

---

## 1. acc_common_util.h/cpp - 公共工具函数

### 文件信息
- 文件路径: `src/acc_links/csrc/common/acc_common_util.h/cpp`
- 代码行数: 168 行
- 主要功能: 提供公共工具函数

### 类定义 (行 26-33)

```cpp
class AccCommonUtil {
public:
    static bool IsValidIPv4(const std::string &ip);
    static Result SslShutdownHelper(SSL *s);
    static uint32_t GetEnvValue2Uint32(const char *envName);
    static bool IsAllDigits(const std::string &str);
    static Result CheckTlsOptions(const AccTlsOption &tlsOption);
};
```

**逐行解读**:
- 第 28 行: `IsValidIPv4` - 验证 IPv4 地址格式
- 第 29 行: `SslShutdownHelper` - SSL 优雅关闭助手
- 第 30 行: `GetEnvValue2Uint32` - 从环境变量获取 uint32 值
- 第 31 行: `IsAllDigits` - 检查字符串是否全为数字
- 第 32 行: `CheckTlsOptions` - 验证 TLS 选项

### IsValidIPv4() - 验证 IPv4 地址 (行 22-30)

```cpp
bool AccCommonUtil::IsValidIPv4(const std::string &ip)
{
    static const std::regex ipv4Regex("^(?:(?:25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)($|(?!\\.$)\\.)){4}$");
    constexpr size_t maxIpv4Len = 15;
    if (ip.size() > maxIpv4Len) {
        return false;
    }
    return std::regex_match(ip, ipv4Regex);
}
```

**逐行解读**:
- 第 24 行: IPv4 正则表达式
  - 格式: `xxx.xxx.xxx.xxx`
  - 每段: 0-255 或 1-9 或空
- 第 25 行: 最大 IPv4 长度（15 字符）
- 第 26-28 行: 检查长度
- 第 29 行: 正则匹配验证

### SslShutdownHelper() - SSL 关闭助手 (行 32-68)

```cpp
Result AccCommonUtil::SslShutdownHelper(SSL *ssl)
{
    if (!ssl) {
        LOG_ERROR("ssl ptr is nullptr");
        return ACC_ERROR;
    }

    const int sslShutdownTimes = 5;
    const int sslRetryInterval = 1; // s
    int ret = OpenSslApiWrapper::SslShutdown(ssl);
    if (ret == 1) {
        return ACC_OK;
    } else if (ret < 0) {
        ret = OpenSslApiWrapper::SslGetError(ssl, ret);
        LOG_ERROR("ssl shutdown failed!, error code is:" << ret);
        return ACC_ERROR;
    } else if (ret != 0) {
        LOG_ERROR("unknown ssl shutdown ret val!");
        return ACC_ERROR;
    }

    for (int i = UNO_1; i <= sslShutdownTimes; ++i) {
        sleep(sslRetryInterval);
        LOG_INFO("ssl showdown retry times:" << i);
        ret = OpenSslApiWrapper::SslShutdown(ssl);
        if (ret == 1) {
            return ACC_OK;
        } else if (ret < 0) {
            LOG_ERROR("ssl shutdown failed!, error code is:" << OpenSslApiWrapper::SslGetError(ssl, ret));
            return ACC_ERROR;
        } else if (ret != 0) {
            LOG_ERROR("unknown ssl shutdown ret val!");
            return ACC_ERROR;
        }
    }
    return ACC_ERROR;
}
```

**逐行解读**:
- 第 34-37 行: SSL 指针检查
- 第 39 行: SSL 关闭重试次数（5 次）
- 第 40 行: 重试间隔（1 秒）
- 第 41 行: 第一次 SSL 关闭
- 第 42-44 行: 返回 1 表示成功
- 第 45-47 行: 负数错误处理
- 第 48-50 行: 未知错误处理
- 第 53-66 行: 重试循环
  - 休眠指定间隔
  - 再次尝试关闭
  - 检查返回值

### GetEnvValue2Uint32() - 获取环境变量 (行 70-85)

```cpp
uint32_t AccCommonUtil::GetEnvValue2Uint32(const char *envName)
{
    // 0 should be illegal for this env variable
    constexpr uint32_t maxUint32Len = 35;
    const char *tmpEnvValue = std::getenv(envName);
    if (tmpEnvValue != nullptr && strlen(tmpEnvValue) <= maxUint32Len && IsAllDigits(tmpEnvValue)) {
        uint32_t envValue = 0;
        std::string str(tmpEnvValue);
        if (!ock::mf::StrUtil::String2Uint(str, envValue)) {
            LOG_ERROR("failed to convert str : " << str << " to uint32_t");
            return 0;
        }
        return envValue;
    }
    return 0;
}
```

**逐行解读**:
- 第 73 行: 最大 uint32 字符串长度（35）
- 第 74 行: 获取环境变量值
- 第 75 行: 验证长度和数字格式
- 第 76-82 行: 转换为 uint32_t
- 第 84 行: 失败或无效则返回 0

### IsAllDigits() - 检查是否全为数字 (行 87-93)

```cpp
bool AccCommonUtil::IsAllDigits(const std::string &str)
{
    if (str.empty()) {
        return false;
    }
    return std::all_of(str.begin(), str.end(), [](unsigned char ch) { return std::isdigit(ch); });
}
```

**逐行解读**:
- 第 89-91 行: 空字符串返回 false
- 第 92 行: 使用 std::all_of 检查是否全为数字

### TLS 选项验证宏 (行 95-165)

```cpp
#define CHECK_FILE_PATH_TLS(key, path)                                                     \
    do {                                                                                   \
        if (ock::mf::FileUtil::IsSymlink(path) || !ock::mf::FileUtil::Realpath(path) ||    \
            !ock::mf::FileUtil::IsFile(path) || !ock::mf::FileUtil::CheckFileSize(path)) { \
            LOG_ERROR("TLS " #key " check failed");                                        \
            return ACC_ERROR;                                                              \
        }                                                                                  \
    } while (0)

#define CHECK_DIR_PATH_TLS(key, path)                                                   \
    do {                                                                                \
        if (ock::mf::FileUtil::IsSymlink(path) || !ock::mf::FileUtil::Realpath(path) || \
            !ock::mf::FileUtil::IsDir(path)) {                                          \
            LOG_ERROR("TLS " #key " check failed");                                     \
            return ACC_ERROR;                                                           \
        }                                                                               \
    } while (0)

Result AccCommonUtil::CheckTlsOptions(const AccTlsOption &tlsOption)
{
    if (!tlsOption.enableTls) {
        return ACC_OK;
    }
    CHECK_DIR_PATH(tlsTopPath, false);
    CHECK_DIR_PATH(tlsCaPath, true);
    CHECK_DIR_PATH(tlsCrlPath, false);
    CHECK_FILE_PATH(tlsCert, true);
    CHECK_FILE_SET(tlsCaFile, tlsOption.tlsTopPath + "/" + tlsOption.tlsCaPath, true);
    CHECK_FILE_SET(tlsCrlFile, tlsOption.tlsTopPath + "/" + tlsOption.tlsCrlPath, false);
    return ACC_OK;
}
```

**逐行解读**:
- 第 95-102 行: 检查文件路径宏
  - 不是符号链接
  - 路径存在
  - 是文件
  - 文件大小合法
- 第 104-122 行: 检查目录路径宏
  - 不是符号链接
  - 路径存在
  - 是目录
- 第 124-141 行: 检查文件集宏
- 第 143-151 行: 检查目录集宏
- 第 153-165 行: `CheckTlsOptions` 函数
  - 检查 TLS 顶层目录（可选）
  - 检查 CA 目录（必需）
  - 检查 CRL 目录（可选）
  - 检查证书文件（必需）
  - 检查 CA 文件集（必需）
  - 检查 CRL 文件集（可选）

---

## 总结

Common 模块提供了 ACC_Links 的公共工具函数：

### 1. IPv4 验证

```
IsValidIPv4()
    ├── 正则表达式匹配
    ├── 检查长度限制（15 字符）
    └── 返回匹配结果
```

### 2. SSL 关闭助手

```
SslShutdownHelper()
    ├── 第一次 SSL_shutdown
    ├── 成功（返回 1）则返回
    ├── 失败则获取错误码
    ├── 重试循环（最多 5 次）
    │   ├── 休眠 1 秒
    │   ├── 再次 SSL_shutdown
    │   └── 检查返回值
    └── 超时返回错误
```

### 3. 环境变量解析

```
GetEnvValue2Uint32()
    ├── 获取环境变量
    ├── 验证长度
    ├── 验证全为数字
    ├── 转换为 uint32_t
    └── 失败返回 0
```

### 4. TLS 选项验证

```
CheckTlsOptions()
    ├── 检查 TLS 顶层目录
    ├── 检查 CA 目录（必需）
    ├── 检查 CRL 目录（可选）
    ├── 检查证书文件（必需）
    ├── 检查 CA 文件集（必需）
    └── 检查 CRL 文件集（可选）
```

### 5. 关键特性

1. **IPv4 验证**: 使用正则表达式严格验证
2. **SSL 优雅关闭**: 支持重试机制
3. **环境变量解析**: 支持字符串到 uint32 的转换
4. **TLS 配置验证**: 完整的证书和密钥路径验证
