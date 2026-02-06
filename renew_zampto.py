import time
from seleniumbase import SB

USERNAME = "alice@o2skygg.com"
PASSWORD = "Scsi520530"
LOCAL_PROXY = "socks5://ac27dfbb:d74d20d73082@162.43.35.176:25575"

def run_zampto():
    print(f"🔧 [Zampto-Renew] 启动浏览器 (载荷监控版)")
    
    with SB(uc=True, test=True, proxy=LOCAL_PROXY) as sb:
        print("🚀 浏览器已启动")

        print("[-] 正在验证代理 IP...")
        try:
            sb.open("https://api.ipify.org/?format=json")
            current_ip = sb.get_text("body")
            print(f"✅ 当前出口 IP: {current_ip}")
        except:
            print("⚠️ IP 验证超时，跳过")

        login_url = "https://auth.zampto.net/sign-in?app_id=bmhk6c8qdqxphlyscztgl"
        print(f"[-] 访问登录页: {login_url}")
        sb.uc_open_with_reconnect(login_url, 20)
        
        if sb.is_element_visible('iframe[src*="cloudflare"]'):
            sb.uc_gui_click_captcha()

        print("[-] 输入账号...")
        sb.type('input[name="identifier"]', USERNAME)
        sb.click('button[type="submit"]')

        print("[-] 等待跳转到密码页...")
        try:
            sb.wait_for_element_visible('input[name="password"]', timeout=15)
            print("✅ 已跳转到密码页")
        except:
            print("❌ 未跳转到密码页")
            sb.save_screenshot("step3_fail.png")
            return

        print("[-] 输入密码...")
        sb.type('input[name="password"]', PASSWORD)
        sb.click('button[name="submit"]')
        
        time.sleep(2)
        if sb.is_element_visible('iframe[src*="cloudflare"]'):
            sb.uc_gui_click_captcha()

        print("[-] 等待跳转 Homepage...")
        is_logged_in = False
        for i in range(60):
            try:
                if "/homepage" in sb.get_current_url():
                    print(f"✅ 登录成功！")
                    is_logged_in = True
                    break
            except:
                pass
            time.sleep(0.5)
        
        if not is_logged_in:
            print("❌ 登录失败，未跳转 homepage")
            sb.save_screenshot("step5_fail.png")
            return

        print("[-] 寻找服务器按钮 (id=2711)...")
        target_server_selector = 'a.server-btn[href*="id=2711"]'
        
        try:
            sb.wait_for_element_visible(target_server_selector, timeout=15)
            sb.click(target_server_selector)
            print("✅ 点击了 View Server")
        except:
            print(f"❌ 未找到服务器按钮")
            sb.save_screenshot("step6_fail.png")
            return

        print("[-] 等待跳转服务器详情页...")
        server_page_loaded = False
        for i in range(40):
            try:
                if "id=2711" in sb.get_current_url():
                    print("✅ 已进入服务器详情页")
                    server_page_loaded = True
                    break
            except:
                pass
            time.sleep(0.5)

        if not server_page_loaded:
            print("⚠️ 页面跳转超时")
            sb.save_screenshot("step7_timeout.png")

        print("[-] 寻找 Renew 按钮...")
        renew_xpath = "//span[contains(., 'Renew Server')]"
        
        try:
            sb.wait_for_element_visible(renew_xpath, timeout=10)
            sb.click(renew_xpath)
            print("✅ 已点击 Renew Server，等待弹窗...")
            time.sleep(2) 
        except:
            print("❌ 超时未找到 Renew Server 按钮")
            sb.save_screenshot("step8_fail.png")
            return

        print("[-] 开始监控 Cloudflare Token 载荷...")
        
        sb.uc_gui_click_captcha()
        
        try:
            if sb.is_element_visible('iframe[src*="cloudflare"]', timeout=2):
                sb.uc_click('iframe[src*="cloudflare"]')
        except:
            pass

        try:
            if sb.is_element_visible('iframe[src*="turnstile"]', timeout=2):
                sb.uc_click('iframe[src*="turnstile"]')
        except:
            pass
        
        time.sleep(1)
        
        token_acquired = False
        token_value = ""
        
        for i in range(30):
            try:
                token_value = sb.get_attribute('[name="cf-turnstile-response"]', "value")
                if token_value and len(token_value) > 20:
                    print(f"✅ Token 已获取 (获取到 Token: {token_value[:20]}...)")
                    token_acquired = True
                    break
            except:
                pass
            
            if i < 3:
                print(f"    ...检查中 ({i+1})...")
            
            if i > 0 and i % 6 == 0:
                sb.uc_gui_click_captcha()
            
            time.sleep(0.5)
        
        if not token_acquired:
            print("❌ 超时：验证码始终未通过 (Token为空)")
            sb.save_screenshot("token_fail.png")
            return

        print("🎯 等待提交...")
        time.sleep(3)

        print("[-] 刷新页面获取最新时间...")
        sb.refresh()
        
        print("[-] 等待时间元素...")
        try:
            sb.wait_for_element_visible("#nextRenewalTime", timeout=10)
            
            time_text = ""
            for i in range(20):
                time_text = sb.get_text("#nextRenewalTime").strip()
                if time_text:
                    break
                if i < 3:
                    print(f"  ⏳ 等待内容加载...")
                time.sleep(0.5)
            
            if time_text:
                print(f"⏱️ 剩余时间: {time_text}")
                
                if "1 day" in time_text or "2 day" in time_text:
                    print("🎉🎉🎉 续期成功！")
                    sb.save_screenshot("zampto_success.png")
                elif "0h" in time_text or "0 day" in time_text:
                    print("⚠️ 时间未增加，续期可能失败")
                    sb.save_screenshot("zampto_fail.png")
                else:
                    print(f"ℹ️ 时间显示异常: {time_text}")
                    sb.save_screenshot("zampto_unknown.png")
            else:
                print("❌ 等了10秒，元素还是空的！")
                sb.save_screenshot("zampto_empty.png")
                
        except Exception as e:
            print(f"❌ 读取时间失败: {e}")
            sb.save_screenshot("zampto_verify_error.png")

if __name__ == "__main__":
    run_zampto()
