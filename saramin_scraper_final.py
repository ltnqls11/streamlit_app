import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager



def scrape_saramin_jobs(url):
    """
    사람인 채용 페이지에서 채용 정보를 크롤링하는 함수
    """
    # Chrome 옵션 설정
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # 디버깅을을 띄우지 않음
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        # 웹드라이버 초기화
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        jobs = []
        
        # 채용 공고 리스트 찾기
        job_selectors = [
            '.item_recruit',
            '.list_item',
            '[class*="recruit"]',
            '[class*="item"]'
        ]
        
        job_elements = []
        for selector in job_selectors:
            try:
                job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if job_elements:
                    print(f"채용공고 {len(job_elements)}개 발견 (셀렉터: {selector})")
                    break
            except:
                continue
        
        if not job_elements:
            # BeautifulSoup으로 페이지 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 사람인 특정 구조 찾기
            containers = soup.find_all(['div'], class_=lambda x: x and any(
                keyword in x.lower() for keyword in ['item', 'recruit', 'job', 'list']
            ))
            
            print(f"BeautifulSoup으로 {len(containers)}개 컨테이너 발견")
            
            for container in containers:  # 모든 컨테이너 처리
                try:
                    job_info = extract_job_info_from_soup(container)
                    if job_info['title'] and len(jobs) < 20:  # 제목이 있고 20개 미만인 경우만 추가
                        jobs.append(job_info)
                except Exception as e:
                    continue
        
        else:
            # Selenium으로 채용 정보 추출
            for element in job_elements:  # 모든 요소 처리
                try:
                    job_info = extract_job_info_from_selenium(element)
                    if job_info['title'] and len(jobs) < 20:  # 제목이 있고 20개 미만인 경우만 추가
                        jobs.append(job_info)
                except Exception as e:
                    continue
        
        driver.quit()
        return jobs
        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def extract_job_info_from_selenium(element):
    """Selenium 요소에서 채용 정보 추출"""
    job_info = {
        'title': '',
        'company': '',
        'location': '',
        'experience': '',
        'education': '',
        'employment_type': '',
        'salary': '',
        'deadline': '',
        'link': ''
    }
    
    try:
        # 채용 제목 추출
        title_selectors = ['.job_tit a', '.recruit_tit', 'h2 a', '.tit a', 'a[title]']
        for selector in title_selectors:
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, selector)
                if title_elem.text.strip():
                    job_info['title'] = title_elem.text.strip()
                    # 링크도 함께 추출
                    job_info['link'] = title_elem.get_attribute('href') or ''
                    break
            except:
                continue
        
        # 회사명 추출
        company_selectors = ['.corp_name a', '.company', '.corp', '[class*="company"]']
        for selector in company_selectors:
            try:
                company_elem = element.find_element(By.CSS_SELECTOR, selector)
                if company_elem.text.strip():
                    job_info['company'] = company_elem.text.strip()
                    break
            except:
                continue
        
        # 지역 추출
        location_selectors = ['.job_condition .condition', '.location', '[class*="location"]', '[class*="area"]']
        for selector in location_selectors:
            try:
                location_elem = element.find_element(By.CSS_SELECTOR, selector)
                text = location_elem.text.strip()
                if text and ('서울' in text or '경기' in text or '부산' in text or '지역' in text or '구' in text):
                    job_info['location'] = text
                    break
            except:
                continue
        
        # 경력 추출
        exp_selectors = ['.job_condition', '.condition', '[class*="career"]', '[class*="experience"]']
        for selector in exp_selectors:
            try:
                exp_elem = element.find_element(By.CSS_SELECTOR, selector)
                text = exp_elem.text.strip()
                if text and ('경력' in text or '신입' in text or '년' in text):
                    job_info['experience'] = text
                    break
            except:
                continue
        
        # 학력 추출
        edu_selectors = ['.job_condition', '.condition', '[class*="education"]']
        for selector in edu_selectors:
            try:
                edu_elem = element.find_element(By.CSS_SELECTOR, selector)
                text = edu_elem.text.strip()
                if text and ('학력' in text or '대졸' in text or '고졸' in text or '무관' in text):
                    job_info['education'] = text
                    break
            except:
                continue
        
        # 고용형태 추출
        type_selectors = ['.job_condition', '.condition', '[class*="employment"]']
        for selector in type_selectors:
            try:
                type_elem = element.find_element(By.CSS_SELECTOR, selector)
                text = type_elem.text.strip()
                if text and ('정규직' in text or '계약직' in text or '파트' in text or '인턴' in text):
                    job_info['employment_type'] = text
                    break
            except:
                continue
        

        
        # 마감일 추출
        deadline_selectors = ['.job_date', '.date', '[class*="deadline"]', '[class*="dday"]']
        for selector in deadline_selectors:
            try:
                deadline_elem = element.find_element(By.CSS_SELECTOR, selector)
                text = deadline_elem.text.strip()
                if text and ('~' in text or '마감' in text or 'D-' in text or '/' in text or '상시' in text or '채용시' in text):
                    job_info['deadline'] = text
                    break
            except:
                continue
                
    except Exception as e:
        pass
    
    return job_info

