# 거래소 API 키 발급 가이드

## 📋 지원 거래소 목록 (7개)

### 1. 🌍 OKX (글로벌)
- **웹사이트**: https://www.okx.com/
- **API 문서**: https://www.okx.com/docs-v5/en/
- **발급 절차**:
  1. OKX 계정 생성 및 KYC 완료
  2. [API Management](https://www.okx.com/account/my-api) 페이지 접속
  3. "Create V5 API Key" 클릭
  4. 권한 설정: **"Read Only"** 체크 (거래 권한 제외)
  5. API Key, Secret Key, Passphrase 저장
- **필요 정보**: `api_key`, `secret_key`, `passphrase`
- **권장 권한**: 읽기 전용 (Reading)

### 2. 🇰🇷 Coinone (한국)
- **웹사이트**: https://coinone.co.kr/
- **API 문서**: https://doc.coinone.co.kr/
- **발급 절차**:
  1. 코인원 계정 생성 및 본인인증 완료
  2. [API 관리](https://coinone.co.kr/account/api_key) 페이지 접속
  3. "API 키 생성" 클릭
  4. 권한 설정: **"조회"만 체크** (거래 권한 제외)
  5. Access Token, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 잔고 조회, 시세 조회만

### 3. 🌍 Gate.io (글로벌)
- **웹사이트**: https://www.gate.io/
- **API 문서**: https://www.gate.io/docs/developers/apiv4/
- **발급 절차**:
  1. Gate.io 계정 생성 및 KYC 완료
  2. [API Management](https://www.gate.io/myaccount/apiv4keys) 페이지 접속
  3. "Create API Key" 클릭
  4. 권한 설정: **"Spot Read Only"** 체크
  5. API Key, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 읽기 전용

### 4. 🇰🇷 Upbit (한국)
- **웹사이트**: https://upbit.com/
- **API 문서**: https://docs.upbit.com/
- **발급 절차**:
  1. 업비트 계정 생성 및 본인인증 완료
  2. [Open API 관리](https://upbit.com/mypage/open_api_management) 페이지 접속
  3. "Open API 키 발급" 클릭
  4. 권한 설정: **"자산 조회", "주문 조회"만 체크** (주문 기능 제외)
  5. Access Key, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 조회 전용

### 5. 🌍 Binance (글로벌)
- **웹사이트**: https://www.binance.com/
- **API 문서**: https://binance-docs.github.io/apidocs/spot/en/
- **발급 절차**:
  1. 바이낸스 계정 생성 및 KYC 완료
  2. [API Management](https://www.binance.com/en/my/settings/api-management) 페이지 접속
  3. "Create API" 클릭
  4. 권한 설정: **"Read Info"만 체크** (Spot & Margin Trading 제외)
  5. API Key, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 읽기 전용

### 6. 🇰🇷 Bithumb (한국)
- **웹사이트**: https://www.bithumb.com/
- **API 문서**: https://apidocs.bithumb.com/
- **발급 절차**:
  1. 빗썸 계정 생성 및 본인인증 완료
  2. [API 설정](https://www.bithumb.com/u1/US127) 페이지 접속
  3. "API Key 생성" 클릭
  4. 권한 설정: **"조회"만 체크** (거래 권한 제외)
  5. Connect Key, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 조회만

### 7. 🌍 Bybit (글로벌)
- **웹사이트**: https://www.bybit.com/
- **API 문서**: https://bybit-exchange.github.io/docs/v5/intro
- **발급 절차**:
  1. 바이비트 계정 생성 및 KYC 완료
  2. [API Management](https://www.bybit.com/app/user/api-management) 페이지 접속
  3. "Create New Key" 클릭
  4. 권한 설정: **"Read-Only"** 체크 (Trading 권한 제외)
  5. API Key, Secret Key 저장
- **필요 정보**: `api_key`, `secret_key`
- **권장 권한**: 읽기 전용

## 🔐 보안 권장 사항

### 1. API 키 권한 최소화
- ✅ **조회/읽기 권한만 활성화**
- ❌ **거래/출금 권한은 절대 비활성화**
- ❌ **IP 제한 설정 (필요시)**

### 2. API 키 관리
- 🔒 API 키를 `.env` 파일에 저장 (Git에 커밋하지 않음)
- 🔒 주기적인 API 키 재발급 (월 1회 권장)
- 🔒 사용하지 않는 API 키는 즉시 삭제

### 3. 모니터링
- 📊 API 사용량 정기 모니터링
- 🚨 비정상적인 API 호출 패턴 감지
- 📈 Rate Limiting 준수

## 🚀 다음 단계

API 키를 발급받으셨다면:
1. `.env` 파일에 API 키 설정
2. `test_production_apis.py` 실행하여 연결 테스트
3. 실제 데이터 수집 시작

**우선 1-2개 거래소부터 시작하는 것을 권장합니다!**
