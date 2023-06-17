from flask import Flask, request, render_template, jsonify, url_for
import hashlib
import sqlite3 as sql
import json
from datetime import datetime
import smtplib
import random
import base64

app = Flask(__name__)
date = datetime.now()
year = str(date.year)
month = str(date.month).zfill(2)
day = str(date.day).zfill(2)

def generateOTP(recpient: str) -> str:
    otp = random.randint(111111, 999999)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    uname, pswd = 'a74564924@gmail.com', 'nfptmuracpnggppi'
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

hash = (lambda pswd: hashlib.sha256(pswd.encode('utf-8')).hexdigest())
check = False
user = ""
first_name = ""
userData = []
genOTP = ""
uType = ""

def validate(uname, pswd, userType):
    conn = sql.connect(r"Files/cms.db")
    res = ""
    if userType == 'customer':
        res = conn.execute(f"SELECT PSWD, FNAME FROM USERS WHERE UNAME='{uname}'").fetchone()
    else:
        res = conn.execute(f"SELECT PSWD, FNAME FROM ADMIN WHERE UNAME='{uname}'").fetchone()
    if res[0] == pswd:
        return [True, res[1]]
    else:
        return [False]

@app.route('/')
def index():
    global check
    global user
    global first_name
    global uType
    try:
        data =  json.loads(request.cookies.get('cred'))
        if data != None:
            fname = data.get('fname')
            print(fname)
            uname = data.get('uname')
            signed = data.get('signed')
            userType = data.get('userType')
            uType = userType
            pswd = data.get('pswd')
            first_name = fname
            user = uname
            if signed == 'true' and validate(uname, pswd, userType)[0]:
                check = True
                print(userType)
                if userType == 'admin':
                    return render_template('admin.html', fname=fname, uname=uname)
                elif userType == 'customer':
                    return render_template('customer.html', fname=fname, uname=uname)
            else:
                return render_template('index.html')
        else:
            return render_template('index.html')
    except Exception as ex:
        return render_template('index.html')



@app.route("/home")
def home():
    if check:
        if uType == 'admin':
            return render_template("admin.html", username=user, fname=first_name)
        else:
            return render_template("customer.html", username=user, fname=first_name)
    else:
        return render_template("index.html", load=True)


# Login
@app.route('/login', methods=["POST"])
def login(): 
    global check
    global user
    global uType
    uname = request.form["uname"]
    pswd = hash(request.form["pswd"])
    signed = request.form["signed"]
    userType = request.form["userType"]
    user = uname
    uType = userType
    try:
        res = validate(uname, pswd, userType)
        if res[0]:
            check = True

            data = {
                'signed': signed,
                'userType': userType,
                'fname': res[1],
                'uname': uname,
                'pswd': pswd
            }

            return jsonify({'success': True, 'redirect': url_for('home'), 'data': data})
        else:
            return "Invalid password!"
    except Exception as ex:
        return f"{ex}"


# Registration
@app.route('/saveRegData', methods=["POST"])
def saveRegData():
    global userData
    global genOTP
    fname = request.form["fname"]
    uname2 = request.form["uname"]
    phone = request.form["phone"]
    pswd = hash(request.form["pswd"])
    userData = [fname, uname2, phone, pswd]
    try:
        genOTP = generateOTP(uname2)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

@app.route("/generateAndValidate", methods=["POST"])
def genVal():
    otp = request.form["otp"]
    if genOTP == otp:
        try:
            conn = sql.connect(r"Files/cms.db")
            cursor = conn.cursor()
            cursor.execute(f"""INSERT INTO USERS VALUES(
                '{userData[0]}',
                '{userData[1]}',
                '{userData[2]}',
                '{userData[3]}'           
            )""")
            conn.commit()
            return jsonify({'success': True, 'message': "User registration successfull"})
        except Exception as ex:
            return jsonify({'success': False, 'message': f"Error: {ex}"})
    else:
        return jsonify({'success': False, 'message': "User registration failed!"})


@app.route('/logout')
def logout():
    global check
    check = False

    return jsonify({'redirect': url_for('home')})

@app.route('/generate_otp', methods=["POST"])
def generate_otp():
    global user
    uname3 = request.form["uname"]
    user = uname3
    return generateOTP(uname3)

@app.route('/change_password', methods=["POST"])
def change_password():
    pswd = hash(request.form["pswd"])
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    ld = cursor.execute(f"UPDATE USERS SET PSWD='{pswd}' WHERE UNAME='{user}'")
    print(ld, user, pswd)
    conn.commit()
    return jsonify({'success': True, 'message': 'Password changed successfull'})

