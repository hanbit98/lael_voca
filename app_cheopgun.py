import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. 기본 설정 및 사용자 계정 관리
# ---------------------------------------------------------
st.set_page_config(page_title="첩약건강보험 분석시스템", layout="wide")

USERS = {
    "admin": {"pw": "1234", "branch": "admin"},
    "gangnam": {"pw": "1111", "branch": "강남"},
    "busan": {"pw": "2222", "branch": "해운대"},
    "han": {"pw": "0000", "branch": "하남"},
}

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_cheopgun_data():
    file_path = 'cheopgun.csv'
    
    column_names = [
        "상병명", "처방이름", "접수일", "차트번호", "나이", "성별", 
        "팩수", "첩당금액", "처방일", "적용여부", "분원명"
    ]
    
    try:
        df = pd.read_csv(file_path, header=0)
        
        if len(df.columns) >= 11:
            df = df.iloc[:, :11]
            df.columns = column_names
        
        # 날짜 변환 및 정렬
        df['처방일'] = pd.to_datetime(df['처방일'])
        df = df.sort_values(by='처방일')
        
        # 연도/월/주차 생성
        df['연도'] = df['처방일'].dt.year.astype(str)
        df['월'] = df['처방일'].dt.month
        df['주차'] = df['처방일'].dt.isocalendar().week
        
        # -----------------------------------------------------
        # [핵심 보정] 연말/연초 주차 꼬임 해결
        # -----------------------------------------------------
        # 문제: 2024-12-30(월)은 ISO 기준 '2025년 1주차'로 잡힘.
        # 해결: 12월이면서 1주차인 경우 -> '53주차'로 강제 변경하여 12월 마지막에 표시되게 함.
        mask_yearend = (df['월'] == 12) & (df['주차'] == 1)
        df.loc[mask_yearend, '주차'] = 53
        
        # (참고) 반대의 경우: 1월 1일이 작년 52/53주차인 경우 -> '0주차'로 만들어 맨 위로 올릴 수도 있음.
        # 일단 요청하신 연말 문제(12월 30일이 1주차로 튀는 현상)는 위 코드로 해결됩니다.

        # 숫자형 변환
        numeric_cols = ['팩수', '첩당금액', '나이']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # 처방차수 계산 (연도별 리셋)
        df['처방차수'] = df.groupby(['차트번호', '상병명', '연도']).cumcount() + 1
        
        return df

    except FileNotFoundError:
        st.error(f"데이터 파일({file_path})을 찾을 수 없습니다.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 에러 발생: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# 3. 로그인 화면
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

if not st.session_state['logged_in']:
    st.title("🌿 첩약건강보험 분석시스템")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("로그인")
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        if st.button("접속하기"):
            if username in USERS and USERS[username]['pw'] == password:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = USERS[username]
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호를 확인해주세요.")
    st.stop()

# ---------------------------------------------------------
# 4. 메인 대시보드 구조 (사이드바)
# ---------------------------------------------------------
user_branch = st.session_state['user_info']['branch']
df = load_cheopgun_data()

if df.empty:
    st.stop()

with st.sidebar:
    st.info(f"접속자: **{user_branch}** 님")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.header("🔍 분석 조건 설정")
    
    # 1. 연도 선택
    available_years = sorted(df['연도'].unique(), reverse=True)
    if not available_years: available_years = ['2026', '2025', '2024']
    selected_year = st.selectbox("📅 연도 선택", available_years, index=0)
    
    # 2. 통계 기준 (기본값을 '주간'으로 변경하기 위해 index=1 설정)
    report_type = st.selectbox("📊 통계 기준", ["월간", "주간"], index=1)

    # 3. 분원 선택
    if user_branch == 'admin':
        branch_list = sorted(df['분원명'].unique().astype(str))
        branch_options = ['전체'] + branch_list
        selected_branch = st.selectbox("🏥 분원 선택", branch_options)
    else:
        selected_branch = user_branch
        st.markdown(f"**분원:** {selected_branch}")

# ---------------------------------------------------------
# 5. 데이터 필터링
# ---------------------------------------------------------
# (1) 연도 필터링
df_filtered = df[df['연도'] == selected_year].copy()

# (2) 분원 필터링
if selected_branch != '전체':
    df_filtered = df_filtered[df_filtered['분원명'] == selected_branch]

# ---------------------------------------------------------
# 6. 통계 및 시각화 로직 (간소화됨: 1주차가 맨 아래)
# ---------------------------------------------------------
st.title(f"첩약건강보험 분석 - {selected_year}년 ({report_type})")
st.markdown(f"**선택된 분원:** {selected_branch}")
st.markdown("---")

# 6-1. 데이터 가공
if report_type == '월간':
    df_filtered['Period'] = df_filtered['월']
    y_axis_label = "월"
    period_suffix = "월"
else:
    df_filtered['Period'] = df_filtered['주차']
    y_axis_label = "주차"
    period_suffix = "주차"

# 6-2. [그래프 1] 처방차수별 처방건수
st.subheader(f"📊 {y_axis_label}별 처방차수 현황")

if not df_filtered.empty:
    # (1) 데이터 집계
    chart_data = df_filtered.groupby(['Period', '처방차수']).size().reset_index(name='건수')
    
    # (2) 라벨 생성 및 정렬 (기본 오름차순: 1, 2, 3...)
    # 1주차가 리스트의 앞쪽에 오면 -> 그래프의 '가장 아래'에 그려집니다. (자연스러운 동작)
    unique_periods_asc = sorted(chart_data['Period'].unique()) 
    period_order_labels = [f"{p}{period_suffix}" for p in unique_periods_asc]
    
    chart_data['Period_Label'] = chart_data['Period'].apply(lambda x: f"{x}{period_suffix}")
    chart_data['처방차수_Str'] = chart_data['처방차수'].astype(str)

    # (3) 색상 매핑
    colors = {'1': 'blue', '2': 'red', '3': '#FFD700', '4': 'green'}
    max_order = chart_data['처방차수'].max()
    color_map = {}
    order_legend = []
    
    for i in range(1, int(max_order) + 1):
        s = str(i)
        order_legend.append(s)
        color_map[s] = colors.get(s, 'orange') # 5차 이상은 orange

    # (4) 그래프 그리기
    fig = px.bar(
        chart_data,
        x="건수",
        y="Period_Label",
        color="처방차수_Str",
        orientation='h',
        color_discrete_map=color_map,
        category_orders={
            # 오름차순 리스트 전달 -> 1주차가 바닥, 53주차가 꼭대기
            "Period_Label": period_order_labels,
            "처방차수_Str": order_legend
        },
        text="건수"
    )

    # 높이 계산 (항목 수에 따라 자동 조절)
    final_height = min(900, max(500, len(unique_periods_asc) * 40))

    fig.update_layout(
        xaxis_title="처방 건수",
        yaxis_title=y_axis_label,
        legend_title="처방차수",
        height=final_height,
        bargap=0.15,
        xaxis=dict(showgrid=True, gridcolor='#eee'),
        plot_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("해당 조건에 맞는 데이터가 없습니다.")

with st.expander("📋 상세 데이터 보기"):
    st.dataframe(df_filtered.sort_values(by='처방일', ascending=False), use_container_width=True)

    