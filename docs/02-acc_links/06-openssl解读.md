# ACC_Links OpenSSL 模块逐行解读

## 模块概述

OpenSSL 模块是 ACC_Links 的安全通信底层封装，提供 OpenSSL 库的动态加载和 API 包装器，实现 SSL/TLS 安全通信功能。

### 设计目标
1. **动态加载**: 通过 dlopen 动态加载 OpenSSL 库，避免编译时依赖
2. **API 包装**: 提供统一的 API 接口，屏蔽底层实现细节
3. **安全验证**: 加载前验证库文件的完整性和权限

## 文件列表

| 文件 | 行数 | 主要功能 |
|------|------|---------|
| openssl_api_dl.h | 214 | 动态加载接口定义 |
| openssl_api_dl.cpp | 305 | 动态加载实现 |
| openssl_api_wrapper.h | 501 | API 包装器 |
| openssl_util.h | 20 | 工具函数接口 |
| openssl_util.cpp | 60 | SSL 关闭助手 |

---

## 1. openssl_api_dl.h/cpp - OpenSSL 动态加载

### 文件信息
- 文件路径: `src/acc_links/csrc/under_api/openssl/openssl_api_dl.h/cpp`
- 代码行数: 305 行 (cpp) + 214 行 (h)
- 主要功能: 动态加载 OpenSSL 库并获取函数指针

### 头文件解读 (openssl_api_dl.h)

#### 类型定义 (行 11-28)

```cpp
using OPENSSL_INIT_SETTINGS = struct ossl_init_settings_st;
using SSL_METHOD = struct ssl_method_st;
using SSL = struct ssl_st;
using SSL_CTX = struct ssl_ctx_st;
using X509_STORE_CTX = struct x509_store_ctx_st;
using X509_CRL = struct x509_crl;
using X509_REVOKED = struct x509_revoked;
using ENGINE = struct engine_st;
using EVP_CIPHER = struct evp_cipher_st;
using EVP_CIPHER_CTX = struct evp_cipher_ctx_st;
using SSL_CIPHER = struct ssl_cipher_st;
using X509 = struct x509_st;
using BIO = struct bio;
using PEM_PASSWORD_CB = struct pem_password_cb;
using BIO_METHOD = struct bio_method;
using X509_STORE = struct x509_store;
using ASN1_TIME = struct asn1_string_st;
using EVP_PKEY = struct evp_pkey_st;
```

**逐行解读**:
- 第 11-28 行: 使用前置声明定义 OpenSSL 不透明类型
  - `OPENSSL_INIT_SETTINGS`: OpenSSL 初始化设置
  - `SSL_METHOD`: SSL 方法结构
  - `SSL`: SSL 连接对象
  - `SSL_CTX`: SSL 上下文
  - `X509_*`: X.509 证书相关类型
  - `EVP_*`: 加密相关类型
  - `BIO_*`: I/O 抽象层类型

#### 函数指针类型定义 (行 30-107)

```cpp
// SSL 初始化相关
using FuncInit = int (*)(uint64_t, const OPENSSL_INIT_SETTINGS *);
using FuncOpensslCleanup = void (*)();

// SSL 方法获取
using FuncGetMethod = const SSL_METHOD *(*)(void);

// SSL 操作函数
using FuncSslOperation = int (*)(SSL *);
using FuncSslFd = int (*)(SSL *, int);
using FuncSslNew = SSL *(*)(SSL_CTX *);
using FuncSslFree = void (*)(SSL *);
using FuncSslCtxNew = SSL_CTX *(*)(const SSL_METHOD *);
using FuncSslCtxFree = void (*)(SSL_CTX *);
using FuncSslWrite = int (*)(SSL *, const void *, int);
using FuncSslRead = int (*)(SSL *, void *, int);
using FuncSslGetError = int (*)(const SSL *, int);
using FuncSslWriteEx = int (*)(SSL *, const void *, size_t, size_t *);
using FuncSslReadEx = int (*)(SSL *, void *, size_t, size_t *);

// SSL 上下文控制
using FuncSetCipherSuites = int (*)(SSL_CTX *, const char *);
using FuncSslCtxCtrl = long (*)(SSL_CTX *, int, long, void *);
using FuncSslGetCurrentCipher = const SSL_CIPHER *(*)(const SSL *);
using FuncSslGetVersion = const char *(*)(const SSL *);
using FuncSslIsServer = int (*)(SSL *);

// 证书和私钥
using FuncUsePrivKey = int (*)(SSL_CTX *ctx, EVP_PKEY *pkey);
using FuncUsePrivKeyFile = int (*)(SSL_CTX *ctx, const char *, int);
using FuncUseCertFile = int (*)(SSL_CTX *, const char *, int);
using FuncPemReadX509 = X509 *(*)(FILE * fp, X509 **x, pem_password_cb *cb, void *u);
using FuncX509Free = X509 *(*)(X509 * cert);
using FuncAsn1Time2Tm = int (*)(const ASN1_TIME *s, struct tm *tm);
using FuncSslCtxSetVerify = void (*)(SSL_CTX *, int mode, int (*)(int, X509_STORE_CTX *));
using FuncSetDefaultPasswdCbUserdata = void (*)(SSL_CTX *, void *);
using FuncSetCertVerifyCallback = void (*)(SSL_CTX *, int (*cb)(X509_STORE_CTX *, void *), void *);
using FuncLoadVerifyLocations = int (*)(SSL_CTX *, const char *, const char *);
using FuncCheckPrivateKey = int (*)(const SSL_CTX *);
using FuncSslGetVerifyResult = long (*)(const SSL *);
using FuncSslGetPeerCertificate = X509 *(*)(const SSL *);
using FuncSsLCtxGet0Certificate = X509 *(*)(const SSL_CTX *ctx);

// 加密函数
using FuncEvpAesCipher = const EVP_CIPHER *(*)();
using FuncEvpCipherCtxNew = EVP_CIPHER_CTX *(*)();
using FuncEvpCipherCtxFree = void (*)(EVP_CIPHER_CTX *);
using FuncEvpCipherCtxCtrl = int (*)(EVP_CIPHER_CTX *, int, int, void *);
using FuncEvpEncryptInitEx = int (*)(EVP_CIPHER_CTX *, const EVP_CIPHER *, ENGINE *, const unsigned char *,
                                     const unsigned char *);
using FuncEvpEncryptUpdate = int (*)(EVP_CIPHER_CTX *, unsigned char *, int *, const unsigned char *, int);
using FuncEvpEncryptFinalEx = int (*)(EVP_CIPHER_CTX *, unsigned char *, int *);
using FuncEvpDecryptInitEx = FuncEvpEncryptInitEx;
using FuncEvpDecryptUpdate = FuncEvpEncryptUpdate;
using FuncEvpDecryptFinalEx = FuncEvpEncryptFinalEx;

// 随机数函数
using FuncRandPoll = int (*)(void);
using FuncRandStatus = FuncRandPoll;
using FuncRandBytes = int (*)(unsigned char *buf, int num);
using FuncRandSeed = void (*)(const void *, int);

// X.509 证书验证
using FuncX509VerifyCert = int (*)(X509_STORE_CTX *ctx);
using FuncX509VerifyCertErrorString = const char *(*)(long n);
using FuncX509StoreCtxGetError = int (*)(const X509_STORE_CTX *ctx);
using FuncPemReadBioX509Crl = X509_CRL *(*)(BIO * bp, X509_CRL **x, PEM_PASSWORD_CB *cb, void *u);
using FuncPemReadBioPk = EVP_PKEY *(*)(BIO * bp, EVP_PKEY **x, PEM_PASSWORD_CB *cb, void *u);
using FuncBioSFile = const BIO_METHOD *(*)(void);
using FuncBioNew = BIO *(*)(const BIO_METHOD *);
using FuncBioNewMemBuf = BIO *(*)(const void *buf, int len);
using FuncBioFree = void (*)(BIO *b);
using FuncBioCtrl = long (*)(BIO *bp, int cmd, long larg, void *parg);
using FuncX509StoreCtxGet0Store = X509_STORE *(*)(const X509_STORE_CTX *ctx);
using FuncX509StoreCtxSetFlags = void (*)(X509_STORE_CTX *ctx, unsigned long flags);
using FuncX509StoreAddCrl = int (*)(X509_STORE *xs, X509_CRL *x);
using FuncX509CrlFree = void (*)(X509_CRL *x);

// X.509 时间和公钥
using FuncX509CmpCurrentTime = int (*)(const ASN1_TIME *s);
using FuncX509CrlGet0ByCert = int (*)(X509_CRL *crl, X509_REVOKED **ret, X509 *x);
using FuncX509CrlGet0NextUpdate = const ASN1_TIME *(*)(const X509_CRL *crl);
using FuncX509GetNotAfter = ASN1_TIME *(*)(const X509 *x);
using FuncX509GetNotBefore = ASN1_TIME *(*)(const X509 *x);
using FuncX509GetPubkey = EVP_PKEY *(*)(X509 * x);
using FuncEvpPkeyBits = int (*)(const EVP_PKEY *pkey);
using FuncEvpPkeyFree = void (*)(EVP_PKEY *pkey);
```

