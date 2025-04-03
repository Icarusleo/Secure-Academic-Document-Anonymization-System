from django.shortcuts import render, get_object_or_404, redirect
from . import models
from . import forms
import fitz
import textwrap
import nltk , re , spacy, string
import Crypto
import base64, io ,shutil , tempfile
import hashlib,os , random
from nltk.tokenize import sent_tokenize, word_tokenize 
from nltk import pos_tag, ne_chunk
from nltk.corpus import stopwords
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from nltk.corpus import words
from reportlab.pdfgen import canvas
from django.conf import settings
#from sentence_transformers import SentenceTransformer
from collections import Counter
from django.http import FileResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageFilter
from django.contrib import messages
from spacy.tokens import Span


print(nltk.data.path)

A4 = (595.27, 841.89)

#nltk.download('punkt_tab')
#nltk.download('maxent_ne_chunker')
#nltk.download('words')
#nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger_eng')
#nltk.download('maxent_ne_chunker_tab')
nlp = spacy.load("en_core_web_md")
#nlp = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
english_words = set(words.words())  # İngilizce kelimeler kümesi
#model = SentenceTransformer("all-MiniLM-L6-v2")  # Hafif ve etkili

SECRET_KEY = "supersecretkey123".encode('utf-8') 

def encrypt_text(text):
    key = hashlib.sha256(SECRET_KEY).digest()
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
    iv = cipher.iv
    return base64.b64encode(iv + ct_bytes).decode('utf-8')[:8]

def decrypt_text(encrypted_text):
    """ AES ile şifrelenmiş veriyi çözer. """
    key = hashlib.sha256(SECRET_KEY).digest()
    encrypted_bytes = base64.b64decode(encrypted_text)  
    iv = encrypted_bytes[:AES.block_size]  
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes[AES.block_size:]), AES.block_size)  
    return decrypted_bytes.decode('utf-8')

KEY = b'Senin32ByteUzunlugundakiAESKeyin'  
IV = b'16ByteIvBurayaa!'  

