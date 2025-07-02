// Dantaro Central Dashboard JavaScript

class DantaroDashboard {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        
        // 데이터 저장소
        this.priceData = new Map();
        this.arbitrageData = [];
        this.kimchiData = [];
        this.priceHistory = new Map();
        
        // 차트 인스턴스
        this.spreadChart = null;
        this.kimchiChart = null;
        
        // 초기화
        this.init();
    }
    
    init() {
        console.log('🚀 Dantaro Dashboard 초기화 시작');
        
        // WebSocket 연결
        this.connectWebSocket();
        
        // 차트 초기화
        this.initCharts();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 주기적 업데이트
        this.startPeriodicUpdates();
        
        console.log('✅ Dashboard 초기화 완료');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
        
        console.log(`🔗 WebSocket 연결 시도: ${wsUrl}`);
        // 브라우저 콘솔에 디버그 정보 표시
        console.log('📝 디버그 정보:');
        console.log('  → 브라우저:', navigator.userAgent);
        console.log('  → 현재 URL:', window.location.href);
        console.log('  → 서버 주소:', window.location.host);
        console.log('  → 웹소켓 URL:', wsUrl);
        
        try {
            // 연결 시작 알림
            this.addLog('info', `웹소켓 연결 시도 중: ${wsUrl}`);
            this.updateConnectionStatus('connecting');
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('✅ WebSocket 연결 성공');
                this.onWebSocketOpen(event);
            };
            
            this.websocket.onmessage = (event) => {
                this.onWebSocketMessage(event);
            };
            
            this.websocket.onclose = (event) => {
                // 종료 코드 및 이유 로깅
                console.log(`❌ WebSocket 연결 종료: 코드=${event.code}, 이유=${event.reason || '알 수 없음'}`);
                this.addLog('warning', `웹소켓 연결 종료: 코드=${event.code}`);
                this.onWebSocketClose(event);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket 오류:', error);
                // 오류 추가 정보 기록
                this.addLog('error', `웹소켓 오류 발생: ${error.message || '알 수 없는 오류'}`);
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
        
        // 연결 상태 업데이트
        this.updateConnectionStatus('connected');
        
        // 초기 데이터 요청
        this.requestInitialData();
        
        // 로그 추가
        this.addLog('success', 'WebSocket 연결 성공');
    }
    
    onWebSocketMessage(event) {
        try {
            const rawData = JSON.parse(event.data);
            console.log('📥 메시지 수신:', rawData.type);
            
            // 서버 데이터 형식을 대시보드 형식으로 변환
            const data = window.DantaroAdapter.processServerMessage(rawData);
            
            switch (data.type) {
                case 'welcome':
                    console.log('🎉 환영 메시지:', data.message);
                    this.addLog('info', data.message);
                    break;
                    
                case 'price_update':
                    console.log('💰 가격 데이터 수신');
                    this.handlePriceUpdate(data.data);
                    break;
                    
                case 'arbitrage_opportunities':
                    console.log('🔄 차익거래 데이터 수신');
                    this.handleArbitrageUpdate(data.data);
                    break;
                    
                case 'kimchi_premium':
                    console.log('🇰🇷 김치 프리미엄 데이터 수신');
                    this.handleKimchiUpdate(data.data);
                    break;
                    
                case 'ping':
                    // 서버에서 핑 - 퐁으로 응답
                    this.sendPong();
                    break;
                    
                case 'pong':
                    // 서버에서 퐁 응답
                    console.log('🏓 Pong 수신');
                    break;
                    
                case 'alert':
                    // 알림 처리
                    const alertData = data.data;
                    this.addLog(alertData.level, alertData.message);
                    break;
                    
                case 'info':
                    // 정보 메시지
                    this.addLog('info', data.message);
                    break;
                    
                default:
                    console.log('📨 알 수 없는 메시지 타입:', data.type);
            }
            
        } catch (error) {
            console.error('❌ 메시지 파싱 오류:', error);
        }
    }
    
    onWebSocketClose(event) {
        this.isConnected = false;
        this.updateConnectionStatus('disconnected');
        this.addLog('warning', 'WebSocket 연결이 끊어졌습니다');
        
        // 재연결 시도
        this.scheduleReconnect();
    }
    
    onWebSocketError(error) {
        this.isConnected = false;
        this.updateConnectionStatus('error');
        this.addLog('error', `WebSocket 오류: ${error.message || '알 수 없는 오류'}`);
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} - ${this.reconnectDelay}ms 후`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
            
            // 재연결 지연 시간 증가 (지수 백오프)
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30000);
        } else {
            console.error('❌ 최대 재연결 시도 횟수 초과');
            this.addLog('error', '재연결 실패 - 새로고침이 필요합니다');
        }
    }
    
    sendPong() {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'pong',
                timestamp: new Date().toISOString()
            }));
        }
    }
    
    requestInitialData() {
        if (this.isConnected && this.websocket) {
            this.websocket.send(JSON.stringify({
                type: 'request_data',
                timestamp: new Date().toISOString()
            }));
        }
    }
    
    handlePriceUpdate(data) {
        Object.entries(data).forEach(([key, priceInfo]) => {
            const oldPrice = this.priceData.get(key)?.price || 0;
            this.priceData.set(key, priceInfo);
            
            // 가격 히스토리 저장
            const history = this.priceHistory.get(key) || [];
            history.push({
                price: priceInfo.price,
                timestamp: new Date(priceInfo.timestamp)
            });
            
            // 최근 100개만 유지
            if (history.length > 100) {
                history.splice(0, history.length - 100);
            }
            this.priceHistory.set(key, history);
            
            // 가격 변화 방향 계산
            const direction = priceInfo.price > oldPrice ? 'up' : 
                             priceInfo.price < oldPrice ? 'down' : 'neutral';
            
            priceInfo.direction = direction;
        });
        
        this.updatePriceTable();
        this.updateStats();
        this.updateLastUpdateTime('price');
    }
    
    handleArbitrageUpdate(data) {
        this.arbitrageData = data;
        this.updateArbitrageTable();
        this.updateSpreadChart();
        this.updateStats();
        this.updateLastUpdateTime('arbitrage');
        
        // 높은 스프레드 기회 알림
        const highSpreadOpportunities = data.filter(opp => opp.spread_percentage > 3);
        if (highSpreadOpportunities.length > 0) {
            this.addLog('success', `🎯 높은 차익거래 기회 발견: ${highSpreadOpportunities.length}개`);
        }
    }
    
    handleKimchiUpdate(data) {
        this.kimchiData = data;
        this.updateKimchiTable();
        this.updateKimchiChart();
        this.updateStats();
        this.updateLastUpdateTime('kimchi');
        
        // 높은 프리미엄 알림
        const highPremiumItems = data.filter(item => Math.abs(item.premium_percentage) > 5);
        if (highPremiumItems.length > 0) {
            this.addLog('info', `🍡 높은 김치 프리미엄 발견: ${highPremiumItems.length}개`);
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const statusText = {
            'connected': '연결됨',
            'disconnected': '연결 끊김',
            'error': '오류'
        };
        
        const statusClass = {
            'connected': 'bg-success',
            'disconnected': 'bg-warning',
            'error': 'bg-danger'
        };
        
        statusElement.className = `badge ${statusClass[status]} me-3 connection-status ${status}`;
        statusElement.innerHTML = `<i class="fas fa-wifi"></i> ${statusText[status]}`;
    }
    
    updateStats() {
        // 추적 심볼 수
        document.getElementById('tracked-symbols').textContent = this.priceData.size;
        
        // 차익거래 기회 수
        document.getElementById('arbitrage-count').textContent = this.arbitrageData.length;
        
        // 김치 프리미엄 수
        document.getElementById('kimchi-count').textContent = this.kimchiData.length;
    }
    
    updatePriceTable() {
        const tbody = document.getElementById('price-table-body');
        
        if (this.priceData.size === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="fas fa-spinner fa-spin"></i> 데이터 로딩 중...
                    </td>
                </tr>
            `;
            return;
        }
        
        const rows = Array.from(this.priceData.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([key, data]) => {
                const [exchange, symbol] = key.split(':');
                const price = parseFloat(data.price).toLocaleString('ko-KR', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 6
                });
                const volume = parseFloat(data.volume).toLocaleString('ko-KR', {
                    maximumFractionDigits: 2
                });
                
                const exchangeClass = `exchange-${exchange.toLowerCase()}`;
                const rowClass = data.direction ? `price-${data.direction}` : '';
                
                return `
                    <tr class="${rowClass}">
                        <td><span class="badge badge-exchange ${exchangeClass}">${exchange.toUpperCase()}</span></td>
                        <td><strong>${symbol}</strong></td>
                        <td>$${price}</td>
                        <td>${volume}</td>
                        <td>
                            ${data.direction === 'up' ? '<i class="fas fa-arrow-up text-success"></i>' : 
                              data.direction === 'down' ? '<i class="fas fa-arrow-down text-danger"></i>' :
                              '<i class="fas fa-minus text-muted"></i>'}
                        </td>
                    </tr>
                `;
            }).join('');
        
        tbody.innerHTML = rows;
    }
    
    updateArbitrageTable() {
        const tbody = document.getElementById('arbitrage-table-body');
        
        if (this.arbitrageData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">
                        <i class="fas fa-search"></i> 기회 탐색 중...
                    </td>
                </tr>
            `;
            return;
        }
        
        const rows = this.arbitrageData.map(opp => {
            const spread = parseFloat(opp.spread_percentage);
            const spreadClass = spread > 3 ? 'spread-high' : spread > 1 ? 'spread-medium' : 'spread-low';
            const confidence = Math.round(parseFloat(opp.confidence * 100));
            const rowClass = spread > 3 ? 'highlight-opportunity' : '';
            
            return `
                <tr class="${rowClass}">
                    <td><strong>${opp.symbol}</strong></td>
                    <td><span class="badge badge-exchange exchange-${opp.buy_exchange.toLowerCase()}">${opp.buy_exchange.toUpperCase()}</span></td>
                    <td><span class="badge badge-exchange exchange-${opp.sell_exchange.toLowerCase()}">${opp.sell_exchange.toUpperCase()}</span></td>
                    <td class="${spreadClass}">${spread.toFixed(2)}%</td>
                    <td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-info" style="width: ${confidence}%">${confidence}%</div>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = rows;
    }
    
    updateKimchiTable() {
        const tbody = document.getElementById('kimchi-table-body');
        
        if (this.kimchiData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="fas fa-chart-bar"></i> 프리미엄 계산 중...
                    </td>
                </tr>
            `;
            return;
        }
        
        const rows = this.kimchiData.map(item => {
            const premium = parseFloat(item.premium_percentage);
            const premiumClass = premium > 0 ? 'premium-positive' : 'premium-negative';
            const status = Math.abs(premium) > 5 ? '높음' : Math.abs(premium) > 2 ? '보통' : '낮음';
            const statusColor = Math.abs(premium) > 5 ? 'text-danger' : Math.abs(premium) > 2 ? 'text-warning' : 'text-success';
            const rowClass = Math.abs(premium) > 5 ? 'highlight-premium' : '';
            
            return `
                <tr class="${rowClass}">
                    <td><strong>${item.symbol}</strong></td>
                    <td><span class="badge badge-exchange exchange-${item.korean_exchange.toLowerCase()}">${item.korean_exchange.toUpperCase()}</span></td>
                    <td><span class="badge badge-exchange exchange-${item.global_exchange.toLowerCase()}">${item.global_exchange.toUpperCase()}</span></td>
                    <td>$${parseFloat(item.korean_price).toLocaleString('ko-KR', {maximumFractionDigits: 6})}</td>
                    <td>$${parseFloat(item.global_price).toLocaleString('ko-KR', {maximumFractionDigits: 6})}</td>
                    <td class="${premiumClass}">${premium.toFixed(2)}%</td>
                    <td><span class="${statusColor}">${status}</span></td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = rows;
    }
    
    updateLastUpdateTime(type) {
        const now = new Date().toLocaleTimeString('ko-KR');
        const elementId = `${type}-update-time`;
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = `마지막 업데이트: ${now}`;
        }
        
        // 전체 업데이트 시간
        document.getElementById('last-update').textContent = `마지막 업데이트: ${now}`;
    }
    
    initCharts() {
        // 스프레드 차트
        const spreadCtx = document.getElementById('spread-chart').getContext('2d');
        this.spreadChart = new Chart(spreadCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '최고 스프레드 (%)',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
        
        // 김치 프리미엄 차트
        const kimchiCtx = document.getElementById('kimchi-chart').getContext('2d');
        this.kimchiChart = new Chart(kimchiCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '평균 김치 프리미엄 (%)',
                    data: [],
                    borderColor: '#17a2b8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
    
    updateSpreadChart() {
        if (this.arbitrageData.length === 0) return;
        
        const now = new Date().toLocaleTimeString();
        const maxSpread = Math.max(...this.arbitrageData.map(opp => opp.spread_percentage));
        
        // 최근 20개 데이터 포인트만 유지
        if (this.spreadChart.data.labels.length >= 20) {
            this.spreadChart.data.labels.shift();
            this.spreadChart.data.datasets[0].data.shift();
        }
        
        this.spreadChart.data.labels.push(now);
        this.spreadChart.data.datasets[0].data.push(maxSpread);
        this.spreadChart.update('none');
    }
    
    updateKimchiChart() {
        if (this.kimchiData.length === 0) return;
        
        const now = new Date().toLocaleTimeString();
        const avgPremium = this.kimchiData.reduce((sum, item) => sum + Math.abs(item.premium_percentage), 0) / this.kimchiData.length;
        
        // 최근 20개 데이터 포인트만 유지
        if (this.kimchiChart.data.labels.length >= 20) {
            this.kimchiChart.data.labels.shift();
            this.kimchiChart.data.datasets[0].data.shift();
        }
        
        this.kimchiChart.data.labels.push(now);
        this.kimchiChart.data.datasets[0].data.push(avgPremium);
        this.kimchiChart.update('none');
    }
    
    addLog(type, message) {
        const container = document.getElementById('log-container');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `
            <span class="log-timestamp">${timestamp}</span>
            ${message}
        `;
        
        // 첫 번째 자식으로 추가 (최신 로그가 위에)
        if (container.firstChild) {
            container.insertBefore(logEntry, container.firstChild);
        } else {
            container.appendChild(logEntry);
        }
        
        // 최대 50개 로그만 유지
        while (container.children.length > 50) {
            container.removeChild(container.lastChild);
        }
    }
    
    setupEventListeners() {
        // 페이지 언로드 시 WebSocket 정리
        window.addEventListener('beforeunload', () => {
            if (this.websocket) {
                this.websocket.close();
            }
        });
        
        // 네트워크 상태 감지
        window.addEventListener('online', () => {
            this.addLog('info', '네트워크 연결 복구됨');
            if (!this.isConnected) {
                this.connectWebSocket();
            }
        });
        
        window.addEventListener('offline', () => {
            this.addLog('warning', '네트워크 연결이 끊어졌습니다');
        });
    }
    
    startPeriodicUpdates() {
        // 30초마다 핑 전송
        setInterval(() => {
            if (this.isConnected && this.websocket) {
                this.websocket.send(JSON.stringify({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                }));
            }
        }, 30000);
        
        // 1분마다 통계 업데이트
        setInterval(() => {
            this.updateStats();
        }, 60000);
    }
}

// 전역 함수
function clearLogs() {
    const container = document.getElementById('log-container');
    container.innerHTML = `
        <div class="text-muted text-center">
            <i class="fas fa-clock"></i> 알림 대기 중...
        </div>
    `;
}

// DOM 로드 완료 시 대시보드 시작
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOM 로드 완료 - Dashboard 시작');
    window.dashboard = new DantaroDashboard();
});
