# Copyright (c) Microsoft Corporation.

# Licensed under the MIT License.


import logging

import azure.functions as func
import json
import collections
#import pyodbc
from azure.cosmos import CosmosClient
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    #logging.info('Python HTTP trigger function processed a request.')

    # get cosmos DB client and container
    url = ''
    key = ''
    client = CosmosClient(url, credential=key)

    database_name = 'customercomplaints'
    database = client.get_database_client(database_name)
    
    container_name = 'complaints'
    complaintscontainer = database.get_container_client(container_name)

    container_name = 'responses'
    responsescontainer = database.get_container_client(container_name)

    container_name = 'employees'
    employeescontainer = database.get_container_client(container_name)

    # get parameters
    name = req.params.get('name')
    dataset = req.params.get('dataset')
    department = req.params.get('department')
    complaintid = req.params.get('complaintid')
    supportagent = req.params.get('supportagent')
    forwarddepartment = req.params.get('forwarddepartment')
    if department:
        department = str(department)
    else:
        department = 'Loans'
    supportagent = req.params.get('supportagent')

    if (dataset == 'supportagents'):
        querystr = 'SELECT  e.employee_id Id, e.name Name, e.department PrimaryDepartment \
                            FROM employees e where e.department in (\'Banking Services\', \'Card Services\', \'Credit Reporting\',\'Debt Collection\', \'Loans\')'

        results = []
        for item in employeescontainer.query_items(query=querystr,enable_cross_partition_query=True):
            results.append(item)
        return func.HttpResponse(json.dumps(results), status_code=200)
    elif (dataset == 'complaints'):
        querystr = 'SELECT c.CustomerId,c.ComplaintId,c.CustomerName,c.ComplaintSubject,c.ComplaintTextSummaryOutlook,c.ComplaintFullText, \
                            c.ComplaintTextSummary,c.CustomerEmail,c.ComplaintDate,c.ComplaintSentiment, \
                            c.ComplaintSentimentScore,c.Department, \
                            c.Class1,c.Class2,c.Class3, \
                            c.SubClass1,c.SubClass1Score,c.SubClass2,c.SubClass2Score,c.SubClass3,c.SubClass3Score, c.id \
                            FROM complaints c where c.Status = \'New\' and c.Department = \'' + department + '\''

        results = []
        for item in complaintscontainer.query_items(query=querystr,enable_cross_partition_query=True):
            results.append(item)
        return func.HttpResponse(json.dumps(results), status_code=200)
    elif (dataset == 'resolvedcomplaints'): 
        querystr = 'SELECT c.CustomerId,c.ComplaintId,c.CustomerName,c.ComplaintSubject,c.ComplaintTextSummaryOutlook,c.ComplaintFullText, \
                            c.ComplaintTextSummary,c.CustomerEmail,c.ComplaintDate,c.ComplaintSentiment, \
                            c.ComplaintSentimentScore,c.Department, \
                            c.Class1,c.Class2,c.Class3, \
                            c.SubClass1,c.SubClass1Score,c.SubClass2,c.SubClass2Score,c.SubClass3,c.SubClass3Score, c.id \
                            FROM complaints c where c.Status = \'Resolved\' and c.SupportAgent = \'' + supportagent + '\''

        results = []
        for item in complaintscontainer.query_items(query=querystr,enable_cross_partition_query=True):
            results.append(item)
        return func.HttpResponse(json.dumps(results), status_code=200)
    elif (dataset == 'updatecomplaintstatus'):
        #body = req.get_body()
        req_body = req.get_json()
        doc_id = req_body.get('id')
        doc_partitionkey = req_body.get('Class1')  
        doc_supportagent = req_body.get('SupportAgent')           
        # doc_id = 'bb15858d-2f01-44bc-8e61-d33aa077d08a'
        # doc_pk = 'Debt Collection'
        read_item = complaintscontainer.read_item(item=doc_id, partition_key=doc_partitionkey)
        read_item

        read_item['Status'] = 'Resolved'
        read_item['SupportAgent'] = doc_supportagent
        read_item['ResolvedDate'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        response = complaintscontainer.upsert_item(body=read_item)
    
        return func.HttpResponse("Updated the status to resolved",status_code=200)
    elif (dataset == 'forwardcomplaint'):
        #body = req.get_body()
        req_body = req.get_json()
        doc_id = req_body.get('id')
        doc_partitionkey = req_body.get('Class1')          
        # doc_id = 'bb15858d-2f01-44bc-8e61-d33aa077d08a'
        # doc_pk = 'Debt Collection'
        read_item = complaintscontainer.read_item(item=doc_id, partition_key=doc_partitionkey)
        read_item

        read_item['Department'] = forwarddepartment
        response = complaintscontainer.upsert_item(body=read_item)
    
        return func.HttpResponse("Updated the status to resolved",status_code=200)
    elif (dataset == 'addcomplaintresponse'):
        new_item = req.get_json()
        response = responsescontainer.upsert_item(body=new_item)
        #return func.HttpResponse(json.dumps(new_item),status_code=200)
        return func.HttpResponse("Added a new response to the complaint",status_code=200)
    elif (dataset == 'getcomplaintresponses'):
        querystr = 'SELECT r.id,r.ComplaintId,r.Response,r.SupportAgent, r.ResponseDate \
                            FROM responses r where r.ComplaintId = \'' + complaintid + '\''
        results = []
        for item in responsescontainer.query_items(query=querystr,enable_cross_partition_query=True):
            results.append(item)
        return func.HttpResponse(json.dumps(results), status_code=200)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a dataset in the query string or in the request body for a personalized response.",
             status_code=200
        )
