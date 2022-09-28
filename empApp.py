from email.mime import application
from flask import Flask, render_template, request, current_app
from pymysql import connections
import os
import io
import boto3
from config import *
from json import dumps

UPLOAD_FOLDER = "app/static/file_upload"

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}

@application.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

#add emp 
@application.route('/addEmp', methods = ['POST'])
def add():
    emp_name = request.form['emp_name']
    emp_email = request.form['emp_email']
    emp_contact = request.form['emp_contact']
    emp_position = request.form['emp_position']
    emp_salary = request.form['emp_salary']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO EMPLOYEE (EMP_NAME, EMP_EMAIL, EMP_CONTACT, EMP_POSITION, EMP_SALARY) VALUES (%s, %s, %s, %s, %s);"
    next_emp_id_sql = "SELECT `AUTO_INCREMENT` FROM  INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'employee' AND TABLE_NAME = 'EMPLOYEE';"
    cursor = db_conn.cursor()

    #fetch new employee id from database
    emp_id = ''
    try:
        cursor.execute(next_emp_id_sql)
        # get all records
        records = cursor.fetchall()
        for id in records:
            emp_id = id[0]
    except Exception as e:
        return str(e)

    #if emp_image_file.filename == "":
        # upload anonymous pic select a file"
    # emp_id = next_emp_id_sql

    try:
        cursor.execute(insert_sql, (emp_name, emp_email, emp_contact, emp_position, emp_salary))
        db_conn.commit()
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = emp_id
        s3 = boto3.resource('s3') 
        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            # s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            #s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3)

            ## save upload file in temporary folder
            emp_image_file.save(os.path.join(application.config['UPLOAD_FOLDER'], emp_image_file.filename))
            
            s3.meta.client.upload_file(str(os.path.join(application.config['UPLOAD_FOLDER'], emp_image_file.filename)), custombucket, str(emp_id))
            
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint']) 
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location 
            objectrl = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3) 
        except Exception as e:
            return str(e)  

    finally:
        cursor.close()

    return render_template('index.html')

#fetch emp
@application.route('/fetchEmp', methods = ['POST'])
def fetch():
    emp_id = request.form['emp_id']
    s3_client = boto3.client('s3')
    try:
        select_sql = "SELECT EMP_NAME, EMP_EMAIL, EMP_CONTACT, EMP_POSITION, EMP_SALARY FROM EMPLOYEE WHERE EMP_ID = %s;"
        cursor = db_conn.cursor()
        cursor.execute(select_sql, (emp_id))
        data = cursor.fetchall()
        for row in data:
            emp_name = row[0]
            emp_email = row[1]
            emp_contact = row[2]
            emp_position = row[3]
            emp_salary = row[4]
        cursor.close()


        return render_template('index.html', emp_id=emp_id, emp_name=emp_name, emp_email=emp_email, emp_contact=emp_contact, emp_position=emp_position, emp_salary=emp_salary)
    except:
        return("ERROR :: EMPLOYEE NOT FOUND")

   
#update emp 
@application.route('/updateEmp', methods = ['POST'])
def update():
    emp_id = request.form['emp_id']
    emp_name = request.form['emp_name']
    emp_email = request.form['emp_email']
    emp_contact = request.form['emp_contact']
    emp_position = request.form['emp_position']
    emp_salary = request.form['emp_salary']
    emp_image_file = request.files['emp_image_file']

    try:

     update_sql = "UPDATE EMPLOYEE SET EMP_NAME = %s, EMP_EMAIL = %s, EMP_CONTACT = %s, EMP_POSITION = %s, EMP_SALARY = %s WHERE EMP_ID = %s;"
     cursor = db_conn.cursor()

     #if emp_image_file.filename == "":
        # upload anonymous pic select a file"

     try:
         cursor.execute(update_sql, (emp_name, emp_email, emp_contact, emp_position, emp_salary, emp_id))
         db_conn.commit()
         # Uplaod image file in S3 #
         emp_image_file_name_in_s3 = emp_id
         s3 = boto3.resource('s3')

         try:
             print("Data inserted in MySQL RDS... uploading image to S3...")
             s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
             bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
             s3_location = (bucket_location['LocationConstraint'])
   
             if s3_location is None:
                 s3_location = ''
             else:
                 s3_location = '-' + s3_location
   
             objectrl = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                 s3_location,
                 custombucket,
                 emp_image_file_name_in_s3)
   
         except Exception as e:
             return str(e)  
   
     finally:
         cursor.close()
          
         return render_template('index.html')

    except:
        return("ERROR :: EMPLOYEE NOT FOUND")

        


#update emp 
@application.route('/removeEmp', methods = ['POST'])
def remove():
    emp_id = request.form['emp_id']

    delete_sql = "DELETE FROM EMPLOYEE WHERE EMP_ID = %s;"
    cursor = db_conn.cursor()

    try:
        cursor.execute(delete_sql, (emp_id))
        db_conn.commit()
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = emp_id
        s3 = boto3.resource('s3')

        try:
            # # print("Data inserted in MySQL RDS... uploading image to S3...")
            # s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3)
            # bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            # s3_location = (bucket_location['LocationConstraint'])

            # if s3_location is None:
            #     s3_location = ''
            # else:
            #     s3_location = '-' + s3_location

            # objectrl = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            #     s3_location,
            #     custombucket,
            #     emp_image_file_name_in_s3)

            s3.Object(custombucket, str(emp_id)).delete()
        except Exception as e:
            return str(e)  

    finally:
        cursor.close()

    return render_template('index.html')        


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)
    
