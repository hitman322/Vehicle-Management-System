from flask import Flask,render_template ,flash, redirect,url_for,session, request,logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_simplelogin import is_logged_in
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
# from flask_wtf import RecaptchaField
import string
import random
import requests
import json
import datetime
from dateutil.relativedelta import relativedelta
from flask_apscheduler import APScheduler


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'iiita123'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'secretman'
# app.config['JOBS'] = [
#     {
#         'id': 'scheduled_job',
#         'func': 'scheduled_job',
#         'trigger': 'cron',
#         'day_of_week': 'mon-sun',
#         'hour': 2,
#         'minute': 35
#     }
# ]
# app.config['SCHEDULER_API_ENABLED'] = True

# app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdY01EUAAAAAP9AaHQs2xmqHlEZTEzJe7fIXlYm'
# app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdY01EUAAAAAJHIc1Jho_nhh4w_FBoTBlxOTZcS'

mysql = MySQL(app)

# scheduler = APScheduler()
# scheduler.init_app(app)


@app.route('/')
def index():
	return render_template('homepage.html')

# @app.route('/About')
# def About():
# 	return render_template('about.html')

# @app.route('/Contact')
# def About():
# 	return render_template('about.html')


@app.route('/About')
def About():
	return render_template('index.html')

#User Registration form class
class RegisterForm(Form):
	name = StringField('Your Name',[validators.Length(min=1, max =50)])
	email = StringField('Email',[validators.Length(min=6, max =50)])
	user_id = StringField('User Id',[validators.Length(min=6, max =50)])
	password = PasswordField('Password',[
		validators.Length(min=8, max =25),
		validators.EqualTo('confirm', message = 'Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')
	mobile = StringField('Mobile Number',[validators.Length(min=10, max =10)])
	# recaptcha = RecaptchaField()

#User Registration
@app.route('/Sign Up', methods = ['GET','POST'])
def signup():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data 
		email = form.email.data
		user_id = form.user_id.data
		password = sha256_crypt.encrypt(str(form.password.data))
		mobile = form.mobile.data


		#create cursor
		cur = mysql.connection.cursor()

		#Checking if user id, email, mobile already exists

		var=0

		result = cur.execute("SELECT * FROM users WHERE user_id=%s",[user_id])

		if result > 0:
			flash ('User Id already exists','danger')
			var =1
			return redirect(url_for ('signup'))

		result = cur.execute("SELECT * FROM users WHERE user_email=%s",[email])

		if result > 0:
			flash ('Email already exists','danger')
			var = 1
			return redirect(url_for ('signup'))


		result = cur.execute("SELECT * FROM users WHERE user_mobile=%s",[mobile])

		if result > 0:
			flash ('Mobile number already exists','danger')
			var =1
			return redirect(url_for ('signup'))

		if var != 1 :
			cur.execute("INSERT INTO users(user_id,user_name,user_password,user_mobile,user_email,user_type) VALUES (%s, %s,%s, %s ,%s,%s)",(user_id,name,password,mobile,email,0))

			#commit to DB
			mysql.connection.commit()

			#Close connection

			cur.close()


			# flash ('You are now successfully registered !!! Log in to continue','success')
			return redirect(url_for ('Login'))

		

	return render_template('3Register.html',form = form)



#User Login
@app.route('/Login', methods = ['GET','POST'])
def Login():
	if request.method == 'POST' :
		user_id=request.form['user_id']
		candidate_password=request.form['password']

		cur=mysql.connection.cursor()

		result = cur.execute("SELECT * FROM users WHERE user_id=%s",[user_id])

		if result > 0:
			data = cur.fetchone()
			password=data['user_password']

			if sha256_crypt.verify(candidate_password,password):
				session['user_id'] = user_id


				user_type = data['user_type']

				cur.execute("SELECT * FROM ride WHERE user_id =%s",[session['user_id']])
				var=0
				data=cur.fetchall()
				for res in data:
					details=cur.execute("SELECT * FROM ridestatus where ride_id = %s AND ride_status=%s",(res['ride_id'],"BOOKED"))
					if details >0:
						var=1
						break

				if user_type == 0:
					session['logged_in'] =True
					if var > 0 :
						session['booked_ride'] = True
						return redirect(url_for ('vieworcancel'))
						 
					else:
						return redirect(url_for ('dashboarduser'))
						
				else :
					session['adminlogged_in'] =True
					return redirect(url_for ('dashboardadmin'))


				
			else :
				error ='Invalid Login'
				return render_template('2LOGIN.html', error = error)

			cur.close()
		else :
			error='User Id not found'
			return render_template('2LOGIN.html', error = error)

	return render_template('2LOGIN.html')

# def is_logged_in (f):
# 	@wraps(f)
# 	def wrap(*args,**kwargs):
# 		if 'logged_in' in session:
# 			return f(*args,**kwargs)
# 		else  :
# 			flash ('Unauthorized. Please Login','danger')
# 			return redirect(url_for ('Login'))

#Logout
@app.route('/Logout')
def Logout():
	if session.get('logged_in') == True or session.get('adminlogged_in') == True:
		session.clear()
		flash ('You are now successfully logged out !!!','success')
		return redirect(url_for ('Login'))
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#dashboard for user
@app.route('/dashboarduser')
def dashboarduser():
	if session.get('logged_in') == True:
		return render_template('dashboard_user.html')
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))



