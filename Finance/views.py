from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.utils import timezone
from django.views.generic import View
from django.contrib.auth import authenticate, login
from Finance import settings
from Finance.pdf_extract import extract, extract_image, extract_zip, extract_image_zip
from Finance.models import ReceiptData, Items, Customer, Uploads, Company, Logs
from Finance.forms import UploadForm
from Finance.render import Render
import pdfkit, datetime, os
from zipfile import ZipFile
from django.core.files.base import ContentFile
from django.contrib import messages
from background_task import background
from Finance import pdf_extract
from django.core.files import File
from tika import parser

def home(request):
    continuousUpload()
    items1 = Items.objects.all()
    receiptFlag = False
    itemsales = {}
    piechart1 = {}

    if request.user.is_authenticated:
        curuser=request.user
        currentcompany=curuser.company_name
        total_sales=0.0
        total_item_sales=0.0
        salesincard=0.0
        salesincheque=0.0

        #print("Current Company "+str(currentcompany))
        receipts=ReceiptData.objects.filter(company_name=currentcompany.company_name)
        if receipts.exists():
            for rec in receipts:
                total_sales=total_sales+float(rec.amount)
                print("Mode : "+str(rec.mode))
                if str(rec.mode) == 'cheque':
                    salesincheque=salesincheque+float(rec.amount)
                else:
                    salesincard=salesincard+float(rec.amount)

            percentcard=salesincard*100/total_sales
            percentcheque=salesincheque*100/total_sales
            print(percentcard)
            print(percentcheque)
            piechart1['card']=percentcard
            piechart1['cheque']=percentcheque
            receiptFlag=True

        for it in items1:
            total_item_sales=total_item_sales+float(it.total)
            if it.item_name in itemsales.keys():
                itemsales[it.item_name]=itemsales[it.item_name]+float(it.total)
            else:
                itemsales[it.item_name]=float(it.total)

    context={
        'piechart1':piechart1,
        'receiptFlag':receiptFlag,
    }

    for x in items1:
        print(x.item_name)

    return render(request, 'index.html',context)

@login_required()
def uploadView(request):


    form = UploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        f = open("templates\\error.csv", 'a')
        myfile = File(f)
        upload = form.save(commit=False)
        var = request.FILES['document'].name
        if var:
            filename = var
            test = 0
            if filename.endswith('.jpg'):
                print('File is a jpg')
                upload.save()
                con, test = extract_image(filename,request)
            elif filename.endswith('.pdf'):
                print('File is a pdf')
                upload.save()
                con, test = extract(filename,request)

            elif filename.endswith('.zip'):
                print('File is a zip')
                with ZipFile(upload.document) as zip_file:
                    names = zip_file.namelist()
                    for n in names:
                        with zip_file.open(n) as myfi:
                            up = Uploads()
                            up.description = n
                            up.document.save(n, ContentFile(myfi.read()))
                            # fyl = up.document
                            if n.endswith('.pdf'):
                                con, test = extract_zip(n,request)
                            elif n.endswith('.jpg'):
                                con, test = extract_image_zip(n,request)
                            else:
                                print('File is NOT in correct format')
                                form = UploadForm()
                                return render(request, 'upload.html', {'form': form})
                                raise form.ValidationError(
                                    "File is not in format. Please upload only jpg,pdf,zip files")
                            if test == 1:
                                myfile.write(str(n) + "," + str(con['report']) + "\n")
                                messages.error(request, str(n) + " has missing fields: " + str(con['report']))
                                log = Logs()
                                log.original_filename = n
                                log.timestamp = datetime.datetime.now()
                                log.status = False
                                log.save()
                                return redirect(home)

            else:
                print('File is NOT in correct format')
                form = UploadForm()
                return render(request, 'upload.html', {'form': form})
                raise form.ValidationError("File is not in format. Please upload only jpg,pdf,zip files")

            if test == 1:
                myfile.write(str(filename) + "," + str(con['report']) + "\n")
                messages.error(request, str(filename)+" has missing fields: "+str(con['report']))
                log = Logs()
                log.original_filename = filename
                log.timestamp = datetime.datetime.now()
                log.status = False
                log.save()
                return redirect(home)

        path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
        now = datetime.datetime.now()
        receipt_list = ReceiptData.objects.filter(mailed_status=False)

        # error_report = []
        # err_flag = 0
        # log = []
        for receipt in receipt_list:
            item = Items.objects.filter(invoice_no=receipt.invoice_no).filter(status=False)
            context = {
                'receipt': receipt,
                'item': item,
                'today': now.strftime("%d-%m-%Y"),
                # 'company': company
            }
            template = get_template('pdf.html')
            html = template.render(context)
            options = {
                'page-size': 'Letter',
                'encoding': "UTF-8",
            }
            filename = receipt.invoice_no
            file_path = os.path.join("pdf\%s.pdf" % filename)
            pdf = pdfkit.from_string(html, file_path, options, configuration=config)
            recipients = []
            for user in Customer.objects.filter(customer_id=receipt.customer_id.customer_id):
                recipients.append(user.customer_email)

            email = EmailMessage(subject='Finance Receipt', body='PFA finance receipt', from_email=settings.EMAIL_HOST_USER,to=recipients)
            email.attach_file(file_path)
            email.send()
            receipt.mailed_status = True
            for i in item:
                i.status = True
                i.save()
            receipt.save()
            # log_entry = []
            # log_entry.append(receipt.original_filename)
            # log_entry.append(receipt.invoice_no)
            # log_entry.append(datetime.datetime.now())
            # log.append(log_entry)
            log = Logs()
            log.original_filename = receipt.original_filename
            log.invoice_no = receipt.invoice_no
            log.timestamp = datetime.datetime.now()
            log.status = True
            log.save()
        messages.success(request, 'Email(s) sent successfully!')
        return redirect(home)
    form = UploadForm()
    return render(request, 'upload.html', {'form': form})

