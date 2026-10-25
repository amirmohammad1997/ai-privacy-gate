\# AI Privacy Gateway — Project Status



\*\*آخرین به‌روزرسانی:\*\* 2026-10-11

\*\*وضعیت:\*\* گام ۴ کامل شد ✅ — حالا گام ۵ (Prompt Guard)

\*\*مکالمه‌ی جاری:\*\* همین مکالمه



\---



\## 🎯 خلاصه‌ی پروژه



پلتفرم جهانی حریم خصوصی AI — ناشناس‌سازی PII قبل از ارسال به LLM.

پشتیبانی از \*\*۱۲ زبان\*\* با معماری چندلایه.



\*\*محیط:\*\*

\- Windows 10/11

\- Python 3.14

\- مسیر پروژه: `C:\\Users\\Lenovo\\ai-privacy-gateway`

\- venv: `.venv\\Scripts\\activate`

\- pydantic 2.12.0 (ثابت — بالاتر نروید!)

\- FastAPI + uvicorn + langdetect



\---



\## ✅ گام‌های کامل‌شده



\### گام ۱: ساختار پروژه ✅

\- `.env.example`, `.gitignore`, `README.md`, `requirements.txt`

\- `app/\_\_init\_\_.py`, `app/config.py`



\### گام ۲: سرور FastAPI ✅

\- `app/main.py` با `/`, `/health`, `/ping`



\### گام ۳: Sanitizer پایه ✅

\- `app/security/sanitizer/{models,regex\_layer,orchestrator}.py`



\### گام ۴: Sanitizer چندزبانه کامل ✅



\*\*Language Detection:\*\*

\- `app/security/sanitizer/language\_detector.py`

\- ۵ لایه heuristic: script, PII markers, special chars, common words, langdetect

\- تست: ۱۲/۱۲ زبان PASS



\*\*Layers (12 languages + universal):\*\*

\- `layers/base.py`, `layers/universal.py`

\- `layers/english.py`, `layers/persian.py`, `layers/turkish.py`

\- `layers/chinese.py`, `layers/japanese.py`, `layers/korean.py`, `layers/arabic.py`

\- `layers/spanish.py`, `layers/french.py`, `layers/german.py`

\- `layers/portuguese.py`, `layers/russian.py`



\*\*Validators:\*\*

\- `validators/universal.py` (Luhn, IBAN, IP, Email)

\- `validators/english.py` (SSN, US Phone, ZIP)

\- `validators/persian.py` (کد ملی، موبایل، پستی)

\- `validators/turkish.py` (TCKN, Phone)

\- `validators/chinese.py` (身份证, Phone)

\- `validators/japanese.py` (My Number, Phone)

\- `validators/korean.py` (RRN, Phone)

\- `validators/arabic.py` (SA/EG/UAE ID, Phone)

\- `validators/spanish.py` (DNI, NIE, Phone)

\- `validators/french.py` (INSEE, Phone)

\- `validators/german.py` (Steuer-ID, Phone)

\- `validators/portuguese.py` (CPF, CNPJ, Phone)

\- `validators/russian.py` (SNILS, INN, Phone)



\*\*API Endpoints:\*\*

\- `POST /v1/sanitize` — ناشناس‌سازی با تشخیص خودکار زبان

\- `POST /v1/restore` — بازگردانی از mapping



\*\*تست نهایی:\*\*

\- `test\_orchestrator.py` — ۱۲/۱۲ زبان PASS + Round-trip PASS



\---



\## 📋 گام بعدی — گام ۵: Prompt Guard



\*\*هدف:\*\* جلوگیری از تزریق دستور (Prompt Injection).



\*\*فایل‌های برنامه‌ریزی‌شده:\*\*

\- `app/security/prompt\_guard/normalizer.py` — نرمال‌سازی (یونیکد، homoglyph، base64)

\- `app/security/prompt\_guard/pattern\_guard.py` — regex برای حملات شناخته‌شده

\- `app/security/prompt\_guard/embedding\_guard.py` — شباهت معنایی (optional)

\- `app/security/prompt\_guard/orchestrator.py` — ادغام لایه‌ها

\- endpoint `POST /v1/check-prompt`



\---



\## 🔑 نکات مهم



\- \*\*pydantic 2.12.0\*\* (نه بالاتر — Python 3.14 wheel ندارد)

\- \*\*Command Prompt ویندوز:\*\* دستورات چندخطی کار نمی‌کنند → از فایل‌های تست استفاده کنید

\- \*\*فارسی در Command Prompt معکوس نمایش داده می‌شود\*\* — طبیعی است

\- \*\*Language Detection\*\* الان از \*\*PII markers\*\* استفاده می‌کند (قبل از langdetect)

\- \*\*سختگیری در validator\*\* برای کاهش false positive



\## 📁 ساختار کامل پروژه



## 🆕 به‌روزرسانی 2026-10-11

### نصب‌های جدید
- ✅ pydantic 2.13.5 (بالاتر از 2.12 — برای سازگاری با spaCy)
- ✅ pydantic-core 2.46.5
- ✅ spaCy 3.8.10
- ✅ en_core_web_sm (مدل NER انگلیسی)
- ✅ sentence-transformers 6.1.0

### چه چیزی حالا داریم
- Sanitizer چندزبانه: ۱۲ زبان ✅
- Prompt Guard (Pattern): ۱۷/۱۷ ✅
- NER Layer: آماده برای پیاده‌سازی
- Embedding Guard: آماده برای پیاده‌سازی

