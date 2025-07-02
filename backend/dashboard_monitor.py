#!/usr/bin/env python3
"""
실시간 대시보드 상태 모니터링 및 자동 진단 시스템
"""
import asyncio
import websockets
import json
import logging
import time
from datetime import datetime
from typing import Dict, List
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardMonitor:
    def __init__(self, server_url="127.0.0.1:8003"):
        self.server_url = server_url
        self.websocket_url = f"ws://{server_url}/ws/realtime"
        self.http_url = f"http://{server_url}"
        
        # 모니터링 상태
        self.is_connected = False
        self.last_message_time = None
        self.message_count = 0
        self.message_types = {}
        self.connection_attempts = 0
        self.errors = []
        
        # 성능 메트릭
        self.connection_start_time = None
        self.avg_message_interval = 0
        self.data_quality_score = 100
        
    async def check_server_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.http_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ HTTP 서버 상태: 정상")
                return True
            else:
                logger.error(f"❌ HTTP 서버 상태: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ HTTP 서버 연결 실패: {e}")
            return False
    
    async def check_dashboard_page(self):
        """대시보드 페이지 로드 확인"""
        try:
            response = requests.get(f"{self.http_url}/dashboard", timeout=5)
            if response.status_code == 200:
                logger.info("✅ 대시보드 페이지: 정상 로드")
                if "dashboard.js" in response.text and "adapter.js" in response.text:
                    logger.info("✅ JavaScript 파일: 정상 포함")
                else:
                    logger.warning("⚠️ JavaScript 파일이 누락될 수 있음")
                return True
            else:
                logger.error(f"❌ 대시보드 페이지 로드 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 대시보드 페이지 접근 실패: {e}")
            return False
    
    async def monitor_websocket(self, duration=60):
        """WebSocket 연결 및 메시지 모니터링"""
        logger.info(f"🔍 WebSocket 모니터링 시작 ({duration}초간)")
        
        try:
            self.connection_attempts += 1
            self.connection_start_time = time.time()
            
            async with websockets.connect(self.websocket_url) as websocket:
                logger.info("✅ WebSocket 연결 성공")
                self.is_connected = True
                
                # 환영 메시지 대기
                try:
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
                    welcome_data = json.loads(welcome_msg)
                    logger.info(f"📨 환영 메시지 수신: {welcome_data.get('type')}")
                    self.record_message(welcome_data)
                except asyncio.TimeoutError:
                    logger.error("❌ 환영 메시지 수신 시간 초과")
                    self.errors.append("환영 메시지 없음")
                
                # 데이터 요청
                request_msg = {"type": "request_data", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(request_msg))
                logger.info("📤 데이터 요청 전송")
                
                # 지정된 시간 동안 메시지 모니터링
                end_time = time.time() + duration
                last_ping_time = time.time()
                
                while time.time() < end_time:
                    try:
                        # 메시지 수신 (타임아웃: 5초)
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        self.record_message(data)
                        
                        # 메시지 타입별 분석
                        msg_type = data.get('type', 'unknown')
                        if msg_type == 'price_update':
                            price_data = data.get('data', {})
                            logger.info(f"💰 가격 업데이트: {len(price_data)}개 항목")
                            self.analyze_price_data(price_data)
                        elif msg_type == 'arbitrage_opportunities':
                            opportunities = data.get('data', [])
                            logger.info(f"🔄 차익거래 기회: {len(opportunities)}개")
                        elif msg_type == 'kimchi_premium':
                            premiums = data.get('data', [])
                            logger.info(f"🇰🇷 김치 프리미엄: {len(premiums)}개")
                        
                    except asyncio.TimeoutError:
                        # 5초간 메시지 없음 - 핑 전송
                        current_time = time.time()
                        if current_time - last_ping_time > 10:  # 10초마다 핑
                            ping_msg = {"type": "ping", "timestamp": datetime.now().isoformat()}
                            await websocket.send(json.dumps(ping_msg))
                            logger.info("📡 핑 메시지 전송")
                            last_ping_time = current_time
                        
                        if current_time - (self.last_message_time or current_time) > 30:
                            logger.warning("⚠️ 30초간 메시지 없음 - 데이터 스트림 문제 가능성")
                            self.errors.append("장시간 메시지 없음")
                
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 오류: {e}")
            self.errors.append(f"WebSocket 오류: {e}")
            self.is_connected = False
    
    def record_message(self, data):
        """메시지 기록 및 분석"""
        current_time = time.time()
        msg_type = data.get('type', 'unknown')
        
        # 메시지 카운트
        self.message_count += 1
        self.message_types[msg_type] = self.message_types.get(msg_type, 0) + 1
        
        # 메시지 간격 계산
        if self.last_message_time:
            interval = current_time - self.last_message_time
            self.avg_message_interval = (self.avg_message_interval + interval) / 2
        
        self.last_message_time = current_time
        
        # 상세 로그
        data_size = len(json.dumps(data))
        logger.info(f"📦 메시지 #{self.message_count}: {msg_type} ({data_size} bytes)")
    
    def analyze_price_data(self, price_data):
        """가격 데이터 품질 분석"""
        if not price_data:
            logger.warning("⚠️ 빈 가격 데이터")
            self.data_quality_score -= 10
            return
        
        valid_count = 0
        for key, item in price_data.items():
            if isinstance(item, dict) and 'price' in item and 'exchange' in item:
                valid_count += 1
            else:
                logger.warning(f"⚠️ 잘못된 가격 데이터 형식: {key}")
                self.data_quality_score -= 5
        
        logger.info(f"📊 유효한 가격 데이터: {valid_count}/{len(price_data)}개")
    
    def generate_report(self):
        """모니터링 리포트 생성"""
        logger.info("=" * 60)
        logger.info("📊 대시보드 모니터링 리포트")
        logger.info("=" * 60)
        
        # 연결 상태
        logger.info(f"🔗 WebSocket 연결: {'성공' if self.is_connected else '실패'}")
        logger.info(f"🔄 연결 시도 횟수: {self.connection_attempts}")
        
        # 메시지 통계
        logger.info(f"📨 총 수신 메시지: {self.message_count}개")
        logger.info(f"⏱️ 평균 메시지 간격: {self.avg_message_interval:.2f}초")
        
        # 메시지 타입별 통계
        logger.info("📋 메시지 타입별 통계:")
        for msg_type, count in self.message_types.items():
            percentage = (count / self.message_count * 100) if self.message_count > 0 else 0
            logger.info(f"  {msg_type}: {count}개 ({percentage:.1f}%)")
        
        # 데이터 품질
        logger.info(f"📈 데이터 품질 점수: {self.data_quality_score}/100")
        
        # 오류 리스트
        if self.errors:
            logger.info("❌ 발견된 문제점:")
            for error in self.errors:
                logger.info(f"  - {error}")
        else:
            logger.info("✅ 문제점 없음")
        
        # 성능 지표
        if self.connection_start_time:
            uptime = time.time() - self.connection_start_time
            logger.info(f"⏳ 모니터링 시간: {uptime:.1f}초")
        
        logger.info("=" * 60)
        
        return {
            "connected": self.is_connected,
            "message_count": self.message_count,
            "message_types": self.message_types,
            "avg_interval": self.avg_message_interval,
            "data_quality": self.data_quality_score,
            "errors": self.errors
        }
    
    def suggest_fixes(self):
        """문제점에 대한 해결책 제안"""
        logger.info("🔧 자동 진단 및 해결책 제안")
        logger.info("-" * 40)
        
        if not self.is_connected:
            logger.info("❌ WebSocket 연결 실패")
            logger.info("  💡 해결책:")
            logger.info("    1. 서버가 실행 중인지 확인")
            logger.info("    2. 포트가 올바른지 확인")
            logger.info("    3. 방화벽 설정 확인")
        
        if self.message_count == 0:
            logger.info("❌ 메시지 수신 없음")
            logger.info("  💡 해결책:")
            logger.info("    1. 데이터 전송 스크립트 실행 확인")
            logger.info("    2. WebSocket 라우터 설정 확인")
        
        if self.avg_message_interval > 10:
            logger.info("❌ 메시지 전송 간격이 너무 큼")
            logger.info("  💡 해결책:")
            logger.info("    1. 데이터 전송 빈도 증가")
            logger.info("    2. 네트워크 지연 확인")
        
        if self.data_quality_score < 80:
            logger.info("❌ 데이터 품질 문제")
            logger.info("  💡 해결책:")
            logger.info("    1. 데이터 형식 검증")
            logger.info("    2. 어댑터 로직 확인")
        
        if "환영 메시지 없음" in self.errors:
            logger.info("❌ 환영 메시지 누락")
            logger.info("  💡 해결책:")
            logger.info("    1. WebSocket 엔드포인트 초기화 로직 확인")
        
    async def run_full_diagnosis(self):
        """전체 진단 실행"""
        logger.info("🚀 대시보드 전체 진단 시작")
        
        # 1. 서버 상태 확인
        server_ok = await self.check_server_health()
        
        # 2. 대시보드 페이지 확인
        page_ok = await self.check_dashboard_page()
        
        # 3. WebSocket 모니터링 (30초간)
        if server_ok:
            await self.monitor_websocket(duration=30)
        
        # 4. 리포트 생성
        report = self.generate_report()
        
        # 5. 해결책 제안
        self.suggest_fixes()
        
        return report

async def main():
    """메인 실행 함수"""
    monitor = DashboardMonitor()
    
    try:
        report = await monitor.run_full_diagnosis()
        
        # 종합 점수 계산
        total_score = 0
        if report["connected"]: total_score += 40
        if report["message_count"] > 0: total_score += 30
        if report["data_quality"] > 80: total_score += 20
        if len(report["errors"]) == 0: total_score += 10
        
        logger.info(f"🎯 종합 대시보드 상태 점수: {total_score}/100")
        
        if total_score >= 80:
            logger.info("🎉 대시보드가 정상적으로 작동하고 있습니다!")
        elif total_score >= 60:
            logger.info("⚠️ 대시보드에 일부 문제가 있지만 기본 기능은 작동합니다.")
        else:
            logger.info("❌ 대시보드에 심각한 문제가 있습니다. 수정이 필요합니다.")
        
    except KeyboardInterrupt:
        logger.info("👋 모니터링 중단됨")
    except Exception as e:
        logger.error(f"💥 진단 중 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