#dashboard for admin
@app.route('/dashboardadmin')
def dashboardadmin():
	if session.get('adminlogged_in') == True:
		return render_template('dashboard_admin.html')
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Booking ride form class
class RideForm(Form):
	start = StringField('Boarding Point',[validators.Length(min=4, max =250)])
	end = StringField('Destination',[validators.Length(min=4, max =250)])
	veh_type = StringField('Vehicle Type',[validators.Length(min=4, max =100)])
	

#Booking a ride
@app.route('/bookride',methods = ['GET','POST'])
def bookride():
	form = RideForm(request.form)
	if request.method == 'POST' and form.validate():
		start = form.start.data 
		end = form.end.data
		veh_type = form.veh_type.data
		api_key = "AIzaSyA4oSzKKcI0Pt5FS5VUy32x6sXoBuu4Nu8"
		url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + start + "&destinations=" + end + "&key=AIzaSyA4oSzKKcI0Pt5FS5VUy32x6sXoBuu4Nu8"

		dist = requests.get(url)
		payload = json.loads(dist.content)
		#print payload
		ride_distance = payload['rows'][0]['elements'][0]['distance']['text']



		#create cursor
		cur = mysql.connection.cursor()

		var=1

		while var ==1 :
			ride_id = random_generator()
			result = cur.execute("SELECT * FROM ride WHERE ride_id=%s",[ride_id])
			if result > 0:
				var=1
			else :
				var=0



		var=1

		while var ==1 :
			cur.execute("SELECT * FROM vehicle WHERE veh_type=%s AND is_deleted=%s ORDER BY RAND() LIMIT 1 ",(veh_type,0))
			res1 = cur.fetchone()
			veh_reg_no= res1['veh_reg_no']

			result = cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id = b.ride_id AND a.veh_reg_no=%s AND b.ride_status=%s",(veh_reg_no,"BOOKED"))
			if result > 0:
				var=1
			else :
				var=0



		var=1

		while var ==1 :
			cur.execute("SELECT * FROM driver WHERE is_deleted=%s ORDER BY RAND() LIMIT 1 ",[0])
			res2 = cur.fetchone()
			driver_id= res2['driver_id']
			result = cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id = b.ride_id AND a.driver_id=%s AND b.ride_status=%s",(driver_id,"BOOKED"))
			if result > 0:
				var=1
			else :
				var=0



		var=0

		cur.execute("SELECT * FROM ride WHERE user_id=%s",[session['user_id']])

		data = cur.fetchall()

		for res in data:
			result = cur.execute("SELECT * FROM ridestatus WHERE ride_id=%s AND ride_status=%s",(res['ride_id'],"BOOKED"))

		if result > 0 :
			flash ('There is an ongoing ride on this user id','danger')
			var =1
			return redirect(url_for ('viewride'))

		if var != 1:

			cur.execute("INSERT INTO rideinfo(ride_id,boarding_point,destination, ride_distance) VALUES (%s, %s,%s, %s )",(ride_id,start,end,ride_distance))

			#commit to DB
			mysql.connection.commit()

			cur.execute("INSERT INTO ridestatus(ride_id, ride_status) VALUES (%s, %s )",(ride_id,"BOOKED"))

			#commit to DB
			mysql.connection.commit()

			cur.execute("INSERT INTO ride(ride_id,user_id,veh_reg_no,driver_id) VALUES (%s, %s, %s, %s)",(ride_id,session.get('user_id'),veh_reg_no,driver_id))
	

			#commit to DB
			mysql.connection.commit()

			#Close connection

			cur.close()

			session['booked_ride'] =True


			#flash('Your ride has been booked !!','success')
			return  redirect(url_for ('vieworcancel'))

		

	return render_template('bookride.html',form = form)



