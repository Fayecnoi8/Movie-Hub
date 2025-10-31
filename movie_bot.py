# =============================================================================
#    *** بوت Movie Byte - الإصدار 2.2 (احترافي) ***
#
#  (جديد) يجلب البوستر العمودي (w500) بدلاً من الأفقي.
#  (جديد) يجلب "منصات المشاهدة" (Watch Providers)
#  (جديد) الرسالة "ذكية": تخفي الأسطر إذا كانت البيانات (مثل الملخص) غير موجودة.
#  (جديد) تذييل مخصص (@F_Aflam).
# =============================================================================

import requests
import os
import sys
import datetime
import locale
import random

# --- [1] الإعدادات والمفاتيح السرية (3 مفاتيح مطلوبة) ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
    TMDB_API_KEY = os.environ['TMDB_API_KEY']
    
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    print("!!! هل تذكرت إضافة (BOT_TOKEN, CHANNEL_USERNAME, TMDB_API_KEY)؟")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
TMDB_API_URL = "https://api.themoviedb.org/3"
# (v2.2) تم التغيير إلى البوستر العمودي (w500) بناءً على طلبك
POSTER_IMAGE_URL = "https://image.tmdb.org/t/p/w500" 
API_KEY_PARAM = {'api_key': TMDB_API_KEY, 'language': 'ar-SA'} 