def extract_job_info_from_soup(container):
    """BeautifulSoup 요소에서 채용 정보 추출"""
    job_info = {
        'title': '',
        'company': '',
        'location': '',
        'experience': '',
        'education': '',
        'employment_type': '',
        'salary': '',
        'deadline': '',
        'link': ''
    }
    
    try:
        # 채용 제목 추출
        title_selectors = ['a[title]', 'h2 a', 'h3 a', '.tit a', '.job_tit a']
        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                job_info['title'] = title_elem.get_text(strip=True)
                job_info['link'] = title_elem.get('href', '')
                if job_info['link'] and not job_info['link'].startswith('http'):
                    job_info['link'] = 'https://www.saramin.co.kr' + job_info['link']
                break
        
        # 회사명 추출
        company_selectors = ['.corp_name a', '.company', '.corp']
        for selector in company_selectors:
            company_elem = container.select_one(selector)
            if company_elem and company_elem.get_text(strip=True):
                job_info['company'] = company_elem.get_text(strip=True)
                break
        
        # 조건 정보들을 한 번에 가져와서 분리 처리
        condition_text = ''
        condition_elements = container.select('.job_condition, .condition, .job_meta, .recruit_condition, .area_job')
        
        for elem in condition_elements:
            condition_text += elem.get_text(strip=True) + '\n'
        
        # 추가로 전체 컨테이너에서 급여 관련 정보 찾기
        all_text = container.get_text()
        condition_text += all_text
        
        # 줄바꿈으로 분리하여 각 조건별로 처리
        lines = [line.strip() for line in condition_text.split('\n') if line.strip()]
        
        for line in lines:
            # 지역 정보 (시/구 포함)
            if not job_info['location'] and any(keyword in line for keyword in ['서울', '경기', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']):
                job_info['location'] = line
            
            # 경력 정보 (년수 관련)
            elif not job_info['experience'] and ('경력' in line or '신입' in line or ('년' in line and ('이상' in line or '~' in line))):
                job_info['experience'] = line
            
            # 학력 정보
            elif not job_info['education'] and ('학력' in line or '대졸' in line or '고졸' in line or '무관' in line or '초대졸' in line):
                job_info['education'] = line
            
            # 고용형태
            elif not job_info['employment_type'] and ('정규직' in line or '계약직' in line or '파트' in line or '인턴' in line or '기간제' in line):
                job_info['employment_type'] = line
            

        
        # 마감일 추출
        deadline_selectors = ['.job_date', '.date', '.dday']
        for selector in deadline_selectors:
            deadline_elem = container.select_one(selector)
            if deadline_elem and deadline_elem.get_text(strip=True):
                text = deadline_elem.get_text(strip=True)
                if '~' in text or '마감' in text or 'D-' in text or '/' in text or '상시' in text or '채용시' in text:
                    job_info['deadline'] = text
                    break
                    
    except Exception as e:
        pass
    
    return job_info

def format_deadline(deadline_text):
    """마감일을 m/d 형식으로 변환"""
    if not deadline_text or deadline_text.strip() == '':
        return ''
    
    # 공백, ~, 입사지원, 홈페이지 지원 등 불필요한 문자 제거
    cleaned_text = deadline_text.replace('~', '').replace('입사지원', '').replace('홈페이지 지원', '').strip()
    
    # 날짜 패턴 찾기 (mm/dd 형식)
    date_pattern = r'(\d{1,2})/(\d{1,2})'
    match = re.search(date_pattern, cleaned_text)
    
    if match:
        month = match.group(1)
        day = match.group(2)
        return f"{month}/{day}"
    
    # 특별한 경우 처리
    if '오늘마감' in cleaned_text:
        today = datetime.now()
        return f"{today.month}/{today.day}"
    elif '내일마감' in cleaned_text:
        tomorrow = datetime.now() + timedelta(days=1)
        return f"{tomorrow.month}/{tomorrow.day}"
    elif '상시채용' in cleaned_text:
        return '상시채용'
    elif '채용시' in cleaned_text:
        return '채용시'
    
    return ''

def format_location(location_text):
    """지역 정보를 (시/구) 형태로 변환"""
    if not location_text or location_text.strip() == '':
        return ''
    
    # 줄바꿈과 불필요한 공백 제거
    cleaned_text = location_text.replace('\n', ' ').strip()
    
    # 시/구 패턴 찾기
    # 예: "서울 종로구", "경기 성남시 수정구", "부산 해운대구" 등
    city_pattern = r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*([가-힣]+시|[가-힣]+구|[가-힣]+군)'
    match = re.search(city_pattern, cleaned_text)
    
    if match:
        province = match.group(1)
        city_or_district = match.group(2)
        
        # 특별시/광역시의 경우 구만 표시
        if province in ['서울', '부산', '대구', '인천', '광주', '대전', '울산']:
            if '구' in city_or_district:
                return city_or_district
            else:
                return f"{province} {city_or_district}"
        # 도의 경우 시/구 표시
        else:
            return f"{city_or_district}"
    
    # 패턴이 매치되지 않으면 첫 번째 단어만 반환
    first_word = cleaned_text.split()[0] if cleaned_text.split() else ''
    return first_word

def extract_location_from_experience(experience_text):
    """experience 컬럼에서 지역 정보를 추출"""
    if not experience_text or experience_text.strip() == '':
        return '', experience_text
    
    # 시/구 패턴 찾기
    city_pattern = r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*([가-힣]+시|[가-힣]+구|[가-힣]+군)'
    match = re.search(city_pattern, experience_text)
    
    if match:
        province = match.group(1)
        city_or_district = match.group(2)
        
        # 지역 정보 추출
        if province in ['서울', '부산', '대구', '인천', '광주', '대전', '울산']:
            if '구' in city_or_district:
                location = city_or_district
            else:
                location = f"{province} {city_or_district}"
        else:
            location = f"{city_or_district}"
        
        # experience에서 지역 정보 제거
        cleaned_experience = re.sub(city_pattern, '', experience_text).strip()
        # 연속된 공백이나 줄바꿈 정리
        cleaned_experience = re.sub(r'\s+', ' ', cleaned_experience).strip()
        
        return location, cleaned_experience
    
    return '', experience_text

def clean_experience_data(text):
    """경력 데이터만 추출 (경력 *년 or 경력 무관)"""
    if not text or text.strip() == '':
        return ''
    
    # 경력 관련 패턴 찾기
    experience_patterns = [
        r'경력\s*\d+~?\d*\s*년',  # 경력 1~5년, 경력 3년 등
        r'경력\s*무관',           # 경력 무관
        r'신입',                 # 신입
        r'\d+년\s*이상',         # 3년 이상
        r'\d+~\d+년',           # 1~5년
    ]
    
    for pattern in experience_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ''

def clean_education_data(text):
    """학력 데이터만 추출 (*졸 or 학력 무관)"""
    if not text or text.strip() == '':
        return ''
    
    # 학력 관련 패턴 찾기
    education_patterns = [
        r'[가-힣]*졸',           # 대졸, 고졸, 초대졸 등
        r'학력\s*무관',          # 학력 무관
        r'대학교\s*졸업',        # 대학교 졸업
        r'전문대\s*졸업',        # 전문대 졸업
    ]
    
    for pattern in education_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ''

def clean_employment_type_data(text):
    """고용형태 데이터만 추출 (정규직 or 계약직)"""
    if not text or text.strip() == '':
        return ''
    
    # 고용형태 관련 패턴 찾기
    employment_patterns = [
        r'정규직',
        r'계약직',
        r'파트타임',
        r'인턴',
        r'기간제',
        r'프리랜서',
    ]
    
    for pattern in employment_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ''

def clean_salary_data(text):
    """급여 데이터만 추출 (*만원 or *원)"""
    if not text or text.strip() == '':
        return ''
    
    # 급여 관련 패턴 찾기 (더 포괄적으로)
    salary_patterns = [
        r'\d+,?\d*만원',                    # 3000만원, 2,500만원 등
        r'\d+,?\d*원',                      # 300000원, 2,500,000원 등
        r'연봉\s*\d+,?\d*만원',             # 연봉 3000만원
        r'월급\s*\d+,?\d*만원',             # 월급 300만원
        r'시급\s*\d+,?\d*원',               # 시급 15000원
        r'\d+~\d+만원',                    # 2500~3000만원
        r'\d+~\d+원',                      # 250000~300000원
        r'면접후\s*결정',                   # 면접후 결정
        r'협의',                           # 협의
        r'회사내규',                       # 회사내규
        r'급여협의',                       # 급여협의
        r'면접시\s*협의',                  # 면접시 협의
        r'경력에\s*따라\s*협의',           # 경력에 따라 협의
        r'능력에\s*따라',                  # 능력에 따라
        r'상담후\s*결정',                  # 상담후 결정
        r'별도협의',                       # 별도협의
        r'추후협의',                       # 추후협의
    ]
    
    for pattern in salary_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    # 패턴이 매치되지 않으면 '만원' 또는 '원'이 포함된 텍스트 찾기
    if '만원' in text or '원' in text:
        # 숫자와 함께 있는 경우 추출
        number_with_won = re.search(r'\d+[,\d]*\s*[만]?원', text)
        if number_with_won:
            return number_with_won.group(0)
    
    # 급여 관련 키워드가 있는 경우
    salary_keywords = ['급여', '연봉', '월급', '시급', '임금', '보수']
    for keyword in salary_keywords:
        if keyword in text:
            return text.strip()
    
    return ''

def save_to_csv(jobs, filename='saramin_jobs.csv'):
    """채용 정보를 CSV 파일로 저장"""
    if jobs:
        df = pd.DataFrame(jobs)
        
        # 각 컬럼별로 데이터 정리
        for idx, row in df.iterrows():
            # 지역 정보 추출 및 이동
            extracted_location, cleaned_text = extract_location_from_experience(row['experience'])
            
            if not row['location'] and extracted_location:
                df.at[idx, 'location'] = extracted_location
            elif extracted_location and extracted_location not in str(row['location']):
                df.at[idx, 'location'] = extracted_location
            
            # experience 컬럼 정리 - 경력 정보만 추출
            experience_clean = clean_experience_data(row['experience'])
            df.at[idx, 'experience'] = experience_clean
            
            # education 컬럼 정리 - 학력 정보만 추출
            education_clean = clean_education_data(row['education'])
            df.at[idx, 'education'] = education_clean
            
            # employment_type 컬럼 정리 - 고용형태 정보만 추출
            employment_clean = clean_employment_type_data(row['employment_type'])
            df.at[idx, 'employment_type'] = employment_clean
            

        
        # deadline 컬럼 형식 변환 (문자열로 변환)
        df['deadline'] = df['deadline'].apply(lambda x: str(format_deadline(x)) if format_deadline(x) else '')
        # location 컬럼 형식 변환
        df['location'] = df['location'].apply(format_location)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"데이터가 {filename}에 저장되었습니다.")
        return df
    else:
        print("저장할 데이터가 없습니다.")
        return None

def main():
    # 사람인 업무자동화 검색 URL
    url = "https://www.saramin.co.kr/zf_user/search?search_area=main&search_done=y&search_optional_item=n&searchType=search&searchword=%rpa"
    
    print("사람인 채용 정보 크롤링을 시작합니다...")
    jobs = scrape_saramin_jobs(url)
    
    if jobs:
        print(f"\n총 {len(jobs)}개의 채용 정보를 수집했습니다.")
        
        # 결과 출력
        for i, job in enumerate(jobs, 1):
            print(f"\n--- 채용공고 {i} ---")
            print(f"제목: {job['title']}")
            print(f"회사: {job['company']}")
            print(f"지역: {job['location']}")
            print(f"경력: {job['experience']}")
            print(f"학력: {job['education']}")
            print(f"고용형태: {job['employment_type']}")
            print(f"급여: {job['salary']}")
            print(f"마감일: {job['deadline']}")
            print(f"링크: {job['link']}")
        
        # CSV 파일로 저장
        df = save_to_csv(jobs, 'saramin_automation_jobs.csv')
        
        if df is not None:
            print(f"\n데이터프레임 정보:")
            print(df.info())
            print(f"\n처음 5개 행:")
            print(df.head())
    
    else:
        print("채용 정보를 수집하지 못했습니다.")

if __name__ == "__main__":
    main()