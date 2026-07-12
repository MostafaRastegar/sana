# Sana BI — فهرست کامل امکانات

## 1. مدیریت منابع داده (Datasources)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **اتصال به PostgreSQL** | اتصال مستقیم به پایگاه داده PostgreSQL برای دریافت داده | `datasources/connectors.py` |
| **اتصال به MySQL** | اتصال مستقیم به پایگاه داده MySQL | `datasources/connectors.py` |
| **اتصال به SQLite** | اتصال به فایل SQLite محلی | `datasources/connectors.py` |
| **اتصال به REST API** | دریافت داده از API‌های REST خارجی با پشتیبانی از هدر و نتایج‌کی | `datasources/connectors.py` |
| **آپلود فایل CSV** | آپلود و پارس فایل CSV به صورت ناهمزمان با Celery | `datasources/views.py`, `datasources/tasks.py` |
| **import-csv** | API اختصاصی برای import فایل CSV با وضعیت Job | `datasources/views.py` (`/import-csv`, `/{pk}/import-csv`) |
| **دریافت رکوردهای منبع داده** | خواندن ردیف‌های جدول mirror شده از source | `datasources/views.py` (`/{pk}/records`) |
| **تست اتصال** | تست connectivity منبع داده | `datasources/views.py` (`/{pk}/test`) |
| **همگام‌سازی (Sync)** | pull داده از منبع خارجی به جدول محلی | `datasources/views.py` (`/{pk}/sync`), `connectors.py` (`sync_data`) |
| **تاریخچه همگام‌سازی** | لاگ موفقیت/شکست sync همراه با تعداد رکورد | `datasources/views.py` (`/{pk}/logs`) |
| **رمزنگاری تنظیمات** | ذخیره امن credentials با AES encryption | `datasources/encryption.py` |
| **Auto-create Dataset** | ایجاد خودکار Dataset پس از sync | `datasources/connectors.py` (`_auto_create_dataset`) |
| **مدیریت Job‌های CSV** | مشاهده وضعیت Job‌های آپلود CSV | `datasources/views.py` (`/{pk}/csv_jobs`) |
| **ایجاد Dataset از DataSource** | تبدیل دستی DataSource به Dataset | `datasources/views.py` (`/{pk}/create_dataset`) |

## 2. مجموعه داده‌ها (Datasets)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **CRUD Dataset** | ایجاد، خواندن، به‌روزرسانی و حذف Dataset | `datasets/views.py` |
| **ایجاد از DataSource** | ایجاد Dataset از روی DataSource موجود | `datasets/views.py` (`from_datasource`) |
| **نمایش داده‌های Dataset** | مشاهده ردیف‌های جدول با صفحه‌بندی | `datasets/views.py` (`data`) |
| **اطلاعات ستون‌ها** | نام، نوع و label ستون‌های Dataset | `datasets/models.py` (`Dataset.columns`) |
| **تعداد ردیف‌ها** | نمایش تعداد ردیف‌های Dataset | `datasets/models.py` (`Dataset.row_count`) |
| **seed_data** | ایجاد دیتاهای نمونه برای تست و دمو | `datasets/management/commands/seed_data.py` |

