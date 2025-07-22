import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# 페이지 설정
st.set_page_config(
    page_title="채용 정보 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("📊 업무자동화 채용 정보 대시보드")
st.markdown("---")

@st.cache_data
def load_data():
    """데이터 로드 및 전처리"""
    try:
        df = pd.read_csv('08-streamlit/saramin_automation_jobs.csv')
        
        # 데이터 전처리
        df = df.dropna(subset=['title'])  # 제목이 없는 행 제거
        
        # 지역 정보 추출 및 정리
        df['clean_location'] = df['location'].apply(extract_location)
        
        # 경력 정보 추출
        df['clean_experience'] = df['experience'].apply(extract_experience)
        
        # 고용형태 추출
        df['clean_employment'] = df['employment_type'].apply(extract_employment_type)
        
        # 급여 정보 추출
        df['clean_salary'] = df['salary'].apply(extract_salary)
        
        return df
    except FileNotFoundError:
        st.error("데이터 파일을 찾을 수 없습니다. 먼저 크롤링을 실행해주세요.")
        return None

def extract_location(location_str):
    """지역 정보 추출"""
    if pd.isna(location_str):
        return "정보없음"
    
    location_str = str(location_str).strip()
    
    # 서울 구별 매핑
    seoul_districts = ['강남구', '서초구', '종로구', '중구', '용산구', '성동구', '광진구', 
                      '동대문구', '중랑구', '성북구', '강북구', '도봉구', '노원구', 
                      '은평구', '서대문구', '마포구', '양천구', '강서구', '구로구', 
                      '금천구', '영등포구', '동작구', '관악구', '송파구', '강동구']
    
    # 서울 구 확인
    for district in seoul_districts:
        if district == location_str:
            return "서울"
    
    # 대전 구 확인
    if location_str in ['유성구', '서구', '중구', '동구', '대덕구']:
        return "대전"
    
    # 부산 구 확인  
    if location_str in ['해운대구', '부산진구', '동래구', '남구', '북구', '사상구', '사하구', '서구', '영도구', '중구', '연제구', '수영구', '금정구', '강서구', '기장군']:
        return "부산"
    
    # 기타 광역시 구 확인
    if '구' in location_str:
        return "기타 광역시"
    
    # 주요 지역 키워드 추출
    regions = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종', 
               '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    
    for region in regions:
        if region in location_str:
            return region
    
    return location_str if location_str else "정보없음"

def extract_experience(exp_str):
    """경력 정보 추출"""
    if pd.isna(exp_str):
        return "정보없음"
    
    exp_str = str(exp_str)
    
    if '신입' in exp_str:
        return "신입"
    elif '경력무관' in exp_str:
        return "경력무관"
    elif '경력' in exp_str and '년' in exp_str:
        # 숫자 추출 (예: "경력 3~15년" -> "경력 3년+")
        numbers = re.findall(r'\d+', exp_str)
        if numbers:
            return f"경력 {numbers[0]}년+"
        return "경력"
    elif '경력' in exp_str:
        return "경력"
    
    return exp_str if exp_str.strip() else "정보없음"

def extract_employment_type(emp_str):
    """고용형태 추출"""
    if pd.isna(emp_str):
        return "정보없음"
    
    emp_str = str(emp_str)
    
    if '정규직' in emp_str:
        return "정규직"
    elif '계약직' in emp_str:
        return "계약직"
    elif '파트' in emp_str:
        return "파트타임"
    elif '인턴' in emp_str:
        return "인턴"
    
    return "기타"

def extract_salary(salary_str):
    """급여 정보 추출"""
    if pd.isna(salary_str):
        return "정보없음"
    
    salary_str = str(salary_str)
    
    # 연봉 정보가 있는 경우
    if '만원' in salary_str:
        numbers = re.findall(r'\d+', salary_str)
        if numbers:
            return f"{numbers[0]}만원"
    elif '원' in salary_str:
        return "급여정보있음"
    
    return "정보없음"

# 데이터 로드
df = load_data()

if df is not None:
    # 사이드바
    st.sidebar.header("🔍 필터 옵션")
    
    # 지역 필터
    locations = ['전체'] + list(df['clean_location'].unique())
    selected_location = st.sidebar.selectbox("지역 선택", locations)
    
    # 경력 필터
    experiences = ['전체'] + list(df['clean_experience'].unique())
    selected_experience = st.sidebar.selectbox("경력 선택", experiences)
    
    # 고용형태 필터
    employment_types = ['전체'] + list(df['clean_employment'].unique())
    selected_employment = st.sidebar.selectbox("고용형태 선택", employment_types)
    
    # 데이터 필터링
    filtered_df = df.copy()
    
    if selected_location != '전체':
        filtered_df = filtered_df[filtered_df['clean_location'] == selected_location]
    
    if selected_experience != '전체':
        filtered_df = filtered_df[filtered_df['clean_experience'] == selected_experience]
    
    if selected_employment != '전체':
        filtered_df = filtered_df[filtered_df['clean_employment'] == selected_employment]
    
    # 메인 대시보드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 채용공고", len(filtered_df))
    
    with col2:
        unique_companies = filtered_df['company'].nunique()
        st.metric("참여 기업수", unique_companies)
    
    with col3:
        regular_jobs = len(filtered_df[filtered_df['clean_employment'] == '정규직'])
        st.metric("정규직 공고", regular_jobs)
    
    with col4:
        seoul_jobs = len(filtered_df[filtered_df['clean_location'] == '서울'])
        st.metric("서울 지역 공고", seoul_jobs)
    
    st.markdown("---")
    
    # 차트 섹션
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 지역별 채용공고 분포")
            location_counts = filtered_df['clean_location'].value_counts()
            
            if len(location_counts) > 0:
                fig_location = px.pie(
                    values=location_counts.values,
                    names=location_counts.index,
                    title="지역별 채용공고 비율"
                )
                fig_location.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_location, use_container_width=True)
            else:
                st.info("표시할 지역 데이터가 없습니다.")
        
        with col2:
            st.subheader("💼 고용형태별 분포")
            employment_counts = filtered_df['clean_employment'].value_counts()
            
            if len(employment_counts) > 0:
                fig_employment = px.bar(
                    x=employment_counts.index,
                    y=employment_counts.values,
                    title="고용형태별 채용공고 수",
                    color=employment_counts.values,
                    color_continuous_scale="viridis"
                )
                fig_employment.update_layout(showlegend=False)
                st.plotly_chart(fig_employment, use_container_width=True)
            else:
                st.info("표시할 고용형태 데이터가 없습니다.")
    
        # 경력별 분포
        st.subheader("🎯 경력별 채용공고 분포")
        experience_counts = filtered_df['clean_experience'].value_counts()
        
        if len(experience_counts) > 0:
            fig_experience = px.bar(
                x=experience_counts.values,
                y=experience_counts.index,
                orientation='h',
                title="경력별 채용공고 수",
                color=experience_counts.values,
                color_continuous_scale="plasma"
            )
            fig_experience.update_layout(showlegend=False)
            st.plotly_chart(fig_experience, use_container_width=True)
        else:
            st.info("표시할 경력 데이터가 없습니다.")
        
        # 회사별 채용공고 수
        st.subheader("🏢 주요 채용 기업")
        company_counts = filtered_df['company'].value_counts().head(10)
        
        if len(company_counts) > 0:
            fig_company = px.bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation='h',
                title="채용공고가 많은 상위 10개 기업",
                color=company_counts.values,
                color_continuous_scale="blues"
            )
            fig_company.update_layout(showlegend=False)
            st.plotly_chart(fig_company, use_container_width=True)
        else:
            st.info("표시할 회사 데이터가 없습니다.")
    
        # 키워드 분석
        st.subheader("🔍 채용공고 제목 키워드 분석")
        
        if len(filtered_df) > 0:
            # 제목에서 키워드 추출 (RPA 관련 키워드로 업데이트)
            all_titles = ' '.join(filtered_df['title'].astype(str))
            keywords = ['RPA', '개발자', 'UiPath', 'UI Path', 'Automation', '자동화', 
                        'Consultant', 'PM', 'PL', '구축', '운영', 'AI', '시스템']
            
            keyword_counts = {}
            for keyword in keywords:
                count = all_titles.upper().count(keyword.upper())
                if count > 0:
                    keyword_counts[keyword] = count
            
            if keyword_counts:
                fig_keywords = px.bar(
                    x=list(keyword_counts.keys()),
                    y=list(keyword_counts.values()),
                    title="채용공고 제목 주요 키워드 빈도",
                    color=list(keyword_counts.values()),
                    color_continuous_scale="viridis"
                )
                fig_keywords.update_layout(showlegend=False)
                st.plotly_chart(fig_keywords, use_container_width=True)
            else:
                st.info("키워드 데이터가 없습니다.")
        else:
            st.info("분석할 데이터가 없습니다.")
    
    # 상세 데이터 테이블
    st.subheader("📋 채용공고 상세 정보")
    
    # 표시할 컬럼 선택
    display_columns = ['title', 'company', 'clean_location', 'clean_experience', 
                      'clean_employment', 'deadline']
    
    display_df = filtered_df[display_columns].copy()
    display_df.columns = ['채용제목', '회사명', '지역', '경력', '고용형태', '마감일']
    
    # 검색 기능
    search_term = st.text_input("🔍 채용공고 검색 (제목 또는 회사명)")
    if search_term:
        mask = (display_df['채용제목'].str.contains(search_term, case=False, na=False) | 
                display_df['회사명'].str.contains(search_term, case=False, na=False))
        display_df = display_df[mask]
    
    st.dataframe(display_df, use_container_width=True)
    
    # 데이터 다운로드
    st.subheader("💾 데이터 다운로드")
    
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 필터링된 데이터 CSV 다운로드",
        data=csv,
        file_name=f"filtered_jobs_{selected_location}_{selected_experience}.csv",
        mime="text/csv"
    )
    
    # 통계 요약
    st.subheader("📈 데이터 요약 통계")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**지역별 통계**")
        location_stats = filtered_df['clean_location'].value_counts()
        st.write(location_stats)
    
    with col2:
        st.write("**경력별 통계**")
        experience_stats = filtered_df['clean_experience'].value_counts()
        st.write(experience_stats)

else:
    st.error("데이터를 로드할 수 없습니다. saramin_scraper.py를 먼저 실행해주세요.")
    
    # 샘플 실행 버튼
    if st.button("🚀 샘플 크롤링 실행"):
        st.info("크롤링을 실행하려면 터미널에서 다음 명령어를 실행하세요:")
        st.code("python 08-streamlit/saramin_scraper.py")

# 푸터
st.markdown("---")
st.markdown("**📊 업무자동화 채용 정보 대시보드** | 데이터 출처: 사람인")