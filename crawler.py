from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import sys

def crawl():
    url = "https://www.kms.or.kr/mathdict/list.html"
    terms = []

    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    total_pages = 339
    
    for i in range(total_pages):
        try:
            start = i * 20
            driver.get(f"{url}?start={start}&sort=ename&key=&keyword=&alpa=")
            print(f"📖 {i + 1} 페이지 크롤링 중...")

            time.sleep(1.5)

            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            soup = BeautifulSoup(driver.page_source, "html.parser")
            rows = soup.select("table.cst-table>tbody tr")

            for row in rows:
                cols = [col.text.strip() for col in row.find_all("td")]
                if len(cols) >= 2:
                    terms.append(cols[1])

            time.sleep(1)

        except Exception as e:
            print(f"⚠️ 페이지 {i + 1}에서 오류 발생: {e}")
            driver.quit()
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            continue

    with open("math_terms.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(terms))

    driver.quit()
    print(f"✅ 총 {len(terms)} 개 용어 저장 완료!")

if __name__ == "__main__":
    crawl()
