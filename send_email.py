from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.header import Header
import zipfile
import os

token = 'whvohbsoivtkcide'


def zip_dir(dir_path, zip_path):
    zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


def sendEmail(from_addr, to_addr, title, content, img_path = None, excel_path = None, zip_path = None):
    # 1. Create a message
    msg = MIMEMultipart()
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header(title)
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    if img_path:
        with open(img_path, 'rb') as f:
            img_data = f.read()
        att = MIMEApplication(img_data)
        att.add_header('Content-Disposition', 'attachment', filename='invoice.jpg')
        msg.attach(att)

    if excel_path:
        with open(excel_path, 'rb') as f:
            excel_data = f.read()
        att = MIMEApplication(excel_data)
        att.add_header('Content-Disposition', 'attachment', filename='info.xlsx')
        msg.attach(att)

    if zip_path:
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        att = MIMEApplication(zip_data)
        att.add_header('Content-Disposition', 'attachment', filename='invoice.zip')
        msg.attach(att)

    # 2. Create an SMTP object
    smtp = SMTP_SSL('smtp.qq.com')

    # 3. Login to the server
    smtp.login(from_addr, token)

    # 4. Send email
    smtp.sendmail(from_addr, to_addr, msg.as_string())

    # 5. Close the connection
    smtp.quit()


if __name__ == '__main__':
    zip_dir('.', './test.zip')