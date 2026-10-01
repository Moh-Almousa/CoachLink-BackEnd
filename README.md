# CoachLink Backend

الـ Backend الخاص بمنصة **CoachLink**، وهي منصة لربط المدربين الرياضيين باللاعبين وإدارة البرامج التدريبية والخطط الغذائية والاشتراكات ومتابعة تقدم اللاعبين، بالإضافة إلى الإشعارات والمحادثات الفورية.

تم تطوير الـ Backend باستخدام **Python, Django, وDjango REST Framework**، مع استخدام **PostgreSQL** كقاعدة بيانات، وتقسيم النظام إلى تطبيقات مستقلة حسب الوظيفة، مما يساعد على تنظيم الكود وتسهيل تطوير وصيانة المشروع.

المشروع مجهّز بالكامل للعمل عبر **Docker**: بيئة تطوير تعمل بأمر واحد (Django + PostgreSQL + Redis + Celery + Celery Beat).

---

## 🚀 الميزات الرئيسية

### 🔐 المصادقة والصلاحيات

يدعم النظام عدة آليات للمصادقة وإدارة صلاحيات المستخدمين:

* تسجيل المستخدمين وتسجيل الدخول.
* المصادقة باستخدام **JWT Access & Refresh Tokens**.
* التحقق من البريد الإلكتروني باستخدام **OTP**.
* استعادة كلمة المرور.
* تسجيل الدخول باستخدام حساب Google.
* نظام أدوار للمستخدمين:

  * Admin
  * Coach
  * Player
* نظام Permissions للتحكم بالوصول إلى الـ APIs.
* نظام للتحقق من حسابات المدربين واعتمادهم من قبل الإدارة.

---

## 👨‍🏫 إدارة المدربين

يوفر النظام مجموعة من الوظائف الخاصة بالمدربين، منها:

* إنشاء وإدارة ملف المدرب.
* رفع شهادة المدرب.
* مراجعة الشهادة من قبل Admin.
* قبول أو رفض شهادة المدرب.
* تحديد تخصص المدرب ومعلوماته المهنية.
* إنشاء وإدارة Subscription Packages.
* إدارة اللاعبين المرتبطين بالمدرب.

---

## 🏋️ البرامج التدريبية

يمكن للمدرب إنشاء برنامج تدريبي مخصص للاعب وإدارته.

هيكل البرنامج:

```text
Program
 └── Week
      └── Day
           └── Exercise
```

يدعم النظام:

* إنشاء البرامج التدريبية.
* تعديل البرامج الموجودة.
* إضافة وحذف الأسابيع.
* إدارة أيام التدريب.
* إضافة وتعديل التمارين.
* ربط التمارين بمصدر خارجي للبيانات.
* تسجيل أداء اللاعب أثناء التمرين.

---

## 🥗 الخطط الغذائية

يوفر النظام وظائف لإدارة الخطط الغذائية الخاصة باللاعبين، ومنها:

* إنشاء الخطط الغذائية.
* إدارة الوجبات.
* البحث عن معلومات الأطعمة من خلال External Nutrition API.
* تسجيل الوجبات التي يتناولها اللاعب.
* متابعة النشاط الغذائي للاعب.

---

## 💳 الاشتراكات والمدفوعات

يستخدم CoachLink خدمة **Stripe** لمعالجة المدفوعات والاشتراكات.

تدفق عملية الدفع:

```text
Player
   ↓
اختيار Subscription Package
   ↓
Stripe Checkout
   ↓
إتمام عملية الدفع
   ↓
Stripe Webhook
   ↓
تفعيل Subscription
   ↓
حساب أرباح المنصة والمدرب
```

يتم تفعيل الاشتراك وحساب الأرباح بعد استقبال حدث الدفع المناسب من **Stripe Webhook**.

---

## 📊 تسجيل ومتابعة تقدم اللاعبين