#random string generator
def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
		   return ''.join(random.choice(chars) for x in range(size))

#Cancel ride 
@app.route('/cancelride')
def cancelride():
	if session.get('booked_ride') == True:
		session['booked_ride']=False
		cur = mysql.connection.cursor()

		cur.execute("SELECT * FROM ride where user_id = %s",[session['user_id']])

		data = cur.fetchall()

		for res in data:
			ride_id=res['ride_id']
			cur.execute("UPDATE ridestatus SET ride_status=%s where ride_id=%s and ride_status=%s",("CANCELLED",ride_id,"BOOKED"))

		mysql.connection.commit()


		#Close connection

		cur.close()

		flash ('You ride has been cancelled !!','success')
		return redirect(url_for ('bookride'))
	else :
		flash ('Unauthorized, please book a ride ','danger')
		return redirect(url_for ('bookride'))
	


#View ride details or cancel ride
@app.route('/vieworcancel')
def vieworcancel():
	if session.get('booked_ride') == True:
		return render_template('vieworcancel.html')
	else :
		flash ('Unauthorized, please book a ride ','danger')
		return redirect(url_for ('bookride'))



#View ride details
@app.route('/viewride')
def viewride():
	if session.get('booked_ride') == True:
		#create cursor
		cur = mysql.connection.cursor()

		cur.execute("SELECT * FROM ride WHERE user_id=%s",[session['user_id']])

		res=cur.fetchall()

		for data in res:
			result=cur.execute("SELECT * FROM ridestatus WHERE ride_id=%s AND ride_status=%s",(data['ride_id'],"BOOKED"))
			if result>0:
				data=cur.fetchone()
				ride_id=data['ride_id']
				break

		cur.execute("SELECT * FROM ride WHERE ride_id=%s",[ride_id])

		res1=cur.fetchone()

		veh_reg_no= res1['veh_reg_no']
		driver_id=res1['driver_id']


		cur.execute("SELECT * FROM vehicle where veh_reg_no =%s AND is_deleted=%s",(veh_reg_no,0))

		res2= cur.fetchone()
		


		cur.execute("SELECT * FROM driver where driver_id=%s AND is_deleted=%s",(driver_id,0))

		res3= cur.fetchone()


		cur.close()



		return render_template('viewride.html',res1=res1,res2=res2,res3=res3)
	else :
		flash ('Unauthorized, please book a ride ','danger')
		return redirect(url_for ('bookride'))



#Display Vehicle details
@app.route('/vehicle')
def vehicle():
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM vehicle WHERE is_deleted=%s",[0])

		data=cur.fetchall()


		if result > 0 :
			return render_template('vehicle.html',data =data)
		else :
			msg='No Vehicles found'
			return render_template('vehicle.html')

		#close connection
		cur.close()

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))



