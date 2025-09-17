#!/usr/bin/env python3
"""
Simple file download server for CarFin Python files
"""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

class FileDownloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)

if __name__ == "__main__":
    port = 8080
    print(f"🚀 파일 다운로드 서버 시작: http://localhost:{port}")
    print("📁 다운로드 가능한 파일들:")
    print("   - CarFin_Python_Complete.tar.gz")
    print("   - CarFin_Python_Files/ (폴더)")
    
    with HTTPServer(("", port), FileDownloadHandler) as httpd:
        print(f"브라우저에서 http://localhost:{port} 접속하세요!")
        httpd.serve_forever()