يحتوي النظام على مجموعة من الـ Logs لمتابعة نشاط اللاعب وتقدمه، ومنها:

* Workout Logs
* Workout Set Logs
* Nutrition Logs
* Body Measurements
* Physical Health Data

ويمكن من خلالها تسجيل ومتابعة البيانات المتعلقة بالتمارين والتغذية والقياسات الجسدية.

---

## 🔔 الإشعارات

يدعم النظام إرسال إشعارات مرتبطة بالأحداث المهمة داخل المنصة، مثل:

* وصول رسالة جديدة.
* إنشاء برنامج تدريبي جديد.
* تفويت تمرين.
* تفويت وجبة.
* قبول شهادة المدرب.
* رفض شهادة المدرب.
* قرب انتهاء الاشتراك.
* بعض الأحداث الإدارية.

---

## ⏰ المهام المجدولة (Celery Beat)

يتم تنفيذ المهام الدورية تلقائياً باستخدام **Celery Beat**، الذي يرسل كل مهمة في موعدها عبر Redis إلى **Celery Worker** لتنفيذها في الخلفية:

| المهمة | التوقيت | الوظيفة |
| --- | --- | --- |
| `send_expiry_reminders_task` | يومياً الساعة 9:00 صباحاً | تذكير اللاعبين الذين ينتهي اشتراكهم خلال 3 أيام (إشعار + بريد إلكتروني) |
| `expire_subscriptions_task` | كل ساعة | تحويل الاشتراكات المنتهية من `active` إلى `finish` |

---

## 💬 المحادثات الفورية

يستخدم CoachLink تقنية **Django Channels وWebSockets** لتوفير محادثات فورية بين المستخدمين.

التدفق الأساسي:

```text
Client
   ↓
WebSocket Connection (ws://.../ws/chat/<id>/?token=JWT)
   ↓
Daphne + Django Channels
   ↓
Redis Channel Layer
   ↓
Chat Consumer
   ↓
Conversation
```

يتم حفظ الرسائل عبر REST API، ثم تُبث فوراً لطرفي المحادثة عبر **Redis Channel Layer**، مما يسمح بتشغيل أكثر من نسخة من السيرفر.

---

# 🏗️ بنية المشروع

تم تقسيم المشروع إلى عدة Django Applications، بحيث تكون كل Application مسؤولة عن جزء محدد من النظام:

```text
CoachLink-BackEnd/
│
├── CoachLink/              # إعدادات ومكونات مشروع Django الرئيسي
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
│
├── users/                  # المستخدمون والمصادقة والصلاحيات والملفات الشخصية
│
├── programs/               # البرامج التدريبية والتمارين
│
├── nutritions/             # الخطط الغذائية والوجبات
│
├── subscriptions/          # الاشتراكات والباقات والمدفوعات
│
├── logs/                   # سجلات التمارين والتغذية والصحة
│
├── notifications/          # نظام الإشعارات
│
├── chats/                  # المحادثات الفورية وWebSockets
│
├── Dockerfile              # بناء صورة الـ Backend
├── docker-compose.yml      # بيئة التطوير
├── .dockerignore
├── .env.example            # نموذج متغيرات البيئة
├── manage.py
├── requirements.txt
└── .gitignore
```

---

# 🛠️ التقنيات المستخدمة

| التقنية               | الاستخدام                    |
| --------------------- | ---------------------------- |
| Python                | لغة البرمجة الأساسية         |
| Django                | إطار عمل الـ Backend         |
| Django REST Framework | بناء REST APIs               |
| PostgreSQL            | قاعدة البيانات               |
| Simple JWT            | المصادقة باستخدام JWT        |
| Django Channels       | دعم الاتصال الفوري           |
| WebSockets            | المحادثات الفورية            |
| Daphne (ASGI)         | سيرفر HTTP وWebSocket        |
| Redis                 | Celery Broker وChannel Layer |
| Celery                | تنفيذ المهام في الخلفية      |
| Celery Beat           | جدولة المهام الدورية         |
| Stripe                | معالجة المدفوعات             |
| Google Authentication | تسجيل الدخول باستخدام Google |
| Docker                | تشغيل المشروع داخل Containers |
| Docker Compose        | إدارة جميع الخدمات بأمر واحد |
| Git                   | Version Control              |
| GitHub                | استضافة وإدارة الكود         |
| Swagger / OpenAPI     | توثيق واختبار الـ APIs       |