def encrypt_url(data: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    padded_data = pad(data.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_url(token: str) -> str:
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decoded = base64.urlsafe_b64decode(token)
    decrypted = unpad(cipher.decrypt(decoded), AES.block_size)
    return decrypted.decode()

KORUNAN_BOLUM = ['INTRODUCTION','METHODOLOGY', 'REFERENCES', 'RELATED WORK','DISCUSSION', 'İLGİLİ ÇALIŞMALAR', 'TEŞEKKÜR',]
name_pattern = r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b'
uni_pattern = r"\b(?:[A-Z][a-zA-Z]*(?: (?:University|Institute|College|Company|Corporation|Ltd|GmbH))|(?:University|Institute|College) of [A-Z][a-zA-Z]*)\b"
mail_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

def read_pdf(pdf_path):
    pdf = fitz.open(pdf_path)
    all_text = ""

    for page in pdf:
        all_text += page.get_text()
        #all_text += "\n\n"
        
    pdf.close()
    return all_text

def split_to_paragraph(text):
    paragraphs = re.split(r'\n(?=([IVX]+\.\s+[A-Z]))', text)

    return paragraphs 

FIELD_KEYWORDS = {
    "Artificial Intelligence & Machine Learning": [
        "deep learning", "natural language processing", "computer vision", "generative ai",
        "neural network", "transformer", "reinforcement learning"
    ],
    "Human-Computer Interaction": [
        "brain-computer interface", "user experience", "ar", "vr", "virtual reality", "augmented reality"
    ],
    "Big Data & Data Analytics": [
        "data mining", "data visualization", "hadoop", "spark", "time series", "big data"
    ],
    "Cybersecurity": [
        "encryption", "secure software", "network security", "authentication", "digital forensics"
    ],
    "Networking & Distributed Systems": [
        "5g", "cloud computing", "blockchain", "peer-to-peer", "decentralized"
    ]
}

def is_title(paragraph):
    
    if len(paragraph.split()) < 100 and any(word.isupper() for word in paragraph.split()):
        return True
    return False

def exclude_names(names):
    exclude_names = ['university','technology','information','network','science','abstractas']
    #exclude_names.append(exclude_names)
    for i in names :
        if exclude_names.__contains__(i):
            names.remove(i)
    print("buraya bak:" ,names)

def clean_text(text):
    text = text.translate(str.maketrans('', '', string.punctuation))

    text = re.sub(r'[^\w\s]', '', text)

    text = re.sub(r'\d+', '', text)
    text = text.lower()

    stop_words = set(stopwords.words('english'))

    words = text.split()
    filtered_text = [word for word in words if word not in stop_words]

    return ' '.join(filtered_text)

def will_be_anonymized(paragraph, current_section):
    if is_title(paragraph):
        return False  

    normalized_title = current_section.upper().strip().replace('.', '').replace(':', '')
    if normalized_title in KORUNAN_BOLUM:
        return False 

    if re.search(name_pattern, paragraph) or re.search(uni_pattern, paragraph) or re.search(mail_pattern, paragraph):
        return True  
    return False  

def extract_authors_info(text):
    lines = text.split('\n')
    limited_lines = []

    for line in lines:
        if "INTRODUCTION" in line.upper():  
            break
        limited_lines.append(line)
 
    #name_pattern = r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b'
    mail_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    uni_pattern = r"\b(?:[A-Z][a-zA-Z]*(?: (?:University|Institute|College|Company|Corporation|Ltd|GmbH))|(?:University|Institute|College) of [A-Z][a-zA-Z]*)\b"

    names = []
    mails = set()
    universities = set()
    
    words = word_tokenize(text)
    for word in text:
        word.lower()
     
    text_nlp = clean_text(limited_lines.__str__())
    print(lines)

    doc = nlp(text_nlp)
    
    for ent in doc.ents:
        print(ent ," : ",ent.label_)
        if ent.label_ != "DATE":
            name_parts = ent.text.split()
            if (len(name_parts)<=10):
                names.append(ent.text)
                
            #print(ent)
                    
    upload_names = str(names)
    upload_names = clean_text(upload_names)
    new_words = word_tokenize(upload_names)
    names.extend(new_words) 
    exclude_names(names)
    #name_pattern = r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+|\b[A-ZÇĞİÖŞÜ]{2,}\s[A-ZÇĞİÖŞÜ]{2,}\b)\b'
     #names# = re.findall(name_pattern, names.__str__())
    print(names)
            
    for line in lines:
        mails.update(re.findall(mail_pattern, line))
        universities.update(re.findall(uni_pattern, line))

    return {
        'names': names,
        'emails': list(mails),
        'universities': list(universities)
    }
    
def anonymize_paragraph(paragraph, authors):

    def anonymize_word(text, word):
        word_lower = word.lower()
        pattern = r'(?<![a-zA-Z])(' + re.escape(word_lower) + r')(?![a-zA-Z])'
        lower_text = text.lower()

        def replace_if_not_in_meaningful_word(match):
            start, end = match.start(), match.end()
            original_word = text[start:end]

            context_window = text[max(0, start-10):min(len(text), end+10)]
            possible_words = re.findall(r'\b\w+\b', context_window)

            for w in possible_words:
                if word_lower in w.lower() and w.lower() in english_words and w.lower() != word_lower:
                    print(f"Skipping anonymization for: {w}")
                    return original_word  

            encrypted = encrypt_text(original_word)
            return encrypted

        return re.sub(pattern, replace_if_not_in_meaningful_word, lower_text, flags=re.IGNORECASE)

    for name in authors['names']:
        paragraph = anonymize_word(paragraph, name)

    for university in authors['universities']:
        paragraph = anonymize_word(paragraph, university)

    for email in authors['emails']:
        paragraph = anonymize_word(paragraph, email)

    return paragraph
   

def anonymize_full_text(text, authors):
    sections = split_to_paragraph(text)  
    result = []

    for section in sections:
        lines = section.strip().split('\n')
        title = lines[0].strip()
        content = '\n'.join(lines[1:]).strip()

        paragraphs = re.split(r'\n\s*\n', content)
        final_paragraphs = []

        for paragraph in paragraphs:
            if will_be_anonymized(paragraph, title):  
                final_paragraphs.append(anonymize_paragraph(paragraph, authors)) 
            else:
                final_paragraphs.append(paragraph)  

        section_text = title + "\n\n" + "\n\n".join(final_paragraphs)
        result.append(section_text)

    return "\n\n".join(result)

def upload_article(request):
    article_no= 0
    
    if request.method == 'POST':
        form = forms.ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            article_no = article.article_no
            if article.email not in models.user.get_users():
                user = models.user(user_Type= 'author',email=article.email)
                user.save()
                models.logs.objects.create(article=article, action="Makale yüklendi", detail=f"E-posta: {article.email}")          
    else:
        form = forms.ArticleForm()
    
    return render(request, 'upload_article.html',{'form':form, 'article_no': article_no})

def query_article(request):
    article = None
    not_found = False
    message_sent = False
    message_form = forms.MessageForm()
    query_form = forms.ArticleQuerryForm()

    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.method == "POST":
        message_form = forms.MessageForm(request.POST)
        if message_form.is_valid():
            article_id = message_form.cleaned_data["article_id"]
            message_content = message_form.cleaned_data["message"]
            try:
                article_obj = models.article.objects.get(id=article_id)
                message = models.messages.objects.create(
                    article=article_obj,
                    email=article_obj.email,
                    content=message_content
                )
                return JsonResponse({"email": message.email, "content": message.content})
            except models.article.DoesNotExist:
                return JsonResponse({"error": "Article not found."}, status=404)
        return JsonResponse({"error": "Invalid form data."}, status=400)

    if 'query' in request.POST:
        query_form = forms.ArticleQuerryForm(request.POST)
        if query_form.is_valid():
            tracking_number = query_form.cleaned_data['tracking_number']
            email = query_form.cleaned_data['email']
            try:
                article = models.article.objects.get(article_no=tracking_number, email=email)
            except models.article.DoesNotExist:
                not_found = True

    messages_for_article = []
    if article:
        messages_for_article = models.messages.objects.filter(article=article).order_by("timestamp")

    return render(request, 'query_article.html', {
        "article": article,
        "not_found": not_found,
        "query_form": query_form,
        "message_form": message_form,
        "message_sent": message_sent,
        "messages_for_article": messages_for_article
    })
    
def example_show_pdf(request, pk=15):
    pdf_kayit = get_object_or_404(models.article, pk=pk)
    text = read_pdf(pdf_kayit.article_pdf.path)
    #anonymized_text = anonymize_full_text(text)
    #print(anonymized_text)
    
    authors_info = extract_authors_info(text)
    anonymized_text = anonymize_full_text(text, authors_info)
    
    return render(request, 'example.html', {'pdf_text': anonymized_text})

def admin_panel(request):
    all_articles = models.article.objects.all() # created_at varsa
    return render(request, 'admin_panel.html', {'articles': all_articles})


def article_detail_admin(request, pk):
    article = get_object_or_404(models.article, pk=pk)
    text = read_pdf(article.article_pdf.path)
    authors_info = extract_authors_info(text)

    form = forms.AnonSelectForm(dynamic_data=authors_info)
    reviewer_form = forms.ReviewerAssignForm()
    top_field, top_keywords = get_top_field_and_keywords(text)
    matched_reviewers = list(get_matching_reviewers_by_keywords(top_keywords))
    print(top_field, top_keywords, matched_reviewers)
    article.keywords = top_keywords
    article.save()
    
    matched_fields = [top_field ]
    matched_fields.append(top_keywords)
    suggested_reviewers = matched_reviewers

    #if not article.keywords:
    #    extracted_keywords = extract_keywords_from_pdf_text(text)
    #    article.keywords = extracted_keywords
    #    article.save()
    # HAKEM ATA
    if request.method == "POST" :
        
        if 'anonymize_btn' in request.POST:
            form = forms.AnonSelectForm(request.POST, dynamic_data=authors_info)
            if form.is_valid():
                
                selected = {
                    "names": form.cleaned_data["names"],
                    "emails": form.cleaned_data["emails"],
                    "universities": form.cleaned_data["universities"],
                }
                
                original_path = article.article_pdf.path
                output_file_name = f"{article.id}_anon.pdf"
                temp_path = os.path.join(settings.MEDIA_ROOT, "anon_pdfs", f"{article.id}_temp.pdf")
                final_path = os.path.join(settings.MEDIA_ROOT, "anon_pdfs", output_file_name)

                blur_images_in_pdf(original_path, temp_path)
                #blur_author_images(original_path, temp_path, selected)

                relative_path = anonymize_pdf_in_place(article.id,temp_path, output_file_name, selected)
                article.anonymized_pdf = relative_path
                article.save()
                models.logs.objects.create(article=article, action="Makale anonimleştirildi")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return redirect("article_detail_admin", pk=pk)
        
        elif 'assign_btn' in request.POST:
            reviewer_form = forms.ReviewerAssignForm(request.POST)
            if reviewer_form.is_valid():
                reviewer_email = reviewer_form.cleaned_data["reviewer_email"]
                models.review_assignment.objects.create(
                    article=article,
                    email=reviewer_email
                )
                models.logs.objects.create(article=article, action="Hakem atandı", detail=f"Hakem: {reviewer_email}")
                return redirect("article_detail_admin", pk=pk)
                        
    assignments = models.review_assignment.objects.filter(article=article)
    logs = article.logs_set.all().order_by("-timestamp")

    return render(request, "article_detail_admin.html", {
        "article": article,
        "form": form,
        "authors_info": authors_info,
        "reviewer_form": reviewer_form,
        "assignments": assignments,
        "logs": logs,
        "matched_fields": matched_fields,
        "suggested_reviewers": suggested_reviewers
    })
    
def save_text_as_pdf(text, file_name):
    # Dosya yolu: media/anon_pdfs/file_name
    output_dir = os.path.join(settings.MEDIA_ROOT, 'anon_pdfs')
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, file_name)
    c = canvas.Canvas(file_path, pagesize=A4)
    
    width, height = A4
    x, y = 50, height - 50  # Başlangıç konumu

    for line in text.split('\n'):
        if y < 50:
            c.showPage()  # Yeni sayfa
            y = height - 50
        c.drawString(x, y, line[:1000])  # Çok uzun satırlar için kırpma
        y -= 15  # Satır aralığı

    c.save()
    return f"/media/anon_pdfs/{file_name}" 

def anonymize_pdf_in_place(article_id,input_pdf_path, output_file_name, authors):
    doc = fitz.open(input_pdf_path)
    article_obj = models.article.objects.get(id=article_id)
    # Anonimleştirilecek kelimeleri al ve temizle
    targets = list(set(t.strip() for t in (
        authors.get('names', []) + authors.get('emails', []) + authors.get('universities', [])
    ) if t.strip()))

    print("🔍 Anonimleştirilecek hedefler:", targets)

    for page_num, page in enumerate(doc):
        print(f"\n📄 Sayfa {page_num+1}")
        page_text = page.get_text("text")  

        for target in targets:
            if len(target) < 3:  
                continue

            pattern = r'\b' + re.escape(target.lower()) + r'\b'
            matches = list(re.finditer(pattern, page_text.lower()))

            print(f"  🔎 '{target}' için {len(matches)} eşleşme bulundu.")

            for match in matches:
                start, end = match.start(), match.end()
                context_window = page_text[max(0, start-100):min(len(page_text), end+100)]
                print("Context window: ", context_window)
                possible_words = re.findall(r'\b[\wçğıöşü]+\b', context_window)
                print("Possible words: ", possible_words)
                should_skip = False
                for w in possible_words:
                    if target.lower() in w.lower() and w.lower() in english_words and w.lower() != target.lower():
                        print(f"     ⏭️ Atlandı (bağlamda anlamlı kelime): {w}")
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                words = page.get_text("words")         
                text_instances = page.search_for(target)
                for inst in text_instances:
                    inst_center_y = (inst.y0 + inst.y1) / 2
                    line_words = [w[4] for w in words if abs(((w[1] + w[3]) / 2) - inst_center_y) < 4]
                    context_text = " ".join(line_words)
                    print(f"📎 Konum bağlamı (inst): {context_text}")
                    doc1 = nlp(context_text)
                    target_found_as_entity = False
                    for ent in doc1.ents:
                        if target.lower() in ent.text.lower() or authors['names'].__contains__(target.lower()):
                            print(f"     🧠 NER eşleşmesi bulundu: {ent.text} → {ent.label_}")
                            if ent.label_ in ["PERSON", "ORG", "EMAIL", "GPE"]:
                                target_found_as_entity = True
                                break
                            
                    if not target_found_as_entity:
                        if email_check(target) or authors.__contains__(target):
                            target_found_as_entity = True
                        else:
                            print(f"     ⏭️ NER bağlamı yetersiz, sansür yapılmadı: {target}")
                            break
                    #pdf_context_window = page.get_text("text", clip=inst).strip()
                    #print("pdf_context " ,pdf_context_window)
                    ## Bağlamsal yanlış eşleşmeyi atla
                    #if  pdf_context_window.lower() in english_words and pdf_context_window!=target:
                    #    print(f"     ⚠️ Skipped (Bağlam yanlış olabilir): {pdf_context_window}")
                    #    break
                    
                    page.add_redact_annot(inst, fill=(1, 0, 0))  # Üstünü beyazla kapat
                    
                    #page.draw_rect(inst, fill=(1, 1, 1), overlay=True)  
                    centered_rect = fitz.Rect(inst.x0, inst.y0, inst.x1, inst.y1)
                    font_size = inst.height * 0.7
                    test_rect = fitz.Rect(inst.x0 - 10, inst.y0 - 10, inst.x1 + 10, inst.y1 + 10)
                    page.apply_redactions()
                    models.AnonymizedItem.objects.create(
                            article=article_obj,
                            page_number=page_num,
                            rect={
                                "x0": inst.x0,
                                "y0": inst.y0,
                                "x1": inst.x1,
                                "y1": inst.y1
                            },
                            placeholder="******",
                            original_text=target
                        )
                    print(f"     ✅ **Şifrelenmiş olarak yazıldı:** {target} ")
                
       
    print("authosrrs: ",authors)
    output_dir = os.path.join(settings.MEDIA_ROOT, 'anon_pdfs')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file_name)
    doc.save(output_path)
    print("✅ PDF başarıyla kaydedildi:", output_path)
    return f"anon_pdfs/{output_file_name}"

