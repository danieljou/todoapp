from  rest_framework.response import Response
from rest_framework.decorators import api_view , permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
# Create your views here.

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from rest_framework import status 

from .models import *
from .serialisers import *

from django.db import transaction

import pyotp
import time


from authentication.permissions import *
KEY = "LOnchaninKeyEncodeEnbASE6432"

# # 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tax_zones(request):
    tax_zones = TaxZone.objects.all()
    serializer = TaxZoneSErializer(tax_zones, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_single_tax_zone(request, id):
    tax_zone = get_object_or_404(TaxZone, pk=id)
    serializer = TaxZoneSErializer(tax_zone)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tax_zone(request):
    if request.method == 'POST':
        serializer  = TaxZoneSErializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_tax_zone(request, id):
    tax_zone = get_object_or_404(TaxZone, pk=id)
    if request.method == 'PUT':
        serializer = TaxZoneSErializer(tax_zone, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

def generer_otp(secret, interval=10):
    """
    Génère un OTP en utilisant la clé secrète fournie.

    Args:
    - secret (str): La clé secrète pour la génération de l'OTP.
    - interval (int): L'intervalle de temps en secondes (par défaut 30 secondes).

    Returns:
    - str: L'OTP généré.
    """
    totp = pyotp.TOTP(secret, interval=interval , digits=4)
    return totp.now()


def verifier_otp(secret, otp, interval=10):
    """
    Vérifie un OTP en utilisant la clé secrète fournie.

    Args:
    - secret (str): La clé secrète pour la vérification de l'OTP.
    - otp (str): L'OTP à vérifier.
    - interval (int): L'intervalle de temps en secondes (par défaut 30 secondes).

    Returns:
    - bool: True si l'OTP est valide, False sinon.
    """
    totp = pyotp.TOTP(secret, interval=interval, digits=4)
    return totp.verify(otp)


@api_view(['GET'])
# @permission_classes([IsAuthenticated , IsTaskAdmin])
@permission_classes([IsAuthenticated ])
def get_formulas(request):
    formulas = Formula.objects.all()
    serializer = FormulaSerializer(formulas, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_single_formula(request, formula_id):
    try:
        formulas = get_object_or_404(Formula, pk=formula_id)
    except:
        return Response(status = status.HTTP_404_NOT_FOUND)
    serializer = FormulaSerializer(formulas)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_formulas(request):
    if request.method == 'POST':
        serialiser = FormulaSerializer(data=request.data)
        if serialiser.is_valid():
            serialiser.save()
            return Response(serialiser.data, status = status.HTTP_201_CREATED)
        else:
            return Response({'errors': serialiser.errors}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_formule(request, formula_id):
    if request.method == 'POST':
        try:
            formula = get_object_or_404(Formula, pk=formula_id)
        except:
            return Response(status = status.HTTP_404_NOT_FOUND)
        serializer = FormuleSerializer(data= request.data)
    
        total = formula.get_percent() + request.data['taux']
        if serializer.is_valid():
            if total > 100:
                return Response({'msg':'Le taux ne peut dépasser 100%'}, status = status.HTTP_400_BAD_REQUEST)
            else:
                
                serializer.save(formula = formula)
                return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
@api_view(['GET'])
@permission_classes([IsAuthenticated])         
def get_pendeing_accounts(request):
    accounts = Member.objects.filter(status='EN ATTENTE')
    serializer = MemberSerializer2(accounts, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def send_otp(request, account_id):
    if request.method == 'POST':
        email = None
        try:
            email = request.data['email']
        except:
            return Response({"msg":"l'email res requise"}, status=status.HTTP_400_BAD_REQUEST)
        account = get_object_or_404(Member, pk = account_id)
        totp = pyotp.TOTP(pyotp.random_base32(), digits=4, interval=120)
        account.otp = totp.secret
        account.save()
        # totp = pyotp.TOTP(account.otp)
        otp = totp.now()
        message = render_to_string('otp.html', {'otp_code':otp})
        send_mail(
            subject="Confirmation du compte",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=message,
            # content_subtype='html'
        )
        return Response({"msg":'success'},status=status.HTTP_201_CREATED)
        

def check_otp(account_otp, user_entered_otp):
    totp = pyotp.TOTP(account_otp, digits=4)  # Assurez-vous de spécifier le nombre de chiffres correct
    return totp.verify(user_entered_otp)
    
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def verify_otp(request, account_id):
    if request.method == 'POST':
        user_entered_otp = request.data['user_entered_otp']
        try:
            account = get_object_or_404(Member, pk=account_id)
        except:
            return Response(status = status.HTTP_404_NOT_FOUND)
        
        totp = pyotp.TOTP(account.otp, interval=120, digits=4)
        test = totp.verify(user_entered_otp)
        if test:
            account.status = 'VALIDE'
            account.save()
            return Response({'msg':'Succès'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'msg':'erreur jkj'}, status=status.HTTP_400_BAD_REQUEST)

    


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_formule_for_formula(request, formula_id):
    try:
        formula = get_object_or_404(Formula, pk=formula_id)
    except:
        return Response(status = status.HTTP_404_NOT_FOUND)
    formules = Formule.objects.filter(formula=formula)
    serializer = FormuleSerializer(formules, many=True)
    return Response(serializer.data, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_data_user(request):
    data = {}
    member = None
    try:
        member = Member.objects.get(owner = request.user) 
    except Member.DoesNotExist:
        member = None
    if member is not None:
        # account_serialiser = AccountSerializer(account)
        # data['account'] = account_serialiser.data
        # member = Member.objects.get(owner = request.user)
        data['member'] = MemberSerializer2(member).data
        # data['all_operations'] = Operation.objects.filter(account = account).count() or 0
    else:
        data['member'] = member
    
    return Response(data, status=status.HTTP_200_OK)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_istitution_account(request):
    if request.method == 'POST':
        serializer = MemberSerializer(data = request.data)
        if serializer.is_valid():
            try:
                account = Account()
                account.number = account.generate_unique_id()
                account.save()
                result = serializer.save(owner = request.user, account = account)
                serial = MemberSerializer2(result)
                return Response({'msg':'success', 'infos': serial.data}, status = status.HTTP_201_CREATED)
            except Exception as e:
                print(e)
                return Response({'code':'70','error':serializer.errors}, status = status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response({'erros':serializer.errors}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_members(request):
    membres = Member.objects.all()
    serializer = MemberSerializer2(membres, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK  )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tax(request):
    if request.method == 'POST':
        serializer = TaxSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(creator = request.user)
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:   
            return Response({'erors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_taxes(request):
    taxes = Tax.objects.all()
    serializer  = TaxDataSerializer(taxes, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def repartition(request,tax_id):
    data = {}
    tax = get_object_or_404(Tax, pk=tax_id)
    serializer = TaxSerializer(tax)
    formules = Formule.objects.filter(formula = tax.formula)
    formules_serializer = FormuleSerializer(formules, many = True)
    types = [item.member_type for item in formules]
    members = {}
    members_percent = {}
    for item in formules:
        if item.benfeniciare:
            local_members = Account.objects.filter(account__type = item.member_type, account__value = item.benfeniciare)
            members[item.member_type + ' - ' +item.benfeniciare] = local_members
            try:
                members_percent[item.member_type + ' - ' +item.benfeniciare] = item.taux / len(local_members)
            except ZeroDivisionError :
                members_percent[item.member_type + ' - ' +item.benfeniciare] = item.taux
        else:
            local_members = Account.objects.filter(account__type = item.member_type)
            members[item.member_type] = local_members
            try:
                members_percent[item.member_type] = item.taux / len(local_members)
            except ZeroDivisionError :
                members_percent[item.member_type] = item.taux
            
    
    members_serializer = {}
    repartition_serializer = {}
    operations_for_save = []
    for key in members.keys():
        local_serial = AccountDetailSerializer(members[key] , many = True)
        members_serializer[key] = local_serial.data
        tab = []
        for item in members[key]:
            operation = Operation()
            operation.account = item
            operation.tax = tax
            operation.amount = (tax.amount * members_percent[key]) / 100
            operation.percent = members_percent[key]
            serial = OperationSerializer(operation)
            operations_for_save.append(operation)
            tab.append(serial.data)
        
        repartition_serializer[key] = tab

    data['tax'] = serializer.data
    data['formules'] = formules_serializer.data
    data['membres'] = members_serializer
    data['members_percent'] = members_percent
    data['repartitions'] = repartition_serializer
    if request.method == 'GET':
        return Response(data, status = status.HTTP_200_OK)
    elif request.method == 'POST':
        if tax.is_close:
            return Response({'error':'Taxe déja repartie'}, status=status.HTTP_400_BAD_REQUEST)
        serial =  OperationSerializer(data = operations_for_save, many = True)
        tax.is_close = True
        
        for item in operations_for_save:
            item.save()
                
        tax.save()
        return Response({'msg':'save sucessfully'}, status = status.HTTP_201_CREATED)
        # else:
        #     print(operations_for_save[0])
        #     return Response({'msg':'error'}, status = status.HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_operations(request):
    operations = Operation.objects.all()
    serializer = OperationSerializer2(operations, many = True)
    return Response(serializer.data, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_operations_for_account(request, member_id):
    data = {}
    member = None
    try:
        member = Member.objects.get( owner__id =member_id)
    except Member.DoesNotExist:
        member = None
    account = None
    if member:
        try:
            account = Account.objects.get(account = member)
            account_serial = AccountSerializer(account)
            data['account'] = account_serial.data
        except Account.DoesNotExist:
            account = None
            data['account'] = None
    
    if account is not None:
        operations = Operation.objects.filter(account = account)
        serializer = OperationSerializer2(operations, many = True)
        data['operations'] = serializer.data
    return Response(data, status = status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_my_operations(request):
    data = {}
    member = None
    try:
        member = Member.objects.get( owner =request.user)
    except Member.DoesNotExist:
        member = None
    account = None
    if member:
        try:
            account = Account.objects.get(account = member)
            account_serial = AccountSerializer(account)
            data['account'] = account_serial.data
        except Account.DoesNotExist:
            account = None
            data['account'] = None
    # data['account'] = account
    if account is not None:
        operations = Operation.objects.filter(account = account)
        serializer = OperationSerializer2(operations, many = True)
        data['operations'] = serializer.data
    return Response(data, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_opeation_detail(request, operation_id):
    operation = get_object_or_404(Operation, pk = operation_id)
    serializer = OperationSerializer2(operation)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_note(request, tax_id):
    if request.method == 'POST':
        tax = get_object_or_404(Tax, pk=tax_id)
        serializer = NoteSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(user = request.user, tax= tax)
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_note_for_tax(request, tax_id):
    tax = get_object_or_404(Tax, pk=tax_id)
    notes = Note.objects.filter(tax=tax)
    serializer = NoteSerializer(notes, many = True)    
    return Response(serializer.data, status = status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def validate_operation(request, operation_id):
    operation = get_object_or_404(Operation , pk=operation_id)
    if operation.account.account.owner != request.user:
        return Response({'error':"Vous n'avez pas le droit"}, status=status.HTTP_403_FORBIDDEN)
    operation.validation = True
    operation.save()
    return Response( {"msg":"succès"},status = status.HTTP_200_OK)   


# # 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tax_zones(request):
    tax_zones = TaxZone.objects.all()
    serializer = TaxZoneSErializer(tax_zones, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_single_tax_zone(request, id):
    tax_zone = get_object_or_404(TaxZone, pk=id)
    serializer = TaxZoneSErializer(tax_zone)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_tax_zone(request):
    if request.method == 'POST':
        serializer  = TaxZoneSErializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_tax_zone(request, id):
    tax_zone = get_object_or_404(TaxZone, pk=id)
    if request.method == 'PUT':
        serializer = TaxZoneSErializer(tax_zone, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_entity(request):
    entities = Entity.objects.all()
    serializer = EntitySErializer(entities, many = True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_entiies_with_parent(request):
    state = Entity.objects.filter(type='ETAT')
    cu = Entity.objects.filter(type='COMMUNAUTE URBAINE')
    serial_cu = EntitySErializer(cu, many = True)
    serial_state = EntitySErializer(state, many = True)
    regions = Entity.objects.filter(type = "REGION")
    regions_ids = [item.id for item in regions]
    entities_groups = []
    for item in regions:
        departements = Entity.objects.filter(type = "DEPARTEMENT", parent = item)
        departments_list = []
        region_serial = EntitySErializer(item)
        
        for department in departements:
            
            communes = Entity.objects.filter(type = "COMMUNE", parent = department)
            communes_arr = Entity.objects.filter(type = "COMMUNE D'ARRONDISSEMENT", parent = department)
            communes_serial = EntitySErializer(communes, many = True)
            communes_arr_serial = EntitySErializer(communes_arr, many = True)
            data = {}
            data['communes'] = communes_serial.data
            data['communes_arr'] = communes_arr_serial.data
            depart_serial = EntitySErializer(department)
            infos = {
                'departement_details': depart_serial.data,
                'data':data
            }
            departments_list.append(infos)
        infos = {
            'region_infos':region_serial.data,
            'department_list':departments_list
        }
        entities_groups.append(infos)
        
            
    data = {
        'cu':serial_cu.data,
        'state':serial_state.data,
        'region':entities_groups
    }       
        
    # serializer = EntitySErializer3(entities, many = True)
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def create_entity(request):
    if request.method == 'POST':
        serializer  = EntitySErializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_single_entity(request, id):
    entity = get_object_or_404(Entity, pk=id)
    serializer = EntitySErializer2(entity)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_entity(request, id):
    entity = get_object_or_404(Entity, pk=id)
    if request.method == 'PUT':
        serializer = EntitySErializer(entity, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_entity_with_children(request, parent_id):
    parent = get_object_or_404(Entity, pk=parent_id)
    children = Entity.objects.filter(parent=parent)
    serializer = EntitySErializer(children, many = True)
    parent_serial = EntitySErializer(parent)
    data = {
        'parent': parent_serial.data,
        'children': serializer.data
    }
    return Response(data, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repartition_automatickly(request,operation_id):
            
    data = {}
    tax = get_object_or_404(Operation, pk=operation_id)
    if tax.type != 'IN':
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE) 
    
    tax_zone = TaxZone.objects.get(account = tax.account)
    # serializer = TaxSerializer(tax)
    formules = Formule.objects.filter(formula = tax_zone.formula)
    formules_serializer = FormuleSerializer(formules, many = True)
    types = [item.member_type for item in formules]
    members = {}
    members_percent = {}
    for item in formules:
        if item.benfeniciare:
            local_members = Account.objects.filter(account__type = item.member_type, account__value = item.benfeniciare)
            members[item.member_type + ' - ' +item.benfeniciare] = local_members
            try:
                members_percent[item.member_type + ' - ' +item.benfeniciare] = item.taux / len(local_members)
            except ZeroDivisionError :
                members_percent[item.member_type + ' - ' +item.benfeniciare] = item.taux
        else:
            local_members = Account.objects.filter(account__type = item.member_type)
            members[item.member_type] = local_members
            try:
                members_percent[item.member_type] = item.taux / len(local_members)
            except ZeroDivisionError :
                members_percent[item.member_type] = item.taux
            
    
    members_serializer = {}
    repartition_serializer = {}
    operations_for_save = []
    for key in members.keys():
        local_serial = AccountDetailSerializer(members[key] , many = True)
        members_serializer[key] = local_serial.data
        tab = []
        for item in members[key]:
            operation = Operation()
            operation.account = item
            operation.tax = tax
            operation.amount = (tax.amount * members_percent[key]) / 100
            operation.percent = members_percent[key]
            serial = OperationSerializer(operation)
            operations_for_save.append(operation)
            tab.append(serial.data)
        
        repartition_serializer[key] = tab

    # data['tax'] = serializer.data
    data['formules'] = formules_serializer.data
    data['membres'] = members_serializer
    data['members_percent'] = members_percent
    data['repartitions'] = repartition_serializer
    if request.method == 'GET':
        return Response(data, status = status.HTTP_200_OK)
    elif request.method == 'POST':
        if tax.is_close:
            return Response({'error':'Taxe déja repartie'}, status=status.HTTP_400_BAD_REQUEST)
        serial =  OperationSerializer(data = operations_for_save, many = True)
        tax.is_close = True
        
        for item in operations_for_save:
            item.save()
                
        tax.save()
        return Response({'msg':'save sucessfully'}, status = status.HTTP_201_CREATED)
        # else:
        #     print(operations_for_save[0])
        #     return Response({'msg':'error'}, status = status.HTTP_406_NOT_ACCEPTABLE)