#Adding vehicle form class
class VehicleForm(Form):
	veh_reg_no = StringField('Vehicle Registration Number',[validators.Length(min=6, max =250)])
	veh_name = StringField('Vehicle Name',[validators.Length(min=4, max =250)])
	veh_type = StringField('Vehicle Type',[validators.Length(min=4, max =100)])
	veh_mileage = StringField('Vehicle Mileage',[validators.Length(min=1, max =3)])
	veh_repairdate=StringField('Vehicle Repair Date',[validators.DataRequired()])
	veh_oilexpenses=StringField('Vehicle Oil Expenses',[validators.Length(min=1, max =6)])
	

#Adding a vehicle by admin
@app.route('/addvehicle',methods = ['GET','POST'])
def addvehicle():
	if session.get('adminlogged_in') == True:
		form = VehicleForm(request.form)
		if request.method == 'POST' and form.validate():
			veh_reg_no = form.veh_reg_no.data 
			veh_name = form.veh_name.data
			veh_type = form.veh_type.data
			veh_mileage=form.veh_mileage.data
			veh_repairdate = form.veh_repairdate.data
			veh_oilexpenses = form.veh_oilexpenses.data


			#create cursor
			cur = mysql.connection.cursor()


			var=0

			result = cur.execute("SELECT * FROM vehicle WHERE veh_reg_no=%s",[veh_reg_no])

			if result > 0:
				flash ('Vehicle Registration Number already exists','danger')
				var =1
				return redirect(url_for ('addvehicle'))

			if var != 1 :
				cur.execute("INSERT INTO vehicle(veh_reg_no,veh_name,veh_type,veh_mileage,veh_repairdate,veh_oilexpenses,is_deleted) VALUES (%s, %s,%s,%s,%s,%s,%s )",(veh_reg_no,veh_name,veh_type,veh_mileage,veh_repairdate,veh_oilexpenses,0))

				#commit to DB
				mysql.connection.commit()

		

				#Close connection

				cur.close()

				flash('Your entry has been successfully added !!','success')
				return  redirect(url_for ('vehicle'))

		return render_template('addvehicle.html',form = form)

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))

#Editing vehicle form class
class EditVehicleForm(Form):
	veh_name = StringField('Vehicle Name',[validators.Length(min=4, max =250)])
	veh_type = StringField('Vehicle Type',[validators.Length(min=4, max =100)])
	veh_mileage = StringField('Vehicle Mileage',[validators.Length(min=1, max =3)])

#Editing a vehicle by admin
@app.route('/editvehicle/<string:veh_reg_no>',methods = ['GET','POST'])
def editvehicle(veh_reg_no):
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id=b.ride_id AND a.veh_reg_no=%s  AND b.ride_status=%s ",(veh_reg_no,"BOOKED"))
		if result > 0:
			flash ('Vehicle has been allotted to a user. ','danger')
			return  redirect(url_for ('vehicle'))

		else:
			cur.execute("SELECT * FROM vehicle WHERE veh_reg_no =%s",[veh_reg_no])

			data = cur.fetchone()

			form = EditVehicleForm(request.form)

			form.veh_name.data = data['veh_name']
			form.veh_type.data= data['veh_type']
			form.veh_mileage.data= data['veh_mileage']

			if request.method == 'POST' and form.validate():
				veh_name = request.form['veh_name']
				veh_type = request.form['veh_type']
				veh_mileage=request.form['veh_mileage']


				cur.execute("UPDATE vehicle SET veh_name=%s, veh_type=%s, veh_mileage=%s where veh_reg_no=%s",(veh_name,veh_type,veh_mileage,veh_reg_no))
			
				#commit to DB
				mysql.connection.commit()

			
				#Close connection
				cur.close()

				return  redirect(url_for ('vehicle'))

			

			return render_template('editvehicle.html',form = form)

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))



