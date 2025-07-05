// Dantaro Central Dashboard JavaScript - 거래소별 탭 버전

class DantaroDashboard {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        
        // 거래소별 데이터 저장소
        this.exchangeData = {
            'OKX': new Map(),
            'Upbit': new Map(),
            'Coinone': new Map()
        };
        this.kimchiData = [];
        this.recommendationData = [];
        
        // 초기화
        this.init();
    }
    
    init() {
        console.log('🚀 Dantaro Dashboard 초기화 시작 (거래소별 탭 버전)');
        
        // WebSocket 연결
        this.connectWebSocket();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 주기적 업데이트
        this.startPeriodicUpdates();
        
        // 초기 추천 코인 로드
        setTimeout(() => {
            this.loadRecommendations();
        }, 2000); // 2초 후 로드
        
        console.log('✅ Dashboard 초기화 완료');
        this.updateConnectionStatus('connecting');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
        
        console.log(`🔗 WebSocket 연결 시도: ${wsUrl}`);
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('✅ WebSocket 연결 성공');
                this.onWebSocketOpen(event);
            };
            
            this.websocket.onmessage = (event) => {
                this.onWebSocketMessage(event);
            };
            
            this.websocket.onclose = (event) => {
                console.log(`❌ WebSocket 연결 종료: 코드=${event.code}`);
                this.onWebSocketClose(event);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket 오류:', error);
                this.onWebSocketError(error);
            };
            
        } catch (error) {
            console.error('❌ WebSocket 생성 오류:', error);
            this.scheduleReconnect();
        }
    }
    
    onWebSocketOpen(event) {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('connected');
        console.log('🔗 WebSocket 연결됨 - 실시간 데이터 수신 준비 완료');
    }
    
    onWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket 메시지 수신:', data.type);
            
            switch (data.type) {
                case 'welcome':
                    this.handleWelcomeMessage(data);
                    break;
                    
                case 'price_update':
                    this.handlePriceUpdate(data);
                    break;
                    
                case 'kimchi_premium':
                    this.handleKimchiPremium(data);
                    break;
                    
                case 'recommendations':
                    this.handleRecommendations(data);
                    break;
                    
                default:
                    console.log('알 수 없는 메시지 타입:', data.type);
            }
            
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('❌ WebSocket 메시지 파싱 오류:', error);
        }
    }
    
    onWebSocketClose(event) {
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        this.scheduleReconnect();
    }
    
    onWebSocketError(error) {
        this.isConnected = false;
        this.updateConnectionStatus('error');
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} (${this.reconnectDelay}ms 후)`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
        } else {
            console.error('❌ 최대 재연결 시도 횟수 초과');
            this.updateConnectionStatus('failed');
        }
    }
    
    handleWelcomeMessage(data) {
        console.log('👋 환영 메시지:', data.message);
    }
    
    handlePriceUpdate(data) {
        console.log('💰 가격 업데이트:', Object.keys(data.data).length, '개 심볼');
        
        // 거래소별로 데이터 분류
        const exchangeDataCount = { OKX: 0, Upbit: 0, Coinone: 0 };
        
        for (const [key, priceInfo] of Object.entries(data.data)) {
            const exchange = priceInfo.exchange;
            if (this.exchangeData[exchange]) {
                this.exchangeData[exchange].set(key, priceInfo);
                exchangeDataCount[exchange]++;
            }
        }
        
        // 거래소별 테이블 업데이트
        this.updateExchangeTables();
        
        // 통계 업데이트
        const totalSymbols = Object.keys(data.data).length;
        document.getElementById('tracked-symbols').textContent = totalSymbols;
        
        console.log('📊 거래소별 데이터:', exchangeDataCount);
    }
    
    updateExchangeTables() {
        // OKX 테이블 업데이트
        this.updateExchangeTable('OKX', 'okx-table-body', 'USD');
        
        // Upbit 테이블 업데이트
        this.updateExchangeTable('Upbit', 'upbit-table-body', 'KRW');
        
        // Coinone 테이블 업데이트
        this.updateExchangeTable('Coinone', 'coinone-table-body', 'KRW');
    }
    
    updateExchangeTable(exchange, tableBodyId, currency) {
        const tableBody = document.getElementById(tableBodyId);
        const data = this.exchangeData[exchange];
        
        if (!tableBody || !data || data.size === 0) {
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            <i class="fas fa-info-circle"></i> ${exchange} 데이터 없음
                        </td>
                    </tr>
                `;
            }
            return;
        }
        
        let html = '';
        const sortedData = Array.from(data.entries()).sort((a, b) => {
            // 가격 기준 내림차순 정렬
            return b[1].price - a[1].price;
        });
        
        for (const [key, priceInfo] of sortedData) {
            const symbol = priceInfo.symbol.replace('/USDT', '').replace('/KRW', '');
            const price = this.formatPrice(priceInfo.price, currency);
            const volume = this.formatVolume(priceInfo.volume_24h || 0, currency);
            const change = priceInfo.change_24h || 0;
            const changeClass = change >= 0 ? 'change-positive' : 'change-negative';
            const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            const updateTime = new Date(priceInfo.timestamp).toLocaleTimeString();
            
            // 지지저항선 계산 (가격의 ±3~5% 범위로 단순 계산)
            const supportLevel = priceInfo.price * 0.97; // 3% 하락
            const resistanceLevel = priceInfo.price * 1.03; // 3% 상승
            const supportPrice = this.formatPrice(supportLevel, currency);
            const resistancePrice = this.formatPrice(resistanceLevel, currency);
            
            html += `
                <tr>
                    <td>
                        <strong>${symbol}</strong>
                        <span class="badge exchange-badge-${exchange.toLowerCase()} ms-1">${exchange}</span>
                    </td>
                    <td class="currency-${currency.toLowerCase()}">
                        <strong>${price}</strong>
                    </td>
                    <td>${volume}</td>
                    <td class="${changeClass}">
                        <i class="fas ${changeIcon}"></i> ${change.toFixed(2)}%
                    </td>
                    <td>
                        <small class="support-level">지지: ${supportPrice}</small><br>
                        <small class="resistance-level">저항: ${resistancePrice}</small>
                    </td>
                    <td><small class="text-muted">${updateTime}</small></td>
                </tr>
            `;
        }
        
        tableBody.innerHTML = html;
    }
    
    formatPrice(price, currency) {
        if (currency === 'KRW') {
            return '₩' + price.toLocaleString('ko-KR');
        } else {
            return '$' + price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
    }
    
    formatVolume(volume, currency) {
        if (volume === 0 || isNaN(volume)) return 'N/A';
        
        if (currency === 'KRW') {
            if (volume >= 1000000000) {
                return '₩' + (volume / 1000000000).toFixed(1) + 'B';
            } else if (volume >= 1000000) {
                return '₩' + (volume / 1000000).toFixed(1) + 'M';
            } else {
                return '₩' + volume.toLocaleString('ko-KR');
            }
        } else {
            if (volume >= 1000000) {
                return '$' + (volume / 1000000).toFixed(1) + 'M';
            } else if (volume >= 1000) {
                return '$' + (volume / 1000).toFixed(1) + 'K';
            } else {
                return '$' + volume.toLocaleString('en-US');
            }
        }
    }
    
    handleKimchiPremium(data) {
        console.log('🌶️ 김치 프리미엄 업데이트:', data.data.length, '개');
        this.kimchiData = data.data;
        this.updateKimchiPremiumDisplay();
        document.getElementById('kimchi-count').textContent = data.data.length;
    }
    
    updateKimchiPremiumDisplay() {
        const container = document.getElementById('kimchi-premium-container');
        if (!container) return;
        
        if (this.kimchiData.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center text-muted">
                    <i class="fas fa-info-circle"></i> 김치 프리미엄 데이터 없음
                </div>
            `;
            return;
        }
        
        let html = '';
        for (const premium of this.kimchiData) {
            const statusClass = premium.premium_percentage >= 0 ? 'text-success' : 'text-danger';
            const statusIcon = premium.premium_percentage >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            
            html += `
                <div class="col-md-4 mb-2">
                    <div class="card bg-dark">
                        <div class="card-body p-2">
                            <h6 class="card-title mb-1">${premium.symbol}</h6>
                            <p class="card-text ${statusClass}">
                                <i class="fas ${statusIcon}"></i> ${premium.premium_percentage.toFixed(2)}%
                            </p>
                            <small class="text-muted">
                                KR: ${this.formatPrice(premium.korean_price, 'KRW')}<br>
                                Global: ${this.formatPrice(premium.global_price, 'KRW')}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
        document.getElementById('kimchi-update-time').textContent = new Date().toLocaleTimeString();
    }
    
    handleRecommendations(data) {
        console.log('⭐ 추천 코인 업데이트:', data.data.length, '개');
        this.recommendationData = data.data;
        this.updateRecommendationsDisplay();
        document.getElementById('recommendation-count').textContent = data.data.length;
    }
    
    updateRecommendationsDisplay() {
        const container = document.getElementById('recommendations-container');
        if (!container) return;
        
        if (this.recommendationData.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-info-circle"></i> 추천 코인 데이터 없음
                </div>
            `;
            return;
        }
        
        let html = '';
        for (const rec of this.recommendationData.slice(0, 10)) { // 상위 10개만 표시
            // API 응답 구조에 맞게 필드 접근
            const symbol = rec.symbol || 'N/A';
            const price = rec.current_price || 0;
            const change = rec.price_change_24h || 0;
            const strength = rec.recommendation_strength || 'unknown';
            const volume = rec.volume_24h || 0;
            
            // 지지선/저항선 계산 (3% 범위)
            const supportLevel = price * 0.97;
            const resistanceLevel = price * 1.03;
            
            html += `
                <div class="recommendation-card p-3 mb-2 bg-dark rounded">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0">${symbol}</h6>
                        <span class="badge bg-success">${strength}</span>
                    </div>
                    <div class="row text-sm">
                        <div class="col-6">
                            <small>현재가: <strong>${this.formatPrice(price, 'USD')}</strong></small>
                        </div>
                        <div class="col-6">
                            <small>24h: <span class="${change >= 0 ? 'text-success' : 'text-danger'}">${(change * 100).toFixed(2)}%</span></small>
                        </div>
                    </div>
                    <div class="row text-sm mt-1">
                        <div class="col-6">
                            <small>지지선: <span class="support-level">${this.formatPrice(supportLevel, 'USD')}</span></small>
                        </div>
                        <div class="col-6">
                            <small>저항선: <span class="resistance-level">${this.formatPrice(resistanceLevel, 'USD')}</span></small>
                        </div>
                    </div>
                    <div class="row text-sm mt-1">
                        <div class="col-12">
                            <small>거래량: <strong>${this.formatVolume(volume)}</strong></small>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
        document.getElementById('recommendation-update-time').textContent = new Date().toLocaleTimeString();
    }
    
    setupEventListeners() {
        // 윈도우 이벤트
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
        });
    }
    
    startPeriodicUpdates() {
        // 5분마다 추천 코인 자동 로드
        setInterval(() => {
            this.loadRecommendations();
        }, 5 * 60 * 1000);
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        switch (status) {
            case 'connected':
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> 연결됨';
                statusElement.className = 'badge bg-success me-3';
                break;
            case 'connecting':
                statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 연결 중...';
                statusElement.className = 'badge bg-warning me-3';
                break;
            case 'disconnected':
                statusElement.innerHTML = '<i class="fas fa-wifi"></i> 연결 끊김';
                statusElement.className = 'badge bg-danger me-3';
                break;
            case 'error':
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 오류';
                statusElement.className = 'badge bg-danger me-3';
                break;
            case 'failed':
                statusElement.innerHTML = '<i class="fas fa-times"></i> 연결 실패';
                statusElement.className = 'badge bg-secondary me-3';
                break;
        }
    }
    
    updateLastUpdateTime() {
        const updateElement = document.getElementById('last-update');
        if (updateElement) {
            updateElement.textContent = new Date().toLocaleTimeString();
        }
    }
    
    // API 호출 메서드들
    async sendRealData() {
        try {
            console.log('📡 실제 데이터 요청 중...');
            const response = await fetch('/api/websocket/broadcast-real-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            console.log('✅ 실제 데이터 응답:', result);
            
            if (result.success) {
                alert(`실제 데이터 수집 완료!\\n데이터 포인트: ${result.data_points}개\\n김치 프리미엄: ${result.kimchi_premiums || 0}개`);
            } else {
                alert('실제 데이터 수집 실패: ' + result.message);
            }
        } catch (error) {
            console.error('❌ 실제 데이터 요청 오류:', error);
            alert('실제 데이터 요청 중 오류가 발생했습니다.');
        }
    }
    
    async startRealDataStream() {
        try {
            console.log('🚀 실시간 스트림 시작 중...');
            const response = await fetch('/api/websocket/start-real-data-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            console.log('✅ 실시간 스트림 시작 응답:', result);
            
            if (result.success) {
                alert(`실시간 스트림 시작!\\n활성 거래소: ${result.active_exchanges.join(', ')}\\n수집 주기: ${result.collection_interval}초`);
            } else {
                alert('실시간 스트림 시작 실패: ' + result.message);
            }
        } catch (error) {
            console.error('❌ 실시간 스트림 시작 오류:', error);
            alert('실시간 스트림 시작 중 오류가 발생했습니다.');
        }
    }
    
    async stopRealDataStream() {
        try {
            console.log('⏹️ 실시간 스트림 중지 중...');
            const response = await fetch('/api/websocket/stop-real-data-stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            console.log('✅ 실시간 스트림 중지 응답:', result);
            
            if (result.success) {
                alert('실시간 스트림이 중지되었습니다.');
            } else {
                alert('실시간 스트림 중지 실패: ' + result.message);
            }
        } catch (error) {
            console.error('❌ 실시간 스트림 중지 오류:', error);
            alert('실시간 스트림 중지 중 오류가 발생했습니다.');
        }
    }
    
    async loadRecommendations() {
        try {
            console.log('⭐ 추천 코인 로드 중...');
            const response = await fetch('/api/v1/recommendations?top_n=20', {
                headers: {
                    'Authorization': 'Bearer dantaro-central-2024'
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ 추천 코인 응답:', result);
                
                if (result.success && result.recommendations) {
                    this.handleRecommendations({ data: result.recommendations });
                    console.log(`✅ 추천 코인 로드 완료! ${result.recommendations.length}개 코인`);
                } else {
                    console.error('❌ 추천 코인 로드 실패:', result.error || '알 수 없는 오류');
                }
            } else {
                console.error(`❌ 추천 코인 로드 실패: HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('❌ 추천 코인 로드 오류:', error);
        }
    }
    
    async sendTestData() {
        try {
            console.log('🧪 테스트 데이터 요청 중...');
            const response = await fetch('/api/websocket/broadcast-test-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            console.log('✅ 테스트 데이터 응답:', result);
            
            if (result.success) {
                alert('테스트 데이터 브로드캐스트 완료!');
            } else {
                alert('테스트 데이터 브로드캐스트 실패: ' + result.message);
            }
        } catch (error) {
            console.error('❌ 테스트 데이터 요청 오류:', error);
            alert('테스트 데이터 요청 중 오류가 발생했습니다.');
        }
    }
}

// 전역 대시보드 인스턴스
let dashboard;

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 DOM 로드 완료 - Dashboard 초기화');
    dashboard = new DantaroDashboard();
    
    // 전역 함수로 노출 (HTML 버튼에서 사용)
    window.sendRealData = () => dashboard.sendRealData();
    window.startRealDataStream = () => dashboard.startRealDataStream();
    window.stopRealDataStream = () => dashboard.stopRealDataStream();
    window.loadRecommendations = () => dashboard.loadRecommendations();
    window.sendTestData = () => dashboard.sendTestData();
});

console.log('📝 Dashboard JavaScript 로드 완료');
