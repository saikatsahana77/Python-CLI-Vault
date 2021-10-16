import sqlite3
import os
import ntpath
import configparser
import getpass
import re
import hashlib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import math
import random
import atexit

def delete_temp_files():
    filelist = [ f for f in os.listdir("temp")]
    for f in filelist:
        os.remove(os.path.join("temp", f))

def convert_into_binary(file_path):
    with open(file_path, 'rb') as file:
        binary = file.read()
    return binary

def encrypt(text):
    b = text.encode()
    enc = hashlib.sha1(b).hexdigest()
    return enc

def sqlite_connect():
    try:
        conn = sqlite3.connect("safe.db")
    except sqlite3.Error:
        print(f"Error connecting to the database safe.db")
    finally:
        return conn


def insert_file(file_name):
    try:
        # Establish a connection
        connection = sqlite_connect()

        # Create a cursor object
        cursor = connection.cursor()

        sqlite_insert_blob_query = f"""
        INSERT INTO safe (name, data, file) VALUES (?, ?, ?)
        """
        sql_create_table_query = """
        CREATE TABLE IF NOT EXISTS safe (name TEXT NOT NULL, data BLOB, file TEXT NOT NULL);
        """
        cursor.execute(sql_create_table_query)

        # Convert the file into binary
        binary_file = convert_into_binary(file_name)

        if os.path.isabs(file_name)==False:
            if os.name == "nt":
                file_name = os.path.dirname(os.path.realpath(__file__))  + "\\" + file_name
            else:
                file_name = os.path.dirname(os.path.realpath(__file__))  + "/" + file_name
        file  = ntpath.basename(file_name)
        data_tuple = (file_name, binary_file, str(file))

        # Execute the query
        cursor.execute(sqlite_insert_blob_query, data_tuple)
        connection.commit()
        print('File inserted successfully')
        if os.path.exists(file_name):
            os.remove(file_name)
        else:
            print("The file does not exist in safe")
        cursor.close()
    except sqlite3.Error:
        print("Failed to insert file")
    finally:
        if connection:
            connection.close()