def infer_fields_from_keywords(keywords):
    all_fields = models.Field.objects.all()
    matched_fields = set()

    for field in all_fields:
        for sub in field.subfields:
            for kw in keywords:
                if sub.lower() in kw.lower():
                    matched_fields.add(field.name)

    return list(matched_fields)


def infer_fields_by_keyword_frequency(text):
    lower_text = text.lower()
    result = {}

    for field, keywords in FIELD_KEYWORDS.items():
        keyword_counts = {}
        total = 0

        for kw in keywords:
            matches = re.findall(r'\b' + re.escape(kw.lower()) + r'\b', lower_text)
            count = len(matches)
            if count > 0:
                keyword_counts[kw] = count
                total += count

        if total > 0:
            result[field] = {
                "total": total,
                "details": keyword_counts  
            }

    sorted_result = dict(sorted(result.items(), key=lambda x: x[1]['total'], reverse=True))
    return sorted_result


def get_top_field_and_keywords(text):
    field_data = infer_fields_by_keyword_frequency(text)
    if not field_data:
        return None, []

    top_field = next(iter(field_data))  
    top_keywords = sorted(
        field_data[top_field]['details'].items(),
        key=lambda x: x[1], reverse=True
    )
    return top_field, [kw for kw, count in top_keywords]

