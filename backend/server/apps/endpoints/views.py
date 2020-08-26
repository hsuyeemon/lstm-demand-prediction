from django.shortcuts import render

# backend/server/apps/endpoints/views.py file
from rest_framework import viewsets
from rest_framework import mixins

from apps.endpoints.models import Endpoint
from apps.endpoints.serializers import EndpointSerializer

from apps.endpoints.models import MLAlgorithm
from apps.endpoints.serializers import MLAlgorithmSerializer

from apps.endpoints.models import MLAlgorithmStatus
from apps.endpoints.serializers import MLAlgorithmStatusSerializer

from apps.endpoints.models import MLRequest
from apps.endpoints.serializers import MLRequestSerializer

from apps.endpoints.models import PTest
from apps.endpoints.serializers import PtSerializer


import json
from numpy.random import rand
from rest_framework import views, status
from rest_framework.response import Response
from apps.dl.registry import MLRegistry
from server.wsgi import registry

from django.http import HttpResponse

from datetime import datetime


# Include the `fusioncharts.py` file which has required functions to embed the charts in html page
from .fusioncharts import FusionCharts

# Loading Data from a Static JSON String
# The `chart` method is defined to load chart data from an JSON string.


class EndpointViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = EndpointSerializer
    queryset = Endpoint.objects.all()


class MLAlgorithmViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    serializer_class = MLAlgorithmSerializer
    queryset = MLAlgorithm.objects.all()


def deactivate_other_statuses(instance):
    old_statuses = MLAlgorithmStatus.objects.filter(parent_mlalgorithm = instance.parent_mlalgorithm,
                                                        created_at__lt=instance.created_at,
                                                        active=True)
    for i in range(len(old_statuses)):
        old_statuses[i].active = False
    MLAlgorithmStatus.objects.bulk_update(old_statuses, ["active"])

class MLAlgorithmStatusViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.CreateModelMixin
):
    serializer_class = MLAlgorithmStatusSerializer
    queryset = MLAlgorithmStatus.objects.all()
    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                instance = serializer.save(active=True)
                # set active=False for other statuses
                deactivate_other_statuses(instance)



        except Exception as e:
            raise APIException(str(e))

class MLRequestViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet,
    mixins.UpdateModelMixin
):
    serializer_class = MLRequestSerializer
    queryset = MLRequest.objects.all()