def write_to_file(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    with open(file_name, 'wb') as file:
        file.write(binary_code)
    print(f'Saved file to path: {file_name}')

def preview_file_save(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    with open(file_name, 'wb') as file:
        file.write(binary_code)
    if os.name == 'nt':
        os.system('"{}"'.format(file_name))
    else:
        os.system("xdg-open '{}'".format(file_name))
    print(f'Previewing file: {file_name}')   

def preview_file(file_name):
    try:
        # Establish a connection
        connection = sqlite_connect()

        # Create a cursor object
        cursor = connection.cursor()

        sql_retrieve_file_query = f"""SELECT * FROM safe WHERE file = ?"""
        cursor.execute(sql_retrieve_file_query, (file_name,))

        # Retrieve results in a tuple
        record = cursor.fetchone()

        # Create teh required path
        if os.name == "nt":
            file_name = os.path.dirname(os.path.realpath(__file__))  + "\\temp\\" + record[2]
        else:
            file_name = os.path.dirname(os.path.realpath(__file__))  + "/temp/" + record[2]

        # Save to a file
        preview_file_save(record[1], file_name)
    except sqlite3.Error:
        print("Failed to retreive blob from the table")
    except TypeError:
        print("File not available")
    finally:
        if connection:
            connection.commit()
            connection.close()
def retrieve_file(file_name):
    try:
        # Establish a connection
        connection = sqlite_connect()

        # Create a cursor object
        cursor = connection.cursor()

        sql_retrieve_file_query = f"""SELECT * FROM safe WHERE file = ?"""
        cursor.execute(sql_retrieve_file_query, (file_name,))

        # Retrieve results in a tuple
        record = cursor.fetchone()
        # Save to a file
        write_to_file(record[1], record[0])

        sql_delete_file_query = f"""DELETE FROM safe WHERE file = ?"""
        cursor.execute(sql_delete_file_query, (file_name,))
    except sqlite3.Error:
        print("Failed to retreive blob from the table")
    except TypeError:
        print("File not available")
    finally:
        if connection:
            connection.commit()
            connection.close()
def tabulate(j):
    len_arr = []
    c = len(j[0])
    for l in range(c):
        len_arr.append(len(j[0][l]))
    for i in j:
        ind = 0
        for ind,x in enumerate(i):
            if len(x)>len_arr[ind]:
                len_arr[ind]=len(x)
    for idx,h in enumerate(len_arr):
        len_arr[idx]+=1
    for idx,i in enumerate(j):
        for ind,k in enumerate(i):
            j[idx][ind] = j[idx][ind] + " "*(len_arr[ind]-len(j[idx][ind]))
    for idx,i in enumerate(j):
        j[idx] = "".join(i)
    for i in j:
        print(i)

def list_files():
    try:
        # Establish a connection
        connection = sqlite_connect()

        # Create a cursor object
        cursor = connection.cursor()

        sql_retrieve_file_query = f"""SELECT * FROM safe"""
        cursor.execute(sql_retrieve_file_query)

        record = cursor.fetchall()
        record_arr = []
        record_arr.append(["file","path"])
        record_arr.append(["",""])
        for i in record:
            record_arr.append([i[2],i[0]])
        print("\n"+ "-"*15)
        tabulate(record_arr)
        print("\n"+ "-"*15)
    except sqlite3.Error:
        print ("Safe is empty!")
    finally:
        if connection:
            connection.close()

def send_otp(email):
    sender_email = "##Enter your email here##"
    receiver_email = email
    password = "##Enter Your Password Here##"
    message = MIMEMultipart()
    message["Subject"] = "OTP For password reset in Python CLI Vault (Check your Spam folder too): "
    message["From"] = sender_email
    message["To"] = receiver_email
    digits = [i for i in range(0, 10)]
    otp = ""
    for i in range(6):
        index = math.floor(random.random() * 10)
        otp += str(digits[index])
    text = "OTP For password reset in Python CLI Vault is {}".format(otp)
    content = MIMEText(text, "plain")
    message.attach(content)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )
    except:
        otp = "Setup your email properly"
    return str(otp)


if __name__ == '__main__':

    
    print(r" /$$    /$$                    /$$   /$$            /$$$$$$  /$$       /$$$$$$")
    print(r"| $$   | $$                   | $$  | $$           /$$__  $$| $$      |_  $$_/")
    print(r"| $$   | $$ /$$$$$$  /$$   /$$| $$ /$$$$$$        | $$  \__/| $$        | $$")  
    print(r"|  $$ / $$/|____  $$| $$  | $$| $$|_  $$_/        | $$      | $$        | $$")  
    print(r" \  $$ $$/  /$$$$$$$| $$  | $$| $$  | $$          | $$      | $$        | $$")  
    print(r"  \  $$$/  /$$__  $$| $$  | $$| $$  | $$ /$$      | $$    $$| $$        | $$")  
    print(r"   \  $/  |  $$$$$$$|  $$$$$$/| $$  |  $$$$/      |  $$$$$$/| $$$$$$$$ /$$$$$$")
    print(r"    \_/    \_______/ \______/ |__/   \___/         \______/ |________/|______/")

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    print("\n")

    content = []

    atexit.register(delete_temp_files)

    if os.path.exists("config.ini"):
        config = configparser.ConfigParser()
        config.read('config.ini')
        try: 
            if (config['DEFAULT']['password'] != ""):
                content.append(config['DEFAULT']['password'])
        except:
            pass
        try: 
            if (config['DEFAULT']['email'] != ""):
                content.append(config['DEFAULT']['email'])
        except:
            pass


    if os.path.exists("config.ini")==False or len(content)!= 2:
        with open('config.ini','w') as file:
            pass
        print("Welsome To Python vault CLI\n")
        while True:
            password = getpass.getpass(prompt="Enter a new password for your vault: ")
            passconf = getpass.getpass(prompt="Confirm your new password: ")
            if (password!=passconf):
                print("\nPasswords do not match, please try again!\n")
            else:
                config = configparser.ConfigParser()
                config.read('config.ini')
                config['DEFAULT']['password'] = encrypt(password)
                with open('config.ini','w') as file:
                    config.write(file)
                break
        while True:
            email = input("Enter an email for password recovery: ")
            if(re.fullmatch(regex, email)):
                config = configparser.ConfigParser()
                config.read('config.ini')
                config['DEFAULT']['email'] = email
                with open('config.ini','w') as file:
                    config.write(file)
                break
            else:
                print ("\nEmail format is not correct\n")
    else:
        while True:
            print("\n"+ "*"*15)
            print("Commands:")
            print("e = enter password")
            print("r = reset password") 
            print("c = change email")
            print("q = quit program") 
            print("*"*15)

            input_ = input(":")

            if input_ == "e":
                password = getpass.getpass(prompt="Enter your password: ")
                config = configparser.ConfigParser()
                config.read('config.ini')
                if (config['DEFAULT']['password'] == encrypt(password)):
                    break
                else:
                    print ("\nPassword Incorrect, please try again!")
            elif input_ == "q":
                os._exit(0)
            elif input_ == "r":
                config = configparser.ConfigParser()
                config.read('config.ini')
                l = config['DEFAULT']['email']
                otp = send_otp(l)
                if (otp=="Setup your email properly"):
                    print("\n"+otp+"\n")
                else:
                    otp_user = input("Enter the otp sent: ")
                    print("\n")
                    if (otp==otp_user):
                        password_conf = getpass.getpass(prompt="Enter your new password: ")
                        config = configparser.ConfigParser()
                        config.read('config.ini')
                        config['DEFAULT']['password'] = encrypt(password_conf)
                        with open('config.ini','w') as file:
                            config.write(file)
                        print ("\nPassword Reset Successfully\n")

                    else:
                        print ("\nPlease enter correct otp\n")
            elif input_ == "c":
                password = getpass.getpass(prompt="Enter your password: ")
                config = configparser.ConfigParser()
                config.read('config.ini')
                if (config['DEFAULT']['password'] == encrypt(password)):
                    email = input("Enter the email to be set: ")
                    if(re.fullmatch(regex, email)):
                        config = configparser.ConfigParser()
                        config.read('config.ini')
                        config['DEFAULT']['email'] = email
                        with open('config.ini','w') as file:
                            config.write(file)
                        print ("\nEmail Changed Successfully\n")
                    else:
                        print ("\nEmail format is not correct\n")
                else:
                    print ("\nPassword Incorrect, please try again!")


    print("\nYou are logged in now, press q to quit the aplication\n")
    while True:
        print("\n"+ "*"*15)
        print("Commands:")
        print("r = retrieve file")
        print("s = store file")
        print("d = display files")
        print("p = preview file")
        print("q = quit program")
        print("*"*15)

        input_ = input(":")

        if input_ == "q":
            break
        elif input_ == "s":
            file = input("\nPlease enter the full path of the file you are trying to store:\n")
            if os.path.exists(file):
                insert_file(file)
            else:
                print("\nPlease enter correct path of a file\n")
        elif input_ == "r":
            file = input("\nPlease enter the name of the file you are trying to retreive:\n")
            retrieve_file(file)
        elif input_ == "d":
            list_files()
        elif input_ == "p":
            file = input("\nPlease enter the name of the file you are trying to preview (Note: No changes done in the file during preview will be saved):\n")
            preview_file(file)
        else:
            print("\nPlease enter correct option\n")


