# StarDima Kodi Addon (watch.stardima)

إضافة Kodi للموقع الجديد `watch.stardima` بدون أي تبعيات خارجية.

## الميزات الحالية
- عرض قائمة المسلسلات من `/watch/tvshows/`
- عرض حلقات المسلسل
- تشغيل الحلقة عبر استخراج رابط iframe
- دعم فك `redirect` المشفر Base64
- إرسال `Referer` و `User-Agent` أثناء التشغيل لتقليل مشاكل 403
- استخدام `urllib` المدمج بدل `requests` لتجنب خطأ `ModuleNotFoundError` داخل Kodi

## الهيكل
- `addon.xml`: تعريف الإضافة
- `default.py`: نقطة الدخول
- `resources/lib/client.py`: عميل HTTP مبني على `urllib`
- `resources/lib/scraper.py`: منطق السحب والاستخراج عبر Regex
- `resources/lib/router.py`: التنقل داخل Kodi

## ملاحظات
- الإصدار الحالي يركز فقط على `watch.stardima` كما طُلِب.
- إذا غيّر الموقع بنية HTML، قد تحتاج Regex للتحديث.