**逐行解读**:
- 第 30 行: `FuncInit` - SSL/CRYPTO 初始化函数指针
- 第 31 行: `FuncOpensslCleanup` - OpenSSL 清理函数指针
- 第 32 行: `FuncGetMethod` - 获取 SSL 方法函数指针
- 第 33-43 行: SSL 基本操作函数指针
- 第 45-50 行: SSL 上下文控制函数指针
- 第 52-65 行: 证书和私钥相关函数指针
- 第 67-77 行: 加密操作函数指针
- 第 79-82 行: 随机数生成函数指针
- 第 84-97 行: X.509 证书和 CRL 验证函数指针
- 第 99-106 行: X.509 时间和公钥获取函数指针

#### OPENSSLAPIDL 类定义 (行 108-209)

```cpp
class OPENSSLAPIDL {
public:
    // SSL 初始化函数指针
    static FuncInit initSsl;
    static FuncInit initCypto;
    static FuncOpensslCleanup opensslCleanup;

    // SSL 方法函数指针
    static FuncGetMethod tlsServerMethod;
    static FuncGetMethod tlsClientMethod;
    static FuncGetMethod tlsMethod;

    // SSL 操作函数指针
    static FuncSslOperation sslShutdown;
    static FuncSslFd sslSetFd;
    static FuncSslNew sslNew;
    static FuncSslFree sslFree;
    static FuncSslCtxNew sslCtxNew;
    static FuncSslCtxFree sslCtxFree;
    static FuncSslWrite sslWrite;
    static FuncSslRead sslRead;
    static FuncSslOperation sslConnect;
    static FuncSslOperation sslConnectState;
    static FuncSslOperation sslAccept;
    static FuncSslOperation sslAcceptState;
    static FuncSslOperation sslGetShutdown;
    static FuncSslGetError sslGetError;
    static FuncSslWriteEx sslWriteEx;
    static FuncSslReadEx sslReadEx;

    // SSL 上下文函数指针
    static FuncSslCtxCtrl sslCtxCtrl;
    static FuncSslGetCurrentCipher sslGetCurrentCipher;
    static FuncSslGetVersion sslGetVersion;
    static FuncSslIsServer sslIsServer;
    static FuncSetCipherSuites setCipherSuites;
    static FuncUsePrivKey usePrivKey;
    static FuncUsePrivKeyFile usePrivKeyFile;
    static FuncUseCertFile useCertFile;
    static FuncPemReadX509 pemReadX509;
    static FuncX509Free x509Free;
    static FuncAsn1Time2Tm asn1Time2Tm;
    static FuncSslCtxSetVerify sslCtxSetVerify;
    static FuncSetDefaultPasswdCbUserdata setDefaultPasswdCbUserdata;
    static FuncSetCertVerifyCallback setCertVerifyCallback;
    static FuncLoadVerifyLocations loadVerifyLocations;
    static FuncCheckPrivateKey checkPrivateKey;
    static FuncSslGetVerifyResult sslGetVerifyResult;
    static FuncSslGetPeerCertificate sslGetPeerCertificate;
    static FuncSsLCtxGet0Certificate ssLCtxGet0Certificate;

    // 加密函数指针
    static FuncEvpAesCipher evpAes128Gcm;
    static FuncEvpAesCipher evpAes256Gcm;
    static FuncEvpCipherCtxNew evpCipherCtxNew;
    static FuncEvpCipherCtxFree evpCipherCtxFree;
    static FuncEvpCipherCtxCtrl evpCipherCtxCtrl;
    static FuncEvpEncryptInitEx evpEncryptInitEx;
    static FuncEvpEncryptUpdate evpEncryptUpdate;
    static FuncEvpEncryptFinalEx evpEncryptFinalEx;
    static FuncEvpDecryptInitEx evpDecryptInitEx;
    static FuncEvpDecryptUpdate evpDecryptUpdate;
    static FuncEvpDecryptFinalEx evpDecryptFinalEx;

    // 随机数函数指针
    static FuncRandPoll randPoll;
    static FuncRandStatus randStatus;
    static FuncRandBytes randBytes;
    static FuncRandBytes randPrivBytes;
    static FuncRandSeed randSeed;

    // X.509 验证函数指针
    static FuncX509VerifyCert x509VerifyCert;
    static FuncX509VerifyCertErrorString x509VerifyCertErrorString;
    static FuncX509StoreCtxGetError x509StoreCtxGetError;
    static FuncPemReadBioX509Crl pemReadBioX509Crl;
    static FuncPemReadBioPk pemReadBioPk;
    static FuncBioSFile bioSFile;
    static FuncBioNew bioNew;
    static FuncBioNewMemBuf bioNewMemBuf;
    static FuncBioFree bioFree;
    static FuncBioCtrl bioCtrl;
    static FuncX509StoreCtxGet0Store x509StoreCtxGet0Store;
    static FuncX509StoreCtxSetFlags x509StoreCtxSetFlags;
    static FuncX509StoreAddCrl x509StoreAddCrl;
    static FuncX509CrlFree x509CrlFree;

    // X.509 时间和公钥函数指针
    static FuncX509CmpCurrentTime x509CmpCurrentTime;
    static FuncX509CrlGet0ByCert x509CrlGet0ByCert;
    static FuncX509CrlGet0NextUpdate x509CrlGet0NextUpdate;
    static FuncX509GetNotAfter x509GetNotAfter;
    static FuncX509GetNotBefore x509GetNotBefore;
    static FuncX509GetPubkey x509GetPubkey;
    static FuncEvpPkeyBits evpPkeyBits;
    static FuncEvpPkeyFree evpPkeyFree;

    // 加载接口
    static int LoadOpensslAPI(const std::string &libPath);

private:
    static const char *gOpensslEnvPath;
    static const char *gOpensslLibSslName;
    static const char *gOpensslLibCryptoName;
    static const char *gSep;
    static bool gLoaded;

    static int GetLibPath(std::string &libDir, std::string &libSslPath, std::string &libCryptoPath);
    static int LoadSSLSymbols(void *sslHandle);
    static int LoadCryptoSymbols(void *cryptoHandle);
};
```

