import html, sqlite3, os, sys, time
from flask import Flask, render_template, request, redirect, flash, send_from_directory, send_file
from datetime import datetime, timedelta, date
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QSettings, QCoreApplication

app = Flask(__name__)

app.secret_key = "This is a secret key."   # flash()함수를 사용하기 위해서는 세션암호화가 필요하고 flask에서는 왼쪽과 같은 문장으로 처리함.

# DBfolderpath = "D:/personal_study/py_Program/p7_Attendance_server/login/attendanceprogram.db"  # DB주소를 기재합니다.

# DBfolderpath를 입력받을 변수를 선언합니다.
DBfolderpath = os.environ.get("DBFOLDERPATH", None)
if DBfolderpath is None:
       DBfolderpath = input("DB 경로를 입력하세요(예:D:/test/test.db): ")

       # DBfolderpath를 설정합니다.
       app.config["DBFOLDERPATH"] = DBfolderpath
else:
    print("DB경로가 입력되지 않았습니다. 실행파일을 다시 실행한 후 경로를 입력하여 주시기 바랍니다.")

host = os.environ.get("HOST", None)
if host is None:
       host = input("host를 입력하세요(이 server IP가 아닌 이 server에 접속하는 라우터 IP, 예:192.168.0.1): ")

       # HOST를 설정합니다.
       app.config["HOST"] = host
else:
    print("host가 입력되지 않았습니다. 실행파일을 다시 실행한 후 host를 입력하여 주시기 바랍니다.")

port = os.environ.get("PORT", None)
if port is None:
       port = input("port를 입력하세요(이 server port가 아닌 이 server에 접속하는 라우터 port, 예:5000): ")

       # PORT를 설정합니다.
       app.config["PORT"] = port
else:
    print("host가 입력되지 않았습니다. 실행파일을 다시 실행한 후 host를 입력하여 주시기 바랍니다.")

app.config['STYLE_CSS_PATH'] = input("style.css파일이 있는 경로를 입력하세요(예:D:/test/templates/style.css): ")

nomatch_id_password = '''  <script>
  window.alert("아이디와 비밀번호가 일치하지 않습니다.");
  location.href = "/";
  </script>
  '''

exist_workon_data = '''<script>
  window.alert("출근기록이 있습니다. 퇴근때 퇴근버튼을 눌러주세요.");
  location.href = "/";
  </script>
  '''
exist_leaveworkplace_data = '''<script>
  window.alert("출근기록이 있습니다. 퇴근때 퇴근버튼을 눌러주세요.");
  location.href = "/";
  </script>
  '''

access_deny = '''<script>
  window.alert("주소입력창에 직접입력하면 접근할 수 없습니다.");
  location.href = "/";
  </script>
  '''

save_ok = '''<script>
  window.alert("저장되었습니다.");
  location.href = "/";
  </script>
  '''

no_work_record = '''<script>
  window.alert("출근기록이 없습니다. 관리자에게 문의하세요.");
  location.href = "/";
  </script>
  '''
nomatch_ch_password = '''  <script>
  window.alert("새로 변경할 비밀번호가 일치하지 않습니다.");
  location.href = "/";
  </script>
  '''

nomatch_info = '''  <script>
  window.alert("해당하는 사원정보가 없습니다. 관리자에게 문의 하세요.");
  location.href = "/";
  </script>
  '''

ch_password_ok = '''  <script>
  window.alert("변경이 완료되었습니다.");
  location.href = "/";
  </script>
  '''


@app.route("/")
def index():
   
   return render_template("intro.html")   # 루트 경로에 template폴더가 있고 거기 안에 해당 파일이 있음.

@app.route('/style.css')
def style():
    # return send_file('D:/personal_study/py_Program/p7_Attendance_server/login/templates/style.css')
    return send_file(app.config['STYLE_CSS_PATH']) 