# (إعداد لغة عربية للتاريخ)
try:
    locale.setlocale(locale.LC_TIME, 'ar_SA.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'ar_EG.UTF-8')
    except locale.Error:
        print("... تحذير: لم يتم العثور على اللغة العربية (ar_SA/ar_EG)، سيتم استخدام التاريخ الافتراضي.")


# --- [2] الدوال المساعدة (إرسال الرسائل - آمنة) ---
# ... (الدوال post_photo_to_telegram و post_text_to_telegram لم تتغير) ...

def post_photo_to_telegram(image_url, text_caption):
    """(آمن) إرسال صورة + نص (مع خدعة الرفع)"""
    print(f"... جاري إرسال (التقرير المصور) إلى {CHANNEL_USERNAME} ...")
    response = None 
    try:
        print(f"   ... (1/2) جاري تحميل الصورة من: {image_url}")
        image_response = requests.get(image_url, timeout=30)
        image_response.raise_for_status()
        image_data = image_response.content
        
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': text_caption, 'parse_mode': 'HTML'}
        content_type = 'image/png' if '.png' in image_url else 'image/jpeg'
        files = {'photo': ('movie_poster', image_data, content_type)}
        
        print("   ... (2/2) جاري رفع الصورة إلى تيليجرام ...")
        response = requests.post(url, data=payload, files=files, timeout=60)
        response.raise_for_status()
        print(">>> تم إرسال (التقرير المصور) بنجاح!")
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إرسال (التقرير المصور): {e} - {error_message}")
        print("... فشل إرسال الصورة، جاري الإرسال كنص احتياطي...")
        post_text_to_telegram(text_caption)

def post_text_to_telegram(text_content):
    """(آمن) إرسال نص فقط"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'HTML', 'disable_web_page_preview': True }
    response = None 
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        print(">>> تم إرسال (التقرير النصي) بنجاح!")
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إرسال (التقرير النصي): {e} - {error_message}")

# --- [3] دوال جلب البيانات وتنسيقها (TMDB v2.2) ---

def get_full_media_details(media_id, media_type='movie'):
    """
    (v2.2) يجلب كل تفاصيل الفيلم/المسلسل المطلوبة (4 طلبات API)
    """
    print(f"... جاري جلب التفاصيل الكاملة لـ {media_type} ID: {media_id}")
    try:
        # 1. التفاصيل الأساسية (المدة، الملخص، التقييم)
        response_details = requests.get(f"{TMDB_API_URL}/{media_type}/{media_id}", params=API_KEY_PARAM, timeout=10)
        response_details.raise_for_status()
        details = response_details.json()

        # 2. طاقم العمل (الممثلين)
        response_credits = requests.get(f"{TMDB_API_URL}/{media_type}/{media_id}/credits", params=API_KEY_PARAM, timeout=10)
        response_credits.raise_for_status()
        credits = response_credits.json()
        
        # 3. التريلر (المقطع الدعائي)
        params_videos = {**API_KEY_PARAM, 'language': 'ar-SA,en-US,null'} 
        response_videos = requests.get(f"{TMDB_API_URL}/{media_type}/{media_id}/videos", params=params_videos, timeout=10)
        response_videos.raise_for_status()
        videos = response_videos.json()
        
        # 4. (جديد) منصات المشاهدة
        response_providers = requests.get(f"{TMDB_API_URL}/{media_type}/{media_id}/watch/providers", params=API_KEY_PARAM, timeout=10)
        response_providers.raise_for_status()
        providers = response_providers.json()

        print(">>> تم جلب التفاصيل الكاملة (4 طلبات) بنجاح.")
        return details, credits, videos, providers
        
    except Exception as e:
        print(f"!!! فشل جلب التفاصيل الكاملة: {e}")
        return None, None, None, None

def format_telegram_post(details, credits, videos, providers, post_title):
    """
    (v2.2) ينسق كل البيانات في رسالة تيليجرام "ذكية" واحترافية
    """
    
    # --- استخراج البيانات ---
    media_type = 'movie' if details.get('title') else 'tv'
    title = details.get('title') or details.get('name', 'N/A')
    year = (details.get('release_date') or details.get('first_air_date', 'N/A')).split('-')[0]
    rating_raw = details.get('vote_average', 0)
    rating = f"{rating_raw:.1f} / 10" if rating_raw > 0 else None

    if media_type == 'movie':
        minutes = details.get('runtime', 0)
        duration = f"{minutes // 60}س {minutes % 60}د" if minutes > 0 else None
    else:
        seasons = details.get('number_of_seasons', 0)
        duration = f"{seasons} مواسم" if seasons > 0 else None

    summary = details.get('overview') # سيتم التحقق منه لاحقاً
        
    cast = [actor['name'] for actor in credits.get('cast', [])[:4]]
    cast_str = ", ".join(cast) if cast else None
    
    trailer_key = next((v['key'] for v in videos.get('results', []) if v['site'] == 'YouTube' and v['type'] == 'Trailer'), None)
    trailer_url = f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None
    
    # (v2.2) البحث عن منصات (الأولوية للعراق ثم أمريكا)
    watch_results = providers.get('results', {})
    watch_providers = watch_results.get('IQ', {}).get('flatrate', []) or watch_results.get('US', {}).get('flatrate', [])
    provider_names = [p['provider_name'] for p in watch_providers]
    
    # (v2.2) استخدام البوستر العمودي (w500)
    poster_path = details.get('poster_path')
    image_url = f"{POSTER_IMAGE_URL}{poster_path}" if poster_path else None
    
    # --- (v2.2) بناء الرسالة "الذكية" ---
    post_parts = []
    
    post_parts.append(f"<b>{post_title}</b>")
    post_parts.append(f"<b>{title} ({year})</b>")
    post_parts.append("=======================")

    # (ذكاء: التحقق قبل الإضافة)
    if rating: post_parts.append(f"⭐️ <b>التقييم:</b> {rating}")
    if duration: post_parts.append(f"⏱ <b>المدة:</b> {duration}")
    if cast_str: post_parts.append(f"🎭 <b>بطولة:</b> {cast_str}")

    # إضافة سطر فاصل إذا كانت هناك أي تفاصيل
    if rating or duration or cast_str:
        post_parts.append("") # سطر فارغ
    
    if summary: 
        post_parts.append(f"📝 <b>الملخص:</b>\n<i>{summary[:400]}...</i>" if len(summary) > 400 else f"📝 <b>الملخص:</b>\n<i>{summary}</i>")
        post_parts.append("") # سطر فارغ

    if provider_names:
        post_parts.append(f"📺 <b>متوفر للمشاهدة على:</b> {', '.join(provider_names)}")

    if trailer_url:
        post_parts.append(f"🍿 <a href='{trailer_url}'><b>شاهد المقطع الدعائي (Trailer)</b></a>")
        
    # (v2.2) التذييل المخصص
    post_parts.append("\n---\n<i>*تابعنا للمزيد من @F_Aflam*</i>")
    
    post_caption = "\n".join(post_parts)
    
    return image_url, post_caption

# --- [4] تعريف المهام (الخطة v2.0) ---

def run_job(endpoint, params, post_title, media_type='movie', pick_random=False):
    """(v2.2) دالة عامة لتشغيل أي مهمة (محدثة لـ 4 تفاصيل)"""
    print(f"--- بدء مهمة [{post_title}] ---")
    response = None
    try:
        base_params = {**API_KEY_PARAM}
        full_params = {**base_params, **params}
        
        response = requests.get(f"{TMDB_API_URL}/{endpoint}", params=full_params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('results'):
            print("!!! لا توجد نتائج من API.")
            return

        if pick_random:
            media_to_post = random.choice(data['results'])
        else:
            media_to_post = data['results'][0] 

        media_id = media_to_post.get('id')
        
        if not media_id:
            print("!!! النتيجة المختارة لا تحتوي على ID.")
            return
            
        # (v2.2) جلب كل التفاصيل (4 متغيرات)
        details, credits, videos, providers = get_full_media_details(media_id, media_type)
        
        if not details:
            print("!!! فشل جلب التفاصيل الكاملة، إلغاء المهمة.")
            return
            
        # (v2.2) إرسال كل التفاصيل (4 متغيرات)
        image_url, post_caption = format_telegram_post(details, credits, videos, providers, post_title)
        
        if image_url:
            post_photo_to_telegram(image_url, post_caption)
        else:
            print(f"!!! لا يوجد بوستر لـ {details.get('title')}. إرسال كنص فقط.")
            post_text_to_telegram(post_caption)
            
    except Exception as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من API')
        print(f"!!! فشلت مهمة ({post_title}): {e} - {error_message}")
        post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب [{post_title}]. يرجى المراجعة.")


# --- [5] التشغيل الرئيسي (الذكي v2.1) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v2.2 - بوت Movie Byte - احترافي)...")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    current_hour_utc = now.hour
    current_day_of_week = now.weekday() 
    
    print(f"الوقت الحالي (UTC): {now.strftime('%A, %H:%M')}")

    is_manual_run = os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
    manual_task = os.environ.get('MANUAL_TASK_INPUT', 'auto') 
    
    job_to_run = None
    
    # --- تحديد المهمة ---
    
    # (الخطوة 1: التحقق من الاختيار اليدوي أولاً)
    if is_manual_run and manual_task != 'auto':
        print(f">>> (تشغيل يدوي للاختبار) - تم اختيار المهمة: [{manual_task}]")
        if manual_task == 'daily_movie':
            job_to_run = lambda: run_job("movie/top_rated", {'sort_by': 'vote_average.desc', 'vote_count.gte': 3000}, "🎬 فيلم اليوم (اختبار يدوي)", "movie")
        elif manual_task == 'random_movie':
            random_page = random.randint(1, 5) 
            job_to_run = lambda: run_job("discover/movie", {'sort_by': 'popularity.desc', 'page': random_page}, "🎲 اختيار الظهيرة (اختبار يدوي)", "movie", pick_random=True)
        elif manual_task == 'weekly_series':
            job_to_run = lambda: run_job("trending/tv/week", {}, "📺 مسلسل الأسبوع (اختبار يدوي)", "tv")
        elif manual_task == 'weekend_movie':
            job_to_run = lambda: run_job("trending/movie/day", {}, "🍿 فيلم سهرة (اختيار يدوي)", "movie")
    
    # (الخطوة 2: إذا لم يكن تشغيلاً يدوياً، أو كان الاختيار 'auto'، استخدم الجدول الزمني)
    if job_to_run is None:
        print(">>> (تشغيل مجدول أو تلقائي) - جاري فحص الجدول الزمني...")
        
        # 1. هل الوقت 6:00 UTC (9 صباحاً بغداد)؟ -> "فيلم اليوم" (الأعلى تقييماً)
        if current_hour_utc == 6:
            print(">>> (الوقت: 6:00 UTC) - تم تحديد [فيلم اليوم].")
            job_to_run = lambda: run_job("movie/top_rated", {'sort_by': 'vote_average.desc', 'vote_count.gte': 3000}, "🎬 فيلم اليوم (الأعلى تقييماً)", "movie")

        # 2. هل الوقت 12:00 UTC (3 عصراً بغداد)؟ -> "اختيار عشوائي"
        elif current_hour_utc == 12:
            print(">>> (الوقت: 12:00 UTC) - تم تحديد [اختيار عشوائي].")
            random_page = random.randint(1, 5) 
            job_to_run = lambda: run_job("discover/movie", {'sort_by': 'popularity.desc', 'page': random_page}, "🎲 اختيار الظهيرة (عشوائي)", "movie", pick_random=True)

        # 3. هل اليوم الأربعاء والساعة 17:00 UTC (8 مساءً بغداد)؟ -> "مسلسل الأسبوع"
        elif current_day_of_week == 2 and current_hour_utc == 17: # 2 = الأربعاء
            print(">>> (الوقت: الأربعاء 17:00 UTC) - تم تحديد [مسلسل الأسبوع].")
            job_to_run = lambda: run_job("trending/tv/week", {}, "📺 مسلسل الأسبوع (الأكثر رواجاً)", "tv")

        # 4. هل اليوم خميس أو جمعة والساعة 19:00 UTC (10 مساءً بغداد)؟ -> "فيلم السهرة"
        elif (current_day_of_week == 3 or current_day_of_week == 4) and current_hour_utc == 19:
            print(f">>> (الوقت: سهرة نهاية الأسبوع {now.strftime('%A')} 19:00 UTC) - تم تحديد [فيلم السهرة].")
            job_to_run = lambda: run_job("trending/movie/day", {}, "🍿 فيلم سهرة نهاية الأسبوع", "movie")

        # 5. أي وقت آخر
        else:
            print(f"... (الوقت: {current_hour_utc}:00 UTC) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    
    if job_to_run:
        job_to_run()
    
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

