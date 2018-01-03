import urllib.request
from bs4 import BeautifulSoup
import csv
from time import sleep
from multiprocessing.dummy import Pool as ThreadPool 

#get bin numbers from building footprint.csv remove headers
with open('footprints/footprint_reduced.csv') as file:
    bin_numbers = [row[4] for row in csv.reader(file)][1:]

def queryBIS(bin_number):
    #get html of jobs page using bin_number
    url = "http://a810-bisweb.nyc.gov/bisweb/JobsQueryByLocationServlet?requestid=1&allbin=%s" %(bin_number)
    page = urllib.request.urlopen( url )
    soup = BeautifulSoup(page, "lxml")
    return soup


def getJobsList(bin_number):
    #wait for BIS to allow us to access page
    waiting = True
    while waiting:
        sleep(.05)
        try:
            soup = queryBIS(bin_number)
        except:
            return None
        waiting = soup.find("div", {'id': 'waiting-main'})
    
    #continue if there is an error message 
    error = soup.find("td", {'class' : 'errormsg'})
    if error:
        print('error', bin_number)
        return None
    
    address = soup.find("td", { "class" : "maininfo" }).get_text().replace('Premises: ','')
    content_table = soup.find("table", { "cellspacing" : "1" })
    new_job = []
        
    trs = content_table.findAll("tr")[2:]
        
    for i,row in enumerate(trs):            
        tds = row.findAll("td")
            
        #append to list if next job or last job of content, then reset 
        if len(tds) == 10 or len(trs) == i + 1:
            if new_job:
                all_jobs.append([bin_number, address] + new_job + [' '.join(details)])
            new_job, details = [], []
            
            for td in tds:
                new_job.append(td.get_text().strip()) 
            
        #append to details
        elif len(tds) == 2:
            for td in tds:
                details.append(td.get_text())
                
    return None

pool = ThreadPool(4) 

if __name__ == '__main__':
    all_jobs = [] #one to many

    pool.map(getJobsList, bin_numbers[:100])
    pool.close() 
    pool.join() 

    #save as all_jobs.tsv  
    header = ['bin','address','file_date','job_num','doc_num','job type',
            'job_status','status_date','lic_num','applicant',
            'in audit','zoning','details']

    with open('all_jobs.tsv', 'w') as file:
        writer = csv.writer(file, delimiter ='\t')
        writer.writerow(header)
        for row in all_jobs:
            writer.writerow(row)