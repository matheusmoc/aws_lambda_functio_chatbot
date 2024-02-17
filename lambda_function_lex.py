import json
import boto3
import uuid
import logging
import datetime
import time

def validate(slots):

    valid_cities = ['montes claros','janaúba','bocaiuva']
    
    if not slots['SCHEDULE_NAME']:
        print("Por favor, informe o nome do paciente")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_NAME'
        }
    
    if not slots['SCHEDULE_LASTNAME']:
        print("Por favor, informe o sobrenome do paciente")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_LASTNAME'
        }
    
    if not slots['SCHEDULE_PHONE']:
        print("Por favor, informe um telefone para melhor contato ou whatsapp")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_PHONE'
        }
    
    if not slots['SCHEDULE_STATE']:
        print("Por favor, informe o estado em que residem")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_STATE'
        }
    
    if not slots['SCHEDULE_CITY']:
        print("Por favor, informe a cidade em que residem")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_CITY'
        }    
        
    if slots['SCHEDULE_CITY']['value']['originalValue'].lower() not in valid_cities:
        print("Infelizmente não atendemos essa região")
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_CITY',
            'message': 'Atualmente, oferecemos suporte apenas a {} como destino válido.'.format(", ".join(valid_cities))
        }
        
    if not slots['SCHEDULE_VACCINE']:
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_VACCINE'
        }

    if not slots['SCHEDULE_DATE']:
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_DATE',
        }
        
    if not slots['SCHEDULE_TIME']:
        return {
            'isValid': False,
            'violatedSlot': 'SCHEDULE_TIME'
        }

    return {'isValid': True}
    
def lambda_handler(event, context):
    
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    print(event['invocationSource'])
    print(slots)
    print(intent)
    validation_result = validate(event['sessionState']['intent']['slots'])
    
    if event['invocationSource'] == 'DialogCodeHook':
        if not validation_result['isValid']:
            if 'message' in validation_result:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            'slotToElicit':validation_result['violatedSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            'name':intent,
                            'slots': slots
                        }
                    },
                    "messages": [
                        {
                            "contentType": "PlainText",
                            "content": validation_result['message']
                        }
                    ]
                }
            else:
                response = {
                    "sessionState": {
                        "dialogAction": {
                            'slotToElicit':validation_result['violatedSlot'],
                            "type": "ElicitSlot"
                        },
                        "intent": {
                            'name':intent,
                            'slots': slots
                        }
                    }
                } 
            return response
        else:
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            dynamodb = boto3.resource('dynamodb')
            lambd = boto3.client('lambda')
            table_name = 'HospitalNurseDB'  
            table = dynamodb.Table(table_name)
            item_id = str(uuid.uuid4())
            
            item = {
                "uuid": item_id,
                "Name": slots['SCHEDULE_NAME']['value']['interpretedValue'],
                "LastName": slots['SCHEDULE_LASTNAME']['value']['interpretedValue'],
                "Phone": slots['SCHEDULE_PHONE']['value']['interpretedValue'],
                "State": slots['SCHEDULE_STATE']['value']['interpretedValue'],
                "City": slots['SCHEDULE_CITY']['value']['interpretedValue'],
                "Vaccine": slots['SCHEDULE_VACCINE']['value']['interpretedValue'],
                "Date": slots['SCHEDULE_DATE']['value']['interpretedValue'],
                "Time": slots['SCHEDULE_TIME']['value']['interpretedValue']
            }
            
            try:
                table.put_item(Item=item)
                logger.info("Item inserido no DynamoDB: %s", json.dumps(item)) 
                response = table.scan()
                logger.info("Dados escaneados no DynamoDB: %s", json.dumps(response)) 
            except Exception as e:
                logger.error("Erro ao inserir item no DynamoDB: %s", str(e))
                raise e
                
            response = {
                "sessionState": {
                    "dialogAction": {
                        "type": "Delegate"
                    },
                    "intent": {
                        'name':intent,
                        'slots': slots
                    }
                }
            } 
        return response
        
        
    if event['invocationSource'] == 'FulfillmentCodeHook':
        response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                'name':intent,
                'slots': slots,
                'state':'Fulfilled'
                
                }
    
            },
        }
                
        return response
