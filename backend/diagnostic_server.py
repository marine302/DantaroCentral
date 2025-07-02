#!/usr/bin/env python3
"""
간단한 HTTP 서버로 WebSocket 진단 도구 호스팅
"""
import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

# 현재 디렉토리 확인
current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
diagnostic_file = current_dir / "websocket_diagnostics.html"

# 포트 설정
PORT = 8080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    """요청 처리 핸들러"""
    
    def do_GET(self):
        """GET 요청 처리"""
        if self.path == '/' or self.path == '/index.html':
            # 진단 도구로 리다이렉트
            self.send_response(302)
            self.send_header('Location', '/websocket_diagnostics.html')
            self.end_headers()
            return
        return super().do_GET()

if __name__ == "__main__":
    # 현재 디렉토리에서 서비스
    os.chdir(current_dir)
    
    # 서버 설정
    handler = MyHandler
    
    # 서버 시작
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"진단 서버가 포트 {PORT}에서 실행 중입니다")
        print(f"브라우저에서 http://localhost:{PORT}/ 를 열어주세요")
        
        # 브라우저 자동 열기
        webbrowser.open(f"http://localhost:{PORT}/")
        
        # 서버 실행
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버가 중지되었습니다.")
            sys.exit(0)
