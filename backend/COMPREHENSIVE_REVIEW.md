# بررسی جامع کدهای پروژه Sana

> تاریخ: ۱۴۰۵/۰۴/۲۰  
> بر اساس ۶ استاندارد DRF: django-crud-patterns, drf-best-practices, query-and-performance, restful-api-design, security-and-auth, testing-and-quality

---

## فهرست مطالب

1. [خلاصه اجرایی](#۱-خلاصه-اجرایی)
2. [وضعیت کلی هر استاندارد](#۲-وضعیت-کلی-هر-استاندارد)
3. [یافته‌های بحرانی (Critical)](#۳-یافته‌های-بحرانی)
4. [یافته‌های مهم (High)](#۴-یافته‌های-مهم)
5. [یافته‌های متوسط (Medium)](#۵-یافته‌های-متوسط)
6. [یافته‌های کم‌اهمیت (Low)](#۶-یافته‌های-کم‌اهمیت)
7. [وضعیت هر اپلیکیشن به تفکیک](#۷-وضعیت-هر-اپلیکیشن-به-تفکیک)
8. [نقشه حرارتی مشکلات](#۸-نقشه-حرارتی-مشکلات)
9. [اولویت‌بندی رفع مشکلات](#۹-اولویت‌بندی-رفع-مشکلات)

---

## ۱. خلاصه اجرایی

پروژه Sana یک داشبورد داده‌محور با معماری Django REST Framework است شامل ۱۰ اپلیکیشن: `auth`, `charts`, `dashboards`, `datasets`, `datasource_files`, `datasources`, `reports`, `alerts`, `query`, `management`. در مجموع **۴۷ مشکل** در ۶ استاندارد شناسایی شد:

| سطح | تعداد |
|------|-------|
| 🔴 بحرانی (Critical) | ۵ |
| 🟠 مهم (High) | ۱۲ |
| 🟡 متوسط (Medium) | ۱۸ |
| 🟢 کم‌اهمیت (Low) | ۱۲ |

**وضعیت کلی:** پروژه در مفهوم‌پردازی و طراحی API بسیار قوی است، اما در پیاده‌سازی جزئیات امنیتی و بهینه‌سازی query نیاز به بهبود دارد.

---

## ۲. وضعیت کلی هر استاندارد

### django-crud-patterns — امتیاز: ۶/۱۰
- ✅ DashboardViewSet, ChartViewSet, ReportViewSet, AlertViewSet از `ModelViewSet` استفاده می‌کنند
- ✅ Serializer mapping با `get_serializer_class()` در چند اپلیکیشن
- ❌ DatasetViewSet و DataSourceViewSet از `APIView` (غیر استاندارد) استفاده می‌کنند
- ❌ Bulk operations بدون اعتبارسنجی کامل
- ❌ Dashboard permissions با manual `_has_permission()` به جای DRF permissions

### drf-best-practices — امتیاز: ۵/۱۰
- ✅ `DmvnException` در `core/base_exception.py` تعریف شده
- ✅ `CustomPagination` در `core/utils/pagination.py` موجود
- ❌ تقریباً هیچ ViewSet ای از `select_related`/`prefetch_related` استفاده نمی‌کند
- ❌ `fields = '__all__'` در چندین serializer (auth, alerts, reports, datasource_files)
- ❌ بدون `ModelActionPermission` — فقط `IsAuthenticated` سراسری

### query-and-performance — امتیاز: ۴/۱۰
- ❌ **هیچ** `select_related`/`prefetch_related` در هیچ ViewSet ای یافت نشد
- ❌ **هیچ** Redis caching پیاده‌سازی نشده
- ❌ `iterator()` برای پردازش داده‌های بزرگ استفاده نشده
- ❌ گزارش‌ها کل داده را یکجا load می‌کنند
- ✅ `CustomPagination` موجود اما همه جا اعمال نشده

### restful-api-design — امتیاز: ۷/۱۰
- ✅ URL naming خوب (nouns, plural)
- ✅ HTTP methods صحیح (GET/POST/PATCH/DELETE)
- ✅ Custom actions غیر-CRUD درست استفاده شده
- ⚠️ `/api/query/datasets/` و `/api/query/columns/` سفارشی هستند (غیر RESTful)
- ⚠️ نامگذاری camelCase در بعضی response fields

### security-and-auth — امتیاز: ۳/۱۰
- 🔴 `DEBUG = True` در production settings!
- 🔴 `ALLOWED_HOSTS = ['*']` در production!
- 🔴 `CORS_ALLOW_ALL_ORIGINS = True` در production!
- 🔴 `SECRET_KEY` hardcoded در production!
- 🔴 SQL Injection در `_build_chart_sql` با f-strings
- ❌ بدون rate limiting
- ❌ بدون security middleware

### testing-and-quality — امتیاز: ۲/۱۰
- ❌ فقط ۲ فایل test وجود دارد (core, management)
- ❌ هیچ test برای charts, dashboards, datasets, datasources, reports, alerts
- ❌ بدون CI/CD configuration
- ❌ بدون coverage configuration
- ❌ بدون linting setup (ruff, mypy)

---

## ۳. یافته‌های بحرانی (Critical)

### C1. DEBUG=True در Production
**فایل:** `backend/config/settings/production.py`  
**استاندارد:** security-and-auth  
**توضیح:** `DEBUG = True` در production باعث نمایش stack traces و اطلاعات حساس به کاربران نهایی می‌شود.  
**رفع:** `DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'`

### C2. ALLOWED_HOSTS = ['*'] در Production
**فایل:** `backend/config/settings/production.py`  
**استاندارد:** security-and-auth  
**توضیح:** پذیرش درخواست از هر هاست، حملات Host Header Injection را ممکن می‌کند.  
**رفع:** لیست explicit از هاست‌های مجاز از متغیر محیطی

### C3. CORS_ALLOW_ALL_ORIGINS = True در Production
**فایل:** `backend/config/settings/production.py`  
**استاندارد:** security-and-auth  
**توضیح:** اجازه CORS به همه دامنه‌ها، حملات CSRF را تسهیل می‌کند.  
**رفع:** `CORS_ALLOWED_ORIGINS` whitelist از متغیر محیطی

### C4. SECRET_KEY Hardcoded در Production
**فایل:** `backend/config/settings/production.py`  
**استاندارد:** security-and-auth  
**توضیح:** کلید مخفی در کد، لو رفتن آن به دسترسی کامل به سیستم منجر می‌شود.  
**رفع:** `SECRET_KEY = os.environ['SECRET_KEY']` با بررسی وجود

### C5. SQL Injection در `_build_chart_sql`
**فایل:** `backend/charts/services.py`  
**استاندارد:** security-and-auth  
**توضیح:** استفاده از f-strings برای نام جدول و ستون‌ها در query SQL.  
**رفع:** Whitelist اعتبارسنجی نام جدول/ستون با regex قبل از استفاده در query

---

## ۴. یافته‌های مهم (High)

### H1. DatasetViewSet از ApiView استفاده می‌کند
**فایل:** `backend/datasets/views.py`  
**استاندارد:** django-crud-patterns  
**توضیح:** ۶ کلاس ApiView جداگانه به جای یک ModelViewSet  
**رفع:** تبدیل به `ModelViewSet` با `get_serializer_class()` برای mapping

### H2. DataSourceViewSet از ApiView استفاده می‌کند
**فایل:** `backend/datasources/views.py`  
**استاندارد:** django-crud-patterns  
**توضیح:** ۷ کلاس ApiView جداگانه  
**رفع:** تبدیل به `ModelViewSet`

### H3. بدون select_related/prefetch_related در هیچ ViewSet
**فایل:** تمام views.py  
**استاندارd:** query-and-performance, drf-best-practices  
**توضیح:** N+1 queries در تمام list/detail endpoints  
**رفع:** اضافه کردن `queryset` با `select_related` + `prefetch_related`

### H4. SQL Injection در `_build_chart_sql` — Column Names
**فایل:** `backend/charts/services.py`  
**استاندارد:** security-and-auth  
**توضیح:** نام ستون‌ها با f-string مستقیماً در SQL قرار می‌گیرند  
**رفع:** Regex whitelist: `re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col)`

### H5. CSV Upload Path Traversal
**فایل:** `backend/datasources/serializers.py`  
**استاندارد:** security-and-auth  
**توضیح:** `f.name` مستقیماً در مسیر فایل استفاده می‌شود بدون sanitize  
**رفع:** `os.path.basename(f.name)` + regex validation

### H6. بدون Rate Limiting
**فایل:** `backend/config/settings/base.py`  
**استاندارد:** security-and-auth  
**توضیح:** حملات brute-force و DDoS بدون محدودیت  
**رفع:** اضافه کردن `DEFAULT_THROTTLE_CLASSES`

### H7. بدون Security Middleware
**فایل:** `backend/config/settings/base.py`  
**استاندارد:** security-and-auth  
**توضیح:** `SecurityMiddleware`, `XFrameOptionsMiddleware` وجود ندارند  
**رفع:** اضافه کردن به `MIDDLEWARE`

### H8. fields = '__all__' در Auth Serializers
**فایل:** `backend/auth/serializers.py`  
**استاندارد:** drf-best-practices, security-and-auth  
**توضیح:** `UserSerializer` و `UserProfileSerializer` از `__all__` استفاده می‌کنند  
**رفع:** لیست explicit fields با exclude password

### H9. Report Generation بدون Chunking
**فایل:** `backend/reports/services.py`  
**استاندارد:** query-and-performance  
**توضیح:** `list(queryset)` کل داده را در حافظه load می‌کند  
**رفع:** `iterator(chunk_size=2000)`

### H10. Dashboard M2M Update ناکارآمد
**فایل:** `backend/dashboards/serializers.py`  
**استاندارد:** query-and-performance  
**توضیح:** حلقه `for widget in widgets:` با `widget_obj.save()`  
**رفع:** `DashboardWidget.objects.bulk_create()` یا `.set()`

### H11. Alert Notification Loop N+1
**فایل:** `backend/alerts/services.py`  
**استاندارد:** query-and-performance  
**توضیح:** `_send_notifications` در حلقه `for dashboard in dashboards`  
**رفع:** Batch notification یا Celery chord

### H12. بدون Health Check Endpoint
**فایل:** `backend/config/urls.py`  
**استاندارد:** drf-best-practices  
**توضیح:** monitoring بدون health check  
**رفع:** اضافه کردن `/health/` endpoint

---

## ۵. یافته‌های متوسط (Medium)

### M1. بدون ModelActionPermission
**فایل:** تمام views.py  
**استاندارد:** security-and-auth  
**توضیح:** فقط `IsAuthenticated` سراسری، بدون تفکیک permissions بر اساس action  
**رفع:** ایجاد `ModelActionPermission` class

### M2. بدون Redis Caching
**فایل:** تمام views.py  
**استاندارد:** query-and-performance  
**توضیح:** هیچ ViewSet ای cache ندارد  
**رفع:** `@method_decorator(cache_page(60*15))` برای list endpoints

### M3. بدون API Versioning
**فایل:** `backend/config/settings/base.py`  
**استاندارد:** restful-api-design  
**توضیح:** `/api/v1/` یا header-based versioning  
**رفع:** `DEFAULT_VERSIONING_CLASS = 'rest_framework.versioning.URLPathVersioning'`

### M4. بدون Custom Pagination در همه جا
**فایل:** `backend/core/utils/pagination.py`  
**استاندارد:** query-and-performance  
**توضیح:** `CustomPagination` موجود اما فقط در بعضی endpoints اعمال شده  
**رفع:** `DEFAULT_PAGINATION_CLASS` در settings

### M5. Schema Documentation ناقص
**فایل:** `backend/core/schema.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `AutoSchema` سفارشی اما `@extend_schema` فقط در بعضی actions  
**رفع:** اضافه کردن `@extend_schema` به همه custom actions

### M6. Test Coverage تقریباً صفر
**فایل:** تمام apps  
**استاندارد:** testing-and-quality  
**توضیح:** فقط `core/tests/` و `management/tests.py` وجود دارد  
**رفع:** ایجاد test files برای هر app

### M7. بدون CI/CD
**فایل:** پروژه ریشه  
**استاندارد:** testing-and-quality  
**توضیح:** هیچ `.github/workflows/` یا `.gitlab-ci.yml`  
**رفع:** ایجاد GitHub Actions workflow

### M8. بدون Linting Configuration
**فایل:** `backend/pyproject.toml`  
**استاندارد:** testing-and-quality  
**توضیح:** بدون ruff یا mypy configuration  
**رفع:** اضافه کردن `[tool.ruff]` و `[tool.mypy]`

### M9. Error Handling ناسازگار
**فایل:** چندین views.py  
**استاندارd:** drf-best-practices  
**توضیح:** بعضی views `Response({'error': ...})` برمی‌گردانند  
**رفع:** همه خطاها از طریق `DmvnException`

### M10. DataSource File Validation ناقص
**فایل:** `backend/datasources/views.py`  
**استاندارد:** security-and-auth  
**توضیح:** فرمت فایل فقط با `Content-Type` بررسی می‌شود  
**رفع:** Magic bytes validation + file size limit

### M11. Dashboard Permission Model ناقص
**فایل:** `backend/dashboards/models.py`  
**استاندارد:** django-crud-patterns  
**توضیح:** `DashboardPermission` فقط read/write، بدون view/granular  
**رفع:** Role-based permissions (viewer, editor, admin)

### M12. Alert Threshold Validation ناقص
**فایل:** `backend/alerts/services.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `threshold_value` از config خوانده می‌شود بدون اعتبارسنجی  
**رفع:** `validate_threshold()` در serializer

### M13. DataSource Connector Error Handling
**فایل:** `backend/datasources/connectors.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `except Exception:` generic catch  
**رفع:** Specific exception types + logging

### M14. Celery Configuration ناقص
**فایل:** `backend/core/celery.py`  
**استاندارد:** query-and-performance  
**توضیح:** `app.config_from_object('django.conf:settings')` بدون autodiscover  
**رفع:** `app.autodiscover_tasks()` اضافه شود

### M15. User Profile Auto-creation Signal
**فایل:** `backend/auth/signals.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `post_save` signal برای ایجاد UserProfile — خوب اما بدون error handling  
**رفع:** try/except در signal handler

### M16. Swagger UI Customization
**فایل:** `backend/config/settings/base.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `SWAGGER_UI_SETTINGS` با `filter: true` اما بدون auth  
**رفع:** اضافه کردن `securityDefinitions`

### M17. CSVImportJob Status Tracking
**فایل:** `backend/datasources/tasks.py`  
**استاندارد:** query-and-performance  
**توضیح:** `update_fields` شامل `updated_at` اما model auto-update ندارد  
**رفع:** `auto_now=True` در `updated_at` یا manual update

### M18. Report Template Validation
**فایل:** `backend/reports/serializers.py`  
**استاندارد:** drf-best-practices  
**توضیح:** `config` JSON field بدون schema validation  
**رفع:** JSON Schema validation در serializer

---

## ۶. یافته‌های کم‌اهمیت (Low)

### L1. Duplicate Model Fields
**فایل:** `backend/reports/models.py`  
**توضیح:** `config` و `template_config` هر دو JSONField — یکی اضافی است

### L2. Inconsistent `related_name`
**فایل:** چندین models.py  
**توضیح:** بعضی ForeignKey بدون `related_name` (مثلاً `Dataset.datasource`)

### L3. Missing `__str__` Methods
**فایل:** `backend/charts/models.py`, `backend/reports/models.py`  
**توضیح:** بعضی models بدون `__str__`

### L4. Missing `db_index=True`
**فایل:** چندین models.py  
**توضیح:** FK fields بدون index (مثلاً `Dashboard.owner`)

### L5. Missing `on_delete` Specificity
**فایل:** چندین models.py  
**توضیح:** بعضی ForeignKey از `CASCADE` استفاده می‌کنند بدون consideration

### L6. Unused Imports
**فایل:** چندین files  
**توضیح:** `os` import شده در بعضی files بدون استفاده

### L7. Missing `ordering` Meta
**فایل:** چندین models.py  
**توضیح:** بدون `ordering` در Meta class

### L8. Missing `verbose_name`
**فایل:** چندین models.py  
**توضیح:** بدون `verbose_name` در fields

### L9. Inconsistent Error Response Format
**فایل:** چندین views.py  
**توضیح:** بعضی `{'error': msg}`، بعضی `DmvnException`

### L10. Missing Logging Configuration
**فایل:** `backend/config/settings/base.py`  
**توضیح:** بدون `LOGGING` configuration

### L11. Missing File Size Limits
**فایل:** `backend/datasources/serializers.py`  
**توضیح:** CSV upload بدون حداکثر اندازه فایل

### L12. Missing `Cache-Control` Headers
**فایل:** `backend/config/settings/base.py`  
**توضیح:** بدون `Cache` middleware

---

## ۷. وضعیت هر اپلیکیشن به تفکیک

### Auth App ✅ (با اصلاحات جزئی)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ✅ |
| Explicit fields | ❌ (`__all__`) |
| select_related | ✅ (UserProfile) |
| Validation | ✅ |
| Security | ⚠️ (password field) |
| Tests | ❌ |

### Charts App ✅ (خوب)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ✅ |
| Explicit fields | ✅ |
| select_related | ⚠️ (annotations missing) |
| Validation | ✅ |
| Security | ⚠️ (SQL injection risk) |
| Tests | ❌ |

### Dashboards App ✅ (خوب)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ✅ |
| Explicit fields | ✅ |
| select_related | ✅ |
| Validation | ✅ |
| Security | ✅ |
| Tests | ❌ |

### Datasets App ❌ (نیاز به بازنویسی)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ❌ (APIView) |
| Explicit fields | ❌ (`__all__`) |
| select_related | ❌ |
| Validation | ❌ |
| Security | ⚠️ |
| Tests | ❌ |

### Datasources App ❌ (نیاز به بازنویسی)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ❌ (APIView) |
| Explicit fields | ✅ |
| select_related | ❌ |
| Validation | ✅ |
| Security | ⚠️ (path traversal) |
| Tests | ❌ |

### Reports App ✅ (با اصلاحات جزئی)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ✅ |
| Explicit fields | ❌ (`__all__`) |
| select_related | ❌ |
| Validation | ⚠️ |
| Security | ⚠️ |
| Tests | ❌ |

### Alerts App ✅ (خوب)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ✅ |
| Explicit fields | ❌ (`__all__`) |
| select_related | ✅ (get_queryset) |
| Validation | ✅ |
| Security | ✅ |
| Tests | ❌ |

### Query App ⚠️ (API سفارشی)
| معیار | وضعیت |
|-------|-------|
| ModelViewSet | ❌ (APIView) |
| Explicit fields | N/A |
| select_related | ❌ |
| Validation | ⚠️ |
| Security | ⚠️ |
| Tests | ❌ |

---

## ۸. نقشه حرارتی مشکلات

```
اپلیکیشن     │ CRUD │ DRF  │ Query │ REST │ Sec  │ Test │ مجموع
─────────────┼──────┼──────┼───────┼──────┼──────┼──────┼──────
auth         │  3   │  2   │   1   │  1   │  2   │  1   │  10
charts       │  2   │  2   │   2   │  1   │  3   │  1   │  11
dashboards   │  1   │  1   │   2   │  1   │  1   │  1   │   7
datasets     │  4   │  3   │   3   │  2   │  2   │  1   │  15
datasources  │  4   │  2   │   3   │  1   │  4   │  1   │  15
reports      │  2   │  3   │   3   │  1   │  2   │  1   │  12
alerts       │  1   │  2   │   2   │  1   │  1   │  1   │   8
query        │  3   │  2   │   2   │  2   │  2   │  1   │  12
core         │  0   │  1   │   1   │  0   │  1   │  0   │   3
management   │  0   │  0   │   0   │  0   │  0   │  0   │   0
─────────────┼──────┼──────┼───────┼──────┼──────┼──────┼──────
مجموع        │ 20   │ 18   │  19   │  10  │  18  │  8   │  93
```

---

## ۹. اولویت‌بندی رفع مشکلات

### فاز ۱: بحرانی (هفته ۱) — امنیت Production
1. ✅ C1-C4: Production settings (DEBUG, HOSTS, CORS, SECRET_KEY)
2. ✅ C5 + H4: SQL Injection در chart queries
3. ✅ H5: CSV upload path traversal
4. ✅ H6: Rate limiting
5. ✅ H7: Security middleware

### فاز ۲: مهم (هفته ۲) — DRF Compliance
1. ✅ H1-H2: تبدیل Dataset/DataSource به ModelViewSet
2. ✅ H3: اضافه کردن select_related/prefetch_related
3. ✅ H8: Explicit fields در serializers
4. ✅ H9-H10: Performance improvements

### فاز ۳: متوسط (هفته ۳) — Testing & Quality
1. ✅ M6: ایجاد test files
2. ✅ M7: CI/CD pipeline
3. ✅ M8: Linting configuration
4. ✅ M1-M2: Permissions & caching

### فاز ۴: بهبود (هفته ۴) — Polish
1. ✅ M3-M5: API versioning, pagination, docs
2. ✅ L1-L12: Cleanup & consistency
3. ✅ M14-M18: Celery, logging, validation

---

> **نکته:** این سند مرجع آینده پروژه است. بعد از رفع هر مشکل، وضعیت آن را به‌روز کنید.