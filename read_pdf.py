#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFファイルから建築限界の計算式を抽出するスクリプト
"""

import PyPDF2
import pdfplumber

def extract_pdf_page_133():
    """PDFファイルの133ページを抽出"""
    pdf_file = "01_第１章_総則（24電SI信管第67号）.pdf"
    
    try:
        # pdfplumberを使用してテキストを抽出
        print("=== PDFファイル 133ページの内容 ===")
        
        with pdfplumber.open(pdf_file) as pdf:
            print(f"総ページ数: {len(pdf.pages)}")
            
            # 133ページ周辺を確認
            target_pages = [132, 133, 134]  # 0から始まるので132, 133, 134
            
            for page_num in target_pages:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    print(f"\n=== {page_num + 1}ページ ===")
                    
                    text = page.extract_text()
                    if text:
                        print(text)
                    else:
                        print("テキストが抽出できませんでした")
                    
                    # 表があれば抽出
                    tables = page.extract_tables()
                    if tables:
                        print(f"\n表の数: {len(tables)}")
                        for i, table in enumerate(tables):
                            print(f"表{i+1}:")
                            for row in table:
                                if row:
                                    print("  ", " | ".join([str(cell) if cell else "" for cell in row]))
                else:
                    print(f"ページ {page_num + 1} は存在しません")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_pdf_page_133()