class PredictView(views.APIView):
    def __init__(self):
        self.prediction = []


    def post(self, request, endpoint_name, format=None):

        algorithm_status = self.request.query_params.get("status", "test")
        algorithm_version = self.request.query_params.get("version","0.0.1")

        algs = MLAlgorithm.objects.filter(parent_endpoint__name = endpoint_name, status__status = algorithm_status, status__active=True)

        if algorithm_version is not None:
            algs = algs.filter(version = algorithm_version)

        if len(algs) == 0:
            return Response(
                {"status": "Error", "message": "ML algorithm is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(algs) != 2 and algorithm_status != "test":
            return Response(
                {"status": "Error", "message": "ML algorithm selection is ambiguous. Please specify algorithm version."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alg_index = 0
        if algorithm_status == "test":
            alg_index = 0 if rand() < 0.5 else 2
            #alg_index = 2

        indx = 0
        for i in registry.endpoints:
            indx = i

        print(alg_index,algs[alg_index].id)
        #algorithm_object = registry.endpoints[algs[alg_index].id]
        algorithm_object = registry.endpoints[indx]
        algorithm_object.setTimeLags(int(request.data['timelags']))
        print("filename",request.data['filename'])
        prediction = algorithm_object.compute_prediction(request.data['filename'])

        label = ""
        labelList = []
        for p in prediction:
            print(p)

            labelList.append( p["label"] if "label" in p else "error")




        ml_request = MLRequest(
            input_data=json.dumps(request.data['filename']),
            full_response=prediction,
            response=label.join("labelList"),
            feedback="",
            parent_mlalgorithm=algs[alg_index],
        )

        ml_request.save()


        for p in prediction:
            p["request_id"] = ml_request.id

        p1 = PTest(pt = json.dumps(prediction))
        p1.save()

        return Response(prediction)



def chart(request):
# Create an object for the column2d chart using the FusionCharts class constructor

    #
    predictions = [p.pt for p in PTest.objects.all()]
    #print(type(predictions),predictions[0])

    print("Length of predic",len(predictions))

    #print(predictions[len(predictions)-1])

    newp = eval(predictions[len(predictions)-1])

    datetime_str = newp[0]['date']





    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption = "forecast from 30 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })


    print(json.dumps(data_chart))
    #data =  data.json()
#first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d = FusionCharts("line", "ex1" , "100%", "400", "chart-1", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                            		"slantLabel": "1",
                            		"xAxisName": 'month',
                            		"yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")
# returning complete JavaScript and HTML code, which is used to generate chart in the browsers.
    newp = eval(predictions[len(predictions)-2])

    datetime_str = newp[0]['date']

    print(len(newp))



    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption =  "forecast from 90 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })

    print(json.dumps(data_chart))
    #data =  data.json()
    #first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d90 = FusionCharts("line", "ex2" , "100%", "400", "chart-2", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                                    "slantLabel": "1",
                                    "xAxisName": 'month',
                                    "yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")

    newp = eval(predictions[len(predictions)-3])

    datetime_str = newp[0]['date']





    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption = "forecast from 365 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })



#first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d365 = FusionCharts("line", "ex3" , "100%", "400", "chart-3", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                            		"slantLabel": "1",
                            		"xAxisName": 'month',
                            		"yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")

    return render(request, 'index.html', {'output1' : column2d.render(),'output2' : column2d90.render(),'output3' : column2d365.render()})


def cChart(request):
# Create an object for the column2d chart using the FusionCharts class constructor

    #
    predictions = [p.pt for p in PTest.objects.all()]
    #print(type(predictions),predictions[0])

    print("Length of predic",len(predictions))

    #print(predictions[len(predictions)-1])

    newp = eval(predictions[len(predictions)-1])

    datetime_str = newp[0]['date']





    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption = "forecast from 30 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })


    print(json.dumps(data_chart))
    #data =  data.json()
#first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d = FusionCharts("column2d", "ex1" , "100%", "400", "chart-1", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                            		"slantLabel": "1",
                            		"xAxisName": 'month',
                            		"yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")
# returning complete JavaScript and HTML code, which is used to generate chart in the browsers.
    newp = eval(predictions[len(predictions)-2])

    datetime_str = newp[0]['date']

    print(len(newp))



    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption =  "forecast from 90 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })

    print(json.dumps(data_chart))
    #data =  data.json()
    #first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d90 = FusionCharts("column2d", "ex2" , "100%", "400", "chart-2", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                                    "slantLabel": "1",
                                    "xAxisName": 'month',
                                    "yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")

    newp = eval(predictions[len(predictions)-3])

    datetime_str = newp[0]['date']





    datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')

    supcaption = "forecast from 365 days ahead"
    data_chart = []
    for i in newp:
        print(i['date'])
        datetest = datetime.strptime(i['date'], '%Y-%m-%d')
        print(datetest.year,datetest.month)
        if datetest.month == 12 and datetest.year == 2018 :
            print("hello")
            data_chart.append({
            "label":i['date'],
            "value":i['demand']
            })



#first arg : column chart => column2d, piechart=>pie2d,line =>line
    column2d365 = FusionCharts("column2d", "ex3" , "100%", "400", "chart-3", "json",
        # The data is passed as a string in the `dataSource` as parameter.
                            """{
                                "chart": {
                                    "caption": 'Demand forecast',
                                    "subCaption" : '"""+supcaption+"""',
                                    "showValues":"1",
                                    "showPercentInTooltip" : "0",
                                    "enableMultiSlicing":"0",
                                    "theme": "fusion",
                                    "exportEnabled" : "1",
                                    "showLabels": "1" ,
                                    "labelDisplay": "rotate",
                            		"slantLabel": "1",
                            		"xAxisName": 'month',
                            		"yAxisName": "demand"
                                },
                                "data": """+json.dumps(data_chart)+"""}""")

    return render(request, 'index.html', {'output1' : column2d.render(),'output2' : column2d90.render(),'output3' : column2d365.render()})






#from django.views.generic import TemplateView

#class AboutView(TemplateView):
