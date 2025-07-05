"""
Support level calculator for trading strategies.

This module provides various methods to calculate support levels
based on historical price data and different time horizons.
"""
from typing import List, Dict, Optional
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import statistics
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupportType(Enum):
    """Types of support level calculations."""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"


@dataclass
class SupportLevel:
    """Data class for support level calculation results."""
    price: Decimal
    confidence: float
    support_type: SupportType
    calculation_method: str
    lookback_days: int
    metadata: Dict


class SupportLevelCalculator:
    """
    Calculate various support levels for trading.
    
    Provides three different calculation methods:
    - Aggressive: 7-day lookback for short-term support
    - Moderate: 30-day lookback for medium-term support  
    - Conservative: 90-day lookback for long-term support
    """
    
    @staticmethod
    def calculate_support_levels(price_history: List[Dict]) -> Dict[str, SupportLevel]:
        """
        Calculate all three types of support levels.
        
        Args:
            price_history: List of price data with 'low', 'high', 'close', 'timestamp'
            
        Returns:
            Dictionary with support levels for each type
        """
        try:
            if not price_history:
                raise ValueError("Price history cannot be empty")
            
            # Sort by timestamp to ensure correct order
            sorted_history = sorted(price_history, key=lambda x: x.get('timestamp', 0))
            
            results = {}
            
            # Calculate aggressive support (7 days)
            aggressive = SupportLevelCalculator.calculate_aggressive_support(sorted_history)
            if aggressive:
                results['aggressive'] = aggressive
            
            # Calculate moderate support (30 days)
            moderate = SupportLevelCalculator.calculate_moderate_support(sorted_history)
            if moderate:
                results['moderate'] = moderate
            
            # Calculate conservative support (90 days)
            conservative = SupportLevelCalculator.calculate_conservative_support(sorted_history)
            if conservative:
                results['conservative'] = conservative
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to calculate support levels: {e}")
            return {}
    
    @staticmethod
    def calculate_aggressive_support(price_history: List[Dict], days: Optional[int] = None) -> Optional[SupportLevel]:
        """
        Calculate aggressive support level using recent lows.
        
        Args:
            price_history: Historical price data
            days: Number of days to look back
            
        Returns:
            SupportLevel object or None if calculation fails
        """
        if days is None:
            days = getattr(settings, "support_aggressive_days", 7)
        try:
            recent_data = price_history[-days:] if len(price_history) >= days else price_history
            
            if not recent_data:
                return None
            
            # Extract low prices
            lows = [Decimal(str(candle.get('low', candle.get('close', 0)))) for candle in recent_data]
            lows = [low for low in lows if low > 0]
            
            if not lows:
                return None
            
            # Method: Use the lowest low with slight buffer
            min_low = min(lows)
            
            # Add small buffer below minimum (1-2%)
            buffer_factor = Decimal('0.98')  # 2% below minimum
            support_price = min_low * buffer_factor
            
            # Calculate confidence based on how many times this level was tested
            confidence = SupportLevelCalculator._calculate_confidence(lows, support_price)
            
            return SupportLevel(
                price=support_price,
                confidence=confidence,
                support_type=SupportType.AGGRESSIVE,
                calculation_method="recent_lows_with_buffer",
                lookback_days=days,
                metadata={
                    'min_low': float(min_low),
                    'buffer_factor': float(buffer_factor),
                    'data_points': len(lows),
                    'price_range': {
                        'min': float(min(lows)),
                        'max': float(max(lows))
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"[SupportLevelCalculator] Aggressive support calc error: {e}")
            return None
    
    @staticmethod
    def calculate_moderate_support(price_history: List[Dict], days: Optional[int] = None) -> Optional[SupportLevel]:
        """
        Calculate moderate support level using multiple methods.
        
        Args:
            price_history: Historical price data
            days: Number of days to look back
            
        Returns:
            SupportLevel object or None if calculation fails
        """
        if days is None:
            days = getattr(settings, "support_moderate_days", 30)
        try:
            recent_data = price_history[-days:] if len(price_history) >= days else price_history
            
            if len(recent_data) < 7:  # Need minimum data
                return None
            
            # Extract prices
            lows = [Decimal(str(candle.get('low', candle.get('close', 0)))) for candle in recent_data]
            closes = [Decimal(str(candle.get('close', 0))) for candle in recent_data]
            
            lows = [low for low in lows if low > 0]
            closes = [close for close in closes if close > 0]
            
            if not lows or not closes:
                return None
            
            # Method 1: Statistical support (20th percentile of lows)
            sorted_lows = sorted(lows)
            percentile_20_idx = int(len(sorted_lows) * 0.2)
            statistical_support = sorted_lows[percentile_20_idx]
            
            # Method 2: Moving average support
            avg_close = sum(closes) / len(closes)
            ma_support = Decimal(str(avg_close)) * Decimal('0.95')  # 5% below average
            
            # Method 3: Pivot point support
            recent_high = max(candle.get('high', candle.get('close', 0)) for candle in recent_data[-7:])
            recent_low = min(candle.get('low', candle.get('close', 0)) for candle in recent_data[-7:])
            recent_close = recent_data[-1].get('close', 0)
            
            pivot = (Decimal(str(recent_high)) + Decimal(str(recent_low)) + Decimal(str(recent_close))) / 3
            pivot_support = pivot - (Decimal(str(recent_high)) - pivot)
            
            # Combine methods (weighted average)
            support_price = (
                statistical_support * Decimal('0.4') +
                ma_support * Decimal('0.3') +
                pivot_support * Decimal('0.3')
            )
            
            # Calculate confidence
            confidence = SupportLevelCalculator._calculate_confidence(lows, support_price)
            
            return SupportLevel(
                price=support_price,
                confidence=confidence,
                support_type=SupportType.MODERATE,
                calculation_method="combined_statistical_ma_pivot",
                lookback_days=days,
                metadata={
                    'statistical_support': float(statistical_support),
                    'ma_support': float(ma_support),
                    'pivot_support': float(pivot_support),
                    'data_points': len(lows),
                    'avg_close': float(avg_close)
                }
            )
            
        except Exception as e:
            logger.error(f"[SupportLevelCalculator] Moderate support calc error: {e}")
            return None
    
    @staticmethod
    def calculate_conservative_support(price_history: List[Dict], days: Optional[int] = None) -> Optional[SupportLevel]:
        """
        Calculate conservative support level using long-term analysis.
        
        Args:
            price_history: Historical price data
            days: Number of days to look back
            
        Returns:
            SupportLevel object or None if calculation fails
        """
        if days is None:
            days = getattr(settings, "support_conservative_days", 90)
        try:
            recent_data = price_history[-days:] if len(price_history) >= days else price_history
            
            if len(recent_data) < 30:  # Need substantial data for conservative calculation
                return None
            
            # Extract prices
            lows = [Decimal(str(candle.get('low', candle.get('close', 0)))) for candle in recent_data]
            lows = [low for low in lows if low > 0]
            
            if not lows:
                return None
            
            # Method 1: Long-term statistical support (10th percentile)
            sorted_lows = sorted(lows)
            percentile_10_idx = int(len(sorted_lows) * 0.1)
            long_term_support = sorted_lows[percentile_10_idx]
            
            # Method 2: Significant low detection
            significant_lows = SupportLevelCalculator._find_significant_lows(recent_data)
            significant_support = min(significant_lows) if significant_lows else long_term_support
            
            # Method 3: Trend line support
            trend_support = SupportLevelCalculator._calculate_trend_support(recent_data)
            
            # Conservative approach: Use the most pessimistic (lowest) value
            support_candidates = [long_term_support, significant_support]
            if trend_support:
                support_candidates.append(trend_support)
            
            support_price = min(support_candidates)
            
            # Apply additional conservative buffer
            conservative_buffer = Decimal('0.95')  # 5% additional buffer
            support_price *= conservative_buffer
            
            # Calculate confidence (conservative tends to have higher confidence)
            confidence = min(SupportLevelCalculator._calculate_confidence(lows, support_price) + 0.1, 1.0)
            
            return SupportLevel(
                price=support_price,
                confidence=confidence,
                support_type=SupportType.CONSERVATIVE,
                calculation_method="long_term_statistical_significant_trend",
                lookback_days=days,
                metadata={
                    'long_term_support': float(long_term_support),
                    'significant_support': float(significant_support),
                    'trend_support': float(trend_support) if trend_support else None,
                    'conservative_buffer': float(conservative_buffer),
                    'data_points': len(lows),
                    'significant_lows_count': len(significant_lows)
                }
            )
            
        except Exception as e:
            logger.error(f"[SupportLevelCalculator] Conservative support calc error: {e}")
            return None
    
    @staticmethod
    def _calculate_confidence(lows: List[Decimal], support_level: Decimal) -> float:
        """
        Calculate confidence score for support level.
        
        Args:
            lows: List of low prices
            support_level: Calculated support level
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            if not lows or support_level <= 0:
                return 0.0
            
            # Count how many lows are near the support level (within 5%)
            tolerance = support_level * Decimal('0.05')
            near_support = sum(1 for low in lows if abs(low - support_level) <= tolerance)
            
            # Base confidence on percentage of prices near support
            base_confidence = min(near_support / len(lows), 0.8)
            
            # Boost confidence if support level is tested multiple times
            if near_support >= 3:
                base_confidence += 0.1
            if near_support >= 5:
                base_confidence += 0.1
            
            return min(base_confidence, 1.0)
            
        except Exception:
            return 0.5  # Default confidence
    
    @staticmethod
    def _find_significant_lows(price_data: List[Dict]) -> List[Decimal]:
        """
        Find significant low points in price data.
        
        A significant low is defined as a local minimum that is lower
        than the surrounding prices within a specified window.
        """
        try:
            if len(price_data) < 5:
                return []
            
            significant_lows = []
            window = 3  # Look 3 periods before and after
            
            for i in range(window, len(price_data) - window):
                current_low = Decimal(str(price_data[i].get('low', price_data[i].get('close', 0))))
                
                # Check if this is a local minimum
                is_significant = True
                
                # Check surrounding periods
                for j in range(i - window, i + window + 1):
                    if j == i:
                        continue
                    
                    compare_low = Decimal(str(price_data[j].get('low', price_data[j].get('close', 0))))
                    
                    if current_low >= compare_low:
                        is_significant = False
                        break
                
                if is_significant and current_low > 0:
                    significant_lows.append(current_low)
            
            return significant_lows
            
        except Exception:
            return []
    
    @staticmethod
    def _calculate_trend_support(price_data: List[Dict]) -> Optional[Decimal]:
        """
        Calculate trend line support using linear regression on lows.
        
        This is a simplified trend line calculation.
        """
        try:
            if len(price_data) < 10:
                return None
            
            # Extract lows with their indices
            lows_with_index = []
            for i, candle in enumerate(price_data):
                low = candle.get('low', candle.get('close', 0))
                if low > 0:
                    lows_with_index.append((i, Decimal(str(low))))
            
            if len(lows_with_index) < 5:
                return None
            
            # Simple linear regression on recent lows
            # Using only the most recent 30% of data for trend
            recent_count = max(5, int(len(lows_with_index) * 0.3))
            recent_lows = lows_with_index[-recent_count:]
            
            # Calculate trend line
            n = len(recent_lows)
            sum_x = sum(x for x, y in recent_lows)
            sum_y = sum(y for x, y in recent_lows)
            sum_xy = sum(x * y for x, y in recent_lows)
            sum_x_squared = sum(x * x for x, y in recent_lows)
            
            # Linear regression formula
            denominator = n * sum_x_squared - sum_x * sum_x
            if abs(denominator) < 1e-10:
                return None
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # Project trend to current position (last index)
            last_index = len(price_data) - 1
            trend_support = slope * last_index + intercept
            
            return max(Decimal(str(trend_support)), Decimal('0'))
            
        except Exception:
            return None