@app.route('/change_password2', methods=["POST"])
def change_password2():
    pswd = hash(request.form["npswd"])
    cpswd = hash(request.form["pswd"])
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    print(uType)
    if uType == "admin":
        res = conn.execute(f"SELECT PSWD FROM ADMIN WHERE UNAME='{user}'").fetchone()[0]
        if res == cpswd:
            cursor.execute(f"UPDATE ADMIN SET PSWD='{pswd}' WHERE UNAME='{user}'")
            conn.commit()
            return jsonify({'success': True, 'message': 'Password changed successfull'})
        else:
            return jsonify({'success': False, 'message': 'Password changed failed'})

    elif uType == "customer":
        res = conn.execute(f"SELECT PSWD FROM USERS WHERE UNAME='{user}'").fetchone()[0]
        if res == cpswd:
            cursor.execute(f"UPDATE USERS SET PSWD='{pswd}' WHERE UNAME='{user}'")
            conn.commit()
            return jsonify({'success': True, 'message': 'Password changed successfull'})
        else:
            return jsonify({'success': False, 'message': 'Password changed failed'})
    
    else:
        return jsonify({'success': False, 'message': 'Password changed failed'})
        


@app.route('/getdata', methods=["POST"])
def getdata():
    conn = sql.connect(r"Files/cms.db")
    nuser = conn.execute("SELECT COUNT(*) FROM USERS").fetchone()[0]
    norder = conn.execute("SELECT COUNT(*) FROM INVOICES WHERE DATE=?", (datetime.now().date(),)).fetchone()[0]
    tprice = conn.execute("SELECT SUM(QUANTITY*PRICE) FROM PURCHASES WHERE BILLNO IN (SELECT BILLNO FROM INVOICES WHERE DATE=?)", (datetime.now().date(),)).fetchone()[0]
    nfeed = conn.execute("SELECT COUNT(*) FROM FEEDBACKS").fetchone()[0]
    sales = conn.execute("SELECT DISTINCT PRODUCT FROM PURCHASES").fetchall()
    tprice = 0 if tprice == None else tprice
    norder = 0 if norder == None else norder

    ls = []
    print(sales)
    for i in sales:
        c = conn.execute(f"SELECT SUM(QUANTITY) FROM PURCHASES WHERE PRODUCT='{i[0]}' AND BILLNO IN (SELECT BILLNO FROM INVOICES WHERE DATE='{year+'-'+month+'-'+day}')").fetchone()
        if c[0] != None:
            ls.append([i[0], c[0]])
    print(ls)
    sales = False if len(ls) == 0 else ls
    # print(sales)
    items = conn.execute("SELECT PRODUCT, PRICE FROM PRODUCTS").fetchall()
    print(nuser)
    return jsonify({'users':nuser, 'orders':norder, 'tprice':tprice, 'feeds':nfeed, 'sales': sales, 'products': items})

@app.route('/addfoods', methods=["POST"])
def addfood():

    food = request.form["fname"]
    qty = request.form["nqty"]
    ftype = request.form["ftype"]
    price = request.form["price"]
    image = request.files["image"].read()
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO PRODUCTS VALUES (?,?,?,?,?)", (food, qty, price, ftype, image))
        conn.commit()
        return jsonify({'success': True})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})
    

def tobase64(blob):
    return base64.b64encode(blob).decode('utf-8')

    

@app.route('/getfoods', methods=["POST"])
def getfood():
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        data = conn.execute("SELECT * FROM PRODUCTS").fetchall()
        ls = []
        for i in data:
            ls.append([i[0], i[1], i[2], i[3], tobase64(i[4])])
            
        return jsonify({'success': True, 'data': ls})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})
    

@app.route('/getinvoices', methods=["POST"])
def getinvoices():
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    ls = []
    try:
        data = conn.execute("SELECT * FROM INVOICES").fetchall()
        for i in data:
            d1 = "SELF" if i[0] == "SELF" else conn.execute(f"SELECT FNAME FROM USERS WHERE UNAME='{i[0]}'").fetchone()[0]
            d2 = conn.execute(f"SELECT SUM(PRICE*QUANTITY) FROM PURCHASES WHERE BILLNO='{i[1]}'").fetchone()[0]
            d3 = conn.execute(f"SELECT PRODUCT, QUANTITY, PRICE FROM PURCHASES WHERE BILLNO={i[1]}").fetchall()
            ls.append([i[1], d1, i[2], d2, d3])      
        return jsonify({'success': True, 'data': ls})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})


