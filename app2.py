import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# 1. إعدادات الصفحة لتناسب شاشات الجوال بالكامل
st.set_page_config(page_title="نظام مبيعات المحل المطور", page_icon="⚡", layout="centered")

# تنسيق الواجهة لتناسب الجوال وضغط العمل اليومي السريع
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 55px; font-size: 18px; font-weight: bold; }
    h1, h2, h3, p, label { text-align: right; direction: rtl; }
    div[data-testid="stDataFrame"] { width: 100%; direction: rtl; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input { text-align: right; direction: rtl; }
    div[data-testid="stNotification"] { direction: rtl; }
    </style>
""", unsafe_allow_html=True)

# 2. دالة الاتصال الرسمية التي تقرأ السطر الطويل النظيف من صندوق الـ Secrets وتنسقه برمجياً
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # جلب المفتاح النظيف المكون من سطر واحد من الـ Secrets
    raw_key = st.secrets["gspread_creds"]["private_key_line"]
    
    # إعادة بناء المفتاح وإضافة ترويسة وخاتمة التشفير مع تقسيم الأسطر كل 64 حرفاً بشكل قياسي 100%
    formatted_key = "-----BEGIN PRIVATE KEY-----\n"
    for i in range(0, len(raw_key), 64):
        formatted_key += raw_key[i:i+64] + "\n"
    formatted_key += "-----END PRIVATE KEY-----\n"
    
    # بناء قاموس بيانات الاعتماد بالكامل
    creds_dict = {
        "type": "service_account",
        "project_id": "shop-management-system-496511",
        "private_key_id": "96a84df5d73ebe1eb399b9c6fca21430cb1a3814",
        "client_email": "shop-app-accessor@shop-management-system-496511.iam.gserviceaccount.com",
        "client_id": "109276117547165424292",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/shop-app-accessor%40shop-management-system-496511.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com",
        "private_key": formatted_key
    }
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    sheet_url = "https://docs.google.com/spreadsheets/d/11J5eCOYQhDfrJ6rqv0Z35M4gs6_wM7dBWJjCmehkntc/edit?usp=sharing"
    spreadsheet = client.open_by_url(sheet_url)
    
    products_sheet = spreadsheet.sheet1
    
    try:
        sales_sheet = spreadsheet.worksheet("المبيعات")
    except gspread.exceptions.WorksheetNotFound:
        sales_sheet = spreadsheet.add_worksheet(title="المبيعات", rows="1000", cols="6")
        sales_sheet.append_row(["رقم الفاتورة", "التاريخ والوقت", "اسم الزبون", "نوع البيع", "تفاصيل الفاتورة (الأصناف)", "المجموع الكلي"])
        
    try:
        debts_sheet = spreadsheet.worksheet("الذمم")
    except gspread.exceptions.WorksheetNotFound:
        debts_sheet = spreadsheet.add_worksheet(title="الذمم", rows="1000", cols="6")
        debts_sheet.append_row(["التاريخ", "اسم الزبون", "تفاصيل الفاتورة", "المبلغ المطلوب (شيكل)", "رقم الفاتورة", "حالة السداد"])

    data = products_sheet.get_all_records()
    df = pd.DataFrame(data)
    st.sidebar.success("متصل بنظام باسل المطور بنجاح! ✅")
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# 3. إدارة سلة المبيعات المؤقتة ورقم الفاتورة الحالية في النظام
if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'invoice_num' not in st.session_state:
    st.session_state.invoice_num = datetime.now().strftime("%d%H%M%S")

# 4. الواجهة الرئيسية بالتطبيق
st.title("⚡ نظام الفواتير الموحدة السريع")
st.write("---")

# قسم بيانات الزبون
st.subheader("👤 بيانات الزبون والفاتورة")
customer_name = st.text_input("اسم الزبون (إجب
