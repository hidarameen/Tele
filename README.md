# صانع بوتات تيليجرام (Python / PostgreSQL / Redis)

منصة بوت تيليجرام (بدون واجهة ويب) تعمل كنظام صانع بوتات. كل مستخدم يمكنه إنشاء عدة بوتات منفصلة، وكل بوت يحتوي مهام توجيه رسائل مستقلة بنوعي التنفيذ: عبر bot token أو userbot (Telethon). النظام مبني بشكل modular مع قابلية تحمل ضغط عالٍ وتخزين مؤقت Redis وقاعدة بيانات PostgreSQL.

## المزايا
- فصل صارم للبيانات لكل مستخدم ولكل بوت ولكل مهمة
- دعم آلاف المستخدمين والبوتات
- نظام صلاحيات/ملكية واضح (المالك هو المتحكم ببوتاته)
- مهام توجيه متعددة لكل بوت (سيتم تخصيص إعداداتها لاحقاً)
- دعم userbot (Telethon) وتسجيل الدخول بالجلسة أو الهاتف
- دعم bot token (Bot API) عبر aiogram
- بدون واجهة ويب: كل التحكم عبر محادثة التيليجرام بلوحة تحكم تفاعلية
- تخزين مؤقت Redis، وقفل توزيع، وجدولة مهام

## التقنية
- Python 3.11+
- aiogram 3.x لبوتات Bot API
- Telethon لـ userbot
- PostgreSQL + SQLAlchemy 2.x + Alembic
- Redis للتخزين المؤقت والقفل
- Pydantic Settings للإعدادات
- Loguru للتسجيل

## التشغيل السريع
1. انسخ `.env.example` إلى `.env` وعدّل القيم (خاصة `BUILDER_BOT_TOKEN` و `APP_ENCRYPTION_KEY`).
2. شغّل قواعد البيانات:
```bash
docker compose up -d postgres redis
```
3. ثبت الاعتمادات:
```bash
pip install -r requirements.txt
```
4. شغّل البوت الصانع:
```bash
python -m app.main
```

## بنية المجلدات
```
app/
  bots/
    builder/        # بوت الصانع (لوحة التحكم وإدارة البوتات)
    runner/         # مدير تشغيل البوتات المصنوعة والمهام
  cache/
  db/
  services/
  utils/
  main.py
```

## ملاحظات اتصال PostgreSQL (Neon وغيرها)
- إذا ظهر الخطأ: `asyncpg.exceptions.InternalServerError: password authentication failed for user 'neondb_owner'`:
  - تأكد أن `DATABASE_URL` صحيح وأن كلمة المرور مُرمّزة URL إن كانت تحتوي رموزاً خاصة.
  - مع Neon استخدم `sslmode=require` واحفظ `options=project%3D<PROJECT_ID>` ضمن العنوان.
  - يمكنك بدلاً من `DATABASE_URL` ضبط المتغيرات: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, مع `DB_SSLMODE=require` لتجنب مشاكل ترميز العنوان.
  - يدعم النظام أيضاً متغيرات `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD/PGSSLMODE` القياسية.

سيتم لاحقاً إضافة تفاصيل إعدادات المهمة (لوحة إعدادات المهمة) حسب المواصفات التي ستزودنا بها.