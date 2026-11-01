# تشغيل مولّد اللوحة على ويندوز

## مرة واحدة
1. ثبّت **Python 3.10 أو أحدث** من python.org، وفعّل خيار **Add Python to PATH** أثناء التثبيت.
2. ثبّت **GitHub Desktop**، واستنسخ المستودع `rabeaammoura-art/-sharpseek-api`.
3. داخل المجلد `cad` اضغط مرتين على **`setup_windows.bat`** (ينزّل المكتبات، ويحتاج إنترنت).
4. ضع ملف الأسعار `filament_prices.xlsx` في `cad\config\` (لا يُرفع إلى GitHub لأن المستودع عام).

## لكل لوحة
1. انسخ `cad\plaque\example_ar.json` (أو `example_en.json`) وغيّر الاسم والوزن والطول والتاريخ والساعة والحجم.
   احفظه بترميز **UTF-8** (Notepad يحفظ كذلك افتراضياً).
2. اسحب ملف الـ json وأفلته على **`make_plaque.bat`**.
3. ستجد في `cad\out\plaque` ملف **`.3mf`** (افتحه في Bambu Studio) وصورة معاينة `.png` وملف الركاية `.stl`.

## ملاحظات
- في ملف الـ json: `"size"` هو 150 أو 200 أو 300، و`"lit": true` للنسخة المضيئة، و`"stand": "feet"` أو `"clip"` أو `"easel"`.
- ملفات الطباعة الجاهزة للأمثلة موجودة في `cad\print_files\`.

## التقطيع وحساب الوقت والكلفة على ويندوز
`bambu_slice.py` يعمل الآن على ويندوز مع Bambu Studio المثبّت (يقطّع بالـ CLI ويحسب الكلفة من ملف الأسعار).
- يبحث عن `bambu-studio.exe` تلقائياً: المتغير `BAMBU_STUDIO_DIR`، ثم PATH، ثم `C:\Program Files\Bambu Studio`، ثم السجل. ويقرأ الملفات الشخصية من `resources\profiles\BBL` داخل التثبيت.
- شغّله من جذر المشروع:
  ```
  .venv-cad\Scripts\python.exe cad\bambu_slice.py --filament "Bambu PETG Basic @BBL H2D 0.4 nozzle" cad\print_files\standard\plaque_ar_150.3mf
  ```
- للتقطيع متعدد الألوان أعد `--filament` لكل خانة، وأضف `--tower-x` و`--tower-y` و`--tower-width` لبرج التنظيف (بدونه التقدير ناقص).
- ملفات STL تُوسَّط عبر `trimesh` (لا يحتاج PrusaSlicer). النتائج تُكتب في `cad\out\bambu`.
