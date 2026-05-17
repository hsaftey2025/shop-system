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

# 2. الاتصال بجوجل شيت عبر مكتبة جوجل الرسمية والحديثة المباشرة
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # جلب الإعدادات وتحويلها لقاموس نقي ليتم تمريره مباشرة للمكتبة الرسمية
    creds_dict = dict(st.secrets["gspread_creds"])
    
    # الربط الرسمي الذكي بدون أخطاء padding أو تشفير
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

# قسم بيانات الزبون (إجباري لحفظ الفاتورة)
st.subheader("👤 بيانات الزبون والفاتورة")
customer_name = st.text_input("اسم الزبون (إجباري لحفظ الفاتورة):", placeholder="اكتب اسم الزبون هنا لفتح الفاتورة...")
customer_type = st.radio("نوع المعاملة:", ["نقدي (كاش)", "ذمم / دين"], horizontal=True)

st.write("---")

# 5. قراءة الباركود أو البحث باسم المنتج المحدث بناءً على الجدول
st.subheader("📦 إضافة الأصناف إلى الفاتورة")

enable_camera = st.checkbox("📷 تشغيل الكاميرا لمسح الباركود مباشرة (بث حي)")
scanned_barcode = ""

if enable_camera:
    st.markdown("<p style='text-align:right;color:gray;'>وجه الكاميرا الخلفية نحو ملصق الباركود ليتم التقاطه فورا وبشكل حي:</p>", unsafe_allow_html=True)
    
    scanner_html = """
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="interactive-reader" style="width:100%; border-radius:12px; overflow:hidden; border:2px solid #ddd;"></div>
    <script>
        function onScanSuccess(decodedText, decodedResult) {
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: decodedText}, '*');
        }
        let html5QrcodeScanner = new Html5QrcodeScanner("interactive-reader", { fps: 20, qrbox: {width: 250, height: 150} });
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    scanned_barcode = components.html(scanner_html, height=350)

search_type = st.tabs(["🔍 البحث باسم الصنف", "🏷️ المسح بالباركود"])
selected_product = None

with search_type[0]:
    search_query = st.text_input("اكتب اسم المنتج أو جزء منه للبحث:", placeholder="مثال: يو شبكة، انتركم، وصلة...")
    if search_query and not df.empty:
        name_col = df.columns[0]
        matched_df = df[df[name_col].astype(str).str.contains(search_query, case=False, na=False)]
        
        if not matched_df.empty:
            product_list = matched_df[name_col].tolist()
            selected_name = st.selectbox("اختر الصنف المطلوب من القائمة:", product_list)
            selected_product = matched_df[matched_df[name_col] == selected_name].iloc[0]
        else:
            st.warning("⚠️ لم يتم العثور على أي صنف مطابِق لهذا الاسم!")

with search_type[1]:
    default_barcode_val = str(scanned_barcode) if scanned_barcode else ""
    barcode_input = st.text_input("أدخل أو امسح الباركود الحالي:", value=default_barcode_val, placeholder="اضغط هنا للبدء بالمسح اليدوي أو بالليزر...")
    
    if barcode_input and not df.empty:
        barcode_col = df.columns[1]
        matched_barcode = df[df[barcode_col].astype(str).str.strip() == str(barcode_input).strip()]
        if not matched_barcode.empty:
            selected_product = matched_barcode.iloc[0]
            st.success("✅ تم العثور على الصنف بالباركود!")
        else:
            st.warning("⚠️ هذا الباركود غير مسجل في جدول الأصناف!")

if selected_product is not None:
    name_col = df.columns[0]
    p_name = selected_product[name_col]
    
    default_price = 0.0
    if len(df.columns) > 3:
        try:
            default_price = float(selected_product[df.columns[3]])
        except:
            default_price = 0.0

    st.markdown(f"### الصنف الحالي المختار: **{p_name}**")
    
    col1, col2 = st.columns(2)
    with col1:
        custom_price = st.number_input("سعر البيع الحالي (شيكل):", min_value=0.0, value=default_price, step=0.5)
    with col2:
        quantity = st.number_input("الكمية المراد بيعها:", min_value=1, value=1, step=1)
        
    if st.button("🛒 إضافة هذا الصنف إلى الفاتورة الحالية"):
        item = {
            "المنتج": p_name,
            "السعر": custom_price,
            "الكمية": quantity,
            "الإجمالي": custom_price * quantity
        }
        st.session_state.cart.append(item)
        st.toast(f"تمت إضافة {p_name} بنجاح! 🛒", icon="✅")

st.write("---")

# 6. عرض الفاتورة الموحدة الكاملة والترحيل
st.subheader(f"📋 تفاصيل الفاتورة الحالية رقم #{st.session_state.invoice_num}")

if st.session_state.cart:
    cart_df = pd.DataFrame(st.session_state.cart)
    st.dataframe(cart_df[["المنتج", "السعر", "الكمية", "الإجمالي"]], use_container_width=True)
    
    total_amount = cart_df["الإجمالي"].sum()
    st.markdown(f"### 💰 إجمالي حساب الفاتورة: **{total_amount} شيكل**")
    
    items_summary = " + ".join([f"{item['المنتج']} [العدد: {item['الكمية']}]" for item in st.session_state.cart])
    
    st.markdown(f"**نص الفاتورة الموحد الجاهز للترحيل لـ Google Sheets:**")
    st.info(items_summary)
    
    if not customer_name.strip():
        st.error("⚠️ يرجى التكرم بكتابة اسم الزبون في الأعلى أولاً (حقل إجباري لتفعيل أزرار الحفظ).")
        st.button("💾 حفظ الفاتورة وترحيلها الآن", disabled=True)
    else:
        col_clear, col_save = st.columns(2)
        with col_clear:
            if st.button("❌ إلغاء وتفريغ الفاتورة"):
                st.session_state.cart = []
                st.session_state.invoice_num = datetime.now().strftime("%d%H%M%S")
                st.rerun()
                
        with col_save:
            if st.button("💾 حفظ الفاتورة وترحيلها الآن"):
                with st.spinner("جاري إرسال الفاتورة الموحدة وحفظ الحساب بالسحابة..."):
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    sales_sheet.append_row([
                        st.session_state.invoice_num,
                        current_time,
                        customer_name.strip(),
                        customer_type,
                        items_summary,
                        total_amount
                    ])
                    
                    if customer_type == "ذمم / دين":
                        debts_sheet.append_row([
                            current_time.split()[0],
                            customer_name.strip(),
                            items_summary,
                            total_amount,
                            st.session_state.invoice_num,
                            "غير مدفوع"
                        ])
                        
                    st.success(f"🎉 ممتاز! تم حفظ وترحيل فاتورة الزبون ({customer_name}) بنجاح!")
                    st.session_state.cart = []
                    st.session_state.invoice_num = datetime.now().strftime("%d%H%M%S")
                    st.rerun()
else:
    st.info("الفاتورة فارغة حالياً. ابحث باسم الصنف أو امسح الباركود لبناء الفاتورة.")
