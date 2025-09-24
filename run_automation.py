# File: run_automation.py (Corrected for "Element Not Interactable" Error)
import argparse
import time
import random
import string
import re
import threading
import os
import shutil
import sys

# --- DEPENDENCIES, HELPERS, and EMAIL HANDLING (Same as before) ---
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from mailtm import Email

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def generate_random_nickname():
    adjectives = ['Cool', 'Smart', 'Fast', 'Bright', 'Happy', 'Clever', 'Wise', 'Brave']
    nouns = ['User', 'Creator', 'Maker', 'Designer', 'Artist', 'Thinker', 'Dreamer', 'Builder']
    numbers = ''.join(random.choice(string.digits) for i in range(3))
    return random.choice(adjectives) + random.choice(nouns) + numbers

def click_login_button_aggressively(driver):
    aggressive_wait = WebDriverWait(driver, 15, poll_frequency=0.1)
    login_button_xpath = "/html/body/header/nav/div[2]/button[1]"
    try:
        print(f"[{time.time():.2f}] Starting aggressive search for the login button...")
        login_button = aggressive_wait.until(EC.element_to_be_clickable((By.XPATH, login_button_xpath)))
        print(f"[{time.time():.2f}] Login button found and clicked.")
        login_button.click()
        return True
    except TimeoutException:
        print(f"[{time.time():.2f}] FAILED: Login button not found after 15 seconds.")
        return False

confirmation_message = None
confirmation_code = None
def email_listener(message):
    global confirmation_message, confirmation_code
    confirmation_message = message
    print(f"\n[{time.time():.2f}] Email received: {message['subject']}")
    content = message['text'] if message['text'] else message['html']
    codes = re.findall(r'\b\d{6}\b', content)
    if codes:
        confirmation_code = codes[0]
        print(f"[{time.time():.2f}] Found verification code: {confirmation_code}")


# --- Core Automation Logic ---
def registration_process(driver):
    # This function is unchanged
    global confirmation_message, confirmation_code
    confirmation_message = None; confirmation_code = None
    wait = WebDriverWait(driver, 15)
    
    try:
        print("--- REGISTRATION PROCESS ---")
        print("[1/8] Setting up temporary email...")
        mailtm = Email()
        mailtm.register()
        temp_email = str(mailtm.address)
        print(f"Email Address: {temp_email}")
        password = generate_random_password() 
        threading.Thread(target=mailtm.start, args=(email_listener,), daemon=True).start()
        print("Email listener started.")

        print("[2/8] Opening website...")
        driver.get("https://flux-ai.io/seedream-4-0/")
        if not click_login_button_aggressively(driver): return False
        
        print("[3/8] Navigating to creation form...")
        wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div/form/div[1]/button"))).click()
            
        print("[4/8] Filling registration form...")
        wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/div/div/form/div[2]/input"))).send_keys(temp_email)
        driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/div[3]/input").send_keys(generate_random_nickname())
        driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/div[4]/input").send_keys(password)
        driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/div[5]/input").send_keys(password)
        
        print("[5/8] Submitting form, waiting for verification email...")
        driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/button[1]").click()
        
        timeout, start_time = 120, time.time()
        while not confirmation_code and (time.time() - start_time) < timeout: time.sleep(1)
        
        if confirmation_code:
            try:
                print(f"[6/8] Code {confirmation_code} received! Entering code...")
                code_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@inputmode='numeric']")))
                if len(code_inputs) >= 6:
                    print("Multiple input boxes found. Entering digits one by one.")
                    for i, digit in enumerate(confirmation_code):
                        code_inputs[i].send_keys(digit)
                elif len(code_inputs) > 0:
                    print("Single input box found. Sending full code.")
                    code_inputs[0].send_keys(confirmation_code)
                else:
                    print("ERROR: No verification code input boxes found on the page.")
                    return False
            except TimeoutException:
                print("ERROR: Timed out waiting for verification code input boxes to appear.")
                return False
            
            print("[7/8] Confirming and logging in...")
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]"))).click()
            
            wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/div/div/form/div[2]/input"))).send_keys(temp_email)
            driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/div[3]/input").send_keys(password)
            driver.find_element(By.XPATH, "/html/body/div[4]/div/div/form/button[1]").click()

            print("[8/8] Waiting for main application page to load...")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "/html/body/main/div/section[1]/div/div[2]/div[2]/form/div/div[2]/div[2]/button")))
            print("Registration and login successful!")
            return True
        else:
            print(f"FAILED: No verification code received within {timeout} seconds.")
            return False
    except Exception as e:
        import traceback
        print(f"An error occurred during registration: {e}")
        print(traceback.format_exc())
        return False