---

# 🔐 آلية المصادقة

يدعم النظام المصادقة المحلية والمصادقة باستخدام Google.

### تسجيل الدخول المحلي

```text
Register
   ↓
Email OTP Verification
   ↓
Login
   ↓
Access Token + Refresh Token
```

### تسجيل الدخول باستخدام Google

```text
Google
   ↓
Google Access Token
   ↓
CoachLink Backend
   ↓
التحقق من بيانات المستخدم
   ↓
إنشاء / جلب المستخدم
   ↓
إصدار JWT Tokens
```

---

# 🔌 REST API

تم بناء الـ Backend باستخدام **Django REST Framework** وفق أسلوب REST API.

تم تقسيم الـ APIs حسب الوظيفة والمسؤولية، مع فصل:

```text
Models
   ↓
Serializers
   ↓
Views
   ↓
URLs
   ↓
Permissions
```

ومن أهم أجزاء النظام:

```text
Authentication
Users & Profiles
Programs
Nutrition
Subscriptions
Logs
Notifications
Chats
```

---

# 📚 توثيق الـ API

يستخدم المشروع **Swagger / OpenAPI** لتوثيق الـ APIs.

يساعد التوثيق على عرض:

* الـ Endpoints المتوفرة.
* HTTP Methods.
* Request Parameters.
* Request Body.
* Response Structure.
* Authentication.
* HTTP Status Codes.

بعد تشغيل المشروع يمكن فتح التوثيق من:

```text
http://localhost:8000/api/docs/     # Swagger UI
http://localhost:8000/api/schema/   # OpenAPI Schema
```

---

# ⚙️ تشغيل المشروع

## 1. تحميل المشروع

```bash
git clone https://github.com/Moh-Almousa/CoachLink-BackEnd.git
cd CoachLink-BackEnd
```

## 2. إعداد Environment Variables

يحتوي المشروع على ملف **`.env.example`** كنموذج لجميع المتغيرات المطلوبة. انسخه إلى `.env` ثم عبّئ القيم الحقيقية:

```bash
cp .env.example .env        # Linux / macOS
copy .env.example .env      # Windows
```

| المجموعة | المتغيرات |
| --- | --- |
| Django | `SECRET_KEY` |
| قاعدة البيانات | `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| Redis | `CELERY_BROKER_URL`, `CHANNEL_REDIS_URL` |
| Stripe | `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `success_url`, `cancel_url` |
| البريد الإلكتروني | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` |
| APIs خارجية | `EXERCISEDB_RAPIDAPI_KEY`, `EXERCISEDB_RAPIDAPI_HOST`, `EDAMAM_APP_ID`, `EDAMAM_APP_KEY` |

> ملف `.env` يحتوي على بيانات سرية، لذلك هو مستثنى من Git ومن صورة Docker، ويبقى `.env.example` فقط في المستودع.

## 3. التشغيل باستخدام Docker (الطريقة المقترحة)

المتطلبات: **Docker Desktop** فقط، بدون الحاجة لتثبيت Python أو PostgreSQL أو Redis على الجهاز.

```bash
docker compose up -d --build
```

يقوم هذا الأمر بتشغيل جميع الخدمات:

| الخدمة | الوظيفة | الوصول من الجهاز |
| --- | --- | --- |
| `web` | Django (runserver مع Daphne، يدعم WebSocket) ويطبق الـ migrations تلقائياً | `http://localhost:8000` |
| `db` | PostgreSQL 17 | `localhost:5433` |
| `redis` | Celery Broker وChannel Layer | داخلي فقط |
| `celery` | تنفيذ المهام في الخلفية | داخلي فقط |
| `celery-beat` | جدولة المهام الدورية | داخلي فقط |