### گام بعدی
- گام ۵ج: NER Layer (spaCy)
- گام ۵ب: Embedding Guard (sentence-transformers)

## 🆕 به‌روزرسانی 2026-10-12

### تصمیم معماری جدید
- Sanitizer حالا دو حالت دارد: `mode="input"` و `mode="output"`
- **ورودی کاربر:** NER فعال (نام، مکان، سازمان شناسایی و ناشناس می‌شود)
- **خروجی LLM:** NER غیرفعال (فقط regex + secrets + entropy)
- **دلیل:** جلوگیری از false positive در پاسخ‌های عادی LLM
  (مثلاً "The capital of France is Paris" نباید ناشناس شود)

### گام‌های کامل
- ✅ گام ۵: Prompt Guard (Pattern + Embedding)
- ✅ گام ۶: Output Filter (Secrets + PII + Entropy)

### گام بعدی
- گام ۷: Chat Endpoint

## 🆕 به‌روزرسانی 2026-10-12 (بخش دوم)

### گام ۶ کامل شد ✅
- `output_filter/secrets_detector.py` — ۲۰+ الگوی کلید
- `output_filter/entropy_analyzer.py` — تشخیص رشته‌های تصادفی
- `output_filter/orchestrator.py` — ادغام + تصمیم
- تست: ۸/۸ PASS

### تصمیم معماری
- Sanitizer دو حالت دارد: `mode="input"` (با NER) و `mode="output"` (بدون NER)
- Output Filter فقط از `mode="output"` استفاده می‌کند

### گام بعدی
- گام ۷: Chat Endpoint — اتصال همه به LLM

# AI Privacy Gateway — Project Status

**آخرین به‌روزرسانی:** 2026-10-12
**وضعیت:** گام ۷ کامل شد ✅ — حالا گام ۸ (تست‌های گسترده + Docs)
**مکالمه‌ی جاری:** ادامه در همین مکالمه

---

## 🎯 خلاصه‌ی پروژه

پلتفرم جهانی حریم خصوصی AI — ناشناس‌سازی PII قبل از ارسال به LLM
با فیلتر ورودی (Prompt Guard) و فیلتر خروجی (Output Filter).

**محیط:**
- Windows 10/11
- Python 3.14.7 (در `.venv`)
- مسیر پروژه: `C:\Users\Lenovo\ai-privacy-gateway`
- pydantic **2.13.5** (بالاتر از 2.12 برای سازگاری با spaCy)
- spaCy 3.8.10 + en_core_web_sm
- sentence-transformers 6.1.0
- FastAPI + uvicorn + langdetect

**تنظیمات مهم محیطی (برای جلوگیری از OpenBLAS error):**
```python
# قبل از هر import
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


---

## 📝 دوم: به‌روزرسانی `requirements.txt`

**مسیر:** `C:\Users\Lenovo\ai-privacy-gateway\requirements.txt`

```cmd
notepad requirements.txt
## 🆕 به‌روزرسانی 2026-10-25

### ✅ Ollama با موفقیت نصب شد
- مدل: `llama3.2:1b` (1.3 GB)
- آدرس: `http://localhost:11434`
- تست تعاملی: موفق (پاسخ به سؤال)

### تنظیمات .env
- `LLM_PROVIDER=ollama`
- `LLM_BASE_URL=http://localhost:11434/v1`
- `LLM_MODEL=llama3.2:1b`
## 🆕 به‌روزرسانی 2026-10-25 (تکمیل گام ۷)

### ✅ Chat Endpoint کامل شد
- **Ollama:** راه‌اندازی شد و مدل `llama3.2:1b` نصب شد.
- **پایپ‌لاین کامل:** تست `test_chat.py` با موفقیت اجرا شد.
- **نتایج تست:**
  - پیام‌های عادی: `200 OK` (ناشناس‌سازی و پاسخ LLM با موفقیت).
  - حملات تزریقی: `400 Bad Request` (Prompt Guard مسدود کرد).
  - زمان پاسخ: ۶۰۰ تا ۱۲۰۰ میلی‌ثانیه.
- **نکته‌ی مهم:** Embedding Guard موقتاً غیرفعال است (به دلیل خطای دانلود مدل از HuggingFace). Prompt Guard با لایه‌ی Pattern (که بسیار قوی است) کار می‌کند.

### ⚠️ نکات فنی
- مدل Ollama در مسیر `C:\Users\Lenovo\.ollama` نصب شده است.
- برای فعال‌سازی مجدد Embedding Guard، باید مدل `all-MiniLM-L6-v2` را دستی دانلود کنیم (گام بعدی).

### 📋 گام بعدی
- **گام ۸:** تست‌های گسترده + مستندات.

## 🆕 به‌روزرسانی 2026-10-25 (گام ۸ کامل شد)

### ✅ تست جامع و مستندات
- **تست `test_full_pipeline.py`:** ۱۲/۱۲ سناریو با موفقیت پاس شد.
- **README.md:** راهنمای کامل نصب و استفاده نوشته شد.
- **LICENSE:** لایسنس MIT اضافه شد.

### ⚠️ نکات فنی (ویندوز)
- خطای `ConnectionResetError` در تست‌ها فقط یک هشدار ویندوز است و مشکلی ایجاد نمی‌کند.
- Embedding Guard حالا به درستی مدل را از HuggingFace لود می‌کند.