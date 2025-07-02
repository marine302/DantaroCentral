#!/usr/bin/env python3
"""
알림 서비스
차익거래 기회 및 김치 프리미엄 알림 전담
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.services.arbitrage_analyzer import ArbitrageOpportunity, KimchiPremium


class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AlertConfig:
    """알림 설정"""
    min_spread_for_alert: float = 2.0  # 최소 스프레드 알림 기준 (%)
    min_premium_for_alert: float = 3.0  # 최소 프리미엄 알림 기준 (%)
    critical_spread_threshold: float = 5.0  # 긴급 스프레드 기준 (%)
    critical_premium_threshold: float = 8.0  # 긴급 프리미엄 기준 (%)
    max_alerts_per_minute: int = 10  # 분당 최대 알림 수
    enable_console_alerts: bool = True  # 콘솔 알림 활성화
    enable_log_alerts: bool = True  # 로그 알림 활성화


@dataclass
class Alert:
    """알림 데이터"""
    timestamp: datetime
    level: AlertLevel
    type: str  # 'arbitrage' or 'premium'
    symbol: str
    message: str
    details: Dict
    processed: bool = False


class NotificationService:
    """알림 서비스"""
    
    def __init__(self, config: AlertConfig = None):
        self.logger = logging.getLogger(f"{__name__}.NotificationService")
        
        # 설정
        self.config = config or AlertConfig()
        
        # 알림 저장소
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # 알림 제한 (스팸 방지)
        self.alert_counts = {}  # {minute: count}
        
        # 외부 알림 핸들러들
        self.alert_handlers: List[Callable] = []
        
        # 통계
        self.stats = {
            'total_alerts': 0,
            'alerts_by_level': {level.value: 0 for level in AlertLevel},
            'alerts_by_type': {},
            'last_alert_time': None
        }
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """외부 알림 핸들러 추가"""
        self.alert_handlers.append(handler)
        self.logger.info("알림 핸들러 추가됨")
    
    def process_arbitrage_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """차익거래 기회 알림 처리"""
        try:
            for opp in opportunities:
                if opp.spread_percentage >= self.config.min_spread_for_alert:
                    level = AlertLevel.CRITICAL if opp.spread_percentage >= self.config.critical_spread_threshold else AlertLevel.WARNING
                    
                    profit_usd = opp.potential_profit
                    profit_krw = profit_usd * 1300
                    
                    message = (
                        f"차익거래 기회 발견: {opp.symbol} "
                        f"{opp.buy_exchange}(${opp.buy_price:.6f}) → "
                        f"{opp.sell_exchange}(${opp.sell_price:.6f}) "
                        f"스프레드: {opp.spread_percentage:.2f}%"
                    )
                    
                    details = {
                        'symbol': opp.symbol,
                        'buy_exchange': opp.buy_exchange,
                        'sell_exchange': opp.sell_exchange,
                        'buy_price': opp.buy_price,
                        'sell_price': opp.sell_price,
                        'spread_percentage': opp.spread_percentage,
                        'potential_profit_usd': profit_usd,
                        'potential_profit_krw': profit_krw,
                        'volume_score': opp.volume_score,
                        'confidence_score': opp.confidence_score
                    }
                    
                    self._create_alert(
                        level=level,
                        alert_type='arbitrage',
                        symbol=opp.symbol,
                        message=message,
                        details=details
                    )
                    
        except Exception as e:
            self.logger.error(f"차익거래 기회 알림 처리 오류: {e}")
    
    def process_kimchi_premiums(self, premiums: List[KimchiPremium]):
        """김치 프리미엄 알림 처리"""
        try:
            for premium in premiums:
                if abs(premium.premium_percentage) >= self.config.min_premium_for_alert:
                    level = AlertLevel.CRITICAL if abs(premium.premium_percentage) >= self.config.critical_premium_threshold else AlertLevel.WARNING
                    
                    direction = "🔥 높은 프리미엄" if premium.premium_percentage > 0 else "❄️ 낮은 프리미엄"
                    sign = "+" if premium.premium_percentage > 0 else ""
                    
                    message = (
                        f"김치 프리미엄 발견: {direction} {premium.symbol} "
                        f"{premium.korean_exchange}(${premium.korean_price:.6f}) vs "
                        f"{premium.international_exchange}(${premium.international_price:.6f}) "
                        f"프리미엄: {sign}{premium.premium_percentage:.2f}%"
                    )
                    
                    details = {
                        'symbol': premium.symbol,
                        'korean_exchange': premium.korean_exchange,
                        'international_exchange': premium.international_exchange,
                        'korean_price': premium.korean_price,
                        'international_price': premium.international_price,
                        'premium_percentage': premium.premium_percentage,
                        'direction': 'positive' if premium.premium_percentage > 0 else 'negative'
                    }
                    
                    self._create_alert(
                        level=level,
                        alert_type='premium',
                        symbol=premium.symbol,
                        message=message,
                        details=details
                    )
                    
        except Exception as e:
            self.logger.error(f"김치 프리미엄 알림 처리 오류: {e}")
    
    def _create_alert(self, level: AlertLevel, alert_type: str, symbol: str, message: str, details: Dict):
        """알림 생성"""
        try:
            # 알림 제한 체크
            if not self._check_alert_rate_limit():
                return
            
            # 알림 객체 생성
            alert = Alert(
                timestamp=datetime.now(),
                level=level,
                type=alert_type,
                symbol=symbol,
                message=message,
                details=details
            )
            
            # 알림 저장
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # 통계 업데이트
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_level'][level.value] += 1
            self.stats['alerts_by_type'][alert_type] = self.stats['alerts_by_type'].get(alert_type, 0) + 1
            self.stats['last_alert_time'] = alert.timestamp
            
            # 알림 처리
            self._process_alert(alert)
            
            # 오래된 알림 정리 (최근 100개만 유지)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
                
        except Exception as e:
            self.logger.error(f"알림 생성 오류: {e}")
    
    def _check_alert_rate_limit(self) -> bool:
        """알림 속도 제한 체크"""
        try:
            current_minute = datetime.now().replace(second=0, microsecond=0)
            
            # 현재 분의 알림 수 확인
            current_count = self.alert_counts.get(current_minute, 0)
            
            if current_count >= self.config.max_alerts_per_minute:
                return False
            
            # 알림 수 증가
            self.alert_counts[current_minute] = current_count + 1
            
            # 오래된 카운트 정리 (최근 5분만 유지)
            cutoff_time = current_minute.timestamp() - 300  # 5분 전
            self.alert_counts = {
                minute: count for minute, count in self.alert_counts.items()
                if minute.timestamp() > cutoff_time
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"알림 속도 제한 체크 오류: {e}")
            return True  # 오류 시 허용
    
    def _process_alert(self, alert: Alert):
        """알림 처리 (로깅, 콘솔 출력, 외부 핸들러 호출)"""
        try:
            # 로그 출력
            if self.config.enable_log_alerts:
                log_level = {
                    AlertLevel.INFO: logging.INFO,
                    AlertLevel.WARNING: logging.WARNING,
                    AlertLevel.CRITICAL: logging.CRITICAL
                }.get(alert.level, logging.INFO)
                
                self.logger.log(log_level, f"[{alert.level.value}] {alert.message}")
            
            # 콘솔 출력
            if self.config.enable_console_alerts:
                level_emoji = {
                    AlertLevel.INFO: "ℹ️",
                    AlertLevel.WARNING: "⚠️",
                    AlertLevel.CRITICAL: "🚨"
                }.get(alert.level, "📢")
                
                print(f"{level_emoji} [{alert.timestamp.strftime('%H:%M:%S')}] {alert.message}")
                
                # 상세 정보 출력 (CRITICAL 레벨만)
                if alert.level == AlertLevel.CRITICAL:
                    if alert.type == 'arbitrage':
                        print(f"    💰 예상 수익: ${alert.details['potential_profit_usd']:.6f} (₩{alert.details['potential_profit_krw']:.0f})")
                        print(f"    🏆 신뢰도: {alert.details['confidence_score']:.1f}%, 거래량 점수: {alert.details['volume_score']:.1f}%")
                    elif alert.type == 'premium':
                        direction = "프리미엄" if alert.details['premium_percentage'] > 0 else "디스카운트"
                        print(f"    📊 {direction}: {abs(alert.details['premium_percentage']):.2f}%")
            
            # 외부 핸들러 호출
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger.error(f"외부 알림 핸들러 오류: {e}")
            
            alert.processed = True
            
        except Exception as e:
            self.logger.error(f"알림 처리 오류: {e}")
    
    def get_recent_alerts(self, limit: int = 20, level: AlertLevel = None) -> List[Alert]:
        """최근 알림 반환"""
        alerts = self.alerts
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_stats(self) -> Dict:
        """알림 통계 반환"""
        return {
            **self.stats,
            'pending_alerts': len([alert for alert in self.alerts if not alert.processed]),
            'total_alerts_stored': len(self.alerts)
        }
    
    def clear_alerts(self):
        """알림 목록 정리"""
        self.alerts.clear()
        self.logger.info("알림 목록 정리 완료")