## 3. نمودارها (Charts)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **CRUD Chart** | ایجاد، خواندن، به‌روزرسانی و حذف نمودار | `charts/views.py` |
| **انواع نمودار** | bar, line, pie, table, kpi, area, scatter, heatmap, gauge, funnel, treemap, radar | `charts/models.py` |
| **محاسبه داده نمودار** | ساخت SQL query پویا بر اساس config نمودار | `charts/views.py` (`_build_chart_sql`) |
| **پیش‌نمایش نمودار** | محاسبه داده بدون ذخیره نمودار | `charts/views.py` (`preview`) |
| **حالت KPI** | نمایش یک مقدار تکی aggregated | `charts/views.py` (`_build_chart_sql`, is_kpi) |
| **Export به CSV** | خروجی داده‌های نمودار به فرمت CSV | `charts/views.py` (`export`) |
| **Drill-down** | جستجوی جزئیات با کلیک روی یک مقدار | `charts/views.py` (`drill_down`) |
| **Drill-down به Chart دیگر** | پرش به نمودار هدف با فیلتر مقدار انتخابی | `charts/views.py` (`drill_down`, target_chart_id) |
| **فیلترهای سراسری** | اعمال global filters روی config نمودار | `charts/views.py` (`data`, merge global_filters) |
| **انواع aggregation** | SUM, AVG, COUNT, MIN, MAX | `charts/views.py` (`_build_chart_sql`) |
| **مرتب‌سازی** | صعودی/نزولی بر اساس ستون | `charts/views.py` (`_build_chart_sql`, sort_config) |
| **محدودیت ردیف** | LIMIT در SQL | `charts/views.py` (`_build_chart_sql`, limit) |
| **فیلتر درون‌نموداری** | فیلترهای EQ, NEQ, GT, GTE, LT, LTE, CONTAINS, IN | `charts/views.py` (`_build_chart_sql`) |
| **پرس‌وجوهای ذخیره شده** | ذخیره و مدیریت queries | `charts/models.py` (`SavedQuery`), `charts/views.py` |
| **گروه‌بندی** | GROUP BY on x_axis + optional group_by column | `charts/views.py` (`_build_chart_sql`) |
| **حاشیه‌نویسی نمودار** | افزودن annotation به نمودارها | `charts/migrations/0004_chartannotation.py` |

## 4. دشبوردها (Dashboards)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **CRUD Dashboard** | ایجاد، خواندن، به‌روزرسانی و حذف دشبورد | `dashboards/views.py` |
| **مدیریت چیدمان** | ذخیره و به‌روزرسانی layout (grid positions charts) | `dashboards/views.py` (`layout`) |
| **فیلترهای سراسری** | تعریف فیلترهای全局 dashboard | `dashboards/views.py` (`filters`) |
| **Render دشبورد** | برگرداندن dashboard با داده‌های chart‌ها resolved | `dashboards/views.py` (`render`) |
| **اعمال global filters در render** | ارسال فیلترها به همه chart‌ها | `dashboards/views.py` (`render`, global_filters query param) |
| **مشارکت (Sharing)** | مدیریت دسترسی کاربران: view/edit/admin | `dashboards/views.py` (`permissions`) |
| **دشبورد عمومی** | قابلیت public کردن دشبورد بدون نیاز به login | `dashboards/models.py` (`is_public`) |
| **قالب دشبورد** | ایجاد، مدیریت و instantiate از template | `dashboards/views.py` (`DashboardTemplateViewSet`, `instantiate`) |
| **جستجوی کاربران** | جستجوی کاربران برای اشتراک‌گذاری | `dashboards/views.py` (`UserSearchView`) |
| **سلسله مراتب دسترسی** | view → edit → admin | `dashboards/views.py` (`_has_permission`) |
| **مالکیت** | owner-only operations برای delete/update | `dashboards/views.py` (`perform_update`, `perform_destroy`) |

## 5. هشدارها (Alerts)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **CRUD Alert** | ایجاد، خواندن، به‌روزرسانی و حذف هشدار | `alerts/views.py` |
| **شرط‌ها** | above, below, equals, change_percent | `alerts/services.py` (`_evaluate_condition`) |
| **Aggregation** | SUM, AVG, COUNT, MIN, MAX | `alerts/services.py` (`_build_aggregate_sql`) |
| **بازه بررسی** | hourly, daily, weekly | `alerts/models.py` (`check_interval`) |
| **فیلتر پیشرفته** | شرط‌های EQ, NEQ, GT, GTE, LT, LTE روی ستون‌ها | `alerts/services.py` (`_build_aggregate_sql`, filters) |
| **اعلان ایمیلی** | ارسال ایمیل به recipients | `alerts/services.py` (`_send_email_notification`) |
| **اعلان Webhook** | POST payload به URL خارجی | `alerts/services.py` (`_send_webhook_notification`) |
| **تاریخچه هشدار** | ثبت هر بار trigger شدن با مقدار واقعی | `alerts/views.py` (`/{pk}/history`) |
| **تغییر وضعیت فعال/غیرفعال** | toggle is_active | `alerts/views.py` (`/alerts/{id}/toggle/`) |
| **اجرای دستی** | بررسی هشدار در لحظه (check_now) | `alerts/views.py` (`/{pk}/check_now`) |
| **آمار هشدارها** | خلاصه آمار: تعداد کل، فعال، غیرفعال | `alerts/views.py` (`/alerts/stats/`) |
| **برنامه‌ریزی Celery** | اجرای دوره‌ای چک‌ها با celery beat | `alerts/tasks.py` |
| **پشتیبانی از چند کانال** | email و webhook همزمان | `alerts/services.py` (`_send_notifications`) |