def get_matching_reviewers_by_keywords(top_keywords):
    matching_reviewers = []

    for reviewer in models.Reviewer.objects.all():
        if any(keyword in reviewer.interested_subfields for keyword in top_keywords):
            matching_reviewers.append(reviewer)
            
    return matching_reviewers


def is_exact_match(text, start, end):
    allowed_before = set(string.punctuation + ' ')
    allowed_after = set(string.punctuation + ' ')

    before = text[start - 1] if start > 0 else ' '
    after = text[end] if end < len(text) else ' '

    return (
        (not before.isalnum() or before in allowed_before)
        and (not after.isalnum() or after in allowed_after)
    ) 
    
def is_valid_leading_char(text, start_index):
    if start_index == 0:
        return True  

    previous_char = text[start_index - 1]

    if previous_char in string.punctuation or previous_char.isspace():
        return True

    return False
           
def add_reviewers():
    all_subfields = [
        "deep learning", "natural language processing", "computer vision", "generative ai",
        "neural network", "reinforcement learning", "brain-computer interface",
        "user experience", "virtual reality", "augmented reality",
        "data mining", "data visualization", "hadoop", "spark", "time series",
        "encryption", "secure software", "network security", "authentication", "digital forensics",
        "5g", "cloud computing", "blockchain", "peer-to-peer", "decentralized"
    ]

    domains = ["gmail.com", "university.edu", "researchlab.org", "techmail.net"]

    for i in range(20):  
        name = f"reviewer{i}"
        email = f"{name}@{random.choice(domains)}"
        interested_subfields = random.sample(all_subfields, random.randint(2, 5))

        models.Reviewer.objects.create(
            email=email,
            name=name,
            interested_subfields=interested_subfields
        )
        print(f"✔️ {email} eklendi, ilgilendiği konular: {interested_subfields}")
        

