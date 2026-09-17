# CoachLink Backend

الـ Backend الخاص بمنصة **CoachLink**، وهي منصة لربط المدربين الرياضيين باللاعبين وإدارة البرامج التدريبية والخطط الغذائية والاشتراكات ومتابعة تقدم اللاعبين، بالإضافة إلى الإشعارات والمحادثات الفورية.

تم تطوير الـ Backend باستخدام **Python, Django, وDjango REST Framework**، مع استخدام **PostgreSQL** كقاعدة بيانات، وتقسيم النظام إلى تطبيقات مستقلة حسب الوظيفة، مما يساعد على تنظيم الكود وتسهيل تطوير وصيانة المشروع.

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
* بعض الأحداث الإدارية.

---

## 💬 المحادثات الفورية

يستخدم CoachLink تقنية **Django Channels وWebSockets** لتوفير محادثات فورية بين المستخدمين.

التدفق الأساسي:

```text
Client
   ↓
WebSocket Connection
   ↓
Django Channels
   ↓
Chat Consumer
   ↓
Conversation
```

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
| Celery                | تنفيذ المهام في الخلفية      |
| Stripe                | معالجة المدفوعات             |
| Google Authentication | تسجيل الدخول باستخدام Google |
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

---

# ⚙️ تشغيل المشروع

## 1. تحميل المشروع

```bash
git clone https://github.com/Moh-Almousa/CoachLink-BackEnd.git
cd CoachLink-BackEnd
```

## 2. إنشاء Virtual Environment

على Windows:

```powershell
python -m venv .venv
```

ثم:

```powershell
.venv\Scripts\activate
```

على Linux / macOS:

```bash
source .venv/bin/activate
```

## 3. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

## 4. إعداد Environment Variables

أنشئ ملف:

```text
.env
```

في مجلد المشروع، وأضف المتغيرات المطلوبة.

مثال:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_NAME=your-database-name
DATABASE_USER=your-database-user
DATABASE_PASSWORD=your-database-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

GOOGLE_CLIENT_ID=your-google-client-id
```


## 5. تشغيل Database Migrations

```bash
python manage.py migrate
```

## 6. تشغيل المشروع

```bash
python manage.py runserver
```

سيعمل الـ API بشكل افتراضي على:

```text
http://127.0.0.1:8000/
```

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
* Background Tasks.
* استخدام PostgreSQL لتخزين البيانات.
* تنظيم المشروع إلى Django Applications مستقلة.

---

# 👨‍💻 المطور

**Moh-Almousa**

Software Engineering Graduate
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
Git & GitHub
Backend Architecture
```

---

## 📌 المشروع

**CoachLink — Fitness Coaching Platform**

مشروع Backend تم تطويره باستخدام Django وDjango REST Framework لتطبيق مفاهيم Backend Development وبناء نظام متكامل يتضمن Authentication وAuthorization وإدارة البيانات والتكامل مع الخدمات الخارجية والمدفوعات والاتصال الفوري.