**逐行解读**:
- 第 110-196 行: 静态函数指针成员，存储动态加载的 OpenSSL API
- 第 197 行: `LoadOpensslAPI` - 加载 OpenSSL 库的公共接口
- 第 199-208 行: 私有成员
  - `gOpensslEnvPath`: 环境变量名 `EP_OPENSSL_PATH`
  - `gOpensslLibSslName`: SSL 库名 `libssl.so`
  - `gOpensslLibCryptoName`: Crypto 库名 `libcrypto.so`
  - `gSep`: 路径分隔符 `/`
  - `gLoaded`: 加载状态标志
  - `GetLibPath`: 获取库路径
  - `LoadSSLSymbols`: 加载 SSL 符号
  - `LoadCryptoSymbols`: 加载 Crypto 符号

### 实现文件解读 (openssl_api_dl.cpp)

#### 头文件引用和宏定义 (行 1-21)

```cpp
#include <linux/limits.h>
#include <dlfcn.h>
#include <unistd.h>
#include "acc_includes.h"
#include "acc_file_validator.h"
#include "openssl_api_dl.h"

#define DLSYM(handle, type, ptr, sym)              \
    do {                                           \
        auto ptr1 = dlsym((handle), (sym));        \
        if (ptr1 == nullptr) {                     \
            LOG_ERROR("Failed to load " << (sym)); \
            return -1;                             \
        }                                          \
        (ptr) = (type)ptr1;                        \
    } while (0)
```

**逐行解读**:
- 第 4 行: `linux/limits.h` - Linux 路径长度限制
- 第 6 行: `dlfcn.h` - 动态链接库操作接口
- 第 7 行: `unistd.h` - POSIX 操作系统 API
- 第 13-21 行: `DLSYM` 宏
  - 使用 dlsym 获取符号地址
  - 失败时打印错误并返回 -1
  - 成功时将指针转换为指定类型

#### 静态成员初始化 (行 23-117)

```cpp
namespace ock {
namespace acc {
FuncInit OPENSSLAPIDL::initSsl = nullptr;
FuncInit OPENSSLAPIDL::initCypto = nullptr;
FuncOpensslCleanup OPENSSLAPIDL::opensslCleanup = nullptr;

FuncGetMethod OPENSSLAPIDL::tlsServerMethod = nullptr;
FuncGetMethod OPENSSLAPIDL::tlsClientMethod = nullptr;
FuncGetMethod OPENSSLAPIDL::tlsMethod = nullptr;
// ... 所有函数指针初始化为 nullptr

bool OPENSSLAPIDL::gLoaded = false;
const char *OPENSSLAPIDL::gOpensslEnvPath = "EP_OPENSSL_PATH";
const char *OPENSSLAPIDL::gOpensslLibSslName = "libssl.so";
const char *OPENSSLAPIDL::gOpensslLibCryptoName = "libcrypto.so";
const char *OPENSSLAPIDL::gSep = "/";
```

**逐行解读**:
- 第 25-111 行: 所有函数指针初始化为 nullptr
- 第 113 行: `gLoaded` 初始化为 false，表示未加载
- 第 114 行: 环境变量名 `EP_OPENSSL_PATH`
- 第 115 行: SSL 库文件名 `libssl.so`
- 第 116 行: Crypto 库文件名 `libcrypto.so`
- 第 117 行: 路径分隔符 `/`

#### GetLibPath() - 获取库路径 (行 119-152)

```cpp
int OPENSSLAPIDL::GetLibPath(std::string &libDir, std::string &libSslPath, std::string &libCryptoPath)
{
    // 检查符号链接
    if (ock::mf::FileUtil::IsSymlink(libDir)) {
        LOG_ERROR("Path for openssl library un-support symlink.");
        return -1;
    }

    // 检查路径有效性
    if (!ock::mf::FileUtil::Realpath(libDir)) {
        LOG_ERROR("Path for openssl library is invalid.");
        return -1;
    }

    // 确保路径以 / 结尾
    if (libDir.back() != '/') {
        libDir.push_back('/');
    }

    // 处理子文件夹（UT 测试时跳过）
    std::string subFolder = "";
#ifdef UT_ENABLED
    subFolder = "";
#endif

    // 构建 libssl.so 路径
    libSslPath = libDir + subFolder + gOpensslLibSslName;
    if (::access(libSslPath.c_str(), F_OK) != 0) {
        LOG_ERROR("libssl.so path set in env is invalid");
        return -1;
    }

    // 构建 libcrypto.so 路径
    libCryptoPath = libDir + subFolder + gOpensslLibCryptoName;
    if (::access(libCryptoPath.c_str(), F_OK) != 0) {
        LOG_ERROR("libcrypto.so path set in env is invalid");
        return -1;
    }
    return 0;
}
```

**逐行解读**:
- 第 121-124 行: 检查路径是否为符号链接（不允许）
- 第 126-129 行: 检查路径是否为有效真实路径
- 第 131-133 行: 确保路径以 `/` 结尾
- 第 135-138 行: UT 测试时可能使用子文件夹
- 第 140-144 行: 构建 libssl.so 完整路径并验证文件存在
- 第 146-150 行: 构建 libcrypto.so 完整路径并验证文件存在
- 第 151 行: 成功返回 0

#### LoadSSLSymbols() - 加载 SSL 符号 (行 154-196)