def reviewer_assignments_api(request):
    email = request.GET.get("email")
    assignments = models.review_assignment.objects.filter(email=email)
    data = []

    for a in assignments:
        article_obj = a.article
        data.append({
            "article_id": article_obj.id,
            "article_name": article_obj.name,
            "article_pdf": article_obj.anonymized_pdf.url if article_obj.anonymized_pdf else article_obj.article_pdf.url,
        })

    return JsonResponse({"assignments": data})


@csrf_exempt
def submit_review(request):
    if request.method == "POST":
        article_id = request.POST.get("article_id")
        content = request.POST.get("content")

        try:
            article_obj = models.article.objects.get(id=article_id)
            models.review.objects.create(article=article_obj, content=content)
            return JsonResponse({"status": "success"})
        except models.article.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Makale bulunamadı."})

    return JsonResponse({"status": "error", "message": "Geçersiz istek."})

def reviewer_panel(request):
    return render(request, "hakem_panel.html")

def email_check(text):
    email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    print("email: ",text)
    return bool(re.fullmatch(mail_pattern, text.strip()))

def is_near_author_text(image_rect, page, author_keywords, max_distance=100):
    words = page.get_text("words")
    for word in words:
        word_text = word[4].lower()
        if any(author.lower() in word_text for author in author_keywords):
            word_rect = fitz.Rect(word[:4])
            if image_rect.intersects(word_rect) or rect_distance(image_rect, word_rect) < max_distance:
                return True
    return False

    