def image_generation_flow(driver, download_dir, prompt, ratio, resolution, img_format, image_path=None):
    try:
        wait = WebDriverWait(driver, 20)
        long_wait = WebDriverWait(driver, 600)
        print("--- IMAGE GENERATION PROCESS ---")
        
        # --- START OF FIX ---
        print("Checking for any post-login pop-ups or banners...")
        try:
            # Use a short wait to quickly check for a pop-up
            short_wait = WebDriverWait(driver, 5)
            # This XPath is generic and looks for common dismiss button texts
            dismiss_button_xpath = "//button[contains(text(), 'Accept') or contains(text(), 'Got it') or contains(text(), 'Continue') or contains(text(), 'Confirm') or contains(text(), 'OK')]"
            dismiss_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, dismiss_button_xpath)))
            dismiss_button.click()
            print("Dismissed a pop-up/banner.")
            time.sleep(1) # Short pause to let the overlay disappear
        except TimeoutException:
            # This is the expected outcome if there is no pop-up.
            print("No pop-ups found, proceeding normally.")
        # --- END OF FIX ---

        print(f"[1/7] Entering prompt: '{prompt[:30]}...'")
        prompt_xpath = "/html/body/main/div/section[1]/div/div[2]/div[2]/form/div/div[1]/div[3]/label/div/textarea"
        # Use a more robust wait condition: element_to_be_clickable ensures it's visible and enabled.
        prompt_textarea = wait.until(EC.element_to_be_clickable((By.XPATH, prompt_xpath)))
        prompt_textarea.send_keys(prompt)

        if image_path and os.path.exists(image_path):
            print(f"[2/7] Uploading image: {os.path.basename(image_path)}")
            driver.find_element(By.XPATH, "//input[@type='file']").send_keys(os.path.abspath(image_path))
        else:
            print("[2/7] Skipping image upload.")

        print(f"[3/7] Setting ratio to {ratio} and resolution to {resolution}.")
        Select(wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/main/div/section[1]/div/div[2]/div[2]/form/div/div[1]/div[7]/select")))).select_by_visible_text(ratio)
        Select(wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/main/div/section[1]/div/div[2]/div[2]/form/div/div[1]/div[9]/select")))).select_by_visible_text(resolution)

        print("[4/7] Starting generation... this may take several minutes.")
        wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/section[1]/div/div[2]/div[2]/form/div/div[2]/div[2]/button"))).click()
        
        download_icon_xpath = "/html/body/main/div/section[1]/div/div[2]/div[3]/div[2]/div[3]/button[2]"
        print("[5/7] Waiting for generation to complete...")
        long_wait.until(EC.element_to_be_clickable((By.XPATH, download_icon_xpath)))
        print("Generation complete!")

        print(f"[6/7] Setting format to {img_format} and downloading...")
        format_span = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/main/div/section[1]/div/div[2]/div[3]/div[2]/div[3]/button[1]/span")))
        driver.execute_script(f"arguments[0].innerText = '{img_format}';", format_span)
        driver.find_element(By.XPATH, download_icon_xpath).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div/div[4]/button"))).click()

        print("[7/7] Verifying download and saving file...")
        time.sleep(5) 
        seconds_waited = 0
        while any(fname.endswith(('.crdownload', '.tmp')) for fname in os.listdir(download_dir)):
            time.sleep(1)
            seconds_waited += 1
            if seconds_waited > 300:
                print("Download is taking too long. Aborting wait.")
                break
        
        list_of_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir)]
        if not list_of_files:
            print("ERROR: No file was downloaded.")
            return False
        latest_file = max(list_of_files, key=os.path.getctime)
        
        sanitized_prompt = re.sub(r'[\\/*?:"<>|]', "", "_".join(prompt.split()[:4]))
        final_folder_name = f"{sanitized_prompt}_{int(time.time())}"
        
        final_output_dir = os.path.join(os.getcwd(), "output", final_folder_name)
        os.makedirs(final_output_dir, exist_ok=True)
        
        final_file_path = os.path.join(final_output_dir, os.path.basename(latest_file))
        shutil.move(latest_file, final_file_path)
        
        print(f"Success! Image saved.")
        print(f"FINAL_PATH:{final_file_path}")
        return True
    except Exception as e:
        import traceback
        print(f"An error occurred during image generation: {e}")
        print(traceback.format_exc())
        return False

# (The __main__ block is unchanged)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Automation Script for Flux AI.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser_register = subparsers.add_parser("register", help="Run the automated registration process ONLY.")
    parser_generate = subparsers.add_parser("generate", help="Run the image generation process ONLY.")
    parser_generate.add_argument("--prompt", required=True)
    parser_generate.add_argument("--ratio", default="16:9")
    parser_generate.add_argument("--resolution", default="1k")
    parser_generate.add_argument("--format", default="jpg")
    parser_generate.add_argument("--image-path")
    parser_combined = subparsers.add_parser("register-and-generate", help="Run registration AND generation in one session.")
    parser_combined.add_argument("--prompt", required=True)
    parser_combined.add_argument("--ratio", default="16:9")
    parser_combined.add_argument("--resolution", default="1k")
    parser_combined.add_argument("--format", default="jpg")
    parser_combined.add_argument("--image-path")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, "temp_downloads")
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(os.path.join(script_dir, "output"), exist_ok=True)

    options = webdriver.EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    prefs = {"download.default_directory": str(download_dir)}
    options.add_experimental_option("prefs", prefs)
    
    driver = None
    try:
        print("Setting up Microsoft Edge Driver from local file...")
        driver_path = os.path.join(script_dir, "msedgedriver.exe")
        if not os.path.exists(driver_path):
             print(f"FATAL ERROR: msedgedriver.exe not found in script directory: {script_dir}")
             sys.exit(1)

        service = Service(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=options)
        print("Driver setup complete.")

        if args.command == "register-and-generate":
            reg_success = registration_process(driver)
            if reg_success:
                print("\n\n--- Registration successful, proceeding to generation. ---")
                image_generation_flow(driver, download_dir, args.prompt, args.ratio, args.resolution, args.format, args.image_path)
            else:
                print("\n\n--- Registration failed. Cannot proceed to image generation. ---")

        elif args.command == "register":
            registration_process(driver)
        elif args.command == "generate":
            driver.get("https://flux-ai.io/seedream-4-0/")
            image_generation_flow(driver, download_dir, args.prompt, args.ratio, args.resolution, args.format, args.image_path)
    
    except Exception as e:
        import traceback
        print(f"A critical error occurred: {e}")
        print(traceback.format_exc())
    finally:
        print("\nScript finished.")
        if driver:
            driver.quit()
        if os.path.exists(download_dir):
            try:
                shutil.rmtree(download_dir)
                print(f"Cleaned up temporary download folder.")
            except OSError as e:
                print(f"Error removing temp folder {download_dir}: {e.strerror}")