```cpp
int OPENSSLAPIDL::LoadSSLSymbols(void *sslHandle)
{
    DLSYM(sslHandle, FuncInit, initSsl, "OPENSSL_init_ssl");
    DLSYM(sslHandle, FuncInit, initCypto, "OPENSSL_init_crypto");
    DLSYM(sslHandle, FuncOpensslCleanup, opensslCleanup, "OPENSSL_cleanup");
    DLSYM(sslHandle, FuncGetMethod, tlsServerMethod, "TLS_server_method");
    DLSYM(sslHandle, FuncGetMethod, tlsClientMethod, "TLS_client_method");
    DLSYM(sslHandle, FuncGetMethod, tlsMethod, "TLS_method");
    DLSYM(sslHandle, FuncSslOperation, sslShutdown, "SSL_shutdown");
    DLSYM(sslHandle, FuncSslFd, sslSetFd, "SSL_set_fd");
    DLSYM(sslHandle, FuncSslNew, sslNew, "SSL_new");
    DLSYM(sslHandle, FuncSslFree, sslFree, "SSL_free");
    DLSYM(sslHandle, FuncSslCtxNew, sslCtxNew, "SSL_CTX_new");
    DLSYM(sslHandle, FuncSslCtxFree, sslCtxFree, "SSL_CTX_free");
    DLSYM(sslHandle, FuncSslWrite, sslWrite, "SSL_write");
    DLSYM(sslHandle, FuncSslRead, sslRead, "SSL_read");
    DLSYM(sslHandle, FuncSslOperation, sslConnect, "SSL_connect");
    DLSYM(sslHandle, FuncSslOperation, sslConnectState, "SSL_set_connect_state");
    DLSYM(sslHandle, FuncSslOperation, sslAccept, "SSL_accept");
    DLSYM(sslHandle, FuncSslOperation, sslAcceptState, "SSL_set_accept_state");
    DLSYM(sslHandle, FuncSslOperation, sslGetShutdown, "SSL_get_shutdown");
    DLSYM(sslHandle, FuncSslGetError, sslGetError, "SSL_get_error");
    DLSYM(sslHandle, FuncSetCipherSuites, setCipherSuites, "SSL_CTX_set_ciphersuites");
    DLSYM(sslHandle, FuncSslCtxCtrl, sslCtxCtrl, "SSL_CTX_ctrl");
    DLSYM(sslHandle, FuncSslGetCurrentCipher, sslGetCurrentCipher, "SSL_get_current_cipher");
    DLSYM(sslHandle, FuncSslGetVersion, sslGetVersion, "SSL_get_version");
    DLSYM(sslHandle, FuncUsePrivKey, usePrivKey, "SSL_CTX_use_PrivateKey");
    DLSYM(sslHandle, FuncUsePrivKeyFile, usePrivKeyFile, "SSL_CTX_use_PrivateKey_file");
    DLSYM(sslHandle, FuncUseCertFile, useCertFile, "SSL_CTX_use_certificate_file");
    DLSYM(sslHandle, FuncSslCtxSetVerify, sslCtxSetVerify, "SSL_CTX_set_verify");
    DLSYM(sslHandle, FuncSetDefaultPasswdCbUserdata, setDefaultPasswdCbUserdata,
          "SSL_CTX_set_default_passwd_cb_userdata");
    DLSYM(sslHandle, FuncSetCertVerifyCallback, setCertVerifyCallback, "SSL_CTX_set_cert_verify_callback");
    DLSYM(sslHandle, FuncLoadVerifyLocations, loadVerifyLocations, "SSL_CTX_load_verify_locations");
    DLSYM(sslHandle, FuncCheckPrivateKey, checkPrivateKey, "SSL_CTX_check_private_key");
    DLSYM(sslHandle, FuncSslGetVerifyResult, sslGetVerifyResult, "SSL_get_verify_result");
    DLSYM(sslHandle, FuncSslGetPeerCertificate, sslGetPeerCertificate, "SSL_get1_peer_certificate");
    DLSYM(sslHandle, FuncSsLCtxGet0Certificate, ssLCtxGet0Certificate, "SSL_CTX_get0_certificate");
    DLSYM(sslHandle, FuncSslWriteEx, sslWriteEx, "SSL_write_ex");
    DLSYM(sslHandle, FuncSslReadEx, sslReadEx, "SSL_read_ex");
    DLSYM(sslHandle, FuncSslIsServer, sslIsServer, "SSL_is_server");
    return 0;
}
```

**逐行解读**:
- 第 156-194 行: 使用 DLSYM 宏加载所有 SSL 相关符号
  - 初始化函数: `OPENSSL_init_ssl`, `OPENSSL_init_crypto`, `OPENSSL_cleanup`
  - 方法函数: `TLS_server_method`, `TLS_client_method`, `TLS_method`
  - 连接操作: `SSL_connect`, `SSL_accept`, `SSL_shutdown`
  - I/O 操作: `SSL_read`, `SSL_write`, `SSL_read_ex`, `SSL_write_ex`
  - 证书验证: `SSL_CTX_set_verify`, `SSL_CTX_load_verify_locations`
  - 密钥和证书: `SSL_CTX_use_PrivateKey`, `SSL_CTX_use_certificate_file`

#### LoadCryptoSymbols() - 加载 Crypto 符号 (行 198-245)

```cpp
int OPENSSLAPIDL::LoadCryptoSymbols(void *cryptoHandle)
{
    // 加密上下文
    DLSYM(cryptoHandle, FuncEvpCipherCtxNew, evpCipherCtxNew, "EVP_CIPHER_CTX_new");
    DLSYM(cryptoHandle, FuncEvpCipherCtxFree, evpCipherCtxFree, "EVP_CIPHER_CTX_free");
    DLSYM(cryptoHandle, FuncEvpCipherCtxCtrl, evpCipherCtxCtrl, "EVP_CIPHER_CTX_ctrl");

    // 加密操作
    DLSYM(cryptoHandle, FuncEvpEncryptInitEx, evpEncryptInitEx, "EVP_EncryptInit_ex");
    DLSYM(cryptoHandle, FuncEvpEncryptUpdate, evpEncryptUpdate, "EVP_EncryptUpdate");
    DLSYM(cryptoHandle, FuncEvpEncryptFinalEx, evpEncryptFinalEx, "EVP_EncryptFinal_ex");
    DLSYM(cryptoHandle, FuncEvpDecryptInitEx, evpDecryptInitEx, "EVP_DecryptInit_ex");
    DLSYM(cryptoHandle, FuncEvpDecryptUpdate, evpDecryptUpdate, "EVP_DecryptUpdate");
    DLSYM(cryptoHandle, FuncEvpDecryptFinalEx, evpDecryptFinalEx, "EVP_DecryptFinal_ex");

    // AES 算法
    DLSYM(cryptoHandle, FuncEvpAesCipher, evpAes128Gcm, "EVP_aes_128_gcm");
    DLSYM(cryptoHandle, FuncEvpAesCipher, evpAes256Gcm, "EVP_aes_256_gcm");

    // 随机数
    DLSYM(cryptoHandle, FuncRandPoll, randPoll, "RAND_poll");
    DLSYM(cryptoHandle, FuncRandStatus, randStatus, "RAND_status");
    DLSYM(cryptoHandle, FuncRandBytes, randBytes, "RAND_bytes");
    DLSYM(cryptoHandle, FuncRandBytes, randPrivBytes, "RAND_priv_bytes");
    DLSYM(cryptoHandle, FuncRandSeed, randSeed, "RAND_seed");

    // X.509 证书验证
    DLSYM(cryptoHandle, FuncX509VerifyCert, x509VerifyCert, "X509_verify_cert");
    DLSYM(cryptoHandle, FuncX509VerifyCertErrorString, x509VerifyCertErrorString, "X509_verify_cert_error_string");
    DLSYM(cryptoHandle, FuncX509StoreCtxGetError, x509StoreCtxGetError, "X509_STORE_CTX_get_error");

    // BIO 和 CRL
    DLSYM(cryptoHandle, FuncPemReadBioX509Crl, pemReadBioX509Crl, "PEM_read_bio_X509_CRL");
    DLSYM(cryptoHandle, FuncPemReadBioPk, pemReadBioPk, "PEM_read_bio_PrivateKey");
    DLSYM(cryptoHandle, FuncBioSFile, bioSFile, "BIO_s_file");
    DLSYM(cryptoHandle, FuncBioNew, bioNew, "BIO_new");
    DLSYM(cryptoHandle, FuncBioNewMemBuf, bioNewMemBuf, "BIO_new_mem_buf");
    DLSYM(cryptoHandle, FuncBioFree, bioFree, "BIO_free");
    DLSYM(cryptoHandle, FuncBioCtrl, bioCtrl, "BIO_ctrl");
    DLSYM(cryptoHandle, FuncX509StoreCtxGet0Store, x509StoreCtxGet0Store, "X509_STORE_CTX_get0_store");
    DLSYM(cryptoHandle, FuncX509StoreCtxSetFlags, x509StoreCtxSetFlags, "X509_STORE_CTX_set_flags");
    DLSYM(cryptoHandle, FuncX509StoreAddCrl, x509StoreAddCrl, "X509_STORE_add_crl");
    DLSYM(cryptoHandle, FuncX509CrlFree, x509CrlFree, "X509_CRL_free");

    // X.509 时间和公钥
    DLSYM(cryptoHandle, FuncX509CmpCurrentTime, x509CmpCurrentTime, "X509_cmp_current_time");
    DLSYM(cryptoHandle, FuncX509CrlGet0ByCert, x509CrlGet0ByCert, "X509_CRL_get0_by_cert");
    DLSYM(cryptoHandle, FuncX509CrlGet0NextUpdate, x509CrlGet0NextUpdate, "X509_CRL_get0_nextUpdate");
    DLSYM(cryptoHandle, FuncX509GetNotAfter, x509GetNotAfter, "X509_getm_notAfter");
    DLSYM(cryptoHandle, FuncX509GetNotBefore, x509GetNotBefore, "X509_getm_notBefore");
    DLSYM(cryptoHandle, FuncX509GetPubkey, x509GetPubkey, "X509_get_pubkey");
    DLSYM(cryptoHandle, FuncEvpPkeyBits, evpPkeyBits, "EVP_PKEY_get_bits");
    DLSYM(cryptoHandle, FuncEvpPkeyFree, evpPkeyFree, "EVP_PKEY_free");
    DLSYM(cryptoHandle, FuncPemReadX509, pemReadX509, "PEM_read_X509");
    DLSYM(cryptoHandle, FuncX509Free, x509Free, "X509_free");
    DLSYM(cryptoHandle, FuncAsn1Time2Tm, asn1Time2Tm, "ASN1_TIME_to_tm");
    return 0;
}
```

