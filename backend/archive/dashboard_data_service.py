#!/usr/bin/env python3
"""
웹 대시보드를 위한 실시간 데이터 서비스
WebSocket 연결과 실제 데이터 수집을 통합
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.websocket_data_manager import MultiExchangeWebSocketManager
from app.api.v1.endpoints.websocket import connection_manager
from app.core.config import settings
from optimization_config import dantaro_optimizer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DashboardDataService:
    """대시보드를 위한 실시간 데이터 서비스"""
    
    def __init__(self):
        self.websocket_manager = MultiExchangeWebSocketManager()
        self.running = False
        
    async def start(self):
        """서비스 시작"""
        try:
            logger.info("🚀 대시보드 데이터 서비스 시작")
            
            # WebSocket 매니저와 연결
            connection_manager.set_websocket_manager(self.websocket_manager)
            
            # 거래소 설정
            exchange_configs = self._get_exchange_configs()
            await self.websocket_manager.initialize_websockets(exchange_configs)
            
            # WebSocket 연결
            await self.websocket_manager.connect_all_websockets()
            
            # 심볼 구독
            symbols_by_exchange = self._get_symbols_by_exchange()
            await self.websocket_manager.subscribe_to_symbols(symbols_by_exchange)
            
            # 리스닝 시작
            await self.websocket_manager.start_listening()
            
            self.running = True
            logger.info("✅ 대시보드 데이터 서비스 시작 완료")
            
            # 무한 실행
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ 서비스 시작 실패: {e}")
            raise
    
    async def stop(self):
        """서비스 중지"""
        self.running = False
        await self.websocket_manager.disconnect_all()
        logger.info("🛑 대시보드 데이터 서비스 중지")
    
    def _get_exchange_configs(self):
        """거래소 설정 구성"""
        exchange_configs = {}
        
        # OKX 설정
        if hasattr(settings, 'okx_api_key') and settings.okx_api_key:
            exchange_configs['okx'] = {
                'api_key': settings.okx_api_key,
                'secret_key': settings.okx_secret_key,
                'passphrase': settings.okx_passphrase
            }
        else:
            exchange_configs['okx'] = {}
        
        # Upbit 설정 (공개 API)
        exchange_configs['upbit'] = {}
        
        # Coinone 설정
        if hasattr(settings, 'coinone_api_key') and settings.coinone_api_key:
            exchange_configs['coinone'] = {
                'api_key': settings.coinone_api_key,
                'secret_key': settings.coinone_secret_key
            }
        else:
            exchange_configs['coinone'] = {}
        
        # Gate.io 설정
        if hasattr(settings, 'gate_api_key') and settings.gate_api_key:
            exchange_configs['gate'] = {
                'api_key': settings.gate_api_key,
                'secret_key': settings.gate_secret_key
            }
        else:
            exchange_configs['gate'] = {}
        
        return exchange_configs
    
    def _get_symbols_by_exchange(self):
        """거래소별 심볼 매핑"""
        active_symbols = dantaro_optimizer.get_active_symbols()
        
        symbols_by_exchange = {}
        
        # OKX 심볼
        okx_symbols = [symbol for symbol in active_symbols if '-USDT' in symbol]
        if not okx_symbols:
            okx_symbols = ['DOGE-USDT', 'ADA-USDT', 'MATIC-USDT', 'SOL-USDT', 'AVAX-USDT']
        symbols_by_exchange['okx'] = okx_symbols
        
        # Upbit 심볼
        upbit_symbols = [symbol for symbol in active_symbols if 'KRW-' in symbol]
        if not upbit_symbols:
            upbit_symbols = ['KRW-DOGE', 'KRW-ADA', 'KRW-MATIC', 'KRW-SOL', 'KRW-AVAX']
        symbols_by_exchange['upbit'] = upbit_symbols
        
        # Coinone 심볼
        coinone_symbols = []
        for symbol in active_symbols:
            if '-' in symbol:
                base_symbol = symbol.split('-')[0] if symbol.startswith('KRW-') else symbol.split('-')[0]
                coinone_symbols.append(base_symbol)
            else:
                coinone_symbols.append(symbol)
        
        if not coinone_symbols:
            coinone_symbols = ['DOGE', 'ADA', 'MATIC', 'SOL', 'AVAX']
        
        symbols_by_exchange['coinone'] = list(set(coinone_symbols))
        
        # Gate.io 심볼
        gate_symbols = [symbol for symbol in active_symbols if '-USDT' in symbol]
        if not gate_symbols:
            gate_symbols = ['DOGE-USDT', 'ADA-USDT', 'MATIC-USDT', 'SOL-USDT', 'AVAX-USDT']
        symbols_by_exchange['gate'] = gate_symbols
        
        return symbols_by_exchange


class VolumeRecommendationAPI:
    """대시보드용 볼륨 기반 추천 API"""
    
    @staticmethod
    async def get_volume_recommendations():
        """대시보드용 볼륨 기반 추천 데이터"""
        try:
            import aiohttp
            # 내부 API 호출
            async with aiohttp.ClientSession() as session:
                headers = {"X-API-Key": "test-api-key-for-enterprise-servers"}
                
                # 추천 데이터 가져오기
                async with session.get("http://localhost:8001/api/v1/recommendations", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        recommendations = data.get('recommendations', [])
                        
                        # 대시보드 형식으로 변환
                        dashboard_data = []
                        for rec in recommendations[:10]:  # 상위 10개만
                            dashboard_data.append({
                                "symbol": rec.get("symbol", ""),
                                "score": rec.get("total_score", 0),
                                "volume_score": rec.get("volume_score", 0),
                                "volatility_score": rec.get("volatility_score", 0),
                                "price": rec.get("current_price", 0),
                                "change_24h": rec.get("price_change_24h", 0),
                                "volume_24h": rec.get("volume_24h", 0),
                                "strength": rec.get("recommendation_strength", ""),
                                "analysis_method": rec.get("analysis_details", {}).get("analysis_method", "volume_based")
                            })
                        
                        return {
                            "success": True,
                            "recommendations": dashboard_data,
                            "metadata": data.get("metadata", {}),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 호출 실패: {response.status}",
                            "recommendations": [],
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": [],
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """메인 실행 함수"""
    service = DashboardDataService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"❌ 서비스 실행 오류: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
