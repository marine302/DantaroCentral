/**
 * Dantaro Dashboard 어댑터 
 * 서버 형식에 맞게 프론트엔드 데이터를 처리하는 어댑터
 */
class DantaroAdapter {
    /**
     * 서버 메시지를 대시보드에서 처리할 수 있는 형식으로 변환
     */
    static processServerMessage(data) {
        console.log('📦 어댑터 처리 시작:', data.type, data);
        const type = data.type;
        const timestamp = data.timestamp;
        
        switch (type) {
            // 서버에서 실제로 보내는 메시지 타입
            case 'price_update':
                console.log('💰 가격 업데이트 데이터 처리');
                return this.processRealtimeData(data);
                
            case 'kimchi_premium':
                console.log('🇰🇷 김치 프리미엄 데이터 처리');
                return data; // 서버 형식 유지
            
            // 이전 호환성 유지
            case 'realtime_data':
                console.log('⚠️ 레거시: 실시간 데이터 변환');
                return this.processRealtimeData(data);
            
            case 'alert':
                return this.processAlertData(data);
                
            case 'welcome':
            case 'info':
            case 'ping':
            case 'pong':
                return data;
                
            default:
                console.warn(`⚠️ 알 수 없는 메시지 타입: ${type}`);
                return data;
        }
    }
    
    /**
     * 실시간 가격 데이터 처리
     * 서버 포맷 처리:
     * - 신규: { type: "price_update", data: {"exchange:symbol": {price, volume, timestamp}} }
     * - 레거시: { type: "realtime_data", data: {"BTC": {"Upbit": price, ...}} }
     */
    static processRealtimeData(data) {
        console.log('🔄 실시간 데이터 변환 시작:', data);
        
        // price_update 타입인 경우 data가 배열 형태
        if (data.type === 'price_update') {
            // 데이터가 이미 배열인지 확인
            const dataArray = Array.isArray(data.data) ? data.data : Object.values(data.data);
            
            const processedData = {
                type: 'price_update',  // 타입을 price_update로 유지
                data: dataArray.map(item => ({
                    exchange: item.exchange,
                    symbol: item.symbol,
                    price: item.price,
                    volume: item.volume,
                    change_24h: item.change_24h,
                    timestamp: item.timestamp
                }))
            };
            console.log('✅ 변환된 실시간 데이터:', processedData);
            return processedData;
        }
        
        // 레거시 realtime_data 형식 처리
        if (data.type === 'realtime_data' && Array.isArray(data.data)) {
            console.log('⚠️ 레거시 데이터 형식 감지됨');
            return data;
        }
        
        console.warn('❌ 알 수 없는 실시간 데이터 형식:', data);
        return data;  // 알 수 없는 형식은 그대로 반환
    }
    
    /**
     * 김치 프리미엄 데이터 처리
     */
    static processKimchiData(data) {
        // 서버의 'premium' 필드를 프론트엔드에서 사용하는 'premium_percentage'로 변환
        const processedData = data.data.map(item => ({
            ...item,
            premium_percentage: item.premium
        }));
        
        return {
            type: "kimchi_premium",
            data: processedData,
            timestamp: data.timestamp
        };
    }
    
    /**
     * 알림 데이터 처리
     */
    static processAlertData(data) {
        return {
            type: "alert",
            data: data.data,
            timestamp: data.timestamp
        };
    }
}

// 전역 객체에 어댑터 노출
window.DantaroAdapter = DantaroAdapter;