**逐行解读**:
- 第 200-208 行: 加载 EVP 加密上下文函数
- 第 210-217 行: 加载加密/解密操作函数
- 第 209-210 行: 加载 AES-GCM 算法
- 第 212-216 行: 加载随机数生成函数
- 第 218-221 行: 加载 X.509 证书验证函数
- 第 222-231 行: 加载 BIO 和 CRL 操作函数
- 第 233-243 行: 加载 X.509 时间和公钥操作函数

#### LoadOpensslAPI() - 加载 OpenSSL API (行 247-303)

```cpp
int OPENSSLAPIDL::LoadOpensslAPI(const std::string &libPath)
{
    LOG_INFO("Starting to load openssl api");

    // 检查是否已加载
    if (gLoaded) {
        return 0;
    }

    // 获取库文件路径
    std::string libDir = libPath;
    std::string libSslPath;
    std::string libCryptoPath;
    if (GetLibPath(libDir, libSslPath, libCryptoPath) != 0) {
        return -1;
    }

    // 验证 libssl.so
    std::string errMsg;
    if (!FileValidator::RegularFilePath(libSslPath, libDir, errMsg) ||
        !FileValidator::IsFileValid(libSslPath, errMsg) ||
        !FileValidator::CheckPermission(libSslPath, 0b101101000, false, errMsg)) {
        LOG_ERROR(errMsg);
        return -1;
    }

    // 验证 libcrypto.so
    if (!FileValidator::RegularFilePath(libCryptoPath, libDir, errMsg) ||
        !FileValidator::IsFileValid(libCryptoPath, errMsg) ||
        !FileValidator::CheckPermission(libCryptoPath, 0b101101000, false, errMsg)) {
        LOG_ERROR(errMsg);
        return -1;
    }

    // 加载 libcrypto.so
    auto cryptoHandle = dlopen(libCryptoPath.c_str(), RTLD_NOW | RTLD_GLOBAL);
    if (cryptoHandle == nullptr) {
        LOG_ERROR("Failed to dlopen libcrypto.so err: " << dlerror());
        return -1;
    }

    // 加载 Crypto 符号
    if (LoadCryptoSymbols(cryptoHandle) == -1) {
        LOG_ERROR("Failed to dlopen libcrypto.so err: " << dlerror());
        dlclose(cryptoHandle);
        return -1;
    }

    // 加载 libssl.so
    auto sslHandle = dlopen(libSslPath.c_str(), RTLD_NOW | RTLD_GLOBAL);
    if (sslHandle == nullptr) {
        LOG_ERROR("Failed to dlopen libssl.so err: " << dlerror());
        dlclose(cryptoHandle);
        return -1;
    }

    // 加载 SSL 符号
    if (LoadSSLSymbols(sslHandle) == -1) {
        LOG_ERROR("Failed to dlopen libssl.so err: " << dlerror());
        dlclose(cryptoHandle);
        dlclose(sslHandle);
        return -1;
    }

    gLoaded = true;
    return 0;
}
```

**逐行解读**:
- 第 249-252 行: 检查是否已加载，避免重复加载
- 第 254-259 行: 获取库文件完整路径
- 第 261-267 行: 验证 libssl.so 文件
  - 检查是否为常规文件路径
  - 检查文件是否有效
  - 检查权限 (0b101101000 = 0x368 = rwxr-x---)
- 第 268-273 行: 验证 libcrypto.so 文件
- 第 275-279 行: 使用 dlopen 加载 libcrypto.so
  - `RTLD_NOW`: 立即解析符号
  - `RTLD_GLOBAL`: 使符号可用于后续加载的共享库
- 第 281-285 行: 加载 Crypto 符号，失败时清理
- 第 287-292 行: 加载 libssl.so
- 第 294-299 行: 加载 SSL 符号，失败时清理两个句柄
- 第 301 行: 设置加载标志为 true
- 第 302 行: 返回成功

---

## 2. openssl_api_wrapper.h - API 包装器

### 文件信息
- 文件路径: `src/acc_links/csrc/under_api/openssl/openssl_api_wrapper.h`
- 代码行数: 501 行
- 主要功能: 提供类型安全的 OpenSSL API 包装器

### 常量定义 (行 13-35)

