// Arbitrage Page JavaScript - 차익거래 기회 전용 페이지

class ArbitrageApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.arbitrageOpportunities = [];
        this.currentFilter = 'all';
        this.currentSort = 'profit';
        
        this.init();
    }
    
    init() {
        console.log('🚀 Arbitrage App 초기화 시작');
        
        // WebSocket 연결 (실시간 업데이트용)
        this.connectWebSocket();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 초기 차익거래 데이터 로드
        this.loadArbitrageOpportunities();
        
        // 주기적 업데이트 (2분마다 - 차익거래는 빠른 업데이트 필요)
        setInterval(() => {
            this.loadArbitrageOpportunities();
        }, 120000);
        
        console.log('✅ Arbitrage App 초기화 완료');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket 연결 성공');
                this.isConnected = true;
                this.updateConnectionStatus('connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('❌ WebSocket 메시지 파싱 오류:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('❌ WebSocket 연결 종료');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                
                // 5초 후 재연결 시도
                setTimeout(() => {
                    this.connectWebSocket();
                }, 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket 오류:', error);
            };
            
        } catch (error) {
            console.error('❌ WebSocket 연결 실패:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'arbitrage_update') {
            console.log('📊 차익거래 실시간 업데이트:', data);
            // 실시간 업데이트가 있으면 데이터 새로고침
            this.loadArbitrageOpportunities();
        }
    }
    
    async loadArbitrageOpportunities() {
        try {
            console.log('⚖️ 차익거래 기회 로드 중...');
            this.updateLoadingStatus(true);
            
            const response = await fetch('/api/v1/arbitrage-opportunities', {
                headers: {
                    'Authorization': 'Bearer dantaro-central-2024'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ 차익거래 기회 응답:', result);
                
                if (result.success && result.data) {
                    this.arbitrageOpportunities = result.data.arbitrage_opportunities || [];
                    this.displayArbitrageOpportunities();
                    this.updateCounts();
                    this.updateAnalysisInfo(result.data);
                } else {
                    console.error('❌ 차익거래 데이터 로드 실패:', result.error || '알 수 없는 오류');
                    this.showError('차익거래 데이터를 가져올 수 없습니다.');
                }
            } else {
                console.error(`❌ 차익거래 데이터 로드 실패: HTTP ${response.status}`);
                this.showError(`서버 오류: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ 차익거래 데이터 로드 오류:', error);
            this.showError('네트워크 오류가 발생했습니다.');
        } finally {
            this.updateLoadingStatus(false);
        }
    }
    
    displayArbitrageOpportunities() {
        const container = document.getElementById('arbitrage-container');
        if (!container) return;
        
        const filteredOpps = this.getFilteredOpportunities();
        const sortedOpps = this.getSortedOpportunities(filteredOpps);
        
        if (sortedOpps.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-search fa-2x mb-3 text-muted"></i>
                    <h5>차익거래 기회가 없습니다</h5>
                    <p class="text-muted">현재 추천 코인들 중에서 수익성 있는 차익거래 기회를 찾을 수 없습니다.</p>
                </div>
            `;
            return;
        }
        
        // 테이블 형태로 표시
        let html = `
            <div class="col-12">
                <div class="table-responsive">
                    <table class="table table-dark table-striped">
                        <thead>
                            <tr>
                                <th>코인</th>
                                <th>매수 거래소</th>
                                <th>매수가</th>
                                <th>매도 거래소</th>
                                <th>매도가</th>
                                <th>수익률</th>
                                <th>예상 수익</th>
                                <th>거래량</th>
                                <th>업데이트</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        sortedOpps.forEach((opp, index) => {
            const profitClass = opp.profit_rate >= 3.0 ? 'text-success' : 
                               opp.profit_rate >= 1.0 ? 'text-warning' : 'text-danger';
            
            html += `
                <tr>
                    <td><strong>${opp.symbol}</strong></td>
                    <td><span class="badge bg-success">${opp.buy_exchange}</span></td>
                    <td>${this.formatPrice(opp.buy_price, this.getCurrencyFromExchange(opp.buy_exchange))}</td>
                    <td><span class="badge bg-danger">${opp.sell_exchange}</span></td>
                    <td>${this.formatPrice(opp.sell_price, this.getCurrencyFromExchange(opp.sell_exchange))}</td>
                    <td class="${profitClass}"><strong>${opp.profit_rate.toFixed(2)}%</strong></td>
                    <td class="text-success">${this.formatPrice(opp.profit_amount, this.getCurrencyFromExchange(opp.sell_exchange))}</td>
                    <td>${this.formatVolume(opp.volume_24h)}</td>
                    <td><small>${this.formatTime(opp.timestamp)}</small></td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
                <div class="col-12 mt-3">
                    <div class="alert alert-warning" role="alert">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>주의:</strong> 실제 거래 시 수수료, 슬리피지, 송금 시간 등을 고려해야 합니다.
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    getFilteredOpportunities() {
        if (this.currentFilter === 'all') {
            return this.arbitrageOpportunities;
        }
        
        return this.arbitrageOpportunities.filter(opp => {
            switch (this.currentFilter) {
                case 'high-profit':
                    return opp.profit_rate >= 3.0;
                case 'medium-profit':
                    return opp.profit_rate >= 1.0 && opp.profit_rate < 3.0;
                case 'domestic':
                    return ['Upbit', 'Coinone'].includes(opp.buy_exchange) && 
                           ['Upbit', 'Coinone'].includes(opp.sell_exchange);
                case 'international':
                    return opp.buy_exchange === 'OKX' || opp.sell_exchange === 'OKX';
                default:
                    return true;
            }
        });
    }
    
    getSortedOpportunities(opportunities) {
        return [...opportunities].sort((a, b) => {
            switch (this.currentSort) {
                case 'profit':
                    return b.profit_rate - a.profit_rate;
                case 'volume':
                    return (b.volume_24h || 0) - (a.volume_24h || 0);
                case 'amount':
                    return (b.profit_amount || 0) - (a.profit_amount || 0);
                default:
                    return b.profit_rate - a.profit_rate;
            }
        });
    }
    
    updateCounts() {
        const totalCount = this.arbitrageOpportunities.length;
        const highProfitCount = this.arbitrageOpportunities.filter(opp => opp.profit_rate >= 3.0).length;
        const mediumProfitCount = this.arbitrageOpportunities.filter(opp => opp.profit_rate >= 1.0 && opp.profit_rate < 3.0).length;
        const domesticCount = this.arbitrageOpportunities.filter(opp => 
            ['Upbit', 'Coinone'].includes(opp.buy_exchange) && 
            ['Upbit', 'Coinone'].includes(opp.sell_exchange)
        ).length;
        
        // 요소들이 있다면 업데이트
        const totalElement = document.getElementById('total-opportunities');
        if (totalElement) totalElement.textContent = totalCount;
        
        const highProfitElement = document.getElementById('high-profit-count');
        if (highProfitElement) highProfitElement.textContent = highProfitCount;
        
        const mediumProfitElement = document.getElementById('medium-profit-count');
        if (mediumProfitElement) mediumProfitElement.textContent = mediumProfitCount;
        
        const domesticElement = document.getElementById('domestic-count');
        if (domesticElement) domesticElement.textContent = domesticCount;
    }
    
    updateAnalysisInfo(result) {
        const lastUpdateElement = document.getElementById('last-analysis-time');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleString('ko-KR');
        }
        
        const avgProfitElement = document.getElementById('avg-profit-rate');
        if (avgProfitElement && this.arbitrageOpportunities.length > 0) {
            const avgProfit = this.arbitrageOpportunities.reduce((sum, opp) => sum + opp.profit_rate, 0) / this.arbitrageOpportunities.length;
            avgProfitElement.textContent = avgProfit.toFixed(2) + '%';
        }
    }
    
    setupEventListeners() {
        // 필터 버튼들
        document.querySelectorAll('[data-filter]').forEach(button => {
            button.addEventListener('click', (e) => {
                // 활성 버튼 변경
                document.querySelectorAll('[data-filter]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                
                // 필터 적용
                this.currentFilter = e.target.dataset.filter;
                this.displayArbitrageOpportunities();
            });
        });
        
        // 정렬 버튼들
        document.querySelectorAll('[data-sort]').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('[data-sort]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                
                this.currentSort = e.target.dataset.sort;
                this.displayArbitrageOpportunities();
            });
        });
        
        // 새로고침 버튼
        const refreshButton = document.getElementById('refresh-arbitrage');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                this.refreshArbitrageOpportunities();
            });
        }
    }
    
    refreshArbitrageOpportunities() {
        console.log('🔄 차익거래 데이터 새로고침');
        this.loadArbitrageOpportunities();
    }
    
    updateLoadingStatus(isLoading) {
        const loadingElement = document.getElementById('loading-indicator');
        if (loadingElement) {
            loadingElement.style.display = isLoading ? 'block' : 'none';
        }
    }
    
    showError(message) {
        const container = document.getElementById('arbitrage-container');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3 text-warning"></i>
                    <h5>오류 발생</h5>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-refresh"></i> 새로고침
                    </button>
                </div>
            `;
        }
    }
    
    getProfitClass(profitRate) {
        if (profitRate >= 3.0) return 'profit-high';
        if (profitRate >= 1.0) return 'profit-medium';
        return 'profit-low';
    }
    
    formatPrice(price, currency = 'USD') {
        if (!price || price === 0) return 'N/A';
        
        const symbol = currency === 'KRW' ? '₩' : '$';
        
        if (currency === 'KRW') {
            if (price >= 1000000) {
                return symbol + (price / 1000000).toFixed(2) + 'M';
            } else if (price >= 1000) {
                return symbol + (price / 1000).toFixed(0) + 'K';
            } else {
                return symbol + price.toFixed(0);
            }
        } else {
            if (price > 1000000) {
                return symbol + (price / 1000000).toFixed(2) + 'M';
            } else if (price > 1000) {
                return symbol + (price / 1000).toFixed(2) + 'K';
            } else if (price < 0.01) {
                return symbol + price.toFixed(6);
            } else {
                return symbol + price.toFixed(2);
            }
        }
    }
    
    formatVolume(volume) {
        if (!volume || volume === 0) return 'N/A';
        
        if (volume >= 1000000000) {
            return '$' + (volume / 1000000000).toFixed(1) + 'B';
        } else if (volume >= 1000000) {
            return '$' + (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return '$' + (volume / 1000).toFixed(1) + 'K';
        } else {
            return '$' + volume.toLocaleString();
        }
    }
    
    formatTime(timeString) {
        try {
            const date = new Date(timeString);
            return date.toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } catch (e) {
            return 'N/A';
        }
    }
    
    getCurrencyFromExchange(exchange) {
        switch (exchange) {
            case 'Upbit':
            case 'Coinone':
                return 'KRW';
            case 'OKX':
            default:
                return 'USD';
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.textContent = status === 'connected' ? '연결됨' : '연결 끊김';
        }
    }
}

// 전역 함수들
function analyzeOpportunity(symbol, buyExchange, sellExchange) {
    alert(`${symbol}의 ${buyExchange} → ${sellExchange} 차익거래 상세 분석 (추후 구현)`);
}

function addToWatchlist(symbol) {
    alert(`${symbol}을(를) 관심목록에 추가했습니다. (추후 구현)`);
}

// 페이지 로드 시 앱 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 차익거래 페이지 로드 완료');
    window.arbitrageApp = new ArbitrageApp();
});