def rect_distance(r1, r2):
    cx1 = (r1.x0 + r1.x1) / 2
    cy1 = (r1.y0 + r1.y1) / 2
    cx2 = (r2.x0 + r2.x1) / 2
    cy2 = (r2.y0 + r2.y1) / 2
    return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

def blur_images_in_pdf(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)
    image_count = 0

    for page_num in range(len(doc)):
        page = doc[-1]
        image_list = page.get_images(full=True)

        print(f"📄 Sayfa {page_num+1} içinde {len(image_list)} resim bulundu.")

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            image = Image.open(io.BytesIO(image_bytes))
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=12))

            img_byte_arr = io.BytesIO()
            blurred_image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            doc.update_stream(xref, img_byte_arr) 
            print(f"   🖼️ Resim {img_index+1} bulanıklaştırıldı.")

            image_count += 1

    doc.save(output_pdf_path)
    print(f"\n✅ Toplam {image_count} resim bulanıklaştırıldı. Kaydedildi → {output_pdf_path}")

def reviewer_detail(request, email):
    assignments = models.review_assignment.objects.filter(email=email)
    articles = [a.article for a in assignments]
    for article in articles:
        article.encrypted_id = encrypt_url(str(article.id))
    return render(request, 'reviewer_detail.html', {
        'email': email,
        'articles': articles
    })
    
