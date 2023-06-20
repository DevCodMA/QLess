import random
import smtplib

def generateOTP(recpient: str) -> str:
    otp = random.randint(111111, 999999)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    uname, pswd = 'srnandanakrishna@gmail.com', 'xfelcqljswqospnx'
    server.login(uname, pswd)
        
    subject = 'OTP for verification'
    body = f"""
            <html>
                <head>
                    <style>
                        table {{
                            border: none;
                            width: 100%;
                            height: 100%;
                            background: linear-gradient(90deg, rgba(2,0,36,1) 0%, rgba(9,9,121,1) 35%, rgba(0,212,255,1) 100%);
                        }}
                        td {{
                            color: #ffffff;
                            text-shadow: 2px 2px #000000;
                            padding: 50px;
                        }}
                        td.otp {{
                            vertical-align: middle;
                            text-align: center;
                            font-size: 30px;
                            font-weight: bold;
                        }}
                        td.note {{
                            font-size: 18px;
                        }}
                    </style>
                </head>
                <body>
                    <table>
                        <tr>
                            <td class="note">We're sending you this one-time password (OTP) to verify your account with us. Please enter the OTP below to complete the verification process:</td>
                        </tr>
                        <tr>
                            <td class="otp">{otp}</td>
                        </tr>
                        <tr>
                            <td class="note">Please note that this OTP is valid only for a limited time and should not be shared with anyone. If you did not request this verification, please ignore this message and contact our support team immediately.<br/><br/>Thank you for using our services.</td>
                        </tr>
                    </table>
                </body>
            </html>
        """
    message = f'Subject: {subject}\nMIME-Version: 1.0\nContent-type: text/html\n\n{body}'
    server.sendmail(uname, recpient, message)
    server.quit()

    return str(otp)

print(generateOTP("majmals1998@gmail.com"))