#Deleting a vehicle by admin
@app.route('/deletevehicle/<string:veh_reg_no>',methods = ['POST'])
def deletevehicle(veh_reg_no):
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id=b.ride_id AND a.veh_reg_no=%s  AND b.ride_status=%s ",(veh_reg_no,"BOOKED"))
		if result > 0:
			flash ('Vehicle has been allotted to a user. ','danger')
			return  redirect(url_for ('vehicle'))
		else :
			cur.execute("UPDATE vehicle SET is_deleted =%s WHERE veh_reg_no=%s",(1,veh_reg_no))

			#commit to DB
			mysql.connection.commit()


			#Close connection
			cur.close()

			return  redirect(url_for ('vehicle'))
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Display Driver details
@app.route('/driver')
def driver():
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM driver WHERE is_deleted=%s",[0])

		data=cur.fetchall()


		if result > 0 :
			return render_template('driver.html',data =data)
		else :
			msg='No Drivers found'
			return render_template('driver.html')

		#close connection
		cur.close()

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Adding driver form class
class DriverForm(Form):
	driver_id = StringField('Driver Id',[validators.Length(min=6, max =250)])
	driver_name = StringField('Driver Name',[validators.Length(min=3, max =250)])
	driver_mobile = StringField('Driver Mobile',[validators.Length(min=10, max =10)])
	

#Adding a driver by admin
@app.route('/adddriver',methods = ['GET','POST'])
def adddriver():
	if session.get('adminlogged_in') == True:
		form = DriverForm(request.form)
		if request.method == 'POST' and form.validate():
			driver_id = form.driver_id.data 
			driver_name = form.driver_name.data
			driver_mobile = form.driver_mobile.data


			#create cursor
			cur = mysql.connection.cursor()


			var=0

			result = cur.execute("SELECT * FROM driver WHERE driver_id=%s",[driver_id])

			if result > 0:
				flash ('Driver Id already exists','danger')
				var =1
				return redirect(url_for ('adddriver'))

			if var != 1 :
				cur.execute("INSERT INTO driver(driver_id,driver_name,driver_mobile,is_deleted) VALUES (%s, %s,%s,%s )",(driver_id,driver_name,driver_mobile,0))

				#commit to DB
				mysql.connection.commit()

		

			#Close connection

			cur.close()

			return  redirect(url_for ('driver'))

		return render_template('adddriver.html',form = form)
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Editing driver form class
class EditDriverForm(Form):
	driver_name = StringField('Driver Name',[validators.Length(min=3, max =40)])
	driver_mobile = StringField('Driver Mobile',[validators.Length(min=10, max =10)])



#Editing a driver by admin
@app.route('/editdriver/<string:driver_id>',methods = ['GET','POST'])
def editdriver(driver_id):
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id=b.ride_id AND a.driver_id=%s AND b.ride_status=%s",(driver_id,"BOOKED"))
		if result > 0:
			flash ('Driver has been allotted to a user. ','danger')
			return  redirect(url_for ('driver'))

		else:
			cur.execute("SELECT * FROM driver WHERE driver_id =%s",[driver_id])

			data = cur.fetchone()

			form = EditDriverForm(request.form)

			form.driver_name.data= data['driver_name']
			form.driver_mobile.data= data['driver_mobile']

			if request.method == 'POST' and form.validate(): 
				driver_name = request.form['driver_name']
				driver_mobile = request.form['driver_mobile']


				#app.logger.info()
			
				cur.execute("UPDATE driver SET driver_name=%s, driver_mobile=%s where driver_id=%s",(driver_name,driver_mobile,driver_id))
			
				#commit to DB
				mysql.connection.commit()

			
				#Close connection
				cur.close()

				# flash('Driver Updated !!','success')
				return  redirect(url_for ('driver'))
			

			return render_template('editdriver.html',form = form)
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Deleting a driver by admin
@app.route('/deletedriver/<string:driver_id>',methods = ['POST'])
def deletedriver(driver_id):
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM ride a,ridestatus b WHERE a.ride_id=b.ride_id AND a.driver_id=%s AND b.ride_status=%s",(driver_id,"BOOKED"))
		if result > 0:
			flash ('Driver has been allotted to a user. ','danger')
			return  redirect(url_for ('driver'))
		else:
			cur.execute("UPDATE driver SET is_deleted =%s WHERE driver_id=%s",(1,driver_id))

			#commit to DB
			mysql.connection.commit()

			#Close connection
			cur.close()

			flash('Driver Deleted !!','success')
			return  redirect(url_for ('driver'))
	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Vehicle Repairhistory and oil expenses
