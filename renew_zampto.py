import time
import argparse
from seleniumbase import SB

def run_zampto(username, password, proxy_url=None, proxy_user=None, proxy_pass=None):
    """
    Zampto 自动续期脚本
    
    Args:
        username: 登录账号
        password: 登录密码
        proxy_url: 代理地址，支持 socks5://host:port 或 http://host:port 格式
        proxy_user: 代理用户名（可选）
        proxy_pass: 代理密码（可选）
    """
    print(f"🔧 [Zampto-Renew] 启动浏览器 (载荷监控版)")
    
    # 配置浏览器参数
    browser_kwargs = {
        "uc": True,
        "test": True
    }
    
    # 如果提供了代理，添加到配置中
    if proxy_url:
        # 如果提供了认证信息，将其嵌入到代理URL中
        if proxy_user and proxy_pass:
            # 格式: socks5://username:password@host:port
            if "://" in proxy_url:
                protocol, address = proxy_url.split("://", 1)
                proxy_url = f"{protocol}://{proxy_user}:{proxy_pass}@{address}"
            else:
                proxy_url = f"socks5://{proxy_user}:{proxy_pass}@{proxy_url}"
            print(f"🌐 使用代理: {protocol}://{proxy_user}:***@{address}")
        else:
            print(f"🌐 使用代理: {proxy_url}")
        
        browser_kwargs["proxy"] = proxy_url
    
    with SB(**browser_kwargs) as sb:
        print("🚀 浏览器已启动")

        # 验证代理 IP
        if proxy_url:
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
        sb.type('input[name="identifier"]', username)
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
        sb.type('input[name="password"]', password)
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


def main():
    parser = argparse.ArgumentParser(
        description='Zampto 自动续期脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 使用 SOCKS5 代理（带认证）
  python zampto_renew.py -u your_username -p your_password -x socks5://127.0.0.1:1080 --proxy-user proxyuser --proxy-pass proxypass
  
  # 使用 SOCKS5 代理（不带认证）
  python zampto_renew.py -u your_username -p your_password -x socks5://127.0.0.1:1080
  
  # 使用 HTTP 代理
  python zampto_renew.py -u your_username -p your_password -x http://127.0.0.1:8080
  
  # 不使用代理
  python zampto_renew.py -u your_username -p your_password
        '''
    )
    
    parser.add_argument('-u', '--username', 
                       required=True,
                       help='Zampto 登录账号')
    
    parser.add_argument('-p', '--password',
                       required=True,
                       help='Zampto 登录密码')
    
    parser.add_argument('-x', '--proxy',
                       required=False,
                       help='代理地址，支持 socks5://host:port 或 http://host:port 格式 (可选)')
    
    parser.add_argument('--proxy-user',
                       required=False,
                       help='代理服务器用户名 (可选)')
    
    parser.add_argument('--proxy-pass',
                       required=False,
                       help='代理服务器密码 (可选)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Zampto 自动续期脚本")
    print("=" * 60)
    print(f"账号: {args.username}")
    print(f"密码: {'*' * len(args.password)}")
    if args.proxy:
        print(f"代理: {args.proxy}")
        if args.proxy_user:
            print(f"代理认证: {args.proxy_user}:{'*' * len(args.proxy_pass) if args.proxy_pass else ''}")
    else:
        print(f"代理: 未使用")
    print("=" * 60)
    print()
    
    run_zampto(args.username, args.password, args.proxy, args.proxy_user, args.proxy_pass)


if __name__ == "__main__":
    main()
