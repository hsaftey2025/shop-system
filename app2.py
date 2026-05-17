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

# 2. وضع المفتاح النشط الجديد برمجياً هنا ليتجاوز مشاكل الـ Secrets نهائياً
# تم توزيعه كـ أسطر بايثون نقية ومضمونة التشفير 100%
PRIVATE_KEY_FIXED = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCkyWo7tyIICqaU\n"
    "VKfjIr1ssWaNVwfXO7s+PP8GEdHwX308vxkULmMeBy2S3Or91y8HgA5FiiLT2DRD\n"
    "VU+BESLNQQCPP25eJyCo2BgoQOSAAXHetvyzqCSc1SyuB2mO4lbYFcr3MPFasf52\n"
    "hUVYLJM20tYaobrC3caAhV5Vmln5lc/8eWBJfHpgPC4JLye59DV+6He6cYzhgzq6\n"
    "GI9UqduxCAg6CpegaN/fiJFm009B8auzDd8rRd9A6koUucVeuwHKFRT7/U8tc12K\n"
    "mLfvlp6NfohWt/hhqhSSwTKRFGEuOUucbA4YmZvygPcd7x0J1r2OO/BVMkMPUtR7\n"
    "b7aa8TgJAgMBAAECggEAB4c0FTpOkbN63LfpW5UQtlB8cOSS9SBDc5pxxCM4RhT2\n"
    "sbnBOYzM9mg5isYQ7jvQaDVPcZnX8XmlGZZiJXFU96+KiQDK1/5NnakRoXUlezuV\n"
    "qikN7l82HPwYKHMqPV7VvNVyCkzwGcab62o3Osn+h7imE11kHNbo5KIzJxIAHkjJ\n"
    "DP2lmSrL8lJElE9elzfWuwVOLxjlkGQtjj4kBHAE6dnEfWKNmvmY/a5UXjHXNHKe\n"
    "4HBX2CglPMgOAN9P+ATd6ewivqtJXKJkAftxx5Nqf9sFg6YsY8qXdEyqUY3qhrhV\n"
    "TUFekmnSAubjjygDrDGh+iV0aXZuDu4lQDQnjU00oQKBgQDQRggdAI9CTbDYfWfo\n"
    "7wdtlVnA2cOamLhyXW7YYKrGGqP+pLsFD2+EGCiwvcpOL5yelMk5U5+vM19+vHhr\n"
    "2YLvOoc55VHDQE7Am/5ObX4ljRb06hREYveRZzVWy3Y1eZlIoeHsGMsajm3NuCW1\n"
    "DrHc0wunn7lm5OkdeE9hpmr55QKBgQDKjFCMv75wPRtq32fqmy1BbQ9hgohEmbOH\n"
    "r0k+V7D9JPQrLGSxY2IEzAzDX3vNZv8XdYyeRnay918et7yTNR2SaGOPQ0z55EWQ\n"
    "ExMqJdHW8pgGdLQd2jBErP1a+8669NnPikztLRcl1upsFk3d9Y9m0icAdvthb6du\n"
    "/NmOHltTVQKBgB7dQfaKTrCUstBiRTPPuFoU9+gMXWBboXnRPsvyB1y0NflWkCB/\n"
    "2RbKPb1zYreTdrJJekh0jAV6p3wwkefpo+2vzrpVsXgt333LoDQfJcKK1gwVZEt+\n"
    "HxH9KXpjTHFAQ+bvlntWcULOOJdz4qKiOtlurRt6IA+PfLxRR/JApznBAoGAAgr6\n"
    "QQEqFY24OhK4xJf+E9vavNwJLc/zDJpK/dL6mQMHZ2wSM+vRsESymEHdSMwSJJVt\n"
    "7qa9Sb7O+ctWnpF5k+Fzp51BKIAR54sZtWIeRLG7sMz6iBaMSBUKlSFXC3GuxLYb\n"
    "yUC58HMKXzsGiIA6UOTWyDYFjp/ENKCCznpJ+UCgYEAnwqionAzk2fm6ssnBywX\n"
    "bnHFLBzBVULG8JroKlTsontK5H9O8+GWwyWqkfZlv7E3EfC/SWLQLTeagw/0YHUO\n"
    "W7nLtc6iVH6EO7xbhdLsy+gFZR8SXbjkqwjByW3MeZJHHX5++xvLweJ1u6TnEh8S\n"
    "3GIrFs1uWQJu46imDBitzeQ=\n"
    "-----END PRIVATE KEY-----\n"
)

@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # بناء قاموس الإعدادات برمجياً لضمان النقاء الكامل للتشفير
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
        "private_key": PRIVATE_KEY_FIXED
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
        debts_sheet.append_row(
