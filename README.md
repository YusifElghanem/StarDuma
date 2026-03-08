# StarDima Kodi Addon (stardima-zk.cartoon.com.im)

إضافة Kodi للموقع:
- `https://stardima-zk.cartoon.com.im/`

## الميزات الحالية
- سحب قائمة المسلسلات من الصفحة الرئيسية
- فتح صفحة المسلسل واستخراج أول رابط تشغيل
- سحب الحلقات من صفحة التشغيل/السلايدر
- إصلاح روابط `undefined` عبر إعادة بناء الرابط باستخدام `slug` الصحيح
- دعم فك `redirect` المشفر Base64
- إرسال `Referer` و `User-Agent` أثناء التشغيل لتقليل مشاكل 403
- بدون أي تبعيات خارجية (استخدام `urllib` المدمج)

## الهيكل
- `addon.xml`: تعريف الإضافة
- `default.py`: نقطة الدخول
- `resources/lib/client.py`: عميل HTTP مبني على `urllib`
- `resources/lib/scraper.py`: منطق السحب والاستخراج عبر Regex
- `resources/lib/router.py`: التنقل داخل Kodi

## ملاحظات
- إذا لم يظهر محتوى، ستظهر رسالة تنبيه داخل Kodi بدل قائمة فارغة.
- إذا غيّر الموقع بنية HTML، ستحتاج Regex للتحديث.