```cpp
class OpenSslApiWrapper {
public:
    // SSL 验证模式
    static const uint32_t SSL_VERIFY_NONE = 0U;
    static const uint32_t SSL_VERIFY_PEER = 1U;
    static const uint32_t SSL_VERIFY_FAIL_IF_NO_PEER_CERT = 2U;

    // 文件类型
    static const uint32_t SSL_FILETYPE_PEM = 1U;

    // AEAD 加密控制
    static const uint32_t EVP_CTRL_AEAD_SET_IVLEN = 9U;
    static const uint32_t EVP_CTRL_AEAD_GET_TAG = 16U;
    static const uint32_t EVP_CTRL_AEAD_SET_TAG = 17U;

    // OpenSSL 初始化选项
    static const uint32_t OPENSSL_INIT_LOAD_SSL_STRINGS = 2097152U;
    static const uint32_t OPENSSL_INIT_LOAD_CRYPTO_STRINGS = 2U;

    // SSL 协议版本
    static const uint32_t SSL_CTRL_SET_MIN_PROTO_VERSION = 123U;
    static const uint32_t TLS1_3_VERSION = 772U;

    // SSL 错误码
    static const uint32_t SSL_ERROR_WANT_READ = 2U;
    static const uint32_t SSL_ERROR_WANT_WRITE = 3U;
    static const uint32_t SSL_ERROR_ZERO_RETURN = 6U;

    // SSL 关闭状态
    static const uint32_t SSL_SENT_SHUTDOWN = 1U;
    static const uint32_t SSL_RECEIVED_SHUTDOWN = 2U;

    // BIO 控制命令
    static const uint32_t BIO_C_SET_FILENAME = 108U;
    static const uint32_t BIO_CLOSE = 1U;
    static const uint32_t BIO_FP_READ = 2U;

    // X.509 验证标志
    static const uint32_t X509_V_FLAG_CRL_CHECK = 4U;
    static const uint32_t X509_V_FLAG_CRL_CHECK_ALL = 8U;
```

**逐行解读**:
- 第 13-15 行: SSL 证书验证模式
  - `SSL_VERIFY_NONE`: 不验证证书
  - `SSL_VERIFY_PEER`: 验证对端证书
  - `SSL_VERIFY_FAIL_IF_NO_PEER_CERT`: 无证书时失败
- 第 16 行: PEM 文件类型
- 第 17-19 行: AEAD (关联数据的认证加密) 控制命令
- 第 20-21 行: OpenSSL 初始化选项
- 第 22-23 行: TLS 1.3 协议版本
- 第 24-26 行: SSL 错误码（非阻塞 I/O 相关）
- 第 28-29 行: SSL 关闭通知状态
- 第 31-33 行: BIO (基本 I/O) 控制命令
- 第 34-35 行: X.509 CRL 验证标志

### 初始化函数 (行 37-65)

```cpp
static int OpensslInitSsl(uint64_t opts, const OPENSSL_INIT_SETTINGS *settings)
{
    VALIDATE_RETURN(OPENSSLAPIDL::initSsl != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::initSsl(opts, settings);
}

static inline int OpensslInitCrypto(uint64_t opts, const OPENSSL_INIT_SETTINGS *settings)
{
    VALIDATE_RETURN(OPENSSLAPIDL::initCypto != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::initCypto(opts, settings);
}

static inline const SSL_METHOD *TlsClientMethod()
{
    VALIDATE_RETURN(OPENSSLAPIDL::tlsClientMethod != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::tlsClientMethod();
}

static inline const SSL_METHOD *TlsMethod()
{
    VALIDATE_RETURN(OPENSSLAPIDL::tlsMethod != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::tlsMethod();
}

static inline const SSL_METHOD *TlsServerMethod()
{
    VALIDATE_RETURN(OPENSSLAPIDL::tlsServerMethod != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::tlsServerMethod();
}
```

**逐行解读**:
- 第 39 行: 使用 `VALIDATE_RETURN` 宏检查函数指针是否为空
- 第 40 行: 调用动态加载的 `OPENSSL_init_ssl`
- 第 43-47 行: `OpensslInitCrypto` - 初始化 Crypto 库
- 第 49-53 行: `TlsClientMethod` - 获取 TLS 客户端方法
- 第 55-59 行: `TlsMethod` - 获取通用 TLS 方法
- 第 61-65 行: `TlsServerMethod` - 获取 TLS 服务器方法

### SSL 对象管理 (行 67-101)

```cpp
static inline int SslShutdown(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslShutdown != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslShutdown(s);
}

static inline int SslSetFd(SSL *s, int fd)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslSetFd != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslSetFd(s, fd);
}

static inline SSL *SslNew(SSL_CTX *ctx)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslNew != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::sslNew(ctx);
}

static inline void SslFree(SSL *s)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::sslFree != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::sslFree(s);
}

static SSL_CTX *SslCtxNew(const SSL_METHOD *method)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslCtxNew != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::sslCtxNew(method);
}

static inline void SslCtxFree(SSL_CTX *ctx)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::sslCtxFree != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::sslCtxFree(ctx);
}
```

**逐行解读**:
- 第 69-71 行: `SslShutdown` - 关闭 SSL 连接
- 第 74-76 行: `SslSetFd` - 关联文件描述符
- 第 79-82 行: `SslNew` - 创建新的 SSL 对象
- 第 85-88 行: `SslFree` - 释放 SSL 对象
- 第 91-94 行: `SslCtxNew` - 创建 SSL 上下文
- 第 97-100 行: `SslCtxFree` - 释放 SSL 上下文

### SSL I/O 操作 (行 103-161)

```cpp
static inline int SslWrite(SSL *s, const void *buf, int num)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslWrite != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslWrite(s, buf, num);
}

static inline int SslRead(SSL *s, void *buf, int num)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslRead != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslRead(s, buf, num);
}

static inline int SslConnect(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslConnect != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslConnect(s);
}

static inline int SslConnectState(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslConnectState != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslConnectState(s);
}

static inline int SslAccept(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslAccept != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslAccept(s);
}

static inline int SslAcceptState(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslAcceptState != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslAcceptState(s);
}

static inline int SslGetShutdown(SSL *s)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslGetShutdown != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslGetShutdown(s);
}

static inline int SslGetError(const SSL *s, int retCode)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslGetError != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslGetError(s, retCode);
}

static inline int SslWriteEx(SSL *s, const void *buf, size_t num, size_t *written)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslWriteEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslWriteEx(s, buf, num, written);
}

static inline int SslReadEx(SSL *s, void *buf, size_t num, size_t *readbytes)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslReadEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslReadEx(s, buf, num, readbytes);
}
```

**逐行解读**:
- 第 105-107 行: `SslWrite` - 写入数据到 SSL 连接
- 第 110-112 行: `SslRead` - 从 SSL 连接读取数据
- 第 115-117 行: `SslConnect` - 客户端发起 TLS 握手
- 第 120-122 行: `SslConnectState` - 设置连接状态
- 第 125-127 行: `SslAccept` - 服务器接受 TLS 握手
- 第 130-132 行: `SslAcceptState` - 设置接受状态
- 第 135-137 行: `SslGetShutdown` - 获取关闭状态
- 第 140-142 行: `SslGetError` - 获取错误码
- 第 145-147 行: `SslWriteEx` - 扩展写入（返回实际写入字节数）
- 第 150-152 行: `SslReadEx` - 扩展读取（返回实际读取字节数）

### SSL 上下文配置 (行 163-269)