## 6. گزارش‌های زمانبندی (Scheduled Reports)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **CRUD Report** | ایجاد، خواندن، به‌روزرسانی و حذف گزارش | `reports/views.py` |
| **برنامه زمانی** | cron, daily, weekly, monthly | `reports/models.py` |
| **تولید HTML** | تبدیل dashboard به HTML report | `reports/services.py` (`generate_report`) |
| **خروجی PDF** | تبدیل HTML به PDF با weasyprint | `reports/views.py` (`download`) |
| **پیش‌نمایش** | مشاهده HTML گزارش در مرورگر | `reports/views.py` (`preview`) |
| **ارسال ایمیلی خودکار** | ارسال گزارش به recipients در زمان مقرر | `reports/services.py` (`generate_and_send`) |
| **اجرای دستی** | trigger_now برای تولید و ارسال فوری | `reports/views.py` (`trigger_now`) |
| **تغییر وضعیت** | فعال/غیرفعال کردن گزارش | `reports/views.py` (`toggle`) |
| **تاریخچه تولید** | لاگ هر بار production با وضعیت موفقیت/شکست | `reports/views.py` (`history`), `reports/models.py` (`ReportHistory`) |
| **محاسبه زمان بعدی** | محاسبه خودکار next_run | `reports/services.py` (`_update_next_run`) |
| **برنامه‌ریزی Celery** | celery beat task برای تولید و ارسال | `reports/tasks.py` |

## 7. پرس‌وجو (Query)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **اجرای SQL مستقیم** | اجرای query روی Dataset‌ها | `query/views.py` |
| **مدیریت Queries ذخیره شده** | ذخیره و بازیابی queries | `query/views.py` |
| **تاریخچه queries** | مشاهده queries اجرا شده | `query/views.py` |

## 8. هسته سیستم (Core)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **احراز هویت JWT** | Simple JWT با access/refresh/verify | `config/urls.py` |
| **سیستم مجوز ModelActionPermission** | نگاشت خودکار action → permission | `core/permissions.py` |
| **صفحه‌بندی سفارشی** | CustomPagination با page_size=20 | `core/utils/pagination.py` |
| **خطای ساختاریافته DmvnException** | فرمت یکسان خطا: status_code, code, message, details | `core/base_exception.py` |
| **Exception Handler سفارشی** | تبدیل تمام خطاها به فرمت DmvnException | `core/middleware.py` |
| **Celery** | پردازش ناهمزمان (tasks alerts/reports) | `core/celery.py` |
| **Celery Beat** | زمانبندی دوره‌ای چک هشدارها و گزارش‌ها | `core/celery.py` |
| **اعتبارسنجی‌ها** | validators برای فیلدهای مختلف | `core/utils/validators.py` |
| **Schema مستندات** | تنظیمات drf-spectacular | `core/schema.py` |
| **i18n** | ترجمه فارسی/انگلیسی | `locale/fa/`, `locale/en/` |
| **CORS** | تنظیمات跨域 | `config/settings/base.py` |
| **تست E2E** | سناریوی end-to-end کامل | `core/tests/test_e2e_scenarios.py` |

## 9. تولید کد (Code Generation)

| ویژگی | توضیحات | فایل‌های مرتبط |
|-------|---------|----------------|
| **تولید TypeScript از مدل‌ها** | خودکارسازی تولید types و API client‌های TypeScript از مدل‌های Django | `management/management/commands/generate_ts.py` |

