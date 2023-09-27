
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import re
import time
import os
import json
import sys
from datetime import datetime
import mysql.connector
from difflib import SequenceMatcher

base_link = "https://salute.regione.veneto.it/servizi/cerca-medici-e-pediatri"
GP_link = "https://salute.regione.veneto.it/servizi/cerca-medici-e-pediatri?p_p_id=MEDICI_WAR_portalgeoreferenziazione_INSTANCE_F5Pm&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-3&p_p_col_count=2&_MEDICI_WAR_portalgeoreferenziazione_INSTANCE_F5Pm_action=ricerca&_MEDICI_WAR_portalgeoreferenziazione_INSTANCE_F5Pm_d-445503-p={page}&_MEDICI_WAR_portalgeoreferenziazione_INSTANCE_F5Pm_form-submit=true"

db = mysql.connector.connect(
  host="app.lagoonmed.eu",
  user="gpuser",
  password="P@xtibi2023",
  database="gp"
)



cursor = db.cursor()
cursor.execute("create database IF NOT EXISTS gp")

Q1 = "CREATE TABLE IF NOT EXISTS GPs (id int PRIMARY KEY , name VARCHAR(50), group_type VARCHAR(50),province VARCHAR(20))"
Q2 = "CREATE TABLE IF NOT EXISTS Second_Clinic (userId int PRIMARY KEY, FOREIGN KEY(userId) REFERENCES GPs(id), address VARCHAR(100), phone_number VARCHAR(50))"
Q3 = "CREATE TABLE IF NOT EXISTS GPs_Group (userId int PRIMARY KEY, FOREIGN KEY(userId) REFERENCES GPs(id), address VARCHAR(100), phone_number VARCHAR(50))"
cursor.execute(Q1)
cursor.execute(Q2)
cursor.execute(Q3)

cursor.execute("SET FOREIGN_KEY_CHECKS=0")

opts = uc.ChromeOptions()
driver = uc.Chrome(driver_executable_path="chromedriver", options=opts)
wait = WebDriverWait(driver,30)
provinces = ['Belluno','Padova','Rovigo','Treviso','Venezia','Vicenza','Verona']
week = ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica']
ambulatorio = ['Ambulatorio principale','Ambulatorio secondario','Ambulatorio terzo','Ambulatorio il quarto','Ambulatorio quinto','Ambulatorio sesto']



Q4 = "INSERT INTO GPs (id, name, group_type,province) VALUES (%s, %s, %s,%s)"
Q5 = "INSERT INTO Second_Clinic (userId, address, phone_number) VALUES (%s, %s, %s)"
Q6 = "INSERT INTO GPs_Group (userId, address, phone_number) VALUES (%s, %s, %s)"
Q7 = "SELECT * FROM GPs WHERE id =%s"

def test():
    """
    converted into global var
    """
    #opts = uc.ChromeOptions()
    # driver = uc.Chrome(driver_executable_path= ChromeDriverManager(version='116.0.5845.141').install(), options=opts)
    
    # driver = uc.Chrome(driver_executable_path="chromedriver", options=opts)
    #wait = WebDriverWait(driver,30)
    #provinces = ['Belluno','Padova','Rovigo','Treviso','Venezia','Vicenza','Verona']
    #week = ['Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato','Domenica']
    #ambulatorio = ['Ambulatorio principale','Ambulatorio secondario','Ambulatorio terzo','Ambulatorio il quarto','Ambulatorio quinto','Ambulatorio sesto']
    #page = 1
    #formated = {}
    start = time.time()
    scanProvince("Belluno")
    print("tempo: "+str(time.time()-start))
    #scanAll(provinces)

def scanAll(provinces):    
    for province in provinces:
        scanProvince(province)