```cpp
static inline int SslCtxSetCipherSuites(SSL_CTX *ctx, const char *str)
{
    VALIDATE_RETURN(OPENSSLAPIDL::setCipherSuites != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::setCipherSuites(ctx, str);
}

static inline long SslCtxCtrl(SSL_CTX *ctx, int cmd, long larg, void *parg)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslCtxCtrl != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslCtxCtrl(ctx, cmd, larg, parg);
}

static inline const char *SslGetVersion(const SSL *ssl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslGetVersion != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::sslGetVersion(ssl);
}

static inline int SslIsServer(SSL *ssl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslIsServer != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslIsServer(ssl);
}

static inline void SslCtxSetVerify(SSL_CTX *ctx, int mode, int (*cb)(int, X509_STORE_CTX *))
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::sslCtxSetVerify != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::sslCtxSetVerify(ctx, mode, cb);
}

static inline int SslCtxUsePrivateKey(SSL_CTX *ctx, EVP_PKEY *pkey)
{
    VALIDATE_RETURN(OPENSSLAPIDL::usePrivKey != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::usePrivKey(ctx, pkey);
}

static inline int SslCtxUsePrivateKeyFile(SSL_CTX *ctx, const char *file, int type)
{
    VALIDATE_RETURN(OPENSSLAPIDL::usePrivKeyFile != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::usePrivKeyFile(ctx, file, type);
}

static inline int SslCtxUseCertificateFile(SSL_CTX *ctx, const char *file, int type)
{
    VALIDATE_RETURN(OPENSSLAPIDL::useCertFile != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::useCertFile(ctx, file, type);
}

static inline X509 *PemReadX509(FILE *fp, X509 **x, PEM_PASSWORD_CB *cb, void *u)
{
    VALIDATE_RETURN(OPENSSLAPIDL::pemReadX509 != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::pemReadX509(fp, x, cb, u);
}

static inline void X509Free(X509 *cert)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::x509Free != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::x509Free(cert);
}

static inline int Asn1Time2Tm(const ASN1_TIME *s, struct tm *tm)
{
    VALIDATE_RETURN(OPENSSLAPIDL::asn1Time2Tm != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::asn1Time2Tm(s, tm);
}

static inline void SslCtxSetDefaultPasswdCbUserdata(SSL_CTX *ctx, void *u)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::setDefaultPasswdCbUserdata != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::setDefaultPasswdCbUserdata(ctx, u);
}

static inline void SslCtxSetCertVerifyCallback(SSL_CTX *ctx, int (*cb)(X509_STORE_CTX *, void *), void *arg)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::setCertVerifyCallback != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::setCertVerifyCallback(ctx, cb, arg);
}

static inline int SslCtxLoadVerifyLocations(SSL_CTX *ctx, const char *cafile, const char *capath)
{
    VALIDATE_RETURN(OPENSSLAPIDL::loadVerifyLocations != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::loadVerifyLocations(ctx, cafile, capath);
}

static inline int SslCtxCheckPrivateKey(const SSL_CTX *ctx)
{
    VALIDATE_RETURN(OPENSSLAPIDL::checkPrivateKey != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::checkPrivateKey(ctx);
}

static inline X509 *SslGetPeerCertificate(const SSL *ssl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslGetPeerCertificate != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::sslGetPeerCertificate(ssl);
}

static inline X509 *SslCtxGet0Certificate(const SSL_CTX *ctx)
{
    VALIDATE_RETURN(OPENSSLAPIDL::ssLCtxGet0Certificate != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::ssLCtxGet0Certificate(ctx);
}

static inline long SslGetVerifyResult(const SSL *ssl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::sslGetVerifyResult != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::sslGetVerifyResult(ssl);
}
```

**逐行解读**:
- 第 165-167 行: `SslCtxSetCipherSuites` - 设置密码套件
- 第 169-171 行: `SslCtxCtrl` - SSL 上下文控制
- 第 173-175 行: `SslGetVersion` - 获取 TLS 版本
- 第 177-179 行: `SslIsServer` - 判断是否为服务器
- 第 181-184 行: `SslCtxSetVerify` - 设置证书验证模式
- 第 186-188 行: `SslCtxUsePrivateKey` - 使用私钥
- 第 190-192 行: `SslCtxUsePrivateKeyFile` - 从文件加载私钥
- 第 194-196 行: `SslCtxUseCertificateFile` - 从文件加载证书
- 第 198-200 行: `PemReadX509` - 读取 X.509 证书
- 第 202-204 行: `X509Free` - 释放证书
- 第 206-208 行: `Asn1Time2Tm` - ASN1 时间转 tm 结构
- 第 210-212 行: `SslCtxSetDefaultPasswdCbUserdata` - 设置私钥密码回调数据
- 第 214-216 行: `SslCtxSetCertVerifyCallback` - 设置证书验证回调
- 第 218-220 行: `SslCtxLoadVerifyLocations` - 加载 CA 证书位置
- 第 222-224 行: `SslCtxCheckPrivateKey` - 检查私钥一致性
- 第 226-228 行: `SslGetPeerCertificate` - 获取对端证书
- 第 230-232 行: `SslCtxGet0Certificate` - 获取本地证书
- 第 234-236 行: `SslGetVerifyResult` - 获取验证结果

### 加密操作 (行 271-339)

```cpp
static inline const EVP_CIPHER *EvpAes128Gcm()
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpAes128Gcm != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::evpAes128Gcm();
}

static inline const EVP_CIPHER *EvpAes256Gcm()
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpAes256Gcm != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::evpAes256Gcm();
}

static inline EVP_CIPHER_CTX *EvpCipherCtxNew()
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpCipherCtxNew != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::evpCipherCtxNew();
}

static inline void EvpCipherCtxFree(EVP_CIPHER_CTX *ctx)
{
    VALIDATE_RETURN_VOID(OPENSSLAPIDL::evpCipherCtxFree != nullptr, "openssl handler not loaded");
    OPENSSLAPIDL::evpCipherCtxFree(ctx);
}

static inline int EvpCipherCtxCtrl(EVP_CIPHER_CTX *ctx, int type, int arg, void *ptr)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpCipherCtxCtrl != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpCipherCtxCtrl(ctx, type, arg, ptr);
}

static inline int EvpEncryptInitEx(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher, ENGINE *impl,
                                   const unsigned char *key, const unsigned char *iv)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpEncryptInitEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpEncryptInitEx(ctx, cipher, impl, key, iv);
}

static inline int EvpEncryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl, const unsigned char *in,
                                   int inl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpEncryptUpdate != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpEncryptUpdate(ctx, out, outl, in, inl);
}

static inline int EvpEncryptFinalEx(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpEncryptFinalEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpEncryptFinalEx(ctx, out, outl);
}

static inline int EvpDecryptInitEx(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher, ENGINE *impl,
                                   const unsigned char *key, const unsigned char *iv)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpDecryptInitEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpDecryptInitEx(ctx, cipher, impl, key, iv);
}

static inline int EvpDecryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl, const unsigned char *in,
                                   int inl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpDecryptUpdate != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpDecryptUpdate(ctx, out, outl, in, inl);
}

static inline int EvpDecryptFinalEx(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl)
{
    VALIDATE_RETURN(OPENSSLAPIDL::evpDecryptFinalEx != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::evpDecryptFinalEx(ctx, out, outl);
}
```