## 10. API Routes Summary

| Method | Path | App | Description |
|--------|------|-----|-------------|
| GET/POST | `/api/token/` | Auth | دریافت/رفرش JWT |
| POST | `/api/token/refresh/` | Auth | رفرش توکن |
| POST | `/api/token/verify/` | Auth | اعتبارسنجی توکن |
| GET/POST | `/api/datasources/` | Datasources | CRUD منابع داده |
| POST | `/api/datasources/import-csv/` | Datasources | آپلود CSV |
| POST | `/datasources/{id}/test/` | Datasources | تست اتصال |
| POST | `/datasources/{id}/sync/` | Datasources | همگام‌سازی |
| GET | `/datasources/{id}/logs/` | Datasources | تاریخچه sync |
| GET | `/datasources/{id}/records/` | Datasources | رکوردهای منبع |
| GET/POST | `/api/datasets/` | Datasets | CRUD مجموعه داده |
| POST | `/datasets/{id}/from_datasource/` | Datasets | ایجاد از منبع |
| GET | `/datasets/{id}/data/` | Datasets | مشاهده داده‌ها |
| GET/POST | `/api/charts/` | Charts | CRUD نمودار |
| POST | `/charts/preview/` | Charts | پیش‌نمایش داده |
| GET | `/charts/{id}/data/` | Charts | داده نمودار |
| GET | `/charts/{id}/drill_down/` | Charts | جزئیات |
| GET | `/charts/{id}/export/` | Charts | خروجی CSV |
| GET/POST | `/api/dashboards/` | Dashboards | CRUD دشبورد |
| PUT | `/dashboards/{id}/layout/` | Dashboards | به‌روزرسانی چیدمان |
| PUT | `/dashboards/{id}/filters/` | Dashboards | فیلترهای سراسری |
| GET | `/dashboards/{id}/render/` | Dashboards | Render با داده |
| GET/POST/DELETE | `/dashboards/{id}/permissions/` | Dashboards | مدیریت دسترسی |
| POST | `/dashboards/{id}/instantiate/` | Dashboards | ایجاد از قالب |
| GET/POST | `/alerts/` | Alerts | CRUD هشدار |
| GET | `/alerts/stats/` | Alerts | آمار هشدارها |
| POST | `/alerts/{id}/toggle/` | Alerts | تغییر وضعیت |
| POST | `/alerts/{id}/check_now/` | Alerts | اجرای دستی |
| GET | `/alerts/{id}/history/` | Alerts | تاریخچه |
| GET/POST | `/reports/` | Reports | CRUD گزارش |
| GET | `/reports/{id}/preview/` | Reports | پیش‌نمایش |
| GET | `/reports/{id}/download/` | Reports | دانلود PDF |
| POST | `/reports/{id}/trigger_now/` | Reports | اجرای فوری |
| POST | `/reports/{id}/toggle/` | Reports | فعال/غیرفعال |
| GET | `/reports/{id}/history/` | Reports | تاریخچه |
| GET/POST | `/api/queries/` | Query | مدیریت پرس‌وجوها |
| POST | `/api/execute/` | Query | اجرای SQL |

## 11. Middleware & Settings

| ویژگی | توضیحات |
|-------|---------|
| **SecurityMiddleware** | HSTS, XSS filter, content-type nosniff |
| **CORS** | دسترسی کنترل‌شده از frontend |
| **Celery** | RabbitMQ broker برای tasks ناهمزمان |
| **SQLite** | پایگاه داده پیش‌فرض (قابل تعویض) |
| **DRF Spectacular** | مستندات خودکار API (Swagger) |

## 12. Deployment

| ویژگی | توضیحات |
|-------|---------|
| **Dockerfile** | containerized deployment |
| **docker-compose.yml** | orchestration شامل app + celery worker + beat |
| **gunicorn.conf.py** | WSGI server configuration |
| **Development/Production/Test settings** | environment segregation |

---

> تاریخ آخرین به‌روزرسانی: 2025-07-11