@app.route('/repairoil')
def repairoil():
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT * FROM vehicle WHERE is_deleted=%s",[0])

		data=cur.fetchall()


		if result > 0 :
			return render_template('repairoil.html',data =data)
		else :
			msg='No Vehicles found'
			return render_template('dashboard_admin.html')

		#close connection
		cur.close()

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))

#Booked Rides Status
@app.route('/bookingdetails')
def bookingdetails():
	if session.get('adminlogged_in') == True:
		#create cursor
		cur = mysql.connection.cursor()

		result=cur.execute("SELECT a.ride_id,a.user_id,b.boarding_point,b.destination,c.ride_status,b.ride_distance FROM ride a,rideinfo b,ridestatus c WHERE a.ride_id=b.ride_id and b.ride_id=c.ride_id")

		data=cur.fetchall()

		cur.execute("SELECT * FROM ridestatus WHERE ride_status=%s",["COMPLETED"])
		quer = cur.fetchall()
		fuel_expenses = []
		for res in quer:
			ride_id=res['ride_id']
			cur.execute("SELECT * FROM rideinfo WHERE ride_id =%s",[ride_id])
			res1= cur.fetchone()
			ride_distance = res1['ride_distance']
			cur.execute("SELECT * FROM ride WHERE ride_id=%s",[ride_id])
			res2 =cur.fetchone()
			cur.execute ("SELECT * FROM vehicle WHERE veh_reg_no=%s",[res2['veh_reg_no']])
			res3 =cur.fetchone()
			veh_mileage = res3['veh_mileage']
			ride_distance = ride_distance.replace(',','')
			dist = ride_distance.split(" ")
			distance = int(dist[0])
			mileage =int(veh_mileage)
			f = (distance/mileage)*70
			fuel_expenses.append((ride_id, f))	
			
	

		if result > 0 :
			return render_template('bookingdetails.html',data=data, fuel_expenses = fuel_expenses)

		else :
			msg='No Rides booked'
			return render_template('dashboard_admin.html')

		#close connection
		cur.close()

	else :
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))

#book another ride
@app.route('/bookanother')
def bookanother():
	if session.get('logged_in') == True:
		session['booked_ride']=False
		cur = mysql.connection.cursor()

		cur.execute("SELECT * FROM ride WHERE user_id=%s",[session['user_id']])

		res=cur.fetchall()

		for data in res:
			ride_id=data['ride_id']
			cur.execute("UPDATE ridestatus SET ride_status=%s WHERE ride_id =%s AND ride_status=%s",("COMPLETED",ride_id,"BOOKED"))
			
		mysql.connection.commit()				
			
			
		cur.close()
		return render_template ('bookanother.html')
	else:
		flash ('Unauthorized, please log in ','danger')
		return redirect(url_for ('Login'))


#Scheduled Job : Cron job
def schedule_job():
	d = datetime.datetime.now()
	s = d.strftime("%Y-%m-%d")
	cur = mysql.connection.cursor()

	result=cur.execute("SELECT veh_repairdate FROM vehicle WHERE veh_repairdate=%s",[s])

	data =cur.fetchone()

	if result > 0:
		x = datetime.datetime.strptime(data['veh_repairdate'], "%Y-%m-%d")
		n = x + relativedelta(months=3)
		cur.execute("UPDATE vehicle SET veh_repairdate =%s",[n.strftime("%Y-%m-%d")])

	cur.close()

if __name__ == '__main__':
	app.secret_key = 'secretman'
	# scheduler.start()
	app.run(debug=True, use_reloader=False)