@csrf_exempt
def submit_review_form(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        content = request.POST.get('content', '').strip()

        if not content:
            return HttpResponseBadRequest("Yorum boş olamaz.")

        try:
            article_obj = get_object_or_404(models.article, id=int(article_id))

            if not article_obj.final_pdf:
                from django.core.files import File
                import shutil, os
                from django.conf import settings

                source_path = article_obj.article_pdf.path
                dest_dir = os.path.join(settings.MEDIA_ROOT, 'final_pdfs')
                os.makedirs(dest_dir, exist_ok=True)

                dest_path = os.path.join(dest_dir, f'final_{article_obj.id}.pdf')
                shutil.copy(source_path, dest_path)

                relative_path = f'final_pdfs/final_{article_obj.id}.pdf'
                article_obj.final_pdf.name = relative_path
                article_obj.save()
            add_review_to_final_pdf(article_obj.id, content)

        except Exception as e:
            return HttpResponseBadRequest(f"Hata oluştu: {e}")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return HttpResponseBadRequest("Sadece POST isteklerine izin verilir.")


def article_messages_panel(request, article_id):
    is_admin = request.GET.get("admin") == "true"       
    art = get_object_or_404(models.article, id=article_id)
    msg_list = models.messages.objects.filter(article=art).order_by("timestamp")
    return render(request, 'article_messages_panel.html', {
        'article': art,
        'messages': msg_list
    })
    
def add_review_to_final_pdf(article_id, review_text):
    try:
        article = models.article.objects.get(id=article_id)
        original_pdf_path = article.final_pdf.path  
        doc = fitz.open(original_pdf_path)

        page = doc.new_page()

        page.insert_text((50, 50), "Reviewer Comment", fontsize=16, fontname="helv", color=(0, 0, 0))

        wrapped = review_text.split('\n')
        y = 80
        for line in wrapped:
            if y > 800:  
                page = doc.new_page()
                y = 50
            page.insert_text((50, y), line, fontsize=12, fontname="helv", color=(0, 0, 0))
            y += 20

 
        doc.saveIncr()
        doc.close()

        article.status = "Article Reviewed"
        article.save()

        print("✅ Yorum orijinal PDF'e eklendi.")
        return True
    except Exception as e:
        print("❌ Hata:", e)
        return False

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        email = 'admin'
        content = request.POST.get('message_content', '').strip()

        if not email or not content:
            return redirect(request.META.get('HTTP_REFERER', '/'))

        article_obj = get_object_or_404(models.article, id=int(article_id))
        models.messages.objects.create(article=article_obj, email=email, content=content)
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')

    """
        # Makale yüklendiğinde
        Log.objects.create(article=article, action="Makale yüklendi", detail=f"E-posta: {article.email}")

        # Anonimleştirme sonrası
        Log.objects.create(article=article, action="Makale anonimleştirildi")

        # Hakem atandığında
        Log.objects.create(article=article, action="Hakem atandı", detail=f"Hakem: {reviewer_email}")

        # Hakem değerlendirme gönderdiğinde
        Log.objects.create(article=article, action="Hakem değerlendirme yükledi")
    """
def check_status(article):
    if article.status == "Atandı" :
        pdf_path = article.article_pdf.path
        review = models.review.objects.get(article=article) 
        output_path = add_review_to_pdf(pdf_path=pdf_path,review_text=review.content)
        
        
def add_review_to_pdf(article_id, pdf_path, review_text, output_path=None):
    doc = fitz.open(pdf_path)
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 800)

    wrapped_lines = textwrap.wrap(review_text, width=100)
    wrapped_text = "\n".join(wrapped_lines)

    page.insert_textbox(rect, wrapped_text, fontsize=12, fontname="helv", color=(0, 0, 0))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp_path = temp.name

    doc.save(temp_path)
    doc.close()

    os.replace(temp_path, pdf_path)


    article = models.article.objects.get(id=article_id)
    article.status = "Article Reviewed"
    article.save()

    print(f"✅ Yorum eklendi ve PDF güncellendi: {pdf_path}")
    return pdf_path

def decrypt_pdf_with_original_text(article_id, input_path, output_path):
    doc = fitz.open(input_path)
    items = models.AnonymizedItem.objects.filter(article_id=article_id)

    for item in items:
        page = doc[item.page_number]
        rect = fitz.Rect(item.rect["x0"], item.rect["y0"], item.rect["x1"], item.rect["y1"])

        # Beyaz kutu çiz
        #page.draw_rect(rect, fill=(1, 1, 1), overlay=True)
        #page.add_redact_annot(rect, fill=(1, 1, 1))
        # Yazıyı ortala
        #font_size = rect.height * 0.8
        #rect = fitz.Rect(item.rect["x0"]-15, item.rect["y0"]-15, item.rect["x1"]+15, item.rect["y1"]+15)
        #
        #page.insert_textbox(
        #    rect,
        #    item.original_text,
        #    fontname="helv",
        #    fontsize=font_size,
        #    color=(0, 0, 0),
        #    align=fitz.TEXT_ALIGN_CENTER
        #)
        #page.apply_redactions()


    doc.save(output_path)
    doc.close()
    print(f"✅ Şifreli alanlar çözüldü → {output_path}")
    return output_path