يتم ربط مجلد المشروع بالـ Container، لذلك أي تعديل على الكود يظهر مباشرة بدون إعادة البناء.

أوامر مفيدة:

```bash
docker compose ps                                        # حالة الخدمات
docker compose logs -f web                               # متابعة الـ logs
docker compose exec web python manage.py createsuperuser # إنشاء حساب Admin
docker compose exec web python manage.py makemigrations  # أي أمر Django
docker compose restart celery celery-beat                # بعد تعديل المهام
docker compose up -d --build                             # بعد تعديل requirements.txt أو Dockerfile
docker compose down                                      # إيقاف الخدمات (البيانات تبقى)
```

## 4. التشغيل بدون Docker

يتطلب وجود **PostgreSQL** و**Redis** على الجهاز، وضبط `DATABASE_URL` و`CELERY_BROKER_URL` و`CHANNEL_REDIS_URL` في `.env` على `localhost`.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # Linux / macOS

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

وفي نوافذ Terminal منفصلة:

```bash
celery -A CoachLink worker -l info          # على Windows أضف: --pool=solo
celery -A CoachLink beat -l info
```

## 5. اختبار Stripe Webhook محلياً

```bash
stripe listen --forward-to localhost:8000/api/subscriptions/webhook/
```

وضع قيمة الـ Signing Secret الناتجة في `STRIPE_WEBHOOK_SECRET`.

---

# 🗄️ قاعدة البيانات

يستخدم المشروع **PostgreSQL** لإدارة وتخزين بيانات المنصة.

تتضمن قاعدة البيانات كيانات مرتبطة بمختلف أجزاء النظام، مثل:

```text
Users
Coach Profiles
Player Profiles
Programs
Weeks
Days
Exercises
Nutrition Plans
Subscriptions
Payments
Workout Logs
Nutrition Logs
Notifications
Chats
```

وتتم إدارة البيانات من خلال **Django ORM** مع استخدام العلاقات بين الـ Models وتنفيذ عمليات الاستعلام والتحديث من خلال Django.

---

# 🎯 هدف المشروع

يهدف CoachLink إلى توفير Backend متكامل لمنصة تدريب رياضي تجمع بين المدربين واللاعبين وتوفر الأدوات اللازمة لإدارة عملية التدريب والمتابعة.

يركز المشروع على:

* بناء REST APIs منظمة.
* Authentication وAuthorization.
* إدارة المستخدمين والأدوار.
* إدارة البرامج التدريبية.
* إدارة الخطط الغذائية.
* الاشتراكات والمدفوعات.
* التكامل مع External APIs.
* Real-Time Communication.
* Background Tasks والمهام المجدولة.
* استخدام PostgreSQL لتخزين البيانات.
* تنظيم المشروع إلى Django Applications مستقلة.
* Containerization باستخدام Docker.

---

# 👨‍💻 المطور

**Moh-Almousa**

Software Engineering Student
Backend Developer

### التخصص

```text
Python
Django
Django REST Framework
REST APIs
Django ORM
PostgreSQL
JWT Authentication
WebSockets
Celery & Redis
Docker & Docker Compose
Git & GitHub
Backend Architecture
```

---

## 📌 المشروع

**CoachLink — Fitness Coaching Platform**

مشروع Backend تم تطويره باستخدام Django وDjango REST Framework لتطبيق مفاهيم Backend Development وبناء نظام متكامل يتضمن Authentication وAuthorization وإدارة البيانات والتكامل مع الخدمات الخارجية والمدفوعات والاتصال الفوري، مع تشغيله بالكامل عبر Docker.
