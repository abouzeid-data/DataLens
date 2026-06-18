const translations = {
  en: {
    // App
    appName: 'DataLens',
    // Navigation
    navDashboard: 'Dashboard',
    navUpload: 'Upload',
    navAnalysis: 'Analysis',
    navReports: 'Reports',
    navHistory: 'History',
    navSettings: 'Settings',
    // Auth
    authWelcome: 'Welcome Back',
    username: 'Username',
    password: 'Password',
    forgotPassword: 'Forgot Password?',
    haveResetToken: 'I have a reset token',
    login: 'Login',
    noAccount: "Don't have an account?",
    signUp: 'Sign Up',
    createAccount: 'Create Account',
    firstName: 'First Name',
    lastName: 'Last Name',
    emailAddress: 'Email Address',
    useCaseLabel: 'What type of data will you analyze?',
    useCaseGeneral: 'General / Other',
    useCaseFinance: 'Finance',
    useCaseEcommerce: 'E-Commerce / Sales',
    useCaseHealthcare: 'Healthcare',
    alreadyHaveAccount: 'Already have an account?',
    resetPassword: 'Reset Password',
    forgotPasswordHelp: "Enter your email address and we'll send you a link to reset your password.",
    sendResetLink: 'Send Reset Link',
    backToLogin: 'Back to Login',
    newPassword: 'New Password',
    updatePassword: 'Update Password',
    cancel: 'Cancel',
    // Upload
    uploadTitle: 'Upload Your Data',
    uploadDesc: 'Drag and drop your CSV or Excel file here',
    uploadBrowse: 'Browse Files',
    uploadSupported: 'Supported formats: CSV, XLS, XLSX',
    // Data Preview
    dataPreview: 'Your Data Snapshot',
    rows: 'Total Rows',
    columns: 'Total Columns',
    missingValues: 'Empty Fields (Missing Data)',
    duplicateRows: 'Exact Copies (Duplicates)',
    // KPIs
    kpiTitle: 'Business Performance Summary',
    totalRevenue: 'Total Revenue',
    averageSale: 'Average Sale',
    maxSale: 'Highest Sale',
    minSale: 'Lowest Sale',
    transactions: 'Transactions',
    bestProduct: 'Best-Selling Product',
    worstProduct: 'Worst-Selling Product',
    bestDay: 'Best Sales Day',
    // Charts
    chartsTitle: 'Charts & Visualizations',
    // Insights
    insightsTitle: 'Business Insights',
    aiInsightsTitle: 'AI Business Explanation',
    aiLoading: 'Getting AI explanation...',
    // Forecast
    forecastTitle: 'Future Revenue Forecast',
    forecastDesc: 'Based on your past sales trends',
    noForecast: 'Not enough data for forecasting. We need at least 2 months of data to predict the future.',
    // Reports
    reportsTitle: 'PDF Report',
    generateReport: 'Generate Report',
    downloadReport: 'Download Report',
    openReport: 'Open Report',
    reportGenerating: 'Generating report...',
    // History
    historyTitle: 'Analysis History',
    historyEmpty: 'No analysis history yet. Upload a file to get started!',
    historyFile: 'File Name',
    historyDate: 'Date',
    historyRows: 'Rows',
    historyCols: 'Columns',
    historyRevenue: 'Revenue',
    // Cleaning
    cleaningTitle: 'Data Cleaning',
    cleaningDone: 'Data has been cleaned successfully',
    // Detected Columns
    detectedColumns: 'Detected Business Columns',
    dateColumn: 'Date Column',
    salesColumn: 'Sales Column',
    productColumn: 'Product Column',
    quantityColumn: 'Quantity Column',
    categoryColumn: 'Category Column',
    priceColumn: 'Price Column',
    notDetected: 'Not detected',
    // Settings
    settingsTitle: 'Settings',
    language: 'Language',
    apiKey: 'Groq API Key',
    apiKeySaved: 'API key saved',
    save: 'Save',
    // General
    loading: 'Loading...',
    offlineMode: 'Offline mode',
    error: 'Error',
    success: 'Success',
    noData: 'N/A',
  },
  ar: {
    // App
    appName: 'DataLens',
    // Navigation
    navDashboard: 'لوحة التحكم',
    navUpload: 'رفع ملف',
    navAnalysis: 'التحليل',
    navReports: 'التقارير',
    navHistory: 'السجل',
    navSettings: 'الإعدادات',
    // Auth
    authWelcome: 'مرحبا بعودتك',
    username: 'اسم المستخدم',
    password: 'كلمة المرور',
    forgotPassword: 'هل نسيت كلمة المرور؟',
    haveResetToken: 'لدي رمز إعادة تعيين',
    login: 'تسجيل الدخول',
    noAccount: 'ليس لديك حساب؟',
    signUp: 'إنشاء حساب',
    createAccount: 'إنشاء حساب',
    firstName: 'الاسم الأول',
    lastName: 'اسم العائلة',
    emailAddress: 'البريد الإلكتروني',
    useCaseLabel: 'ما نوع البيانات التي ستقوم بتحليلها؟',
    useCaseGeneral: 'عام / أخرى',
    useCaseFinance: 'المالية',
    useCaseEcommerce: 'التجارة الإلكترونية / المبيعات',
    useCaseHealthcare: 'الرعاية الصحية',
    alreadyHaveAccount: 'لديك حساب بالفعل؟',
    resetPassword: 'إعادة تعيين كلمة المرور',
    forgotPasswordHelp: 'أدخل بريدك الإلكتروني وسنرسل لك رابطا لإعادة تعيين كلمة المرور.',
    sendResetLink: 'إرسال رابط إعادة التعيين',
    backToLogin: 'العودة إلى تسجيل الدخول',
    newPassword: 'كلمة المرور الجديدة',
    updatePassword: 'تحديث كلمة المرور',
    cancel: 'إلغاء',
    // Upload
    uploadTitle: 'ارفع بياناتك',
    uploadDesc: 'اسحب وأفلت ملف CSV أو Excel هنا',
    uploadBrowse: 'تصفح الملفات',
    uploadSupported: 'الصيغ المدعومة: CSV, XLS, XLSX',
    // Data Preview
    dataPreview: 'نظرة عامة على بياناتك',
    rows: 'إجمالي الصفوف',
    columns: 'إجمالي الأعمدة',
    missingValues: 'الحقول الفارغة (بيانات مفقودة)',
    duplicateRows: 'نسخ متطابقة (مكررة)',
    // KPIs
    kpiTitle: 'ملخص أداء الأعمال',
    totalRevenue: 'إجمالي الإيرادات',
    averageSale: 'متوسط البيع',
    maxSale: 'أعلى بيع',
    minSale: 'أدنى بيع',
    transactions: 'المعاملات',
    bestProduct: 'المنتج الأكثر مبيعاً',
    worstProduct: 'المنتج الأقل مبيعاً',
    bestDay: 'أفضل يوم مبيعات',
    // Charts
    chartsTitle: 'الرسوم البيانية',
    // Insights
    insightsTitle: 'رؤى الأعمال',
    aiInsightsTitle: 'شرح الذكاء الاصطناعي',
    aiLoading: 'جاري الحصول على شرح الذكاء الاصطناعي...',
    // Forecast
    forecastTitle: 'توقعات الإيرادات المستقبلية',
    forecastDesc: 'بناءً على اتجاهات مبيعاتك السابقة',
    noForecast: 'لا توجد بيانات كافية للتنبؤ. نحتاج إلى شهرين على الأقل من البيانات لتوقع المستقبل.',
    // Reports
    reportsTitle: 'تقرير PDF',
    generateReport: 'إنشاء التقرير',
    downloadReport: 'تحميل التقرير',
    openReport: 'فتح التقرير',
    reportGenerating: 'جاري إنشاء التقرير...',
    // History
    historyTitle: 'سجل التحليل',
    historyEmpty: 'لا يوجد سجل تحليل بعد. ارفع ملفاً للبدء!',
    historyFile: 'اسم الملف',
    historyDate: 'التاريخ',
    historyRows: 'الصفوف',
    historyCols: 'الأعمدة',
    historyRevenue: 'الإيرادات',
    // Cleaning
    cleaningTitle: 'تنظيف البيانات',
    cleaningDone: 'تم تنظيف البيانات بنجاح',
    // Detected Columns
    detectedColumns: 'الأعمدة المكتشفة',
    dateColumn: 'عمود التاريخ',
    salesColumn: 'عمود المبيعات',
    productColumn: 'عمود المنتج',
    quantityColumn: 'عمود الكمية',
    categoryColumn: 'عمود الفئة',
    priceColumn: 'عمود السعر',
    notDetected: 'غير مكتشف',
    // Settings
    settingsTitle: 'الإعدادات',
    language: 'اللغة',
    apiKey: 'مفتاح Groq API',
    apiKeySaved: 'تم حفظ المفتاح',
    save: 'حفظ',
    // General
    loading: 'جاري التحميل...',
    offlineMode: 'وضع عدم الاتصال',
    error: 'خطأ',
    success: 'نجاح',
    noData: 'غير متوفر',
  }
};

let currentLang = localStorage.getItem('datalens_lang') || 'en';

function t(key) {
  return translations[currentLang]?.[key] || translations['en']?.[key] || key;
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('datalens_lang', lang);
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang;
  updateAllTranslations();
}

function updateAllTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });
}