@csrf_exempt
def send_final_to_author(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        art = get_object_or_404(models.article, id=article_id)

        #input_path = art.article_pdf.path
        #output_path = input_path.replace("anon_pdfs", "final_pdfs")  # final_pdfs alt klasörü
#
        ## Şifreli alanları çöz ve geçici dosyaya yaz
        #with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        #    temp_path = tmp.name
        #decrypt_pdf_with_original_text(article_id=art.id, input_path=input_path, output_path=temp_path)
#
        ## Geçici dosyayı gerçek output path'e taşı
        #os.makedirs(os.path.dirname(output_path), exist_ok=True)
        #os.replace(temp_path, output_path)

        art.status = "Result Sent to Author"
        art.save()

        models.logs.objects.create(article=art, action="Yöneticiden yazara sonuç iletildi")

        messages.success(request, "✅ Değerlendirme başarıyla yazara iletildi.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return HttpResponseBadRequest("Geçersiz istek.")
@csrf_exempt
def cancel_article_review(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        art = get_object_or_404(models.article, id=article_id) 
        art.status = "Article Reviewed"
        art.save()  
        models.logs.objects.create(article=art, action="Yazara gönderim iptal edildi.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return HttpResponseBadRequest("Geçersiz istek.")

@csrf_exempt
def cancel_review(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        art = get_object_or_404(models.article, id=article_id) 
        art.status = "Awaiting review"
        art.save()
        models.logs.objects.create(article=art, action="Değerlendirme iptal edildi.")
        review = models.review.objects.filter(article=art)
        if review.exists():
            review.delete()
            
        try:
            path = art.anonymized_pdf.path if art.anonymized_pdf else art.article_pdf.path
            doc = fitz.open(path)

            if len(doc) > 1:
                doc.delete_page(len(doc) - 1)  
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    temp_path = tmp.name
                doc.save(temp_path)
                doc.close()
                os.replace(temp_path, path)
                print("📄 Yorum sayfası PDF'ten silindi.")
            else:
                print("❗ PDF'te silinecek ek sayfa yok.")
        except Exception as e:
            print(f"⚠️ PDF'ten yorum silme sırasında hata oluştu: {e}")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return HttpResponseBadRequest("Geçersiz istek.")

@csrf_exempt
def cancel_reviewer_assingment(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        art = get_object_or_404(models.article, id=article_id) 
        assigment = get_object_or_404(models.review_assignment, article = art)
        assigment.delete()
        art.status = "Awaiting review"
        art.save()  
        models.logs.objects.create(article=art, action="Hakem ataması İptal edildi.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return HttpResponseBadRequest("Geçersiz istek.")

def view_pdf_encrypted(request, token):
    try:
        article_id = int(decrypt_url(token))
        article = get_object_or_404(models.article, id=article_id)
        return FileResponse(article.anonymized_pdf.open(), content_type='application/pdf')
    except Exception as e:
        return HttpResponseBadRequest("PDF gösterilemedi: " + str(e))
    
@csrf_exempt
def update_uploaded_pdf(request):
    if request.method == "POST":
        article_id = request.POST.get("article_id")
        new_pdf = request.FILES.get("new_pdf")

        if not new_pdf:
            return HttpResponseBadRequest("PDF dosyası gönderilmedi.")

        try:
            article = models.article.objects.get(id=article_id)
            article.article_pdf = new_pdf
            article.save()
            messages.success(request, "PDF başarıyla güncellendi.")
            models.logs.objects.create(article=article, action="Yazar tarafından makale revize edildi.")
            article.status = "Awaiting review"
            article.save()
            
            review = models.review.objects.filter(article=article)
            if review.exists():
                review.delete()
                models.logs.objects.create(article=article, action="Yazar makaleyi revize ettiğinden değerlendirme iptal edildi.")
        except models.article.DoesNotExist:
            return HttpResponseBadRequest("Makale bulunamadı.")

        return redirect(request.META.get("HTTP_REFERER", "/"))
    return HttpResponseBadRequest("Sadece POST isteklerine izin verilir.")