def scanProvince(province):

    driver.get(base_link)
    drop=Select(driver.find_element(By.ID, 'provinciaChangeEvent'))
    drop.select_by_visible_text(province)
    drop=Select(driver.find_element(By.ID, 'tipologiaChangeEvent'))
    drop.select_by_visible_text('Medici di Medicina Generale')
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#button1 > input"))).click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#map-results > div > ul > li:nth-child(10) > a > img"))).click()
    #find last page
    els=driver.find_elements(By.XPATH,'//*[@id="map-results"]/div/ul/li')
    last = els[len(els)-1].text

    #goto 1st page
    driver.back()

    page = 1
    formated = {}
    while True:
        driver.get(GP_link.format(page = str(page)))
        try:
            elements = [el.get_attribute('onclick') for el in wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "poi")))]
        except TimeoutError:
            sys.exit()
        for ele in elements:
            cursor.execute(Q7,[re.sub("\D", "", ele)])

            res = cursor.fetchall()
            if len(res) > 0:
                print("exist")
                continue

            driver.execute_script(ele)
            data = wait.until(EC.presence_of_element_located((By.ID, "tab01"))).text
            data_list = data.split('\n')
            while("" in data_list):
                data_list.remove("")

            table = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "results")))

            result1 = html_to_json(table[0].get_attribute('innerHTML')).replace("\\u00e0","")
            last_name = [s for s in data_list if "COGNOME" in s]
            if len(last_name) > 0 :
                result3 = html_to_json(table[len(table)-1].get_attribute('innerHTML')).replace("\\n","")
            else:
                result3 = ""
            # address = data_list[data_list.index('Ambulatorio principale')+1]
            phone_indexes = [i for i,s in enumerate(data_list) if "Telefono" in s]
            if len(phone_indexes) == 0:
                phone_indexes.append(data_list.index("Ambulatorio principale")+2)
            result2 = {}
            for idx, phone_index in enumerate(phone_indexes):
                address = data_list[phone_index - 1]
                try:
                    phone = data_list[phone_index].split(":")[1].strip()
                except:
                    phone = "N/A"
                # print(address, phone)
                time_table={}
                
                try:
                    sub = data_list[phone_index:phone_indexes[idx+1]]
                except:
                    sub = data_list[phone_index:]
                for day  in week:
                    try:                        
                        if time_validation(sub[sub.index(day)+1].split("-")[0].strip()):
                            time_table[day]=sub[sub.index(day)+1]
                    except:
                        continue

                result2[ambulatorio[idx]] = {"address": address, "phone": phone, "time_table":time_table}

            # print(data_list)
            if result3 == "":
                formated[data_list[0]] = {"1st_pane":{"1": data_list[1],"time_table":json.loads(result1)},"2nd_pane":result2}
                group_id = 0
            else:                                            
                formated[data_list[0]] = {"1st_pane":{"1": data_list[1],"time_table":json.loads(result1)},"2nd_pane":result2,"3rd_pane":json.loads(result3)}
                s = 0
                for d in json.loads(result3):
                    s += similar(result2['Ambulatorio principale']['address'], d['ambulatorio principale'])
                rate = s / len(json.loads(result3))
                if rate < 0.8:
                    group_id = 1
                else:
                    group_id = 2

            print(page,"/",last,data_list[0],"region code : ", re.sub("\D", "", ele), "group id : ", group_id,province)

            r= json.dumps(formated)
            # print(json.loads(r))

            cursor.execute(Q4, (re.sub("\D", "", ele),data_list[0],group_id,province))


            try:
                print(result2['Ambulatorio secondario'])
                cursor.execute(Q5, (re.sub("\D", "", ele), result2['Ambulatorio secondario']['address'],result2['Ambulatorio secondario']['phone']))
            except KeyError:
                # cursor.execute(Q4, (re.sub("\D", "", ele), "NULL","NULL"))
                pass
            cursor.execute(Q6, (re.sub("\D", "", ele), result2['Ambulatorio principale']['address'],result2['Ambulatorio principale']['phone']))

            db.commit()
            with open('test.txt', 'w',encoding='utf-8') as json_file:
                # json_file.write(json.sloads(r))
                json.dump(json.loads(r), json_file, ensure_ascii=False)
            driver.back()


        page += 1
        if len(elements) != 5:
            break


def time_validation(stime): 
    try:
        datetime.strptime(stime, "%H:%M")
        return True
    except:
        return False
    

def html_to_json(content, indent=None):
    soup = BeautifulSoup(content, "html.parser")
    rows = soup.find_all("tr")
    
    headers = {}
    thead = soup.find("thead")
    if thead:
        thead = soup.find_all("th")
        for i in range(len(thead)):
            headers[i] = thead[i].text.strip().lower()
    data = []
    for row in rows:
        cells = row.find_all("td")
        if thead:
            items = {}
            if len(cells) > 0:
                for index in headers:
                    try:
                        items[headers[index]] = cells[index].text
                    except:
                        items[headers[index]] = ""
        else:
            items = []
            for index in cells:
                items.append(index.text.strip())
        if items:
            data.append(items)
    return json.dumps(data, indent=indent)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

if __name__ == "__main__":

    test()