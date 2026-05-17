import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# 1. إعدادات الصفحة لتناسب شاشات الجوال بالكامل
st.set_page_config(page_title="نظام مبيعات المحل المطور", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 55px; font-size: 18px; font-weight: bold; }
    h1, h2, h3, p, label { text-align: right; direction: rtl; }
    div[data-testid="stDataFrame"] { width: 100%; direction: rtl; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input { text-align: right; direction: rtl; }
    div[data-testid="stNotification"] { direction: rtl; }
    </style>
""", unsafe_allow_html=True)

# 2. جلب البيانات من رابط CSV المباشر والآمن
@st.cache_data(ttl=60)
def load_data_alternative():
    sheet_id = "11J5eCOYQhDfrJ6rqv0Z35M4gs6_wM7dBWJjCmehkntc"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"فشل الاتصال المباشر بالجدول: {e}")
        return pd.DataFrame()

df = load_data_alternative()

if not df.empty:
    st.sidebar.success("متصل بنظام باسل المطور بنجاح! ✅")
else:
    st.error("خطأ: تعذر جلب البيانات. تأكد من إعدادات مشاركة الجدول.")
    st.stop()

# إدارة الذاكرة المؤقتة للباركود
if 'scanned_barcode_val' not in st.session_state:
    st.session_state.scanned_barcode_val = ""

if 'cart' not in st.session_state:
    st.session_state.cart = []

if 'invoice_num' not in st.session_state:
    st.session_state.invoice_num = datetime.now().strftime("%d%H%M%S")

# 3. الواجهة الرئيسية
st.title("⚡ نظام الفواتير الموحدة السريع")
st.write("---")

st.subheader("👤 بيانات الزبون والفاتورة")
customer_name = st.text_input("اسم الزبون (إجباري لحفظ الفاتورة):", placeholder="اكتب اسم الزبون هنا لفتح الفاتورة...")
customer_type = st.radio("نوع المعاملة:", ["نقدي (كاش)", "ذمم / دين"], horizontal=True)

st.write("---")

# 4. قسم إضافة الأصناف (كاميرا البث الحي التلقائي المحمية)
st.subheader("📦 إضافة الأصناف إلى الفاتورة")

enable_camera = st.checkbox("📷 تشغيل الكاميرا الحية لمسح الباركود تلقائياً")

if enable_camera:
    st.markdown("<p style='text-align:right;color:gray;'>وجه الكاميرا الخلفية بدقة وبشكل أفقي نحو ملصق الباركود التجاري:</p>", unsafe_allow_html=True)
    
    # كود جافاسكربت هجين ومستقر مخصص لمنع تكرار البيانات والشاشة السوداء
    scanner_html = """
    <script src="https://unpkg.com/html5-qrcode"></script>
    <div id="interactive-reader" style="width:100%; border-radius:12px; overflow:hidden; border:3px solid #00c853; background:#000;"></div>
    <script>
        let lastScannedCode = "";
        let scanCount = 0;

        function onScanSuccess(decodedText, decodedResult) {
            // التحقق من أن الكود المقروء جديد لتجنب تعليق المتصفح والشاشة السوداء
            if (decodedText !== lastScannedCode) {
                lastScannedCode = decodedText;
                scanCount++;
                
                // إرسال الكود بأمان تام إلى تطبيق بايثون
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue', 
                    value: String(decodedText) + "_" + scanCount
                }, '*');
            }
        }
        
        // دعم شامل لكل أنواع الباركودات في المحلات (EAN-13, CODE-128, QR)
        const formatsToSupport = [
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E
        ];

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "interactive-reader", 
            { 
                fps: 20, 
                qrbox: function(viewfinderWidth, viewfinderHeight) {
                    // صندوق فحص مستطيل عريض جداً مثالي للقطع التجارية والمنتجات
                    return { width: Math.floor(viewfinderWidth * 0.9), height: Math.floor(viewfinderHeight * 0.45) };
                },
                formatsToSupport: formatsToSupport,
                rememberLastUsedCamera: true,
                aspectRatio: 1.777778
            }
        );
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    camera_result = components.html(scanner_html, height=320, scrolling=False)
    
    # معالجة النص القادم وفصل رقم العداد الأمني لضمان التحديث المستمر للحقول
    if camera_result and type(camera_result) == str and "_" in camera_result:
        raw_code = camera_result.split("_")[0]
        st.session_state.scanned_barcode_val = raw_code.strip()

search_type = st.tabs(["🔍 البحث باسم الصنف", "🏷️ المسح بالباركود الحالي"])
selected_product = None

with search_type[0]:
    search_query = st.text_input("اكتب اسم المنتج أو جزء منه للبحث:", placeholder="مثال: يو شبكة، انتركم...")
    if search_query and not df.empty:
        name_col = df.columns[0]
        matched_df = df[df[name_col].astype(str).str.contains(search_query, case=False, na=False)]
        if not matched_df.empty:
            product_list = matched_df[name_col].tolist()
            selected_name = st.selectbox("اختر الصنف المطلوب من القائمة:", product_list)
            selected_product = matched_df[matched_df[name_col] == selected_name].iloc[0]
        else:
            st.warning("⚠️ لم يتم العثور على أي صنف مطابِق!")

with search_type[1]:
    # استقبال القراءة الحية والآمنة هنا تلقائياً
    barcode_input = st.text_input("رمز الباركود المقروء حالياً:", value=st.session_state.scanned_barcode_val, placeholder="سيظهر الرمز هنا تلقائياً بمجرد توجيه الكاميرا...")
    
    if barcode_input and not df.empty:
        barcode_col = df.columns[1]
        matched_barcode = df[df[barcode_col].astype(str).str.strip() == str(barcode_input).strip()]
        if not matched_barcode.empty:
            selected_product = matched_barcode.iloc[0]
            st.success("✅ تم العثور على الصنف بالباركود!")
        else:
            st.warning(f"⚠️ الباركود ({barcode_input}) غير مسجل في جدول الأصناف!")

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
        st.session_state.scanned_barcode_val = "" # تفريغ الخانة فوراً للاستعداد للمنتج التالي
        st.toast(f"تمت إضافة {p_name} بنجاح! 🛒", icon="✅")
        st.rerun()

st.write("---")

# 5. عرض الفاتورة وإدارتها
st.subheader(f"📋 تفاصيل الفاتورة الحالية رقم #{st.session_state.invoice_num}")

if st.session_state.cart:
    cart_df = pd.DataFrame(st.session_state.cart)
    st.dataframe(cart_df[["المنتج", "السعر", "الكمية", "الإجمالي"]], use_container_width=True)
    
    total_amount = cart_df["الإجمالي"].sum()
    st.markdown(f"### 💰 إجمالي حساب الفاتورة: **{total_amount} شيكل**")
    
    if st.button("🔄 تفريغ الفاتورة وتصفير السلة للبدء من جديد"):
        st.session_state.cart = []
        st.session_state.scanned_barcode_val = ""
        st.session_state.invoice_num = datetime.now().strftime("%d%H%M%S")
        st.rerun()
else:
    st.info("الفاتورة فارغة حالياً. ابحث باسم الصنف أو وجه الكاميرا نحو الباركود لبناء الفاتورة.")
