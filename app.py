import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import pyodbc
import plotly.graph_objects as go
from dotenv import load_dotenv
from pathlib import Path
import os

st.set_page_config(layout= 'wide',page_title="Quản lý máy may",page_icon=":bar_chart:")
# st.logo("logo.png")
st.markdown(
    """
    <style>
    .centered-title {
        text-align: center;
        margin-top: 0 px;
        color: 'rgb(255,255,255)';
        font-size : 48px;
        font-family = 'Arial';
    }
    div.block-container{padding-top:1rem;
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="centered-title">BÁO CÁO QUẢN LÝ MÁY MAY</h1>', unsafe_allow_html=True)
#HÀM LẤY DATA TỪ SQL

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / ".env"
load_dotenv(env_file)

def get_data(DB,query):
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        f'SERVER={os.getenv("SERVER")};'
        f'DATABASE={DB};'
        f'UID={os.getenv("UID")};'
        f'PWD={os.getenv("PASSWORD")}'
    )
    df = pd.read_sql(query,conn)
    conn.close()
    return df
def run_exec_sql(from_date,to_date,buffer):
    conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    f'SERVER={os.getenv("SERVER")};'
    f'DATABASE={os.getenv("DB")};'
    f'UID={os.getenv("UID")};'
    f'PWD={os.getenv("PASSWORD")}'
    )
    query = f"EXEC QUAN_LY_MAY_MAY '{from_date}','{to_date}','{buffer}'"
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.commit()
    cursor.close()
    conn.close()

df = get_data('DW','SELECT * FROM CAN_DOI_MAY_MAY WHERE LOAI_MAY IS NOT NULL')
df['NGAY'] = pd.to_datetime(df['NGAY'], format = '%Y-%m-%d')

cols = st.columns((2,2,2,1,1))
with cols[0]:
    min_date = pd.to_datetime(df['NGAY'].min())
    from_date = pd.to_datetime(st.date_input("Từ ngày:",value=min_date.date()))
with cols[1]:
    max_date = pd.to_datetime(df['NGAY'].max())
    to_date = pd.to_datetime(st.date_input("Đến ngày:",value=max_date.date()))
with cols[2]:
    trang_thai = st.selectbox("Tình trạng máy:",options=['OK','Hỏng'],index=0)
df = df[(df['NGAY']>= from_date) & (df['NGAY']<= to_date)]
with cols[3]:
    buffer = st.slider(label="Chọn khoảng buffer",min_value=0.0,max_value=1.0,value=0.1)
with cols[4]:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    if st.button("Tải lại dữ liệu",use_container_width=True):
        run_exec_sql(from_date.strftime("%Y-%m-%d"),to_date.strftime("%Y-%m-%d"),buffer)
        df = get_data('DW','SELECT * FROM CAN_DOI_MAY_MAY WHERE LOAI_MAY IS NOT NULL')
        df['NGAY'] = pd.to_datetime(df['NGAY'], format = '%Y-%m-%d')
        st.rerun()
        st.success("Tải thành công dữ liệu mới!")

df['NGAY'] = df['NGAY'].dt.date
df1 = df[df['NHA_MAY'] == "NT1"]
df2 = df[df['NHA_MAY'] == "NT2"]

df1_1 = df1.melt(id_vars=['NGAY','Loai_may'],value_vars=['MAY_CAN','MAY_TON'] )
df2_1 = df2.melt(id_vars=['NGAY','Loai_may'],value_vars=['MAY_CAN','MAY_TON'] )

df1_2 = df1_1.sort_values('NGAY')
df2_2 = df2_1.sort_values('NGAY')
df3_2 = df.sort_values('NGAY')
df4_1 = df3_2[df3_2['NHA_MAY']=='NT1']
df4_2 = df3_2[df3_2['NHA_MAY']=='NT2']
df4_3 = pd.merge(df4_1,df4_2, on = ['NGAY','Loai_may'], how='left')
#TÍNH SỐ LƯỢNG MÁY CHO MƯỢN
df4_3['Cân bằng'] = df4_3.apply(lambda x: 
    -x['THUA_THIEU_y'] if (x['THUA_THIEU_x'] < 0 and x['THUA_THIEU_y'] > 0 and (x['THUA_THIEU_x'] + x['THUA_THIEU_y']) <= 0 )
    else x['THUA_THIEU_x'] if (x['THUA_THIEU_x'] < 0 and x['THUA_THIEU_y'] > 0 and (x['THUA_THIEU_x'] + x['THUA_THIEU_y']) > 0 )
    else x['THUA_THIEU_x'] if (x['THUA_THIEU_x'] > 0 and x['THUA_THIEU_y'] < 0 and (x['THUA_THIEU_x'] + x['THUA_THIEU_y']) <= 0)
    else -x['THUA_THIEU_y'] if (x['THUA_THIEU_x'] > 0 and x['THUA_THIEU_y'] < 0 and (x['THUA_THIEU_x'] + x['THUA_THIEU_y']) > 0)
    else 0, axis=1
)
df4_3 = df4_3[['NGAY','Loai_may','Cân bằng']].sort_values('NGAY')
# FORMATING
df1_2['value_formated'] = df1_2['value'].apply(lambda x: f"{x:,.0f}")
df2_2['value_formated'] = df2_2['value'].apply(lambda x: f"{x:,.0f}")
df3_2['thua_thieu_formated'] = df3_2['THUA_THIEU'].apply(lambda x: f"{x:,.0f}")
df4_3['Cân bằng formated'] = df4_3['Cân bằng'].apply(lambda x: f"{x:,.0f}")
df1_2 = df1_2.replace({'variable' : {'MAY_CAN' : 'Máy cần','MAY_TON' : 'Máy đang có'}})
df2_2 = df2_2.replace({'variable' : {'MAY_CAN' : 'Máy cần','MAY_TON' : 'Máy đang có'}})

# BIỂU ĐỒ THỪA THIẾU MÁY MAY
# color_seq = ['blue','light blue','green','dark green','red','light red','orange','black']
def thua_thieu_may(nha_may):
    df3_2_filtered = df3_2[(df3_2['NHA_MAY'] == nha_may) & (df3_2['Loai_may'].isin(ds_may_selected))]
    
    fig1 = px.line(df3_2_filtered,
                   x="NGAY",y="THUA_THIEU",color="Loai_may",text="thua_thieu_formated",
                   category_orders= {'Loai_may' : ds_may_selected})
    fig1.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig1.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số lượng máy may thừa thiếu",
        title = f"Số lượng máy may thừa thiếu - {nha_may}",
        hovermode = 'x'
    )
    fig1.update_traces(
        textposition = 'top center',
        textfont = dict(size = 12),
        mode = 'lines+text',
        hovertemplate = None
    )
    
    for loai_may in df3_2_filtered['Loai_may'].unique():
    # Lấy dữ liệu theo loại máy hiện tại
        df_may = df3_2_filtered[df3_2_filtered['Loai_may'] == loai_may]

    # Gán màu theo điều kiện âm/dương cho từng loại máy riêng biệt
    #     fig1.add_trace(
    #         go.Scatter(
    #             x=df_may['NGAY'],
    #             y=df_may['THUA_THIEU'],
    #             mode='text',
    #             text=df_may['thua_thieu_formated'],
    #             textposition='top center',
    #             textfont=dict(
    #                 size=14,
    #                 color=['red' if val < 0 else 'green' for val in df_may['THUA_THIEU']]
    #             ),
    #             name=loai_may
    #     )
    # )

    st.plotly_chart(fig1,use_container_width=True)

def thua_thieu_may_fill(nha_may):
    df3_2_filtered = df3_2[(df3_2['NHA_MAY'] == nha_may) & (df3_2['Loai_may'].isin(ds_may_selected))]
    
    fig = go.Figure()
    
    for loai_may in df3_2_filtered['Loai_may'].unique():
    # Lấy dữ liệu theo loại máy hiện tại
        df_may = df3_2_filtered[df3_2_filtered['Loai_may'] == loai_may]

    # Gán màu theo điều kiện âm/dương cho từng loại máy riêng biệt
        fig.add_trace(
            go.Scatter(
                x=df_may['NGAY'],
                y=df_may['THUA_THIEU'],
                mode='lines+text',
                text=df_may['thua_thieu_formated'],
                textposition='top center',
                fill= 'tozeroy',
                textfont=dict(
                    size=12,
                    color=['red' if val < 0 else 'green' for val in df_may['THUA_THIEU']]
                ),
                name=loai_may
        )
    )
        fig.update_xaxes(
            dtick = 'D1',
            tickangle = 45,
            tickformat = "%d/%m"
        )
        fig.update_layout(
            xaxis_title = "Ngày",
            yaxis_title = "Số lượng máy may thừa thiếu",
            title = f"Số lượng máy may thừa thiếu - {nha_may}",
            hovermode = 'x'
        )
        fig.update_traces(
            hovertemplate = None,
            showlegend = True
        )

    st.plotly_chart(fig,use_container_width=True)
def can_bang_may():
    df4_3_filtered =df4_3[df4_3['Loai_may'].isin(ds_may_selected)] 
    fig1 = px.line(df4_3_filtered,x='NGAY',y='Cân bằng',text='Cân bằng formated',
                   color="Loai_may",category_orders= {'Loai_may' : ds_may_selected},hover_data=None)
    fig1.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig1.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số máy NT1 cho NT2 mượn",
        title = f"Cân bằng máy may đề xuất (+ NT1 cho NT2 mượn , - NT2 cho NT1 mượn)"
    )
    fig1.update_traces(
        textposition = 'top center',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        mode = 'lines+text'
    )
    st.plotly_chart(fig1,use_container_width=True)

def can_bang_may_fill():
    df4_3_filtered = df4_3[df4_3['Loai_may'].isin(ds_may_selected)] 

    fig1 = go.Figure()

    # Lặp qua từng loại máy để thêm dữ liệu với fill
    for loai_may in df4_3_filtered['Loai_may'].unique():
        df_loai_may = df4_3_filtered[df4_3_filtered['Loai_may'] == loai_may]
        
        fig1.add_trace(go.Scatter(
            x=df_loai_may['NGAY'],
            y=df_loai_may['Cân bằng'],
            mode='lines+text',  # Hiển thị cả đường và văn bản
            text=df_loai_may['Cân bằng formated'],
            textposition=['top center' if val < 0 else 'bottom center' for val in df_loai_may['Cân bằng']],
            fill='tozeroy',  # Tô phần nền từ đường đến trục x
            name=loai_may,  # Loại máy
            textfont=dict(color=['red' if val < 0 else 'green' for val in df_loai_may['Cân bằng']],
                          size=12,),
        ))

    # Cập nhật trục x
    fig1.update_xaxes(
        dtick='D1',
        tickangle=45,
        tickformat="%d/%m"
    )

    # Cập nhật bố cục của biểu đồ
    fig1.update_layout(
        xaxis_title="Ngày",
        yaxis_title="Số máy NT1 cho NT2 mượn",
        title="Cân bằng máy may đề xuất (+ NT1 cho NT2 mượn , - NT2 cho NT1 mượn)",
        showlegend=True
    )

    # Hiển thị biểu đồ trong Streamlit
    st.plotly_chart(fig1, use_container_width=True)

    
      
#HÀM ĐỂ VẼ CHI TIẾT THEO TỪNG LOẠI MÁY
def detail_chart(loai_may):
    fig1 = px.line(df1_2[df1_2['Loai_may'] == loai_may],x="NGAY",y="value",color="variable",text="value_formated",
                   color_discrete_map={'Máy cần' : 'red','Máy đang có' : 'green'})
    fig2 = px.line(df2_2[df2_2['Loai_may'] == loai_may],x="NGAY",y="value",color="variable",text="value_formated",
                   color_discrete_map={'Máy cần' : 'red','Máy đang có' : 'green'})
    fig3 = px.line(df3_2[df3_2['Loai_may'] == loai_may],x='NGAY',y='THUA_THIEU',color='NHA_MAY',text='thua_thieu_formated',
                   color_discrete_map={'NT1': 'blue','NT2' : 'light blue'})
    fig4 = px.line(df4_3[df4_3['Loai_may'] == loai_may],x='NGAY',y='Cân bằng',text='Cân bằng formated',
                   color_discrete_map={'Cân bằng': 'black'})
    fig1.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig1.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số lượng máy may",
        title = f"Máy {loai_may} - Nam Thuận 1"    
    )
    fig1.update_traces(
        textposition = 'top center',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        mode = 'lines+text'
    )
    fig2.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig2.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số lượng máy may",
        title = f"Máy {loai_may} - Nam Thuận 2"
    )
    fig2.update_traces(
        textposition = 'top center',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        mode = 'lines+text'
    )
    fig3.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig3.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số lượng máy may",
        title = f"Máy {loai_may} - Số lượng máy thừa/thiếu trên mỗi nhà máy"
    )
    fig3.update_traces(
        textposition = 'top center',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        mode = 'lines+text'
    )
    fig4.update_xaxes(
        dtick = 'D1',
        tickangle = 45,
        tickformat = "%d/%m"
    )
    fig4.update_layout(
        xaxis_title = "Ngày",
        yaxis_title = "Số lượng máy may cho mượn (đề xuất)",
        title = f"Cân bằng Máy {loai_may} (+ NT1 cho NT2 mượn , - NT2 cho NT1 mượn)"
    )
    fig4.update_traces(
        textposition = 'top center',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        mode = 'lines+text'
    )

    st.plotly_chart(fig1,use_container_width= True)
    st.plotly_chart(fig2,use_container_width= True)
    st.plotly_chart(fig3,use_container_width= True)
    st.plotly_chart(fig4,use_container_width= True)
    
def bar_chart_may_ton(nha_may,trang_thai):
    df_may_ton = get_data('DW',f"SELECT * FROM MAYTON WHERE NGAY = CAST(GETDATE() AS DATE) and Nha_may = '{nha_may}' and trang_thai = N'{trang_thai}'")
    fig = px.bar(df_may_ton.sort_values(by='Loai_may',ascending=False),
                 x= 'Loai_may',
                 y='So_luong',
                 color='Trang_thai',
                 title=f"Tổng số máy may ngày hôm nay - nhà máy {nha_may}",
                 text='So_luong'
                 )
    fig.update_layout(
        xaxis_title = "Loại máy",
        yaxis_title = "Số lượng tồn",
        title = f"Số lượng máy tồn nhà máy {nha_may} ngày hôm nay"
    )
    fig.update_traces(
        textposition = 'outside',
        textfont = dict(color = 'rgb(0,0,0)',size = 12)
    )
    max_y = df_may_ton['So_luong'].max() * 1.2
    fig.update_yaxes(
        range=[0, max_y]
    )
    st.plotly_chart(fig,use_container_width=True)  
def pie_chart(nha_may):
    df_may_ton = get_data('DW',f"SELECT * FROM MAYTON WHERE NGAY = CAST(GETDATE() AS DATE) and Nha_may = '{nha_may}'")
    fig = px.pie(df_may_ton,names='Trang_thai',values='So_luong',title="Tình trạng máy trong ngày")
    fig.update_traces(
        textposition = 'outside',
        textfont = dict(color = 'rgb(0,0,0)',size = 12),
        textinfo = 'label+percent'
    )
    st.plotly_chart(fig)
cols = st.columns(2)
with cols[0]:
    bar_chart_may_ton("NT1",trang_thai)
    pie_chart(nha_may="NT1")
with cols[1]:
    bar_chart_may_ton("NT2",trang_thai)
    pie_chart(nha_may="NT2")
#CHỌN LOẠI MÁY ĐỂ PHÂN TÍCH
ds_may = pd.Series(df3_2['Loai_may'].unique()).sort_values(ascending=False)
ds_may_selected = st.multiselect("Chọn loại máy:",options=ds_may,default=['SN','OL','FL (hemming)'])

with st.expander("Chi tiết máy SN"): 
    detail_chart("SN")           
with st.expander("Chi tiết máy OL"): 
    detail_chart("OL")
with st.expander("Chi tiết máy OL Top feeder - Máy cổ nhỏ"): 
    detail_chart("OL Top feeder - Máy cổ nhỏ")
with st.expander("Chi tiết máy FL binding"): 
    detail_chart("FL binding")
with st.expander("Chi tiết máy Bartack (BTK)"): 
    detail_chart("Bartack (BTK)")
with st.expander("Chi tiết máy BTH"):
    detail_chart("BTH") 
with st.expander("Cân đối máy may"):
    thua_thieu_may("NT1")
    thua_thieu_may("NT2")
    can_bang_may()