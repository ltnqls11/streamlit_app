import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# 페이지 설정
st.set_page_config(
    page_title="사람인 업무자동화 채용 대시보드",
    page_icon="📊",
    layout="wide"
)

# 제목
st.title("📊 사람인 업무자동화 채용 통계 대시보드")
st.markdown("---")

# 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('saramin_automation_jobs.csv')
        return df
    except FileNotFoundError:
        st.error("saramin_automation_jobs.csv 파일을 찾을 수 없습니다.")
        return None

df = load_data()

if df is not None:
    # 사이드바 - 필터링 옵션
    st.sidebar.header("🔍 필터링 옵션")
    
    # 지역 필터
    locations = ['전체'] + sorted(df['location'].dropna().unique().tolist())
    selected_location = st.sidebar.selectbox("지역 선택", locations)
    
    # 경력 필터
    experiences = ['전체'] + sorted(df['experience'].dropna().unique().tolist())
    selected_experience = st.sidebar.selectbox("경력 선택", experiences)
    
    # 고용형태 필터
    employment_types = ['전체'] + sorted(df['employment_type'].dropna().unique().tolist())
    selected_employment = st.sidebar.selectbox("고용형태 선택", employment_types)
    
    # 데이터 필터링
    filtered_df = df.copy()
    if selected_location != '전체':
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    if selected_experience != '전체':
        filtered_df = filtered_df[filtered_df['experience'] == selected_experience]
    if selected_employment != '전체':
        filtered_df = filtered_df[filtered_df['employment_type'] == selected_employment]
    
    # 메인 대시보드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 채용공고", len(filtered_df))
    
    with col2:
        unique_companies = filtered_df['company'].nunique()
        st.metric("참여 기업수", unique_companies)
    
    with col3:
        regular_jobs = len(filtered_df[filtered_df['employment_type'] == '정규직'])
        st.metric("정규직 채용", regular_jobs)
    
    with col4:
        deadline_jobs = len(filtered_df[filtered_df['deadline'].notna() & (filtered_df['deadline'] != '')])
        st.metric("마감일 있는 채용", deadline_jobs)
    
    st.markdown("---")
    
    # 차트 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 지역별 채용공고 분포")
        location_counts = filtered_df['location'].value_counts()
        if not location_counts.empty:
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
        employment_counts = filtered_df['employment_type'].value_counts()
        if not employment_counts.empty:
            fig_employment = px.bar(
                x=employment_counts.index,
                y=employment_counts.values,
                title="고용형태별 채용공고 수",
                labels={'x': '고용형태', 'y': '채용공고 수'}
            )
            fig_employment.update_layout(showlegend=False)
            st.plotly_chart(fig_employment, use_container_width=True)
        else:
            st.info("표시할 고용형태 데이터가 없습니다.")
    
    # 경력별 분석
    st.subheader("🎯 경력별 채용공고 분포")
    experience_counts = filtered_df['experience'].value_counts()
    if not experience_counts.empty:
        fig_experience = px.bar(
            x=experience_counts.values,
            y=experience_counts.index,
            orientation='h',
            title="경력별 채용공고 수",
            labels={'x': '채용공고 수', 'y': '경력 요구사항'}
        )
        st.plotly_chart(fig_experience, use_container_width=True)
    else:
        st.info("표시할 경력 데이터가 없습니다.")
    
    # 학력별 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎓 학력별 요구사항")
        education_counts = filtered_df['education'].value_counts()
        if not education_counts.empty:
            fig_education = px.pie(
                values=education_counts.values,
                names=education_counts.index,
                title="학력별 채용공고 비율"
            )
            st.plotly_chart(fig_education, use_container_width=True)
        else:
            st.info("표시할 학력 데이터가 없습니다.")
    
    with col2:
        st.subheader("📅 마감일 현황")
        deadline_status = []
        for deadline in filtered_df['deadline']:
            if pd.isna(deadline) or deadline == '':
                deadline_status.append('마감일 없음')
            elif '상시채용' in str(deadline):
                deadline_status.append('상시채용')
            elif '채용시' in str(deadline):
                deadline_status.append('채용시')
            else:
                deadline_status.append('마감일 있음')
        
        deadline_counts = Counter(deadline_status)
        if deadline_counts:
            fig_deadline = px.pie(
                values=list(deadline_counts.values()),
                names=list(deadline_counts.keys()),
                title="마감일 현황 분포"
            )
            st.plotly_chart(fig_deadline, use_container_width=True)
        else:
            st.info("표시할 마감일 데이터가 없습니다.")
    
    # 상위 기업 분석
    st.subheader("🏢 채용 활발한 기업 TOP 10")
    company_counts = filtered_df['company'].value_counts().head(10)
    if not company_counts.empty:
        fig_companies = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            title="기업별 채용공고 수",
            labels={'x': '채용공고 수', 'y': '기업명'}
        )
        st.plotly_chart(fig_companies, use_container_width=True)
    else:
        st.info("표시할 기업 데이터가 없습니다.")
    
    # 키워드 분석
    st.subheader("🔍 채용공고 제목 키워드 분석")
    
    # 제목에서 키워드 추출
    all_titles = ' '.join(filtered_df['title'].dropna().tolist())
    keywords = ['AI', '인공지능', 'RPA', '자동화', '개발자', '시스템', '솔루션', '기술', '데이터', '프로그래밍']
    keyword_counts = {}
    
    for keyword in keywords:
        count = all_titles.upper().count(keyword.upper())
        if count > 0:
            keyword_counts[keyword] = count
    
    if keyword_counts:
        fig_keywords = px.bar(
            x=list(keyword_counts.keys()),
            y=list(keyword_counts.values()),
            title="채용공고 제목 키워드 빈도",
            labels={'x': '키워드', 'y': '빈도'}
        )
        st.plotly_chart(fig_keywords, use_container_width=True)
    else:
        st.info("표시할 키워드 데이터가 없습니다.")
    
    # 데이터 테이블
    st.subheader("📋 채용공고 상세 정보")
    
    # 컬럼 선택
    display_columns = st.multiselect(
        "표시할 컬럼 선택",
        options=filtered_df.columns.tolist(),
        default=['title', 'company', 'location', 'experience', 'employment_type', 'deadline']
    )
    
    if display_columns:
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            height=400
        )
    
    # 데이터 다운로드
    st.subheader("💾 데이터 다운로드")
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="필터링된 데이터 CSV 다운로드",
        data=csv,
        file_name=f"filtered_jobs_{selected_location}_{selected_experience}.csv",
        mime="text/csv"
    )
    
    # 통계 요약
    st.markdown("---")
    st.subheader("📈 통계 요약")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**지역별 통계:**")
        location_stats = filtered_df['location'].value_counts()
        for location, count in location_stats.head(5).items():
            percentage = (count / len(filtered_df)) * 100
            st.write(f"- {location}: {count}개 ({percentage:.1f}%)")
    
    with col2:
        st.write("**경력별 통계:**")
        experience_stats = filtered_df['experience'].value_counts()
        for experience, count in experience_stats.head(5).items():
            percentage = (count / len(filtered_df)) * 100
            st.write(f"- {experience}: {count}개 ({percentage:.1f}%)")

else:
    st.error("데이터를 로드할 수 없습니다. saramin_automation_jobs.csv 파일이 있는지 확인해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>📊 사람인 업무자동화 채용 대시보드 | 데이터 기반 채용 시장 분석</p>
    </div>
    """,
    unsafe_allow_html=True
)