@app.route('/removefood', methods=["POST"])
def removefood():
    pname = request.form["product"]
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM PRODUCTS WHERE PRODUCT='{pname}'")
        conn.commit()    
        return jsonify({'success': True})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})
    
@app.route('/editfoods', methods=["POST"])
def editfood():
    food = request.form["fname"]
    qty = request.form["nqty"]
    ftype = request.form["ftype"]
    price = request.form["price"]
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE PRODUCTS SET PRODUCT='{food}', PRICE={price}, QUANTITY={qty}, FOODTYPE='{ftype}' WHERE PRODUCT='{food}'")
        conn.commit()
        return jsonify({'success': True})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})
    

@app.route("/getbillno")
def getbillno():
    conn = sql.connect(r"Files/cms.db")
    bno = conn.execute(f"SELECT BILLNO FROM INVOICES ORDER BY BILLNO DESC").fetchone()[0]
    return jsonify({'bno':int(bno)+1, 'date':year+"-"+month+"-"+day})

#[pname, qty, cost]
#data = [$("#bno").val(), $("#bdate").val(), "SELF", prod_ls]
@app.route("/addinvoices", methods=["POST"])
def addinvoices():
    data = request.get_json(force=True)
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        cursor.execute(f"INSERT INTO INVOICES VALUES ('{data[2]}', {data[0]}, '{data[1]}')")
        for i in data[3]:
            cursor.execute(f"INSERT INTO PURCHASES VALUES ({data[0]}, '{i[0]}', {i[1]}, {i[2]})")
        conn.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})


@app.route('/removeinvoice', methods=["POST"])
def removeinvoice():
    bno = request.form["bno"]
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM PURCHASES WHERE BILLNO={bno}")
        cursor.execute(f"DELETE FROM INVOICES WHERE BILLNO={bno}")
        conn.commit()    
        return jsonify({'success': True})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})


@app.route("/getfoodlist")
def getfoodlist():
    conn = sql.connect(r"Files/cms.db")
    rs = [val[0] for val in conn.execute("SELECT DISTINCT FOODTYPE FROM PRODUCTS").fetchall()]
    if "Specials" in rs:
        rs.insert(0, rs.pop(rs.index("Specials")))
    data = []
    for i in rs:
        rs2 = conn.execute(f"SELECT PRODUCT, QUANTITY, PRICE, IMAGE FROM PRODUCTS WHERE FOODTYPE='{i}'").fetchall()
        ls = []
        for j in rs2:
            ls.append([j[0], j[1], j[2], 'data:image/jpeg;base64,'+tobase64(j[3])])
        data.append([i, ls])
    return data

@app.route("/shoppingdata", methods=["POST"])
def shopdata():
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    data = request.get_json(force=True)
    bno = int(conn.execute(f"SELECT BILLNO FROM INVOICES ORDER BY BILLNO DESC").fetchone()[0])+1
    cursor.execute(f"INSERT INTO INVOICES VALUES ('{user}', {bno}, '{data['0'][3]}')")
    for key in data.keys():
        prod = data[key]
        cursor.execute(f"INSERT INTO PURCHASES VALUES ({bno}, '{prod[0]}', {prod[2]}, {prod[1]})")
        cursor.execute(f"UPDATE PRODUCTS SET QUANTITY=QUANTITY-{prod[2]} WHERE PRODUCT='{prod[0]}'")
    conn.commit()
    return jsonify({'success': True})

@app.route('/getinvoices2', methods=["POST"])
def getinvoices2():
    conn = sql.connect(r"Files/cms.db")
    cursor = conn.cursor()
    ls = []
    try:
        name = conn.execute(f"SELECT FNAME FROM USERS WHERE UNAME='{user}'").fetchone()[0]
        data = conn.execute(f"SELECT BILLNO, DATE FROM INVOICES WHERE UID='{user}'").fetchall()
        for i in data:
            d2 = conn.execute(f"SELECT SUM(PRICE*QUANTITY) FROM PURCHASES WHERE BILLNO='{i[0]}'").fetchone()[0]
            d3 = conn.execute(f"SELECT PRODUCT, QUANTITY, PRICE FROM PURCHASES WHERE BILLNO={i[0]}").fetchall()
            ls.append([i[0], i[1], d2, d3, name])      
        return jsonify({'success': True, 'data': ls})
    except Exception as ex:
        print(ex)
        return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)