from django.shortcuts import get_object_or_404
import json
from django.http import HttpResponse

from cheques.models import ChequeRecibido


def get_monto_cheque_recibido(request):
    cheque_id = int(request.GET['cheque_id'])

    result_set = []

    if cheque_id:
        monto = float((get_object_or_404(ChequeRecibido, pk=cheque_id)).monto)
        result_set.append({
            'monto': monto,
        })

    return HttpResponse(json.dumps(result_set), 
                        content_type='application/json')