@app.route("/submit", methods=["GET", "POST"])
def submit():
  
  if request.method == "GET":
        return access_deny

  elif request.method == "POST":
     # 입력 값
     company_num = request.form["company_num"]
     password = request.form["password"]
     checkday = request.form["checkday"]   # 뒤에 checktime은 위에 일자를 받아온다.
     checktime = request.form["checktime"]   # 뒤에 checktime은 위에 시간을 받아온다.
     workstart = str("workstart")
     leaveworkplace = str("leaveworkplace")
     attendtype_normal = str("정상")

     if request.form.get("work"):
        conn = sqlite3.connect(DBfolderpath)
        cur = conn.cursor()
        cur.execute("SELECT * FROM infoDB WHERE comnum=? AND password=?;", (company_num, password))
        rows = cur.fetchall()
        
        if rows == []:
          #  return redirect("/", code=302)
           return nomatch_id_password
          
        else:
           # 패스워드 검증이 완료되면 이후 출근기록이 있는지 확인한다. 출근기록이 없어야 출근을 할수 있다.
           cur.execute("SELECT * FROM att WHERE comnum=? AND startdate=? AND work_leave=?;", (company_num, checkday, workstart))
           exist_att_rows = cur.fetchall()
           if exist_att_rows == []:
              # 그 다음 근태기록 테이블에 넣을 부서정보를 insaDB로부터 가져온다.
              cur.execute("SELECT department FROM infoDB WHERE comnum=?;", (company_num,))
              extra_insert_info_row = cur.fetchone()
              extra_insert_info_department = str(extra_insert_info_row[0])
              cur.execute("SELECT name FROM infoDB WHERE comnum=?;", (company_num,))
              extra_insert_info_row_name = cur.fetchone()
              extra_insert_info_name = str(extra_insert_info_row_name[0])
              # insaDB에서 가져온 데이터와 입력된 데이터를 근태기록테이블에 기록한다.
              cur.execute("INSERT INTO att(comnum, name, department, attendtype, starttime, work_leave, startdate, enddate) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(company_num, extra_insert_info_name, extra_insert_info_department, attendtype_normal, checktime, workstart, checkday, checkday))
              conn.commit()
              return save_ok
           else:
              return exist_workon_data

     elif request.form.get("leave"):
        conn = sqlite3.connect(DBfolderpath)
        cur = conn.cursor()
        cur.execute("SELECT * FROM infoDB WHERE comnum=? AND password=?;", (company_num, password))
        rows = cur.fetchall()
        
        if rows == []:
           return nomatch_id_password
          
        else:
           cur.execute("SELECT * FROM att WHERE comnum=? AND startdate=? AND work_leave=?;", (company_num, checkday, workstart))
           no_work_record_rows = cur.fetchall()
           if no_work_record_rows == []:
              return no_work_record
           else:              
            cur.execute("SELECT * FROM att WHERE comnum=? AND startdate=? AND work_leave=?;", (company_num, checkday, leaveworkplace))
            exist_att_rows = cur.fetchall()
            if exist_att_rows == []:
               cur.execute("SELECT department FROM infoDB WHERE comnum=?;", (company_num,))
               extra_insert_info_row = cur.fetchone()
               extra_insert_info_department = str(extra_insert_info_row[0])
               cur.execute("SELECT name FROM infoDB WHERE comnum=?;", (company_num,))
               extra_insert_info_row_name = cur.fetchone()
               extra_insert_info_name = str(extra_insert_info_row_name[0])
               insert_text = "insert into att(comnum, name, department, attendtype, endtime, work_leave, startdate, enddate) values('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(company_num, extra_insert_info_name, extra_insert_info_department, attendtype_normal, checktime, leaveworkplace, checkday, checkday)
               cur.execute(insert_text)
               conn.commit()
               return save_ok
            else:
               return exist_leaveworkplace_data
    

     return "에러발생 확인해야 합니다. 관리자에게 알려주세요."

@app.route("/result", methods=["GET", "POST"])
# intro.html에서 form태그 변경 script로 남은연차계산을 클릭했을 때 경로
def result():
   # infoDB 테이블순서: No, Comnum, password, name, birth, department, position, joindate
   # att 테이블순서: comnum, name, department, attendtype, work_leave, startdate, enddate, daycount, starttime, endtime, reason
   company_num = request.form["company_num"]
   password = request.form["password"]
   checkday = request.form["checkday"]
   calculatepoleday1 = request.form.get("checkday", "")
   yearoff = request.form.get("yearoff")
   basic_yearoff_count = 12
   if_last_year_att_full_ok_addday = 3
   if_calculatepoleday1_joinday_count_2_addday = 1
   if_calculatepoleday1_joinday_count_4_addday = 2
   if_calculatepoleday1_joinday_count_6_addday = 3
   if_calculatepoleday1_joinday_count_8_addday = 4
   if_calculatepoleday1_joinday_count_10_addday = 5

   calculatepoleday1_text = datetime.strptime(calculatepoleday1, '%Y-%m-%d')  # 기준일자를 년월일만 남기기(계산용도)
   calculatepoleday1_text_text = calculatepoleday1_text.strftime('%Y-%m-%d')
   print(calculatepoleday1_text_text)   # 기준일자를 문자열로 변경

   checkday_text = datetime.strptime(checkday, '%Y-%m-%d')

   yearoff_total_list = []


   conn = sqlite3.connect(DBfolderpath)
   cur = conn.cursor()
   # 사번과 패스워드가 일치하는 사원의 입사일자를 가지고 옴
   match_comnum_sql = "SELECT * FROM infoDB WHERE comnum=? AND password=?;"
   cur.execute(match_comnum_sql, (company_num, password))
   rows = cur.fetchall()
   conn.commit()
   print("사번과 패스워드가 일치하는 사원정보 = " + str(rows))

   company_join_1 = str(rows[0][7])                        # insaDB 테이블에서  입사일자를 불러온 값
   company_join_1_t = datetime.strptime(company_join_1, '%Y-%m-%d')    # 입사일자를 년월일만 남기기(계산용도)
   print(company_join_1_t.strftime('%Y-%m-%d'))              # 입사일자를 문자열로 변경
   calculatepoleday1_text_2 = int((calculatepoleday1_text - company_join_1_t).days/365)   # int(기준일자-입사일자/365) = 입사후 경과년수
   print("입사후 기준일까지 경과년수 " + str(calculatepoleday1_text_2))
   near_pole_yearoff_date = datetime(company_join_1_t.year + calculatepoleday1_text_2, company_join_1_t.month, company_join_1_t.day).strftime('%Y-%m-%d')
   near_pole_yearoff_date_text = str(near_pole_yearoff_date)
   near_pole_yearoff_date_text_strptime = datetime.strptime(near_pole_yearoff_date_text, '%Y-%m-%d')
   print("입사후 가장가까운 연차산정일자는 " + str(near_pole_yearoff_date))
   attendtype_yearoff = "연차"

   conn2 = sqlite3.connect(DBfolderpath)
   cur2 = conn2.cursor()
   #연차계산 중 연차기간이 연차산정시작일자부터 연차산정종료일자까지 기간내에 있는 연차는 계산함
   yearoff_list_sql_1st = "SELECT daycount, startdate, enddate FROM att WHERE comnum=? AND attendtype=? AND startdate BETWEEN ? AND ? AND enddate BETWEEN ? AND ?;"
   cur2.execute(yearoff_list_sql_1st, (company_num, attendtype_yearoff, near_pole_yearoff_date_text, checkday, near_pole_yearoff_date_text, checkday,))
   yearoff_rows_1_s = cur2.fetchall()
   #해당하는 연차일자 데이터를 yearoff_total_list에 추가함
   for yearoff_total_list_extend in yearoff_rows_1_s:
       yearoff_total_list.append(yearoff_total_list_extend)
   #해당하는 연차산정식
   yearoff_rows_1_s_sum = 0
   for yearoff_rows_1 in yearoff_rows_1_s:
       yearoff_rows_1_s_sum += int(str(yearoff_rows_1[0]))
   print("연차기록이 있는 DB데이터 중 연차산정시작일부터 기준일까지 리스트 =" + str(yearoff_rows_1_s))
   # print(yearoff_rows_1_s[0][0])
   print("연차기록이 있는 DB데이터 중 연차산정시작일부터 기준일까지 연차일수 =" + str(yearoff_rows_1_s_sum))

   #연차계산 중 연차시작일자가 연차산정시작일과 연차산정종료일의 중간에 있고 연차종료일자가 연차산정시작일과 연차산정종료일을 경우 계산
   yearoff_list_sql_s = "SELECT startdate FROM att WHERE comnum=? AND attendtype=? AND startdate BETWEEN ? AND ? AND ?<enddate;"
   cur2.execute(yearoff_list_sql_s, (company_num, attendtype_yearoff, near_pole_yearoff_date_text, checkday, checkday,))
   yearoff_rows_2 = cur2.fetchone()
   print("연차기록이 있는 DB데이터 중 연차시작일자가 연차산정시작일자와 기준일자사이에 있고 연차종료일자는 기준일자 이후에 있을 경우 일수 =" + str(yearoff_rows_2))
   if yearoff_rows_2 is not None:
            add_startdate_s = datetime.strptime(str(yearoff_rows_2[0]), '%Y-%m-%d')
            add_startdate_s_add = datetime(add_startdate_s.year, add_startdate_s.month, add_startdate_s.day).strftime('%Y-%m-%d')
            #add_startdate_s는 조건에 맞는 연차시작일자를 나타낸다
            add_day_s = (checkday_text - add_startdate_s).days + 1   #산정기준일자에서 해당하는 연차시작일자를 빼줘야 일수가 나옴
            add_day_s_tuple = (add_day_s, str(add_startdate_s_add), str(calculatepoleday1_text_text))
            print(add_day_s_tuple)
            yearoff_total_list.append(add_day_s_tuple)
   else:
       add_day_s = 0
       #add_day_s는 위조건에 맞는 값이 있을 경우 연차산정종료일자에서 연차시작일자를 뺀 일자의 경우 수임

   #연차계산 중 연차시작일자가 연차산정시작일자보다 앞에 있고 연차종료일자가 연차산정시작일과 연차산정종료일의 중간에 있는 경우 계산
   yearoff_list_sql_e = "SELECT enddate FROM att WHERE comnum=? AND attendtype=? AND startdate<? AND enddate BETWEEN ? AND ?;"
   cur2.execute(yearoff_list_sql_e, (company_num, attendtype_yearoff, near_pole_yearoff_date_text, near_pole_yearoff_date_text, checkday,))
   yearoff_rows_3 = cur2.fetchone()
   print("연차기록이 있는 DB데이터 중 연차시작일자가 연차산정시작일자보다 앞에 있고 연차종료일자가 연차산정시작일자와 기준일자 사이에 있을 경우 일수 =" + str(yearoff_rows_3))
   if yearoff_rows_3 is not None:
            add_enddate_e = datetime.strptime(str(yearoff_rows_3[0]), '%Y-%m-%d')
            add_enddate_e_add = datetime(add_enddate_e.year, add_enddate_e.month, add_enddate_e.day).strftime('%Y-%m-%d')
            #add_startdate_s는 조건에 맞는 연차시작일자를 나타낸다
            add_day_e = (add_enddate_e - near_pole_yearoff_date_text_strptime).days + 1   # 해당하는 연차종료일자에서 연차산정시작일자를 빼줘야 함
            add_day_e_tuple = (add_day_e, str(near_pole_yearoff_date), str(add_enddate_e_add))
            print(add_day_e_tuple)
            yearoff_total_list.append(add_day_e_tuple)
   else:
       add_day_e = 0


   conn2.commit()

   if calculatepoleday1_text_2 >= 10:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + if_calculatepoleday1_joinday_count_10_addday
   elif 8 <= calculatepoleday1_text_2 < 10:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + if_calculatepoleday1_joinday_count_8_addday
   elif 6 <= calculatepoleday1_text_2 < 8:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + if_calculatepoleday1_joinday_count_6_addday
   elif 4 <= calculatepoleday1_text_2 < 6:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + if_calculatepoleday1_joinday_count_4_addday
   elif 2 <= calculatepoleday1_text_2 < 4:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + if_calculatepoleday1_joinday_count_2_addday
   else:
       individual_yearoff_full_count_value_calculate = basic_yearoff_count + if_last_year_att_full_ok_addday + 0


   print("첫번째:"+str(yearoff_rows_1_s_sum) + "두번째:"+str(add_day_s) + "세번째:"+str(add_day_e))
   yecaroff_total = yearoff_rows_1_s_sum + add_day_s + add_day_e
   print("기준일자에서 누적 연차사용일수는 "+str(yecaroff_total))
   print(yearoff_total_list)

   
   if request.method == "GET":
        return access_deny
   elif request.method == "POST":
      #  calculatepoleday1 = request.form.get("checkday", "")
      #  yearoff = request.form.get("yearoff")

       if yearoff == "남은연차계산":
         #   calculatepoleday1_text = datetime.strptime(calculatepoleday1, '%Y-%m-%d')  # 기준일자를 년월일만 남기기(계산용도)
         #   calculatepoleday1_text_text = calculatepoleday1_text.strftime('%Y-%m-%d')
         #   print(calculatepoleday1_text_text)   # 기준일자를 문자열로 변경
         #   company_join_1 = str(rows[0][7])                        # insaDB 테이블에서  입사일자를 불러온 값
         #   company_join_1_t = datetime.strptime(company_join_1, '%Y-%m-%d')    # 입사일자를 년월일만 남기기(계산용도)
         #   print(company_join_1_t.strftime('%Y-%m-%d'))              # 입사일자를 문자열로 변경
         #   calculatepoleday1_text_2 = int((calculatepoleday1_text - company_join_1_t).days/365)   # int(기준일자-입사일자/365) = 입사후 경과년수
         #   print("입사후 기준일까지 경과년수 " + str(calculatepoleday1_text_2))
         #   near_pole_yearoff_date = datetime(company_join_1_t.year + calculatepoleday1_text_2, company_join_1_t.month, company_join_1_t.day).strftime('%Y-%m-%d')
         #   print("입사후 가장가까운 연차산정일자는 " + str(near_pole_yearoff_date))

           return render_template("result.html", company_join_value=str(company_join_1_t.strftime('%Y-%m-%d')), 
                                  yearoff_pole_date_value=str(near_pole_yearoff_date),
                                  individual_yearoff_full_count_value = str(individual_yearoff_full_count_value_calculate),
                                  yearoff_count_value=yecaroff_total, 
                                  yearoff_date_value=yearoff_total_list)

@app.route("/password_ch", methods=["GET", "POST"])
def password_ch():
    if request.method == "GET":
        return access_deny

    elif request.method == "POST":
        company_num = request.form["company_num"]
        password = request.form["password"]
        change_pw = request.form["change_pw"]
        change_pw_confirm = request.form["change_pw_confirm"]

        conn_pw = sqlite3.connect(DBfolderpath)
        cur_pw = conn_pw.cursor()
        # 사번과 패스워드가 일치하는 사원의 입사일자를 가지고 옴
        cur_pw.execute("SELECT * FROM infoDB WHERE comnum=? AND password=?;", (company_num, password,))
        rows_pw = cur_pw.fetchone()
        print(rows_pw)

        if rows_pw is None:
            return nomatch_info
        else:
            if change_pw == change_pw_confirm:
                ch_password_cmd = "UPDATE infoDB SET password = ? WHERE comnum = ?;"
                cur_pw.execute(ch_password_cmd, (change_pw, company_num,))
                conn_pw.commit()
                return ch_password_ok
            else:
                return nomatch_ch_password

    else:
        return access_deny



if __name__ == "__main__":
  app.run(host=host, debug=True, port=port, use_reloader=False)
  # app.run(host="127.0.0.1", debug=True, port=9999)
  # app.run(host='0.0.0.0', debug=True, port=9999) 
  # debug=True는 실행파일만들때 False로 변경할 것  
  # 모든 ip에서 접근이 가능하게 하는 것이 0.0.0.0 이고 여기에 특정 주소를 주면 해당 주소의 ip에서만 접근이 가능하다.
  # 즉, 웹서버를 구성한 후 웹서버의 공인ip를 넣으면 접근할 수 있다.
  # 단, 웹서버에서 포트포워드작업을 해서 외부에서 접근하는 port번호와 flask서버가 설치된 곳의 port번호(내부포트)를 맵핑해줘야 한다.