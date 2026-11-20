# Quiz Bot

بوت ديسكورد للأسئلة العشوائية باستخدام Python و discord.py.

## المميزات
- أسئلة عشوائية مع تصنيفات: ثقافة عامة، علوم، تاريخ، رياضة، ألعاب، جغرافيا.
- أزرار للإجابة مع مهلة 20 ثانية.
- 10 نقاط لكل إجابة صحيحة.
- لوحة ترتيب أفضل 10 لاعبين.
- عرض نقاط اللاعب.
- حفظ النتائج في SQLite حتى بعد إعادة تشغيل البوت.

## الأوامر
- /quiz سؤال عشوائي.
- /quiz category سؤال من تصنيف محدد.
- /leaderboard ترتيب اللاعبين.
- /score نقاطك.
- /help_quiz المساعدة.

## التشغيل محلياً
1. ثبّت Python 3.10 أو أحدث.
2. نفّذ: pip install -r requirements.txt
3. أنشئ متغير بيئة باسم DISCORD_TOKEN وضع فيه توكن البوت.
4. شغّل: python bot.py

لا تضع التوكن داخل ملفات المشروع أو ترفعه إلى GitHub.

## إعداد Discord
1. أنشئ تطبيقاً من https://discord.com/developers/applications
2. من تبويب Bot أنشئ Bot Token واحتفظ به سرياً.
3. من OAuth2 > URL Generator اختر scopes: bot و applications.commands.
4. امنح البوت صلاحيات Send Messages و Embed Links و Use Application Commands ثم أضفه إلى سيرفرك.

## التشغيل 24/7
ارفع المشروع إلى استضافة تدعم Background Worker مثل Railway أو Render paid worker:
- اربط مستودع GitHub.
- اختر تشغيل Worker/Background Service.
- أمر التشغيل: python bot.py
- أضف متغير البيئة DISCORD_TOKEN.
- استخدم قرصاً دائماً واحفظ قاعدة البيانات في مساره عبر DATABASE_PATH حتى لا تضيع النقاط عند إعادة النشر.

مهم: GitHub يحفظ الكود ولا يشغّل البوت. التشغيل المستمر يحتاج استضافة عاملة وخطة لا توقف الخدمة. لا توجد طريقة لضمان 24/7 على خطة مجانية قد تدخل في وضع السكون.
