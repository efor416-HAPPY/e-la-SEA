# -*- coding: utf-8 -*-
import os
import shutil

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(WORKSPACE_DIR, 'ara-ai', 'frontend')

def sync():
    print("==================================================")
    print("      ARA Frontend Synchronization Utility")
    print("==================================================")
    
    # 1. Sync index.html and update relative paths
    src_html = os.path.join(WORKSPACE_DIR, 'index.html')
    dst_html = os.path.join(FRONTEND_DIR, 'index.html')
    
    if os.path.exists(src_html):
        print(f"Syncing index.html -> {os.path.relpath(dst_html, WORKSPACE_DIR)}")
        with open(src_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace stylesheet reference
        content = content.replace('href="style.css"', 'href="./css/style.css"')
        
        # Replace script references
        content = content.replace('src="brain.js"', 'src="./js/brain.js"')
        content = content.replace('src="app.js"', 'src="./js/app.js"')
        
        with open(dst_html, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  - index.html synced successfully.")
        
    # 2. Sync style.css
    src_css = os.path.join(WORKSPACE_DIR, 'style.css')
    dst_css = os.path.join(FRONTEND_DIR, 'css', 'style.css')
    
    if os.path.exists(src_css):
        print(f"Syncing style.css -> {os.path.relpath(dst_css, WORKSPACE_DIR)}")
        os.makedirs(os.path.dirname(dst_css), exist_ok=True)
        shutil.copy2(src_css, dst_css)
        print("  - style.css synced successfully.")
        
    # 3. Sync brain.js
    src_brain = os.path.join(WORKSPACE_DIR, 'brain.js')
    dst_brain = os.path.join(FRONTEND_DIR, 'js', 'brain.js')
    
    if os.path.exists(src_brain):
        print(f"Syncing brain.js -> {os.path.relpath(dst_brain, WORKSPACE_DIR)}")
        os.makedirs(os.path.dirname(dst_brain), exist_ok=True)
        shutil.copy2(src_brain, dst_brain)
        print("  - brain.js synced successfully.")
        
    # 4. Sync app.js
    src_app = os.path.join(WORKSPACE_DIR, 'app.js')
    dst_app = os.path.join(FRONTEND_DIR, 'js', 'app.js')
    
    if os.path.exists(src_app):
        print(f"Syncing app.js -> {os.path.relpath(dst_app, WORKSPACE_DIR)}")
        os.makedirs(os.path.dirname(dst_app), exist_ok=True)
        shutil.copy2(src_app, dst_app)
        print("  - app.js synced successfully.")
        
    print("\n[OK] All frontend files successfully synchronized!")
    print("==================================================")

if __name__ == '__main__':
    sync()