**逐行解读**:
- 第 273-275 行: `EvpAes128Gcm` - 获取 AES-128-GCM 算法
- 第 278-280 行: `EvpAes256Gcm` - 获取 AES-256-GCM 算法
- 第 283-285 行: `EvpCipherCtxNew` - 创建加密上下文
- 第 288-290 行: `EvpCipherCtxFree` - 释放加密上下文
- 第 293-295 行: `EvpCipherCtxCtrl` - 控制加密上下文
- 第 297-301 行: `EvpEncryptInitEx` - 初始化加密
- 第 303-307 行: `EvpEncryptUpdate` - 加密更新
- 第 309-312 行: `EvpEncryptFinalEx` - 加密结束
- 第 314-318 行: `EvpDecryptInitEx` - 初始化解密
- 第 320-324 行: `EvpDecryptUpdate` - 解密更新
- 第 326-329 行: `EvpDecryptFinalEx` - 解密结束

### 随机数和证书操作 (行 341-489)

```cpp
static inline int RandPoll()
{
    VALIDATE_RETURN(OPENSSLAPIDL::randPoll != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::randPoll();
}

static inline int RandStatus()
{
    VALIDATE_RETURN(OPENSSLAPIDL::randStatus != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::randStatus();
}

static inline int RandPrivBytes(unsigned char *buf, int num)
{
    VALIDATE_RETURN(OPENSSLAPIDL::randPrivBytes != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::randPrivBytes(buf, num);
}

static inline int X509VerifyCert(X509_STORE_CTX *ctx)
{
    VALIDATE_RETURN(OPENSSLAPIDL::x509VerifyCert != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::x509VerifyCert(ctx);
}

static inline const char *X509VerifyCertErrorString(long n)
{
    VALIDATE_RETURN(OPENSSLAPIDL::x509VerifyCertErrorString != nullptr, "openssl handler not loaded", nullptr);
    return OPENSSLAPIDL::x509VerifyCertErrorString(n);
}

static inline int X509StoreCtxGetError(X509_STORE_CTX *ctx)
{
    VALIDATE_RETURN(OPENSSLAPIDL::x509StoreCtxGetError != nullptr, "openssl handler not loaded", -1);
    return OPENSSLAPIDL::x509StoreCtxGetError(ctx);
}

// ... 更多 X.509 和 BIO 操作包装函数
```

### 加载/卸载接口 (行 491-497)

```cpp
static inline int Load(const std::string &libPsth)
{
    return OPENSSLAPIDL::LoadOpensslAPI(libPsth);
}

static inline void UnLoad() {}
```

**逐行解读**:
- 第 492-494 行: `Load` - 加载 OpenSSL 库
- 第 496 行: `UnLoad` - 空实现（不主动卸载）

---

## 3. openssl_util.h/cpp - 工具函数

### 文件信息
- 文件路径: `src/acc_links/csrc/under_api/openssl/openssl_util.h/cpp`
- 代码行数: 60 行
- 主要功能: SSL 辅助工具函数

### 头文件 (openssl_util.h)

```cpp
namespace ock {
namespace acc {

Result SslShutdownHelper(SSL *s);

}
}
```

**逐行解读**:
- 第 14 行: 声明 `SslShutdownHelper` 函数

### 实现 (openssl_util.cpp)

```cpp
Result SslShutdownHelper(SSL *ssl)
{
    // 检查 SSL 指针
    if (!ssl) {
        LOG_ERROR("ssl ptr is nullptr");
        return ACC_ERROR;
    }

    // 配置重试参数
    const int sslShutdownTimes = 5;       // 最大重试次数
    const int sslRetryInterval = 1;        // 重试间隔（秒）

    // 第一次尝试关闭
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

    // 重试循环
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
- 第 23-26 行: 检查 SSL 指针有效性
- 第 28-29 行: 定义重试次数（5 次）和间隔（1 秒）
- 第 31 行: 首次尝试 SSL 关闭
- 第 32-34 行: 返回 1 表示成功
- 第 35-37 行: 负数错误处理
- 第 38-40 行: 未知错误处理
- 第 42-55 行: 重试循环
  - 休眠指定间隔
  - 再次尝试关闭
  - 检查返回值
- 第 56 行: 超时返回错误

---

## 总结

OpenSSL 模块提供了 ACC_Links 的安全通信基础设施：

### 1. 动态加载机制

```
LoadOpensslAPI()
    ├── 获取库路径（从环境变量 EP_OPENSSL_PATH）
    ├── 验证库文件（权限、有效性）
    ├── 加载 libcrypto.so
    │   └── LoadCryptoSymbols() - 加载加密相关符号
    └── 加载 libssl.so
        └── LoadSSLSymbols() - 加载 SSL 相关符号
```

### 2. API 包装器

```
OpenSslApiWrapper
    ├── 初始化函数
    │   ├── OpensslInitSsl()
    │   ├── OpensslInitCrypto()
    │   ├── TlsClientMethod()
    │   ├── TlsServerMethod()
    │   └── TlsMethod()
    ├── SSL 对象管理
    │   ├── SslNew() / SslFree()
    │   ├── SslCtxNew() / SslCtxFree()
    │   └── SslSetFd()
    ├── SSL I/O 操作
    │   ├── SslConnect() / SslAccept()
    │   ├── SslRead() / SslWrite()
    │   ├── SslReadEx() / SslWriteEx()
    │   └── SslShutdown()
    ├── SSL 上下文配置
    │   ├── SslCtxSetVerify()
    │   ├── SslCtxUsePrivateKeyFile()
    │   ├── SslCtxUseCertificateFile()
    │   ├── SslCtxLoadVerifyLocations()
    │   └── SslCtxSetCertVerifyCallback()
    ├── 加密操作
    │   ├── EvpAes128Gcm() / EvpAes256Gcm()
    │   ├── EvpEncryptInitEx/Update/FinalEx()
    │   └── EvpDecryptInitEx/Update/FinalEx()
    ├── 证书操作
    │   ├── X509VerifyCert()
    │   ├── X509GetNotAfter() / X509GetNotBefore()
    │   ├── X509GetPubkey() / EvpPkeyBits()
    │   └── PemReadX509() / X509Free()
    └── 加载/卸载
        ├── Load()
        └── UnLoad()
```

### 3. 关键特性

1. **动态加载**: 通过 dlopen 动态加载 OpenSSL，避免编译时依赖
2. **类型安全**: 使用函数指针类型定义和包装器提供类型安全接口
3. **错误处理**: 每个函数都检查函数指针是否为空
4. **优雅关闭**: SSL 关闭助手支持重试机制
5. **安全验证**: 加载前验证库文件权限和完整性
6. **TLS 1.3 支持**: 支持 TLS 1.3 协议
7. **CRL 支持**: 支持证书吊销列表验证

### 4. 与其他模块的关系

```
acc_tcp_ssl_helper.cpp (Security 模块)
    ├── 使用 OpenSslApiWrapper 调用 OpenSSL API
    ├── 使用 SslShutdownHelper 优雅关闭 SSL
    └── 实现 SSL/TLS 安全通信
        ↓
    openssl_api_wrapper.h (包装器层)
    ├── 提供 C++ 包装接口
    └── 验证函数指针有效性
        ↓
    openssl_api_dl.cpp (动态加载层)
    ├── dlopen 加载 libssl.so 和 libcrypto.so
    └── dlsym 获取函数指针
```
