// Markets Page JavaScript - 거래소별 전체 시세 표시

class MarketsApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        
        // 데이터 저장소
        this.allMarketData = new Map();
        this.currentFilter = 'all';
        this.sortBy = 'symbol';
        this.sortOrder = 'asc';
        
        this.init();
    }
    
    init() {
        console.log('🚀 Markets App 초기화 시작');
        
        // WebSocket 연결
        this.connectWebSocket();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 초기 시장 데이터 로드
        this.loadMarketData();
        
        // 주기적 업데이트
        this.startPeriodicUpdates();
        
        console.log('✅ Markets App 초기화 완료');
        this.updateConnectionStatus('connecting');
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/realtime`;
        
        console.log(`🔗 WebSocket 연결 시도: ${wsUrl}`);
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket 연결 성공');
                this.isConnected = true;
                this.reconnectAttempts = 0;
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
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket 오류:', error);
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('❌ WebSocket 연결 실패:', error);
            this.scheduleReconnect();
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('📨 WebSocket 메시지 수신:', data.type);
        
        switch (data.type) {
            case 'market_data':
                this.handleMarketData(data);
                break;
            case 'connection_count':
                console.log(`👥 활성 연결: ${data.count}개`);
                break;
            default:
                console.log('🔍 알 수 없는 메시지 타입:', data.type);
        }
    }
    
    handleMarketData(data) {
        console.log('💰 시장 데이터 업데이트:', Object.keys(data.data).length, '개');
        console.log('📊 기존 데이터 수:', this.allMarketData.size, '개');
        
        // 데이터 저장
        for (const [key, priceInfo] of Object.entries(data.data)) {
            this.allMarketData.set(key, priceInfo);
        }
        
        console.log('📈 업데이트 후 데이터 수:', this.allMarketData.size, '개');
        
        // 테이블 업데이트
        this.updateMarketsTable();
        this.updateCounts();
        this.updateLastUpdateTime();
    }
     updateMarketsTable() {
        const tableBody = document.getElementById('markets-table-body');
        if (!tableBody) {
            console.error('❌ markets-table-body 요소를 찾을 수 없습니다!');
            return;
        }

        // 필터링된 데이터 가져오기
        const filteredData = this.getFilteredData();
        console.log('🔍 필터링된 데이터:', filteredData.length, '개');
        
        if (filteredData.length === 0) {
            console.log('⚠️ 표시할 데이터가 없습니다');
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="fas fa-info-circle"></i> 
                        ${this.currentFilter === 'all' ? '데이터 없음' : `${this.currentFilter} 거래소 데이터 없음`}
                    </td>
                </tr>
            `;
            return;
        }
        
        // 정렬
        filteredData.sort(this.getSortFunction());
        
        let html = '';
        for (const [key, priceInfo] of filteredData) {
            const symbol = priceInfo.symbol.replace('/USDT', '').replace('/KRW', '');
            const exchange = priceInfo.exchange;
            const currency = priceInfo.currency || (priceInfo.symbol.includes('KRW') ? 'KRW' : 'USD');
            
            const price = this.formatPrice(priceInfo.price, currency);
            const volume = this.formatVolume(priceInfo.volume_24h || 0, currency);
            const change = priceInfo.change_24h || 0;
            const changeClass = change >= 0 ? 'change-positive' : 'change-negative';
            const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            const updateTime = new Date(priceInfo.timestamp).toLocaleTimeString();
            
            // 지지/저항선 계산
            const supportLevel = priceInfo.price * 0.97;
            const resistanceLevel = priceInfo.price * 1.03;
            const supportPrice = this.formatPrice(supportLevel, currency);
            const resistancePrice = this.formatPrice(resistanceLevel, currency);
            
            html += `
                <tr>
                    <td class="symbol-cell">
                        <strong>${symbol}</strong>
                    </td>
                    <td>
                        <span class="badge exchange-badge-${exchange.toLowerCase()}">${exchange}</span>
                    </td>
                    <td class="price-cell text-end">
                        <strong>${price}</strong>
                    </td>
                    <td class="text-end">${volume}</td>
                    <td class="text-center ${changeClass}">
                        <i class="fas ${changeIcon}"></i> ${change.toFixed(2)}%
                    </td>
                    <td class="text-center">
                        <small class="d-block text-success">지지: ${supportPrice}</small>
                        <small class="d-block text-danger">저항: ${resistancePrice}</small>
                    </td>
                    <td class="text-center">
                        <small class="text-muted">${updateTime}</small>
                    </td>
                </tr>
            `;
        }
        
        tableBody.innerHTML = html;
    }
    
    getFilteredData() {
        if (this.currentFilter === 'all') {
            return Array.from(this.allMarketData.entries());
        } else {
            return Array.from(this.allMarketData.entries())
                .filter(([key, data]) => data.exchange === this.currentFilter);
        }
    }
    
    getSortFunction() {
        return (a, b) => {
            let aVal, bVal;
            
            switch (this.sortBy) {
                case 'symbol':
                    aVal = a[1].symbol;
                    bVal = b[1].symbol;
                    break;
                case 'price':
                    aVal = a[1].price;
                    bVal = b[1].price;
                    break;
                case 'volume':
                    aVal = a[1].volume_24h || 0;
                    bVal = b[1].volume_24h || 0;
                    break;
                case 'change':
                    aVal = a[1].change_24h || 0;
                    bVal = b[1].change_24h || 0;
                    break;
                default:
                    return 0;
            }
            
            if (this.sortBy === 'symbol') {
                return this.sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            } else {
                return this.sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
            }
        };
    }
    
    updateCounts() {
        const okxCount = Array.from(this.allMarketData.values())
            .filter(data => data.exchange === 'OKX').length;
        const upbitCount = Array.from(this.allMarketData.values())
            .filter(data => data.exchange === 'Upbit').length;
        const coinoneCount = Array.from(this.allMarketData.values())
            .filter(data => data.exchange === 'Coinone').length;
        const totalCount = this.allMarketData.size;
        
        document.getElementById('okx-count').textContent = okxCount;
        document.getElementById('upbit-count').textContent = upbitCount;
        document.getElementById('coinone-count').textContent = coinoneCount;
        document.getElementById('total-count').textContent = totalCount;
    }
    
    setupEventListeners() {
        // 거래소 필터 버튼
        document.querySelectorAll('#exchange-filter .nav-link').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                // 활성 버튼 변경
                document.querySelectorAll('#exchange-filter .nav-link').forEach(btn => 
                    btn.classList.remove('active'));
                button.classList.add('active');
                
                // 필터 적용
                this.currentFilter = button.dataset.exchange;
                this.updateMarketsTable();
            });
        });
        
        // 테이블 헤더 클릭으로 정렬
        document.addEventListener('click', (e) => {
            const th = e.target.closest('th');
            if (!th) return;
            
            const sortKey = th.dataset.sort;
            if (!sortKey) return;
            
            if (this.sortBy === sortKey) {
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortBy = sortKey;
                this.sortOrder = 'asc';
            }
            
            this.updateMarketsTable();
        });
    }
    
    startPeriodicUpdates() {
        // 30초마다 데이터 요청
        setInterval(() => {
            this.refreshData();
        }, 30000);
    }
    
    async loadMarketData() {
        try {
            console.log('� 시장 데이터 로드 중...');
            
            // 새로운 API 사용: 거래량 기준 상위 코인
            const response = await fetch('/api/v1/top-coins-by-volume?top_n=50');
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ 시장 데이터 응답:', result);
                
                if (result.success && result.data && result.data.top_coins) {
                    console.log('📊 받은 코인 수:', result.data.top_coins.length);
                    
                    // 데이터를 WebSocket 형식으로 변환
                    const marketData = {};
                    result.data.top_coins.forEach((coin, index) => {
                        console.log(`🪙 코인 ${index + 1}:`, coin.symbol, coin.exchange);
                        const key = `${coin.exchange}_${coin.full_symbol}`;
                        marketData[key] = {
                            symbol: coin.full_symbol,
                            exchange: coin.exchange,
                            price: coin.current_price,
                            volume_24h: coin.volume_24h,
                            change_24h: coin.change_24h,
                            currency: coin.currency,
                            timestamp: coin.timestamp,
                            is_recommended: coin.is_recommended,
                            recommendation_score: coin.recommendation_score,
                            support_level: coin.support_level,
                            resistance_level: coin.resistance_level
                        };
                    });
                    
                    console.log('🔄 변환된 마켓 데이터:', Object.keys(marketData).length, '개');
                    console.log('📋 변환된 데이터 샘플:', Object.values(marketData)[0]);
                    
                    // 기존 핸들러 호출
                    this.handleMarketData({ data: marketData });
                } else {
                    console.error('❌ 시장 데이터 로드 실패:', result.error || '알 수 없는 오류');
                }
            } else {
                console.error(`❌ 시장 데이터 로드 실패: HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('❌ 시장 데이터 로드 오류:', error);
        }
    }
    
    exportToCSV() {
        const filteredData = this.getFilteredData();
        if (filteredData.length === 0) {
            alert('내보낼 데이터가 없습니다.');
            return;
        }
        
        const csvHeader = 'Symbol,Exchange,Price,Volume_24h,Change_24h,Support,Resistance,Timestamp\n';
        const csvRows = filteredData.map(([key, data]) => {
            const symbol = data.symbol.replace(/[,]/g, '');
            const supportLevel = data.price * 0.97;
            const resistanceLevel = data.price * 1.03;
            
            return [
                symbol,
                data.exchange,
                data.price,
                data.volume_24h || 0,
                data.change_24h || 0,
                supportLevel.toFixed(2),
                resistanceLevel.toFixed(2),
                data.timestamp
            ].join(',');
        }).join('\n');
        
        const csvContent = csvHeader + csvRows;
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `dantaro_markets_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    // 유틸리티 함수들
    formatPrice(price, currency) {
        if (currency === 'KRW') {
            return '₩' + price.toLocaleString('ko-KR');
        } else {
            return '$' + price.toLocaleString('en-US', { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 8 
            });
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
        }
    }
    
    updateLastUpdateTime() {
        const element = document.getElementById('last-update');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts} (${this.reconnectDelay/1000}초 후)`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
            
            this.reconnectDelay *= 1.5; // 지수 백오프
        } else {
            console.error('❌ 최대 재연결 시도 횟수 초과');
            this.updateConnectionStatus('error');
        }
    }
}
