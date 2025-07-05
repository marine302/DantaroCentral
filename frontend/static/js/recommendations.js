// Recommendations Page JavaScript - AI 추천 코인 전용 페이지

class RecommendationsApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.recommendations = [];
        this.currentFilter = 'all';
        this.currentSort = 'score';
        
        this.init();
    }
    
    init() {
        console.log('🚀 Recommendations App 초기화 시작');
        
        // WebSocket 연결 (추천 업데이트용)
        this.connectWebSocket();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 초기 추천 데이터 로드
        this.loadRecommendations();
        
        // 주기적 업데이트 (5분마다)
        setInterval(() => {
            this.loadRecommendations();
        }, 300000);
        
        console.log('✅ Recommendations App 초기화 완료');
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
            };
            
        } catch (error) {
            console.error('❌ WebSocket 연결 실패:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'recommendations':
                this.handleRecommendationsUpdate(data);
                break;
            default:
                // 다른 메시지는 무시
                break;
        }
    }
    
    handleRecommendationsUpdate(data) {
        console.log('⭐ 추천 데이터 WebSocket 업데이트:', data.data.length, '개');
        this.recommendations = data.data;
        this.displayRecommendations();
        this.updateCounts();
    }
    
    async loadRecommendations() {
        try {
            console.log('⭐ 추천 코인 로드 중...');
            
            // 새로운 거래량 기반 추천 API 사용
            const response = await fetch('/api/v1/top-coins-by-volume?top_n=50');
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ 추천 코인 응답:', result);
                
                if (result.success && result.data) {
                    this.recommendations = result.data.top_coins || [];
                    this.displayRecommendations();
                    this.updateCounts();
                    this.updateAnalysisInfo(result.data);
                } else {
                    console.error('❌ 추천 코인 로드 실패:', result.error || '알 수 없는 오류');
                    this.showError('추천 데이터를 가져올 수 없습니다.');
                }
            } else {
                console.error(`❌ 추천 코인 로드 실패: HTTP ${response.status}`);
                this.showError(`서버 오류: ${response.status}`);
            }
        } catch (error) {
            console.error('❌ 추천 코인 로드 오류:', error);
            this.showError('네트워크 오류가 발생했습니다.');
        }
    }
    
    displayRecommendations() {
        const container = document.getElementById('recommendations-container');
        if (!container) return;
        
        const filteredRecs = this.getFilteredRecommendations();
        const sortedRecs = this.getSortedRecommendations(filteredRecs);
        
        if (sortedRecs.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-info-circle fa-2x mb-3 text-muted"></i>
                    <h5>추천 코인이 없습니다</h5>
                    <p class="text-muted">필터 조건을 변경하거나 데이터를 새로고침해보세요.</p>
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
                                <th>순위</th>
                                <th>코인</th>
                                <th>거래소</th>
                                <th>현재가</th>
                                <th>24h 변화</th>
                                <th>거래량</th>
                                <th>점수</th>
                                <th>지지선</th>
                                <th>저항선</th>
                                <th>진입가</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        sortedRecs.forEach((rec, index) => {
            const changePercent = (rec.change_24h || 0);
            const changeClass = changePercent >= 0 ? 'text-success' : 'text-danger';
            
            html += `
                <tr>
                    <td><span class="badge bg-secondary">${rec.volume_rank || index + 1}</span></td>
                    <td><strong>${rec.symbol}</strong></td>
                    <td><span class="badge bg-primary">${rec.exchange}</span></td>
                    <td>${this.formatPrice(rec.current_price, rec.currency)}</td>
                    <td class="${changeClass}">${changePercent.toFixed(2)}%</td>
                    <td>${this.formatVolume(rec.volume_24h)}</td>
                    <td><span class="badge bg-warning">${rec.recommendation_score || 0}</span></td>
                    <td class="text-success">${this.formatPrice(rec.support_level, rec.currency)}</td>
                    <td class="text-danger">${this.formatPrice(rec.resistance_level, rec.currency)}</td>
                    <td class="text-info">${this.formatPrice(rec.entry_price_suggestion, rec.currency)}</td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    getFilteredRecommendations() {
        if (this.currentFilter === 'all') {
            return this.recommendations;
        }
        
        return this.recommendations.filter(rec => {
            switch (this.currentFilter) {
                case 'okx':
                    return rec.exchange === 'OKX';
                case 'upbit':
                    return rec.exchange === 'Upbit';
                case 'coinone':
                    return rec.exchange === 'Coinone';
                default:
                    return true;
            }
        });
    }
    
    getSortedRecommendations(recommendations) {
        return [...recommendations].sort((a, b) => {
            switch (this.currentSort) {
                case 'score':
                    return (b.recommendation_score || 0) - (a.recommendation_score || 0);
                case 'volume':
                    return (b.volume_24h || 0) - (a.volume_24h || 0);
                case 'change':
                    return (b.change_24h || 0) - (a.change_24h || 0);
                case 'rank':
                    return (a.volume_rank || 999) - (b.volume_rank || 999);
                default:
                    return (b.recommendation_score || 0) - (a.recommendation_score || 0);
            }
        });
    }
    
    updateCounts() {
        const totalCount = this.recommendations.length;
        const okxCount = this.recommendations.filter(rec => rec.exchange === 'OKX').length;
        const upbitCount = this.recommendations.filter(rec => rec.exchange === 'Upbit').length;
        const coinoneCount = this.recommendations.filter(rec => rec.exchange === 'Coinone').length;
        
        // 기존 요소들이 있다면 업데이트, 없다면 무시
        const totalElement = document.getElementById('total-analyzed');
        if (totalElement) totalElement.textContent = totalCount;
        
        const okxElement = document.getElementById('okx-count');
        if (okxElement) okxElement.textContent = okxCount;
        
        const upbitElement = document.getElementById('upbit-count');
        if (upbitElement) upbitElement.textContent = upbitCount;
        
        const coinoneElement = document.getElementById('coinone-count');
        if (coinoneElement) coinoneElement.textContent = coinoneCount;
    }
    
    updateAnalysisInfo(result) {
        const lastUpdateElement = document.getElementById('last-analysis-time');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleString('ko-KR');
        }
        
        const statsElement = document.getElementById('analysis-stats');
        if (statsElement && result.stats) {
            statsElement.textContent = `기준: ${result.stats.criteria || '거래량'} | 최소 거래량: ${this.formatVolume(result.stats.min_volume_threshold || 0)}`;
        }
    }
    
    setupEventListeners() {
        // 필터 버튼들
        document.querySelectorAll('[data-filter]').forEach(button => {
            button.addEventListener('click', (e) => {
                // 활성 버튼 변경
                document.querySelectorAll('[data-filter]').forEach(btn => 
                    btn.classList.remove('active'));
                button.classList.add('active');
                
                this.currentFilter = button.dataset.filter;
                this.displayRecommendations();
            });
        });
    }
    
    sortBy(criteria) {
        this.currentSort = criteria;
        this.displayRecommendations();
    }
    
    refreshRecommendations() {
        this.loadRecommendations();
    }
    
    showError(message) {
        const container = document.getElementById('recommendations-container');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-exclamation-triangle fa-2x mb-3 text-warning"></i>
                    <h5>오류 발생</h5>
                    <p class="text-muted">${message}</p>
                    <button class="btn btn-primary" onclick="window.recommendationsApp.refreshRecommendations()">
                        <i class="fas fa-sync"></i> 다시 시도
                    </button>
                </div>
            `;
        }
    }
    
    // 유틸리티 함수들
    getStrengthClass(strength) {
        const s = strength.toLowerCase();
        if (s.includes('strong')) return 'strength-strong';
        if (s.includes('moderate')) return 'strength-moderate';
        return 'strength-weak';
    }
    
    getScoreClass(score) {
        if (score >= 70) return 'score-high';
        if (score >= 40) return 'score-medium';
        return 'score-low';
    }
    
    getStrengthBadgeClass(strength) {
        const s = strength.toLowerCase();
        if (s.includes('strong')) return 'success';
        if (s.includes('moderate')) return 'warning';
        return 'danger';
    }
    
    getStrengthText(strength) {
        const s = strength.toLowerCase();
        if (s.includes('strong')) return '강력 추천';
        if (s.includes('moderate')) return '보통 추천';
        return '약한 추천';
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
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        switch (status) {
            case 'connected':
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> 연결됨';
                statusElement.className = 'badge bg-success me-3';
                break;
            case 'disconnected':
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> 연결 끊김';
                statusElement.className = 'badge bg-danger me-3';
                break;
        }
    }
}

// 글로벌 함수들
function showDetails(symbol) {
    alert(`${symbol}의 상세 분석 정보를 표시합니다. (추후 구현)`);
}

function addToWatchlist(symbol) {
    alert(`${symbol}을(를) 관심목록에 추가했습니다. (추후 구현)`);
}