def loginview(request):
    global user
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                raw = parser.from_file(r"C:\Users\91996\PycharmProjects\Confidential101\templates\2.pdf")
                print(raw)
                return redirect(request, 'index.html')
            else:
                return render(request, 'registration/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'registration/login.html', {'error_message': 'Invalid login'})
    raw = parser.from_file(r"C:\Users\91996\PycharmProjects\Confidential101\templates\2.pdf")
    print(raw)
    return redirect(request, 'index.html')

#login_required()
#@background(schedule=0)
def continuousUpload():
    while os.listdir('templates/Upload'):
        for filename in os.listdir('templates/Upload'):
            if filename.endswith(".zip"):
                with ZipFile(os.path.join('templates/Upload', filename), 'r') as zip:
                    zip.extractall(os.path.join('templates/Upload'))
                os.remove(os.path.join('templates/Upload', filename))
                continue;
            elif filename.endswith(".jpg"):
                pdf_extract.extract_image_file(filename)
            elif filename.endswith(".pdf"):
                pdf_extract.extract_file(filename)
            else:
                print("File" + filename + "skipped because it doesn't confirm to file standards")
            path_wkthmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
            now = datetime.datetime.now()
            receipt_list = ReceiptData.objects.filter(mailed_status=False)
            for receipt in receipt_list:
                item = Items.objects.filter(invoice_no=receipt.invoice_no)
                context = {
                    'receipt': receipt,
                    'item': item,
                    'today': now.strftime("%d-%m-%Y"),
                }
                template = get_template('pdf.html')
                html = template.render(context)
                options = {
                    'page-size': 'Letter',
                    'encoding': "UTF-8",
                }
                filen = receipt.invoice_no
                file_path = os.path.join("pdf\%s.pdf" % filen)
                pdf = pdfkit.from_string(html, file_path, options, configuration=config)
                recipients = []
                for user in Customer.objects.filter(customer_id=receipt.customer_id.customer_id):
                    recipients.append(user.customer_email)

                email = EmailMessage(subject='Finance Receipt', body='PFA finance receipt',
                                     from_email=settings.EMAIL_HOST_USER, to=recipients)
                email.attach_file(file_path)
                email.send()
                os.remove(file_path)
                os.remove(os.path.join('templates/Upload', filename))
                receipt.mailed_status = True
                receipt.save()
                #print("done nannnnnan")
            log = Logs()
            log.original_filename = filename
            log.invoice_no = receipt.invoice_no
            log.timestamp = datetime.datetime.now()
            log.status = True
            log.save()
    return redirect('home')

def log_view(request):
    log = Logs.objects.all()
    return render(request, 'log.html', {'log': log})
